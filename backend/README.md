# NarrativeIQ Backend

FastAPI service over the generated NarrativeIQ mart.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs).
