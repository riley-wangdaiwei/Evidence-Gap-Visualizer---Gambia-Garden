# Visual semantics

The app shell is near-black (`#050505`), left aligned, white type, serif display/reading text, and small mono metadata. Matrix figures use paper `#0B1016`, inner water/background `#0A1119`, and off-white vector marks `#E8EEF2`. The land token `#17222C` is reserved for actual land polygons; this build has no boundary geometry and does not paint matrix cells as land.

Gap and mismatch colors remain semantic: low documented problem is muted teal, medium/proxy is amber, higher mismatch or searched-without-direct-hit is restrained rust/crimson. Unknown uses neutral charcoal and a visible `///` hatch label. Unknown is never encoded as a numeric zero. Each matrix page renders its own legend.

View A arrows point evidence/comparator → target gap. View B arrows point observed variable/series → target indicator. The `R`/`H` marker and hover detail identify RULE_DERIVED or HUMAN_REVIEWED provenance. Width is the number of deduplicated independent sources; line length does not encode evidence or importance. No LLM-derived links are implemented.

Wind means a modeled research-connection field and stays disabled until the directed relation network and valid coordinates exist. Friction markers represent typed evidence/access barriers, not the social harm under study; selecting a marker displays the barrier evidence and verification status. Geography and observation level are shown from source records. National-only evidence can produce a subnational disaggregation warning, but its value and source counts are never copied into an LGA/border-area cell.
