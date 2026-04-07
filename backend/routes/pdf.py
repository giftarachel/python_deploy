"""
POST /api/pdf  - Generate a PDF report for a simulation result using ReportLab.
"""

from flask import Blueprint, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
from reportlab.lib.units import cm
import io
from datetime import datetime

pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.route("/pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json()

    links = data.get("links", [])
    external_force = data.get("external_force", 0)
    force_type = data.get("force_type", "bump")
    results = data.get("results", [])
    max_stress_link = data.get("max_stress_link", 0)
    method = data.get("method", "N/A")
    residual = data.get("residual", 0)
    timestamp = data.get("timestamp", datetime.utcnow().isoformat())
    dcm = data.get("direction_cosine_matrix", [])
    fv = data.get("external_force_vector", [])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 fontSize=16, textColor=colors.HexColor("#0f172a"),
                                 spaceAfter=6)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                               fontSize=10, textColor=colors.HexColor("#475569"),
                               spaceAfter=4)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"],
                                   fontSize=12, textColor=colors.HexColor("#1e40af"),
                                   spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body", parent=styles["Normal"],
                                fontSize=9, textColor=colors.HexColor("#1e293b"))

    story = []

    # Title
    story.append(Paragraph("Matrix-Based Force Distribution", title_style))
    story.append(Paragraph("Multi-Link Suspension System — Simulation Report", sub_style))
    story.append(Paragraph(f"Generated: {timestamp}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 0.3*cm))

    # Simulation Parameters
    story.append(Paragraph("Simulation Parameters", heading_style))
    params = [
        ["Parameter", "Value"],
        ["Number of Links", str(len(links))],
        ["External Force", f"{external_force} N"],
        ["Force Type", force_type.capitalize()],
        ["Solver Method", method.replace("_", " ").title()],
        ["Equilibrium Residual", f"{residual:.6f}"],
    ]
    t = Table(params, colWidths=[7*cm, 9*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # External Force Vector
    story.append(Paragraph("External Force Vector [Fx, Fy]", heading_style))
    fv_str = f"Fx = {fv[0]:.2f} N,  Fy = {fv[1]:.2f} N" if len(fv) >= 2 else "N/A"
    story.append(Paragraph(fv_str, body_style))
    story.append(Spacer(1, 0.3*cm))

    # Direction Cosine Matrix
    if dcm:
        story.append(Paragraph("Direction Cosine Matrix (A)", heading_style))
        story.append(Paragraph("Rows: [cos θ] and [sin θ] for each link column", body_style))
        story.append(Spacer(1, 0.2*cm))
        dcm_header = [""] + [f"Link {i+1}" for i in range(len(links))]
        dcm_rows = [dcm_header]
        row_labels = ["cos θ (Fx)", "sin θ (Fy)"]
        for ri, row in enumerate(dcm):
            dcm_rows.append([row_labels[ri]] + [f"{v:.4f}" for v in row])
        dt = Table(dcm_rows)
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(dt)
        story.append(Spacer(1, 0.4*cm))

    # Link Configuration & Results
    story.append(Paragraph("Link Configuration & Force Distribution (T = A⁻¹·F)", heading_style))
    link_header = ["Link #", "Angle (°)", "Length (mm)", "Force T (N)", "Status"]
    link_rows = [link_header]
    for i, (lnk, force) in enumerate(zip(links, results)):
        status = "⚠ MAX STRESS" if i == max_stress_link else "OK"
        link_rows.append([
            str(i + 1),
            f"{lnk['angle']}°",
            f"{lnk['length']} mm",
            f"{force:.4f} N",
            status,
        ])
    lt = Table(link_rows, colWidths=[2*cm, 3*cm, 3.5*cm, 4*cm, 4*cm])
    lt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (4, 1), (4, -1), colors.HexColor("#dc2626")),
    ]))
    story.append(lt)
    story.append(Spacer(1, 0.5*cm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Engineering Keywords: Direction Cosine Matrix · Static Equilibrium · "
        "Linear System Solver · Matrix Inversion · Force Propagation · Suspension Topology",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.HexColor("#94a3b8"), alignment=1)
    ))

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="suspension_simulation_report.pdf"
    )
