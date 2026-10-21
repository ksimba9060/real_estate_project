"""PDF tax-document indexing and retrieval for the advisor RAG."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from database import get_connection

PROJECT_DIR = Path(__file__).resolve().parent
PDF_DIR = PROJECT_DIR / "pdf"
DOCUMENT_ROOT = PROJECT_DIR.parent


def _chunks(text: str, size: int = 1400, overlap: int = 180):
    text = re.sub(r"\s+", " ", text).strip()
    for start in range(0, len(text), size - overlap):
        chunk = text[start:start + size].strip()
        if len(chunk) >= 40:
            yield chunk


def index_tax_pdfs() -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF RAG를 사용하려면 pypdf 설치가 필요합니다. pip install pypdf") from exc
    files = sorted(
        path for path in DOCUMENT_ROOT.rglob("*.pdf")
        if ".venv" not in path.parts and ".git" not in path.parts
    )
    if not files:
        raise RuntimeError("PDF 문서를 찾지 못했습니다.")
    saved = 0
    pages = 0
    with get_connection() as conn:
        conn.execute("DELETE FROM tax_document_chunks")
        for pdf_path in files:
            reader = PdfReader(str(pdf_path))
            document_name = str(pdf_path.relative_to(DOCUMENT_ROOT))
            for page_no, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages += 1
                for chunk_no, chunk in enumerate(_chunks(text)):
                    conn.execute("INSERT INTO tax_document_chunks(document_name,page_number,chunk_number,content,source_path) VALUES(?,?,?,?,?)", (document_name, page_no, chunk_no, chunk, str(pdf_path)))
                    saved += 1
        conn.commit()
    return {"files": len(files), "pages": pages, "chunks": saved}


def retrieve_tax_context(question: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = [x for x in re.findall(r"[가-힣A-Za-z0-9]{2,}", question) if x not in {"그리고", "어떻게", "얼마나"}][:8]
    if not terms:
        terms = ["세금"]
    score = " + ".join("CASE WHEN content LIKE ? THEN 1 ELSE 0 END" for _ in terms)
    params: list[Any] = []
    for term in terms:
        params.append(f"%{term}%")
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(f"SELECT document_name,page_number,content,source_path,{score} AS relevance FROM tax_document_chunks ORDER BY relevance DESC, page_number LIMIT ?", params).fetchall()
    return [dict(row) for row in rows]


def format_tax_context(items: list[dict[str, Any]]) -> str:
    if not items:
        return "저장된 세금 PDF 근거가 없습니다. AI가 세법을 추정하지 않도록 안내하세요."
    lines = ["세금 PDF RAG 근거:"]
    for item in items:
        lines.append(f"- {item['document_name']} p.{item['page_number']} | {item['content']}")
    return "\n".join(lines)
