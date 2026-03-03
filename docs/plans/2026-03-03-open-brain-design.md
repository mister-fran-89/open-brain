# Open Brain - Technical Design Document

**Date:** 2026-03-03
**Status:** Approved
**Author:** Claude + Francesco

---

## Overview

Open Brain is a personal knowledge capture and retrieval system that transforms unstructured input (text, voice) into organized, queryable knowledge stored as Obsidian-compatible markdown files.

## Infrastructure Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Host | Proxmox LXC | Lightweight, easy snapshots, sufficient for workload |
| OS | Debian 12 | Stable, lean, excellent Docker support |
| Containerization | Docker Compose | Simple orchestration, portable, easy updates |
| Storage Location | NAS-mounted volume | Separate from compute, shared access for Obsidian |

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROXMOX LXC (Debian 12)                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Docker Compose Stack                         │  │
│  │                                                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │  open-brain │  │   whisper   │  │       chromadb          │   │  │
│  │  │   (FastAPI) │  │  (faster-   │  │    (vector store)       │   │  │
│  │  │   :8000     │  │   whisper)  │  │       :8001             │   │  │
│  │  └──────┬──────┘  └─────────────┘  └─────────────────────────┘   │  │
│  │         │                                                         │  │
│  │  ┌──────┴──────────────────────────────────────────────────────┐ │  │
│  │  │                    Shared Volumes                            │ │  │
│  │  │  /vault (NAS) ──► Obsidian markdown + SQLite index          │ │  │
│  │  │  /config      ──► .env, schedules, category schemas         │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌─────────┐    ┌──────────┐    ┌──────────┐
              │Telegram │    │   n8n    │    │  Email   │
              │   Bot   │    │ Webhooks │    │  SMTP    │
              └─────────┘    └──────────┘    └──────────┘
```

### Containers

| Container | Image | Purpose | Port |
|-----------|-------|---------|------|
| open-brain | Custom (Python 3.11) | Core API, classification, RAG, digests | 8000 |
| whisper | fedirz/faster-whisper-server | Voice transcription (OpenVINO) | 8001 |
| chromadb | chromadb/chroma | Vector embeddings for RAG | 8002 |

## Data Flow

### Capture Flow

```
Input (text/voice/webhook)
       │
       ▼
┌─────────────────┐
│  /api/capture   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Voice?  │──Yes──► Whisper ──► Text
    └────┬────┘
         │ No (or transcribed)
         ▼
┌─────────────────┐
│   Classifier    │──► AI Provider (local/cloud)
│  (category +    │
│   metadata)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│              Write to Vault             │
│  1. Markdown file with YAML frontmatter │
│  2. SQLite index (metadata, full-text)  │
│  3. Vector embedding (ChromaDB)         │
└─────────────────────────────────────────┘
```

### Query Flow (RAG)

```
Question
    │
    ▼
┌──────────────────┐
│ Embed question   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Vector search    │──► Top-k relevant chunks
│ (ChromaDB)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Retrieve full    │──► Read markdown files
│ context          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LLM generates    │──► Answer with citations
│ answer           │
└──────────────────┘
```

## Storage Design

### Vault Structure

```
/vault (NAS mount, Obsidian vault)
├── people/
│   └── alice-chen.md
├── projects/
│   └── website-redesign.md
├── ideas/
│   └── automation-concept.md
├── admin/
│   └── dentist-appointment.md
├── _inbox/              # Low-confidence items for review
├── _index/
│   ├── brain.db         # SQLite (metadata + FTS)
│   └── chroma/          # Vector embeddings
└── .obsidian/           # Obsidian config (untouched)
```

### File Format

```markdown
---
id: 20260303-143022-a1b2c3
type: person
name: Alice Chen
organization: Acme Corp
tags: [client, design]
confidence: 0.87
captured: 2026-03-03T14:30:22
source: telegram
---

Met Alice at the design conference. She's leading their rebrand project.
Interested in collaborating on the new logo system.

Follow up next week about proposal.
```

### Category Schemas

**People:**
- name, organization, relationship
- last_interaction, follow_ups
- tags, notes

**Projects:**
- name, status (active|waiting|blocked|someday|done)
- next_action, due_date
- tags, notes

**Ideas:**
- title, summary
- related_concepts
- tags, notes

**Admin:**
- task, due_date
- status (todo|done)
- tags, notes

## API Design

### Endpoints

```
CAPTURE
  POST /api/capture        ← text or structured input
  POST /api/capture/voice  ← audio file → Whisper → classify

QUERY
  POST /api/query          ← natural language question (RAG)
  GET  /api/search         ← structured search with filters

DIGEST
  POST /api/digest         ← generate on-demand
  GET  /api/digest/latest  ← retrieve most recent

CURATION
  GET    /api/items/{id}
  PATCH  /api/items/{id}   ← edit, reclassify
  DELETE /api/items/{id}

HEALTH
  GET  /api/health         ← status for monitoring
```

### Adapters

| Channel | Direction | Implementation |
|---------|-----------|----------------|
| CLI | In/Out | Python CLI (`brain capture`, `brain query`) |
| Telegram | In/Out | Bot with webhooks, sends digests |
| Slack | In/Out | Slash commands, webhook notifications |
| Email | In/Out | IMAP polling (via n8n), SMTP for digests |
| n8n | In/Out | HTTP webhooks both directions |
| OpenWebUI | In | Custom tool calling `/api/query` |
| Voice | In | Audio files → Whisper container |

## AI Provider Abstraction

### Interface

```python
class AIProvider(ABC):
    @abstractmethod
    def classify(self, text: str) -> ClassificationResult: ...

    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def query(self, question: str, context: list[str]) -> str: ...

    @abstractmethod
    def summarize(self, items: list[Item]) -> str: ...
```

### Implementations

- OllamaProvider (local, default)
- GeminiProvider
- OpenAIProvider
- ClaudeProvider
- OpenVINOProvider (Intel-optimized local)

### Configuration

```yaml
ai:
  default_provider: ollama

  # Per-task override
  classify: ollama      # Fast, local
  embed: ollama         # Local embeddings
  query: gemini         # Complex RAG
  summarize: gemini     # Digest generation

  # Fallback chain
  fallback: [ollama, gemini, openai]
```

### Recommended Models (Intel iGPU)

| Task | Local Model | Cloud Fallback |
|------|-------------|----------------|
| Classify | Phi-3-mini, Qwen2-1.5B | Gemini Flash |
| Embed | nomic-embed-text | text-embedding-3-small |
| Query/RAG | Qwen2-7B | Gemini Pro |
| Summarize | Qwen2-7B | Gemini Pro |

## Deployment

### Repository Structure

```
open-brain/
├── docker-compose.yml
├── Dockerfile
├── setup.sh
├── .env.example
│
├── src/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── ai/
│   ├── storage/
│   ├── adapters/
│   └── config/
│
├── cli/
│   └── brain.py
│
├── config/
│   ├── categories.yaml
│   ├── prompts/
│   └── schedules.yaml
│
└── docs/
    └── plans/
```

### Environment Variables

```bash
# Storage
VAULT_PATH=/vault
DATA_PATH=/data

# AI Providers
OLLAMA_HOST=http://localhost:11434
GEMINI_API_KEY=
OPENAI_API_KEY=

# Integrations
TELEGRAM_BOT_TOKEN=
SLACK_WEBHOOK_URL=
SMTP_HOST=
SMTP_USER=
SMTP_PASS=
EMAIL_TO=

# Whisper
WHISPER_MODEL=base
```

### Bootstrap Process

```bash
# 1. Fresh Debian 12 LXC on Proxmox
# 2. Bootstrap:
curl -fsSL https://raw.githubusercontent.com/you/open-brain/main/setup.sh | bash

# 3. Configure:
cd /opt/open-brain
nano .env

# 4. Mount NAS:
# Add to /etc/fstab: //nas/vault /vault cifs credentials=/etc/nas-creds,uid=1000 0 0
mount -a

# 5. Start:
docker compose up -d

# 6. Verify:
brain capture "Test thought"
brain query "What did I just capture?"
```

## Digest System

### Schedule

- **Daily:** 8:00 AM - yesterday's captures, today's follow-ups
- **Weekly:** Monday 8:00 AM - week review, patterns, upcoming items

### Delivery Channels

Configurable in `.env`:
- Email (SMTP)
- Telegram (bot message)
- Slack (webhook)
- n8n (trigger workflow)

## Security Considerations

- Single-user system, no authentication layer
- Private network deployment
- API keys stored in `.env` (not committed)
- NAS credentials in `/etc/nas-creds` with restricted permissions

## Performance Targets

| Operation | Target |
|-----------|--------|
| Capture (text) | < 3 seconds |
| Capture (voice) | < 10 seconds |
| Query (RAG) | < 10 seconds |
| Digest generation | < 30 seconds |

## Future Enhancements

- Smart connections (auto-linking related items)
- Proactive surfacing (pre-meeting briefs)
- Mobile capture app
- Multi-device sync
- Team/shared vaults

---

*This design document serves as the authoritative reference for Open Brain implementation.*
