"""Input validation and sanitization utilities."""

import re
import bleach


def validate_email(email):
    """Return True if email matches a valid format."""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password):
    """
    Return True if password meets strength requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character
    """
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def validate_task_data(data):
    """
    Validate task creation/update data.
    Returns (True, None) on success or (False, error_message) on failure.
    """
    if not data.get('title') or not data['title'].strip():
        return False, "Title is required."
    if len(data['title']) > 200:
        return False, "Title must be 200 characters or fewer."
    valid_priorities = ['low', 'medium', 'high']
    if 'priority' in data and data['priority'] not in valid_priorities:
        return False, f"Priority must be one of: {valid_priorities}"
    valid_statuses = ['todo', 'in_progress', 'completed']
    if 'status' in data and data['status'] not in valid_statuses:
        return False, f"Status must be one of: {valid_statuses}"
    return True, None


def sanitize_input(text):
    """Strip all HTML tags from the input string."""
    if not text:
        return text
    return bleach.clean(text, tags=[], strip=True)