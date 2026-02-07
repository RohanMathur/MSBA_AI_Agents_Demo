from __future__ import annotations
from graph import build_graph

if __name__ == "__main__":
    app = build_graph()

    state = {
        "pdf_path": "data/SeeWeeS Specialty distribution.pdf",
        "csv_path": "data/Incoming_shipment_02_08.csv",
    }

    final = app.invoke(state)

    report_html = final.get("report_html", "")
    print("\n=== REPORT (first 2000 chars) ===\n")
    print(report_html[:2000])
