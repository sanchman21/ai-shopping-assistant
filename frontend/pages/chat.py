import os
import streamlit as st
from dotenv import load_dotenv
from frontend.utils.chat import (
    get_openai_model_choices,
    get_categories,
    search_initial,
    search_product_listings,
    fetch_chat_sessions,
    process_selected_chat_session,
)

load_dotenv()

def preprocess_products(raw_products):
    """
    Preprocess and validate the product list to ensure all necessary fields are present.
    """
    processed_products = []
    for product in raw_products:
        processed_products.append({
            "title": product.get("title", "Product title unavailable"),
            "price": product.get("price", "Price unavailable"),
            "product_url": product.get("product_url", "#"),
            "merchant_name": product.get("merchant_name", "Merchant unavailable"),
        })
    return processed_products

def create_cards(product_list, title="Recommended Products"):
    """
    Create HTML cards for the product list with an optional title.
    """
    if not product_list:
        return "<p>No products found.</p>"

    all_rows_html = f"<h3>{title}</h3>"
    cards_per_row = 4
    for i in range(0, len(product_list), cards_per_row):
        row_items = product_list[i: i + cards_per_row]
        row_html = '<div style="display: flex; gap: 10px; margin-bottom: 10px;">'
        for item in row_items:
            # Extract product details safely with fallback values
            title = item.get("title", "Product title unavailable")
            price = item.get("price", "Price unavailable")
            product_url = item.get("product_url", "#")
            merchant_name = item.get("merchant_name", "Merchant unavailable")

            # Create card HTML
            card_html = f"""
            <div style="
                flex: 1;
                background-color: #f0f0f0;
                border-radius: 8px;
                padding: 15px;
                min-width: 150px;
            ">
                <p style="font-weight: bold; margin-bottom: 5px; color: #333;">{merchant_name}</p>
                <p style="color: #d9534f; font-size: 1.1em; margin: 0;">{price}</p>
                <p style="font-size: 0.9em; color: #333;">{title}</p>
                <a href="{product_url}" target="_blank" style="color: #0275d8; text-decoration: none; font-size: 0.9em;">
                    View Product
                </a>
            </div>"""
            row_html += card_html
        row_html += "</div>"
        all_rows_html += row_html

    return all_rows_html

def qa_interface():
    st.title("Search Interface")

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
    if "recommended_products" not in st.session_state:
        st.session_state.recommended_products = []
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = None

    # Fetch models/categories
    models = get_openai_model_choices() or ["gpt-3.5-turbo"]
    categories = get_categories() or ["general"]

    # Sidebar
    with st.sidebar:
        st.title("🔧 Settings")
        model = st.selectbox("Model", models)
        category = st.selectbox("Category", categories)
        selected_chat_session = st.selectbox(
            "Chat Session", options=["New Chat"] + fetch_chat_sessions()
        )
        if selected_chat_session:
            st.session_state.chat_session_id = process_selected_chat_session(selected_chat_session)

        if st.button("Clear Chat"):
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Hello! How can I help you today?"}
            ]
            st.session_state.recommended_products = []
            st.rerun()

    # Main chat container
    chat_container = st.container()

    # Handle user input
    prompt = st.chat_input("Enter your prompt:")

    # Display chat history and process new input
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt:
            # Add user prompt to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Perform initial search for every prompt
            with st.spinner("Searching for recommendations..."):
                try:
                    response = search_initial(model, prompt, category, selected_chat_session, st.session_state.chat_history)

                    if isinstance(response, dict):
                        rag_output = response.get("response", {})
                        products = rag_output.get("products", [])
                        reasoning_summary = rag_output.get("reasoning_summary", "")

                        # Handle empty or malformed product recommendations
                        if not products:
                            st.warning("No products found in initial search. Fetching direct product listings.")
                        else:
                            # Preprocess RAG products
                            processed_products = [
                                {
                                    "title": product.get("product_name", "Product title unavailable"),
                                    "price": "Price unavailable",
                                    "product_url": "#",
                                    "merchant_name": "Merchant unavailable",
                                    "reason": product.get("reason_for_recommendation", "No reason provided."),
                                }
                                for product in products
                            ]

                            st.session_state.recommended_products = processed_products

                            # Display recommendations
                            assistant_reply = "Based on the community discussions, here are some recommended products:\n\n"
                            for idx, product in enumerate(processed_products, start=1):
                                assistant_reply += (
                                    f"**{idx}. {product['title']}**\n"
                                    f"Reason: {product['reason']}\n"
                                    f"Price: {product['price']}\n"
                                    f"Merchant: {product['merchant_name']}\n\n"
                                )

                            if reasoning_summary:
                                assistant_reply += f"**Reasoning Summary:** {reasoning_summary}"

                            with st.chat_message("assistant"):
                                st.markdown(assistant_reply)
                            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

                            # Fetch product listings for each recommended product
                            for product in processed_products:
                                with st.spinner(f"Fetching product links for: {product['title']}..."):
                                    try:
                                        product_response = search_product_listings(product['title'])
                                        if isinstance(product_response, list) and product_response:
                                            additional_products = preprocess_products(product_response)
                                            card_markdown = create_cards(additional_products[:5], title=f"Product Listings for {product['title']}")
                                            st.markdown(card_markdown, unsafe_allow_html=True)
                                    except Exception as e:
                                        st.error(f"Error fetching products for {product['title']}: {e}")
                except Exception as e:
                    st.error(f"Error during initial search: {e}")

if __name__ == "__main__":
    qa_interface()
