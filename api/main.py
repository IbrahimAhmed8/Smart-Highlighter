import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

        return FileResponse(
            temp_output,
            media_type="application/pdf",
            filename=f"highlighted_{mode}.pdf",
        )

    except Exception as exc:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
