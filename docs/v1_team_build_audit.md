# V1 Team Build Audit

**Build:** one-time graph build, 2026-10-31

**Review boundary:** display and counting only. Human assessment and approval are deferred to a later run after the user says the graph looks OK. Nothing was approved, promoted, or written to the approved database or tensor.

## Navigation

The prior sidebar page radio was retired from the app entry point. The only top-level navigation is:

1. README
2. View A
3. View B
4. View C

The existing page modules remain in the repository but are not exposed by the V1 app navigation.

## CSV inventory used

The app reads the CSVs directly from `data/preview/` and `data/candidate_2026-10-31/`. It does not call the legacy batch loader, approved database, or tensor builder.

Seed CSVs used (row counts):

| CSV | Rows |
|---|---:|
| `alignments.csv` | 50 |
| `barriers.csv` | 10 |
| `concept_boxes.csv` | 62 |
| `data_products.csv` | 14 |
| `gap_claims.csv` | 10 |
| `indicators.csv` | 36 |
| `mapping.csv` | 333 |
| `observations.csv` | 20 |
| `search_candidates.csv` | 33 |
| `search_runs.csv` | 38 |
| `sources.csv` | 33 |
| `variables.csv` | 27 |

No seed `data_production_audit.csv` exists; seed producer, collector, and funder values are taken from the seed source/product rows when present.

Candidate CSVs used (row counts):

| CSV | Rows |
|---|---:|
| `alignments (1).csv` | 15 |
| `barriers (1).csv` | 3 |
| `concept_boxes (1).csv` | 1 |
| `data_production_audit.csv` | 5 |
| `data_products (1).csv` | 3 |
| `gap_claims (1).csv` | 1 |
| `indicators (1).csv` | 7 |
| `mapping (1).csv` | 182 |
| `observations (1).csv` | 15 |
| `search_candidates (1).csv` | 15 |
| `search_runs (1).csv` | 45 |
| `sources (1).csv` | 5 |
| `variables (1).csv` | 58 |

All five provisional candidate source IDs (`LLM_CAND_SOURCE_0001` through `LLM_CAND_SOURCE_0005`) remain unchanged. The source merge found one exact URL duplicate: seed `S010` shares its URL with seed `S009`; it is reported as a duplicate alias, not silently discarded. No seed row was overwritten.

## Documentary inventory

- Unique documentary items after source-ID then URL deduplication: **37** (38 raw source rows).
- Unique source families: **34** (`source_family_id`, falling back to `source_id`).
- Distinct data products: **17** (unique `(source_id, data_product_id)` pairs).
- Counts are unweighted. A multi-topic item contributes once to the global document total and to each explicitly mapped parent, so parent totals are non-additive.
- Source-frame totals are not exhaustive; logged search activity is bounded.

### View A documents by Layer A parent and observation-time bin

The 10 parent labels come from the seed concept-box records, including the conditional A09 parent. The unmapped lane is separate. Publication time was not substituted for observation time.

| Layer A parent | 2010-2014 | 2015-2019 | 2020-2022 | 2023-2026 | Observation period unknown |
|---|---:|---:|---:|---:|---:|
| substance-specific use | 0 | 6 | 0 | 3 | 4 |
| health outcomes/harms | 0 | 0 | 0 | 1 | 1 |
| treatment/service access | 0 | 1 | 1 | 2 | 0 |
| prevention policies | 0 | 2 | 0 | 2 | 2 |
| programme delivery/reach/participation/dose | 0 | 0 | 0 | 2 | 1 |
| post-participation outcomes | 0 | 1 | 0 | 2 | 1 |
| enforcement/supply | 0 | 0 | 0 | 3 | 2 |
| social/livelihood/risk factors | 0 | 0 | 0 | 0 | 1 |
| cross-border/illicit finance (only if actually measured) | 0 | 0 | 0 | 0 | 0 |
| data production/governance/access | 1 | 4 | 0 | 12 | 6 |
| UNMAPPED / REVIEW_REQUIRED | 0 | 0 | 0 | 0 | 1 |

## View B claim and measure audit

The rows comprise the core under-18 causal claim, existing targets I009/I013/I014/I015, and four TEAM_CANDIDATE memo cases (GYTS, WENDU, Jallow, and DLEAG-UNDP). The X lineage includes **85** variable rows (27 seed + 58 candidate), whether or not an alignment exists. The display has **9 × 85 = 765** claim-measure cells.

| Cell state | Display cells |
|---|---:|
| DIRECT_MATCH | 3 |
| HARMONIZABLE | 0 |
| PROXY | 3 |
| CONCEPTUALLY_RELATED | 3 |
| INCOMPATIBLE | 6 |
| UNKNOWN_REQUIRES_REVIEW | 2 |
| NOT_ASSESSED (display-only) | 748 |
| NOT_APPLICABLE | 0 |

There are 65 stored alignment rows in the input CSVs (50 seed + 15 candidate). Display states are assigned only when an exact stored claim/target and observed-variable identifier can be matched; explicitly present variable IDs in alignment labels are parsed as IDs, not inferred from text similarity. Rows not joinable to a visible variable or not belonging to the displayed claims are not paired by topic or keyword. No alignment class was promoted. `NOT_ASSESSED` and `NOT_APPLICABLE` are display states only and are not written to alignment storage.

The previous proxy matrix depended on reviewed database/tensor relations and did not expose this full candidate variable lineage. All **85** lineage variables are now available in the table. Within the merged input, **71** have no exact stored alignment reference and therefore would not have appeared as relation-backed measures. Documents without linked variables remain in a separate contextual-document group, not as observed-variable columns.

Literal guardrails are rendered in View B: WENDU NIL values remain text; the age x region and substance tables are not joined; OCIndex criminality and PREVENTION resilience scales are not compared; Kush is not equated with cannabis or a synthetic-index item; GYTS remains tobacco-only for school-going ages 13-15; and the DLEAG-UNDP launch is existence evidence only.

## View C production roles and joins

View C contains **37** data-product/document rows. Role values are preserved verbatim and never inferred from prominence. Exact `UNKNOWN`, `N/A`, or `NOT RECORDED` values count as unknown; partially specified text is retained as documented text.

| Role | Documented text | UNKNOWN |
|---|---:|---:|
| funder | 25 | 12 |
| collector | 32 | 5 |
| producer | 37 | 0 |
| indicator authority | 4 | 33 |
| custodian | 1 | 36 |

No arrows are drawn: the loaded records do not provide a complete documented relation type plus evidence reference for each proposed edge. The table still shows the five candidate data-production audit rows and seed role values where available.

### Orphan and missing joins

- **Source-to-document:** no unmatched source IDs remain after recognizing the exact URL duplicate alias `S010` → `S009`. The duplicate and affected URL are reported; `S010` was not treated as a second unique document.
- **Observation-to-variable:** one exact `(source_id, variable_id)` join is missing: `S008` / `GDHS_TOBACCO_MEN_15_19` / observation `O014`.
- **Variable-to-data-product:** 59 variables do not have one unambiguous product at source level because a variable row has no product ID or its source has zero/multiple product rows. Affected source IDs: `S003` (1 variable), `S032` (57), `S033` (1). These product joins display `UNKNOWN`; no product is guessed.
- **Alignment-to-variable:** 39 stored alignment rows have an observed reference that does not exactly match a visible variable ID/name. Affected source IDs: `LLM_CAND_SOURCE_0002`, `LLM_CAND_SOURCE_0004`, `LLM_CAND_SOURCE_0005`, `S001`, `S003`, `S004`, `S006`, `S007`, `S008`, `S009`, `S016`, `S017`, `S018`, `S019`, `S021`, `S032`, and `S033`. These may be indicator/questionnaire or free-text references; they remain unpaired rather than being converted to measures.
- **Rows without a source key:** seed counts are indicators 17, concept boxes 62, mapping 80, and search runs 1. Candidate counts are mapping 30, search runs 29, and search candidates 1. These records have `source_id=UNKNOWN` and remain unresolved rather than being attached to a source. No other child-table source IDs are orphaned.

### National-to-subnational check

No national observation was copied to an LGA or named border area. The app preserves geography text from its source or observation row and does not expand national records into subnational cells. Mixed values such as `national + regional` remain source-native.

### Candidate-status check

All **355** rows across the 13 candidate CSVs remain `CANDIDATE_PENDING_HUMAN_REVIEW`. No approval action, approved-database write, tensor rebuild, or source-status change occurred.

## Formula and weights

`config/measures.yaml` is read-only and currently configures:

- Name: `proxy_mismatch`
- Version: `1.0`
- Components: `definition_mismatch=20`, `population_mismatch=15`, `geography_mismatch=15`, `time_window_mismatch=10`, `unit_denominator_mismatch=15`, `measurement_method_mismatch=10`, `aggregation_level_mismatch=15`
- Unknown policy: `omit_score`

The README displays those actual values read-only. No user-editable source or weight controls are present. Inventory and heatmap document counts are unweighted; these weights are not applied to graph counts.

## Contour and axis-adjacency audit

No contour map or smoothing is used. Topic parents are nominal categories, not a continuous spatial or numeric field. Observation-time bins are ordered on the X axis only; that ordering does not establish adjacency between topics and is not a basis for interpolation or contouring. The matrix remains discrete.

## Unresolved human decisions

These are deferred; none is resolved by this build:

1. Review the proposed WENDU B52 box against existing B06, including the differing geography, denominator, and estimand; do not adopt B52 until human approval.
2. Review Jallow B29-B32 construct collisions and decide whether to split lifetime use, past-year use, and age-at-first-use boxes. The split remains a proposal; do not infer an under-18 subgroup from mean age.
3. Verify WENDU table transcription and decide downstream handling of source-native `NIL`; this app keeps `NIL` as text.
4. Review Jallow abstract/Figure/Table discrepancies, questionnaire wording, response universes, and observation-time uncertainty.
5. Review OCIndex criminality versus resilience scales and the use of contextual indicators; they are not prevalence or physical-flow measures.
6. Re-verify the DLEAG-UNDP launch source and assess any future roster, reach, coverage, baseline, follow-up, or comparison evidence. The current launch remains existence evidence only.
7. Assess candidate records, unaligned measures, and exact missing joins. All such records and cells remain pending or `NOT_ASSESSED`.

## Verification

- `py_compile` passed for both changed Python files.
- Streamlit on `127.0.0.1:8767` returned HTTP 200. README, View A, View B, and View C rendered; the View A heatmap, View B cell-state summary, and View C table loaded. The server was stopped after verification.
- No pytest loop was run, as instructed; pytest status remains **unresolved**.
