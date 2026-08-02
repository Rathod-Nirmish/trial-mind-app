import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str, target_chars: int) -> list[str]:
    sentences = _SENTENCE_END.split(text)
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if not buf:
            buf = s
        elif len(buf) + 1 + len(s) <= target_chars:
            buf = f"{buf} {s}"
        else:
            chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    return chunks


def chunk_text(text: str, *, target_chars: int = 1200, overlap: int = 150) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    raw_chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(p) > target_chars:
            if buf:
                raw_chunks.append(buf)
                buf = ""
            raw_chunks.extend(_split_sentences(p, target_chars))
            continue
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= target_chars:
            buf = f"{buf}\n\n{p}"
        else:
            raw_chunks.append(buf)
            buf = p
    if buf:
        raw_chunks.append(buf)

    if overlap <= 0 or len(raw_chunks) <= 1:
        return raw_chunks
    with_overlap: list[str] = [raw_chunks[0]]
    for i in range(1, len(raw_chunks)):
        prev_tail = raw_chunks[i - 1][-overlap:]
        with_overlap.append(prev_tail + raw_chunks[i])
    return with_overlap
