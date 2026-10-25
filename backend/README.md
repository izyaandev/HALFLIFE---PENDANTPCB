# backend (mock)

A small FastAPI server that accepts what the pendant uploads and runs it through a mock AI pipeline.

```
cd backend
pip install -r requirements.txt
PENDANT_API_TOKEN=change-me uvicorn main:app --reload
pytest -q          # 7 tests: router tiers, fallback, upload, bookmarks, search, delete-everything
```

- `router.py`: the AI router. Tags/titles always go to the fast model; summaries go to the fast model under 1,500 words and the strong model above. If a provider fails it tries the other tier.
- `pipeline.py`: transcribe, then summarize / action items / tags. Transcription and model calls are stubs until a provider is picked.
- `schema.sql`: planned Supabase tables (devices, recordings, bookmarks) with a pgvector column for semantic search.
