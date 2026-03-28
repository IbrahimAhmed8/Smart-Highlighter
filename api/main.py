import base64
import os
import tempfile
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import core modules
from core import extract_sentences, highlight_sentences

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Smart Highlighter API")

# ── CORS CONFIGURATION (CRITICAL FOR VERCEL) ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Vercel to communicate with this API
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

# ── HEALTH CHECK ENDPOINT ────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "🚀 API is LIVE and running perfectly!",
        "cors": "Enabled for all origins",
        "message": "Send a POST request to /process-pdf to use the engine."
    }

# ── API ENDPOINT ─────────────────────────────────────────────────────────
@app.post("/process-pdf")
async def process_pdf(
    mode: str = Form("study"),
    file: UploadFile = File(...),
):
    if not API_KEY:
        print("❌ ERROR: GEMINI_API_KEY is missing!")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in environment variables")

    fd_in, temp_input = tempfile.mkstemp(suffix=".pdf")
    fd_out, temp_output = tempfile.mkstemp(suffix=".pdf")
    os.close(fd_in)
    os.close(fd_out)

    try:
        print(f"📥 Received file: {file.filename} | Mode: {mode}")
        
        with open(temp_input, "wb") as buffer:
            buffer.write(await file.read())

        print("🧠 Extracting sentences via Gemini...")
        sentences = extract_sentences(API_KEY, temp_input, mode)
        
        if not sentences:
            print("⚠️ Warning: No sentences extracted by Gemini.")

        print("🖍️ Highlighting sentences in PDF...")
        match_results = highlight_sentences(temp_input, temp_output, sentences)

        with open(temp_output, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

        highlighted_count = sum(1 for r in match_results if r["highlighted"])
        not_found_count = len(match_results) - highlighted_count

        print(f"✅ Success! Highlighted {highlighted_count} sentences.")

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
        print("❌ SERVER ERROR OCCURRED:")
        traceback.print_exc()  
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exc)}")

    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)


if __name__ == "__main__":
    import uvicorn
    print("\n✅ Smart Highlighter running → http://0.0.0.0:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)