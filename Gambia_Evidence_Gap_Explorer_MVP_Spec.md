# Gambia Evidence Gap Explorer — MVP Product & Engineering Specification

**Purpose of this file:** Give a coding agent a complete product brief and implementation contract. The agent should turn this spec into a runnable local MVP and then provide precise CLI commands, setup instructions, tests, and a list of any remaining manual steps.

**Status:** Proposed MVP design. All default scoring coefficients and demo records are provisional. No synthetic/demo result may be presented as a real finding about The Gambia.

---

## 1. Product definition

Build a reusable evidence-discovery and measurement-gap tool. It must answer three research questions:

1. **What do we know?** What sources, datasets, indicators, and observed variables exist, who collected/produced them, how were they collected, and what exactly do they measure?
2. **What are we missing?** Which population, location, topic, indicator, or time period lacks evidence that directly answers a researcher’s question? Which publications explicitly say that evidence is missing?
3. **What should we do next?** Can existing evidence be reused as a proxy? What is lost by using it? What new data, access arrangement, harmonization, or field research would close the gap?

The MVP contains **two linked heatmap views** that use one input pipeline, one canonical data model / sparse evidence tensor, one provenance system, one visual language, and one versioned formula configuration:

- **View A — Missing Evidence Heatmap:** Where is direct, usable evidence missing, insufficient, old, geographically coarse, or still unverified?
- **View B — Proxy / Indicator Alignment Heatmap:** When the desired concept is not directly measured, which existing indicators or variables may serve as proxies, how closely do their definitions match, and what limitations arise?

Both views support the same visual layers and controls: heatmap/scalar field, discrete vectors/arrows, optional derived wind/streamline field, resistance/barrier markings, time filter, source details, and method/legend panel. The renderer must not fabricate spatial differences or real-world flows where supporting data do not exist.

### Example motivating problem

A researcher wants to measure **savings** in The Gambia. One source may report savings-account counts, another may report the number of account holders, and a household survey may ask whether a person or household saved in the previous 12 months. These are related but not identical measurements. The system must display:

- the desired target measure;
- the observed variable/series available in each source;
- who collected or reported it and how;
- the measurement unit, population, denominator, reference period, aggregation level, and geography;
- whether the evidence is directly comparable, harmonizable, a proxy, merely conceptually related, incompatible, or unknown;
- which transformation assumptions would be required and what cannot be inferred;
- any paper or report that explicitly says the desired subgroup/time/geography/measure is missing.

The same framework should later support drug evidence, youth prevention, treatment, livelihoods, remittances, or another configurable topic without rewriting the app.

---

## 2. MVP principles and non-goals

### Principles

1. **Evidence first; visualization second.** Every cell, arrow, proxy relationship, and barrier must trace to a source, a deterministic rule, an explicit model assumption, or a human review.
2. **Unknown is not zero.** `not searched`, `search incomplete`, `searched but not found`, `restricted`, and `not collected` are distinct states.
3. **Do not equate data products, indicators, and variables.** A report is a source; a macro series is a data product/series; a microdata variable is a field in a dataset; an observation is a measured value; a gap claim is a statement about missing knowledge.
4. **Preserve original definitions.** Standardized categories must never overwrite original variable names, age bands, definitions, units, and denominators.
5. **One canonical source of truth.** All entry methods feed the same validation pipeline and database.
6. **One shared measurement engine.** Formula definitions and weights are centrally configured, versioned, inspectable, and used by both views.
7. **Human-reviewable AI.** LLM output is a candidate extraction, not ground truth. The original source passage and location must be retained for every consequential claim.
8. **Use real geography only when it exists.** A country-level indicator must not be smoothed or imputed into regional/LGA variation without an explicitly justified model.
9. **No invented causal interpretation.** A vector may represent an evidence relationship, information path, or a clearly labelled simulated field. It does not automatically prove influence or causality.
10. **Research ethics and permissions.** Do not bypass paywalls or dataset access controls, or ingest identifiable/restricted microdata without authorization and appropriate safeguards.

### Not in scope for MVP

- Autonomous publication of findings without review.
- Downloading or storing restricted person-level microdata by default.
- A claim that all published or unpublished data have been found.
- ML-trained research-priority weights.
- An empirically validated physical fluid simulation of social systems.
- Persistent homology/topological analysis as a required feature.
- Automated recommendations naming specific NGOs or individuals without verified capability data.
- Real-time financial or drug-route flow claims without data.

---

## 3. Core user flow

1. A researcher chooses a **target question/indicator** (e.g., “people who saved during the last 12 months,” or “youth prevalence for a specified substance”).
2. They configure topic, geography, publication year range, observation period, population, source types, and search providers.
3. The system searches metadata/catalogs and imports user-provided PDFs, CSV/Excel files, URLs, DOIs, reports, questionnaires, codebooks, and data dictionaries.
4. All input is normalized into one common schema and placed in a review queue.
5. The LLM suggests source metadata, indicator definitions, variables, gap claims, comparability mappings, and barriers, each with provenance and uncertainty.
6. Rules and a human reviewer verify/adjust important fields.
7. The application updates the sparse evidence tensor and regenerates the two views.
8. The researcher selects a cell, source, variable, arrow, or barrier to inspect its supporting records.
9. The researcher can save a formula configuration, compare scenarios, and export a standardized research task.

---

## 4. The two heatmaps

## View A — Missing Evidence Heatmap

### Research question

**Where is sufficiently direct and usable evidence missing for the target research question?**

### Geographic mode (primary visual style)

- Render the geographic areas supported by the data (e.g., country or administrative regions) on a dark, subdued basemap.
- The fill value represents **evidence gap / lack of fit for the selected target indicator**, not the prevalence of the phenomenon itself.
- Each polygon uses only evidence valid for that geographic level. If a source is national-only, show a national-level status; do not assign that value to every LGA.
- When a location has no suitable data, display a missing/unknown treatment with a distinct pattern or neutral dark fill, depending on the search state. Never silently make it look like a measured low or high value.
- Provide a cell/polygon details drawer: direct evidence count, independent source count, year coverage, population match, method quality, data granularity, author-reported gap claims, last search date, and uncertainty/review state.

### Matrix mode (required fallback and analytical companion)

- Default X-axis: standardized population groups (preserving original age/sex definitions in detail).
- Default Y-axis: evidence domains/target indicators.
- Filters: geography, substance/topic, observation-year window, publication-year window, source type, and access status.
- Alternative axis presets may be configured, but only two dimensions should appear as axes at a time.
- Matrix cells and geographic polygons must use the same underlying evidence records and status logic.

### Heat value / state

The MVP must implement categorical states first:

- `NOT_SEARCHED_OR_UNKNOWN`
- `SEARCH_INCOMPLETE`
- `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`
- `INDIRECT_OR_NOT_COMPARABLE_EVIDENCE`
- `DIRECT_EVIDENCE_FOUND`
- `MULTIPLE_INDEPENDENT_DIRECT_SOURCES`
- `RESTRICTED_ACCESS`
- `OUTDATED_OR_TEMPORALLY_MISMATCHED`
- `INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION`

A cell may need multiple flags; do not force all distinctions into a single label. The visual fill should use a primary display state plus warning badges/patterns for additional issues.

If a numerical gap score is enabled, its components and weight configuration must be shown. Do not require a numeric score where the evidence does not support one.

### What vectors mean in View A

Vectors/arrows are **discrete research bridges** from an evidence/comparator cell toward a target gap cell. Example: existing adult data plus an explicitly sourced recommendation to study youth creates a candidate adult-evidence → youth-gap relationship.

- Arrow direction: evidence/comparator → target research question/gap.
- Arrow width/opacity: a separately defined, inspectable support-strength measure (e.g., count of independent supporting sources after deduplication, optionally adjusted by reviewer-approved reliability); never just “importance” without definition.
- Arrow label/details: relationship type, supporting source IDs/quotes, extraction/review status.
- Geometric line length on a map must not imply more evidence, more accuracy, or greater priority.
- A link inferred only from semantic similarity must be labelled `LLM_SUGGESTED`, not verified.

### What wind/streamlines mean in View A

A wind field is a **derived visualization of a documented research-connection/accessibility network**, not a claim that evidence behaves physically like fluid. It is optional and only appears when there are enough geolocated directional relations or explicit model inputs to construct it.

A candidate definition:

- Each directed relation edge `i -> j` has `bridge_strength_ij` in [0,1], derived from documented evidence and/or reviewer rating.
- Each edge has `resistance_ij` in [0,1] only when defined evidence supports a resistance assessment; otherwise it is unknown.
- Effective edge strength: `f_ij = bridge_strength_ij * accessibility_ij`, with `accessibility_ij = 1 / (1 + lambda_r * resistance_ij)` when resistance is known. If unknown, do not secretly treat it as zero; use a configured missing-resistance policy and show that the field is partially unknown.
- In a projected coordinate system, let `u_ij` be the unit direction vector from source node i to target node j and `m_ij` the edge midpoint. A smoothed display field can be computed as `v(x) = sum_ij f_ij * K_h(x - m_ij) * u_ij`, where `K_h` is a documented kernel with configurable bandwidth `h`.
- This streamline field is **model-derived**. Label it “modeled evidence-connection field,” show `h`, resistance policy, and edge set in the method panel, and allow it to be switched off.
- If there are too few meaningful geospatial relations, show a message explaining why the wind layer is unavailable. Do not synthesize attractive but unsupported wind arrows.

In matrix mode, use discrete directed connectors by default. Do not render continuous wind streamlines across categorical cells unless a specific graph-layout/field model is defined and labelled.

### What friction/resistance means in View A

Resistance represents barriers to obtaining, comparing, or transferring evidence—not the severity of the underlying social phenomenon.

Initial documented barrier types:

- `ACCESS_RESTRICTED`
- `MISSING_DISAGGREGATION`
- `DEFINITION_MISMATCH`
- `TIME_MISMATCH`
- `GEOGRAPHY_MISMATCH`
- `INCOMPATIBLE_UNIT_OR_DENOMINATOR`
- `COLLECTION_CAPACITY_CONSTRAINT`
- `LANGUAGE_OR_COMMUNICATION_BARRIER`
- `INSTITUTIONAL_COORDINATION_BARRIER`
- `UNKNOWN_BARRIER`

Display friction as restrained markers/dashes or a line pattern near the affected edge/cell. Clicking it should reveal supporting sources, why it matters, verification status, and what action may address it. A numerical resistance score is optional and requires a formula and evidence; MVP can use typed categories.

---

## View B — Proxy / Indicator Alignment Heatmap

### Research question

**When the desired measure is not directly available, which existing indicators/variables can inform it, how close are they, and what inferential information would be lost?**

### Default matrix axes

- Y-axis: target concepts / target indicators specified by the researcher (e.g., savings activity, formal savings-account ownership, savings balance; or a defined youth-use indicator).
- X-axis: observed indicators, macro series, data products, or microdata variables found in sources.
- A source may have multiple candidate variables. Show each variable/series as a separate item, grouped by data product/source.
- Filters: geography, population, observation period, source type, access status, and review status.

### Geographic mode

A geographic proxy heatmap may display proxy availability/alignment by country or subnational unit only where the candidate proxy’s geographic level supports it. The default display is a matrix because indicator alignment is inherently a relationship between measures, not necessarily a map. A map mode can be enabled for target concepts with geographically identified candidate measures.

### Heat value / relationship class

Store both a categorical class and, only where justified, a configurable mismatch score:

- `DIRECT_MATCH`: same target measurement under compatible definitions.
- `HARMONIZABLE`: difference can be addressed by a documented, defensible conversion/harmonization rule.
- `PROXY`: related measurement can inform the target but is not equivalent.
- `CONCEPTUALLY_RELATED`: useful background but not a substitute measurement.
- `INCOMPATIBLE`: cannot validly answer the target with the available information.
- `UNKNOWN_REQUIRES_REVIEW`: definitions/documentation are insufficient to judge.

The visual scale should follow one global convention: **cooler/teal = lower documented mismatch/problem; warmer/amber/red = higher mismatch/problem**. `UNKNOWN` must use a separate neutral/pattern style rather than being treated as high or low mismatch.

### Proxy mismatch formula (configurable, not automatically authoritative)

For target indicator `q` and observed variable/series `j`, define component mismatches in [0,1]:

- `definition_mismatch`
- `population_mismatch`
- `geography_mismatch`
- `time_window_mismatch`
- `unit_denominator_mismatch`
- `measurement_method_mismatch`
- `aggregation_level_mismatch`

Candidate weighted mismatch:

`M(q,j) = sum_k w_k * d_k(q,j)` where `sum_k w_k = 1`.

Rules:

- Component values require rule-based comparison, documented metadata, reviewer judgment, or an LLM suggestion that remains unverified.
- A component with insufficient documentation is `UNKNOWN`, not automatically zero. If any high-impact component is unknown, the UI should flag the overall score as provisional or omit it depending on configuration.
- Store the categorical class separately from M.
- The weights and component rules are centrally configured, versioned, visible to the user, and saved with each run.
- The MVP should never convert “account count” into “unique people who saved” unless a documented method and required inputs justify that conversion.

### What vectors mean in View B

Arrow direction: observed variable/series → target indicator, meaning “this observed measure may support/inform this target.”

- Arrow style distinguishes direct match, harmonizable measure, proxy, or conceptual link.
- Arrow width/opacity can represent validated relationship confidence/support, not physical magnitude.
- Each arrow opens its definitions, original wording, unit, denominator, reference period, source location, reviewer status, and limitations.
- An LLM-suggested connection must remain visually distinct from a reviewer-approved one.

### Wind and friction in View B

- The same renderer and layer controls are used so the product feels like one coherent atlas.
- The wind layer is a network-derived “evidence navigation” field only if there is a defined graph of relationships and valid layout coordinates. It must not imply geographic flow in an indicator matrix.
- The resistance overlay shows what blocks a candidate proxy from answering the target question: definition mismatch, missing denominator, different unit, nonmatching population, incompatible geography, outdated period, inaccessible dataset, or unverified documentation.
- If the data support only discrete links, the continuous wind layer is disabled with a clear explanation; do not manufacture a continuous vector field merely for decoration.

---

## 5. Shared visual design system

Use one rendering system for both heatmap views.

### Art direction

- Dark, cartographic, research-atlas look; restrained and legible rather than futuristic or highly animated.
- Background: near-black charcoal/navy (`#0B1016` or similar).
- Land/base polygons: deep slate (`#17222C`).
- Water/background: darker navy (`#0A1119`).
- Borders/contours: muted slate, low contrast.
- Low problem/mismatch: muted teal/blue-green.
- Medium problem: muted amber.
- High gap/mismatch: restrained rust/crimson.
- Unknown/unsearched: neutral charcoal/grey with optional hatching.
- Vectors: off-white (`#E8EEF2`), thin and directional; thicker/more opaque only when the legend says why.
- Wind streamlines: thin translucent off-white, sparse, optional, no glow trails or constant particle animation.
- Resistance: amber/rust small marks, broken lines, or short barrier ticks; avoid alarm-style badges everywhere.
- Use a consistent legend and semantic meaning in both views: warmer colors always mean a greater defined problem (gap or mismatch), not “more data.”

### Layer controls

- `Heatmap` on/off.
- `Vectors / Research Bridges` on/off.
- `Wind / Modeled Field` on/off where valid.
- `Friction / Barriers` on/off.
- `Sources and labels` on/off.
- `Time window` selection.
- `View: geographic / matrix` where meaningful.

### Static-first behavior

Default to static arrows and streamlines. Any animation must be optional and must encode time or a clear modeled process, not just visual spectacle. Respect reduced-motion settings if supported by the UI library.

### Legends are mandatory

Every map must state:
- what fill color means for the active view;
- what each arrow represents and how direction is defined;
- whether arrow thickness is observed, calculated, or reviewer-rated;
- what wind streamlines mean, with “modeled” wording when appropriate;
- what friction markers represent;
- what is unknown or not searched;
- whether observations are national, regional, household, person, institutional, or other level.

---

## 6. One unified input system

All inputs must end at the same canonical validation/review step and database. Build input adapters, not separate data silos.

### Required input methods

1. **Manual entry forms:** create/edit a source, data product, indicator, variable, observation, gap claim, proxy link, and barrier.
2. **CSV/Excel import:** support standardized templates and show row-level validation errors before import. Excel may be handled through pandas/openpyxl; do not silently coerce units or IDs.
3. **PDF/document ingestion:** accept user-provided, legally accessible reports and papers; extract text and page locations. For scanned documents, mark OCR-derived text as lower-confidence and require review for key numbers/quotes.
4. **URL/DOI entry:** retrieve accessible metadata and let the user request extraction.
5. **Search APIs:** configurable scholarly metadata providers and institutional/dataset catalogs. API results enter as candidates, not automatically verified evidence.
6. **Dataset documentation import:** questionnaires, codebooks, variable dictionaries, macro-series definitions, microdata catalog pages, and data-access metadata.
7. **Future extensions:** API connectors, direct database imports, multilingual/local-source workflows. Do not build every connector in the first sprint.

### Shared ingest pipeline

`Input adapter -> RawCandidate -> schema validation -> duplicate resolution -> normalized records -> review queue -> approved canonical records -> sparse tensor/projections -> visualizations`.

Every record must retain the raw source payload/file reference where legally permitted, source URL/DOI, extraction method, retrieval time, and review history. A generated field must be marked as AI-suggested; never make it indistinguishable from user-entered or source-verified metadata.

---

## 7. Unified data model and sparse evidence tensor

Use one canonical relational database for durable records. Build the tensor as a **sparse, indexed analytical representation** from those canonical records rather than forcing every possible combination into a dense N-dimensional array. Many combinations have no observation, and “no row” must not mean “zero value.”

### Core dimensions

- `geography`: country, admin level, region/LGA, border area, coordinates/polygon ID when reliable.
- `population`: original age range and subgroup; normalized population category where justified.
- `topic/domain`: configurable subject taxonomy.
- `target_indicator`: researcher’s desired concept and operational definition.
- `observed_indicator`: what an existing source actually measures.
- `time_period`: collection/reference period and publication period separately.
- `source/data_product`: source record, dataset/series, collector/producer, method, access status.
- `method`: survey, census, admin record, financial-provider reporting, interview, modeled estimate, review, etc.

### Logical evidence tensor

Define an analytical cell as:

`EvidenceCell[geography_id, population_id, target_indicator_id, observation_period_id]`

Each sparse cell is an object, not just a scalar. It contains:

- search status and last search run;
- matching source/data-product IDs;
- observations and observed-indicator IDs;
- directness/comparability state;
- temporal/geographic/population specificity;
- quality/uncertainty metadata where available;
- relevant gap-claim IDs;
- possible proxy-alignment IDs;
- barriers/resistance IDs;
- reviewer status and provenance.

The **Missing Evidence Heatmap** is a projection of these cells. The **Proxy Alignment Heatmap** is a projection of the relationships between each `target_indicator` and observed indicators/variables, with cells optionally linked to the same evidence cells. This is the shared tensor/model, not two independent datasets.

### Required durable entities

#### `Source`
- `source_id`
- title, authors/organization, source type, DOI/URL, publication year, language, repository/publisher
- access/license state, version, retrieval timestamp, source-location/page metadata

#### `DataProduct`
- `data_product_id`, `source_id`
- name, producing institution, data collector, reporting agency, funder if documented
- collection method and reporting process
- unit of collection (person/household/account/institution/aggregate/etc.)
- geographic coverage/resolution
- population coverage
- collection/reference period, reporting cadence, publication/update cadence
- data type (`MICRODATA`, `MACRODATA`, `ADMINISTRATIVE`, `QUALITATIVE`, `LITERATURE`, `METADATA_ONLY`, etc.)
- access level, license, citation, documentation URL

#### `IndicatorDefinition`
- `indicator_id`, preferred concept/name, domain, target/observed role
- exact definition, original label, numerator, denominator, unit, reference period
- population scope, aggregation level, geographic level
- calculation/metadata definition, compatible conversions if documented
- provenance and reviewer status

#### `MicroVariable`
- `variable_id`, `data_product_id`, original variable name, label/question wording
- response codes/categories, unit, skip logic, universe/eligible respondent
- unit of analysis (person/household/establishment/etc.)
- weights/strata/cluster metadata when documented
- data access status, codebook/questionnaire page/section
- standardized indicator mapping and mapping status

#### `MacroSeries`
- `series_id`, `data_product_id`, series code/name and official definition
- unit, population/sector covered, numerator/denominator if applicable
- frequency, reference period, country/geographic coverage
- values/flags when allowed, revisions, missing-value codes, methodology notes

#### `Observation`
- `observation_id`, `source_id`, `data_product_id`, `indicator_id`
- geography, population, period, value (nullable), unit, denominator/numerator/sample size when known
- observed/collected year, publication year, estimate vs direct measurement
- uncertainty/limitations, source page/table, verification status

#### `GapClaim`
- `gap_claim_id`, `source_id`, exact quote, page/section, publication year
- gap type (no data, underrepresented group, geographic gap, temporal gap, incompatible measures, access barrier, proposed future work, etc.)
- target topic/population/geography/period/indicator
- explicitly stated vs model-inferred
- independent-claim cluster/duplicate citation chain
- AI extraction confidence, human review status

#### `IndicatorAlignment`
- `alignment_id`, target `indicator_id`, observed `indicator_id` or `variable_id`/`series_id`
- relationship class: `DIRECT_MATCH`, `HARMONIZABLE`, `PROXY`, `CONCEPTUALLY_RELATED`, `INCOMPATIBLE`, `UNKNOWN_REQUIRES_REVIEW`
- each mismatch component and any overall mismatch score
- proposed conversion/assumptions, inferential limitations, evidence sources
- AI-suggested/reviewer-approved status, review notes

#### `ResearchBridge`
- source cell/evidence node, target cell/gap node, relationship type, supporting records
- direction semantics, relationship-strength basis, computed/display status, reviewer state

#### `Barrier`
- barrier ID/type, affected cell/edge/alignment, description, source evidence, verification state
- measured/proxy/qualitative basis, action that could address it

#### `SearchRun` and `ResearchTask`
- `SearchRun`: exact query/configuration, providers, dates, result counts, errors, scope and completeness notes.
- `ResearchTask`: question, geography/population, gap, existing evidence, proposed method, required capabilities, access/ethics constraints, deliverables, completion criteria, status.

### Tensor storage rule

Keep durable source records in normalized tables with stable IDs and many-to-many link tables. Materialize/update the sparse evidence tensor using deterministic Python functions. Do not store the only copy of the evidence in a notebook, visualization state, or LLM prompt. No downstream chart may independently reinterpret the raw records with its own hidden rules.

---

## 8. Shared formula and weight configuration

Create one `config/measures.yaml` and a shared formula engine. Both heatmaps must read the same configuration/versioning infrastructure. Different views may use different named measures, but no formula may be hard-coded inside a plotting function.

### Principles

- Weights are optional, editable, validated, and versioned.
- All weights for a weighted measure sum to 1 (or 100% in the UI).
- A saved result records formula ID/version, weights, component values, data snapshot/version, and run timestamp.
- Show each component next to the total; allow scenario comparison and sensitivity analysis.
- Unknown component values are null/unknown, never quietly converted to zero.
- Do not compare total scores across different formula versions without an explicit warning.
- Default to categorical outcomes until a numeric score has a defensible interpretation.

### Candidate measure A: evidence gap

Component examples in [0,1]: directness, population fit, geography fit, temporal fit, methodological adequacy, and evidence independence/coverage. These must be operationally defined and tested. A preliminary score might be:

`S_evidence = sum_k w_k * coverage_component_k`

`G_gap = 1 - S_evidence`

However:
- `G_gap` is only calculated when the relevant search scope is sufficiently complete and required components are known.
- If no search has been run or its scope is incomplete, status is unknown/incomplete, not `G_gap = 1`.
- Source quantity alone must not imply quality or adequacy.
- The first version may show component/status profiles instead of `G_gap` where a scalar would hide important distinctions.

### Candidate measure B: proxy mismatch

For target indicator q and observed variable/series j:

`M(q,j) = sum_k w_k * mismatch_k(q,j)`

Components (each defined in [0,1] where justifiable): indicator-definition mismatch, population mismatch, geographic mismatch, time-window mismatch, unit/denominator mismatch, collection-method mismatch, aggregation-level mismatch.

- Lower `M` means lower documented mismatch; higher `M` means greater mismatch/problem.
- Component weights are configurable and documented.
- Missing documentation is unknown, not a perfect match.
- Class label and numeric score are separately stored.
- No numeric conversion from accounts to people, participation to balance, or national to subnational values unless a defensible method and required data exist.

### Candidate measure C: relationship strength and resistance

If used, define their inputs explicitly. For example:

`effective_edge_strength = documented_bridge_strength * accessibility_factor`

`accessibility_factor = 1 / (1 + lambda_r * resistance_score)` only when resistance is numerically available and validated.

If resistance is categorical/unknown, keep the relationship categorical or show a sensitivity range rather than inventing a precise score.

### Weight editor

Build a single shared Formula Settings panel that supports:
- selecting a named measure (gap, proxy mismatch, edge/bridge strength if used);
- adjusting component weights with sliders/input fields;
- immediate validation that weights sum to 100%;
- saving named scenarios (e.g., Youth-focused, Method-quality-focused, Low-cost collection);
- entering rationale, author/reviewer, and version notes;
- comparing rankings/scores across configurations;
- exporting configuration JSON/YAML.

Do not train ML to set normative research-priority weights in the MVP. LLMs may suggest candidate metadata or classifications, while experts set and justify the actual prioritization rules.

---

## 9. Unified formula/visual semantics

The two views must share the same layer controls and semantics wherever meaningful:

| Layer | Missing Evidence View | Proxy Alignment View |
|---|---|---|
| Heatmap | Degree/state of missing or insufficient direct evidence for the selected target question | Degree/state of mismatch between target measure and observed indicator/variable |
| Vectors | Existing comparator evidence -> target gap | Observed variable/series -> target indicator |
| Wind | Optional modeled spatial field from valid geolocated research/access relations | Optional modeled evidence-navigation field if graph/layout assumptions are explicitly defined; otherwise disabled |
| Friction | Documented barriers to obtaining/using evidence at a cell or edge | Definition/unit/population/time/geography/access mismatch or other documented obstacle to proxy use |
| Time | Observation/reference period and publication period are separately available | Same; never conflate publication year with measurement period |
| Click-through | Sources, observations, gap claims, search scope, barriers | Target and observed definitions, variables, unit, denominator, mapping rationale, limitations |

“Wind” is a visual rendering layer, not a claim that a social system literally follows fluid dynamics. Use it when it carries a well-defined, disclosed meaning; make it optional otherwise.

---

## 10. Search and LLM design

### Search providers

Implement a provider interface. Start with a small number of accessible services rather than every possible source:

- Crossref for bibliographic metadata.
- OpenAlex for scholarly works, authors, institutions, and topic-related metadata.
- Optional PubMed where relevant to health/public-health publications.
- User-entered URLs/DOIs and locally supplied documents.
- Configurable official-source links and dataset catalog connectors.

Source links and APIs are discovery mechanisms, not exhaustive proof of the literature. Document search dates, queries, coverage and API limitations. Respect source terms and rate limits. Store query configuration and results so searches can be repeated.

### LLM tasks

Use a provider-agnostic adapter selected by `LLM_PROVIDER` and `LLM_MODEL` environment variables. Do not hard-code a model name or price in application logic. At implementation, choose a currently available low-cost model for routine metadata extraction and benchmark it against a human-reviewed sample. Route only ambiguous/high-impact cases to a stronger model or human review.

LLM may:
- expand search synonyms and query strategies;
- extract title, publisher/producer, collection method, observation period, geographic scope and access instructions;
- extract indicator definition, unit, denominator, population, reference period and aggregation level from documentation;
- extract author-stated gap claims with exact quotations and source locations;
- propose, but not finalize, comparability/proxy mappings and barriers;
- explain why a suggested proxy is limited, based on documented definitions.

LLM must not:
- fabricate values, references, page numbers, indicators or source coverage;
- assert a report contains a variable without checking the codebook/table/metadata;
- treat semantically similar indicators as directly comparable by default;
- infer that data do not exist from zero search hits;
- claim a barrier or causality without evidence;
- automatically upgrade AI suggestions to verified.

### Structured response and audit

Request strict JSON matching the appropriate Pydantic schema. Each consequential claim must include `evidence_quote`, `source_location`, `source_id`, `extraction_method`, `confidence`, and `review_status`. When a page/section cannot be reliably determined, set it unknown and route for review rather than inventing a location.

---

## 11. Folder structure to implement

```text
gambia-evidence-gap-explorer/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
│   ├── project.yaml
│   ├── search_sources.yaml
│   ├── taxonomy.yaml
│   ├── comparability_rules.yaml
│   └── measures.yaml
├── data/
│   ├── demo/                    # clearly labelled synthetic fixtures only
│   ├── imports/                 # local import staging; ignored by git
│   └── registry.sqlite          # ignored by git if it includes user/restricted data
├── src/evidence_gap/
│   ├── __init__.py
│   ├── schemas.py
│   ├── database.py
│   ├── provenance.py
│   ├── adapters/
│   │   ├── base.py
│   │   ├── csv_excel.py
│   │   ├── pdf_document.py
│   │   ├── crossref.py
│   │   ├── openalex.py
│   │   └── user_url_doi.py
│   ├── search.py
│   ├── extraction.py
│   ├── deduplication.py
│   ├── normalization.py
│   ├── tensor.py
│   ├── indicators.py
│   ├── micro_variables.py
│   ├── macro_series.py
│   ├── gap_claims.py
│   ├── comparability.py
│   ├── formulas.py
│   ├── heatmap_gap.py
│   ├── heatmap_proxy.py
│   ├── research_bridges.py
│   ├── wind_field.py
│   ├── resistance.py
│   └── task_builder.py
├── app/
│   ├── app.py
│   ├── components/
│   │   ├── dark_atlas.py        # shared map/matrix renderer and palette
│   │   ├── layer_controls.py
│   │   ├── legend.py
│   │   └── source_drawer.py
│   └── pages/
│       ├── source_registry.py
│       ├── evidence_gap_map.py
│       ├── proxy_alignment_map.py
│       ├── formula_settings.py
│       └── research_tasks.py
├── scripts/
│   ├── run_search.py
│   ├── import_records.py
│   ├── rebuild_tensor.py
│   └── validate_data.py
├── tests/
│   ├── test_schemas.py
│   ├── test_provenance.py
│   ├── test_search_deduplication.py
│   ├── test_gap_states.py
│   ├── test_comparability.py
│   ├── test_formula_versions.py
│   ├── test_tensor_projections.py
│   ├── test_vectors_wind_resistance.py
│   └── test_no_synthetic_as_real.py
├── docs/
│   ├── data_dictionary.md
│   ├── methods_and_formulas.md
│   ├── search_protocol.md
│   ├── visual_semantics.md
│   ├── access_ethics.md
│   └── decisions_log.md
└── .github/workflows/tests.yml
```

The agent may adjust filenames if there is a compelling implementation reason, but must preserve the separation of concerns, the common data model, and the shared visualization/formula semantics.

---

## 12. Recommended technical stack

- **Python** for data processing, validation, search orchestration, calculation and network logic.
- **Streamlit** for the smallest maintainable research UI.
- **SQLite** for the local MVP database. Keep source records normalized; use stable IDs and link tables.
- **Pydantic** for schema validation and typed LLM output.
- **pandas** for CSV/Excel and analytical tables.
- **Plotly** for interactive matrices and charts.
- **GeoPandas + Shapely** or a suitable GeoJSON mapping approach for actual spatial polygons; use a proper projection for vector-field calculations.
- **NetworkX** for directed relationship graphs.
- **PyMuPDF** for extracting text/page references from accessible PDFs. OCR should be a fallback and its output should be marked accordingly.
- **pytest + GitHub Actions** for automated tests and CI.
- **YAML** for taxonomies, source configuration, comparability rules, palette/layer configuration, and formula coefficients.

Keep package choices and external API dependencies narrow. The app must run locally without any LLM API key using imported/demo data; AI-assisted features should be optional and fail gracefully when keys are absent.

### Cost-conscious AI strategy

Do not lock the app to a specific model name. The coding agent should:
1. implement a provider/model adapter and environment-based configuration;
2. check current official pricing at implementation time;
3. benchmark a low-cost model on a manually reviewed test set of source/indicator/gap-claim extractions;
4. use ordinary Python rules for unit/field validation, exact deduplication, simple date parsing, score calculations and plotting;
5. batch routine tasks where supported;
6. use a more capable model or human review only for ambiguous, conflicting or consequential cases;
7. log token use/cost by search run without storing secret keys.

Do not choose a model solely on its token price: table extraction accuracy, structured-output compliance, citations/page references, latency and correction burden also matter.

---

## 13. CLI contract

The application should expose usable, documented commands. Exact implementation is up to the agent, but target commands should resemble:

```bash
# install dependencies
python -m venv .venv
# activate the environment using the command appropriate to the user's OS
pip install -e ".[dev]"

# run the local application
streamlit run app/app.py

# validate imported data
python scripts/validate_data.py --input data/imports/example.csv

# run a configured metadata search (requires configured providers; no search happens silently)
python scripts/run_search.py --config config/project.yaml

# rebuild the sparse evidence tensor from approved canonical records
python scripts/rebuild_tensor.py

# run automated checks
a pytest
```

The agent must implement actual commands consistent with `pyproject.toml`, document Windows PowerShell commands as well as generic commands, and not leave placeholder commands that do nothing.

---

## 14. Testing / acceptance criteria

The MVP is acceptable only when all these are true:

1. It starts locally without requiring an LLM key.
2. It can import a sample CSV and/or a small set of metadata records into the same canonical model.
3. It stores sources, data products, indicators, variables, observations, and gap claims as separate linked entities.
4. The same approved records and configuration generate both heatmap projections; charts do not maintain separate hidden copies of data.
5. A national-only statistic never becomes a subnational observation without an explicit transformation/model flag.
6. `NOT_SEARCHED_OR_UNKNOWN` and `SEARCHED_NO_DIRECT_EVIDENCE_FOUND` remain distinct.
7. A microdata catalog record can describe variables and questionnaire metadata without storing person-level data.
8. A macro series records the producer/collector/reporting agency, collection method if known, frequency, aggregation level, unit and definition.
9. Every LLM-extracted claim has provenance and review status.
10. Duplicate papers/citation chains do not automatically count as independent evidence.
11. Every formula result records the formula version, weight values, component values, data snapshot/run, and timestamp.
12. Weights that fail to sum to 100% cannot be saved as a valid normalized configuration.
13. Unknown formula components are not silently interpreted as zero.
14. The gap view's vectors point from supporting/comparator evidence to a target gap; the proxy view's vectors point from the observed candidate variable toward the target indicator.
15. Arrow width, length, opacity and wind streamlines all have explicit legends and computational definitions.
16. The wind layer is unavailable/disabled when suitable relationship and spatial data do not exist; it never fabricates real spatial flow.
17. Friction markers link to typed barriers, evidence, and verification status.
18. Synthetic demo records are visually labelled and cannot be mixed into real outputs without a warning.
19. Tests cover schemas, formula consistency, tensor regeneration, provenance, gap states, comparability, arrows/wind and synthetic-data labeling.
20. The README explains installation, configuration, how to add a source/topic, limitations, data permissions, and how to reproduce a result.

---

## 15. Development sequence

### Phase 1 — Canonical model and demo pipeline

Build schemas, SQLite tables, stable IDs, configurable taxonomies, measurement definitions, demo records clearly marked as synthetic, CSV import, and validation. Define the formula/versioning API before plotting.

**Deliverable:** data can be entered once and queried consistently.

### Phase 2 — Two heatmaps, shared design system

Build a common renderer and layer controls. Implement the missing-evidence view and proxy-alignment view from the same underlying records. Add source-detail drawer, shared legend, filters, and time controls. Implement static arrows and documented barriers first.

**Deliverable:** both views run and use the same data/provenance/formula conventions.

### Phase 3 — Search and LLM extraction

Add Crossref/OpenAlex or other configured search adapters, URL/DOI import, accessible PDF parsing, variable/codebook extraction, gap-claim extraction, and a human-review queue. Add rate-limit handling, errors and search-run logs.

**Deliverable:** a small, repeatable search run can create candidates and reviewers can promote them into canonical records.

### Phase 4 — Formulas, optional wind field, and task export

Add adjustable/versioned formula settings, sensitivity comparison, optional spatial wind rendering when supported, task generation, and Markdown/JSON export.

**Deliverable:** a reviewed evidence gap can become an auditable next-step research task.

### Phase 5 — Validation and polish

Run automated tests, manually inspect a sample of extracted records, verify visual semantics with a researcher, document limitations and ensure unsupported data states remain unknown. Optimize cost only after extraction quality is measured.

**Deliverable:** reproducible local MVP with documented limits.

---

## 16. What requires researcher judgment, not autonomous coding

The coding agent must flag these decisions and provide a decision log rather than silently choosing on the user's behalf:

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

The UI should distinguish `AI_SUGGESTED`, `RULE_DERIVED`, `HUMAN_REVIEWED`, and `SOURCE_VERIFIED` states.

---

## 17. Final instruction to the coding agent

Implement the smallest coherent end-to-end MVP, not a large collection of disconnected placeholders. Start with the canonical model and the two linked heatmaps. The interface must have one visual style, one input pipeline, one sparse evidence tensor, one provenance model, and one versioned formula-settings system.

Use realistic structure but clearly marked synthetic records until real records have been retrieved and checked. At completion, return:

1. a concise architecture summary;
2. the exact folder/file tree created;
3. exact Windows PowerShell setup and run commands;
4. tests run and their results;
5. which real public sources were queried, with search dates and limitations;
6. which parts remain synthetic or require human review;
7. a list of unresolved research-design decisions for the user.

Do not claim the system has found all existing data or verified any substantive research gap unless the search protocol and evidence review justify that statement.

---

## Reference documentation for implementation

- Crossref REST API documentation: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- OpenAlex API documentation: https://help.openalex.org/api/
- OpenAlex authentication and rate limits: https://help.openalex.org/api/authentication/
- Review of evidence gap map methodology: https://pmc.ncbi.nlm.nih.gov/articles/PMC8356343/

Check current API policies, rate limits, licenses, package versions and model prices at implementation time. These may change.
