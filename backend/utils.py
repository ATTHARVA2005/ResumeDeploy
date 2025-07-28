# backend/utils.py

import os
import uuid
import aiofiles
import re
import math
from pathlib import Path
from typing import List, Tuple, Union

from fastapi import UploadFile # Keep this import for UploadFile type hint
import httpx # NEW: Import httpx for async HTTP requests
from bs4 import BeautifulSoup # NEW: Import BeautifulSoup for HTML parsing

async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Asynchronously saves an uploaded file to a specified destination directory.
    Generates a unique filename to prevent collisions.

    Args:
        upload_file (UploadFile): The file object received from FastAPI.
        destination (str): The directory where the file should be saved.

    Returns:
        str: The full path to the saved file.
    
    Raises:
        IOError: If there's an issue writing the file.
    """
    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)
    
    # Generate a unique filename using UUID to prevent naming conflicts
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(destination, unique_filename)
    
    try:
        # Asynchronously write the file content
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read() # Read content asynchronously
            await f.write(content)
        return file_path
    except Exception as e:
        print(f"Error saving uploaded file {upload_file.filename} to {file_path}: {e}")
        raise IOError(f"Failed to save file: {e}")

def delete_file(file_path: str) -> bool:
    """
    Deletes a file from the filesystem if it exists.

    Args:
        file_path (str): The full path to the file to be deleted.

    Returns:
        bool: True if the file was successfully deleted or didn't exist, False if an error occurred.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            # print(f"File deleted: {file_path}") # Optional: for debugging
            return True
        # print(f"File not found, no deletion needed: {file_path}") # Optional: for debugging
        return True # Return True if file doesn't exist (goal is achieved)
    except OSError as e: # Catch specific OSError for file operations
        print(f"Error deleting file {file_path}: {e}")
        return False
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred while deleting file {file_path}: {e}")
        return False

# Note: The create_directories function is now primarily handled by run.py
# Keeping it here for modularity, but its direct call in main.py was removed.
def create_directories():
    """
    Creates necessary directories for the application if they don't already exist.
    This function is now primarily called by `run.py` at application startup.
    """
    directories = [
        "uploads",
        "data",
        "frontend/static/css",
        "frontend/static/js",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("All necessary directories ensured.")

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validates if a file has an allowed extension.

    Args:
        filename (str): The name of the file.
        allowed_extensions (List[str]): A list of allowed file extensions (e.g., ['.pdf', '.docx']).

    Returns:
        bool: True if the file extension is in the allowed list, False otherwise.
    """
    if not filename:
        return False
    
    file_extension = Path(filename).suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]

def format_file_size(size_bytes: int) -> str:
    """
    Formats a file size in bytes into a human-readable string (e.g., "10.5 MB").

    Args:
        size_bytes (int): The size of the file in bytes.

    Returns:
        str: A human-readable string representation of the file size.
    """
    if size_bytes == 0:
        return "0 B" # Changed to "0 B" for consistency
    
    size_names = ["B", "KB", "MB", "GB", "TB"] # Added TB for larger files
    
    # Calculate the appropriate unit
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """
    Cleans a filename by removing or replacing invalid characters for various file systems.
    Replaces characters like < > : " / \\ | ? * with underscores.
    Normalizes whitespace and multiple dots.

    Args:
        filename (str): The original filename.

    Returns:
        str: The cleaned filename.
    """
    # Remove invalid characters for filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace multiple dots with a single dot, but preserve the last extension dot
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    # Replace spaces and underscores with a single underscore
    cleaned = re.sub(r'[\s_]+', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    return cleaned

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncates a given text string to a specified maximum length,
    appending an ellipsis if truncated.

    Args:
        text (str): The input text string.
        max_length (int): The maximum desired length for the text.

    Returns:
        str: The truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """
    Calculates a percentage, handling division by zero.

    Args:
        part (Union[int, float]): The numerator.
        total (Union[int, float]): The denominator.

    Returns:
        float: The calculated percentage, rounded to 2 decimal places. Returns 0.0 if total is zero.
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)

class FileValidator:
    """
    Utility class for validating uploaded files based on extension and size.
    """
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.doc'} # .doc might require antiword for textract
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    @classmethod
    def is_valid_file(cls, file: UploadFile) -> Tuple[bool, str]:
        """
        Validates an uploaded file (FastAPI UploadFile object).

        Args:
            file (UploadFile): The uploaded file object.

        Returns:
            Tuple[bool, str]: A tuple where the first element is True if valid, False otherwise,
                              and the second element is a status message.
        """
        # Check if file object itself is provided and has a filename
        if not file or not file.filename:
            return False, "No file provided or filename is missing."
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}"
        
        # Check file size (UploadFile.size is available after file is read or if client provides Content-Length)
        # Note: file.size might be None before file.read() is called or if client doesn't send Content-Length.
        # For a robust check, you might need to read a chunk first or rely on client-side validation.
        # However, for most common FastAPI setups, file.size is populated.
        if file.size is not None and file.size > cls.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {format_file_size(cls.MAX_FILE_SIZE)}. Provided: {format_file_size(file.size)}"
        
        return True, "File is valid."

async def fetch_text_from_url(url: str) -> str:
    """
    Fetches content from a URL and attempts to extract human-readable text.
    Handles basic HTML parsing to remove tags.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client: # Add a timeout
            response = await client.get(url)
            response.raise_for_status() # Raise an exception for bad status codes

            # Check content-type header for text/html
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style tags
                for script_or_style in soup(['script', 'style']):
                    script_or_style.extract()
                # Get text, then clean up whitespace
                text = soup.get_text()
                return re.sub(r'\s+', ' ', text).strip()
            elif 'text/plain' in content_type:
                return response.text.strip()
            else:
                # For other content types, just return the text as is or raise an error
                # For this feature, we primarily expect text or HTML job descriptions
                print(f"Warning: Unexpected content type '{content_type}' for URL: {url}")
                return response.text.strip() # Try to return text anyway
    except httpx.RequestError as e:
        raise ValueError(f"Network error or invalid URL: {e}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP error fetching URL: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise ValueError(f"Could not fetch or parse content from URL: {e}")