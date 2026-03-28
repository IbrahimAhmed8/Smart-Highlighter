import base64
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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

# ── Serve the client folder as static files ──────────────────────────────────
# This means opening http://localhost:8000 in your browser is all you need.
# No separate file server, no mixed-content errors.
CLIENT_DIR = Path(__file__).parent.parent / "client"
if CLIENT_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(CLIENT_DIR)), name="static")

    @app.get("/")
    async def serve_ui():
        return FileResponse(str(CLIENT_DIR / "index.html"))


# ── API endpoint ─────────────────────────────────────────────────────────────
@app.post("/process-pdf")
async def process_pdf(
    mode: str = Form("study"),
    file: UploadFile = File(...),
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in .env")

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
        import traceback
        traceback.print_exc()          # prints full traceback to terminal
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)


if __name__ == "__main__":
    import uvicorn
    print("\n✅  Smart Highlighter running → http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
