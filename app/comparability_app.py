import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd
    from vega_datasets import data as vega_data

    from src import PROJECT_ROOT
    from src.schemas.proposal import MAX_PROPOSAL_YEAR, MIN_PROPOSAL_YEAR, Proposal
    from src.scoring.reply import build_public_reply
    from src.scoring.stability import rank_stability

    return (
        MAX_PROPOSAL_YEAR,
        MIN_PROPOSAL_YEAR,
        PROJECT_ROOT,
        Proposal,
        alt,
        build_public_reply,
        mo,
        pd,
        rank_stability,
        vega_data,
    )


@app.cell
def _(mo):
    _interaction_flow = mo.mermaid("""
    flowchart LR
        Proposal["1. Set proposal facts"] --> Start["2. Start here"]
        Start --> Bills["3A. Electric bills"]
        Start --> Air["3B. Air quality"]
        Bills --> Ask["4. Ask a question"]
        Air --> Ask
        Ask --> Robustness["5. Check ranking stability if needed"]
    """)
    mo.vstack(
        [
            mo.md("""
    # Northern Virginia data center comparability

    Visual decision support using published evidence. Follow the path below; each tab
    answers a different question. Similarity scores organize evidence, not predict outcomes.
    """),
            _interaction_flow,
        ],
        gap=1,
    )
    return


@app.cell
def _(MAX_PROPOSAL_YEAR, MIN_PROPOSAL_YEAR, mo):
    proposal_fields = mo.ui.dictionary(
        {
            "locality": mo.ui.text(value="Loudoun", label="County or locality"),
            "utility_territory": mo.ui.dropdown(
                ["Dominion", "NOVEC", "other", "unknown"],
                value="unknown",
                label="Utility territory",
            ),
            "proposed_mw": mo.ui.number(
                start=0, value=100, step=1, label="Proposed capacity (MW)"
            ),
            "filing_year": mo.ui.dropdown(
                {str(year): year for year in range(MIN_PROPOSAL_YEAR, MAX_PROPOSAL_YEAR + 1)},
                value="2026",
                label="Expected or actual filing year",
            ),
            "distance_to_residence_miles": mo.ui.number(
                start=0,
                value=0.5,
                step=0.1,
                label="Distance to nearest residence (miles)",
            ),
            "has_backup_generators": mo.ui.checkbox(
                value=True, label="Proposal has backup generators"
            ),
        },
        label="Proposal inputs",
    )
    proposal_form = mo.ui.form(
        proposal_fields,
        submit_button_label="Set proposal",
        show_clear_button=True,
    )
    proposal_form
    return proposal_fields, proposal_form


@app.cell
def _(mo):
    synthesis_toggle = mo.ui.checkbox(
        value=True,
        label="Validated AI synthesis (turn off for deterministic-only answers)",
    )
    synthesis_toggle
    return (synthesis_toggle,)


@app.cell
def tab_state(mo):
    get_active_tab, set_active_tab = mo.state("Start here")
    return get_active_tab, set_active_tab


@app.cell
def _(
    PROJECT_ROOT,
    Proposal,
    build_public_reply,
    mo,
    pd,
    proposal_fields,
    proposal_form,
    synthesis_toggle,
):
    corpus_path = PROJECT_ROOT / "data" / "processed" / "outcome_corpus.parquet"
    outcome_corpus = pd.read_parquet(corpus_path)
    submitted = proposal_form.value is not None
    proposal_input = proposal_form.value or proposal_fields.value
    proposal = Proposal(
        locality=str(proposal_input["locality"]),
        utility_territory=str(proposal_input["utility_territory"]),
        proposed_mw=float(proposal_input["proposed_mw"]),
        filing_year=int(proposal_input["filing_year"]),
        distance_to_residence_miles=float(proposal_input["distance_to_residence_miles"]),
        has_backup_generators=bool(proposal_input["has_backup_generators"]),
    )

    bill_context = outcome_corpus.loc[
        outcome_corpus["outcome_domain"].eq("bill")
        & outcome_corpus["source_name"].eq("U.S. EIA Form EIA-861")
    ].copy()
    air_context = outcome_corpus.loc[
        outcome_corpus["outcome_domain"].eq("air")
        & outcome_corpus["source_name"].eq("U.S. EPA daily AQI by county")
    ].copy()
    aqi_available_years = sorted(
        int(year) for year in air_context["target_year"].dropna().unique()
    )
    _aqi_years_at_or_before_filing = [
        year for year in aqi_available_years if year <= proposal.filing_year
    ]
    aqi_year = (
        max(_aqi_years_at_or_before_filing)
        if _aqi_years_at_or_before_filing
        else min(aqi_available_years)
    )
    _aqi_source_index = pd.read_csv(
        PROJECT_ROOT / "data" / "raw" / "virginia_daily_aqi_by_county_2015_2026.csv",
        usecols=["date", "county_or_city_name", "county_fips"],
        dtype={"county_fips": "string"},
    )
    _aqi_source_index["date"] = pd.to_datetime(
        _aqi_source_index["date"], errors="coerce"
    )
    aqi_latest_date = _aqi_source_index["date"].max()
    aqi_is_partial = (
        aqi_year == int(aqi_latest_date.year)
        and (aqi_latest_date.month, aqi_latest_date.day) < (12, 31)
    )
    aqi_period_label = (
        f"{aqi_year} partial through {aqi_latest_date.date()}"
        if aqi_is_partial
        else str(aqi_year)
    )
    aqi_year_note = (
        f"Showing proposal-year AQI context for {aqi_period_label}."
        if aqi_year == proposal.filing_year
        else f"No AQI observations exist for {proposal.filing_year}; showing latest available context: {aqi_period_label}."
    )
    bill_data_end_year = int(bill_context["target_year"].max())
    county_fips_lookup = (
        _aqi_source_index[["county_or_city_name", "county_fips"]]
        .dropna()
        .drop_duplicates("county_or_city_name")
    )
    aqi_map_data = air_context.loc[air_context["target_year"].eq(aqi_year)].merge(
        county_fips_lookup,
        left_on="geography_or_territory",
        right_on="county_or_city_name",
        how="left",
    )
    aqi_map_data["county_fips"] = pd.to_numeric(
        aqi_map_data["county_fips"], errors="coerce"
    ).astype("Int64")

    def _normalize_locality(value):
        return str(value).casefold().replace(" county", "").replace(" city", "").strip()

    aqi_map_data["is_selected"] = aqi_map_data["geography_or_territory"].map(
        _normalize_locality
    ).eq(_normalize_locality(proposal.locality))
    selected_aqi = aqi_map_data.loc[aqi_map_data["is_selected"]]

    if not submitted:
        resident_interface = mo.callout(
            "Submit proposal inputs to activate evidence questions.",
            kind="info",
            title="Chat waits for a proposal",
        )
    else:
        def _resident_model(messages, config):
            del config
            return mo.md(
                build_public_reply(
                    str(messages[-1].content),
                    proposal,
                    outcome_corpus,
                    use_model_synthesis=bool(synthesis_toggle.value),
                )
            )

        resident_interface = mo.ui.chat(
            _resident_model,
            prompts=[
                "Why is this bill evidence a good match?",
                "What does the air map show for my county?",
                "What do the DEQ permits say about backup generators?",
                "Compare the bill and air evidence for this proposal.",
                "Can this prototype tell me what my bill will be?",
            ],
            show_configuration_controls=False,
            max_height=460,
        )
    return (
        aqi_map_data,
        aqi_period_label,
        aqi_year,
        aqi_year_note,
        bill_context,
        bill_data_end_year,
        outcome_corpus,
        proposal,
        resident_interface,
        selected_aqi,
    )


@app.cell
def _(mo, outcome_corpus, pd, proposal, rank_stability):
    stability_report = pd.concat(
        [
            rank_stability(proposal, outcome_corpus, "bill"),
            rank_stability(proposal, outcome_corpus, "air"),
        ],
        ignore_index=True,
    )
    stability_churn = int(stability_report["top_k_churn"].max())
    stability_order_changes = int((~stability_report["same_order"]).sum())
    _stability_title = (
        "Top matches stayed the same"
        if stability_churn == 0
        else "Some top matches changed"
    )
    _stability_message = (
        "We slightly increased and decreased each ranking priority, one at a time. "
        + (
            "The same three records remained on top in every test."
            if stability_churn == 0
            else f"At most {stability_churn} of the top three records was replaced."
        )
        + " This checks ranking consistency only; it does not prove the evidence is complete."
    )
    stability_panel = mo.vstack(
        [
            mo.callout(
                _stability_message,
                kind="success" if stability_churn == 0 else "warn",
                title=_stability_title,
            ),
            mo.hstack(
                [
                    mo.stat(
                        "No replacements" if stability_churn == 0 else str(stability_churn),
                        label="Largest change to top three",
                        bordered=True,
                    ),
                    mo.stat(
                        str(stability_order_changes),
                        label="Tests that changed order",
                        bordered=True,
                    ),
                    mo.stat(
                        str(len(stability_report)),
                        label="Small priority changes tested",
                        bordered=True,
                    ),
                ],
                widths="equal",
                gap=1,
            ),
            mo.accordion(
                {
                    "Show technical details": mo.ui.table(
                        stability_report[
                            [
                                "domain",
                                "feature",
                                "multiplier",
                                "top_k_churn",
                                "jaccard",
                                "same_order",
                            ]
                        ],
                        pagination=True,
                        page_size=8,
                    )
                }
            ),
        ],
        gap=1,
    )
    return (stability_panel,)


@app.cell
def _(PROJECT_ROOT, mo, pd):
    _manifest = pd.read_csv(PROJECT_ROOT / "provenance" / "manifest.csv")

    def _status(notes: str) -> str:
        if "Verified via WebFetch" in notes:
            return "Verified"
        if "403 Forbidden" in notes or "TLS certificate" in notes:
            return "Blocked (source refused fetch)"
        return "Unverified"

    def _url(value) -> str | None:
        return value if isinstance(value, str) and value.startswith("http") else None

    _rows = []
    for _source, _group in _manifest.groupby("source", sort=False):
        _first = _group.iloc[0]
        _rows.append(
            {
                "Source": _source,
                "Delivered files": len(_group),
                "Verification status": _status(str(_first.get("notes", ""))),
                "URL": _url(_first.get("query_or_url")),
                "Pull-date basis": _first.get("date_basis"),
            }
        )
    source_summary = pd.DataFrame(_rows)
    source_panel = mo.vstack(
        [
            mo.callout(
                "Read-only summary of where each delivered dataset came from. "
                "\"Verified\" means a fetched page or document was checked this "
                "session and matched the described source. \"Blocked\" means the "
                "source domain refused automated access. \"Unverified\" means no "
                "URL has been confirmed yet. Full per-file detail, including why "
                "each field is null or unconfirmed, is in provenance/manifest.csv.",
                kind="info",
                title="How to read this table",
            ),
            mo.ui.table(source_summary, pagination=False),
        ],
        gap=1,
    )
    return (source_panel,)


@app.cell
def decision_dashboard(
    alt,
    aqi_map_data,
    aqi_period_label,
    aqi_year,
    aqi_year_note,
    bill_context,
    bill_data_end_year,
    get_active_tab,
    mo,
    outcome_corpus,
    pd,
    proposal,
    resident_interface,
    selected_aqi,
    set_active_tab,
    source_panel,
    stability_panel,
    vega_data,
):
    _deq_permit_count = int(outcome_corpus["source_name"].eq("Virginia DEQ issued data center air permits").sum())
    _deq_emission_count = int(outcome_corpus["source_name"].eq("Virginia DEQ 2015 criteria emissions inventory").sum())
    _counties = alt.topo_feature(vega_data.us_10m.url, "counties")
    _air_map_chart = (
        alt.Chart(_counties)
        .mark_geoshape()
        .transform_filter((alt.datum.id >= 51000) & (alt.datum.id < 52000))
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                aqi_map_data,
                "county_fips",
                ["geography_or_territory", "value_low", "value_high", "is_selected"],
            ),
        )
        .encode(
            color=alt.condition(
                "isValid(datum.value_high)",
                alt.Color(
                    "value_high:Q",
                    title=f"Highest daily AQI ({aqi_period_label})",
                    scale=alt.Scale(scheme="yelloworangered"),
                ),
                alt.value("#e5e7eb"),
            ),
            stroke=alt.condition(
                "datum.is_selected === true", alt.value("#2563eb"), alt.value("#ffffff")
            ),
            strokeWidth=alt.condition(
                "datum.is_selected === true", alt.value(3), alt.value(0.6)
            ),
            tooltip=[
                alt.Tooltip("geography_or_territory:N", title="Locality"),
                alt.Tooltip("value_low:Q", title="Lowest daily AQI"),
                alt.Tooltip("value_high:Q", title="Highest daily AQI"),
            ],
        )
        .project(type="albersUsa")
        .properties(
            width="container",
            height=360,
            title={
                "text": f"Virginia county AQI context, {aqi_period_label}",
                "subtitle": f"Blue outline: {proposal.locality}; gray: no delivered observation",
            },
        )
    )
    _air_map_view = mo.ui.altair_chart(
        _air_map_chart, chart_selection=False, legend_selection=False
    )

    _air_bar_chart = (
        alt.Chart(aqi_map_data.dropna(subset=["value_high"]))
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("geography_or_territory:N", sort="-x", title=None),
            x=alt.X("value_high:Q", title=f"Highest daily AQI in {aqi_period_label}"),
            color=alt.condition(
                alt.datum.is_selected,
                alt.value("#2563eb"),
                alt.value("#f59e0b"),
            ),
            tooltip=[
                alt.Tooltip("geography_or_territory:N", title="Locality"),
                alt.Tooltip("value_low:Q", title="Lowest daily AQI"),
                alt.Tooltip("value_high:Q", title="Highest daily AQI"),
            ],
        )
        .properties(width="container", height=250)
    )
    _air_bar_view = mo.ui.altair_chart(
        _air_bar_chart, chart_selection=False, legend_selection=False
    )

    _bill_lines = (
        alt.Chart(bill_context)
        .mark_line(point=alt.OverlayMarkDef(filled=True, size=55), strokeWidth=3)
        .encode(
            x=alt.X("target_year:O", title="Year"),
            y=alt.Y(
                "value_high:Q",
                title="Residential average price (cents/kWh)",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color("utility_territory:N", title="Utility territory"),
            tooltip=[
                alt.Tooltip("utility_territory:N", title="Utility"),
                alt.Tooltip("target_year:O", title="Year"),
                alt.Tooltip("value_high:Q", title="Cents/kWh", format=".2f"),
            ],
        )
    )
    _filing_rule = (
        alt.Chart(pd.DataFrame({"filing_year": [proposal.filing_year]}))
        .mark_rule(color="#6b7280", strokeDash=[6, 4], size=2)
        .encode(x=alt.X("filing_year:O"))
    )
    _bill_chart = (_bill_lines + _filing_rule).properties(
        width="container",
        height=300,
        title={
            "text": "Delivered Virginia residential utility context",
            "subtitle": "Dashed line: proposal filing year; EIA-861 averages are context, not project impacts",
        },
    )
    _bill_chart_view = mo.ui.altair_chart(
        _bill_chart, chart_selection=False, legend_selection=False
    )

    _selected_aqi_value = (
        f"No delivered {aqi_year} AQI row"
        if selected_aqi.empty
        else f"{selected_aqi.iloc[0]['value_high']:.0f} max"
    )
    _territory_kind = "success" if proposal.utility_territory == "Dominion" else "warn"
    _territory_text = (
        "Dominion input: JLARC regional projection can be shown with transfer limits."
        if proposal.utility_territory == "Dominion"
        else "Dominion applicability blocked until utility territory is verified as Dominion."
    )
    _summary_stats = mo.hstack(
        [
            mo.stat(f"{proposal.proposed_mw:g} MW", label="Proposed scale", bordered=True),
            mo.stat(str(proposal.filing_year), label="Filing year", bordered=True),
            mo.stat(_selected_aqi_value, label=f"{proposal.locality} AQI context", bordered=True),
            mo.stat(proposal.utility_territory, label="Utility input", bordered=True),
        ],
        widths="equal",
        gap=1,
    )
    _overview = mo.vstack(
        [
            mo.callout(
                "Start here after submitting the form. Confirm proposal facts, check utility-territory warnings, and scan which evidence is available before opening a topic tab.",
                kind="info",
                title="How to use this view",
            ),
            _summary_stats,
            mo.hstack(
                [
                    _air_map_view,
                    mo.vstack(
                        [
                            mo.callout(_territory_text, kind=_territory_kind, title="Territory check"),
                            mo.callout(
                                "County AQI is measured locality context. It cannot attribute air quality to one data center or generator fleet.",
                                kind="info",
                                title="How far the map carries",
                            ),
                            mo.callout(
                                f"{_deq_permit_count} Northern Virginia DEQ permit records are extracted and labeled permitted—not measured. Generator fleet totals, aggregate capacity, and original permit URLs remain unavailable or unverified.",
                                kind="warn",
                                title="Permit evidence limits",
                            ),
                        ],
                        gap=1,
                    ),
                ],
                widths=[2, 1],
                align="start",
                gap=1.5,
            ),
        ],
        gap=1.25,
    )
    _bill_panel = mo.vstack(
        [
            mo.callout(
                f"Use this tab to compare historical residential utility prices through {bill_data_end_year} and understand the JLARC regional projection. The chart provides context; it does not calculate this project's effect on a household bill.",
                kind="info",
                title="How to read electric-bill evidence",
            ),
            _bill_chart_view,
            mo.callout(
                f"The line ends in {bill_data_end_year} because that is the final year in the delivered EIA-861 data. The prototype does not extend the line because later values would require a separate forecast.",
                kind="neutral",
                title=f"Why the chart stops at {bill_data_end_year}",
            ),
            mo.callout(
                "JLARC projects $14–$37 per month by 2040 for a typical Dominion residential customer in constant 2024 dollars. It is projected, regional evidence, not a single-project bill estimate.",
                kind="info",
                title="Bill anchor and transfer limit",
            ),
        ],
        gap=1,
    )
    _air_panel = mo.vstack(
        [
            mo.callout(
                f"{aqi_year_note} Use the map to locate your county, then use the bars to compare its highest monitored AQI day with nearby localities. Resubmit the proposal after changing its year. These displays describe ambient conditions, not emissions from a proposed site.",
                kind="info",
                title="How to read air-quality context",
            ),
            _air_map_view,
            _air_bar_view,
            mo.callout(
                f"Permit records describe regulatory limits, not actual emissions. The {_deq_emission_count} matched 2015 inventory rows are historical facility-wide measurements—not generator-only or current emissions.",
                kind="warn",
                title="Permitted versus measured",
            ),
            mo.callout(
                "Map and bars show annual daily AQI range from government monitoring. They do not measure data-center-attributable emissions.",
                kind="info",
                title="Measured context, not project outcome",
            ),
        ],
        gap=1,
    )
    _ask_panel = mo.vstack(
        [
            mo.callout(
                "Ask one question about the displayed evidence. Answers use plain language, cite one best-matching record, and explain what it cannot establish.",
                kind="info",
                title="How to use evidence questions",
            ),
            resident_interface,
        ],
        gap=1,
    )
    _method_panel = mo.vstack(
        [
            mo.callout(
                "Optional check. It slightly changes each ranking priority and reports whether the same evidence stays near the top. Most residents can rely on the summary and leave technical details collapsed.",
                kind="info",
                title="What ranking stability means",
            ),
            stability_panel,
        ],
        gap=1,
    )
    dashboard = mo.ui.tabs(
        {
            "Start here": _overview,
            "Electric bills": _bill_panel,
            "Air quality": _air_panel,
            "Ask a question": _ask_panel,
            "Ranking stability": _method_panel,
            "Data sources": source_panel,
        },
        value=get_active_tab(),
        on_change=set_active_tab,
        lazy=True,
    )
    _build_notes = mo.callout(
        mo.md(
            "- **LandMARC exports are capped at 1,000 rows per file** by the "
            "source portal; five permit-export files delivered under different "
            "date-range names turned out byte-identical, so the filenames' "
            "implied date slicing is not real.\n"
            "- **194 DEQ air-permit PDFs were extracted locally**; 36 have "
            "OCR/text-encoding corruption severe enough to exclude them from "
            "numeric fields. Generator fleet totals were filled only where a "
            "permit has exactly one unambiguous equipment table with no "
            "amendment history — amendments, mixed fleets, or split tables "
            "are left null rather than estimated.\n"
            "- **DEQ's site blocks automated URL verification** (HTTP 403 to "
            "every fetch attempt). Most permit-PDF source URLs were instead "
            "recovered from a manually supplied browser export and matched "
            "back to files by registration number; a couple of rows stayed "
            "unverified rather than guessed.\n"
            "- **LandMARC has no project-scale (MW) field**, and daily AQI "
            "readings are locality-level context only — neither can be "
            "attributed to a specific site or generator."
        ),
        kind="neutral",
        title="Data gaps navigated building this prototype",
    )
    mo.vstack([dashboard, _build_notes], gap=1)
    return


if __name__ == "__main__":
    app.run()
