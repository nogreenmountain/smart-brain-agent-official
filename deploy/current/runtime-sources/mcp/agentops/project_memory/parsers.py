from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


TEXT_CODE_FORMATS = {
    "bat",
    "c",
    "conf",
    "cpp",
    "cs",
    "css",
    "csv",
    "go",
    "h",
    "hpp",
    "java",
    "js",
    "json",
    "jsx",
    "log",
    "ps1",
    "py",
    "rs",
    "scss",
    "sh",
    "sql",
    "ts",
    "tsx",
    "vue",
    "xml",
    "yaml",
    "yml",
}
COMMON_DOCUMENT_FORMATS = {
    "txt", "doc", "docx", "pdf", "rtf", "md", "markdown",
    "xls", "xlsx", "csv", "ppt", "pptx",
}
IMAGE_FORMATS = {"jpg", "jpeg", "png", "gif", "svg", "webp"}
AUDIO_FORMATS = {"mp3", "wav", "aac", "flac", "m4a"}
VIDEO_FORMATS = {"mp4", "avi", "mkv", "mov", "wmv"}
ARCHIVE_FORMATS = {"zip", "rar", "7z", "tar", "gz"}
DATABASE_FORMATS = {"db", "sqlite", "sql"}
SYSTEM_FORMATS = {"exe", "msi", "dll", "iso"}
EBOOK_FORMATS = {"epub", "mobi", "azw"}
SUPPORTED_FORMATS = {
    *COMMON_DOCUMENT_FORMATS,
    "html", "htm",
    *IMAGE_FORMATS,
    *AUDIO_FORMATS,
    *VIDEO_FORMATS,
    *ARCHIVE_FORMATS,
    *DATABASE_FORMATS,
    *SYSTEM_FORMATS,
    *EBOOK_FORMATS,
    *TEXT_CODE_FORMATS,
}
METADATA_ONLY_FORMATS = (
    IMAGE_FORMATS - {"png", "jpg", "jpeg"}
    | AUDIO_FORMATS | VIDEO_FORMATS | (ARCHIVE_FORMATS - {"zip"}) | SYSTEM_FORMATS
    | EBOOK_FORMATS | {"doc", "xls", "ppt", "rtf"}
)
_ARCHIVE_TEXT_FORMATS = {
    "txt", "md", "markdown", "csv", "json", "yaml", "yml", "xml", "html", "htm",
    "py", "ts", "tsx", "js", "jsx", "css", "sql", "log", "conf", "ini", "sh", "bat",
}
_EXECUTABLE_FORMATS = {"exe", "dll", "msi", "iso"}


def _validate_archive_member(name: str) -> None:
    cleaned = str(name).replace("\\", "/")
    path = PurePosixPath(cleaned)
    if (
        not cleaned or "\x00" in cleaned or cleaned.startswith("/")
        or cleaned.startswith("//") or re.match(r"^[A-Za-z]:", cleaned)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"unsafe archive member: {name}")


@dataclass(frozen=True)
class ExtractedText:
    filename: str
    format: str
    text: str


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if value:
            self.parts.append(value)


def _normalize_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    compact: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank:
                compact.append("")
            previous_blank = True
            continue
        compact.append(line)
        previous_blank = False
    return "\n".join(compact).strip()


def _extract_html(path: Path) -> str:
    parser = _TextHTMLParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return _normalize_text("\n".join(parser.parts))


def _extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    texts = [
        node.text or ""
        for node in root.iter()
        if node.tag.endswith("}t") and node.text
    ]
    return _normalize_text("\n".join(texts))


def _extract_pptx(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            slide_text = [
                node.text or ""
                for node in root.iter()
                if node.tag.endswith("}t") and node.text
            ]
            if slide_text:
                texts.append("\n".join(slide_text))
    return _normalize_text("\n\n".join(texts))


def _extract_xlsx(path: Path) -> str:
    shared_strings: list[str] = []
    sheets: list[str] = []
    with zipfile.ZipFile(path) as archive:
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.iter():
                if not item.tag.endswith("}si"):
                    continue
                shared_strings.append(
                    "".join(
                        node.text or ""
                        for node in item.iter()
                        if node.tag.endswith("}t")
                    )
                )

        sheet_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        for name in sheet_names:
            root = ElementTree.fromstring(archive.read(name))
            rows: list[str] = []
            for row in root.iter():
                if not row.tag.endswith("}row"):
                    continue
                values: list[str] = []
                for cell in row:
                    if not cell.tag.endswith("}c"):
                        continue
                    cell_type = cell.attrib.get("t", "")
                    value_node = next(
                        (node for node in cell if node.tag.endswith("}v")),
                        None,
                    )
                    value = ""
                    if cell_type == "s" and value_node is not None and value_node.text:
                        try:
                            value = shared_strings[int(value_node.text)]
                        except (IndexError, ValueError):
                            value = value_node.text
                    elif cell_type == "inlineStr":
                        value = "".join(
                            node.text or ""
                            for node in cell.iter()
                            if node.tag.endswith("}t")
                        )
                    elif cell_type == "b" and value_node is not None:
                        value = "TRUE" if value_node.text == "1" else "FALSE"
                    elif value_node is not None and value_node.text:
                        value = value_node.text
                    else:
                        formula_node = next(
                            (node for node in cell if node.tag.endswith("}f")),
                            None,
                        )
                        if formula_node is not None and formula_node.text:
                            value = formula_node.text
                    if value:
                        values.append(value)
                if values:
                    rows.append("\t".join(values))
            if rows:
                sheets.append("\n".join(rows))
    return _normalize_text("\n\n".join(sheets))


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return _normalize_text("\n\n".join(pages))


def _extract_zip(path: Path) -> str:
    """Extract only bounded UTF-8 text members from a ZIP in memory.

    Archive members are never materialized on disk or executed.  Rejecting
    unsafe names before reading protects callers that later persist the
    returned text under a project storage root.
    """
    texts: list[str] = []
    extracted_bytes = 0
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 5000:
            raise ValueError("archive has too many members")
        for info in infos:
            _validate_archive_member(info.filename)
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower().lstrip(".")
            if suffix in _EXECUTABLE_FORMATS or suffix not in _ARCHIVE_TEXT_FORMATS:
                continue
            if info.file_size > 8 * 1024 * 1024 or extracted_bytes + info.file_size > 64 * 1024 * 1024:
                continue
            payload = archive.read(info)
            extracted_bytes += len(payload)
            texts.append(payload.decode("utf-8", errors="replace"))
    return _normalize_text("\n\n".join(texts))


def _extract_image(path: Path, fmt: str) -> str:
    """Return searchable, deterministic metadata for images.

    OCR is intentionally optional: production images do not currently ship an
    OCR runtime. Keeping the image as a first-class document while indexing its
    filename/format lets uploads and approvals succeed and leaves room for a
    later OCR worker without rejecting user data.
    """
    payload = path.read_bytes()
    if fmt == "png" and not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG image")
    if fmt in {"jpg", "jpeg"} and not payload.startswith(b"\xff\xd8"):
        raise ValueError("invalid JPEG image")
    return _normalize_text(
        f"图片文件：{path.name}\n格式：{fmt}\n图片内容待 OCR 处理。"
    )


def _extract_metadata_only(path: Path, fmt: str) -> str:
    """Keep binary uploads searchable without parsing or executing them."""
    size = path.stat().st_size
    return _normalize_text(
        f"文件：{path.name}\n格式：{fmt}\n大小：{size} 字节\n该格式已接收，内容待专用解析器处理。"
    )


def extract_text(path: Path) -> ExtractedText:
    suffix = path.suffix.lower().lstrip(".")
    fmt = "html" if suffix == "htm" else suffix
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"unsupported project memory format: {suffix}")
    if fmt == "pdf":
        text = _extract_pdf(path)
    elif fmt in {"png", "jpg", "jpeg"}:
        text = _extract_image(path, fmt)
    elif fmt in METADATA_ONLY_FORMATS:
        text = _extract_metadata_only(path, fmt)
    elif fmt == "html":
        text = _extract_html(path)
    elif fmt == "docx":
        text = _extract_docx(path)
    elif fmt == "pptx":
        text = _extract_pptx(path)
    elif fmt == "xlsx":
        text = _extract_xlsx(path)
    elif fmt == "zip":
        text = _extract_zip(path)
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = _normalize_text(text)
    if not text:
        raise ValueError(f"no extractable text: {path.name}")
    return ExtractedText(filename=path.name, format=fmt, text=text)
