<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

<h1 align="center">open-brain</h1>

<p align="center">
  <strong>Capture anything. Recall everything. Own your data.</strong><br>
  A self-hosted personal knowledge system — rant at it, it figures the rest out.
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#the-pipeline">The Pipeline</a> •
  <a href="#web-ui">Web UI</a> •
  <a href="#api">API</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#storage">Storage</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## What it does

You throw raw thoughts at it — rushed, ungrammatical, repetitive, half-formed. It distils them into clean, dense notes, classifies them, stores them in a searchable vault, and lets you query your own knowledge in plain English.

**What it is:** a searchable external memory. Ask it "what happened with the holiday requests?" and it finds everything relevant, across time.

**What it isn't:** a narrator. It won't reconstruct a two-year story or spot patterns across notes automatically. The Obsidian vault is the long-term durable record — open it and search chronologically when you need the full picture.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Docker Compose                          │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │ open-brain  │ │   whisper   │ │      chromadb        │  │
│  │  FastAPI    │ │  (voice)    │ │   (vectors / RAG)    │  │
│  │  :8000      │ │  :8001      │ │      :8002           │  │
│  └──────┬──────┘ └─────────────┘ └──────────────────────┘  │
│         │                                                    │
│  ┌──────▼──────────────────────┐                            │
│  │   brain-web  (Mr.Fran)      │                            │
│  │   terminal UI · :8010       │                            │
│  └─────────────────────────────┘                            │
└──────────────────────┬───────────────────────────────────────┘
                       │ LAN
                       ▼
          ┌─────────────────────────┐
          │     Ollama (external)   │
          │   192.168.x.x:11434     │
          │                         │
          │  phi4-mini  — preprocess│
          │  qwen2.5:7b — classify  │
          │  nomic-embed — embed    │
          │  qwen2.5:7b — query     │
          └─────────────────────────┘
                       │
                       ▼
          ┌─────────────────────────┐
          │        Storage          │
          │  /vault — markdown      │
          │  /data  — ChromaDB      │
          └─────────────────────────┘
```

Ollama is **not bundled** — point `OLLAMA_HOST` at any Ollama instance on your LAN.

---

## The Pipeline

Every capture goes through four stages:

```
Raw input (your words, unfiltered)
        │
        ▼
   PREPROCESS  ──  phi4-mini:3.8b  ──────────────────────────────
   Distil into dense personal notes. Cut repetition. Keep all      │
   unique facts, emotion, context. Fix spelling. Add one → action  │
   line. Raw input preserved in vault frontmatter as raw_input.    │
        │                                                           │
        ▼                                                           │
   CLASSIFY  ──  qwen2.5:7b ─────────────────────────────────────  │
   Assign category (idea / task / person / project / learning /    │
   admin / reference), title, tags, confidence.                    │
        │                                                           │
        ▼                                                           │
   EMBED  ──  nomic-embed-text ──────────────────────────────────  │
   Vector embedding of clean content → ChromaDB.                   │
   Raw input is never embedded — only clean text.                  │
        │                                                           │
        ▼                                                           │
   VAULT  ──  Obsidian-compatible markdown ──────────────────────  │
   Stored as /vault/{category}/{id}.md with full YAML frontmatter. │
        │            including raw_input ◄──────────────────────────
        ▼
   Done. Searchable immediately.
```

**Why separate preprocess and classify models:**
Preprocessing (distillation) and classification are different cognitive tasks. Keeping them on separate model slots means you can tune each independently without affecting the other.

---

## Web UI

`brain-web` runs at `:8010` — dark terminal aesthetic, mobile-first.

| Tab | What it does |
|-----|-------------|
| **Capture** | Type or dictate. On submit: input hides, processing timer shows elapsed time, confirmation card appears with title, date, and category. Tap the title to open the full note. |
| **Ask** | Natural language question answered by RAG — retrieves relevant notes, synthesises an answer. |
| **Search** | Filter by category, tags, or free text. Results are cards — tap any to open full markdown view. |
| **Digest** | Generate a daily or weekly summary of recent captures. |

**Mobile keyboard shortcut:** tap the `> _` button at the bottom of the screen to activate the keyboard without reaching up to the text box. Implemented as a `<label>` element so iOS Safari opens the keyboard natively.

---

## API

All endpoints are on `open-brain` at `:8000`. `brain-web` proxies the relevant ones from `:8010`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/capture` | POST | Full pipeline: preprocess → classify → embed → vault |
| `/api/query` | POST | RAG query against the knowledge base |
| `/api/search` | GET | Search by `category`, `tags`, `text`, `limit` |
| `/api/digest` | POST | Summarise recent notes (`period: daily\|weekly`) |
| `/api/health` | GET | Health check |

<details>
<summary><strong>Examples</strong></summary>

```bash
# Capture
curl -X POST http://localhost:8000/api/capture \
  -H "Content-Type: application/json" \
  -d '{"text": "Ran the retro again today, same outcome as last three times — no real change. Need to escalate.", "source": "cli"}'

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What issues have I had with the team this quarter?"}'

# Search
curl "http://localhost:8000/api/search?category=task&limit=10"
curl "http://localhost:8000/api/search?text=Ross&limit=5"

# Digest
curl -X POST http://localhost:8000/api/digest \
  -H "Content-Type: application/json" \
  -d '{"period": "weekly"}'
```

</details>

---

## Configuration

Key variables in `.env`:

```bash
# Storage
VAULT_PATH=/vault                        # Where markdown files live
DATA_PATH=/data                          # ChromaDB storage

# Ollama
OLLAMA_HOST=http://192.168.1.100:11434   # External Ollama instance

# Model assignment — each task runs on its own model slot
OLLAMA_PREPROCESS_MODEL=phi4-mini:3.8b          # Distil raw input
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M        # Classify
OLLAMA_EMBED_MODEL=nomic-embed-text             # Embed
OLLAMA_QUERY_MODEL=qwen2.5:7b-instruct-q4_K_M  # Answer queries
OLLAMA_SUMMARIZE_MODEL=qwen2.5:7b-instruct-q4_K_M

# Provider routing (ollama | gemini | openai)
AI_CLASSIFY_PROVIDER=ollama
AI_PREPROCESS_PROVIDER=ollama
```

See [.env.example](.env.example) for all options.

---

## Storage

All notes are stored as **Obsidian-compatible markdown** under `/vault`:

```
/vault
├── idea/
├── task/
├── person/
├── project/
├── learning/
├── admin/
├── reference/
└── _inbox/          # Low-confidence items (< threshold)
```

Each file:

```yaml
---
id: 20260305-143022-abc123
type: idea
title: Retro process is broken — needs escalation
tags: [team, process, retro]
confidence: 0.91
source: web_text
captured: 2026-03-05T14:30:22
raw_input: "so the standup this morning was an absolute joke like i dont even
  know why we bother having them anymore..."
---

Ran retro for the fourth time — same result, no change. Mark avoids conflict,
everyone nods, nothing ships. Team can see it but no one pushes back.

→ Talk to Mark before Friday's retro, not after — go in with a plan.
```

`raw_input` is your original unedited text. It lives in frontmatter only — never embedded, never retrieved, never used in queries. It's there so you can always see exactly what you said.

---

## Deployment

### Proxmox LXC (Debian 12)

```bash
# On Proxmox host — create and enter the container
pct create 111 local:vztmpl/debian-12-standard_*.tar.zst \
  --hostname open-brain --memory 2048 --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.55/24,gw=192.168.1.1 \
  --unprivileged 1 --features nesting=1
pct start 111 && pct enter 111

# Inside the container
apt update && apt install -y git docker.io docker-compose-plugin
git clone https://github.com/mister-fran-89/open-brain.git /opt/open-brain
cd /opt/open-brain
cp .env.example .env
nano .env   # Set OLLAMA_HOST and model names
docker compose up -d
```

### Permissions (unprivileged LXC)

UID 1000 inside an unprivileged container maps to UID 101000 on the host. Fix bind-mount ownership on the **host**:

```bash
chown -R 101000:101000 /path/to/vault /path/to/data
chmod -R 775 /path/to/vault /path/to/data
```

---

## License

MIT

---

<p align="center">
  <sub>Built for humans who think faster than they can organise.</sub>
</p>
