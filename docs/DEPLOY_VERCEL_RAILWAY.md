# Deploy: Vercel (frontend) + Railway (backend)

This guide deploys the OH AI Agent so you can share a **Vercel URL** with end users. The **Railway** service runs the FastAPI backend, ChromaDB, and audit log.

**Estimated fixed cost:** ~$5/month (Railway only). Vercel Hobby is free. LLM is pay-per-use.

### Minimal pricing checklist

| Item | Choose | Cost |
|---|---|---|
| Frontend | **Vercel Hobby** (personal) | **$0** |
| Backend | **Railway Hobby** (~512 MB RAM, 1 GB volume) | **~$5/mo** |
| LLM | OpenRouter + `openai/gpt-4o-mini` | **~$0.01–0.05** per workflow |
| Site password | `SITE_PASSWORD` env var (built-in middleware) | **$0** |
| Skip | Vercel Pro, Deployment Protection add-on ($150/mo) | — |

**Do not pay for:** Vercel Pro, Password Protection add-on, or a custom domain (optional).

---

## Architecture

```
End user → https://your-app.vercel.app (Next.js UI)
                ↓ NEXT_PUBLIC_API_URL
           https://your-api.up.railway.app (FastAPI + ChromaDB)
                ↓
           OpenRouter / OpenAI (pay per request)
```

---

## Part 1 — Railway (backend)

### 1. Create a Railway project

1. Sign in at [railway.app](https://railway.app).
2. **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Railway detects `railway.toml` and builds from the root `Dockerfile`.

### 2. Add persistent storage

ChromaDB and audit logs must survive redeploys.

1. In your Railway service, open **Settings** → **Volumes**.
2. **Add Volume**:
   - **Mount path:** `/app/data`
   - Size: 1 GB is enough to start.

### 3. Set environment variables

In the Railway service → **Variables**, add:

| Variable | Value | Notes |
|---|---|---|
| `OH_ENVIRONMENT` | `production` | |
| `OH_DEBUG` | `false` | |
| `OH_LOG_LEVEL` | `INFO` | |
| `OH_LLM_PROVIDER` | `openrouter` | or `litellm` |
| `OH_LLM_API_KEY` | `sk-or-...` | Your LLM API key |
| `OH_LLM_MODEL` | `openai/gpt-4o-mini` | Cost-effective default |
| `OH_CHROMA_PERSIST_DIR` | `/app/data/chroma` | On the mounted volume |
| `OH_AUDIT_LOG_FILE` | `/app/data/logs/audit.jsonl` | On the mounted volume |

Optional:

| Variable | Value |
|---|---|
| `OH_LLM_BASE_URL` | Leave empty for OpenRouter preset |
| `OH_LLM_TEMPERATURE` | `0.1` |
| `OH_LLM_MAX_TOKENS` | `4096` |

Do **not** commit API keys to git. Set them only in Railway.

### 4. Generate a public URL

1. Open **Settings** → **Networking**.
2. **Generate Domain** (e.g. `oh-ai-agent-production.up.railway.app`).
3. Copy this URL — you need it for Vercel.

### 5. Verify the backend

Open in a browser:

- `https://YOUR-RAILWAY-URL.up.railway.app/health` — should return JSON with `"status": "healthy"`.
- `https://YOUR-RAILWAY-URL.up.railway.app/docs` — Swagger UI.

First startup may take 30–60 seconds while documents in `knowledge_base/` are ingested into ChromaDB.

---

## Part 2 — Vercel (frontend)

### 1. Create a Vercel project

1. Sign in at [vercel.com](https://vercel.com).
2. **Add New** → **Project** → import the same GitHub repo.
3. **Root Directory:** click **Edit** and set to `frontend`.
4. Framework preset should detect **Next.js** automatically.

### 2. Set environment variables

Before the first deploy, add:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RAILWAY-URL.up.railway.app` |
| `SITE_PASSWORD` | A shared demo password (recommended — free lock screen) |

The frontend proxies API calls through `/api/backend` on the same Vercel origin (no browser CORS issues). `NEXT_PUBLIC_API_URL` is used by Next.js rewrites at build time.

Set this for **Production**, **Preview**, and **Development** so all builds use the correct backend.

> `NEXT_PUBLIC_*` variables are baked in at build time. After changing this value, trigger a **Redeploy** on Vercel.

### 3. Deploy

Click **Deploy**. When finished, Vercel gives you a URL like:

`https://oh-ai-agent.vercel.app`

Share the Vercel URL and credentials with your end user:

- **Username:** `ohdemo` (fixed)
- **Password:** your `SITE_PASSWORD` value

### 4. Verify the frontend

1. Open the Vercel URL.
2. On the **Dashboard**, confirm **System Health** shows the backend as healthy.
3. Try **Workflow Generator** with a simple hazard test.

---

## Part 3 — Protect the URL (free)

The app has no user accounts. Without protection, anyone with the link can spend your LLM quota.

**Recommended (free):** set `SITE_PASSWORD` on Vercel. The repo includes middleware that shows a browser login prompt. Username must be **`ohdemo`**; password must match `SITE_PASSWORD`.

**Skip (paid):** Vercel Password Protection requires Pro + a **$150/month** add-on — not needed for a single demo user.

**Optional:** set a spending cap on [OpenRouter](https://openrouter.ai/settings/credits) so LLM costs cannot run away.

---

## Redeploying after code changes

| Change | Action |
|---|---|
| Backend code | Push to GitHub — Railway redeploys automatically |
| Frontend code | Push to GitHub — Vercel redeploys automatically |
| New `NEXT_PUBLIC_API_URL` | Update Vercel env var → **Redeploy** |
| New Railway env vars | Update in Railway → service restarts |

---

## Troubleshooting

### Dashboard shows backend unreachable

- Confirm `NEXT_PUBLIC_API_URL` matches the Railway public URL (no trailing slash).
- **Redeploy Vercel** after changing env vars (build-time).
- In DevTools → Network, requests should go to `/api/backend/health` on your Vercel domain (not `localhost`).
- Check Railway logs for startup errors.

### Railway deploy fails health check

- Ensure the volume is mounted at `/app/data` and env vars point inside it:
  - `OH_CHROMA_PERSIST_DIR=/app/data/chroma`
  - `OH_AUDIT_LOG_FILE=/app/data/logs/audit.jsonl`
- Check **Deploy Logs** (not just build logs) for `Permission denied` or ChromaDB errors.
- First deploy can take 1–2 minutes; health check timeout is 300s.
- Open `https://YOUR-URL/health` manually after deploy — should return `"status": "healthy"`.

### 402 / 502 on workflow generation

- Invalid or missing LLM API key.
- Insufficient provider quota — check OpenRouter/OpenAI billing.

### Knowledge base empty after redeploy

- Volume not mounted, or `OH_CHROMA_PERSIST_DIR` not pointing inside `/app/data`.
- Re-ingest via the **Knowledge Base** page or `POST /api/v1/knowledge/ingest`.

### CORS errors in browser

- Backend CORS allows all origins by default. If you changed this, add your Vercel URL to allowed origins.

---

## Cost tips

- **Fixed hosting:** ~$5/mo total (Railway only; Vercel Hobby is $0).
- **LLM:** `OH_LLM_MODEL=openai/gpt-4o-mini` — avoid larger models for demos.
- **OpenRouter:** add a credit limit in account settings.
- **Railway:** use the smallest volume (1 GB) and one service; avoid extra add-ons.
- **Do not upgrade** to Vercel Pro unless you need team features — Basic Auth via `SITE_PASSWORD` is free.

---

## Quick reference

| Service | URL | Config |
|---|---|---|
| Frontend | `https://*.vercel.app` | Root dir: `frontend`, `NEXT_PUBLIC_API_URL` |
| Backend | `https://*.up.railway.app` | Root `Dockerfile`, volume at `/app/data` |
| LLM | External | `OH_LLM_API_KEY`, `OH_LLM_MODEL` |
