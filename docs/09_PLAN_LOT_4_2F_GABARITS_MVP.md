# Lot 4.2F — Gabarits du casting MVP

**Statut :** terminé et vérifié le 5 août 2026

Les cinq gabarits v1 sont installables sans instancier de monde :
`resident.sophie`, `resident.erika`, `resident.luna`, `resident.chuu` et
`resident.patoune`.

Ils sont liés aux composants v1 précis et aux données de conception de
`docs/08_CASTING_MVP.md`. Les gabarits sont atomiques et idempotents; une
version personnelle ultérieure ne réécrit pas leur version 1.

Chuu porte `physiology.resource_dependent_state` avec la ressource
`hydration`. Ce contrat annonce une future règle canonique; il ne simule encore
ni la déshydratation, ni une baisse effective de cognition. Cette limite est
intentionnelle et doit être levée avant son instanciation réelle.

**Validation :** 455 tests complets réussis.
