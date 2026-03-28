import json
from google import genai
from google.genai import types

PROMPTS = {
    "study": """You are an expert academic tutor preparing a student for an exam.
From the provided document, extract only the most high-value sentences a student must memorize or understand. Focus on:
1. Precise definitions of key terms or concepts
2. Statements that explain cause-effect relationships or mechanisms
3. Specific facts: dates, statistics, formulas, laws, or named theories
4. Concluding or thesis statements that capture the author's main argument
Ignore transitional phrases, examples, filler sentences, and redundant restatements.""",

    "code": """You are a Senior Software Engineer conducting a code review and knowledge transfer.
From the provided document, extract only the sentences that carry actionable technical meaning. Focus on:
1. Function, class, or module definitions and their stated purpose
2. Descriptions of core algorithmic logic or data flow
3. Configuration values, environment variables, or hard-coded constants with their intent
4. Explicit warnings, known limitations, or areas flagged as bug-prone
5. API contracts, expected inputs/outputs, and error-handling behavior
Ignore boilerplate comments, auto-generated text, and obvious or redundant descriptions.""",

    "cyber": """You are a senior Cybersecurity Researcher writing a threat intelligence brief.
From the provided document, extract only the sentences that carry security-relevant technical detail. Focus on:
1. Precise vulnerability or weakness descriptions (e.g., CVE IDs, CWE types, affected components)
2. Severity ratings, CVSS scores, and their justification
3. Attack vectors, exploitation prerequisites, and step-by-step Proof of Concept actions
4. Indicators of Compromise (IoCs): hashes, IPs, domains, registry keys, file paths
5. Specific remediation steps, patches, mitigations, or workarounds
Ignore marketing language, general security advice not tied to the specific issue, and repetitive disclaimers.""",

    "medical": """You are a licensed medical professional reviewing clinical documentation.
From the provided document, extract only the sentences that carry direct clinical significance. Focus on:
1. Specific patient-reported symptoms and their onset, duration, or severity
2. Objective diagnostic findings: lab values, imaging results, vital signs with their reference context
3. Diagnoses, differential diagnoses, and the clinical reasoning behind them
4. Prescribed medications with dosage, route, frequency, and duration
5. Follow-up instructions, red-flag warnings given to the patient, and referral details
Ignore administrative filler, standard consent boilerplate, and non-clinical background text.""",
}

_BASE_INSTRUCTION = """

Your job is to act as a highlighter on the original text.
Identify every sentence that deserves to be marked as important based on the criteria above.

RULES:
- Copy each sentence VERBATIM and EXACTLY as it appears — do not paraphrase, summarize, or merge.
- Preserve the original language; do not translate.
- Each marked sentence must be self-contained and meaningful without surrounding context.
- Prefer specificity: if a general and a specific sentence convey the same point, mark only the specific one.
- Do not mark the same sentence twice even if it appears in multiple sections.

OUTPUT FORMAT:
Return ONLY a valid JSON array of the marked sentences. No markdown fences, no commentary.
Example: ["Sentence one.", "Sentence two.", "Sentence three."]
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
