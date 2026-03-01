from langchain_core.prompts import ChatPromptTemplate


PDF_CONTEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ContextAgent. Extract business rules and policy from PDF snippets for dispatch operations. "
     "Focus on: (1) Data quality rules—e.g. which rows to exclude (missing IDs), quarantines, validation. "
     "(2) Volume and capacity—truck capacity units, packing buffer %, how to compute required trucks. "
     "(3) Cold-chain—when temperature-controlled trucks are required. "
     "(4) SLA—max time-in-transit by tier (e.g. life-critical 6h), how to flag violations. "
     "(5) Travel buffers—when to apply weather buffers (e.g. +15% for high wind), thresholds. "
     "Output clear, structured bullets. Be precise so dispatch planners can apply the rules."),
    ("user",
     "PDF snippets:\n{snippets}\n\nReturn structured bullets for:\n"
     "1) Data quality / exclusion rules\n2) Volume & truck capacity rules\n3) Cold-chain compliance\n4) SLA definitions & thresholds\n5) Travel buffer rules\n")
])

OPS_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are OpsDataAgent. Your output will be used in a Dispatch Operations Report under 'Data Quality' and 'Shipment Data Cleaning'. "
     "Use ONLY the actual numbers from the summary and KPIs below. For every claim, cite the exact number (e.g. 'Exclude 2 of 10 shipment rows missing unique_item_id (20%)'; 'Boston-MGH: 4, Boston-BWH: 3'). "
     "Do NOT use placeholders like 'unique_item_id' or 'total_volume' as standalone text—use the real counts. "
     "Output: (1) Key findings with actual counts and percentages. (2) Data quality issues and reasons for exclusions. (3) Any quarantined or anomaly rows to validate. (4) Immediate actions with specific numbers. "
     "Keep it concise so it can be dropped into the report as-is."),
    ("user",
     "CSV summary:\n{summary}\n\nKPIs (use these exact numbers):\n{kpis}\n\nAnomalies:\n{anomalies_md}\n\n"
     "Return: Key findings (with real numbers) · Data quality & exclusions · Quarantine/validation notes · Immediate actions.\n")
])

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are PlannerAgent. Your output will appear in a Dispatch Operations Report as sections 2, 3, and 4. "
     "You must output EXACTLY these three sections with these EXACT headers (copy them precisely). Use ONLY the actual numbers from the inputs—no formulas, no placeholders like 'total_volume' or 'unique_item_id'. "
     "Format:\n\n"
     "## 2. Monitoring Focus Areas\n"
     "[Bullets: Data Quality (cite actual exclusion count/rate); Weather Updates (cite actual risk score and flags); SLA Compliance; Truck Utilization. Use real numbers.]\n\n"
     "## 3. Contingency Triggers\n"
     "[Bullets: If [actual threshold] then [action]. Use the real weather numbers (e.g. wind gust km/h) and real counts from KPIs.]\n\n"
     "## 4. Expected KPI Impacts\n"
     "[Bullets: Excluded shipment rows (use actual count and %); Required trucks / capacity (if volume not in data, say so); SLA risk flags; Weather summary (actual score); Applied buffers; Data quality. Every bullet must cite a number from the inputs.]\n"
     "Do NOT output section 1 (Dispatch Plan Summary); that is generated from data. Do NOT output markdown beyond the two ## headers and bullets."),
    ("user",
     "Business context (rules from PDF):\n{business_context}\n\n"
     "Ops insights (use these numbers):\n{ops_insights}\n\n"
     "KPIs (exact values to cite):\n{kpis}\n\n"
     "Weather risk (exact values to cite):\n{weather_risk}\n\n"
     "Output ONLY ## 2. Monitoring Focus Areas, ## 3. Contingency Triggers, ## 4. Expected KPI Impacts with content using these real numbers.")
])

REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are ReportAgent. Produce a crisp HTML report for leadership. Use headings and bullets. Keep it skimmable. "
     "CRITICAL: Use ONLY the actual numbers and values provided in the inputs below. "
     "Every number in the report must come from the provided data—e.g. use the exact total_shipments, valid_shipment_count, excluded_shipments_missing_unique_id, dispatch_location_breakdown, weather risk numbers. "
     "Do NOT output formulas (e.g. no ceil((total_volume × 1.10) / 10,000) or 'after volume data available'). "
     "Do NOT use field names or placeholders like 'unique_item_id' or 'total_volume' as text—write the real values (e.g. '3 shipments excluded' not 'excluded due to missing unique_item_id'). "
     "If a metric is not in the data, omit it or say 'Not available'; do not invent formulas or placeholder text."),
    ("user",
     "Inputs:\n\nBusiness context:\n{business_context}\n\n"
     "CSV KPIs:\n{kpis}\n\n"
     "Anomaly highlights:\n{anomaly_highlights}\n\n"
     "Weather risk:\n{weather_risk}\n\n"
     "Dispatch plan:\n{dispatch_plan}\n\n"
     "Generate HTML report using only these real values.")
])
