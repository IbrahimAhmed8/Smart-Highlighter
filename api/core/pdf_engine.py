"""
pdf_engine.py

Architecture: we extract text from the PDF ourselves, send that text to
Gemini, and Gemini returns sentences copied from that same text.
Since both sides use identical text, search_for() always finds them.

highlight_sentences() receives sentences that came from our own extraction,
so they match the text layer exactly — no font encoding mismatch possible.
"""

import fitz  # PyMuPDF


def extract_pages(pdf_path: str) -> list[dict]:
    """
    Extract text from each page, returning a list of:
        {"page_num": int, "text": str, "words": [...]}
    where words are (x0, y0, x1, y1, word) tuples.
    """
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        words = [(w[0], w[1], w[2], w[3], w[4]) for w in page.get_text("words")]
        pages.append({"page_num": i, "text": text, "words": words})
    doc.close()
    return pages


def extract_full_text(pdf_path: str) -> str:
    """
    Return the complete text of the PDF exactly as PyMuPDF extracts it.
    This is what gets sent to Gemini — Gemini must copy from THIS text.
    """
    doc = fitz.open(pdf_path)
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    return "\n\n".join(parts)


def highlight_sentences(
    input_path: str,
    output_path: str,
    sentences: list[str],
) -> list[dict]:
    """
    Highlight sentences in the PDF.

    Since sentences came from our own extract_full_text() call, they
    match the text layer exactly. We use page.search_for() directly.
    For safety, we also try a word-span walk as fallback.
    """
    doc = fitz.open(input_path)
    match_results: list[dict] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        found = False

        for page in doc:
            # Primary: direct search (works since text came from same extraction)
            try:
                rects = page.search_for(sentence, flags=fitz.TEXT_DEHYPHENATE)
            except Exception:
                rects = page.search_for(sentence)

            if not rects:
                # Fallback: word-span walk for sentences split across lines
                rects = _word_span_search(page, sentence)

            for rect in rects:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=(1, 1, 0))
                annot.update()
                found = True

        match_results.append({"sentence": sentence, "highlighted": found})

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return match_results


def _word_span_search(page: fitz.Page, sentence: str, min_words: int = 3) -> list[fitz.Rect]:
    """
    Word-level bbox search. Slides a window of sentence words over page words,
    unions matching bboxes. Handles line-wrap splits.
    """
    needle_words = sentence.lower().split()
    n = len(needle_words)
    if n < min_words:
        min_words = max(1, n)

    word_data = page.get_text("words")
    if not word_data:
        return []

    page_words = [(w[4].lower(), fitz.Rect(w[:4])) for w in word_data]
    page_texts = [pw[0] for pw in page_words]
    pw_n = len(page_texts)

    rects = []
    seen: set = set()

    for window in range(n, min_words - 1, -1):
        for i in range(pw_n - window + 1):
            if page_texts[i:i+window] == needle_words[:window]:
                if i not in seen:
                    seen.add(i)
                    union = page_words[i][1]
                    for j in range(i + 1, i + window):
                        union = union | page_words[j][1]
                    rects.append(union)
        if rects:
            break

    return rects
