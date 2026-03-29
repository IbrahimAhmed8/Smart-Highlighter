# ai_service.py

import json
from .pdf_engine import extract_full_text
from google import genai
from google.genai import types


PROMPTS = {
    "study": """You are an expert academic tutor preparing a student for an exam.

Focus ONLY on sentences that:
- Define key concepts precisely
- Contain cause-effect relationships
- Include concrete facts (dates, laws, statistics, formulas)
- Represent core arguments or conclusions

EXCLUDE sentences that:
- Are introductory or transitional
- Contain vague language (e.g., "this shows", "it is important")
- Do not stand alone without surrounding context
""",

    "code": """You are a Senior Software Engineer conducting a code review.

Focus ONLY on sentences that:
- Describe functions, classes, or modules
- Explain core logic or data flow
- Mention configs, constants, or environment variables
- Define API inputs/outputs or behavior
- Highlight warnings, limitations, or bugs

EXCLUDE:
- Boilerplate comments
- Obvious or redundant explanations
- High-level descriptions without technical detail
""",

    "cyber": """You are a senior Cybersecurity Researcher writing a threat intelligence brief.

Focus ONLY on sentences that:
- Describe vulnerabilities (CVE, CWE, affected systems)
- Include severity (CVSS, risk explanation)
- Explain attack vectors or exploitation steps
- Contain IoCs (IPs, hashes, domains, paths)
- Provide remediation or mitigation steps

EXCLUDE:
- Generic security advice
- Awareness or training statements
- Marketing or non-technical text
""",

    "medical": """You are a licensed medical professional reviewing clinical documentation.

Focus ONLY on sentences that:
- Describe symptoms (with duration/severity)
- Contain diagnostic findings (labs, imaging, vitals)
- State diagnoses or clinical reasoning
- Include medications (dose, route, duration)
- Provide follow-up or red-flag instructions

EXCLUDE:
- Administrative text
- Consent boilerplate
- Non-clinical background
""",
}


_BASE_INSTRUCTION = """
DOCUMENT TEXT:
<text>
{pdf_text}
</text>

YOUR TASK:
Extract ONLY high-value, complete sentences from the document.

CRITICAL DEFINITION OF A VALID SENTENCE:
A valid sentence MUST:
- Contain a SUBJECT and a VERB (explicit or clearly implied)
- Express a COMPLETE idea (not a fragment)
- Be at least 10 words long
- Start with a capital letter (A–Z)
- End with ".", ":", or ";"

STRICT REJECTION RULES (VERY IMPORTANT):
DO NOT extract anything that:
- Is a single word (e.g., "learning")
- Is 2–9 words long
- Looks like a keyword, label, or tag
- Comes from broken PDF formatting
- Is part of a split sentence across lines
- Contains mostly nouns without a clear action
- Is a section title, header, or bullet label
- Starts with lowercase (likely mid-sentence fragment)

SEMANTIC REQUIREMENTS:
Each selected sentence MUST contain at least one:
- Defined concept
- Cause-effect relationship
- Measurable or factual information
- Technical or domain-specific explanation

DENSITY FILTER:
- Prefer sentences with multiple meaningful terms
- Reject vague or generic statements

SELF-VALIDATION (MANDATORY):
For each candidate sentence, internally verify:
1. Does it read naturally as a full sentence?
2. Would a human understand it without surrounding context?
3. Does it contain real informational value?
4. Is it free from PDF extraction artifacts?

Only include sentences that pass ALL checks.

STRICT COPYING RULES:
- Copy text EXACTLY as it appears in <text>
- Do NOT paraphrase or fix formatting
- Do NOT merge sentences
- Each sentence MUST be searchable word-for-word
- Do NOT include duplicates

OUTPUT FORMAT:
Return ONLY a valid JSON array.
No markdown. No explanation.

Example:
["Sentence one.", "Sentence two."]
"""


def get_prompt(mode: str, pdf_text: str) -> str:
    role = PROMPTS.get(mode, PROMPTS["study"])
    return role + _BASE_INSTRUCTION.format(pdf_text=pdf_text)


def extract_sentences(api_key: str, pdf_path: str, mode: str) -> list[str]:
    """
    Pipeline:
    1. Extract text from PDF (controlled source)
    2. Send clean text to Gemini
    3. Gemini returns STRICTLY filtered sentences
    4. Sentences match original text exactly
    """

    # Step 1: Extract text
    pdf_text = extract_full_text(pdf_path)

    # Optional (recommended): light cleanup
    pdf_text = _clean_text(pdf_text)

    # Step 2: Build prompt
    prompt = get_prompt(mode, pdf_text)

    # Step 3: Call Gemini
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    # Step 4: Parse response safely
    sentences: list[str] = _safe_json_parse(response.text)

    return sentences


def _clean_text(text: str) -> str:
    """
    Light normalization to reduce garbage extraction.
    Keeps text faithful but removes obvious noise.
    """
    lines = text.splitlines()

    cleaned_lines = []
    for line in lines:
        line = line.strip()

        # Remove empty lines
        if not line:
            continue

        # Remove likely page numbers
        if line.isdigit():
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _safe_json_parse(text: str) -> list[str]:
    """
    Robust JSON parsing in case model adds minor noise.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt recovery
        text = text.strip()

        # Remove accidental code fences if any
        if text.startswith("```"):
            text = text.strip("`")

        return json.loads(text)