# Gambia Evidence Gap Explorer

A local Streamlit prototype for recording research sources and comparing measurement concepts. It stores sources, data products, indicators, variables, observations, gap claims, alignments, barriers, searches and formula configurations in a shared SQLite registry. **The present heatmap cells are not yet generated from one shared batch of approved evidence records**; see the acceptance audit below. All bundled measurement fixtures and target concepts are marked **SYNTHETIC** and are not findings about The Gambia. The app does not require an LLM key.

## Setup and verification (Windows PowerShell)

Run these commands in order from the repository root. In this Windows session, bare `python.exe` could not launch before the virtual environment existed, so the venv was created with `& 'C:\Users\Dell\.local\bin\python3.14.exe' -m venv .venv`. After activation, `python` resolved to `.venv\Scripts\python.exe` normally. If your PATH `python` works, use the first command below; otherwise use the local Python executable above.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/validate_data.py --input data/demo/example.csv
python scripts/rebuild_tensor.py
pytest -q
streamlit run app/app.py
```

`validate_data.py` reports valid candidate rows. To write those rows as source records, pass `--import-valid`; this currently creates source records directly and does not create linked data products or put them in a review queue. `rebuild_tensor.py` regenerates `data/tensor.json` from saved alignments. The Streamlit prototype has Overview plus five functional navigation pages: Evidence gap map, Proxy alignment map, Source registry, Formula settings, and Research tasks.

## Pages and current behavior

- **Evidence gap map** — matrix with target indicators on Y and population groups on X; cells stay `NOT_SEARCHED_OR_UNKNOWN` until scope and evidence are reviewed. Geography and observation-period filters are disabled because no geocoded observations or scoped measurements are present. There is no polygon map yet.
- **Proxy alignment map** — target concepts on Y and observed measures on X when a saved alignment exists. The bundled account-count, account-holder, and previous-12-month-savings concepts are distinct synthetic catalog fixtures. With no saved alignment rows, the matrix is empty and explicitly says relationships are unknown; the UI does not invent a cross-product of pairings.
- **Source registry** — lists formal sources separately from search candidates pending human review. Stable IDs, DOI/URL and search-run IDs provide basic provenance. DOI/URL/title duplicates are collapsed by the search adapter before insertion; the interface does not show suppressed-duplicate counts or source-lineage decisions.
- **Formula settings** — edits weights and allows saving a named formula version only when weights sum to 100% and a rationale is supplied. A missing component remains `None` in formula calculations. Saved settings are in SQLite; formula-run snapshots are not yet wired to the interface.
- **Research tasks** — creates draft tasks and offers Markdown and JSON downloads.

The Overview is a sixth navigation item, separate from the five work pages.

Edit `config/project.yaml` for project scope and providers, `config/taxonomy.yaml` for controlled terms, `config/comparability_rules.yaml` for comparisons, and `config/measures.yaml` for formula defaults. `data/imports/` is local staging and ignored by Git. Check source terms and access permissions before storing or sharing imported material; see `docs/access_ethics.md`.

## Matrix semantics and statuses

The intended View A matrix axes follow the spec: X = population group; Y = evidence domain/target indicator. Geographic mode must use only observations at their recorded level. A national observation must never be copied into a region or district. Geographic mode is not implemented in this prototype; its controls are disabled. View B uses X = observed indicator/variable and Y = target concept.

View A gap states:

`NOT_SEARCHED_OR_UNKNOWN`, `SEARCH_INCOMPLETE`, `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`, `INDIRECT_OR_NOT_COMPARABLE_EVIDENCE`, `DIRECT_EVIDENCE_FOUND`, `MULTIPLE_INDEPENDENT_DIRECT_SOURCES`, `RESTRICTED_ACCESS`, `OUTDATED_OR_TEMPORALLY_MISMATCHED`, `INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION`.

View B alignment classes:

`DIRECT_MATCH`, `HARMONIZABLE`, `PROXY`, `CONCEPTUALLY_RELATED`, `INCOMPATIBLE`, `UNKNOWN_REQUIRES_REVIEW`.

The state helper and tests distinguish `NOT_SEARCHED_OR_UNKNOWN` from `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`; a search with five metadata candidates does not establish that the target evidence search is complete. Account count, account holders, and saved in the prior 12 months retain separate names and units. No observations are bundled.

## Layers, provenance and extraction

The matrices use the atlas palette: chart background `#0B1016`, lower problem teal, middle amber, higher rust, and neutral grey with the text label `UNKNOWN`. Map land (`#17222C`) and water (`#0A1119`) tokens are reserved; no geographic polygons are currently rendered. Both legends state direction semantics, but this prototype draws no vectors. Therefore arrow thickness/length are not currently visible; intended semantics are documented in `docs/visual_semantics.md`. Wind controls are disabled because there are no documented directional links or map coordinates. Friction is not rendered and has no interactive barrier detail drawer yet.

The Source registry shows stable source/candidate IDs, DOI/URL and search-run IDs. Duplicate DOI/URL/title candidates are removed before the review queue; suppressed entries and citation lineage are not currently inspectable in the UI. Search output is stored in `search_candidates` with `PENDING_HUMAN_REVIEW`, separate from formal sources.

**LLM extraction is not implemented.** The environment variables in `.env.example` are placeholders only; no provider adapter, extraction flow, or LLM review queue is connected. Metadata search is ordinary Crossref/OpenAlex API discovery and does not call an LLM.

## One real metadata search (2026-10-22)

- Provider: Crossref
- Query: `The Gambia savings account household survey`
- Requested maximum / returned: 5 / 5 metadata candidates
- Result: candidates are in `data/registry.sqlite` under `PENDING_HUMAN_REVIEW`; none were promoted to formal sources or used as evidence.
- Limitation: one short metadata query against Crossref only; no title/full-text screening, coverage assessment, OpenAlex search, source validation, or measurement review. Search results and zero-result searches cannot prove that evidence exists or does not exist.

## Verification and acceptance walkthrough (2026-10-22)

Commands run after installing dependencies in `.venv`:

| Step | Result |
|---|---|
| Dependency installation | Passed after environment correction and network approval. Bare PATH `python.exe` was blocked; Python 3.14.6 created `.venv`; `.venv\Scripts\python.exe -m pip install -e ".[dev]"` installed the editable project and dependencies. Initial sandbox attempt failed with PyPI `WinError 10013`; approved retry succeeded. |
| `python scripts/validate_data.py --input data/demo/example.csv` | Passed; `Valid candidate rows: 3`, exit 0. |
| `python scripts/rebuild_tensor.py` | Passed; `Tensor rebuilt deterministically from registry: 0 alignment records`, exit 0. |
| `pytest -q` | Passed after final code edits; **15 passed in 0.13s**, exit 0. |
| `streamlit run app/app.py --server.headless true --server.port 8765` | Final server started at `http://localhost:8765` (2026-10-22 12:05 EDT); HTTP 200. |
| Streamlit `AppTest` | Overview and all five work pages passed with no app exceptions. A task form smoke check showed Markdown and JSON downloads after submit; a 99% formula scenario disabled Save. |
| Crossref search | `The Gambia savings account household survey`, requested 5, returned 5 on 2026-10-22; all pending human review, none promoted. |

Additional requested workflow check: Research task Markdown and JSON exports **PASS (UI smoke)** — AppTest submitted a temporary task and both download controls appeared; the temporary row was removed.

§14 walkthrough evidence and gaps:

| Acceptance item | Status / evidence |
|---|---|
| Starts without an LLM key | **PASS** — Streamlit AppTest ran with no LLM environment variables. |
| Sample CSV enters canonical model | **PARTIAL** — validator accepted 3 rows; `--import-valid` writes source rows only, without linked products/variables or a review stage. |
| Separate source/product/indicator/variable/observation/gap/alignment entities | **PASS (schema)** — separate SQLite tables in `src/evidence_gap/database.py`; the demo has no observations. |
| Same approved records generate both heatmaps | **FAIL** — View B now renders only recorded alignment rows, but View A still uses an unsearched target/population status matrix rather than a shared batch of approved evidence records. |
| National data never become subnational observations | **PASS (guard by omission)** — no geographic projection/imputation exists; `Observation.geography_level` is retained. No dedicated transform pipeline is implemented. |
| Not searched differs from searched/no direct evidence | **PASS (logic/test)** — `tests/test_gap_states.py`; statuses remain distinct. The one metadata search does not mark target cells searched-complete. |
| Microdata catalog can describe variables without person records | **PASS (metadata helper/schema)** — `micro_variables.describe_variable`; no person-level observation fixture is stored. |
| Macro series records producer/collector/method/frequency/level/unit/definition | **PARTIAL** — `macro_series.validate_series_metadata` checks these fields, but no macro-series persistence table/UI exists. |
| Every extracted claim has provenance and review status | **FAIL / N/A** — LLM extraction is not implemented. |
| Repeated citation chains do not count as independent evidence | **PARTIAL** — `tests/test_search_deduplication.py` covers duplicate DOI; cross-DOI shared-source lineage and reviewer decisions are not implemented. |
| Formula run stores version/weights/components/snapshot/time | **PARTIAL** — `formulas.record_formula_run` produces these fields; the UI does not create formula runs. Formula configurations can be saved by version. |
| Invalid weight sums cannot be saved | **PASS (core + UI check)** — `tests/test_formula_versions.py`; AppTest changed weights to 99% and confirmed the Save button was disabled. |
| Unknown components are not zero | **PASS (core test)** — formula returns `None` for missing inputs in `tests/test_formula_versions.py`; UI does not yet show component results. |
| Vector directions | **PARTIAL** — `tests/test_vectors_wind_resistance.py` checks direction helpers; arrows are not drawn. |
| Arrow width/length legends | **FAIL** — intended semantics are stated in the legend/docs, but no vector renderer or measured widths exist. |
| Wind unavailable without suitable data | **PASS (logic)** — `tests/test_vectors_wind_resistance.py`; controls are disabled and explain missing relations/coordinates. |
| Friction links to typed barriers/evidence/review | **FAIL** — barrier schema/helper exist; interactive barrier details are not implemented. |
| Synthetic demo separated from real outputs | **PARTIAL** — fixtures and pages show `SYNTHETIC`; search candidates are separate from sources. There is no general export-layer synthetic exclusion mechanism. |
| Tests cover required areas | **PARTIAL** — 15 tests pass, covering schemas, provenance, duplicate DOI, gap states, formula validation, tensor projections, country scope, task export helpers, wind gating and synthetic labels. Several missing UI features cannot yet be tested. |
| README permissions/configuration/reproduction limitations | **PASS (document review)** — setup, config paths, access/ethics, search limits and implementation gaps are documented here and in `docs/access_ethics.md`. |

## Design division audit

**Chart layer:** `app/components/dark_atlas.py` uses chart background `#0B1016`, vector/text off-white `#E8EEF2`, muted teal `#4B918C`, amber `#B58B48`, rust `#A34D42`, and neutral grey `#454B50`. Current matrix cells render neutral grey with a literal `UNKNOWN` label. Hatching is not implemented. Land `#17222C` and water `#0A1119` are reserved because no polygon map is rendered. No arrows are drawn, although the vector token and direction text are defined. Both heatmap pages render a legend. These map/vector/pattern gaps remain; the chart colors were not replaced with the interface’s monochrome palette.

**Interface layer:** source inspection confirms black `#050505` app background, white text, Georgia serif headings/body, 10px Courier New metadata, left alignment, 900px left-aligned edit pages, full-width chart pages, and left-column details on heatmap pages. Navigation radio markers are hidden to present plain text choices. Inputs use dark fills and bottom rules with white focus rules; buttons are square and text-led. No gradients, stock photos, rounded card grid, or decorative chart overlays are used. AppTest checks rendering/navigation, not pixel-level appearance.

During this audit, the evidence map's placeholder mid-scale fill was replaced with neutral `UNKNOWN` cells, the matrix axes were corrected to population group × target, unsupported map/time filters and vector/friction/wind controls were disabled with reasons, and source details were moved to the heatmap pages' left column. A Streamlit import collision was fixed so the page checks could run. Remaining chart deviations are the absent map, hatching, vector and interactive friction layers noted above.

## Remaining limits and research decisions

The app is a prototype, not an evidence-gap finding. Missing functionality is listed above; in particular, LLM extraction, geographic maps, heatmaps populated from one shared set of approved records, vector rendering, interactive barriers, formula-run UI and complete CSV entity import remain unimplemented. See `docs/decisions_log.md` for unchanged researcher decisions and `docs/after-mvp.md` for future directions. Access rules and data permissions are in `docs/access_ethics.md`.
