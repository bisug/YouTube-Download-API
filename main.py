from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import httpx
import urllib.parse

app = FastAPI(title="NoTube API", description="Unofficial NoTube API Wrapper", version="1.0.0")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Header & formats like in JS
HEADER = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://notube.lol",
    "Referer": "https://notube.lol/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"'
}

FORMATS = [
    "mp3hd", "mp4", "mp3", "mp4hd", "mp42k", "m4a", "wav", "3gp", "flv"
]

async def fetch_with_retry(url, data, retries=3, delay=2):
    async with httpx.AsyncClient(timeout=15) as client:
        last_error = None
        for attempt in range(retries):
            try:
                resp = await client.post(url, headers=HEADER, data=data)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_error = str(e)
                if attempt == retries - 1:
                    raise
                import asyncio
                await asyncio.sleep(delay * (2 ** attempt))
        raise Exception(last_error)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/download")
async def download(
    url: str = Query(..., description="YouTube video URL"),
    format: str = Query("mp4hd", description="Download format"),
    lang: str = Query("en", description="Language"),
    subscribed: str = Query("false", description="Subscribed status")
):
    if format not in FORMATS:
        format = "mp4"

    form_data = f"url={urllib.parse.quote(url)}&format={format}&lang={lang}&subscribed={subscribed}"

    try:
        data = await fetch_with_retry("https://s53.notube.lol/recover_weight.php", form_data)
        return {
            "success": True,
            "data": data,
            "format": format,
            "lang": lang,
            "subscribed": subscribed,
            "videoUrl": url,
            "Owner": "https://github.com/bisug",
            "status": 200,
            "successful": "success"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error fetching video data: {str(e)}"}
        )

@app.get("/health")
async def health():
    return {"status": "ok", "message": "API is running", "version": "1.0.0"} 
