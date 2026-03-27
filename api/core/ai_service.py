import json
from google import genai
from google.genai import types


PROMPTS = {
    "study": "Act as an academic tutor. Identify: 1. Key definitions 2. Core concepts 3. Essential formulas/dates 4. Main conclusions.",
    "code": "Act as a Senior Developer. Identify: 1. Function definitions 2. Core logic blocks 3. Configuration variables 4. Bug-prone areas.",
    "cyber": "Act as a Cybersecurity Researcher. Identify: 1. Vulnerability descriptions 2. CVSS scores/severity 3. Proof of Concept steps 4. Remediation advice.",
    "medical": "Act as a Medical Professional. Identify: 1. Patient symptoms 2. Diagnostic results 3. Prescribed medications 4. Follow-up instructions.",
}

_BASE_INSTRUCTION = """
Extract these as EXACT verbatim sentences from the text in their ORIGINAL language.
Return ONLY a JSON list of strings. No markdown.
Format: ["sentence 1", "sentence 2"]
"""


def get_prompt(mode: str) -> str:
    """Return the full extraction prompt for the given mode."""
    role_prompt = PROMPTS.get(mode, PROMPTS["study"])
    return role_prompt + _BASE_INSTRUCTION


def extract_sentences(api_key: str, pdf_path: str, mode: str) -> list[str]:
    """
    Upload the PDF to Gemini and return the list of key sentences
    identified according to the chosen mode.
    """
    client = genai.Client(api_key=api_key)

    pdf_file = client.files.upload(file=pdf_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[pdf_file, get_prompt(mode)],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    sentences: list[str] = json.loads(
        response.text.encode("utf-8").decode("utf-8")
    )
    return sentences
