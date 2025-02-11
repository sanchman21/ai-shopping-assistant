from pydantic import BaseModel, Field


class ExtractedProduct(BaseModel):
    """Product details for each of the extract products"""
    product_name: str = Field(..., description="The name of the product extracted from the text")
    reason_for_recommendation: str = Field(..., description="The reasons for recommending this product")


class SearchResult(BaseModel):
    """Search result containing extracted products"""
    products: list[ExtractedProduct] = Field(..., description="List of extracted products")
    reasoning_summary: str = Field(..., description="A brief summary of how the LLM derived these suggestions")
