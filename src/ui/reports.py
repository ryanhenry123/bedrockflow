from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.reports.catalog import CATALOG
from src.reports.paths import REPORTS_DIR, ensure_reports_dir, report_path


def resolve_pdf_file(slug: str) -> Path:
    if slug.startswith("catalog-"):
        candidate = report_path(slug)
        if candidate.exists():
            return candidate

    ensure_reports_dir()
    direct = REPORTS_DIR / f"{slug}.pdf"
    if direct.exists():
        return direct

    matches = sorted(REPORTS_DIR.glob(f"{slug}*.pdf"))
    if matches:
        return matches[-1]

    raise HTTPException(status_code=404, detail=f"Report not found: {slug}")


def catalog_entries() -> list[dict[str, str]]:
    ensure_reports_dir()
    entries: list[dict[str, str]] = []
    for dataset in CATALOG:
        slug = f"catalog-{dataset.slug}"
        path = report_path(slug)
        entries.append(
            {
                "slug": slug,
                "title": dataset.title,
                "subtitle": dataset.subtitle,
                "download_url": f"/reports/{slug}.pdf",
                "ready": str(path.exists()).lower(),
            }
        )
    return entries


def pdf_file_response(path: Path) -> FileResponse:
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )
