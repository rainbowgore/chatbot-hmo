import os
from typing import List, Dict, Any
from openai import AzureOpenAI
from dotenv import load_dotenv
from ..models.user import UserProfile
from .embeddings import get_embeddings_service

load_dotenv()

class ChatService:
    def __init__(self):
        # Use same Azure OpenAI client as openai_client
        self.client = AzureOpenAI(
            api_key=os.getenv("AOAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        
    def generate_answer(self, 
                       query: str, 
                       user_profile: UserProfile, 
                       history: List[Dict] = None,
                       language: str | None = None) -> Dict[str, Any]:
        """Generate an answer using knowledge base and user context"""
        
        # Get embeddings service
        embeddings_service = get_embeddings_service()
        
        # Retrieve relevant context
        context, sources = embeddings_service.get_context_for_query(
            query=query,
            user_hmo=user_profile.hmo,
            user_tier=user_profile.membership_tier,
            max_context_length=2000
        )
        
        # Also get top 3 matches with scores for transparency (does not affect prompt)
        top_matches = embeddings_service.search_similar(
            query=query,
            user_hmo=user_profile.hmo,
            user_tier=user_profile.membership_tier,
            top_k=3
        )
        retrieved_chunks = []
        for chunk, score in top_matches:
            preview = (chunk.content or "").replace("\n", " ")[:120]
            retrieved_chunks.append({
                "score": float(score),
                "content_preview": preview
            })
        
        # Build conversation history context
        history_context = ""
        if history:
            recent_history = history[-3:]  # Last 3 exchanges
            history_parts = []
            for exchange in recent_history:
                if 'user' in exchange and 'assistant' in exchange:
                    history_parts.append(f"משתמש: {exchange['user']}")
                    history_parts.append(f"עוזר: {exchange['assistant']}")
            history_context = "\n".join(history_parts)
        
        # Create comprehensive prompt (respect requested language)
        prompt = self._build_chat_prompt(query, user_profile, context, history_context, language)
        
        try:
            # Generate response using Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful healthcare assistant for Israeli HMOs. Answer strictly in the requested language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            
            return {
                "status": "answered",
                "answer": answer,
                "sources": sources,
                "context_used": len(context) > 0,
                "retrieved_chunks": retrieved_chunks
            }
            
        except Exception as e:
            return {
                "status": "error",
                "answer": f"מצטער, אירעה שגיאה בעיבוד השאלה. / Sorry, an error occurred processing your question: {str(e)}",
                "sources": [],
                "context_used": False,
                "retrieved_chunks": []
            }
            
    def _build_chat_prompt(self, 
                          query: str, 
                          user_profile: UserProfile, 
                          context: str, 
                          history_context: str,
                          language: str | None = None) -> str:
        """Build comprehensive prompt for chat response"""
        
        # User profile summary
        profile_summary = f"""פרופיל משתמש:
- שם: {user_profile.first_name} {user_profile.last_name}
- קופת חולים: {user_profile.hmo or 'לא צוין'}
- דרגת חברות: {user_profile.membership_tier or 'לא צוין'}
- גיל: {user_profile.age or 'לא צוין'}"""

        # Determine target language
        lang = (language or "he").lower()
        if lang == "en":
            prompt = f"""You are an AI assistant for Israeli health funds. Answer strictly in English.

User profile:
- Name: {user_profile.first_name} {user_profile.last_name}
- HMO: {user_profile.hmo or 'Not specified'}
- Membership tier: {user_profile.membership_tier or 'Not specified'}
- Age: {user_profile.age or 'Not specified'}

Relevant knowledge:
{context if context else 'No relevant information found in the knowledge base'}

Recent conversation history:
{history_context if history_context else 'No previous history'}

User question:
{query}

Instructions:
1. Answer only in English.
2. If the user belongs to a specific HMO, focus on the relevant details for that HMO.
3. If there are differences between membership tiers, explain clearly.
4. If exact information is missing, say so and give general guidance.
5. Include phone numbers or links if available.

Answer:"""
        else:
            prompt = f"""אתה עוזר AI מומחה לקופות החולים בישראל. ענה אך ורק בעברית.

{profile_summary}

מידע רלוונטי מבסיס הידע:
{context if context else 'לא נמצא מידע רלוונטי בבסיס הידע'}

היסטוריית שיחה אחרונה:
{history_context if history_context else 'אין היסטוריית שיחה קודמת'}

שאלת המשתמש:
{query}

הנחיות:
1. ענה רק בעברית.
2. אם המשתמש שייך לקופת חולים מסוימת, התמקד במידע הרלוונטי לו.
3. אם יש הבדלים בין דרגות החברות, הסבר זאת בבירור.
4. אם אין מידע מדויק, אמור זאת בכנות ותן הנחיות כלליות.
5. כלול מספרי טלפון או קישורים אם זמינים.

תשובה:"""

        return prompt

# Global instance
chat_service = None

def get_chat_service() -> ChatService:
    """Get or create global chat service instance"""
    global chat_service
    if chat_service is None:
        chat_service = ChatService()
    return chat_service
