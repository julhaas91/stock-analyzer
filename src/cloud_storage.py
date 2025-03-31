"""
This module contains the CloudStorage class for caching data in Google Cloud Storage.
"""

from google.cloud import storage
from pathlib import Path
import pickle
from datetime import datetime, timedelta
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")

class CloudStorage:
    def __init__(self, bucket_name: str):
        """Initialize the Cloud Storage client with a bucket name."""
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def _get_blob(self, file_path: str) -> storage.Blob:
        """Get a blob from the bucket."""
        return self.bucket.blob(file_path)

    def _get_metadata_blob(self, file_path: str) -> storage.Blob:
        """Get the metadata blob for a file."""
        return self.bucket.blob(f"{file_path}_metadata")

    def delete_from_cache(self, file_path: str) -> None:
        """
        Delete a file and its metadata from the cache.
        
        Args:
            file_path: The path of the file to delete
        """
        # Delete the data file
        blob = self._get_blob(file_path)
        if blob.exists():
            blob.delete()
        
        # Delete the metadata file
        metadata_blob = self._get_metadata_blob(file_path)
        if metadata_blob.exists():
            metadata_blob.delete()

    def save_to_cache(self, data: any, file_path: str) -> None:
        """
        Save data to cache in Google Cloud Storage.
        
        Args:
            data: The data to cache
            file_path: The path where the data should be stored
        """
        # Save the data
        blob = self._get_blob(file_path)
        with blob.open("wb") as f:
            pickle.dump(data, f)

        # Save the metadata
        metadata_blob = self._get_metadata_blob(file_path)
        metadata = {"date": datetime.now()}
        with metadata_blob.open("wb") as f:
            pickle.dump(metadata, f)

    def load_from_cache(self, file_path: str, max_age_days: int = 1) -> any:
        """
        Load data from cache if it exists and is not expired.
        
        Args:
            file_path: The path to the cached data
            max_age_days: Maximum age of the cache in days
            
        Returns:
            The cached data if valid, None otherwise
        """
        blob = self._get_blob(file_path)
        metadata_blob = self._get_metadata_blob(file_path)

        if not blob.exists() or not metadata_blob.exists():
            return None

        # Check metadata for expiration
        with metadata_blob.open("rb") as f:
            metadata = pickle.load(f)
            cache_date = metadata["date"]

        # Check if cache is expired
        if datetime.now() - cache_date > timedelta(days=max_age_days):
            return None

        # Load the data
        with blob.open("rb") as f:
            return pickle.load(f)

    def save_csv_to_cache(self, df: any, file_path: str) -> None:
        """
        Save a DataFrame to cache as CSV in Google Cloud Storage.
        
        Args:
            df: The DataFrame to cache
            file_path: The path where the data should be stored
        """
        blob = self._get_blob(file_path)
        with blob.open("w") as f:
            df.to_csv(f, index=False)

    def load_csv_from_cache(self, file_path: str) -> any:
        """
        Load CSV data from cache if it exists.
        
        Args:
            file_path: The path to the cached CSV data
            
        Returns:
            The cached DataFrame if it exists, None otherwise
        """
        blob = self._get_blob(file_path)
        if not blob.exists():
            return None

        with blob.open("r") as f:
            return pd.read_csv(f)

# Initialize the Cloud Storage client with the bucket name from environment variable
cloud_storage = CloudStorage(BUCKET_NAME)
