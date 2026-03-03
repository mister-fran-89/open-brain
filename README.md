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

# Start services
docker compose up -d

# Pull an LLM model
docker exec ollama ollama pull phi3:mini

# Capture your first thought
curl -X POST http://localhost:8000/api/capture \
  -H "Content-Type: application/json" \
  -d '{"text": "Met Alice Chen from Acme Corp today"}'
```

---

## Features

| | |
|---|---|
| **Capture** | Text, voice, webhooks — classify and store automatically |
| **Query** | Natural language questions with RAG-powered answers |
| **Search** | Full-text search + category/tag filters |
| **Digest** | Daily and weekly summaries delivered anywhere |
| **Storage** | Obsidian-compatible markdown — you own your data |
| **AI** | Pluggable providers (Ollama, Gemini, OpenAI, Claude) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │ Open Brain  │ │   Whisper   │ │      ChromaDB       ││
│  │   FastAPI   │ │  (voice)    │ │   (vectors/RAG)     ││
│  │   :8000     │ │   :8001     │ │      :8002          ││
│  └──────┬──────┘ └─────────────┘ └─────────────────────┘│
│         │                                                │
│  ┌──────┴──────────────────────────────────────────────┐│
│  │              Ollama (local LLM) :11434              ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     ┌────────────┐              ┌────────────┐
     │  /vault    │              │   /data    │
     │ (markdown) │              │  (sqlite)  │
     └────────────┘              └────────────┘
```

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
nano .env  # Add your API keys

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
VAULT_PATH=/vault              # Where markdown files live
OLLAMA_HOST=http://ollama:11434
AI_CLASSIFY_PROVIDER=ollama    # ollama | gemini | openai
GEMINI_API_KEY=                # If using Gemini
```

See [.env.example](.env.example) for all options.

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
