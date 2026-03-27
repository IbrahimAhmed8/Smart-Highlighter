import fitz  # PyMuPDF


def highlight_sentences(input_path: str, output_path: str, sentences: list[str]) -> None:
    """
    Open the PDF at *input_path*, highlight every occurrence of each sentence,
    and save the result to *output_path*.

    Highlights are rendered in yellow (RGB 1, 1, 0).
    """
    doc = fitz.open(input_path)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        for page in doc:
            for rect in page.search_for(sentence):
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=(1, 1, 0))
                annot.update()

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
