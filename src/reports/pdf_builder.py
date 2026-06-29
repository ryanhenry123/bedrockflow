from __future__ import annotations

import io
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.reports.catalog import ReportDataset, resolve_dataset
from src.reports.paths import ensure_reports_dir

NAVY = colors.HexColor("#0b1f33")
ACCENT = colors.HexColor("#42b4ff")
ORANGE = colors.HexColor("#ff9900")
MUTED = colors.HexColor("#5a6a7a")
PANEL = colors.HexColor("#f4f7fb")
WHITE = colors.white


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug[:80] or "report"


def _parse_narrative_sections(narrative: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "Executive Summary"
    buffer: list[str] = []
    for line in narrative.splitlines():
        if line.startswith("# Research Report:"):
            continue
        if line.startswith("---"):
            continue
        if line.startswith("_generated"):
            continue
        if line.startswith("## "):
            if buffer:
                sections[current] = "\n".join(buffer).strip()
            current = line.removeprefix("## ").strip()
            buffer = []
            continue
        buffer.append(line)
    if buffer:
        sections[current] = "\n".join(buffer).strip()
    if not sections and narrative.strip():
        sections["Executive Summary"] = narrative.strip()
    return sections


def _chart_image(series: Any, *, width: float = 6.5, height: float = 2.6) -> Image:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(width, height), dpi=120)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    if series.chart_type == "bar":
        ax.bar(series.x, series.y, color="#42b4ff", edgecolor="#0b1f33", linewidth=0.6)
    else:
        ax.plot(
            series.x, series.y, color="#ff9900", linewidth=2.4, marker="o", markersize=5
        )
        ax.fill_between(range(len(series.y)), series.y, alpha=0.12, color="#42b4ff")

    ax.set_title(series.label, fontsize=11, fontweight="bold", color="#0b1f33", pad=10)
    ax.set_ylabel(series.ylabel, fontsize=9, color="#334155")
    ax.tick_params(axis="x", rotation=25, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.35)
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")

    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return Image(buffer, width=width * inch, height=height * inch)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontSize=26,
            leading=30,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=base["Normal"],
            fontSize=13,
            leading=18,
            textColor=ACCENT,
            spaceAfter=8,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#cbd5e1"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=8,
        ),
        "muted": ParagraphStyle(
            "Muted",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
            textColor=MUTED,
            spaceAfter=6,
        ),
        "kpi_value": ParagraphStyle(
            "KpiValue",
            parent=base["Normal"],
            fontSize=18,
            leading=22,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "kpi_label": ParagraphStyle(
            "KpiLabel",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


def _header_footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    width, height = letter
    if canvas.getPageNumber() == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 1.35 * inch, width, 1.35 * inch, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(0.75 * inch, height - 0.55 * inch, "ORCHFLOW RESEARCH")
    else:
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.line(
            0.75 * inch, height - 0.55 * inch, width - 0.75 * inch, height - 0.55 * inch
        )
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.75 * inch, height - 0.42 * inch, "Orchflow Research")
        canvas.drawRightString(
            width - 0.75 * inch,
            height - 0.42 * inch,
            f"Page {canvas.getPageNumber()}",
        )
    canvas.restoreState()


def build_research_pdf(
    *,
    topic: str,
    narrative: str,
    output_path: Path | None = None,
    run_id: str | None = None,
) -> Path:
    dataset = resolve_dataset(topic)
    slug = _slugify(run_id or dataset.slug)
    target = output_path or (ensure_reports_dir() / f"{slug}.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)

    styles = _styles()
    story: list[Any] = []
    generated = datetime.now(UTC).strftime("%B %d, %Y %H:%M UTC")

    story.append(Spacer(1, 1.55 * inch))
    story.append(Paragraph(dataset.title, styles["cover_title"]))
    story.append(Paragraph(dataset.subtitle, styles["cover_sub"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(f"Topic: {topic}", styles["cover_meta"]))
    story.append(Paragraph(f"Generated: {generated}", styles["cover_meta"]))
    if run_id:
        story.append(Paragraph(f"Run ID: {run_id[:8]}", styles["cover_meta"]))
    story.append(PageBreak())

    story.append(Paragraph("Key metrics", styles["h1"]))
    kpi_cells = []
    for label, value in dataset.kpis:
        kpi_cells.append(
            [
                Paragraph(value, styles["kpi_value"]),
                Paragraph(label, styles["kpi_label"]),
            ]
        )
    kpi_table = Table(kpi_cells, colWidths=[1.6 * inch] * len(dataset.kpis))
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbeafe")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.2 * inch))

    sections = _parse_narrative_sections(narrative)
    story.append(Paragraph("Narrative synthesis", styles["h1"]))
    for heading, body in sections.items():
        story.append(Paragraph(heading, styles["h2"]))
        story.append(Paragraph(body.replace("\n", "<br/>"), styles["body"]))

    story.append(PageBreak())
    story.append(Paragraph("Statistical analysis", styles["h1"]))
    story.append(Paragraph(dataset.methodology, styles["muted"]))
    story.append(Spacer(1, 0.12 * inch))
    for series in dataset.series:
        story.append(_chart_image(series))
        story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph(dataset.table_title, styles["h2"]))
    table_data = [list(dataset.table_headers), *map(list, dataset.table_rows)]
    stats_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[1.4 * inch, 1.2 * inch, 1.2 * inch, 2.8 * inch],
    )
    stats_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PANEL]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(stats_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Worked examples", styles["h2"]))
    for example in dataset.examples:
        story.append(Paragraph(f"• {example}", styles["body"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "<b>Disclaimer:</b> Illustrative quantitative research for workflow demonstration. "
            "Statistics are synthetic but methodology-aligned; not investment advice.",
            styles["muted"],
        )
    )

    doc = SimpleDocTemplate(
        str(target),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.65 * inch,
        title=dataset.title,
        author="Orchflow Research",
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return target
