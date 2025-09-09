"""
Unit tests for utility functions.
"""
import pytest
from app import sanitise_input


class TestSanitiseInput:
    """Test cases for the sanitise_input function."""
    
    def test_sanitise_input_removes_html_tags(self):
        """Test that HTML tags are removed from input."""
        input_text = "<script>alert('xss')</script>Hello World"
        result = sanitise_input(input_text, 100)
        assert result == "scriptalert(xss)/scriptHello World"
    
    def test_sanitise_input_removes_dangerous_characters(self):
        """Test that dangerous characters are removed."""
        input_text = "Test<>\"'&String"
        result = sanitise_input(input_text, 100)
        assert result == "TestString"
    
    def test_sanitise_input_limits_length(self):
        """Test that input is truncated to max_length."""
        input_text = "This is a very long string that should be truncated"
        result = sanitise_input(input_text, 10)
        assert result == "This is a "
        assert len(result) == 10
    
    def test_sanitise_input_empty_string(self):
        """Test sanitise_input with empty string."""
        result = sanitise_input("", 100)
        assert result == ""
    
    def test_sanitise_input_max_length_zero(self):
        """Test sanitise_input with max_length of 0."""
        result = sanitise_input("Hello", 0)
        assert result == ""
    
    def test_sanitise_input_normal_text(self):
        """Test sanitise_input with normal text."""
        input_text = "Hello World 123"
        result = sanitise_input(input_text, 100)
        assert result == "Hello World 123"
    
    def test_sanitise_input_unicode_characters(self):
        """Test sanitise_input with unicode characters."""
        input_text = "Hello 世界 🌍"
        result = sanitise_input(input_text, 100)
        assert result == "Hello 世界 🌍"
