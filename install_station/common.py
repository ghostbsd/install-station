"""
Common utility functions for Install Station.

This module provides various utility functions including password strength
checking, text validation, and deprecation decorators.
"""
import re
import warnings
from install_station.data import get_text


def lower_case(text: str) -> bool:
    """
    Find if password contain only lower case.
    :param text: password

    :return: True if password contain only lower case
    """
    search = re.compile(r'[^a-z]').search
    return not bool(search(text))


# Find if password contain only upper case
def upper_case(text: str) -> bool:
    """
    Find if password contain only upper case.
    :param text: password

    :return: True if password contain only upper case
    """
    search = re.compile(r'[^A-Z]').search
    return not bool(search(text))


# Find if password contain only lower case and number
def lower_and_number(text: str) -> bool:
    """
    Find if password contain only lower case and number.
    :param text: password

    :return: True if password contain only lower case and number
    """
    search = re.compile(r'[^a-z0-9]').search
    return not bool(search(text))


# Find if password contain only upper case and number
def upper_and_number(text: str) -> bool:
    """
    Find if password contain only upper case and number.
    :param text: password

    :return: True if password contain only upper case and number
    """
    search = re.compile(r'[^A-Z0-9]').search
    return not bool(search(text))


# Find if password contain only lower and upper case and
def lower_upper(text: str) -> bool:
    """
    Find if password contain only lower and upper case and
    :param text: password

    :return: True if password contain only lower and upper case and
    """
    search = re.compile(r'[^a-zA-Z]').search
    return not bool(search(text))


def lower_upper_number(text: str) -> bool:
    """
    Find if password contains only lowercase, uppercase letters and numbers.
    
    Args:
        text: password to check
        
    Returns:
        True if password contains only lowercase, uppercase letters and numbers
    """
    search = re.compile(r'[^a-zA-Z0-9]').search
    return not bool(search(text))


# Find if password contain only lowercase, uppercase numbers
# and some special character.
def all_character(text: str) -> bool:
    """
    Find if password contain only lowercase, uppercase numbers
    and some special character.
    :param text: password

    :return: True if password contain only lowercase, uppercase numbers
    and some special character.
    """
    search = re.compile(r'[^a-zA-Z0-9~!@#$%^&*_+":;\'-]').search
    return not bool(search(text))


def password_strength(password: str, label3) -> None:
    """
    Evaluate and display password strength.
    
    Args:
        password: The password to evaluate
        label3: GTK Label widget to display strength result
    """
    same_character_type = any(
        [
            lower_case(password),
            upper_case(password),
            password.isdigit()
        ]
    )
    mix_character = any(
        [
            lower_and_number(password),
            upper_and_number(password),
            lower_upper(password)
        ]
    )
    if ' ' in password or '\t' in password:
        label3.set_text(get_text("Space not allowed"))
    elif len(password) <= 4:
        label3.set_text(get_text("Super Weak"))
    elif len(password) <= 8 and same_character_type:
        label3.set_text(get_text("Super Weak"))
    elif len(password) <= 8 and mix_character:
        label3.set_text(get_text("Very Weak"))
    elif len(password) <= 8 and lower_upper_number(password):
        label3.set_text(get_text("Fairly Weak"))
    elif len(password) <= 8 and all_character(password):
        label3.set_text(get_text("Weak"))
    elif len(password) <= 12 and same_character_type:
        label3.set_text(get_text("Very Weak"))
    elif len(password) <= 12 and mix_character:
        label3.set_text(get_text("Fairly Weak"))
    elif len(password) <= 12 and lower_upper_number(password):
        label3.set_text(get_text("Weak"))
    elif len(password) <= 12 and all_character(password):
        label3.set_text(get_text("Strong"))
    elif len(password) <= 16 and same_character_type:
        label3.set_text(get_text("Fairly Weak"))
    elif len(password) <= 16 and mix_character:
        label3.set_text(get_text("Weak"))
    elif len(password) <= 16 and lower_upper_number(password):
        label3.set_text(get_text("Strong"))
    elif len(password) <= 16 and all_character(password):
        label3.set_text(get_text("Fairly Strong"))
    elif len(password) <= 20 and same_character_type:
        label3.set_text(get_text("Weak"))
    elif len(password) <= 20 and mix_character:
        label3.set_text(get_text("Strong"))
    elif len(password) <= 20 and lower_upper_number(password):
        label3.set_text(get_text("Fairly Strong"))
    elif len(password) <= 20 and all_character(password):
        label3.set_text(get_text("Very Strong"))
    elif len(password) <= 24 and same_character_type:
        label3.set_text(get_text("Strong"))
    elif len(password) <= 24 and mix_character:
        label3.set_text(get_text("Fairly Strong"))
    elif len(password) <= 24 and lower_upper_number(password):
        label3.set_text(get_text("Very Strong"))
    elif len(password) <= 24 and all_character(password):
        label3.set_text(get_text("Super Strong"))
    elif same_character_type:
        label3.set_text(get_text("Fairly Strong"))
    else:
        label3.set_text(get_text("Super Strong"))


def deprecated(*, version: str, reason: str):
    """
    Decorator to mark functions as deprecated.
    
    Args:
        version: Version when function was deprecated
        reason: Reason for deprecation
        
    Returns:
        Decorator function that adds deprecation warnings
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated (version {version}): {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
