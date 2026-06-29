from __future__ import annotations

from pathlib import Path

import pytest

from src.reports.catalog import CATALOG
from src.reports.pdf_builder import build_research_pdf
from src.ui.reports import catalog_entries, resolve_pdf_file


@pytest.fixture
def tmp_reports(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("src.reports.paths.REPORTS_DIR", tmp_path)
    monkeypatch.setattr("src.ui.reports.REPORTS_DIR", tmp_path)
    return tmp_path


def test_build_research_pdf_writes_file(tmp_reports: Path):
    dataset = CATALOG[0]
    out = build_research_pdf(
        topic=dataset.title,
        narrative=(
            f"# Research Report: {dataset.title}\n\n"
            "## Overview\nSynthetic vol selling crowding analysis.\n"
            "## References\n- Orchflow test fixture\n"
        ),
        output_path=tmp_reports / "unit-test.pdf",
        run_id="unit-test-run",
    )
    assert out.exists()
    assert out.stat().st_size > 5000
    assert out.read_bytes()[:4] == b"%PDF"


def test_resolve_pdf_file_by_slug(tmp_reports: Path):
    slug = "catalog-vol-selling"
    path = tmp_reports / f"{slug}.pdf"
    path.write_bytes(b"%PDF-1.4 test")
    assert resolve_pdf_file(slug) == path


def test_catalog_entries_reflect_files(tmp_reports: Path):
    for dataset in CATALOG:
        (tmp_reports / f"catalog-{dataset.slug}.pdf").write_bytes(b"%PDF")
    entries = catalog_entries()
    assert len(entries) == len(CATALOG)
    assert all(item["ready"] == "true" for item in entries)
    assert all(item["download_url"].endswith(".pdf") for item in entries)
