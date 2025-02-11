import pytest
from unittest.mock import patch, MagicMock
from backend.schemas.search import InitialSearchResponse
from backend.services.search import (
    process_initial_search_query,
    fetch_google_shopping_results,
    extract_product_details,
)

# Fixtures
@pytest.fixture
def mock_agent_workflow():
    with patch("backend.agent.agent_workflow.invoke", return_value={
        "generation": "Generated response",
        "steps": ["Step 1", "Step 2"],
        "perform_web_search": True,
    }) as mock:
        yield mock

@pytest.fixture
def google_shopping_response():
    return {
        "results": [
            {
                "content": {
                    "results": {
                        "organic": [
                            {
                                "product_id": "12345",
                                "title": "Test Product",
                                "price_str": "$99.99",
                                "merchant": {"name": "Test Merchant"},
                            }
                        ]
                    }
                }
            }
        ]
    }



# Test extract_product_details
def test_extract_product_details(google_shopping_response):
    products = extract_product_details(google_shopping_response)
    assert len(products) == 1
    assert products[0]["title"] == "Test Product"
    assert products[0]["price"] == "$99.99"
    assert products[0]["merchant_name"] == "Test Merchant"
    assert products[0]["product_url"] == "https://www.google.com/shopping/product/12345"

# Test extract_product_details with invalid response
def test_extract_product_details_invalid():
    products = extract_product_details({})
    assert products == []
