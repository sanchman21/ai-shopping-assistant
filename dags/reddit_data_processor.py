import os
import json
from datetime import datetime
import pandas as pd
import time
import numpy as np

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Additional imports
from pinecone import Pinecone, ServerlessSpec
import boto3
import psycopg2
from dotenv import load_dotenv

class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle NumPy arrays and other non-serializable types
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)

class RedditDataProcessor:
    def __init__(self):
        """
        Initialize the RedditDataProcessor with necessary configurations and clients
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT')
        self.pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
        
        # AWS S3 configuration
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_s3_bucket = os.getenv('AWS_S3_BUCKET')
        
        # PostgreSQL configuration
        self.db_host = os.getenv("POSTGRES_HOSTNAME")
        self.db_name = os.getenv("POSTGRES_DB")
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_port = os.getenv("POSTGRES_PORT")
        
        # Initialize clients
        self._init_s3_client()
        self._init_pinecone()
        self._init_embedding_model()
        
    def _init_s3_client(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
    
    def _init_pinecone(self):
        """Initialize Pinecone client and index"""
        pc = Pinecone(
            api_key=self.pinecone_api_key
        )

        # Check existing indexes
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

        if self.pinecone_index_name not in existing_indexes:
            pc.create_index(
                name=self.pinecone_index_name, 
                dimension=1536, 
                metric='euclidean',
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            while not pc.describe_index(self.pinecone_index_name).status["ready"]:
                time.sleep(1)

        self.pc_index = pc.Index(self.pinecone_index_name)
    
    def _init_embedding_model(self):
        """Initialize OpenAI embedding model"""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.openai_api_key,
            model='text-embedding-3-small'
        )
    
    
    def save_to_s3(self, content, filename):
        """
        Save content to S3 bucket
        
        Args:
            content (str): Content to save
            filename (str): Filename/key for S3 object
            
        Returns:
            str: S3 URL of saved object
        """
        try:
            # Use custom JSON encoder to handle non-serializable types
            serialized_content = json.dumps(content, cls=NumpyEncoder, default=str)
            
            self.s3_client.put_object(
                Bucket=self.aws_s3_bucket,
                Key=filename,
                Body=serialized_content.encode('utf-8'),
                ContentType='application/json'
            )
            return f"s3://{self.aws_s3_bucket}/{filename}"
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            raise

    def process_reddit_data(self, dataframe):
        """
        Process Reddit data by:
        1. Saving to S3
        2. Creating vector embeddings
        3. Storing in Pinecone with metadata in a specific namespace
        4. Inserting into PostgreSQL
        
        Args:
            dataframe (pd.DataFrame): DataFrame containing Reddit posts
        """
        # Explicitly set namespace
        namespace = 'headphones'
        
        # Timestamp for S3 and tracking
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process each post
        for _, row in dataframe.iterrows():
            try:
                # Convert row to dictionary with safe serialization
                row_dict = row.to_dict()
                
                # Safely handle comments and convert NumPy types
                if 'comments' in row_dict:
                    row_dict['comments'] = [
                        {k: (v.tolist() if isinstance(v, np.ndarray) else v) 
                         for k, v in comment.items()}
                        for comment in row_dict['comments']
                    ]
                
                # Combine title, body, and comments for embedding
                comments_text = " ".join([
                    f"Comment by {comment.get('author', 'Unknown')}: {comment.get('text', '')}" 
                    for comment in row_dict.get('comments', [])
                ])
                full_text = f"{row_dict['title']} {row_dict.get('body', '')} {comments_text}"
                
                # Save raw data to S3
                s3_key = f"reddit_posts/{timestamp}/{row_dict['id']}.json"
                s3_url = self.save_to_s3(row_dict, s3_key)

                vector_store = PineconeVectorStore(
                    index=self.pc_index, 
                    embedding=self.embeddings,
                    namespace=namespace
                )

                # Prepare metadata for Pinecone
                metadata = {
                    'id': row_dict['id'],
                    'title': row_dict['title'],
                    'body': row_dict.get('body', ''),
                    'author': row_dict['author'],
                    'subreddit': row_dict['subreddit'],
                    'score': row_dict['score'],
                    'created': str(row_dict['created']),
                    's3_url': s3_url,
                    'namespace': namespace,
                    'comments': json.dumps(row_dict.get('comments', []), cls=NumpyEncoder)
                }

                # Add text with metadata
                vector_store.add_texts(
                    texts=[full_text],
                    ids=[row_dict['id']],
                    metadatas=[metadata]
                )
                
                # Prepare post data for database
                post_data = {
                    'id': row_dict['id'],
                    'title': row_dict['title'],
                    'body': row_dict.get('body', ''),
                    'author': row_dict['author'],
                    'subreddit': row_dict['subreddit'],
                    'score': row_dict['score'],
                    'created': row_dict['created'],
                    's3_url': s3_url,
                    'vector_id': f"{namespace}_{row_dict['id']}",
                    'namespace': namespace,
                    'comments': row_dict.get('comments', [])
                }
                
                # Insert into database
                self.insert_reddit_article(post_data)
                
                print(f"Processed post in {namespace} namespace: {row_dict['title']}")
            
            except Exception as e:
                print(f"Error processing post: {e}")
                # Optionally, print full traceback for debugging
                import traceback
                traceback.print_exc()

    def insert_reddit_article(self, post_data):
        """
        Insert Reddit post data into PostgreSQL
        
        Args:
            post_data (dict): Dictionary containing post details
        
        Returns:
            bool: Success status of insertion
        """
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            
            cursor = conn.cursor()
            
            # Ensure table exists
            create_table_query = """
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                body TEXT,
                author TEXT,
                subreddit TEXT,
                score INTEGER,
                created_at TIMESTAMP,
                s3_url TEXT,
                vector_id TEXT,
                namespace TEXT,
                comments JSONB
            );
            """
            cursor.execute(create_table_query)
            
            # Insert or update post
            insert_query = """
            INSERT INTO reddit_posts 
            (id, title, body, author, subreddit, score, created_at, s3_url, vector_id, namespace, comments)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
            title = EXCLUDED.title,
            body = EXCLUDED.body,
            score = EXCLUDED.score,
            s3_url = EXCLUDED.s3_url,
            vector_id = EXCLUDED.vector_id,
            namespace = EXCLUDED.namespace,
            comments = EXCLUDED.comments;
            """
            
            # Use the custom JSON encoder to handle NumPy types
            comments_json = json.dumps(post_data.get('comments', []), cls=NumpyEncoder)
            
            cursor.execute(insert_query, (
                post_data.get('id', ''),
                post_data.get('title', ''),
                post_data.get('body', ''),
                post_data.get('author', ''),
                post_data.get('subreddit', ''),
                post_data.get('score', 0),
                post_data.get('created', datetime.now()),
                post_data.get('s3_url', ''),
                post_data.get('vector_id', ''),
                post_data.get('namespace', ''),
                comments_json
            ))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"Database insertion error: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                conn.close()