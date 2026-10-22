# Gambia Evidence Gap Explorer

A local Streamlit evidence registry and paired matrix views for the configured youth drug prevention research scope. The application does not contain a youth evidence batch yet. It starts with configured topics and explicit `NOT_SEARCHED_OR_UNKNOWN` cells; it does not fall back to a savings example or manufacture observations. No LLM key is required because LLM extraction is **not implemented**.

## Install, validate, rebuild, test, then launch (Windows PowerShell)

Run from the repository root. First place only a permitted source-linked CSV bundle supplied by the research team in `data/youth/`; this repository intentionally ships no youth research/test dataset.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$batchFile = "data/youth/<provided-bundle>.csv"
python scripts/validate_data.py --input $batchFile
python scripts/import_records.py --input $batchFile
python scripts/rebuild_tensor.py
python -m pytest -q
python -m streamlit run app/app.py
```

`requirements.txt` lists the runtime dependencies from `pyproject.toml`; for deployments that install requirements directly, use `python -m pip install -r requirements.txt`. An optional LLM key is neither read nor required. The CSV importer only places complete bundles in the pending review queue. A reviewer must inspect and approve a bundle in **Source registry** before it can contribute to either matrix.

CSV columns are `source_id`, `source_title`, `source_url_or_doi`, `retrieved_at` (ISO date), `bundle_json`, and optional `synthetic`. `bundle_json` is a JSON object containing linked arrays named `sources`, `data_products`, `indicators`, `variables`, `observations`, `alignments`, `gap_claims`, `barriers`, `research_claims`, `claim_requirements`, and/or `macro_series`. See the **Download CSV header** control for an empty header; it contains no chosen or example research data. For validation only, omit `--import-valid`; `scripts/import_records.py` queues candidates and never approves them.

## Pages

There are six navigation items, including five work pages:

- **Overview** — configured project, batch-folder and review-first status.
- **Evidence gap map** — View A; configured target topics by supported geographic unit, with population, observation-period, and source filters. Select a target and geography for its evidence/provenance detail.
- **Proxy / indicator alignment** — View B; approved target measures by observed indicator/variable, with relationship class, rationale, and measurement loss. Its Claim Audit reads reviewed claims and variable requirements from the registry.
- **Source registry** — source-linked CSV/manual candidates, metadata search candidates, review status, deduplication/lineage information, and approved macro-series metadata.
- **Formula settings** — versioned weights, nullable component values, score display, and persisted formula-run snapshots.
- **Research tasks** — draft task creation with Markdown and JSON downloads.

## Matrix axes and geography guard

View A rows are topics from `config/taxonomy.yaml`; columns are legal geographic units from that taxonomy plus named places explicitly present at an allowed level in approved observations. Each cell is internally scoped by the selected population group. Age/population, observation period, and source are filters, not matrix axes. Geography names and levels must match the source record; a country-level observation is never copied to an LGA or border-area cell. The initial configuration includes only `national`; add specific LGAs or named border areas only when a permitted source identifies them. No polygon map is bundled.

View B rows are targets referenced by approved alignments; columns are observed indicators/variables. A missing relationship is not inferred from a similar name. Both projections come from the same approved, non-synthetic registry records held by the shared tensor. The empty youth batch therefore produces unknown View A cells and no invented View B alignments.

### View A gap states

`NOT_SEARCHED_OR_UNKNOWN`, `SEARCH_INCOMPLETE`, `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`, `INDIRECT_OR_NOT_COMPARABLE_EVIDENCE`, `DIRECT_EVIDENCE_FOUND`, `MULTIPLE_INDEPENDENT_DIRECT_SOURCES`, `RESTRICTED_ACCESS`, `OUTDATED_OR_TEMPORALLY_MISMATCHED`, `INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION`.

### View B alignment classes

`DIRECT_MATCH`, `HARMONIZABLE`, `PROXY`, `CONCEPTUALLY_RELATED`, `INCOMPATIBLE`, `UNKNOWN_REQUIRES_REVIEW`.

Search state affects a cell only when a completed/reviewed run has an explicit matching target, population, and geography scope. `NOT_SEARCHED_OR_UNKNOWN` is kept distinct from `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`. Observation year and source publication year are separate fields.

## Provenance, deduplication, review, and layers

The **Source registry** shows stable source IDs, DOI/URL, retrieval date, `review_status`, synthetic status, and underlying-data lineage. Pending bundles and metadata results are separate from formal sources. Exact DOI, URL, or normalized title duplicates are suppressed at CSV queue time. A shared `underlying_data_id` across distinct records is surfaced for lineage review and counted as one independent source. Provenance stays linked from product/indicator/variable/observation/alignment/barrier back to its source.

Synthetic records are excluded from both projections and marked in the registry. A CSV row marked synthetic stays excluded even after approval. Unknown matrix cells use neutral charcoal and `///`; teal/amber/rust retain evidence and mismatch meanings. View A arrows point evidence/comparator → target gap; View B arrows point observed measure → target. Arrow thickness means deduplicated independent source count; length has no evidentiary meaning. Arrow labels show `RULE_DERIVED` or `HUMAN_REVIEWED`. Friction markers are selectable and expose typed barriers, evidence, and verification state. Wind remains disabled because this repository has no validated geolocated directional network and coordinate set; no field is synthesized.

## Search example and limits

Historical metadata smoke search recorded on **2026-10-22**: query `The Gambia savings account household survey`; provider **Crossref**; requested/returned **5/5** metadata candidates. These remain `PENDING_HUMAN_REVIEW` and are not youth evidence or approved findings. This was one short catalog query only: no title/full-text screening, coverage assessment, source validation, or measurement review. A zero-result search does not show that evidence does not exist, and a positive result does not establish that it answers the target question. To run an explicit search, use `python scripts/run_search.py --query "<query>" --provider crossref --limit 5`; it does not silently run at startup.

LLM extraction is **not implemented**. Search adapters retrieve bibliographic metadata only. They do not extract claims or automatically promote any record into evidence.

## Current implementation verification (2026-10-22)

- **CSV validation/import:** not run in this change because `data/youth/` is intentionally empty and no researcher-provided batch was supplied. No synthetic youth CSV was created.
- **Tensor rebuild:** `python scripts/rebuild_tensor.py` passed; it wrote 7 configured target × population × national cells, all `NOT_SEARCHED_OR_UNKNOWN`, and 0 approved alignments from `data/youth/`.
- **pytest:** `.venv` Python `-m pytest -q` passed: **27 passed in 0.55s** (the bare `pytest` command was not on PowerShell PATH).
- **Streamlit:** port 8765 was already occupied. `python -m streamlit run app/app.py --server.headless true --server.address 127.0.0.1 --server.port 8767` started locally; HTTP returned 200. Streamlit AppTest loaded Overview and all five work pages with zero exceptions.

## Reuse and deployment notes

To reuse the project, fork the repository, place the research team's permitted source bundle CSVs in the configured `data/youth/` folder (or change `default_batch_dir` in `config/project.yaml`), update the project question and topics/geographic levels in `config/project.yaml` and `config/taxonomy.yaml`, then adjust comparability rules only after researcher review. The application reads repository batch files as pending candidates at startup; reviewers approve them in the registry. No source data is embedded in Python code.

Before importing a source, review its terms, access restrictions, copyright, and ethics permissions in `docs/access_ethics.md`. Restricted person-level data is not included by default.

The ignored `data/registry.sqlite` is a local runtime cache, not a deployment prerequisite. On a fresh runtime, the schema is created and bundled CSVs are re-queued from the repository batch folder. A shared production deployment still needs a persistent, access-controlled database and a reviewed permissions/backup plan; deployment is not configured or validated by this repository change. Do not commit `.env`, restricted imports, local SQLite files, or unapproved source material.

## Not implemented / researcher decisions

Not implemented: LLM extraction; geographic polygon rendering; modeled wind; macro-series visualization beyond its reviewable metadata table; automatic data transformations; and automated causal identification. Discrete vectors and barriers render only when approved records support them. Claim Audit can display only requirements and limits explicitly entered in reviewed records; collecting all required data does not itself identify a causal effect.

Research decisions remain unresolved in `docs/decisions_log.md`, including target concept, eligible sources/populations/periods/geographies, direct-vs-proxy boundaries, transformation defensibility, source independence, what counts as sufficiently searched, documented-vs-hypothesized barriers, support for vector links, optional formula variables/weights, and data-sharing permissions. The configured youth topics reflect the requested project scope; they do not constitute reviewed operational definitions.
