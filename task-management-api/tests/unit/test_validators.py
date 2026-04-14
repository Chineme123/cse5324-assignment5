"""Unit tests for utility validators."""

import unittest
from app.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_task_data,
    sanitize_input
)


class TestEmailValidator(unittest.TestCase):
    """Tests for validate_email."""

    def test_valid_standard_email(self):
        """Standard email format should be valid."""
        self.assertTrue(validate_email('user@example.com'))

    def test_valid_subdomain_email(self):
        """Email with subdomain should be valid."""
        self.assertTrue(validate_email('test.user@domain.co.uk'))

    def test_valid_plus_tag_email(self):
        """Email with plus tag should be valid."""
        self.assertTrue(validate_email('user+tag@example.com'))

    def test_invalid_no_at_symbol(self):
        """Email without @ should be invalid."""
        self.assertFalse(validate_email('invalid'))

    def test_invalid_no_domain(self):
        """Email with no domain after @ should be invalid."""
        self.assertFalse(validate_email('user@'))

    def test_invalid_no_local_part(self):
        """Email with nothing before @ should be invalid."""
        self.assertFalse(validate_email('@example.com'))

    def test_invalid_spaces_in_email(self):
        """Email with spaces should be invalid."""
        self.assertFalse(validate_email('user name@example.com'))

    def test_invalid_none_input(self):
        """None input should return False."""
        self.assertFalse(validate_email(None))

    def test_invalid_empty_string(self):
        """Empty string should return False."""
        self.assertFalse(validate_email(''))


class TestPasswordValidator(unittest.TestCase):
    """Tests for validate_password_strength."""

    def test_valid_strong_password(self):
        """Strong password should pass all checks."""
        self.assertTrue(validate_password_strength('SecurePass123!'))

    def test_too_short(self):
        """Password under 8 characters should fail."""
        self.assertFalse(validate_password_strength('Sh0rt!'))

    def test_no_uppercase(self):
        """Password without uppercase should fail."""
        self.assertFalse(validate_password_strength('nouppercase123!'))

    def test_no_lowercase(self):
        """Password without lowercase should fail."""
        self.assertFalse(validate_password_strength('NOLOWERCASE123!'))

    def test_no_digits(self):
        """Password without digits should fail."""
        self.assertFalse(validate_password_strength('NoNumbers!'))

    def test_no_special_characters(self):
        """Password without special characters should fail."""
        self.assertFalse(validate_password_strength('NoSpecial123'))

    def test_none_input(self):
        """None input should return False."""
        self.assertFalse(validate_password_strength(None))

    def test_empty_string(self):
        """Empty string should return False."""
        self.assertFalse(validate_password_strength(''))


class TestTaskDataValidator(unittest.TestCase):
    """Tests for validate_task_data."""

    def test_valid_minimal_task(self):
        """Task with just a title should be valid."""
        valid, error = validate_task_data({'title': 'My Task'})
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_valid_full_task(self):
        """Task with all fields should be valid."""
        valid, error = validate_task_data({
            'title': 'Full Task',
            'priority': 'high',
            'status': 'todo'
        })
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_missing_title(self):
        """Task without title should fail validation."""
        valid, error = validate_task_data({'priority': 'high'})
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_empty_title(self):
        """Task with empty title should fail validation."""
        valid, error = validate_task_data({'title': ''})
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_title_too_long(self):
        """Task with title over 200 characters should fail."""
        valid, error = validate_task_data({'title': 'x' * 201})
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_invalid_priority(self):
        """Task with invalid priority should fail."""
        valid, error = validate_task_data(
            {'title': 'Task', 'priority': 'urgent'}
        )
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_invalid_status(self):
        """Task with invalid status should fail."""
        valid, error = validate_task_data(
            {'title': 'Task', 'status': 'pending'}
        )
        self.assertFalse(valid)
        self.assertIsNotNone(error)


class TestSanitizeInput(unittest.TestCase):
    """Tests for sanitize_input."""

    def test_removes_script_tags(self):
        """Script tags should be stripped from input."""
        dirty = 'Hello <script>alert("xss")</script>'
        clean = sanitize_input(dirty)
        self.assertNotIn('<script>', clean)
        self.assertNotIn('</script>', clean)

    def test_removes_html_tags(self):
        """HTML tags should be stripped from input."""
        dirty = '<b>Bold</b> text'
        clean = sanitize_input(dirty)
        self.assertNotIn('<b>', clean)
        self.assertIn('Bold', clean)

    def test_plain_text_unchanged(self):
        """Plain text with no HTML should be returned unchanged."""
        text = 'Hello world'
        self.assertEqual(sanitize_input(text), 'Hello world')

    def test_none_input_returns_none(self):
        """None input should return None."""
        self.assertIsNone(sanitize_input(None))

    def test_empty_string_returns_empty(self):
        """Empty string should return empty string."""
        self.assertEqual(sanitize_input(''), '')