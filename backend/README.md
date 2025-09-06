# HMO Chatbot Service

A production-ready FastAPI microservice for Israeli health fund (HMO) customer support, featuring:

- User profile collection with validation
- RAG-powered Q&A using Azure OpenAI embeddings
- Knowledge base from 6 health service categories
- Structured logging and monitoring
- Bilingual Hebrew/English responses

## Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI application & endpoints
│   ├── models/user.py          # Pydantic models
│   └── services/
│       ├── openai_client.py    # Azure OpenAI integration
│       ├── chat.py             # RAG chat service
│       ├── embeddings.py       # Vector embeddings & search
│       ├── knowledge_base.py   # HTML parsing & chunking
│       └── validation.py       # Input validation
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## Environment Setup

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Azure OpenAI Configuration (Required)
AOAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Optional Configuration
USE_MOCK=false                  # Set to 'true' for local testing without Azure OpenAI
DEBUG_RETRIEVAL=false          # Set to 'true' to include retrieval scores in /chat responses
```

### Installation

1. **Install dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Verify knowledge base files exist:**
   ```bash
   ls ../phase2_data/
   # Should show: alternative_services.html, communication_clinic_services.html,
   # dentel_services.html, optometry_services.html, pragrency_services.html, workshops_services.html
   ```

## Running the Service

### Local Development

```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

### Production

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The service will be available at:

- **API**: `http://127.0.0.1:8001`
- **Swagger UI**: `http://127.0.0.1:8001/docs`
- **Health Check**: `http://127.0.0.1:8001/health`

## API Endpoints

### Core Endpoints

| Endpoint             | Method | Purpose                                |
| -------------------- | ------ | -------------------------------------- |
| `/collect_user_info` | POST   | User registration & profile collection |
| `/chat`              | POST   | RAG-powered Q&A with knowledge base    |
| `/health`            | GET    | Service health & system status         |
| `/kb_stats`          | GET    | Knowledge base statistics              |

### Testing in Swagger

Visit `http://127.0.0.1:8001/docs` for interactive API documentation.

**Example /chat request:**

```json
{
  "message": "Does Maccabi cover dental cleaning?",
  "user_profile": {
    "hmo": "מכבי",
    "membership_tier": "זהב",
    "confirmed": true
  },
  "history": []
}
```

**Example response:**

```json
{
  "status": "answered",
  "answer": "כן, מכבי מכסה ניקוי שיניים...",
  "sources": ["dentel_services.html"],
  "user_profile_used": {
    "hmo": "מכבי",
    "membership_tier": "זהב"
  },
  "context_used": true
}
```

### Testing with cURL

**Health check:**

```bash
curl http://127.0.0.1:8001/health
```

**Chat query:**

```bash
curl -X POST "http://127.0.0.1:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What pregnancy services are available?",
    "user_profile": {"hmo": "כללית", "membership_tier": "כסף", "confirmed": true},
    "history": []
  }'
```

## Features

### Knowledge Base

- **120 chunks** across 6 health service categories
- **Vector embeddings** using Azure OpenAI text-embedding-ada-002
- **Profile-aware filtering** by HMO and membership tier
- **Semantic search** with cosine similarity

### User Profile Collection

- **Progressive questioning** using Azure OpenAI
- **Input validation** for Israeli ID numbers, HMOs, membership tiers
- **Bilingual prompts** (Hebrew/English)
- **Mock mode** for local testing without API calls

### Production Features

- **Structured JSON logging** for all requests/responses
- **Request monitoring** with counters and timing
- **Health checks** with system status verification
- **Error handling** with structured responses
- **Debug mode** for retrieval transparency

## Monitoring

### Logs

All logs are in structured JSON format:

```json
{
  "endpoint": "/chat",
  "timestamp": "2024-01-15T10:30:00",
  "status": "answered",
  "processing_time": 1.23,
  "sources": ["dentel_services.html"],
  "hmo": "מכבי",
  "membership_tier": "זהב"
}
```

### Health Monitoring

```bash
curl http://127.0.0.1:8001/health
```

Returns:

```json
{
  "status": "ok",
  "uptime": 3600,
  "requests_served": 42,
  "service": "HMO Chatbot Service",
  "version": "1.4",
  "checks": {
    "openai_credentials": true,
    "knowledge_base": true,
    "embeddings": true
  }
}
```

## Development

### Testing Knowledge Base

```bash
python test_kb.py "dental cleaning"
python test_kb.py "pregnancy services"
```

### Mock Mode

Set `USE_MOCK=true` in `.env` to test without Azure OpenAI:

- Deterministic responses for profile collection
- No embedding generation (uses zero vectors)
- Faster local development

### Debug Mode

Set `DEBUG_RETRIEVAL=true` to see retrieval details:

```json
{
  "retrieved_chunks": [
    { "score": 0.795, "content_preview": "הריון תקופת ההריון..." },
    { "score": 0.786, "content_preview": "הריון - מידע ליצירת קשר..." }
  ]
}
```

## Troubleshooting

### Common Issues

1. **"No module named 'app'"**

   - Run `uvicorn` from the `backend/` directory
   - Verify you're in the correct working directory

2. **"ModuleNotFoundError: No module named 'openai'"**

   - Install dependencies: `pip install -r requirements.txt`

3. **Health check shows "degraded"**

   - Verify `.env` file has correct Azure OpenAI credentials
   - Check that `phase2_data/` directory exists with HTML files

4. **No knowledge base matches**
   - Ensure embedding generation completed successfully
   - Check logs for embedding service initialization errors

### Support

- View logs for detailed error information
- Use `/health` endpoint to verify system status
- Test with mock mode (`USE_MOCK=true`) to isolate issues
