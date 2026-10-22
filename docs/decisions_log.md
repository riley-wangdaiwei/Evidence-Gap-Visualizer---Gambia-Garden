# Decisions requiring researcher judgment

The following items are reproduced from spec §16 and remain unresolved:

- What target concept/question is being measured.
- Which sources, populations, time periods, and geographic scales are eligible.
- What counts as direct evidence versus a proxy.
- Whether a transformation between indicators is methodologically defensible.
- Whether evidence sources are independent or repeat the same underlying observation.
- What makes an evidence cell sufficiently searched.
- Which barriers are documented versus hypothesized.
- Whether a vector relationship is empirically supported or merely suggested by the LLM.
- Which variables and weights define any optional numeric score.
- Which real data may be stored, displayed or shared under the source terms and ethics approvals.

## Verification status (2026-10-22)

One Crossref metadata query (`The Gambia savings account household survey`) returned five items. They remain `PENDING_HUMAN_REVIEW` candidates and do not resolve any decision above. No target concept, eligible source scope, proxy boundary, independence judgment, search sufficiency threshold, barrier claim, vector claim, score weight, or sharing permission was inferred from that search.

Validation notes (2026-10-22): CSV validation accepted three synthetic candidate rows; tensor rebuild read zero alignment records; pytest passed 15 tests; Streamlit HTTP returned 200 and AppTest passed Overview plus all five work pages. A 99% formula scenario disabled Save. The Crossref candidates remain pending human review. These software checks do not verify a substantive research gap.
