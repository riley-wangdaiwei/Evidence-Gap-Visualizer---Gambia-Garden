# Audit memo — Youth Drug Prevention in The Gambia

**Run date:** 2026-10-31  
**Status:** Candidate discovery and extraction only; all output rows remain `CANDIDATE_PENDING_HUMAN_REVIEW`.  
**Input:** `gambia-evidence-llm-intake-v1(1).zip` plus the accompanying LLM run instructions.  
**Output boundary:** `candidate_outputs/` only. No approved database writes and no edits to `seed_v2/`.

## 1. Executive summary

This is a bounded discovery pass, not an exhaustive review of every possible source. Search activity covered all ten configured source-target families, prioritising Gambia-specific material. The work produced five new documentary source candidates and extracted additional variables/observations from two existing sources (WENDU 2023 and the Jallow 2025 pilot). GYTS 2017 was re-checked against the official factsheet and microdata dictionary to preserve the tobacco-only guardrail.

| Candidate output | Rows |
|---|---:|
| New source candidates | 5 |
| Data products | 3 |
| Indicators | 7 |
| Variables | 58 |
| Observations | 15 |
| Assessed View B alignment candidates | 15 |
| Source-authored gap-claim candidates | 1 |
| New barrier candidates | 3 |
| Data-production audit rows | 5 |
| Search and direct-inspection logs | 45 |
| Search candidate dispositions | 15 |
| Proposed Layer B box definitions | 1 |
| Mapping rows | 182 |

The 113 substantive entity rows (sources, data products, indicators, variables, observations, alignments, gaps, barriers, production audit and proposed box) are all mapped to at least one Layer A parent / Layer B box. The seven distinct source IDs attached to substantive rows have no mapping orphans. Search-run and search-candidate metadata rows are also mapped. No row is approved.

## 2. Search activity and audit trail

- **29 web searches** were run on 2026-10-31 (`SR039`–`SR067`). Provider result counts were not reliably exposed, so every count is recorded as `UNKNOWN`; no result totals were invented.
- **16 direct URL/document inspections** were logged (`SR068`–`SR083`): 9 completed inspections and 7 partial/access-limited attempts.
- Search target coverage included: UNODC/substance-use and harms; GIABA illicit-finance and AML/CFT; OCIndex/ENACT market context; DLEAG administration and prevention; WHO/GYTS/GSHS surveys; academic studies; WENDU reports/methodology; national policy and drug-control strategy; DHS/MICS/GBoS dictionaries; and programme evaluation/monitoring.
- Exact query text, run date, provider, period, result-count status, inclusion logic, access notes and full-text status are retained row-by-row in `search_runs.csv`. The exact direct-inspection URLs and access outcomes are in the same file.
- The exact UNDP/DLEAG query `site:undp.org/the-gambia "youth-led" drug prevention initiative "27 March 2026" DLEAG` was run twice (`SR057` and `SR067`) and logged twice; it is not counted as two independent source discoveries.

### Exact web-search queries

| Run | Exact query |
|---|---|
| SR039 | `The Gambia adolescent substance use youth drug use survey 2010 2026 UNODC Gambia country data harms supply` |
| SR040 | `site:giaba.org "The Gambia" mutual evaluation follow-up drug proceeds asset seizure financial data 2024 2025` |
| SR041 | `The Gambia drug market organized crime index methodology country profile ENACT Global Organized Crime Index 2025` |
| SR042 | `DLEAG annual report The Gambia arrests seizures youth schools outreach statistics annual report 2010 2026` |
| SR043 | `The Gambia GYTS GSHS substance use questionnaire microdata codebook adolescents WHO survey` |
| SR044 | `(Gambia OR "The Gambia") (adolescent OR youth OR child) (drug OR "substance use" OR prevention OR treatment OR cannabis OR Kush) study` |
| SR045 | `WENDU Gambia under 18 arrests region substance cases treatment F12 HMIS reporting age sex disaggregation 2023 2024 2025` |
| SR046 | `The Gambia National Development Plan 2023-2027 youth drugs prevention successor National Drug Control Strategy implementation report` |
| SR047 | `Gambia DHS MICS substance use questionnaire variable codebook youth tobacco drug GBoS microdata` |
| SR048 | `DLEAG UNDP youth-led prevention project Gambia logframe M&E baseline endline participant roster evaluation budget 2026` |
| SR049 | `site:dleag-gambia.org annual report 2024 2025 youth school outreach arrests seizures Gambia DLEAG PDF` |
| SR050 | `site:undp.org/gambia DLEAG youth-led drug prevention initiative 27 March 2026 programme participants baseline logframe` |
| SR051 | `site:gov.gm "National Drug Control Strategy" successor Gambia 2024 2025 drug prevention` |
| SR052 | `site:gbosdata.org "The Gambia Demographic and Health Survey 2019-2020" V463 data dictionary age respondents tobacco` |
| SR053 | `site:extranet.who.int/ncdsmicrodata "Gambia" GYTS 2017 CR7 questionnaire weights ages 13 15` |
| SR054 | `The Gambia youth drug treatment services access adolescent rehabilitation centre mental health drug dependency 2019 2026 Ministry Health` |
| SR055 | `The Gambia substance use prevalence school students cannabis cocaine Kush survey adolescent study 2010 2026` |
| SR056 | `The Gambia youth risk protective factors school dropout unemployment family peer substance use survey indicators data` |
| SR057 | `site:undp.org/the-gambia "youth-led" drug prevention initiative "27 March 2026" DLEAG` |
| SR058 | `site:dleag-gambia.org "youth-led" "UNDP" drug prevention` |
| SR059 | `site:moh.gov.gm Gambia substance use treatment adolescent youth drug dependency mental health HMIS report 2023 2024` |
| SR060 | `The Gambia WENDU National Focal Point annual data return methodology HMIS treatment DLEAG reporting template` |
| SR061 | `Gambia MRC Unit LSHTM sub-national tobacco survey results 2025 2026 tobacco control capacity programme` |
| SR062 | `site:giaba.org "The Gambia" "drug proceeds" "asset recovery" "2024" follow-up` |
| SR063 | `The Gambia 2025 Global Organized Crime Index methodology 2024 data expert assessment scoring scale` |
| SR064 | `site:fctc.who.int "The Gambia" "needs assessment" "Protocol to Eliminate Illicit Trade" 2025` |
| SR065 | `site:policies.gov.gm "The Gambia Health Management Information System Policy 2017-2025" Ministry of Health` |
| SR066 | `The Gambia assessment of National Disease Surveillance System 2025 DHIS2 health facilities` |
| SR067 | `site:undp.org/the-gambia "youth-led" drug prevention initiative "27 March 2026" DLEAG` |

### Direct inspections and access limitations

| Run | Inspected item | Outcome |
|---|---|
| SR068 | `https://ecowas.int/wp-content/uploads/2024/10/EN-Rev-Final-Updated-WENDU-Report-2023-Final-Copy.pdf` | YES — relevant tables and surrounding country-report text; screenshots of pp.62 and 64 checked |
| SR069 | `https://www.scivisionpub.com/pdfs/drug-abuse-among-senior-secondary-school-students-in-banjul-area-council-zone-the-gambia-a-pilot-study-3990.pdf` | YES — methods, Tables 2–4 and charts; screenshots of pp.3–5 checked |
| SR070 | `https://ocindex.net/assets/downloads/2025/english/ocindex_profile_gambia_2025.pdf` | YES — all profile text; screenshot p.1 checked |
| SR071 | `https://ocindex.net/assets/downloads/english/ocindex_methodology.pdf` | YES — methodology text and screenshots pp.2–3 checked |
| SR072 | `https://usher.ed.ac.uk/tobacco-control-capacity-programme/our-research/population-surveys` | YES — page content checked |
| SR073 | `https://fctc.who.int/newsroom/news/item/05-08-2025-the-gambia-assesses-its-needs-to-strengthen-implementation-of-the-protocol-to-eliminate-illicit-trade-in-tobacco-products` | YES — full webpage content checked |
| SR074 | `https://policies.gov.gm/f/caa65bd5-5bad-11ec-9b31-029254d29bb1` | PARTIAL — repository summary page checked; linked PDF not accessible |
| SR075 | `https://www.panafrican-med-journal.com/content/article/51/91/full/` | YES — full article text and relevant facility results/discussion checked |
| SR076 | `https://www.giaba.org/mutualevaluation/3340-2nd-enhanced-follow-up-report-of-the-gambia-2024` | PARTIAL — landing page checked; linked attachment viewer did not expose PDF text |
| SR077 | `https://mogcsw.gov.gm/wp-content/uploads/2024/09/RF-NDP-2023-2027.pdf` | PARTIAL — PDF text/page content opened; screenshot attempt timed out |
| SR078 | `https://microdata.gbosdata.org/index.php/catalog/2` | NO — request timed out; search snippet only |
| SR079 | `UNKNOWN (exact endpoint not preserved in recorded fetch)` | NO — request timed out; search snippet only |
| SR080 | `UNKNOWN (exact endpoint not preserved in recorded fetch)` | NO — request timed out; search snippet only |
| SR081 | `https://cdn.who.int/media/docs/default-source/ncds/ncd-surveillance/data-reporting/gambia/gambia-2017-factsheet-%28ages-13-15%29-final_508tagged.pdf` | YES — full two-page factsheet text and screenshots of pages 1–2 checked |
| SR082 | `https://extranet.who.int/ncdsmicrodata/index.php/catalog/776/data-dictionary/F1` | YES — catalog dictionary opened; CR7 labelled “Smoked past 30 days”; 12,585 cases and 69 variables |
| SR083 | `https://standard.gm/dleag-undp-launch-youth-led-drug-prevention/` | NO — web open returned internal error |

Important access failures/limitations:
- The Government policy-repository page for the 2017–2025 HMIS policy was inspected, but its linked policy PDF did not load. Candidate claims are restricted to the repository summary.
- GIABA’s official landing page was inspected, but its linked 2024 follow-up PDF viewer did not expose the full report text/annexes. The report is already seed source `S020`; no duplicate source row was created.
- GBoS DHS catalogue and dictionary/field page requests timed out. A search snippet suggested a possible tobacco field, but the field was not verified; no DHS variable or observation was created. Exact failed child-page endpoints were not retained in the fetched record and are marked `UNKNOWN` rather than fabricated.
- The NDP PDF text was accessible but its screenshot attempt timed out; this was treated as a partial re-check of existing seed source `S003`, not a new source.
- The Standard article used as the existing DLEAG–UNDP launch source (`S017`) returned an internal error on re-open. The launch-date guardrail (27 March 2026) is retained from the supplied project instructions/seed context; independent full-text re-verification was not achieved in this run.

## 3. New source candidates and data products

Five new documentary candidates were assigned provisional IDs. They are not five independent measures of youth drug use:

| Provisional source ID | Candidate | What is supported | Scope / limitation |
|---|---|---|---|
| `LLM_CAND_SOURCE_0001` | Global Organized Crime Index 2025 — The Gambia profile | Four separate drug-market expert scores (heroin, cocaine, cannabis, synthetic drugs) and a general PREVENTION resilience score; methodology reviewed. | Country context, not youth consumption, prevalence, physical quantities, route flows or programme effects. 2025 edition describes dynamics during 2024. Same index family as seed `S021`. |
| `LLM_CAND_SOURCE_0002` | MRC Unit The Gambia / LSHTM sub-national tobacco survey project page | A Gambia-specific population survey project is described, with aims around tobacco burden and policy knowledge/barriers. | Inspected page does not identify age band, exact sites, questionnaire, sample, field dates, estimates, microdata custodian or access conditions. A separate Ethiopia adolescent survey on the page was not imported as Gambian evidence. |
| `LLM_CAND_SOURCE_0003` | WHO FCTC 2025 Tobacco Protocol needs-assessment mission | Gambia-specific institutional mission and priorities around enforcement, coordination, supply-chain control and international cooperation. | Tobacco-product illicit trade only; not illicit drugs, youth drug use or drug-market quantities. |
| `LLM_CAND_SOURCE_0004` | The Gambia HMIS Policy 2017–2025 repository summary | Government repository identifies Ministry of Health policy sector and describes HMIS strengthening aims and system issues. | Underlying policy PDF was inaccessible; summary-only candidate. Policy existence is not proof of operational capture of youth substance-use measures. |
| `LLM_CAND_SOURCE_0005` | National Disease Surveillance System assessment, January 2025 | Peer-reviewed assessment of 74 health facilities, including a reported DHIS2 reporting-use percentage and general surveillance-system limitations. | General IDSR / disease-surveillance evidence, not drug-use or youth treatment surveillance. |

Three product-level candidates were created: OCIndex 2025 Gambia profile, MRC sub-national tobacco survey project description, and the NDSS/IDSR facility assessment. The FCTC mission and HMIS repository record remain policy/context source candidates rather than invented survey/data products.

## 4. Extracted measures and observations

### WENDU 2023 — existing source `S001`

The full report’s Gambia age-by-region table (printed p.62) was inspected. Seven regional cells were added as observation candidates: Banjul `NIL`, Kanifing Municipality 4, West Coast Region 13, Lower River Region `NIL`, Central River Region 1, Upper River Region 2 and North Bank Region 5. The two `NIL` cells are retained literally, not converted to zero. These are counts of drug-related arrestees aged 17 years and below, not population prevalence.

The source reports 10 of 650 recorded drug-related arrestees (all ages) aged 17 and below in 2022 (1.54%), and 25 of 633 in 2023 (4%). The published percentages are retained as reported, not recalculated. The seed already contains the 2023 national total of 25; it was not duplicated. A proposed box `B52_WENDU_UNDER18_SHARE_OF_RECORDED_ARRESTEES_2022_2023` distinguishes the national share/denominator measure from existing `B06` regional count cells.

**Guardrail:** WENDU’s under-18 age distribution and substance-specific arrest table are separate margins. There is no age × substance cross-tab. No under-18 Kush/cannabis arrest figure can be inferred by combining them. Arrest counts are not prevalence.

### Jallow et al. 2025 pilot — existing source `S032`

The full text and Tables 2–4 were checked. Fifty-one separate variables were extracted: 30 substance-specific item fields (ever, past-year, and age-at-first-use items for ten substances), one awareness item, eight perception items, ten perceived-consequence items and two knowledge scales. No numeric observations were emitted from this source.

The study is a single-school, all-male pilot with n=142 and mean age 18.5 (SD 1.33). The publication does not provide an under-18 subgroup or a fieldwork date. The abstract, Figure 1 and Table 2 contain inconsistent values/denominators. Those conflicts are retained for human review; publication year 2025 is not treated as fieldwork time. Items concerning beliefs and consequences are knowledge/perception constructs, not actual substance exposure or observed health outcomes.

### OCIndex 2025 — new source candidate

Five numeric candidates were extracted: heroin market 2.50, cocaine market 7.50, cannabis market 6.50, synthetic-drug market 5.00, and PREVENTION resilience 4.50. The four market ratings use the criminality scale; the resilience component uses the oppositely oriented resilience scale (10 is strongest). They are not comparable to one another as if they were all “more drug use” scores. The profile/methodology do not supply age-specific use or physical route/flow amounts.

The source narrative’s reference to Kush does not justify reclassifying the synthetic-drug market score as a Kush-only measure. “Kush” was not equated with cannabis or with a synthetic-drug index item.

### NDSS January 2025 assessment — new source candidate

The article reports 47% of assessed facilities used DHIS2 for data reporting, with an assessed sample of 74 facilities (16 hospitals and 58 primary-health-care facilities) drawn from a frame of 195. The source percentage is rounded; no numerator was inferred. This is a facility-level general surveillance measure, not a youth/substance-use reporting rate. One source-authored gap claim was retained: “gaps remain in data analysis, implementation of eIDSR, and preparedness planning” (abstract/conclusion). It is restricted to general disease-surveillance-system context.

## 5. Four case guardrails

1. **GYTS 2017:** Re-checked the official Gambia factsheet and WHO NCD microdata dictionary. The factsheet describes a nationally representative school-based survey of students in grades associated with ages 13–15; it reports 12,585 eligible grade 7–9 respondents, of whom 7,176 were aged 13–15, and weights estimates to students aged 13–15 enrolled in school. It separately shows current cigarette smokers (6.5%) and current users of any tobacco product (10.5%). WHO’s dictionary labels CR7 “Smoked past 30 days”; this cigarette-specific field is not the same as the broader any-tobacco composite. Tobacco only; no illicit-drug measure and no out-of-school adolescents.
2. **WENDU 2023:** The total 25 under-18 arrestees and regional distribution were checked at printed p.62. Age and substance tables are not cross-tabulated. No age × substance inference; recorded arrests are not prevalence.
3. **Jallow Banjul pilot:** Full text confirms one school, all-male sample, n=142, mean age18.5 (SD1.33). Under-18 subgroup and observation time remain `UNKNOWN`. Abstract/Figure/Table inconsistencies are not resolved; no numeric observations added.
4. **DLEAG–UNDP youth-led initiative:** The supplied instructions identify a launch on 27 March 2026. The seed launch source `S017` was retained as evidence of programme existence only. Its direct re-open failed in this run; no roster, baseline, follow-up or comparison group was independently found in the bounded pass. Launch/activity counts do not establish unique participation, coverage or effect.

## 6. Layer A parent mapping and orphan audit

Counts below are distinct substantive candidate entity rows by parent; an entity can be mapped to more than one parent when the source genuinely spans topics. Search-run and search-candidate administrative rows are excluded from this substantive count (they are all separately mapped to A10 for auditability).

| Layer A | Parent | Distinct substantive entity rows |
|---|---|---:|
| A01 | Substance-specific use | 31 |
| A02 | Health outcomes / harms | 0 |
| A03 | Treatment / service access | 0 |
| A04 | Prevention policies | 7 |
| A05 | Programme delivery / reach / participation / dose | 0 |
| A06 | Post-participation outcomes | 0 |
| A07 | Enforcement / supply | 37 |
| A08 | Social / livelihood / risk factors | 21 |
| A09 | Cross-border / illicit finance | 0 |
| A10 | Data production / governance / access | 22 |

The parent assignments sum to more than 113 because four substantive entities are multi-mapped across parents, producing five extra parent assignments (one source spans three parents). By exact row counts: 113/113 substantive entity rows have one or more mapping records (0% unmapped); 7/7 unique substantive `source_id` values have mapped records (0% orphan source IDs). Including 45 search-run rows and 15 search-candidate rows, the output contains 173 distinct mapped entities and 182 mapping rows. The nine extra mapping rows arise from multi-parent mappings; they are not extra independent sources.

No new substantive candidate rows were mapped to A02, A03, A05, A06 or A09 in this pass. This is an evidence-inventory result, not proof those data do not exist. Search and access limitations are set out below.

## 7. View B candidate relationships

| Relationship class | Candidate rows |
|---|---:|
| DIRECT_MATCH | 0 |
| HARMONIZABLE | 0 |
| PROXY | 1 |
| CONCEPTUALLY_RELATED | 9 |
| INCOMPATIBLE | 4 |
| UNKNOWN_REQUIRES_REVIEW | 1 |

The 15 assessed relationships are: one `PROXY` (WENDU national share among recorded arrestees versus a regional recorded-arrest claim); four `INCOMPATIBLE` (each OCIndex market score against a cross-border physical-flow claim); nine `CONCEPTUALLY_RELATED` (market-context versus youth-use claims, resilience versus post-programme outcome, and general HMIS/IDSR capacity versus data-system availability); and one `UNKNOWN_REQUIRES_REVIEW` (MRC survey project versus GYTS current-tobacco target because age, item wording, geography and reference period are not published on the inspected page).

No new `DIRECT_MATCH` or `HARMONIZABLE` relationship was justified. Unassessed claim × measure combinations, including the Jallow items, were not fabricated as stored relations. The UI may present missing candidate relationships as neutral `NOT_ASSESSED`; this state is not stored as an alignment row and is not included in the counts.

## 8. Empty / still-required target areas

| Search target | Outcome in this pass |
|---|---|
| ST01 — UNODC / youth use, harms, supply | No new national under-18 population prevalence series or comparable Gambia-specific youth-use survey located. WENDU arrest and Jallow pilot evidence are not substitutes. |
| ST02 — GIABA / illicit finance | Existing GIABA follow-up `S020` confirmed on its landing page, but full attachment not accessible. No Gambia-specific measured drug-proceeds, transaction or asset-recovery series was extracted; A09 remains unpopulated by new measured candidates. |
| ST03 — OCIndex / ENACT | New 2025 Gambia profile and methodology checked; country-context market/resilience scores extracted. |
| ST04 — DLEAG administration | No new official annual-report series, age-disaggregated enforcement dataset or programme monitoring product was verified. Existing programme launch source is not a monitoring dataset. |
| ST05 — WHO / GYTS / GSHS | GYTS 2017 tobacco factsheet and CR7 dictionary verified. No illicit-drug measure was found in this GYTS item; no new GSHS drug-use product was established in this pass. |
| ST06 — academic studies | Jallow 2025 pilot full text extended at item level. It is not a national or under-18 prevalence estimate. No stronger new Gambian youth-drug study verified. |
| ST07 — WENDU | WENDU 2023 full report inspected for relevant Gambia pages. A separate 2024/2025 full report/table return or national focal-point template was not located/checked in this pass. |
| ST08 — national plans / drug-control strategy | Existing NDP `S003` re-checked; WHO FCTC tobacco protocol mission added as context. No new successor drug-control strategy implementation logframe/budget/outcome series verified. |
| ST09 — DHS / MICS / GBoS | Catalogue/dictionary access failed intermittently; possible tobacco field snippets were not accepted as evidence. No new variable or observation added. |
| ST10 — programme monitoring / youth-led initiative | Existing DLEAG–UNDP launch guardrail carried forward. No verifiable roster, baseline/endline, comparison group, unique participation, dose or completion measure found in the bounded search. |

“Not located in this pass” means only that the bounded searches and attempted pages did not identify a verifiable artifact; it is not an assertion that the artifact does not exist.

## 9. Source-family dependency and duplicate handling

- **OCIndex:** The new 2025 Gambia profile is related to seed `S021` and its index programme. The methodology PDF is logged as a dependency, not as a second independent empirical source. The five profile measures belong to one source family and are not five sources.
- **WENDU:** New region cells and share observations extend `S001`. The national 2023 under-18 total 25 already in the seed is not duplicated. Existing seed barriers `B001`–`B003` are not copied into candidate output; the current output only adds measures and audit notes.
- **Jallow:** The 51 extracted item variables all belong to existing study `S032`; they are not 51 separate sources or 51 numeric observations.
- **GYTS:** Factsheet `S018` and dictionary/item record `S033` refer to the same 2017 survey. This is a guardrail re-verification, not a new survey source. The factsheet’s any-tobacco composite is kept distinct from cigarette-specific CR7.
- **GIABA / NDP / DHS / DLEAG:** Existing seed sources `S020`, `S003`, `S007` and `S017` were rechecked or sought; no duplicate source records were created. Where access failed, source-family links and failure details remain in the search logs.

## 10. Within-box collisions and split/merge suggestions

1. **Jallow B29–B32:** Each currently groups three distinct constructs for a substance: ever use, past-year use and age at first use. Thirty candidate variables are explicitly flagged `REVIEW_SPLIT_LIFETIME_VS_PAST_YEAR_VS_AGE_FIRST_USE`. Recommend human review of 12 child operational boxes (four substances × three constructs) or an equivalent normalized construct design. Do not merge lifetime and past-year use.
2. **Other Jallow substances:** Amphetamine, Diazepam on own, heroin, tramadol, cocaine and solvents each retain three item-level variables. They remain in broad inventory-only `B22` pending stable source-specific box definitions; do not force them into cannabis/Kush or other existing substance boxes.
3. **Jallow beliefs and consequences:** The eight perception items, ten consequence-belief items and two knowledge scales remain distinct variables under the social/risk inventory branch; they are not observed use, health outcomes or intervention outcomes. Awareness is kept in existing `B33`.
4. **WENDU B06 vs proposed B52:** Regional age-17-and-below counts and national age-group shares among all arrestees have different geography/denominator and estimand. `B52` is proposed as a separate box split from `B06`; do not merge them.
5. **OCIndex B18:** Keep heroin, cocaine, cannabis and synthetic-drug market scores as distinct variables even though they share the market-context box. The general PREVENTION resilience score is not one of those drug-market scores and remains a separate inventory/context measure.
6. **General surveillance context:** The NDSS facility DHIS2 measure and HMIS policy summary remain in `B22` / `B20` general-system context. They should not be merged into a youth-drug reporting indicator absent substance-specific reporting fields.

No seed taxonomy or existing box definitions were edited. `B52` is a proposal only and requires human approval before adoption.

## 11. Data production: facts, supported interpretations and hypotheses

The five rows in `data_production_audit.csv` cover the OCIndex profile, MRC survey project, NDSS assessment, HMIS policy repository summary and WENDU 2023 report. Interpretation statuses are exactly the three allowed labels: two `已证实事实` and three `支持中的解释`; no `待验证假设` was written as fact. Unknown roles remain `UNKNOWN`.

- **Established/documented roles:** ECOWAS/WENDU is the report framework/producer and the Gambia national focal point contributes country data, but exact table-level collector/custodian is not identified; the NDSS assessment describes Ministry of Health staff at central/regional levels with WHO Gambia Country Office support; the HMIS repository identifies the Ministry of Health policy sector; OCIndex profile/methodology attributes the assessment to the GI-TOC/OCIndex programme context.
- **Supported interpretations, not confirmed production facts:** broader programme funder information is not automatically product-level funding. UKRI GCRF is named for the broader MRC Tobacco Control Capacity Programme, not a confirmed survey-specific allocation. ENACT/EU and US Department of State acknowledgements do not identify exact country-profile cost shares. WENDU-related support does not prove the report’s product-specific funding period.
- **Unknown:** underlying data custodians for OCIndex, MRC and NDSS; MRC survey questionnaire/age/sample/field team; frequency of source-level returns; exact Gambia authority for some individual WENDU indicators; HMIS operational data-custody roles; and several funding periods. These are explicitly `UNKNOWN`, not inferred.
- **Potential hypotheses not promoted to facts:** whether general HMIS/IDSR fragmentation is the reason youth substance data are missing; whether household survey module design explains absent drug-use variables; whether gaps in AML/CFT metrics imply no cross-border drug finance measurement. Those hypotheses need direct documentation and are not in the new candidate fact rows.

Existing seed barriers B001–B003 already capture WENDU-reported research, resource and HMIS reporting concerns. They were not duplicated. Three new barrier candidates are limited to the HMIS repository summary and the general NDSS assessment; none is re-labelled as a drug-specific barrier.

## 12. Remaining human-review priorities

- Verify WENDU table transcription against printed p.62 and decide how to handle source `NIL` values in downstream numeric storage; keep source-native text until the decision is documented.
- Review the Jallow abstract/Figure/Table discrepancies, confirm exact questionnaire wording/response universes and approve any split of B29–B32. Do not infer under-18 subgroup membership from the mean age.
- Review the OCIndex criminality versus resilience scales and whether the proposed contextual indicators are useful in View A; do not treat them as flow or prevalence data.
- Retrieve the HMIS policy PDF and GIABA attachment if access becomes available; check the GBoS questionnaire/dictionary directly before adding any putative variable.
- Obtain primary DLEAG programme documentation (eligibility, named sites, roster schema, unique participants, activity dose/completion, baseline/follow-up, comparison) before mapping any reach or effect indicator.
- Confirm data custodian, collection frequency, funder period and indicator authority with source-level documentation rather than organisational assumptions.
- Assess unaligned Jallow variables against claims only when age, observation period, denominator, question wording and geography can be evaluated. Unassessed pairs remain uncreated.

## 13. Reproducibility and integrity checks

- All CSV outputs use the supplied `output_templates/` headers; each template header matched exactly.
- All new rows carry `CANDIDATE_PENDING_HUMAN_REVIEW`; no approval status was assigned.
- The 15 View B rows are candidate relationships only; no unsupported direct match was created.
- `mapping.csv` contains 182 mapping rows over 173 distinct output entities (113 substantive entities + 45 search runs + 15 candidate dispositions).
- A byte-for-byte SHA-256 comparison of all 15 `seed_v2/` files in the uploaded ZIP against the extracted working corpus found no missing or modified seed files.
- No files were written outside `candidate_outputs/` in the source package, except the final downloadable archive created separately in `/mnt/data/`.
- Counts and run IDs are duplicated in `run_notes.json`; exact search and inspection rows are in `search_runs.csv`.

**Interpretation:** The strongest direct youth-specific evidence added here remains the limited Jallow single-school pilot’s documented item inventory, not a nationally representative under-18 estimate. The strongest under-18 administrative observation added remains WENDU recorded-arrestee counts/shares, which are not prevalence. The principal new broader context is market scoring and health-data-system infrastructure, neither of which substitutes for youth substance-use or prevention-effect measurement.
