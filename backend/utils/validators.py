from pathlib import Path
from typing import Dict, List
import re
import magic  # python-magic for file type validation
import logging

logger = logging.getLogger(__name__)

def validate_file(file, max_size: int, allowed_extensions: List[str]) -> Dict:
    """
    Validate uploaded file
    
    Args:
        file: UploadFile object
        max_size: Maximum file size in bytes
        allowed_extensions: List of allowed extensions (without dot)
    
    Returns:
        {
            'valid': bool,
            'error': str (if invalid)
        }
    """
    try:
        # Check filename
        if not file.filename:
            return {'valid': False, 'error': 'No filename provided'}
        
        # Check extension
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in allowed_extensions:
            return {
                'valid': False,
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            if file.size > max_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {max_size / (1024*1024):.1f}MB'
                }
        
        # Check for malicious filenames
        if not is_safe_filename(file.filename):
            return {
                'valid': False,
                'error': 'Invalid filename. Contains illegal characters'
            }
        
        return {'valid': True}
        
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return {'valid': False, 'error': f'Validation failed: {str(e)}'}


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal, etc.)
    """
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for null bytes
    if '\x00' in filename:
        return False
    
    # Check for control characters
    if any(ord(char) < 32 for char in filename):
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Remove or replace special characters
    # Keep alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple consecutive dots
    filename = re.sub(r'\.+', '.', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = Path(filename).stem, Path(filename).suffix
        name = name[:max_length - len(ext)]
        filename = name + ext
    
    return filename


def validate_document_id(doc_id: str) -> bool:
    """
    Validate MongoDB ObjectId format
    """
    if not doc_id or len(doc_id) != 24:
        return False
    
    # Check if hexadecimal
    try:
        int(doc_id, 16)
        return True
    except ValueError:
        return False


def validate_text_length(text: str, min_length: int = 10, max_length: int = 1000000) -> Dict:
    """
    Validate text content length
    """
    text_length = len(text)
    
    if text_length < min_length:
        return {
            'valid': False,
            'error': f'Text too short. Minimum {min_length} characters required'
        }
    
    if text_length > max_length:
        return {
            'valid': False,
            'error': f'Text too long. Maximum {max_length} characters allowed'
        }
    
    return {'valid': True}


def validate_email(email: str) -> bool:
    """
    Validate email address format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """
    Validate date string format
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def check_file_magic(file_path: str, expected_types: List[str]) -> bool:
    """
    Check actual file type using magic numbers (not just extension)
    
    Args:
        file_path: Path to file
        expected_types: List of expected MIME types
    
    Returns:
        True if file type matches expected types
    """
    try:
        import magic
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        return any(expected in file_type for expected in expected_types)
    except Exception as e:
        logger.warning(f"Magic type check failed: {e}")
        return True  # Fallback to allowing file if magic check fails