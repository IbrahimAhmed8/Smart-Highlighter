# Smart Highlighter

AI-powered PDF highlighter using Gemini 2.5 Flash.

## Setup & Run

```bash
cd api
pip install -r requirements.txt
python main.py
```

Then open **http://localhost:8000** in your browser.

> ⚠️  Do NOT open `client/index.html` directly — it will always fail with
> "Connection Failed" because browsers block file:// → http:// requests.
> Always use http://localhost:8000 after starting the server.

## Configuration

Edit `api/.env` and set your Gemini API key:

```
GEMINI_API_KEY="your-key-here"
```
