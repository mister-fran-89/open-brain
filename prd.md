# Open Brain - Product Requirements Document

## Vision

Open Brain is a **personal knowledge capture and retrieval system** that eliminates the friction between having a thought and preserving it for future use. It transforms unstructured input (text, voice, any format) into organized, queryable knowledge that lives locally on your machine.

The system should feel like having a second brain that:
- Never forgets anything you tell it
- Organizes information without you deciding where it goes
- Answers questions about what you know
- Surfaces relevant information when you need it

---

## Problem Statement

Knowledge capture today is broken:

1. **Too much friction** - By the time you open an app, create a file, decide on a folder, and tag it properly, the thought is gone or the moment has passed.

2. **Organization paralysis** - "Where should this go?" is a question that kills momentum. People either over-organize (100 folders, never find anything) or under-organize (one giant note, chaos).

3. **Information silos** - Notes about people end up separate from projects they're connected to. Context is lost.

4. **Retrieval failure** - You know you wrote something down, but searching yields nothing. The information exists but is effectively lost.

5. **No intelligence layer** - Traditional note systems store exactly what you type. They don't understand, connect, or surface information proactively.

---

## Core Principles

### 1. Capture First, Organize Never

Users should dump information in any form. The system handles organization. The user's job is to capture; the system's job is to make it findable later.

### 2. AI as Infrastructure

AI is not a feature - it's the foundation. Classification, retrieval, summarization, and connection-making are all AI-powered by default.

### 3. Local-First, Privacy-Respecting

All data lives on the user's machine in human-readable formats. No cloud lock-in. No proprietary databases. Export is trivial because the storage format is standard markdown.

### 4. Confidence Over Certainty

The system should be transparent about what it knows vs. what it infers. When uncertain, flag for human review rather than silently miscategorize.

### 5. Progressive Enhancement

Start simple, grow with the user. Day one: capture and retrieve. Month one: patterns emerge. Year one: true second brain that knows your world.

---

## User Personas

### The Overwhelmed Professional
- Has 50+ browser tabs open
- Meets 10 people a week, forgets half their names
- Knows they wrote something down "somewhere"
- Needs: frictionless capture, reliable retrieval

### The Creative Collector
- Ideas come at random moments (shower, commute, 3am)
- Voice notes pile up unprocessed
- Connections between ideas exist but aren't explicit
- Needs: voice capture, idea linking, creative digests

### The Relationship Builder
- Networking is core to their work
- Struggles to remember context from past conversations
- Wants to follow up but loses track
- Needs: people-centric organization, follow-up surfacing

### The Project Juggler
- Multiple projects in various states
- Loses track of next actions
- Weekly reviews are painful (manual aggregation)
- Needs: project status tracking, automated summaries

---

## Functional Requirements

### Capture

**What it does:**
Accept any input and persist it intelligently.

**Input methods:**
- Text (typed, pasted, or programmatic)
- Voice (recorded and transcribed)
- Future: files, images, URLs, emails

**Behavior:**
- Input is analyzed and classified automatically
- Appropriate metadata is extracted and attached
- Content is stored in a retrievable format
- An audit trail records what was captured and how it was classified

**User experience:**
- Capture should take under 5 seconds
- User should not need to decide "where" something goes
- Feedback should show what the system understood

### Classification

**What it does:**
Determine what type of information was captured and extract relevant metadata.

**Categories (extensible):**
- **People** - Contacts, relationships, meeting notes, follow-ups
- **Projects** - Tasks, initiatives, things with next actions
- **Ideas** - Thoughts, concepts, creative sparks
- **Admin** - Appointments, reminders, administrative tasks

**Behavior:**
- Each category has a defined metadata schema
- Classification includes a confidence score
- Low-confidence items are flagged for review
- Users can reclassify at any time (learning opportunity)

**Metadata by type:**

People:
- Name, relationship context, organization
- Last interaction, follow-up items
- Tags, notes

Projects:
- Name, status (active, waiting, blocked, someday, done)
- Next physical action
- Due date, dependencies
- Tags, notes

Ideas:
- Title, one-liner summary
- Related concepts
- Tags, notes

Admin:
- Task name, due date
- Status (todo, done)
- Tags, notes

### Retrieval

**What it does:**
Answer questions about stored knowledge.

**Query types:**
- Natural language: "What do I know about Alice?"
- Structured: "Show me all active projects"
- Temporal: "What did I capture last week?"
- Semantic: "Find anything related to the logo redesign"

**Behavior:**
- Queries search across all stored knowledge
- Results include source attribution
- Answers synthesize information, not just list matches
- Related items may be surfaced proactively

### Digests

**What it does:**
Generate periodic summaries of captured knowledge.

**Digest types:**
- Daily: What was captured today, what needs attention
- Weekly: Review of the week, patterns, upcoming items
- Custom: User-defined time ranges or filters

**Behavior:**
- Digests are generated on-demand or scheduled
- Output is human-readable (markdown or similar)
- Actionable items are highlighted
- Digests can be stored as artifacts

### Curation

**What it does:**
Allow users to correct, refine, and enhance stored knowledge.

**Capabilities:**
- Reclassify: Move item to different category
- Edit: Modify name, metadata, or content
- Delete: Remove items
- Merge: Combine related items
- Link: Explicitly connect items

**Behavior:**
- All curation actions update the audit trail
- Reclassification can inform future classification
- Edits preserve history (optional versioning)

---

## Non-Functional Requirements

### Performance
- Capture response: < 3 seconds
- Query response: < 10 seconds (for vaults under 10k items)
- Digest generation: < 30 seconds

### Scalability
- Support 10,000+ items without degradation
- Efficient indexing for large vaults

### Reliability
- No data loss on crash or interruption
- Atomic writes (all-or-nothing file operations)
- Graceful degradation if AI services unavailable

### Privacy
- All data stored locally by default
- API keys provided by user (not shared)
- No telemetry or data collection without consent

### Portability
- Storage format: standard markdown with YAML frontmatter
- Compatible with Obsidian, Logseq, or any markdown editor
- Export: copy the folder, done

### Extensibility
- Categories can be added without code changes
- Classification prompts are configurable
- API enables third-party integrations

---

## Technical Considerations

### Storage Layer
The system needs a storage layer that:
- Reads and writes markdown with YAML frontmatter
- Supports folder-based organization
- Enables efficient search (text and metadata)
- Maintains an audit log of operations

### AI Layer
The system needs an AI layer that:
- Classifies unstructured text into categories
- Extracts structured metadata from text
- Answers natural language queries over stored knowledge
- Generates summaries from collections of items

### Interface Layer
The system needs interfaces that:
- Enable quick capture (web, CLI, mobile, API)
- Display classification results with confidence
- Support natural language queries
- Present digests in readable format

### Integration Layer
The system should support:
- Voice transcription services
- File import (various formats)
- Calendar/email integration (future)
- Webhook/API for automation

---

## Success Metrics

### Capture Friction
- Time from thought to captured: < 5 seconds
- Percentage of captures requiring manual organization: < 20%

### Retrieval Quality
- Query success rate (user found what they needed): > 90%
- Average queries before finding information: < 2

### Classification Accuracy
- Auto-classification accuracy: > 80%
- User reclassification rate: < 15%

### User Engagement
- Weekly active captures: > 10 per user
- Weekly query usage: > 5 per user
- Digest generation: > 1 per week

---

## Open Questions

### Category System
- Should categories be fixed or user-definable?
- How do items that span categories get handled?
- Should there be a hierarchy (subcategories)?

### Confidence Handling
- What threshold triggers manual review?
- Should confidence improve over time (learning)?
- How to handle consistently low-confidence input?

### Multi-Device
- How does sync work across devices?
- Conflict resolution strategy?
- Real-time or eventual consistency?

### Collaboration
- Is this always single-user?
- If shared, how are permissions handled?
- Can vaults be merged?

### AI Provider
- Single provider or pluggable?
- Offline/local model option?
- Cost management for heavy users?

### Retention
- Auto-archive old items?
- Explicit deletion vs. soft delete?
- Compliance considerations (GDPR)?

---

## Future Possibilities

### Smart Connections
Automatically link related items across categories. "This project involves these 3 people and relates to these 2 ideas."

### Proactive Surfacing
"You're meeting with Alice tomorrow. Here's what you captured about her last time."

### Pattern Recognition
"You tend to capture project ideas on Monday mornings. Your most productive capture day is Wednesday."

### External Sync
Bidirectional sync with calendar, email, task managers. Capture from anywhere, retrieve everywhere.

### Team Brain
Shared knowledge base with individual and team views. "What does the team know about this client?"

### Voice-First Interface
Conversational interaction. "What's on my plate this week?" spoken aloud, answered aloud.

### Mobile-Native Capture
Dedicated mobile app optimized for quick capture. Widget, share sheet, voice shortcut integration.

---

## Appendix: Inspiration Sources

This PRD draws inspiration from:
- **Getting Things Done (GTD)** - Capture everything, decide later
- **Zettelkasten** - Atomic notes, emergent connections
- **Obsidian/Roam** - Local-first, markdown-based knowledge
- **Notion AI** - AI-augmented knowledge work
- **PARA Method** - Projects, Areas, Resources, Archives
- **Building a Second Brain** - Progressive summarization, actionable knowledge

---

*This document describes what Open Brain should be, not how it should be built. Implementation decisions (language, framework, architecture) are intentionally left open to enable the best solution for the requirements.*
