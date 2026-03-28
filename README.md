# Smart PDF Highlighter

Most PDF tools just do a basic keyword search. We wanted something that actually reads the context of a document and does the heavy lifting for us. This tool takes your PDF, figures out what matters based on your field, and hands you back a fully highlighted file ready to download. 

Built for LovHack Season 2.

## Live Demo
You can test the live version of the application here:
https://smart-highlighter.vercel.app/

## What it does
* Context-aware extraction: Uses Gemini to understand the text instead of just finding exact words.
* Four modes: Tailored for Study, Cybersecurity, Code Analysis, and Medical docs.
* Auto-highlighting: It doesn't just return a text summary. It uses PyMuPDF to highlight the actual document and hands it back to you.
* Mobile-ready: Clean UI built with Tailwind, plus a fallback download button since mobile browsers usually block blob PDFs in iframes.

## Tech Stack
* Frontend: HTML, Vanilla JS, Tailwind CSS (Vercel)
* Backend: Python, FastAPI, PyMuPDF, Docker (Hugging Face Spaces)
* AI Core: Google Gemini API

## How it works under the hood
1. You upload a PDF and pick a mode on the frontend.
2. The file gets sent to our FastAPI backend.
3. Gemini scans the text and pulls out the key sentences based on the context.
4. PyMuPDF locates those exact sentences in the document and applies the highlights.
5. The backend encodes the new PDF to base64 and sends it back.
6. The frontend renders it and gives you a download link.

Try it out: https://smart-highlighter.vercel.app/
