"""
Input validation utilities for authentication and user data.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_password(password: str) -> None:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password:
        raise ValidationError("Password is required")
    
    # Check minimum length
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    # Check maximum length (bcrypt limit)
    if len(password.encode('utf-8')) > 72:
        raise ValidationError(
            "Password is too long. Maximum length is 72 bytes. "
            "Please use a shorter password."
        )
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;`~]', password):
        raise ValidationError("Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_passwords = [
        'password', 'password123', '12345678', 'qwerty123', 'admin123',
        'letmein123', 'welcome123', 'monkey123', 'dragon123'
    ]
    if password.lower() in weak_passwords:
        raise ValidationError("Password is too common. Please choose a stronger password")


def validate_username(username: str) -> None:
    """
    Validate username meets requirements.
    
    Args:
        username: Username to validate
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username:
        raise ValidationError("Username is required")
    
    # Check length
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")
    
    if len(username) > 50:
        raise ValidationError("Username must not exceed 50 characters")
    
    # Check format (alphanumeric, underscores, hyphens only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Must start with a letter
    if not username[0].isalpha():
        raise ValidationError("Username must start with a letter")
    
    # Check for reserved usernames
    reserved_usernames = [
        'admin', 'root', 'system', 'api', 'test', 'user', 'guest',
        'administrator', 'moderator', 'superuser', 'support'
    ]
    if username.lower() in reserved_usernames:
        raise ValidationError(f"Username '{username}' is reserved")


def validate_email(email: str) -> None:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email is required")
    
    # Check length
    if len(email) > 100:
        raise ValidationError("Email must not exceed 100 characters")
    
    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    # Check for consecutive dots
    if '..' in email:
        raise ValidationError("Email cannot contain consecutive dots")
    
    # Check local part length (before @)
    local_part = email.split('@')[0]
    if len(local_part) > 64:
        raise ValidationError("Email local part is too long")


def validate_full_name(full_name: Optional[str]) -> None:
    """
    Validate full name if provided.
    
    Args:
        full_name: Full name to validate (optional)
        
    Raises:
        ValidationError: If name is invalid
    """
    if full_name is None or full_name == "":
        return  # Full name is optional
    
    # Check length
    if len(full_name) > 100:
        raise ValidationError("Full name must not exceed 100 characters")
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s'-]+$", full_name):
        raise ValidationError(
            "Full name can only contain letters, spaces, hyphens, and apostrophes"
        )
    
    # Check minimum length if provided
    if len(full_name.strip()) < 2:
        raise ValidationError("Full name must be at least 2 characters long")


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize a string input by removing dangerous characters and limiting length.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def validate_file_upload_size(size_bytes: int, max_size_mb: int = 50) -> None:
    """
    Validate uploaded file size.
    
    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB
        
    Raises:
        ValidationError: If file is too large
    """
    max_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(f"File size exceeds maximum of {max_size_mb}MB")
    
    if size_bytes == 0:
        raise ValidationError("File is empty")


def validate_conversation_title(title: str) -> None:
    """
    Validate conversation title.
    
    Args:
        title: Conversation title to validate
        
    Raises:
        ValidationError: If title is invalid
    """
    if not title:
        raise ValidationError("Conversation title is required")
    
    if len(title) > 255:
        raise ValidationError("Conversation title must not exceed 255 characters")
    
    if len(title.strip()) < 1:
        raise ValidationError("Conversation title cannot be empty")
    
    # Remove dangerous characters
    sanitized_title = sanitize_string(title, max_length=255)
    if sanitized_title != title:
        raise ValidationError("Conversation title contains invalid characters")


def validate_query_parameter(param: str, param_name: str, max_length: int = 1000) -> None:
    """
    Validate query parameters to prevent injection attacks.
    
    Args:
        param: Parameter value to validate
        param_name: Name of the parameter (for error messages)
        max_length: Maximum allowed length
        
    Raises:
        ValidationError: If parameter is invalid
    """
    if param is None:
        return
    
    if len(param) > max_length:
        raise ValidationError(f"{param_name} exceeds maximum length of {max_length} characters")
    
    # Check for SQL injection patterns
    sql_patterns = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(--\s)',
        r'(\/\*.*\*\/)',
        r'(\bEXEC\b|\bEXECUTE\b)',
        r'(\bSCRIPT\b)',
        r'(<script[^>]*>.*?</script>)',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, param, re.IGNORECASE):
            raise ValidationError(f"{param_name} contains potentially malicious content")


def validate_integer_parameter(value: any, param_name: str, min_val: int = 0, max_val: int = 1000) -> int:
    """
    Validate and convert integer parameters.
    
    Args:
        value: Value to validate and convert
        param_name: Name of the parameter
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated integer value
        
    Raises:
        ValidationError: If value is invalid
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{param_name} must be a valid integer")
    
    if int_value < min_val or int_value > max_val:
        raise ValidationError(f"{param_name} must be between {min_val} and {max_val}")
    
    return int_value

