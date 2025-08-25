from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import time
import os
from datetime import datetime
from app.models.user import UserProfile, ChatRequest, ChatResponse
from app.services.openai_client import get_next_question
from app.services.chat import get_chat_service
from app.services import validation

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="HMO Chatbot Service", version="1.4")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://127.0.0.1:3000"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global monitoring variables
startup_time = time.time()
chat_requests_served = 0

class UserInfoRequest(BaseModel):
    message: str
    user_profile: UserProfile = UserProfile()
    language: str = "he"  # Default to Hebrew

class ChatRequestExtended(BaseModel):
    message: str
    user_profile: UserProfile
    history: List[Dict[str, str]] = []
    language: str | None = None

@app.post("/collect_user_info")
async def collect_user_info(req: UserInfoRequest):
    """Collect and validate user profile information"""
    start_time = time.time()
    
    # Log request (non-sensitive fields only)
    logger.info(json.dumps({
        "endpoint": "/collect_user_info",
        "timestamp": datetime.now().isoformat(),
        "message_length": len(req.message),
        "profile_fields_provided": {
            "first_name": bool(req.user_profile.first_name),
            "last_name": bool(req.user_profile.last_name),
            "id_number": bool(req.user_profile.id_number),
            "hmo": req.user_profile.hmo or None,
            "membership_tier": req.user_profile.membership_tier or None,
            "confirmed": req.user_profile.confirmed
        }
    }))
    
    # Validate known fields if present
    if req.user_profile.id_number and not validation.validate_id_number(req.user_profile.id_number):
        error_response = {"status": "error", "message": "מספר זהות לא תקין / Invalid ID number"}
        logger.warning(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "validation_error",
            "error": "invalid_id_number",
            "processing_time": time.time() - start_time
        }))
        return error_response
        
    if req.user_profile.age and not validation.validate_age(req.user_profile.age):
        error_response = {"status": "error", "message": "גיל לא תקין / Invalid age"}
        logger.warning(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "validation_error",
            "error": "invalid_age",
            "processing_time": time.time() - start_time
        }))
        return error_response
        
    if req.user_profile.hmo and not validation.validate_hmo(req.user_profile.hmo):
        error_response = {"status": "error", "message": "קופת חולים לא תקינה / Invalid HMO"}
        logger.warning(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "validation_error",
            "error": "invalid_hmo",
            "hmo_provided": req.user_profile.hmo,
            "processing_time": time.time() - start_time
        }))
        return error_response
        
    if req.user_profile.membership_tier and not validation.validate_membership_tier(req.user_profile.membership_tier):
        error_response = {"status": "error", "message": "דרגת חברות לא תקינה / Invalid membership tier"}
        logger.warning(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "validation_error", 
            "error": "invalid_membership_tier",
            "tier_provided": req.user_profile.membership_tier,
            "processing_time": time.time() - start_time
        }))
        return error_response

    try:
        # Get next question from OpenAI
        question = get_next_question(req.user_profile, req.message, req.language)
        
        # Note: Field extraction is now handled within get_next_question() if enabled
        # This avoids duplicate extraction logic
        
        response = {
            "status": "in_progress",
            "next_question": question,
            "user_profile": req.user_profile.dict()
        }
        
        # Log successful response
        logger.info(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "processing_time": time.time() - start_time,
            "question_generated": bool(question)
        }))
        
        return response
        
    except Exception as e:
        logger.error(json.dumps({
            "endpoint": "/collect_user_info",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
            "processing_time": time.time() - start_time
        }))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat")
async def chat(req: ChatRequestExtended):
    """
    Answer user questions using the knowledge base and user profile context
    """
    global chat_requests_served
    chat_requests_served += 1
    start_time = time.time()
    
    # Log request (non-sensitive fields only)
    logger.info(json.dumps({
        "endpoint": "/chat",
        "timestamp": datetime.now().isoformat(),
        "message_length": len(req.message),
        "hmo": req.user_profile.hmo or None,
        "membership_tier": req.user_profile.membership_tier or None,
        "confirmed": req.user_profile.confirmed,
        "history_length": len(req.history),
        "request_count": chat_requests_served
    }))
    
    try:
        # Check if user profile is confirmed. If not, allow chat when all
        # required fields are present (backward-compatible behavior).
        if not req.user_profile.confirmed:
            profile = req.user_profile
            is_complete = all([
                bool(getattr(profile, 'first_name', None)),
                bool(getattr(profile, 'last_name', None)),
                bool(getattr(profile, 'id_number', None)),
                bool(getattr(profile, 'gender', None)),
                getattr(profile, 'age', None) is not None,
                bool(getattr(profile, 'hmo', None)),
                bool(getattr(profile, 'hmo_card_number', None)),
                bool(getattr(profile, 'membership_tier', None)),
            ])

            if is_complete:
                # Soft-confirm the profile to prevent blocking valid users
                req.user_profile.confirmed = True
            else:
                error_response = {
                    "status": "registration_required", 
                    "message": "Please complete your registration first using /collect_user_info."
                }
                logger.warning(json.dumps({
                    "endpoint": "/chat",
                    "timestamp": datetime.now().isoformat(),
                    "status": "registration_required",
                    "processing_time": time.time() - start_time
                }))
                return error_response
        
        # Validate user profile if provided
        if req.user_profile.hmo and not validation.validate_hmo(req.user_profile.hmo):
            error_response = {"status": "error", "message": "קופת חולים לא תקינה / Invalid HMO"}
            logger.warning(json.dumps({
                "endpoint": "/chat",
                "timestamp": datetime.now().isoformat(),
                "status": "validation_error",
                "error": "invalid_hmo",
                "hmo_provided": req.user_profile.hmo,
                "processing_time": time.time() - start_time
            }))
            return error_response
            
        if req.user_profile.membership_tier and not validation.validate_membership_tier(req.user_profile.membership_tier):
            error_response = {"status": "error", "message": "דרגת חברות לא תקינה / Invalid membership tier"}
            logger.warning(json.dumps({
                "endpoint": "/chat",
                "timestamp": datetime.now().isoformat(),
                "status": "validation_error",
                "error": "invalid_membership_tier",
                "tier_provided": req.user_profile.membership_tier,
                "processing_time": time.time() - start_time
            }))
            return error_response

        # Get chat service
        chat_service = get_chat_service()
        
        # Generate answer
        result = chat_service.generate_answer(
            query=req.message,
            user_profile=req.user_profile,
            history=req.history,
            language=req.language
        )
        
        # Check if no knowledge base match was found
        if not result.get("context_used", False) and not result.get("sources", []):
            no_match_response = {
                "status": "no_match",
                "message": "Sorry, I couldn't find relevant information in the knowledge base.",
                "sources": [],
                "user_profile_used": {
                    "hmo": req.user_profile.hmo,
                    "membership_tier": req.user_profile.membership_tier
                },
                "context_used": False
            }
            logger.info(json.dumps({
                "endpoint": "/chat",
                "timestamp": datetime.now().isoformat(),
                "status": "no_match",
                "processing_time": time.time() - start_time,
                "hmo": req.user_profile.hmo,
                "membership_tier": req.user_profile.membership_tier
            }))
            return no_match_response
        
        response = {
            "status": result["status"],
            "answer": result["answer"],
            "sources": result["sources"],
            "user_profile_used": {
                "hmo": req.user_profile.hmo,
                "membership_tier": req.user_profile.membership_tier
            },
            "context_used": result["context_used"]
        }
        
        # Add debug retrieval info if enabled
        debug_retrieval = os.getenv("DEBUG_RETRIEVAL", "false").lower() == "true"
        if debug_retrieval:
            response["retrieved_chunks"] = result.get("retrieved_chunks", [])
        
        # Log successful response
        logger.info(json.dumps({
            "endpoint": "/chat",
            "timestamp": datetime.now().isoformat(),
            "status": result["status"],
            "processing_time": time.time() - start_time,
            "sources": result["sources"],
            "hmo": req.user_profile.hmo,
            "membership_tier": req.user_profile.membership_tier,
            "context_used": result["context_used"]
        }))
        
        return response
        
    except Exception as e:
        logger.error(json.dumps({
            "endpoint": "/chat",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
            "processing_time": time.time() - start_time,
            "hmo": req.user_profile.hmo,
            "membership_tier": req.user_profile.membership_tier
        }))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint with uptime, metrics, and system status"""
    uptime_seconds = int(time.time() - startup_time)
    
    # Basic health checks
    health_status = "ok"
    checks = {
        "openai_credentials": False,
        "knowledge_base": False,
        "embeddings": False
    }
    
    try:
        # Check OpenAI credentials
        aoai_key = os.getenv("AOAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if aoai_key and aoai_endpoint:
            checks["openai_credentials"] = True
        
        # Check knowledge base and embeddings
        from app.services.embeddings import get_embeddings_service
        embeddings_service = get_embeddings_service()
        if len(embeddings_service.chunks) > 0:
            checks["knowledge_base"] = True
        if len(embeddings_service.chunk_embeddings) > 0:
            checks["embeddings"] = True
            
    except Exception as e:
        health_status = "degraded"
        logger.warning(f"Health check failed: {str(e)}")
    
    # Overall status
    if not all(checks.values()):
        health_status = "degraded"
    
    response = {
        "status": health_status,
        "uptime": uptime_seconds,
        "requests_served": chat_requests_served,
        "service": "HMO Chatbot Service",
        "version": "1.4",
        "checks": checks
    }
    
    # Log health check
    logger.info(json.dumps({
        "endpoint": "/health",
        "timestamp": datetime.now().isoformat(),
        "status": health_status,
        "uptime": uptime_seconds,
        "requests_served": chat_requests_served,
        "checks": checks
    }))
    
    return response

@app.get("/kb_stats")
async def knowledge_base_stats():
    """Get knowledge base statistics"""
    try:
        from app.services.embeddings import get_embeddings_service
        embeddings_service = get_embeddings_service()
        stats = embeddings_service.get_stats()
        return stats
    except Exception as e:
        return {"error": f"Could not load knowledge base stats: {str(e)}"}

# Optional eager init: uncomment to pre-warm embeddings on startup
# @app.on_event("startup")
# async def startup_event():
#     from app.services.embeddings import get_embeddings_service
#     get_embeddings_service()