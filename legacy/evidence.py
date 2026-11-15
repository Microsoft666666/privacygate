"""Presentation of real synthetic measurements, with denominator-aware labels."""
import platform
import altair as alt
import streamlit as st
from benchmarks.compare import comparison_reports
from legacy import state
from detector import detect
from evaluation import ADVERSARIAL, DATASET, NEGATIVE_CONTROLS, reports, latency_sample


def display_metrics(report: dict) -> dict:
    positive_cases = report["tp"] + report["fn"] > 0
    return {metric: f"{report[metric]:.1%}" if positive_cases else "N/A — no positive cases"
            for metric in ("precision", "recall", "f1")}


def negative_pass_rate(report: dict) -> float:
    return sum(row["result"] == "PASS" for row in report["cases"]) / report["messages"] if report["messages"] else 0.0


def render_evidence() -> None:
    st.subheader("Evidence, not a privacy guarantee")
    st.caption("99 developer-authored synthetic messages, kept in three separate sets. No real-user data or independent benchmark claims.")
    all_reports = reports()
    headings = ["Original baseline", "Adversarial cases", "Negative controls"]
    keys = ["baseline", "adversarial", "negative"]
    for col, title, key, report in zip(st.columns(3), headings, keys, all_reports.values()):
        with col, st.container(key=f"metric_{key}"):
            st.write(f"**{title}** · {report['messages']} messages")
            presented = display_metrics(report)
            if report["tp"] + report["fn"]:
                st.metric("Precision", presented["precision"])
                st.caption(f"Recall {presented['recall']} · F1 {presented['f1']}")
                st.caption(f"{report['tp']} true matches · {report['fp']} false alerts · {report['fn']} missed")
            else:
                st.metric("False alerts", report["fp"])
                st.caption(f"{negative_pass_rate(report):.1%} of negative-control messages passed")
                st.caption("Precision / recall / F1: N/A — no positive cases")
    st.caption("The scorer still uses zero for zero denominators. Negative-only sets show N/A here because positive-class metrics are not informative; their false-alert count and message pass rate are shown instead.")

    chart_rows = [{"Dataset": name.split(' · ')[0], "Metric": metric.title(), "Score": report[metric]}
                  for name, report in all_reports.items() if report["tp"] + report["fn"]
                  for metric in ("precision", "recall", "f1")]
    chart = alt.Chart(alt.Data(values=chart_rows)).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("Dataset:N", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset="Metric:N", y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%"), title="Exact-span score"),
        color=alt.Color("Metric:N", scale=alt.Scale(range=["#2763D9", "#597592", "#172333"])),
        tooltip=["Dataset:N", "Metric:N", alt.Tooltip("Score:Q", format=".1%")]).properties(height=240)
    st.altair_chart(chart, use_container_width=True)
    with st.expander("Accessible score table"):
        st.table([{"Dataset": name, **display_metrics(report), "TP": report["tp"], "FP": report["fp"], "FN": report["fn"]}
                  for name, report in all_reports.items()])

    st.subheader("Regression check · executable before / after")
    comparisons = comparison_reports()
    st.write("Version-labeled numbers are now filtered unless nearby IP/network context takes precedence. The frozen v2 detector is rerun on the same gold annotations below.")
    st.table([{"Dataset": name, "Detector": version, "TP": r['tp'], "FP": r['fp'], "FN": r['fn'], **display_metrics(r)}
              for name, versions in comparisons.items() for version, r in versions.items()])
    st.caption("This fixes the two documented version-string false positives across the sets without losing existing true positives. It is a context heuristic: a real IP mislabeled as a version may be missed. It is not semantic understanding.")

    st.subheader("Where the detector still fails")
    cases = {c.name: c for c in ADVERSARIAL}
    failed_names = list(dict.fromkeys(e["case"] for e in all_reports['Adversarial · extended']["errors"]))[:3]
    for i, name in enumerate(failed_names):
        case = cases[name]
        with st.expander(f"{i + 1} · {name}", expanded=i == 0):
            st.caption("FICTIONAL REPRODUCTION · deliberately includes a known detection limit")
            st.code(case.text, language=None)
            predicted = detect(case.text, case.sensitive_phrases)
            st.text("Expected: " + str(list(case.expected)))
            st.text("Actual: " + str([(f.category, f.start, f.end) for f in predicted]))
            st.button("Load this fictional case in Workspace", key=f"failure_{i}", on_click=state.load_failure, args=(case,))

    with st.expander("Category error matrix & complete case details"):
        name = st.selectbox("Evaluation dataset", list(all_reports), key="eval_dataset")
        report = all_reports[name]
        st.table([{"Category": cat, "TP": m['tp'], "FP": m['fp'], "FN": m['fn'],
                   **display_metrics(m)} for cat, m in report["per_category"].items()])
        if report['errors']:
            st.dataframe(report['errors'], hide_index=True)
        else:
            st.caption("No false alerts in this small negative-control set.")
        st.dataframe([{**row, **display_metrics(row)} for row in report['cases']], hide_index=True)

    st.subheader("Local scanner timing")
    st.caption(f"Python {platform.python_version()} · {platform.system()} {platform.machine()} · excludes browser, UI and network overhead.")
    if st.button("Measure local scanner latency"):
        st.session_state.synthetic_latency = latency_sample()
    if "synthetic_latency" in st.session_state:
        timing = st.session_state.synthetic_latency
        st.info(f"Median {timing['median_ms']:.3f} ms · {timing['runs']} runs · {timing['characters']} synthetic characters. Machine-specific, not a network-performance claim.")
