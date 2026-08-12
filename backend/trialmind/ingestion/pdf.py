from pypdf import PdfReader


def parse_pdf(path: str) -> str:
    reader = PdfReader(path)
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n\n".join(p.strip() for p in parts if p.strip())
