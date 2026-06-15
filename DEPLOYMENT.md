# NarrativeIQ — Deployment Guide (Render + Supabase)

## Do I need Supabase?

**Short answer: Yes, recommended — but optional.**

NarrativeIQ uses PostgreSQL for:
- Saving live topic search snapshots (so they persist across sessions)
- Background ingestion scheduler history
- `dim_live_topic` warehouse table for narrative intelligence

**Without a database:** The app still works fully in warehouse mode (the default 50k-record mart) and live-search mode. Only the *Save Brief* / *Saved Snapshots* features require PostgreSQL.

**Render's own PostgreSQL** (free tier) expires after **90 days** and has 256 MB storage.  
**Supabase** (free tier) is **permanent**, 500 MB, and has a generous connection pool — ideal for a portfolio/exhibition deployment.

> ✅ **Recommended:** Use **Supabase** for the database.

---

## Step-by-Step Deployment

### 1. Set up Supabase (Database)

1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Create a new project → choose a region close to you.
3. After setup, go to **Settings → Database → Connection string → URI** and copy the `postgresql://...` connection string.
4. In the Supabase **SQL Editor**, paste and run the schema file:
   ```
   warehouse/003_live_topic_schema.sql
   ```
   This creates the `dim_live_topic` and related tables inside a `narrativeiq` schema.

5. Keep the connection string — you'll need it in the next step.

---

### 2. Deploy Backend to Render

1. Go to [https://render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository.
3. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables:**
   | Key | Value |
   |-----|-------|
   | `NARRATIVEIQ_DATABASE_URL` | Your Supabase connection string (from step 1) |
   | `NARRATIVEIQ_ADMIN_KEY` | Any secure password you choose |
   | `DEEPSEEK_API_KEY` | (Optional) Your DeepSeek API key |
5. Click **Deploy**. Note the URL (e.g., `https://narrativeiq-backend.onrender.com`).

---

### 3. Deploy Frontend to Render

1. **New → Web Service** → same GitHub repo.
2. Configure:
   - **Root Directory:** `frontend`
   - **Runtime:** Node
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `node node_modules/next/dist/bin/next start -H 0.0.0.0 -p $PORT`
3. Add **Environment Variables:**
   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_BASE_URL` | Your backend URL from step 2 |
4. Click **Deploy**.

---

### 4. Update CORS in Backend (Important!)

After deploying the frontend, open `backend/app/main.py` and update the CORS `allow_origins` to include your Render frontend URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://narrativeiq-frontend.onrender.com",  # ← add your frontend URL
    ],
    ...
)
```

Commit and push — Render will auto-redeploy.

---

### 5. Run the Live Topic Schema on Supabase

In your Supabase **SQL Editor**, run the contents of:
```
warehouse/003_live_topic_schema.sql
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `NARRATIVEIQ_DATABASE_URL` | Optional | Full PostgreSQL connection URI (Supabase or Render PG) |
| `NARRATIVEIQ_ADMIN_KEY` | Optional | Admin password for ETL / upload / warehouse endpoints |
| `DEEPSEEK_API_KEY` | Optional | DeepSeek API key for AI enrichment feature |
| `NEXT_PUBLIC_API_BASE_URL` | **Required on Render** | Backend URL (e.g., `https://narrativeiq-backend.onrender.com`) |

---

## Local Development

```powershell
# Backend
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
node node_modules/next/dist/bin/next start -H 0.0.0.0 -p 3000
```

Or use the one-click start script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1
```
