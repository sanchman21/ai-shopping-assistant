from fastapi import APIRouter

from backend.schemas.choices import ChoicesResponse
from backend.services.choices import get_supported_product_categories

choices_router = APIRouter(prefix="/choices", tags=["choices"])


@choices_router.get("/openai-models", response_model=ChoicesResponse)
async def get_openai_model_choices() -> ChoicesResponse:
    """
    Returns a list of available OpenAI model choices.
    """
    supported_openai_models = ["gpt-4o-2024-05-13", "gpt-4o-mini-2024-07-18"]
    return ChoicesResponse(choices=supported_openai_models)


@choices_router.get("/categories", response_model=ChoicesResponse)
async def get_product_categories() -> ChoicesResponse:
    return ChoicesResponse(choices=get_supported_product_categories())
