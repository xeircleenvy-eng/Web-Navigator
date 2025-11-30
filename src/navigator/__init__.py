# src/navigator/__init__.py
"""
Web Navigator Tool - A standalone tool for applying web navigation commands to any AI.

This module provides the WebNavigator class that wraps browser functionality and
exposes all web navigation commands (click, type, scroll, goto, etc.) as simple
methods that can be easily integrated into any AI system.

Example usage:
    from src.navigator import WebNavigator
    
    async with WebNavigator() as nav:
        # Navigate to a webpage
        await nav.goto("https://google.com")
        
        # Get the current page state
        state = await nav.get_state()
        
        # Click on an element
        await nav.click(index=5)
        
        # Type in an input field
        await nav.type(index=3, text="Hello World")
"""

from src.navigator.web_navigator import WebNavigator
from src.navigator.config import NavigatorConfig

__all__ = ['WebNavigator', 'NavigatorConfig']
