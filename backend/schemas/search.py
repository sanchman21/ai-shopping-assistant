from pydantic import BaseModel, field_validator

from backend.schemas.chain import SearchResult as LlmSearchResult
from backend.services.choices import get_supported_product_categories


class InitialSearchRequest(BaseModel):
    model: str
    prompt: str
    category: str
    chat_session_id: int | None

    # @field_validator('category')
    # @classmethod
    # def _cat_supported(cls, v: str) -> str:
    #     if v not in get_supported_product_categories():
    #         raise ValueError(f"{v} is not a supported product category.")
    #     return v


class InitialSearchResponse(BaseModel):
    chat_session_id: int
    response: LlmSearchResult
    tools_used: list[str]


class SearchQuery(BaseModel):
    query: str

class Product(BaseModel):
    title: str
    price: str
    product_url: str
    merchant_name: str
