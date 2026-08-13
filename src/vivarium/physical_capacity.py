"""Noyau pur de capacité physique P.

Ce module ne possède aucune persistance et ne connaît ni ``need_state`` ni le
runtime. Il sépare explicitement deux contrats qui étaient historiquement
mélangés dans le banc synthétique :

- une activité impose un seuil de capacité et un *débit* de P par heure ;
- une traversée impose un coût discret par arête, appliqué seulement si la
  mutation canonique correspondante réussit.

Les coefficients viennent toujours d'une politique versionnée fournie par
l'appelant. Aucun coefficient biologique ou de gameplay n'est caché ici.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol


PhysicalLoadClass = Literal["none", "light", "moderate", "vigorous"]
PhysiologyState = Literal["wake", "rest", "sleep"]
_LOAD_CLASSES = frozenset({"none", "light", "moderate", "vigorous"})
_RECOVERY_STATES = frozenset({"rest", "sleep"})
_DENOMINATOR_SECONDS_PER_HOUR = 3600


class PhysicalCapacityError(ValueError):
    """Contrat P invalide, sans effet de bord."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class PhysicalCapacityPolicyLike(Protocol):
    activity_cost_per_hour_milli: Mapping[str, int]
    minimum_capacity_milli: Mapping[str, int]
    traversal_cost_per_edge_milli: int
    recovery_per_hour_milli: Mapping[str, int]


@dataclass(frozen=True)
class PhysicalRequest:
    """Demande pure de faisabilité physique.

    Pour ``activity``, ``physical_load_class`` est obligatoire et le résultat
    expose un débit temporel. Pour ``traversal``, ``edge_count`` est obligatoire
    et le résultat expose un coût discret. Les deux unités ne sont jamais
    fusionnées dans un même champ.
    """

    operation: Literal["activity", "traversal"]
    physical_load_class: PhysicalLoadClass | None = None
    edge_count: int | None = None

    def __post_init__(self) -> None:
        if self.operation == "activity":
            if self.physical_load_class not in _LOAD_CLASSES or self.edge_count is not None:
                raise PhysicalCapacityError(
                    "demande d'activité physique invalide", code="invalid_physical_request"
                )
            return
        if self.operation == "traversal":
            if self.physical_load_class is not None or isinstance(self.edge_count, bool) \
                    or not isinstance(self.edge_count, int) or self.edge_count < 1:
                raise PhysicalCapacityError(
                    "demande de traversée physique invalide", code="invalid_physical_request"
                )
            return
        raise PhysicalCapacityError("opération physique invalide", code="invalid_physical_request")


@dataclass(frozen=True)
class PhysicalEvaluation:
    feasible: bool
    required_capacity_milli: int
    activity_rate_milli_per_hour: int | None
    traversal_cost_milli: int | None
    reason_code: Literal["physical_capacity_ok", "physical_capacity_insufficient"]


def _capacity(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100_000:
        raise PhysicalCapacityError("capacité physique invalide", code="invalid_physical_capacity")
    return value


def _policy_value(mapping: Mapping[str, int], key: str, *, field: str) -> int:
    try:
        value = mapping[key]
    except (KeyError, TypeError) as exc:
        raise PhysicalCapacityError(f"{field} absent", code="invalid_physical_policy") from exc
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PhysicalCapacityError(f"{field} invalide", code="invalid_physical_policy")
    return value


def evaluate_physical_request(
    policy: PhysicalCapacityPolicyLike,
    request: PhysicalRequest,
    *,
    capacity_milli: Any,
) -> PhysicalEvaluation:
    """Évalue un seuil P sans muter l'état ni consulter le legacy."""

    capacity = _capacity(capacity_milli)
    if request.operation == "activity":
        assert request.physical_load_class is not None
        load = request.physical_load_class
        required = _policy_value(
            policy.minimum_capacity_milli, load, field="seuil de capacité d'activité"
        )
        activity_rate = _policy_value(
            policy.activity_cost_per_hour_milli, load, field="débit de capacité d'activité"
        )
        traversal_cost = None
    else:
        assert request.edge_count is not None
        per_edge = policy.traversal_cost_per_edge_milli
        if isinstance(per_edge, bool) or not isinstance(per_edge, int) or per_edge < 0:
            raise PhysicalCapacityError(
                "coût de traversée invalide", code="invalid_physical_policy"
            )
        required = per_edge * request.edge_count
        activity_rate = None
        traversal_cost = required
    feasible = capacity >= required
    return PhysicalEvaluation(
        feasible=feasible,
        required_capacity_milli=required,
        activity_rate_milli_per_hour=activity_rate,
        traversal_cost_milli=traversal_cost,
        reason_code=(
            "physical_capacity_ok" if feasible else "physical_capacity_insufficient"
        ),
    )


def capacity_rate_milli_per_hour(
    policy: PhysicalCapacityPolicyLike,
    *,
    state: PhysiologyState,
    physical_load_class: PhysicalLoadClass,
) -> int:
    """Retourne le débit signé de P pour un segment causal constant.

    ``rest`` et ``sleep`` sont des régimes de récupération versionnés. Toute
    veille utilise la classe physique objective de l'activité courante ; une
    absence d'activité se représente par ``none``.
    """

    if state not in {"wake", "rest", "sleep"}:
        raise PhysicalCapacityError("état physiologique invalide", code="invalid_physical_regime")
    if physical_load_class not in _LOAD_CLASSES:
        raise PhysicalCapacityError("classe physique invalide", code="invalid_physical_regime")
    if state in _RECOVERY_STATES:
        return _policy_value(
            policy.recovery_per_hour_milli, state, field=f"récupération {state}"
        )
    return -_policy_value(
        policy.activity_cost_per_hour_milli,
        physical_load_class,
        field="débit de capacité d'activité",
    )


def advance_physical_capacity(
    policy: PhysicalCapacityPolicyLike,
    *,
    capacity_milli: Any,
    rate_remainder: Any,
    state: PhysiologyState,
    physical_load_class: PhysicalLoadClass,
    duration_seconds: Any,
) -> tuple[int, int]:
    """Avance P exactement en milli-unités et conserve le reste rationnel.

    La représentation utilise un dénominateur de 3600 s/h. Elle est stable au
    partitionnement : découper le même segment causal en plusieurs appels donne
    le même P et le même reste. Une saturation à 0 ou 100000 remet le reste à
    zéro afin de ne pas conserver une dette/créance numérique au-delà d'une
    borne physique.
    """

    capacity = _capacity(capacity_milli)
    if isinstance(rate_remainder, bool) or not isinstance(rate_remainder, int) \
            or not 0 <= rate_remainder < _DENOMINATOR_SECONDS_PER_HOUR:
        raise PhysicalCapacityError("reste de capacité invalide", code="invalid_capacity_remainder")
    if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, int) \
            or duration_seconds < 0:
        raise PhysicalCapacityError("durée physique invalide", code="invalid_physical_duration")
    if duration_seconds == 0:
        return capacity, rate_remainder

    rate = capacity_rate_milli_per_hour(
        policy, state=state, physical_load_class=physical_load_class
    )
    numerator = rate * duration_seconds + rate_remainder
    delta, remainder = divmod(numerator, _DENOMINATOR_SECONDS_PER_HOUR)
    next_capacity = capacity + delta
    if next_capacity <= 0:
        return 0, 0
    if next_capacity >= 100_000:
        return 100_000, 0
    return next_capacity, remainder


def apply_traversal_cost(
    policy: PhysicalCapacityPolicyLike,
    *,
    capacity_milli: Any,
    edge_count: Any,
) -> int:
    """Applique un coût discret après validation d'une traversée réussie."""

    capacity = _capacity(capacity_milli)
    request = PhysicalRequest("traversal", edge_count=edge_count)
    evaluation = evaluate_physical_request(policy, request, capacity_milli=capacity)
    if not evaluation.feasible or evaluation.traversal_cost_milli is None:
        raise PhysicalCapacityError(
            "capacité physique insuffisante", code="physical_capacity_insufficient"
        )
    return capacity - evaluation.traversal_cost_milli
