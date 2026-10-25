# Gambia Youth Drug Prevention — Concept Box Design & Evidence Audit Memo

**Purpose:** Decide how to define the “boxes” in the topic-wide evidence heatmap before changing either MVP view. This is a research/design memo, not an import approval. No values should be invented, and proxies must not be treated as direct observations.

## 1. Recommendation in brief

Do not select any of the three proposed standards by itself. Use a **two-layer, topic-complete and claim-testable scheme**:

1. **Topic inventory boxes** capture every in-scope kind of evidence, whether or not it has already been paired to a research claim. Examples include substance-specific self-reported use, treatment/service records, prevention activities and participation, post-program outcomes, enforcement/supply records, social determinants, and data-production/access records.
2. **Operational measurement / claim boxes** define exactly what a piece of evidence measures and which testable claim it can inform. Each box should preserve population, substance, observation period, outcome, unit, denominator, geography, and method where available.

Every eligible source/data product/indicator/variable/observation must remain visible in the broad inventory. It can then be mapped to zero, one, or multiple operational boxes with an explicit relationship status. Unmapped items go into a visible `UNMAPPED / REVIEW_REQUIRED` lane rather than disappearing. A source can be relevant to the topic without directly measuring the selected outcome.

For visualization, keep separate encodings for:

- **Inventory presence/density:** what evidence products or measurements exist in the topic/time box, independent of claim pairing.
- **Claim fit/answerability:** whether those measurements directly answer, partially inform, serve only as proxies for, conflict with, or have not yet been reviewed against a specific claim.

Do not compress both into one heat value. A box can contain a large amount of evidence and still be unable to answer a causal question.

## 2. Compare the three proposed box standards

| Standard | Advantages | What it can lose or distort | What is likely to remain empty |
|---|---|---|---|
| **1. Paper-first: every concept raised in a paper becomes a box** | Anchors concepts in research questions and author-stated gaps; makes it easier to preserve a stated gap even when no data have been found. Useful for the literature-review and gap-claim layer. | Peer-reviewed papers are not the whole topic. It can miss administrative data, program records, policy implementation data, and variables that papers do not discuss. Similar concepts can proliferate under different names. A paper's broad wording may not define a measurable variable. Publication bias determines which concepts become boxes. | Concepts mentioned in literature but not measured; unique one-off concepts; topics outside the published literature; boxes that only repeat another box with different wording. |
| **2. X-axis-first: define the complete X universe; Y indicates how much each X item is populated** | Keeps a fixed inventory of X concepts in view; makes cross-category coverage comparisons easy; exposes gaps instead of hiding them. Good if X is an explicitly defined, topic-wide taxonomy. | If X boxes are too narrow, many real records have no legitimate home and either disappear or are forced into bad matches. If X boxes are too broad, unlike measures share a cell. Treating “all X items must be full” literally encourages forced assignments and proxy inflation. | Empty X-by-Y cells when time periods, variables, populations, or source types are unavailable; these can be real gaps, not a failure of the chart. |
| **3. Y-axis-first: define the complete Y universe; X indicates how much each Y item is populated** | Same benefit as standard 2, but can be easier when the Y-axis is the primary research taxonomy and X is time/source/measurement. Can be easier to read when Y has many hierarchical concepts and X has fewer time bins. | Mathematically, merely swapping axes does not solve the granularity problem. It has the same risk of a too-narrow/too-broad taxonomy and forced alignment. The choice of orientation can change readability, but not evidence validity. | Same as standard 2: absent observations, unknown periods, unmatched variables, and gaps at meaningful intersections. |

**Important interpretation:** “The axis must be complete” should mean every intended category appears in the inventory—not that every cell must contain a value. Empty, unknown, not searched, and not applicable are different states.

## 3. A better standard: topic-complete parent boxes + testable child boxes

Use a controlled hierarchy rather than choosing between “all paper concepts” and “all data must fit into one flat axis.”

### Layer A — Topic-wide evidence inventory

Parent categories should be broad enough to retain all in-scope material, but still distinguish what kind of evidence it is. Candidate parent categories for this project:

1. Substance-specific use and patterns (one substance per child category; preserve source wording)
2. Substance-related health outcomes and harms
3. Treatment, care, and service access
4. Prevention policies and planned activities
5. Prevention programme delivery, reach, participation, and dose
6. Post-participation outcomes and follow-up
7. Enforcement and supply-suppression records
8. Social / livelihood / risk and protective factors
9. Cross-border flows or illicit-finance evidence (only if a source actually measures them)
10. Data production, indicator governance, and access restrictions

This layer answers: **what kinds of topic-related material exist, across the available sources and years?** It is not a claim that every source directly measures youth use.

### Layer B — Operational measurement boxes

A child box must say what was measured. Examples:

- Current tobacco use among nationally sampled school-going students aged 13–15, Gambia, GYTS 2017.
- Registered drug-related arrestees aged 17 and below by region, The Gambia, 2023.
- Lifetime cannabis use as measured by the adapted questionnaire in the Banjul senior-secondary-school pilot; survey/reference date and under-18 subgroup availability require review.
- Number of distinct under-18 participants who actually took part in a named prevention programme during a defined period (requires participant roster and consistent definition of participation).
- Under-18 participants' self-reported past-30-day use of a named substance at baseline and a fixed follow-up after programme participation (requires direct outcome measurement and a comparison design for a causal interpretation).

A child box must be specific enough to define its unit, population, substance, reference period, numerator/denominator where applicable, geography, and method. If a field is unknown, keep it `UNKNOWN`; do not silently fill it.

### The two layers should not be collapsed

- The broad inventory keeps a relevant dataset visible even if it does not answer a chosen claim.
- The operational layer prevents a broad phrase like “youth drug use” from merging prevalence, arrests, treatment admissions, programme activity, and causal effects.
- A record can map to the broad inventory but have `INCOMPATIBLE` or `CONCEPTUALLY_RELATED` status against a specific claim.
- A target claim can have an empty direct-evidence cell while related proxy/source material remains visible elsewhere.

## 4. How to decide whether a box is too narrow, too broad, or about right

Use the current candidate CSVs and sources, rather than inventing test observations. Run candidate taxonomies side by side: paper-first, X-first, Y-first, and the recommended hybrid. Review the results at the record level.

### Diagnostics

1. **In-scope retention / orphan rate**
   - Denominator: eligible records under the agreed topic, country, population scope, and search period.
   - Count how many can be assigned to a topic-inventory box without misrepresenting their meaning.
   - A high orphan rate suggests the taxonomy is too narrow, the vocabulary is incomplete, or mapping review is inadequate. Keep an explicit unmapped lane while investigating; do not force records into a false box.

2. **Within-box heterogeneity / collision rate**
   - For records in the same box, compare population, substance, recall period, outcome, unit, denominator, geography, and data-collection method.
   - If one box holds incompatible estimands—such as self-reported prevalence, number of arrests, mass of drugs seized, and programme attendance—it is too broad for analysis and should be split.

3. **Operational testability**
   - Ask whether a reviewer can write down the exact measure, population, substance, period, unit/denominator, and supported inference for the box.
   - If not, the box is too vague for the operational/claim layer. It may still be a valid parent topic box.

4. **Direct-match versus proxy burden**
   - Measure how many candidate relationships are `DIRECT_MATCH`, `HARMONIZABLE`, `PROXY`, `CONCEPTUALLY_RELATED`, `INCOMPATIBLE`, or `UNKNOWN_REQUIRES_REVIEW`.
   - A high proxy/related rate against a specific target is a warning that the target cannot be directly answered; it is not permission to treat proxies as direct. A large number of incompatible constructs inside one box is evidence it should be split.

5. **Empty-but-expected versus arbitrary empty boxes**
   - Keep an empty operational box if it corresponds to a consequential claim in the study brief, a policy commitment, or an explicit source-stated gap. It may be the gap the project needs to show.
   - Review boxes that exist only because one paper used a unique phrase and that have no distinct measurable meaning or research decision attached. Merge them when the concepts are genuinely equivalent.
   - An empty cell alone does not prove a box is too narrow or that data do not exist.

6. **Redundancy and stability**
   - If two boxes routinely receive the same evidence and have no difference in definition, denominator, population, time, or inference, consider merging them.
   - If each newly added source forces another near-duplicate box, the taxonomy is likely source-specific rather than reusable.

These diagnostics should guide reviewer judgement; avoid declaring a fixed universal threshold from a small pilot. Record the number and reason for every split/merge decision so the taxonomy can be audited.

## 5. Examples of too broad, too narrow, and appropriately sized boxes

### Too broad: one box called “youth drug use”

This could inadvertently combine:

- a school survey's self-reported current tobacco use;
- a paper's lifetime cannabis-use question;
- WENDU's counts of under-18 people arrested for drug-related offences;
- drug-induced psychosis cases recorded by health facilities;
- attendance at a prevention awareness activity.

These outcomes have different populations, denominators, recall periods, data-generating processes, and meanings. More items would make the box look dense but would not create a coherent measure of youth drug use.

**Fix:** keep these items in the topic-wide inventory, but separate the operational boxes into self-reported use by substance/recall period, health-service outcomes, enforcement records, and programme exposure/participation.

### Too narrow for the topic inventory: “under-18 Kush use in each LGA in every year”

That is a legitimate future research target only if its specific detail is substantively needed, but current source material may not carry LGA-level, age-specific, substance-specific, repeated survey measurements. If this is the only definition of the overall topic box, it would make all other useful data disappear.

**Fix:** retain a broader parent box such as “substance-specific use measurements”; keep the narrow claim as an operational child/target and show it as not directly answered unless evidence supplies those exact dimensions. Do not spread national figures across LGAs.

### About right: administrative outcome measured by WENDU

“Registered drug-related arrestees aged 17 and below by region, The Gambia, 2023” is a well-defined descriptive administrative box: age cut-off, period, geography, and outcome are reported. The report lists 25 people in the 17-and-below group and provides regional counts. This is **recorded arrests, not prevalence or drug use**. The report separately lists case counts by substance, but the published tables do not give a complete age × substance × region cross-tab; do not infer which substances the minors were arrested for.

### About right: school-survey outcome measured by GYTS

“Current tobacco use among school-going adolescents aged 13–15, nationally, Gambia, 2017” is a reasonably precise survey measurement box for tobacco. It does not measure illicit drug prevalence, community adolescents who are not enrolled in school, or the causal effect of a drug-prevention programme.

## 6. Keep “heat” honest: proposed visual semantics

### View A — topic-wide evidence inventory by concept × observation time

The rows should be a hierarchical topic/operational-concept inventory. The columns should reflect the **actual observation/reference period**. If a source's observation period is not reported, use an explicit `OBSERVATION_PERIOD_UNKNOWN` column/state; do not substitute publication year.

- **Heat/fill:** a categorical or binned representation of inventory presence/density for the relevant concept and period, based on distinct underlying data products or measurement systems—not the number of documents repeating the same statistic.
- **Separate mark/badge/texture:** whether the evidence is direct for the selected claim, only indirect/proxy, known incompatible, or not yet reviewed.
- **Separate evidence-type counts:** keep measured datasets/administrative series, publications, policy/program descriptions, and explicit gap claims distinguishable; do not add their counts into one supposedly comparable quantity.
- **Click-through:** list every contributing source, data product, indicator/variable, underlying observation and citation/location. Include relevant items that have not yet been paired to a claim.
- **Empty/unknown states:** distinguish `NOT_SEARCHED`, `SEARCH_INCOMPLETE`, `SEARCHED_NO_DIRECT_EVIDENCE_FOUND`, `RESTRICTED_ACCESS`, `NOT_REPORTED`, and `NOT_APPLICABLE` where supported. Never infer non-existence from absence in one search.

This makes View A a map of **all relevant topic evidence**, not a heatmap of successful claim-variable matches only.

### View B — target claim × all plausible observed measures

- Show all in-scope candidate measures/variables from the source registry, including ones not yet mapped to a target claim.
- An unreviewed plausible candidate is `UNKNOWN_REQUIRES_REVIEW`, not an absent variable.
- Show incompatible and proxy relations if they are informative, with explicit reason and measurement loss.
- Do not create a fake observation for a target/variable pair just because it is a cell in the matrix.
- Do not generate a full Cartesian product against unrelated variables merely to fill the screen; use the topic inventory to preserve the full data universe and use View B to inspect plausible target-measure relationships.

## 7. Four source-grounded research-question cases

These are research-question templates to test the route **source → variable → observation → alignment → gap**. They are not approval of the sources or a claim that all underlying data have been retrieved. “Unknown” means the public source inspected does not provide the field; it does not mean the data do not exist.

### Case 1 — Descriptive: current tobacco use in school-going minors

**Question:** Among school-going adolescents aged 13–15 in The Gambia, what was the prevalence of current tobacco use under the GYTS 2017 survey definition?

- **Population:** school-going adolescents aged 13–15; this is not every minor in The Gambia.
- **Substance:** tobacco; treat it as its own substance category, not as a proxy for cannabis/Kush or other illicit drugs.
- **Time:** survey observation year 2017 (not the metadata-page creation year).
- **Outcome:** survey-defined current tobacco use; numerator/denominator and any specific item wording should be checked against the questionnaire/codebook before importing numerical observations.
- **Source:** WHO NCD Microdata Repository, *Global Youth Tobacco Survey 2017, Gambia* — https://extranet.who.int/ncdsmicrodata/index.php/catalog/776
- **Variable/observation path:** survey item(s) on current tobacco use → weighted survey estimate/fact sheet or a reproducible estimate from public-use microdata → link to the exact claim.
- **What can be answered:** a direct descriptive measure for this particular school-going age group and tobacco, once the item definition and estimate are verified.
- **What cannot be answered:** illicit-drug prevalence, non-school-going minors, under-18 estimates for every age, prevention programme effectiveness, or a 2026 trend without comparable repeated survey waves.
- **Box implication:** a good specific operational box, but it should remain adjacent/parallel to—not pooled with—illicit-substance use.

### Case 2 — Descriptive administrative outcome: recorded drug-related arrests among minors

**Question:** How many people aged 17 and below were recorded as arrested for drug-related offences in each Gambian administrative region during 2023?

- **Population:** arrestees aged 17 and below (the WENDU table's wording; preserve it rather than silently rewriting the source's age variable).
- **Substance:** drug-related offences aggregated; the age-by-region table does not identify the substance for each minor.
- **Time:** calendar year 2023.
- **Outcome:** recorded arrestee count by region, not prevalence or self-reported use.
- **Source:** ECOWAS, *Fourth WENDU Report: Statistics and Trends on Illicit Drug Use and Supply (2023)*, The Gambia section, report pages 62–64 — https://ecowas.int/wp-content/uploads/2024/10/EN-Rev-Final-Updated-WENDU-Report-2023-Final-Copy.pdf
- **Variable/observation path:** age bracket `17 yrs and below`, region, year, arrestee count → published table reports a total of 25 and regional counts → direct alignment to “recorded under-18 drug-related arrests by region in 2023.”
- **What can be answered:** the recorded geographical distribution of these arrest events/arrestees as reported.
- **What cannot be answered:** youth drug-use prevalence; whether arrests reflect use prevalence; a substance-specific minor-arrest count; or a causal effect of prevention.
- **Important join limitation:** WENDU separately tabulates drug-related case counts by substance, including Kush, but those counts cannot be joined to the under-18 regional table without a supplied cross-tab or linked records. Do not infer under-18 Kush arrests from the separate tables.
- **Box implication:** this is a well-sized box for an administrative descriptive outcome. It must sit separately from self-reported use and substance-specific prevalence.

### Case 3 — Measurement audit: does the Banjul school pilot support a minors-only estimate?

**Question:** In the all-boys senior-secondary-school pilot in Banjul Area Council, does the available measurement record support a separately reported lifetime cannabis-use estimate for respondents younger than 18?

- **Population target:** respondents aged under 18 in the named pilot school; the target subgroup must be verified in the data, not assumed from the word “students.”
- **Substance:** cannabis, kept separate from tobacco and alcohol.
- **Time:** lifetime use at the survey date; the public abstract's fieldwork/observation date is `UNKNOWN` and must not be replaced with the 2025 publication year.
- **Outcome:** binary lifetime cannabis-use response and its subgroup denominator.
- **Source:** Jallow et al., *Drug Abuse among Senior Secondary School Students in Banjul Area Council Zone, The Gambia—A Pilot Study* (2025), DOI 10.33425/2639-8451.1056 — https://www.scivisionpub.com/journals/addiction-research/articles/drug-abuse-among-senior-secondary-school-students-in-banjul-area-council-zone-the-gambia-a-pilot-study
- **Variable/observation path:** adapted WHO student drug-use questionnaire → article abstract reports a single-school, all-male sample with mean age 18.5 (SD 1.33) and an overall lifetime cannabis-use result → alignment to an under-18-only claim remains `UNKNOWN_REQUIRES_REVIEW` until full text, subgroup tables, or authorized microdata are inspected.
- **What can be answered:** the paper is a candidate source for the questionnaire, the broad substance list and an all-sample descriptive result, subject to full-text review.
- **What cannot be answered from the abstract alone:** a minor-only prevalence, national prevalence, a representative regional comparison, or a causal prevention effect.
- **Box implication:** “secondary-school student drug use” is too broad if it silently means “minors.” Preserve the actual age distribution and ask whether the under-18 subgroup can be separated.

### Case 4 — Causal: a youth-led prevention initiative and later use

**Question:** Among participants confirmed to be younger than 18 in the DLEAG–UNDP youth-led prevention initiative, did programme participation reduce self-reported past-30-day Kush use at six months compared with otherwise comparable nonparticipants?

- **Population:** actual programme participants aged under 18; the launch report says “youth” but does not define ages, so minors' participation must first be verified from programme documentation/rosters.
- **Substance:** Kush, proposed as a specific outcome to avoid a vague “any drug” measure. The launch article does not establish that Kush was the programme's sole or intended substance-specific endpoint.
- **Time:** initiative launched on 27 March 2026; proposed outcome is at a fixed six-month follow-up from each participant's actual exposure date. This is a proposed evaluation window, not a claim that follow-up data already exist.
- **Outcome:** individual-level past-30-day self-reported Kush use at baseline and follow-up; compare participants with a credible comparison group. A baseline-to-follow-up change in participants alone is not sufficient for causal identification.
- **Source:** *The Standard*, “DLEAG, UNDP launch youth-led drive to tackle drug abuse,” 2 April 2026 — https://standard.gm/dleag-undp-launch-youth-led-drug-prevention/
- **Variable/observation path:** current public report documents programme launch/partners/date → it does not provide a verified minors' roster, participant denominator, baseline measure, follow-up outcome, or comparison data → alignment is direct only to programme-existence/launch; coverage is unknown; causal-effect alignment is unsupported.
- **What can be answered now:** that a named youth-led drug-prevention initiative was launched with DLEAG and UNDP involvement on the reported date.
- **What cannot be answered now:** reach among minors, change in use, or programme impact.
- **Required next evidence:** age eligibility and roster; dates/intensity/attendance; baseline and six-month outcome definitions; comparator design; attrition; confounders such as baseline use, age, school/community and other prevention exposure; ethics/privacy protections for minors.
- **Box implication:** programme activity/participation, participant characteristics, measured outcome and causal effect are four separate boxes. An event or awareness-session count is not an effect estimate.

## 8. MVP implementation implications

1. **Do not delete or rewrite existing raw CSV records just to fit the new taxonomy.** Keep raw source-native fields and values; add reviewed mapping/classification records through the existing model.
2. **Audit before migration:** report record counts by entity type, candidate source, observed time vs publication time, original age definition, geography level, substance, unit/denominator, source access and review status. Flag duplicated underlying statistics.
3. **Compare the four taxonomies on the same frozen CSV snapshot.** Produce a decision table: included / unmapped / multi-mapped records; concept collisions; direct/proxy/incompatible/unknown relation counts; empty-but-required boxes; and examples of any record that changes status.
4. **Never inflate density:** no national-to-LGA copying, no fabricated years, no inference of juvenile substance from separate aggregated tables, no conversion of arrests/seizures/activity counts into prevalence or effects.
5. **Keep View A and View B distinct:** View A is the topic-wide evidence inventory over time; View B is the target-claim-to-measure relationship audit. They share the same reviewed underlying records, but not the same interpretation of heat.
6. **Document every box split/merge** with rationale and the sources/records affected. No universal numerical cutoff should be chosen based only on a small pilot.

## 9. Source reference list

- ECOWAS, *Fourth WENDU Report: Statistics and Trends on Illicit Drug Use and Supply (2023)*: https://ecowas.int/wp-content/uploads/2024/10/EN-Rev-Final-Updated-WENDU-Report-2023-Final-Copy.pdf
- WHO NCD Microdata Repository, *Global Youth Tobacco Survey 2017, Gambia*: https://extranet.who.int/ncdsmicrodata/index.php/catalog/776
- Jallow et al. (2025), *Drug Abuse among Senior Secondary School Students in Banjul Area Council Zone, The Gambia—A Pilot Study*, DOI: https://doi.org/10.33425/2639-8451.1056
- The Standard (2 Apr 2026), *DLEAG, UNDP launch youth-led drive to tackle drug abuse*: https://standard.gm/dleag-undp-launch-youth-led-drug-prevention/
- WHO Global Health Observatory, *Epidemiological data collection system for substance use among children and adolescents*: https://www.who.int/data/gho/data/indicators/indicator-details/GHO/epidemiological-data-collection-system-for-substance-use-among-children-and-adolescents
- The Gambia National Development Plan 2023–2027: https://mogcsw.gov.gm/wp-content/uploads/2024/09/RF-NDP-2023-2027.pdf

**Status:** Research/design memo. Candidate records, mapped relationships, and proposed causal questions require human review. This memo does not assert that the search is exhaustive or that all underlying datasets have been retrieved.
