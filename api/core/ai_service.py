"""
ai_service.py

Key design: we extract the PDF text ourselves with PyMuPDF, then send
ONLY that extracted text to Gemini. Gemini copies sentences verbatim
from our text. Since both sides use the same source, search_for() finds
every sentence — no font encoding, ligature, or small-caps mismatch.

We do NOT send the PDF file to Gemini at all. This also means:
- No Files API quota usage
- No hallucination from Gemini ignoring the file
- Works on any PDF regardless of font encoding quirks
"""

import json
from .pdf_engine import extract_full_text
from google import genai
from google.genai import types

PROMPTS = {
    "study": """You are an expert academic tutor preparing a student for an exam.
From the provided document text, extract only the most high-value sentences a student must memorize or understand. Focus on:
1. Precise definitions of key terms or concepts
2. Statements that explain cause-effect relationships or mechanisms
3. Specific facts: dates, statistics, formulas, laws, or named theories
4. Concluding or thesis statements that capture the author's main argument
Ignore transitional phrases, examples, filler sentences, and redundant restatements.""",

    "code": """You are a Senior Software Engineer conducting a code review and knowledge transfer.
From the provided document text, extract only the sentences that carry actionable technical meaning. Focus on:
1. Function, class, or module definitions and their stated purpose
2. Descriptions of core algorithmic logic or data flow
3. Configuration values, environment variables, or hard-coded constants with their intent
4. Explicit warnings, known limitations, or areas flagged as bug-prone
5. API contracts, expected inputs/outputs, and error-handling behavior
Ignore boilerplate comments, auto-generated text, and obvious or redundant descriptions.""",

    "cyber": """You are a senior Cybersecurity Researcher writing a threat intelligence brief.
From the provided document text, extract only the sentences that carry security-relevant technical detail. Focus on:
1. Precise vulnerability or weakness descriptions (e.g., CVE IDs, CWE types, affected components)
2. Severity ratings, CVSS scores, and their justification
3. Attack vectors, exploitation prerequisites, and step-by-step Proof of Concept actions
4. Indicators of Compromise (IoCs): hashes, IPs, domains, registry keys, file paths
5. Specific remediation steps, patches, mitigations, or workarounds
Ignore marketing language, general security advice not tied to the specific issue, and repetitive disclaimers.""",

    "medical": """You are a licensed medical professional reviewing clinical documentation.
From the provided document text, extract only the sentences that carry direct clinical significance. Focus on:
1. Specific patient-reported symptoms and their onset, duration, or severity
2. Objective diagnostic findings: lab values, imaging results, vital signs with their reference context
3. Diagnoses, differential diagnoses, and the clinical reasoning behind them
4. Prescribed medications with dosage, route, frequency, and duration
5. Follow-up instructions, red-flag warnings given to the patient, and referral details
Ignore administrative filler, standard consent boilerplate, and non-clinical background text.""",
}

_BASE_INSTRUCTION = """

DOCUMENT TEXT:
<text>
{pdf_text}
</text>

YOUR TASK:
Identify the most important sentences from the document text above and return them verbatim.

STRICT RULES:
- Copy each sentence CHARACTER FOR CHARACTER from the <text> block above — including any spacing quirks, abbreviations, or formatting exactly as they appear.
- Do NOT paraphrase, reword, merge, or summarize.
- Do NOT copy from memory or the visual PDF — only from the <text> block.
- Do NOT fix or alter any text — copy it as-is, even if it looks unusual.
- Do NOT translate.
- Each extracted sentence must be findable word-for-word in the <text> block.
- Do not repeat the same sentence twice.

OUTPUT FORMAT:
Return ONLY a valid JSON array. No markdown, no commentary.
Example: ["First sentence.", "Second sentence."]
"""


def get_prompt(mode: str, pdf_text: str) -> str:
    role = PROMPTS.get(mode, PROMPTS["study"])
    return role + _BASE_INSTRUCTION.format(pdf_text=pdf_text)


def extract_sentences(api_key: str, pdf_path: str, mode: str) -> list[str]:
    """
    1. Extract text from PDF using PyMuPDF (we control the text).
    2. Send that text to Gemini as a plain text prompt.
    3. Gemini returns sentences copied from our text.
    4. Those sentences are guaranteed to match search_for() on the same PDF.
    """
    # Step 1: extract text ourselves
    pdf_text = extract_full_text(pdf_path)

    # Step 2: build prompt with extracted text embedded
    prompt = get_prompt(mode, pdf_text)

    # Step 3: call Gemini with text only — no PDF file needed
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    # Step 4: parse and return
    sentences: list[str] = json.loads(
        response.text.encode("utf-8").decode("utf-8")
    )
    return sentences
