"""Preuves de provenance du code réellement chargé par un runtime officiel."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Any

import vivarium


class RuntimeProvenanceError(RuntimeError):
    """Une preuve de checkout ou de référence produit est absente ou incohérente."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RuntimeProvenance:
    product_head: str
    runtime_head: str
    python_package_root: str
    checkout_root: str
    expected_checkout_root: str
    expected_runtime_head: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "PRODUCT_HEAD": self.product_head,
            "RUNTIME_HEAD": self.runtime_head,
            "PYTHON_PACKAGE_ROOT": self.python_package_root,
            "CHECKOUT_ROOT": self.checkout_root,
            "EXPECTED_CHECKOUT_ROOT": self.expected_checkout_root,
            "EXPECTED_RUNTIME_HEAD": self.expected_runtime_head,
        }


def _git(checkout_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout_root), *args],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeProvenanceError(
            f"preuve Git indisponible pour {checkout_root}: {exc}",
            code="git_provenance_unavailable",
        ) from exc
    return result.stdout.strip()


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.realpath(left)) == os.path.normcase(os.path.realpath(right))


def verify_runtime_provenance(
    *, expected_checkout_root: Path,
    expected_runtime_head: str,
    expected_product_head: str | None = None,
) -> RuntimeProvenance:
    """Vérifie le package importé, son worktree, son HEAD et product/current.

    La preuve ne dépend ni du cwd ni de la branche courante : elle part du
    chemin du module Python effectivement importé, puis interroge Git depuis
    cette racine.
    """
    expected_root = Path(expected_checkout_root).resolve()
    package_root = Path(vivarium.__file__).resolve().parent
    actual_root = package_root.parent.parent
    if not _same_path(package_root, expected_root / "src" / "vivarium"):
        raise RuntimeProvenanceError(
            "le package vivarium importé ne provient pas du checkout attendu",
            code="python_package_root_mismatch",
        )
    checkout = Path(_git(actual_root, "rev-parse", "--show-toplevel")).resolve()
    if not _same_path(checkout, expected_root):
        raise RuntimeProvenanceError(
            "la racine Git du package importé diffère du checkout attendu",
            code="git_checkout_root_mismatch",
        )
    runtime_head = _git(checkout, "rev-parse", "HEAD")
    if runtime_head != expected_runtime_head:
        raise RuntimeProvenanceError(
            f"RUNTIME_HEAD inattendu: {runtime_head} != {expected_runtime_head}",
            code="runtime_head_mismatch",
        )
    try:
        product_head = _git(checkout, "rev-parse", "origin/product/current")
    except RuntimeProvenanceError as exc:
        raise RuntimeProvenanceError(
            "origin/product/current est introuvable ou illisible",
            code="product_head_unavailable",
        ) from exc
    if expected_product_head is not None and product_head != expected_product_head:
        raise RuntimeProvenanceError(
            f"PRODUCT_HEAD inattendu: {product_head} != {expected_product_head}",
            code="product_head_mismatch",
        )
    return RuntimeProvenance(
        product_head=product_head,
        runtime_head=runtime_head,
        python_package_root=str(package_root),
        checkout_root=str(checkout),
        expected_checkout_root=str(expected_root),
        expected_runtime_head=expected_runtime_head,
    )
