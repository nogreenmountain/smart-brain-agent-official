"""Versioned structured document representation used by the v3 shadow path.

This module is intentionally side-effect free: it never writes v2 rows and can
be exercised in isolation before a future asynchronous indexer is enabled.
"""
from __future__ import annotations

import re
import uuid
import zipfile
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


@dataclass
class StructuredBlock:
    kind: str
    text: str
    order: int
    heading_path: tuple[str, ...] = ()
    page: int | None = None
    slide: int | None = None
    sheet: str | None = None
    cell_range: str | None = None
    locator: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class StructuredDocument:
    source_type: str
    blocks: list[StructuredBlock]
    warnings: list[str] = field(default_factory=list)


@dataclass
class ContextualChunk:
    id: uuid.UUID
    document_id: uuid.UUID
    project_id: uuid.UUID
    source_type: str
    source_locator: str | None
    page: int | None
    slide: int | None
    sheet: str | None
    cell_range: str | None
    heading_path: str | None
    parent_chunk_id: uuid.UUID | None
    previous_chunk_id: uuid.UUID | None
    next_chunk_id: uuid.UUID | None
    parser_version: str
    chunker_version: str
    retrieval_version: str
    original_text: str
    contextual_prefix: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.original_text.encode("utf-8")).hexdigest()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _texts(element: ET.Element) -> list[str]:
    return [node.text.strip() for node in element.iter() if _local(node.tag) == "t" and node.text and node.text.strip()]


def _docx(path: Path) -> StructuredDocument:
    blocks: list[StructuredBlock] = []
    heading_stack: list[tuple[int, str]] = []
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    order = 0
    body = next((node for node in root.iter() if _local(node.tag) == "body"), root)
    for child in body:
        kind = _local(child.tag)
        if kind == "p":
            text = "".join(_texts(child)).strip()
            if not text:
                continue
            style = next(
                (
                    next((value for key, value in node.attrib.items() if _local(key) == "val"), "")
                    for node in child.iter()
                    if _local(node.tag) == "pStyle"
                ),
                "",
            )
            match = re.search(r"heading(\d+)", style, re.I)
            if match:
                level = int(match.group(1))
                heading_stack = [(lvl, title) for lvl, title in heading_stack if lvl < level]
                heading_stack.append((level, text))
                block_kind = "heading"
            else:
                block_kind = "paragraph"
            blocks.append(StructuredBlock(block_kind, text, order, tuple(title for _, title in heading_stack)))
            order += 1
        elif kind == "tbl":
            rows = []
            for row in child:
                if _local(row.tag) != "tr":
                    continue
                cells = [" ".join(_texts(cell)).strip() for cell in row if _local(cell.tag) == "tc"]
                if cells:
                    rows.append("\t".join(cells))
            if rows:
                blocks.append(StructuredBlock("table", "\n".join(rows), order, tuple(title for _, title in heading_stack)))
                order += 1
    return StructuredDocument("docx", blocks)


def _pptx(path: Path) -> StructuredDocument:
    blocks: list[StructuredBlock] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted((name for name in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)), key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        order = 0
        for name in slide_names:
            slide_no = int(re.search(r"(\d+)", name).group(1))
            texts = _texts(ET.fromstring(archive.read(name)))
            for idx, text in enumerate(texts):
                blocks.append(StructuredBlock("slide_title" if idx == 0 else "paragraph", text, order, slide=slide_no, locator=f"slide:{slide_no}"))
                order += 1
        note_names = sorted(name for name in archive.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", name))
        for name in note_names:
            slide_no = int(re.search(r"(\d+)", name).group(1))
            text = "\n".join(_texts(ET.fromstring(archive.read(name))))
            if text:
                blocks.append(StructuredBlock("speaker_notes", text, order, slide=slide_no, locator=f"slide:{slide_no}:notes"))
                order += 1
    return StructuredDocument("pptx", blocks)


def _xlsx(path: Path) -> StructuredDocument:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels")) if "xl/_rels/workbook.xml.rels" in archive.namelist() else None
        targets = {rel.attrib.get("Id"): rel.attrib.get("Target", "") for rel in rels or []}
        sheets = [
            (
                next((value for key, value in sheet.attrib.items() if _local(key) == "id"), ""),
                sheet.attrib.get("name", "Sheet"),
            )
            for sheet in workbook.iter()
            if _local(sheet.tag) == "sheet"
        ]
        blocks: list[StructuredBlock] = []
        order = 0
        for rel_id, sheet_name in sheets:
            target = targets.get(rel_id, f"worksheets/sheet{order + 1}.xml").lstrip("/")
            target = target if target.startswith("xl/") else f"xl/{target}"
            if target not in archive.namelist():
                continue
            root = ET.fromstring(archive.read(target))
            for row in (node for node in root.iter() if _local(node.tag) == "row"):
                cells = []
                refs = []
                for cell in row:
                    if _local(cell.tag) != "c":
                        continue
                    ref = cell.attrib.get("r", "")
                    value = next((node.text for node in cell if _local(node.tag) == "v" and node.text is not None), None)
                    formula = next((node.text for node in cell if _local(node.tag) == "f" and node.text), None)
                    inline = "".join(_texts(cell))
                    cells.append(inline or value or formula or "")
                    refs.append(ref)
                if cells:
                    locator = f"sheet:{sheet_name}:{refs[0]}:{refs[-1]}" if refs else f"sheet:{sheet_name}"
                    blocks.append(StructuredBlock("spreadsheet_row", "\t".join(cells), order, sheet=sheet_name, cell_range=f"{refs[0]}:{refs[-1]}", locator=locator, metadata={"formula": formula or ""}))
                    order += 1
    return StructuredDocument("xlsx", blocks)


def _pdf(path: Path) -> StructuredDocument:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    blocks: list[StructuredBlock] = []
    warnings: list[str] = []
    for page_no, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            warnings.append(f"page {page_no}: {type(exc).__name__}")
            continue
        if text:
            blocks.append(StructuredBlock("page_text", text, len(blocks), page=page_no, locator=f"page:{page_no}"))
    return StructuredDocument("pdf", blocks, warnings)


def parse_structured(path: str | Path, source_type: str | None = None) -> StructuredDocument:
    file_path = Path(path)
    fmt = (source_type or file_path.suffix.lstrip(".")).lower()
    if fmt == "docx":
        return _docx(file_path)
    if fmt == "pptx":
        return _pptx(file_path)
    if fmt == "xlsx":
        return _xlsx(file_path)
    if fmt == "pdf":
        return _pdf(file_path)
    raise ValueError(f"structured parser does not support {fmt}")


def _locator(block: StructuredBlock) -> str | None:
    if block.locator:
        return block.locator
    if block.page is not None:
        return f"page:{block.page}"
    if block.slide is not None:
        return f"slide:{block.slide}"
    if block.sheet and block.cell_range:
        return f"sheet:{block.sheet}:{block.cell_range}"
    return None


def build_contextual_chunks(
    blocks: Iterable[StructuredBlock],
    *,
    document_id: uuid.UUID,
    project_id: uuid.UUID,
    source_type: str,
    parser_version: str,
    chunker_version: str,
    retrieval_version: str,
    document_context: str = "",
) -> list[ContextualChunk]:
    selected = [block for block in blocks if block.text.strip()]
    chunks: list[ContextualChunk] = []
    active_parent_id: uuid.UUID | None = None
    for block in selected:
        heading = " > ".join(block.heading_path) if block.heading_path else ""
        prefix_parts = [part for part in (document_context.strip(), heading) if part]
        chunk = ContextualChunk(
            id=uuid.uuid4(), document_id=document_id, project_id=project_id, source_type=source_type,
            source_locator=_locator(block), page=block.page, slide=block.slide, sheet=block.sheet,
            cell_range=block.cell_range, heading_path=heading or None,
            parent_chunk_id=None if block.kind == "heading" else active_parent_id,
            previous_chunk_id=chunks[-1].id if chunks else None, next_chunk_id=None,
            parser_version=parser_version, chunker_version=chunker_version, retrieval_version=retrieval_version,
            original_text=block.text, contextual_prefix="\n".join(prefix_parts),
        )
        if chunks:
            chunks[-1].next_chunk_id = chunk.id
        chunks.append(chunk)
        if block.kind == "heading":
            active_parent_id = chunk.id
    return chunks
