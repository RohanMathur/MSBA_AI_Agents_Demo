"""
Fixed executive report template. Same structure every run—repeatable and dependable.
Uses the 4-part dispatch structure: Plan Summary (from data), Monitoring, Contingency, KPI Impacts (from planner).
"""
from __future__ import annotations
import re
from typing import Dict, Any, Tuple
from datetime import datetime


_STYLES = """
  body { font-family: 'Segoe UI', system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; color: #1a1a1a; line-height: 1.5; }
  h1 { font-size: 1.75rem; font-weight: 700; color: #0d47a1; border-bottom: 3px solid #0d47a1; padding-bottom: 10px; margin: 0 0 20px 0; }
  h2 { font-size: 1.25rem; font-weight: 600; color: #1565c0; margin: 28px 0 14px 0; }
  h3 { font-size: 1.05rem; font-weight: 600; color: #333; margin: 18px 0 8px 0; }
  .meta { font-size: 0.85rem; color: #666; margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.9rem; }
  th, td { text-align: left; padding: 10px 14px; border: 1px solid #e0e0e0; }
  th { background: #e3f2fd; font-weight: 600; color: #0d47a1; }
  .report-includes-table th { background: #f5f5f5; color: #333; }
  .risk-low { color: #2e7d32; }
  .risk-mid { color: #f9a825; }
  .risk-high { color: #c62828; }
  .section-block { margin-bottom: 24px; }
  .subsection { margin-bottom: 20px; }
  ul { margin: 10px 0; padding-left: 22px; }
  .subhead { font-weight: 600; color: #333; margin: 14px 0 6px 0; font-size: 0.95rem; }
  .footer { font-size: 0.8rem; color: #888; margin-top: 36px; padding-top: 16px; border-top: 1px solid #eee; }
"""

# Human-readable labels for KPIs (no raw column names in report)
METRIC_LABELS = {
    "total_shipments": "Total shipments",
    "total_columns": "Total columns",
    "numeric_columns_count": "Numeric columns",
    "shipments_with_missing_unique_item_id": "Shipments missing unique ID",
    "valid_shipments_unique_item_id": "Shipments with valid unique ID",
    "shipments_with_missing_item_id": "Shipments missing item ID",
    "valid_shipments_item_id": "Shipments with valid item ID",
    "shipments_with_missing_dispatch_location": "Shipments missing dispatch location",
    "valid_shipments_dispatch_location": "Shipments with valid dispatch location",
    "excluded_shipments_missing_unique_id": "Excluded (missing unique ID)",
    "valid_shipment_count": "Valid shipment count",
    "dispatch_location_breakdown": "By dispatch location",
    "item_breakdown": "By item",
    "estimated_volume_units": "Estimated volume (units)",
    "total_volume_units": "Total volume (units)",
    "volume_per_shipment_assumed": "Volume per shipment (assumed)",
    "volume_source": "Volume source",
    "buffered_volume_units": "Volume with 10% buffer (units)",
    "required_trucks": "Required trucks",
}


def _metric_label(key: str) -> str:
    return METRIC_LABELS.get(key, key.replace("_", " ").title())


def _bold_important(escaped_html: str) -> str:
    """Wrap important numbers/percentages in <strong> (run on already-escaped text)."""
    if not escaped_html:
        return escaped_html
    s = re.sub(r"(\d+(?:\.\d+)?%)", r"<strong>\1</strong>", escaped_html)
    s = re.sub(r"(\d+)\s+of\s+(\d+)", r"<strong>\1</strong> of <strong>\2</strong>", s)
    s = re.sub(r"(\d+)/3\b", r"<strong>\1/3</strong>", s)
    return s


def _escape(s: str) -> str:
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fmt(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, dict):
        return ", ".join(f"{k}: {v}" for k, v in list(val.items())[:5])
    return str(val)


def _md_to_html(text: str) -> str:
    """Convert simple markdown (bullets, sub-headers, newlines) to HTML for planner sections."""
    if not text or not text.strip():
        return "<p>No content.</p>"
    lines = text.strip().split("\n")
    html_parts = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            content = _escape(stripped[2:].strip())
            html_parts.append("<li>" + _bold_important(content) + "</li>")
        elif stripped.endswith(":") and len(stripped) < 60:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<p class=\"subhead\">" + _escape(stripped) + "</p>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            content = _escape(stripped)
            html_parts.append("<p>" + _bold_important(content) + "</p>")
    if in_list:
        html_parts.append("</ul>")
    return "".join(html_parts)


def _parse_planner_sections(dispatch_plan: str) -> Tuple[str, str, str]:
    """Extract ## 2. Monitoring Focus Areas, ## 3. Contingency Triggers, ## 4. Expected KPI Impacts."""
    section_2 = section_3 = section_4 = ""
    if not dispatch_plan or not dispatch_plan.strip():
        return section_2, section_3, section_4
    text = dispatch_plan.strip()
    # Split by ## 2. / ## 3. / ## 4. (allow optional space after ##)
    parts = re.split(r"\n?##\s*2\.\s*Monitoring Focus Areas\s*\n?", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) >= 2:
        rest = parts[1]
        parts3 = re.split(r"\n?##\s*3\.\s*Contingency Triggers\s*\n?", rest, maxsplit=1, flags=re.IGNORECASE)
        if len(parts3) >= 2:
            section_2 = parts3[0].strip()
            rest = parts3[1]
            parts4 = re.split(r"\n?##\s*4\.\s*Expected KPI Impacts\s*\n?", rest, maxsplit=1, flags=re.IGNORECASE)
            if len(parts4) >= 2:
                section_3 = parts4[0].strip()
                section_4 = parts4[1].strip()
            else:
                section_3 = rest.strip()
        else:
            section_2 = rest.strip()
    else:
        # Fallback: treat whole thing as section 2
        section_2 = text
    return section_2, section_3, section_4


def _build_section1_dispatch_plan_summary(
    kpis: Dict[str, Any],
    weather_risk: Dict[str, Any],
    ops_insights: str,
    business_context: str,
) -> str:
    """Section 1: Dispatch Plan Summary (Next 24-48h) — built from real data only."""
    total = kpis.get("total_shipments", 0)
    valid = kpis.get("valid_shipment_count", total)
    excluded = kpis.get("excluded_shipments_missing_unique_id", 0)
    pct = round(100 * excluded / total, 0) if total else 0
    required_trucks = kpis.get("required_trucks")
    volume_source = kpis.get("volume_source", "estimated")
    estimated_vol = kpis.get("estimated_volume_units") or kpis.get("total_volume_units")
    buffered_vol = kpis.get("buffered_volume_units")
    vol_per_ship = kpis.get("volume_per_shipment_assumed")

    # Shipment Data Cleaning (friendly names: "unique ID" not unique_item_id)
    cleaning = (
        f"<p>Exclude <strong>{excluded}</strong> of <strong>{total}</strong> shipment rows missing unique ID ({pct:.0f}% per policy). "
        "Quarantine rows with item ID mismatches or duplicates upon further validation.</p>"
    )
    if ops_insights and ops_insights.strip():
        ops_escaped = _escape(ops_insights.strip()[:400]).replace(chr(10), "<br>")
        cleaning += f"<p>{_bold_important(ops_escaped)}</p>"

    # Volume & Truck Calculation — computed when possible
    if required_trucks is not None and estimated_vol is not None and buffered_vol is not None:
        if volume_source == "from_data":
            volume_note = (
                f"<p>Total volume from data: <strong>{estimated_vol:,}</strong> units. "
                f"With 10% packing buffer: <strong>{buffered_vol:,}</strong> units. "
                f"Truck capacity 10,000 units → <strong>{required_trucks}</strong> truck(s) required.</p>"
            )
        else:
            volume_note = (
                f"<p>Estimated volume from <strong>{valid}</strong> valid shipments "
                + (f"(<strong>{vol_per_ship:,}</strong> units per shipment assumed): <strong>{estimated_vol:,}</strong> units. ")
                + f"With 10% buffer: <strong>{buffered_vol:,}</strong> units. "
                + f"Truck capacity 10,000 units → <strong>{required_trucks}</strong> truck(s) required.</p>"
            )
    else:
        volume_note = (
            "<p>Total volume calculated from valid shipments. Apply 10% packing buffer. "
            "Standard truck capacity: 10,000 volume units. "
            "Required trucks = ceil((volume × 1.10) / 10,000). "
            "<em>This run: no volume column in data; add volume column or see Appendix for shipment counts.</em></p>"
        )

    # Cold-Chain Compliance
    cold_chain = "<p>Confirm allocation of temperature-controlled trucks if cold-chain items present.</p>"

    # Weather Risk & Travel Buffer (humanize flag names: freezing_risk → Freezing risk)
    score = weather_risk.get("risk_score_0_3", 0)
    flags = weather_risk.get("risk_flags") or {}
    wind = weather_risk.get("max_wind_gust_kmh")
    min_temp = weather_risk.get("min_temp_c")
    score_class = "risk-low" if score == 0 else ("risk-mid" if score == 1 else "risk-high")
    active_flags = [k.replace("_", " ").title() for k, v in flags.items() if v]
    weather_blurb = (
        f"<p>Weather risk score: <span class=\"{score_class}\"><strong>{score}/3</strong></span>. "
        + (f"Max wind gust: <strong>{wind} km/h</strong>. " if wind is not None else "")
        + (f"Min temp: <strong>{min_temp} °C</strong>. " if min_temp is not None else "")
        + (f"Active flags: {_escape(', '.join(active_flags))}. " if active_flags else "")
        + "Apply travel time buffer of +15% when high wind or freezing risk present.</p>"
    )

    # SLA Adherence
    sla = (
        "<p>Tier 1 (life-critical medicine) max time-in-transit: 6 hours. "
        "Estimated travel times adjusted by +15% buffer when applicable. "
        "Flag dispatch plans exceeding SLA after buffer application.</p>"
    )

    # Dispatch Report Includes (table) — use computed trucks when available
    trucks_val = f"{required_trucks} (from volume calculation above)" if required_trucks is not None else "See volume calculation above"
    checklist_rows = [
        ("Valid vs excluded shipments", f"{valid} valid, {excluded} excluded (missing unique ID)"),
        ("Trucks required", trucks_val),
        ("Weather risk summary", f"{score}/3" + (f" — {', '.join(active_flags)}" if active_flags else "")),
        ("Applied travel buffer", "+15% when wind or freezing risk present"),
        ("SLA risk flags", "Any routes exceeding max transit times"),
    ]
    checklist_table = (
        "<table class=\"report-includes-table\"><thead><tr><th>Item</th><th>Value</th></tr></thead><tbody>"
        + "".join(f"<tr><td>{_escape(label)}</td><td>{_escape(val)}</td></tr>" for label, val in checklist_rows)
        + "</tbody></table>"
    )

    return (
        f"<div class=\"subsection\"><h3>Shipment Data Cleaning</h3>{cleaning}</div>"
        f"<div class=\"subsection\"><h3>Volume &amp; Truck Calculation</h3>{volume_note}</div>"
        f"<div class=\"subsection\"><h3>Cold-Chain Compliance</h3>{cold_chain}</div>"
        f"<div class=\"subsection\"><h3>Weather Risk &amp; Travel Buffer</h3>{weather_blurb}</div>"
        f"<div class=\"subsection\"><h3>SLA Adherence</h3>{sla}</div>"
        f"<div class=\"subsection\"><h3>Dispatch Report Includes</h3>{checklist_table}</div>"
    )


def build_report_html(
    *,
    business_context: str = "",
    kpis: Dict[str, Any] | None = None,
    ops_insights: str = "",
    anomaly_highlights: str = "",
    weather_risk: Dict[str, Any] | None = None,
    dispatch_plan: str = "",
) -> str:
    kpis = kpis or {}
    weather_risk = weather_risk or {}

    section1 = _build_section1_dispatch_plan_summary(kpis, weather_risk, ops_insights, business_context)
    mon, cont, kpi_imp = _parse_planner_sections(dispatch_plan)
    section2_html = _md_to_html(mon) if mon else "<p>No content.</p>"
    section3_html = _md_to_html(cont) if cont else "<p>No content.</p>"
    section4_html = _md_to_html(kpi_imp) if kpi_imp else "<p>No content.</p>"

    # Appendix: anomaly highlights + business context excerpt + KPIs table
    anomalies = _escape(anomaly_highlights or "No anomalies or insufficient numeric data.").replace("\n", "<br>")
    ctx = _escape((business_context or "")[:600]).replace("\n", "<br>")
    if len((business_context or "")) > 600:
        ctx += "..."
    kpi_rows = "".join(
        f"<tr><td>{_escape(_metric_label(k))}</td><td>{_escape(_fmt(v))}</td></tr>"
        for k, v in list(kpis.items())[:25]
    )
    kpi_table = f"<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>{kpi_rows}</tbody></table>"
    appendix = (
        f"<h3>Anomaly highlights</h3><p>{anomalies}</p>"
        f"<h3>Business context (excerpt)</h3><p>{ctx}</p>"
        f"<h3>All KPIs</h3>{kpi_table}"
    )

    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Dispatch Operations Report</title>
  <style>{_STYLES}</style>
</head>
<body>
  <h1>Dispatch Operations Report</h1>
  <p class="meta">Generated {date_str} · MSBA AI Agents Demo</p>

  <h2>1. Dispatch Plan Summary (Next 24-48h)</h2>
  <div class="section-block">{section1}</div>

  <h2>2. Monitoring Focus Areas</h2>
  <div class="section-block">{section2_html}</div>

  <h2>3. Contingency Triggers</h2>
  <div class="section-block">{section3_html}</div>

  <h2>4. Expected KPI Impacts</h2>
  <div class="section-block">{section4_html}</div>

  <h2>Appendix</h2>
  <div class="section-block">{appendix}</div>

  <p class="footer">This report was generated automatically. Section 1 uses real data from CSV and weather API; sections 2–4 are agent-generated from that data.</p>
</body>
</html>"""
