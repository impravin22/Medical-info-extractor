from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.app.settings import get_settings
from src.domain.layout import parse_layout_dsl
from src.ingest.extractors import build_report
from src.ingest.pdf_reader import extract_text_by_page
from src.llm.reason_summarizer import init_llm_gemini
from src.llm.nebius_llm import init_llm_nebius
from src.render.docx_writer import render_report_to_docx
from src.render.markdown_writer import render_report_to_markdown
from src.utils.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Medical Summary Builder")
    parser.add_argument("--pdf", required=True, help="Path to input Medical File.pdf")
    parser.add_argument(
        "--template",
        required=False,
        help="Path to Medical Summary.docx (optional; a new doc is created if omitted)",
    )
    parser.add_argument("--out", required=True, help="Output .docx path")
    parser.add_argument(
        "--md-out", required=False, help="Optional Markdown output path"
    )
    parser.add_argument("--layout", required=False, help="Layout DSL string")
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pages = extract_text_by_page(pdf_path)

    # Initialize LLM based on backend
    if settings.llm_backend == "nebius":
        if not settings.nebius_api_key:
            raise SystemExit(
                "No Nebius API key provided. Set MSB_NEBIUS_API_KEY or NEBIUS_API_KEY."
            )
        model = init_llm_nebius(
            settings.nebius_api_key,
            settings.nebius_model,
            settings.nebius_base_url
        )
        logging.info(f"Using Nebius backend with model: {settings.nebius_model}")
        report = build_report(pages, model, backend="nebius", model_name=settings.nebius_model)
    else:
        # Fallback to Gemini
        if not settings.gemini_api_key:
            raise SystemExit(
                "No API key provided. Set MSB_GEMINI_API_KEY or GOOGLE_API_KEY."
            )
        model = init_llm_gemini(settings.gemini_api_key, settings.gemini_model)
        logging.info(f"Using Gemini backend with model: {settings.gemini_model}")
        report = build_report(pages, model, backend="gemini")

    # Set reason_summary to reason_raw
    for evt in report.events:
        evt.reason_summary = evt.reason_raw

    layout = parse_layout_dsl(args.layout)
    render_report_to_docx(
        report,
        args.out,
        layout,
        template_path=args.template,
    )
    if args.md_out:
        render_report_to_markdown(report, args.md_out, layout)
    logging.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
