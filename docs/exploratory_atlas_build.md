# Exploratory Evidence Atlas Build

**Build date:** 2026-10-31  
**Mode:** maximum candidate-data visibility; exploratory, not an approval or evidence-validation run.

The four-tab Streamlit app is now an exploratory atlas over the seed and `data/candidate_2026-10-31/` CSVs. Review state, access, age scope, metadata completeness, and stored alignment do not gate display. Raw CSV rows remain available in the linked-layer tables; the source overview also reports exact-ID/URL duplicates rather than treating them as silent losses.

## Current inventory

| Inventory measure | Count |
|---|---:|
| Loaded CSV files | 25 (12 seed, 13 candidate) |
| Seed CSV rows | 666 |
| Candidate CSV rows | 355 |
| Raw source rows | 38 |
| Unique displayed documents after source-ID / URL deduplication | 37 |
| Distinct source families | 34 |
| Data-product rows | 17 |
| View B measures | 129 (43 indicators, 85 variables, 1 observation without a linked measure row) |
| View B claims | 20 (core claim, 4 pilot targets, 4 memo cases, 11 source-stated gap claims) |
| View B cells | 2,580 (20 × 129) |
| View C data-product/document rows | 37 |
| View C graph nodes / documented edges | 468 / 262 |
| Extra/unparsed CSV rows | 0 |

One source URL duplicate is preserved in the duplicate report and raw source layer. The unique-document display contains 37 items from 38 source rows. Multi-topic parent counts may be non-additive.

## Visual layers

### README

- Presents the fixed project scope, all loaded CSV row counts, candidate presence, provenance labels, and data-universe KPIs.
- Shows the fixed exploratory relevance components and weights read-only.
- Separates the configured `proxy_mismatch` formula in `config/measures.yaml` from exploratory relevance; that configured formula is not applied to the relevance matrix or inventory counts.

### View A — Topic Inventory

- Keeps the parent × observation-time heatmap and switches its single counting unit among documents, data products, indicators, variables, and observations; the entity types are never added together.
- Adds all-included-by-default filters for search, Layer A parent, observation time, publication time, substance, age/population, geography, source type, access, review, and operational box. The reset control restores the complete inventory.
- Keeps observation time separate from publication time and routes unknown observation time to its own heatmap bin.
- Adds an optional per-parent observed-year count view. Each topic has a separate subplot; no curve is smoothed across nominal topic categories.
- Adds an optional semantic evidence landscape: word-level TF-IDF, deterministic PCA, and density contours calculated only in that text-projection space. Document, measure, and claim points expose source provenance on hover. The coordinates are not geographic or temporal.
- Makes source documents, products, indicators, variables, observations, gap claims, alignments, barriers, mappings, search runs, and search candidates inspectable as separate layers.

### View B — Claim & Measure Audit

- Includes source-stated gap claims and the full indicator/variable/observation-only measure universe, not only measures referenced by stored alignments.
- Every one of the 2,580 claim × measure cells is filled by either the `RULE_DERIVED` exploratory relevance score or an exact stored alignment/display state. The user can switch between those layers.
- Fixed provisional relevance components and weights:

  | Component | Weight |
  |---|---:|
  | Concept / definition text | 0.25 |
  | Layer A topic overlap | 0.15 |
  | Substance compatibility | 0.15 |
  | Population overlap | 0.15 |
  | Outcome / construct overlap | 0.15 |
  | Observation-period compatibility | 0.05 |
  | Unit / denominator / method compatibility | 0.05 |
  | Geography compatibility | 0.05 |

- `R(c,m)` is the weighted mean over known components. `C(c,m)` is the sum of weights for known components. Text overlap is lexical/Jaccard; age and date compatibility use recorded intervals; substance compatibility uses explicit categories; geography uses recorded geography and source context. Unknown inputs reduce coverage and never remove a cell.
- `R` is a navigation aid only. It never writes or promotes a stored alignment. Exact stored classes stay visible independently, including mixed stored classes on a single cell.

| Display state | Cells |
|---|---:|
| DIRECT_MATCH | 3 |
| HARMONIZABLE | 0 |
| PROXY | 2 |
| CONCEPTUALLY_RELATED | 3 |
| INCOMPATIBLE | 6 |
| UNKNOWN_REQUIRES_REVIEW | 2 |
| NOT_ASSESSED (display-only) | 2,563 |
| NOT_APPLICABLE | 0 |
| MULTIPLE_STORED (display aggregate; underlying classes retained) | 1 |

The one `MULTIPLE_STORED` display cell retains its two underlying stored classes (`DIRECT_MATCH` and `PROXY`) in the cell provenance.

### View C — Data Production Flow

- Shows the source/product/indicator/variable/observation lineage alongside source-recorded roles: funder, collector, producer, indicator authority, custodian, reporting recipient, and access authority.
- Draws only explicit source/product/measure links and non-unknown role values with an evidence reference. Every visible edge has a relationship type and reference in hover and the edge table.
- Uses a deterministic force-directed graph layout (`networkx.spring_layout`, seed 2026, 24 iterations). Layout coordinates are not geography.
- Unknown role slots are visible as disconnected nodes; they create no relationship. The candidate input contains no stored model-suggested production edges, so none are fabricated.

## Fixed guardrails and data handling

- Four main tabs: README, View A, View B, View C. The prior page-list sidebar remains hidden.
- `data/preview/` and `data/candidate_2026-10-31/` are read-only inputs. No CSV, approved database, or tensor was modified by the app.
- All source and measure rows remain visible regardless of age, geography, access, review, or directness.
- Existing WENDU, OCIndex/PREVENTION, Kush, GYTS, and DLEAG–UNDP interpretation guardrails remain visible in View B.
- Unknown values remain explicit. National observations are not replicated into subnational areas.
- Candidate records retain their input review labels; this build does not approve or reject any record.

## Validation

- `python -m py_compile app/app.py app/v1_views.py`: passed.
- Streamlit `AppTest`: 4 tabs, 5 chart elements, 15 data tables, no app exceptions.
- Local browser on `127.0.0.1:8767`: HTTP 200; README and all three views rendered; the four tab labels were confirmed.
- Screenshot previews of README, View A, View B, and View C were captured during browser validation.
- Full pytest suite was not run for this visualization-focused build.

## Runtime requirement

The app uses Streamlit's `width="stretch"` API, so the minimum Streamlit dependency is now 1.50. No new visualization package was added; the semantic projection uses NumPy and the network uses the existing NetworkX dependency.
