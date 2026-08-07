# 🧠 ThoughtLinker

> **Think. Link. Grow.**

ThoughtLinker is an AI-powered Personal Knowledge Management (PKM) system that helps users capture ideas, organize notes, discover semantic relationships, and transform unstructured thoughts into meaningful knowledge.

The application combines modern full-stack development with AI engineering techniques such as multi-model routing, semantic search, agentic guardrails, and LangGraph orchestration.

---

## ✨ Features

- 🔐 Secure user authentication
- 📝 Rich Text Note Editor
- 🧠 Brain Dump processing
- 🤖 AI-generated note suggestions
- 🏷️ Automatic tag generation
- 🔍 Semantic search using vector embeddings
- 🕸️ Knowledge Graph visualization
- 📂 Collections and note organization
- 📄 PDF / TXT / Markdown document import
- ⚡ Multi-model AI routing
- 🛡️ Agentic Guardrails
- 🔄 LangGraph workflow orchestration
- 📊 Model Routing Dashboard
- 🌗 Light / Dark / System themes
- 🚀 Live cloud deployment

---

# System Architecture

```text
                    User
                      │
                      ▼
             React + Vite Frontend
                  (Vercel)
                      │
                 REST APIs
                      │
                      ▼
              FastAPI Backend
                 (Railway)
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
 PostgreSQL       LangGraph       AI Routing
 + pgvector      Workflow Engine   (Small/Large)
     │                │
     └────────────┬───┘
                  ▼
          AI Suggestions
                  │
          Human Review
                  │
                  ▼
           Saved Knowledge
```

---

# Technology Stack

## Frontend

- React
- Vite
- React Router
- Tailwind CSS
- TipTap Rich Text Editor
- Axios

---

## Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic
- JWT Authentication

---

## Database

- PostgreSQL
- pgvector

---

## AI Stack

- LangGraph
- Sentence Transformers (all-MiniLM-L6-v2)
- Multi-Model Routing
- Agentic Guardrails
- Semantic Search

---

## Deployment

| Service | Platform |
|----------|----------|
| Frontend | Vercel |
| Backend | Railway |
| Database | PostgreSQL |
| Version Control | GitHub |

---

# Core Modules

## Authentication

- User Registration
- Login
- Forgot Password
- Reset Password
- Delete Account

---

## Brain Dump

Users can write unstructured thoughts or import documents.

The system automatically:

- analyzes the content
- generates a title
- creates AI suggestions
- extracts tags
- finds related notes
- identifies knowledge gaps

Suggestions are **never stored automatically**.

Users review, edit, accept, or reject every suggestion before it becomes a permanent note.

---

## Multi-Model Routing

ThoughtLinker intelligently selects the appropriate AI model for each request.

### Small Model

**llama-3.1-8b-instant**

Used for:

- Tag generation
- Simple summaries
- Keyword extraction
- Fast responses

---

### Large Model

**llama-3.3-70b-versatile**

Used for:

- Complex reasoning
- Ambiguous Brain Dumps
- Advanced AI suggestions

This routing strategy improves performance while reducing unnecessary AI costs.

---

## Agentic Guardrails

Every AI response passes through validation before reaching the database.

Guardrails verify:

- Output schema
- Related note IDs
- Tag limits
- Confidence thresholds
- Data integrity

Invalid AI responses are rejected and logged.

---

## Semantic Search

Instead of matching exact keywords, ThoughtLinker performs semantic search using vector embeddings.

This enables users to discover related notes based on meaning rather than exact wording.

---

## Knowledge Graph

The Knowledge Graph automatically visualizes relationships between notes.

This helps users explore connected ideas and discover hidden knowledge.

---

## LangGraph Workflow

Brain Dump processing follows an inspectable LangGraph workflow.

```text
Brain Dump
      │
Normalize
      │
Semantic Search
      │
Model Routing
      │
AI Suggestion
      │
Guardrails
      │
Knowledge Gap Detection
      │
Human Review
      │
Accept / Reject
      │
Saved Note
```

---

# REST APIs

Major API modules include:

```
/auth
/notes
/tags
/collections
/dashboard
/search
/brain-dumps
/suggestions
/model-calls
/knowledge-graph
/file-imports
```

---

# Project Structure

```text
frontend/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   └── assets/
│
backend/
│
├── routers/
├── models/
├── schemas/
├── services/
├── database/
├── core/
└── utils/
```

---

# Deployment

The application is deployed using a modern cloud architecture.

- Frontend hosted on **Vercel**
- Backend hosted on **Railway**
- PostgreSQL database
- Automatic deployment through GitHub

---

# Key Learning Outcomes

Throughout this project I gained practical experience in:

- Full Stack Development
- React Architecture
- FastAPI
- PostgreSQL
- pgvector
- REST API Development
- LangGraph
- Semantic Search
- AI Prompt Engineering
- Multi-Model Routing
- Agentic Guardrails
- MCP Integration
- JWT Authentication
- Cloud Deployment
- Git & GitHub Workflow

---

# Future Improvements

- Voice note support
- Mobile application
- Real-time collaboration
- Offline mode
- Advanced Retrieval-Augmented Generation (RAG)
- AI-powered knowledge recommendations

---

# Developer

**Uma E. Rubab**

AI & Full Stack Software Developer

---

# Mentor

**Usama Sadiq**

---

# License

This project was developed for educational and internship purposes.
