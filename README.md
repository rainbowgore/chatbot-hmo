# Smart Health System - Healthcare Q&A with Profile Management

A complete bilingual (Hebrew/English) healthcare system featuring an AI-powered Q&A interface with personalized user profile collection. Built with FastAPI backend and Streamlit frontend.

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

```bash
# From the ha-part2 root directory
./start_system.sh
```

This script will:

- Install dependencies for both backend and frontend
- Start the backend on port 8001
- Start the frontend on port 8501
- Test the connection between them
- Show live logs from both services

### Option 2: Manual Startup

#### 1. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

#### 2. Start Frontend (in a new terminal)

```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🔗 Access Points

- **Frontend Application**: http://localhost:8501
- **Backend API**: http://127.0.0.1:8001
- **API Documentation**: http://127.0.0.1:8001/docs
- **Health Check**: http://127.0.0.1:8001/health

## 📋 System Features

### 🏥 Core Functionality

- **Bilingual Support**: Full Hebrew/English interface with RTL text handling
- **Three-Phase Workflow**: Language selection → Profile collection → Medical Q&A
- **AI-Powered Q&A**: Personalized healthcare answers based on user profile
- **Knowledge Base**: 120+ healthcare chunks across 6 service categories
- **Real-time Integration**: Seamless frontend-backend communication

### 🔧 Technical Features

- **Deterministic Profile Collection**: Sequential field collection (First name → Last name → ID → Gender → Age → HMO → Card → Tier → Confirmation)
- **Language-Aware Responses**: AI answers strictly in the user's selected language
- **Session Management**: Persistent user state across interactions
- **Debug Mode**: Developer tools for troubleshooting
- **Structured Logging**: JSON-formatted logs for monitoring
- **Health Monitoring**: System status checks and metrics

## 🌐 User Experience Flow

### Phase 1: Language Selection

- Choose between Hebrew (עברית) and English
- Clean, centered interface with flag icons

### Phase 2: Profile Collection

1. **Sequential Data Collection**: The system follows a strict order:

   - First name (שם פרטי)
   - Last name (שם משפחה)
   - ID number (תעודת זהות - 9 digits, validated)
   - Gender (מין - Male/Female, זכר/נקבה)
   - Age (גיל - 0-120 range)
   - HMO (קופת חולים - מכבי, כללית, מאוחדת, לאומית)
   - HMO card number (מספר כרטיס בקופה)
   - Membership tier (דרגת חברות - זהב, כסף, ארד)
   - Confirmation (Yes/כן or No/לא)

2. **Smart Features**:
   - Progress indicator showing completion percentage
   - Resume functionality if session is interrupted
   - Bilingual input support (e.g., "Maccabi" → "מכבי")
   - Real-time validation

### Phase 3: Medical Q&A

1. **Personalized Chat**: Ask healthcare questions in natural language
2. **Context-Aware Answers**: Responses filtered by your HMO and membership tier
3. **Source Attribution**: See which documents informed each answer
4. **Conversation History**: Persistent chat within your session

## 🔧 Configuration

### Backend Configuration

Create `.env` file in `backend/` directory:

```env
# Azure OpenAI (Required)
AOAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Optional Settings
USE_MOCK=false                  # Set to 'true' for testing without Azure OpenAI
DEBUG_RETRIEVAL=false          # Set to 'true' to see retrieval details in responses
USE_EXTRACTION=false           # Set to 'true' to enable LLM-based field extraction
```

### Frontend Configuration

The frontend automatically connects to `http://127.0.0.1:8001`. To customize:

Edit `frontend/config/settings.py`:

```python
BACKEND_BASE_URL = "http://your-backend-url:port"
```

### Knowledge Base Setup

Mind the `phase2_data/` directory contains these HTML files, they make up for this service's knowldge base:

- `alternative_services.html` (רפואה משלימה)
- `communication_clinic_services.html` (מרפאות תקשורת)
- `dentel_services.html` (מרפאות שיניים)
- `optometry_services.html` (אופטומטריה)
- `pragrency_services.html` (הריון)
- `workshops_services.html` (סדנאות בריאות)

## 🧪 Testing & Verification

### Connection Test

```bash
cd frontend
python3 test_connection.py
```

### API Examples

**Profile Collection:**

```bash
curl -X POST "http://127.0.0.1:8001/collect_user_info" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "David",
    "user_profile": {"first_name": "", "last_name": ""},
    "language": "en"
  }'
```

**Medical Chat:**

```bash
curl -X POST "http://127.0.0.1:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Does Maccabi cover dental cleaning?",
    "user_profile": {
      "hmo": "מכבי",
      "membership_tier": "זהב",
      "confirmed": true
    },
    "history": [],
    "language": "en"
  }'
```

## 🔍 Troubleshooting

### Common Issues

**Backend connection failed:**

- Verify backend is running: `curl http://127.0.0.1:8001/health`
- Check port 8001 availability: `lsof -i :8001`
- Review Azure OpenAI credentials in `.env`

### Debug Mode

Enable comprehensive debugging:

1. **Frontend**: Check "Debug" checkbox in header
2. **Backend**: Set `DEBUG_RETRIEVAL=true` in `.env`
3. **View**: API requests, responses, retrieval chunks, session state

### Health Monitoring

```bash
# System health
curl http://127.0.0.1:8001/health

# Knowledge base statistics
curl http://127.0.0.1:8001/kb_stats
```

## 📊 System Architecture

### Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py                 # API endpoints & CORS
│   ├── models/user.py          # Pydantic models
│   └── services/
│       ├── openai_client.py    # Deterministic profile collection
│       ├── chat.py             # Language-aware Q&A
│       ├── embeddings.py       # Vector search
│       ├── knowledge_base.py   # HTML parsing & chunking
│       └── validation.py       # Input validation
└── requirements.txt
```

### Frontend (Streamlit)

```
frontend/
├── streamlit_app.py            # Main entry point
├── components/
│   ├── language_selector.py   # Phase 0: Language choice
│   ├── profile_collector.py   # Phase 1: Profile collection
│   ├── chat_interface.py      # Phase 2: Medical Q&A
│   ├── session_manager.py     # State management
│   └── api_client.py           # Backend communication
├── utils/
│   ├── hebrew_support.py       # RTL text handling
│   ├── formatters.py           # UI formatting
│   └── validators.py           # Frontend validation
├── config/settings.py          # Configuration
└── assets/style.css            # Hebrew/RTL styling
```

## 📝 Getting Started

1. **Clone and start**: `./start_system.sh`
2. **Open browser**
3. **Select language**: Choose Hebrew or English
4. **Complete registration**: Follow the 9-step profile collection
5. **Ask questions**: Get personalized healthcare answers
6. **Enable debug mode**: See system internals (optional)