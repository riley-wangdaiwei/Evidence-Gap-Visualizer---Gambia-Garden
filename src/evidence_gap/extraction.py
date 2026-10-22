"""Optional extraction; suggestions are never automatically approved."""
import os
def llm_configuration():
    return {"provider":os.getenv("LLM_PROVIDER"),"model":os.getenv("LLM_MODEL"),"enabled":bool(os.getenv("LLM_PROVIDER") and os.getenv("LLM_MODEL") and os.getenv("LLM_API_KEY"))}
def require_review(claim):
    claim["review_status"]="AI_SUGGESTED"
    return claim
