"""Generate catalog PDF research reports."""

from __future__ import annotations

from src.reports.catalog import CATALOG
from src.reports.pdf_builder import build_research_pdf
from src.reports.paths import report_path


def main() -> None:
    for dataset in CATALOG:
        narrative = (
            f"# Research Report: {dataset.title}\n\n"
            f"## Overview\nAutomated catalog report for {dataset.subtitle}.\n"
            f"## Recent Evidence\nSee statistical exhibits and tables in this document.\n"
            f"## Implications\nRisk teams should monitor regime shifts and crowding.\n"
            f"## References\n- Orchflow Research Catalog ({dataset.slug})\n"
        )
        out = build_research_pdf(
            topic=dataset.title,
            narrative=narrative,
            output_path=report_path(f"catalog-{dataset.slug}"),
        )
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
