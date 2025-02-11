import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# Retrieve API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Ensure API keys are set
if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    raise ValueError("Google API Key or CSE ID is missing. Check your .env file.")

class ReviewSummarizer:
    def __init__(self):
        # Initialize Google Search API wrapper
        self.google_search_tool = GoogleSearchAPIWrapper(
            google_api_key=GOOGLE_API_KEY,
            google_cse_id=GOOGLE_CSE_ID
        )
        # Initialize ChatOpenAI for summarization
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.5)

    def google_search_reviews(self, product_query):
        """
        Perform Google Search to find reviews about the product.
        """
        search_query = f"{product_query} reviews"
        print(f"Performing Google Search for query: {search_query}")
        try:
            results = self.google_search_tool.run(search_query)
            print("Raw Google Search results:", results)

            if not results:
                print("No results returned from Google Search.")
                return []

            # Return raw text results split by newline for further processing
            return results.split('\n')
        except Exception as e:
            print(f"Error during Google Search: {e}")
            return []

    def summarize_reviews(self, reviews):
        """
        Summarize the fetched reviews using GPT chat model.
        """
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant who summarizes product reviews."},
                {"role": "user", "content": "Summarize the following reviews into key insights and opinions:\n\n" + "\n\n".join(reviews)}
            ]
            summary = self.llm(messages)
            return summary.content
        except Exception as e:
            print(f"Error during summarization: {e}")
            return "Failed to summarize reviews."

    def process_reviews(self, product_query):
        """
        Complete flow: Perform search and summarize.
        """
        # Step 1: Perform Google Search
        search_results = self.google_search_reviews(product_query)
        if not search_results:
            return "No results found from Google Search."

        print(f"Found {len(search_results)} results. Summarizing content...\n")

        # Step 2: Summarize the reviews
        summary = self.summarize_reviews(search_results)
        return summary

if __name__ == "__main__":
    # Initialize the summarizer
    summarizer = ReviewSummarizer()

    # Define the product query
    product_query = "Bose QC45 headphones"

    print(f"Starting review summarization for: {product_query}\n")
    try:
        # Process reviews and generate summary
        summary = summarizer.process_reviews(product_query)

        print("\nSummary of Reviews:\n")
        print(summary)
    except Exception as e:
        print(f"An error occurred: {e}")
