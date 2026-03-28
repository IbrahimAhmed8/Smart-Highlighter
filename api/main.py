import base64
import os
import tempfile
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core import extract_sentences, highlight_sentences

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Smart Highlighter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "🚀 API is LIVE on Hugging Face Spaces!"}

@app.post("/process-pdf")
async def process_pdf(
    mode: str = Form("study"),
    file: UploadFile = File(...),
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in Environment Variables")

    fd_in, temp_input = tempfile.mkstemp(suffix=".pdf")
    fd_out, temp_output = tempfile.mkstemp(suffix=".pdf")
    os.close(fd_in)
    os.close(fd_out)

    try:
        with open(temp_input, "wb") as buffer:
            buffer.write(await file.read())

        sentences = extract_sentences(API_KEY, temp_input, mode)
        match_results = highlight_sentences(temp_input, temp_output, sentences)

        with open(temp_output, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

        highlighted_count = sum(1 for r in match_results if r["highlighted"])
        not_found_count = len(match_results) - highlighted_count

        return JSONResponse(content={
            "filename": f"highlighted_{mode}.pdf",
            "pdf_base64": pdf_base64,
            "total_sentences": len(sentences),
            "sentences": sentences,
            "match_stats": {
                "highlighted": highlighted_count,
                "not_found": not_found_count,
            },
            "match_results": match_results,
        })

    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)