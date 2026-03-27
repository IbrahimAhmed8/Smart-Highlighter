import base64
import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core import extract_sentences, highlight_sentences

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Gemini PDF Insight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process-pdf")
async def process_pdf(
    mode: str = Form("study"),
    file: UploadFile = File(...),
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured on server.")

    temp_input = f"temp_{file.filename}"
    temp_output = f"highlighted_{file.filename}"

    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        sentences = extract_sentences(API_KEY, temp_input, mode)
        highlight_sentences(temp_input, temp_output, sentences)
        os.remove(temp_input)

        with open(temp_output, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
        os.remove(temp_output)

        return JSONResponse(content={
            "filename": f"highlighted_{mode}.pdf",
            "pdf_base64": pdf_base64,
            "total_sentences": len(sentences),
            "sentences": sentences,
        })

    except Exception as exc:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
