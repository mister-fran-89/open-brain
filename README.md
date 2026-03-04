<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

<h1 align="center">Open Brain</h1>

<p align="center">
  <strong>Your second brain that never forgets.</strong><br>
  Capture anything. Find everything. Own your data.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#api">API</a> •
  <a href="#cli">CLI</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## Quick Start

```bash
# Clone and configure
git clone https://github.com/mister-fran-89/open-brain.git
cd open-brain
cp .env.example .env

# Point to your LLM server (edit .env)
# OLLAMA_HOST=http://192.168.1.100:11434

# Start services
docker compose up -d

# Capture your first thought
curl -X POST http://localhost:8000/api/capture \
  -H "Content-Type: application/json" \
  -d '{"text": "Met Alice Chen from Acme Corp today"}'
```

Open the web interface at `http://localhost:8010`.

---

## Features

| | |
|---|---|
| **Capture** | Text, webhooks — classify and store automatically |
| **Query** | Natural language questions with RAG-powered answers |
| **Search** | Full-text search + category/tag filters |
| **Digest** | Daily and weekly summaries delivered anywhere |
| **Web UI** | Mobile-first terminal interface (Mr.Fran) at `:8010` |
| **Storage** | Obsidian-compatible markdown — you own your data |
| **AI** | Pluggable providers (Ollama, Gemini, OpenAI, Claude) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Docker Compose                          │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐   │
│  │ Open Brain  │ │   Whisper   │ │       ChromaDB       │   │
│  │   FastAPI   │ │  (voice)    │ │    (vectors/RAG)     │   │
│  │   :8000     │ │   :8001     │ │       :8002          │   │
│  └──────┬──────┘ └──────┬──────┘ └──────────────────────┘   │
│         │               │                                     │
│  ┌──────▼───────────────▼──────┐                             │
│  │       brain-web (Mr.Fran)   │                             │
│  │    terminal UI · :8010      │                             │
│  └─────────────────────────────┘                             │
└──────────────────────┬───────────────────────────────────────┘
                       │ LAN
                       ▼
          ┌─────────────────────┐
          │   LLM Server        │
          │  (Ollama — external)│
          │  192.168.x.x:11434  │
          └─────────────────────┘
                       │
                       ▼
          ┌─────────────────────┐
          │     Storage         │
          │  /vault  │  /data   │
          │   (md)   │ (sqlite) │
          └─────────────────────┘
```

---

## Web UI

`brain-web` is a minimal dark-terminal interface running at `:8010`.

| Tab | What it does |
|-----|-------------|
| **Capture** | Type or dictate a thought — classified and stored instantly |
| **Ask** | Natural language question against your knowledge base |
| **Search** | Filter by category, tags, or full-text |
| **Digest** | Generate a daily or weekly summary |

Optimised for mobile (iPhone). Tap the `> _` button at the bottom to activate the keyboard without reaching for the text box.

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/capture` | POST | Capture and classify text |
| `/api/query` | POST | Ask questions (RAG) |
| `/api/search` | GET | Search with filters |
| `/api/digest` | POST | Generate summary |
| `/api/health` | GET | Health check |

<details>
<summary><strong>Examples</strong></summary>

```bash
# Capture
curl -X POST http://localhost:8000/api/capture \
  -H "Content-Type: application/json" \
  -d '{"text": "Project idea: Build a CLI for note-taking", "source": "cli"}'

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What project ideas do I have?"}'

# Search
curl "http://localhost:8000/api/search?category=person&limit=10"

# Digest
curl -X POST http://localhost:8000/api/digest \
  -H "Content-Type: application/json" \
  -d '{"period": "daily"}'
```

</details>

---

## CLI

```bash
brain capture "Met John at the conference"
brain query "Who did I meet recently?"
brain search --category person
brain digest --period weekly
```

---

## Deployment

### One-liner (Debian 12 LXC)

```bash
curl -fsSL https://raw.githubusercontent.com/mister-fran-89/open-brain/main/setup.sh | sudo bash
```

### Manual

```bash
# 1. Clone
git clone https://github.com/mister-fran-89/open-brain.git /opt/open-brain
cd /opt/open-brain

# 2. Configure
cp .env.example .env
nano .env  # Set OLLAMA_HOST and paths

# 3. Start
docker compose up -d

# 4. (Optional) Mount NAS for vault
# Add to /etc/fstab:
# //nas/share /vault cifs credentials=/etc/nas-creds,uid=1000 0 0
```

---

## Configuration

Key environment variables in `.env`:

```bash
VAULT_PATH=/vault                       # Where markdown files live
DATA_PATH=/data                         # SQLite and ChromaDB storage
OLLAMA_HOST=http://192.168.1.100:11434  # Your external LLM server IP
AI_CLASSIFY_PROVIDER=ollama             # ollama | gemini | openai
GEMINI_API_KEY=                         # If using Gemini
```

Ollama is **not bundled** — point `OLLAMA_HOST` at any Ollama instance on your LAN. See [.env.example](.env.example) for all options.

---

## Storage

All data is stored as **Obsidian-compatible markdown**:

```
/vault
├── people/
│   └── alice-chen.md
├── projects/
├── ideas/
├── admin/
└── _inbox/          # Low-confidence items
```

Each file has YAML frontmatter:

```yaml
---
id: 20260303-143022-abc123
type: person
title: Alice Chen
tags: [client, design]
confidence: 0.87
captured: 2026-03-03T14:30:22
---

Met Alice at the design conference...
```

---

## License

MIT

---

<p align="center">
  <sub>Built for humans who think faster than they can organize.</sub>
</p>
