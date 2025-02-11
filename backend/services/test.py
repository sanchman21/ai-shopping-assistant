# # backend.py
#
# import requests
# import os
# from dotenv import load_dotenv
#
# # Load environment variables from .env file
# load_dotenv()
#
# # Get Oxylabs credentials from environment variables
# USERNAME = os.getenv("OXYLABS_USERNAME")
# PASSWORD = os.getenv("OXYLABS_PASSWORD")
#
# def fetch_google_shopping_results(search_term):
#     """
#     Fetches Google Shopping search results for a given search term using Oxylabs API.
#
#     Args:
#         search_term (str): The search term to query.
#
#     Returns:
#         dict: The JSON response from the API.
#     """
#     payload = {
#         'source': 'google_shopping_search',
#         'domain': 'com',
#         'query': search_term,
#         'pages': 1,
#         'parse': True,
#     }
#
#     try:
#         response = requests.post(
#             'https://realtime.oxylabs.io/v1/queries',
#             auth=(USERNAME, PASSWORD),
#             json=payload,
#         )
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error invoking API: {e}")
#         return None
#
# def extract_product_details(api_response):
#     """
#     Extracts product details from the API response.
#
#     Args:
#         api_response (dict): The JSON response from the API.
#
#     Returns:
#         list: A list of dictionaries containing product details.
#     """
#     products = []
#     if not api_response or 'results' not in api_response:
#         print("Invalid API response.")
#         return products
#
#     for result in api_response['results']:
#         content = result.get('content', {})
#         organic_results = content.get('results', {}).get('organic', [])
#
#         for product in organic_results:
#             product_id = product.get('product_id', 'N/A')
#             title = product.get('title', 'N/A')
#             price = product.get('price_str', 'N/A')
#             merchant_info = product.get('merchant', {})
#             merchant_name = merchant_info.get('name', 'N/A')
#
#             # Construct product URL
#             product_url = f"https://www.google.com/shopping/product/{product_id}"
#
#             products.append({
#                 'title': title,
#                 'price': price,
#                 'product_url': product_url,
#                 'merchant_name': merchant_name,
#             })
#
#     return products
