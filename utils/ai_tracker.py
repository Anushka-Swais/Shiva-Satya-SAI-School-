from sqlalchemy.orm import Session
from models import AIUsageLog

def log_gemini_usage(
    db: Session,
    response,
    client_name: str,
    user_email: str,
    module_name: str,
    feature_name: str
):
    """
    Extracts token usage from a Gemini AI response and logs it to the PostgreSQL database.
    """
    prompt_tokens = 0
    completion_tokens = 0

    # Safely extract token counts from Gemini's usage_metadata
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
        completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

    total_tokens = prompt_tokens + completion_tokens

    # Create the database record mapped to your exact requirements
    new_log = AIUsageLog(
        client_name=client_name,
        user_email=user_email,
        module_name=module_name,
        feature_name=feature_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )

    # Save to PostgreSQL
    try:
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
    except Exception as e:
        print(f"⚠️ Failed to log AI usage to database: {e}")
        db.rollback()