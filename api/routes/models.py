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

        # Always load models fresh from Ollama instead of relying on global state
        import requests
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
            response.raise_for_status()
            ollama_data = response.json()
        except requests.exceptions.RequestException:
            return {
                "models": [],
                "ollama_enabled": True,
                "ollama_available": False,
                "current_model": None,
                "total_models": 0,
            }

        models = []
        for model in ollama_data.get("models", []):
            model_info = {
                "name": model.get("name", ""),
                "size": model.get("size", 0),
                "modified_at": model.get("modified_at", ""),
                "family": model.get("details", {}).get("family", ""),
                "format": model.get("details", {}).get("format", ""),
                "families": model.get("details", {}).get("families", []),
                "parameter_size": model.get("details", {}).get("parameter_size", ""),
                "quantization_level": model.get("details", {}).get("quantization_level", ""),
            }
            models.append(model_info)

        # Set current model if not set
        current_model_name = current_model if current_model else (models[0]["name"] if models else None)
        
        print(f"DEBUG: /models endpoint - current_model from global: '{current_model}', returning: '{current_model_name}'")

        return {
            "models": models,
            "ollama_enabled": True,
            "ollama_available": len(models) > 0,
            "current_model": current_model_name,
            "total_models": len(models),
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

        # Load models fresh from Ollama instead of relying on global state
        import requests
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
            response.raise_for_status()
            ollama_data = response.json()
        except requests.exceptions.RequestException:
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to Ollama. Make sure Ollama is running.",
            )

        # Extract model names
        available_model_names = [model.get("name", "") for model in ollama_data.get("models", [])]
        
        # Check if the requested model exists
        if request.model_name not in available_model_names:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model_name}' not found. Available models: {available_model_names}",
            )

        # Update the global current model
        print(f"DEBUG: Changing model to '{request.model_name}'")
        success = set_current_model(request.model_name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set the new model")

        print(f"DEBUG: Model successfully changed to '{request.model_name}'")
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


