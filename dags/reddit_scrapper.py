import os
import praw
import pandas as pd
import datetime as dt
from typing import List, Optional, Dict
from dotenv import load_dotenv
from praw.models import MoreComments
import concurrent.futures
from typing import List

class RedditScraper:
    """
    A comprehensive class for scraping Reddit subreddit data with flexible authentication.
    
    Supports authentication via:
    1. Environment variables
    2. Direct credential input
    3. JSON configuration file
    """

    def __init__(
        self, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None, 
        user_agent: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        load_env: bool = True
    ):
        """
        Initialize the Reddit Scraper with flexible authentication options.
        
        Args:
            client_id (str, optional): Reddit API client ID
            client_secret (str, optional): Reddit API client secret
            user_agent (str, optional): User agent string
            username (str, optional): Reddit username
            password (str, optional): Reddit password
            load_env (bool, optional): Whether to load environment variables. Defaults to True.
        """
        # Load environment variables if specified
        if load_env:
            load_dotenv()

        # Prioritize direct input over environment variables
        self.credentials = {
            'client_id': client_id or os.getenv('REDDIT_CLIENT_ID'),
            'client_secret': client_secret or os.getenv('REDDIT_CLIENT_SECRET'),
            'user_agent': user_agent or os.getenv('REDDIT_USER_AGENT', 'Reddit Scraper'),
            'username': username or os.getenv('REDDIT_USERNAME'),
            'password': password or os.getenv('REDDIT_PASSWORD')
        }

        # Authenticate Reddit instance
        self.reddit = self._authenticate()

    def _authenticate(self) -> praw.Reddit:
        """
        Authenticate with Reddit API using provided or environment credentials.
        
        Returns:
            praw.Reddit: Authenticated Reddit instance
        
        Raises:
            ValueError: If required credentials are missing
        """
        # Remove None values from credentials
        cleaned_credentials = {k: v for k, v in self.credentials.items() if v is not None}

        # Validate essential credentials
        required_keys = ['client_id', 'client_secret', 'user_agent']
        for key in required_keys:
            if key not in cleaned_credentials:
                raise ValueError(f"Missing essential Reddit API credential: {key.upper()}")

        try:
            return praw.Reddit(**cleaned_credentials)
        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")

    def scrape_subreddit(
        self,
        subreddit_name: str,
        sort_by: str = 'top',
        time_filter: str = 'year',
        limit: int = 1000,
        include_comments: bool = True,
        comments_limit: int = 25
    ) -> pd.DataFrame:
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Use generator methods to reduce memory consumption
            sorting_methods = {
                'top': subreddit.top(time_filter=time_filter, limit=limit),
                'hot': subreddit.hot(limit=limit),
                'new': subreddit.new(limit=limit),
                'rising': subreddit.rising(limit=limit)
            }
            
            posts = sorting_methods.get(sort_by.lower())
            if not posts:
                raise ValueError(f"Invalid sort method: {sort_by}")

            # Use list comprehension for faster data collection
            topics_data = [
                {
                    "title": submission.title,
                    "score": submission.score,
                    "id": submission.id,
                    "url": submission.url,
                    "comments_num": submission.num_comments,
                    "created": dt.datetime.fromtimestamp(submission.created),
                    "author": str(submission.author) if submission.author else "Deleted",
                    "body": submission.selftext or "No body text",
                    "subreddit": subreddit_name,
                    "comments": (
                        self._extract_comments(submission, comments_limit) 
                        if include_comments else []
                    )
                }
                for submission in posts
            ][:limit]  # Ensure we don't exceed limit

            df = pd.DataFrame(topics_data)
            print(f"Scraped {len(df)} posts from r/{subreddit_name}")
            return df

        except Exception as e:
            print(f"Error scraping {subreddit_name}: {e}")
            return pd.DataFrame()

    def _extract_comments(self, submission, comments_limit=5):
        """
        Efficiently extract comments with minimal overhead
        """
        try:
            # submission.comments.replace_more(limit=0)
            a = [
                {
                    'text': comment.body,
                    'score': comment.score,
                    'author': str(comment.author)
                }
                for comment in submission.comments[:comments_limit]
                if not isinstance(comment, MoreComments)
            ]
            # print(a)
            return a
        except Exception:
            return []


        
    def save_to_file(
        self,
        dataframe: pd.DataFrame,
        base_filename: str = 'reddit_data',
        output_dir: str = 'output',
        formats: List[str] = ['csv', 'json']
    ) -> None:
        """
        Enhanced file saving method with better error handling
        """
        if dataframe.empty:
            print("No data to save.")
            return

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Save to specified formats
            for fmt in formats:
                filename = os.path.join(output_dir, f'{base_filename}_{timestamp}.{fmt}')
                
                if fmt == 'csv':
                    dataframe.to_csv(filename, index=False)
                elif fmt == 'xlsx':
                    dataframe.to_excel(filename, index=False)
                elif fmt == 'json':
                    dataframe.to_json(filename, orient='records')
                
                print(f"Data saved to {fmt.upper()}: {filename}")

        except PermissionError:
            print("Permission denied. Unable to save files.")
        except Exception as e:
            print(f"Error saving files: {e}")

    def scrape_multiple_subreddits_concurrent(
        self,
        subreddits: List[str],
        sort_by: str = 'top',
        time_filter: str = 'year',
        limit: int = 5,
        max_workers: int = 4
    ) -> pd.DataFrame:
        """
        Scrape multiple subreddits concurrently
        
        Args:
            subreddits: List of subreddit names
            max_workers: Number of concurrent threads
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks for each subreddit
            future_to_subreddit = {
                executor.submit(
                    self.scrape_subreddit, 
                    subreddit_name=subreddit,
                    sort_by=sort_by,
                    time_filter=time_filter,
                    limit=limit
                ): subreddit 
                for subreddit in subreddits
            }
            
            # Collect results
            combined_data = []
            for future in concurrent.futures.as_completed(future_to_subreddit):
                subreddit = future_to_subreddit[future]
                try:
                    subreddit_data = future.result()
                    if not subreddit_data.empty:
                        combined_data.append(subreddit_data)
                except Exception as exc:
                    print(f'{subreddit} generated an exception: {exc}')
        
        return pd.concat(combined_data, ignore_index=True) if combined_data else pd.DataFrame()