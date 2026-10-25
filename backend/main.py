"""Mock backend for the Half Life pendant. Run:  uvicorn main:app --reload

Matches what the firmware uploads: a WAV body plus X-Device-Id and X-Bookmarks (comma separated seconds).
The 'database' is an in-memory list. backend/schema.sql is the planned Supabase table.
"""
import os
from fastapi import FastAPI, Header, HTTPException, Request

import pipeline

API_TOKEN = os.environ.get("PENDANT_API_TOKEN", "change-me")
app = FastAPI(title="Half Life pendant backend (mock)")
DB: list[dict] = []


def _check(authorization: str):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="bad token")


@app.post("/api/upload")
async def upload(request: Request, authorization: str = Header(default=""),
                 x_device_id: str = Header(default="unknown"), x_bookmarks: str = Header(default="")):
    _check(authorization)
    audio = await request.body()
    if len(audio) < 1000:
        raise HTTPException(status_code=400, detail="audio too short")
    marks = [float(x) for x in x_bookmarks.split(",") if x.strip()]
    rec = pipeline.process(audio, marks)
    rec["id"] = len(DB)
    rec["device_id"] = x_device_id
    DB.append(rec)
    return {"ok": True, "id": rec["id"]}


@app.get("/api/recordings")
def list_recordings(authorization: str = Header(default="")):
    _check(authorization)
    return DB


@app.get("/api/search")
def search(q: str, authorization: str = Header(default="")):
    _check(authorization)
    # TODO: embed q and run a pgvector cosine search. Plain text match for now.
    return [r for r in DB if q.lower() in (r["transcript"] + " " + r["summary"]).lower()]


@app.delete("/api/recordings")
def delete_everything(authorization: str = Header(default="")):
    _check(authorization)
    DB.clear()
    return {"ok": True}
