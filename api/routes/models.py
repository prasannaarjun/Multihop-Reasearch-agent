import os
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    available_models,
    current_model,
    load_available_models,
    set_current_model,
)
from api.schemas import ModelChangeRequest
from auth import get_current_active_user, get_current_admin_user, TokenData


router = APIRouter()


@router.get("/models")
async def get_available_models(current_user: TokenData = Depends(get_current_active_user)):
    try:
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        if not use_ollama:
            return {
                "models": [],
                "ollama_enabled": False,
                "message": "Ollama is not enabled. Set USE_OLLAMA=true to enable model listing.",
            }

        if not available_models:
            load_available_models()

        return {
            "models": available_models,
            "ollama_enabled": True,
            "ollama_available": len(available_models) > 0,
            "current_model": current_model,
            "total_models": len(available_models),
        }
    except Exception as e:
        return {
            "models": [],
            "ollama_enabled": True,
            "ollama_available": False,
            "error": f"Error listing models: {str(e)}",
        }


@router.post("/models/change")
async def change_model(
    request: ModelChangeRequest, current_user: TokenData = Depends(get_current_active_user)
):
    try:
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        if not use_ollama:
            raise HTTPException(
                status_code=400,
                detail="Ollama is not enabled. Set USE_OLLAMA=true to enable model changes.",
            )

        if not available_models:
            load_available_models()

        model_exists = any(model["name"] == request.model_name for model in available_models)
        if not model_exists:
            available_model_names = [model["name"] for model in available_models]
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model_name}' not found. Available models: {available_model_names}",
            )

        success = set_current_model(request.model_name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set the new model")

        return {
            "message": f"Model successfully changed to '{request.model_name}'",
            "new_model": request.model_name,
            "restart_required": False,
        }
    except HTTPException:
        raise
    except Exception:
        # Redact internal error details to avoid leaking sensitive info
        raise HTTPException(status_code=500, detail="Error changing model")


