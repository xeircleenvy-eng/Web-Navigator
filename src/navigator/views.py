# src/navigator/views.py
"""Data classes for Web Navigator state and elements."""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
import base64


@dataclass
class ElementInfo:
    """Information about an interactive element on the page."""
    index: int
    tag: str
    text: str
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class NavigatorState:
    """
    Complete state of the browser for AI consumption.
    
    This class contains all the information an AI needs to understand
    the current state of the webpage and make navigation decisions.
    
    Attributes:
        current_url: URL of the current page
        current_title: Title of the current page
        current_tab_index: Index of the current tab
        tabs: List of (index, url, title) tuples for all open tabs
        interactive_elements: String description of clickable/input elements
        informative_elements: String description of text/content elements
        scrollable_elements: String description of scrollable containers
        screenshot: Screenshot bytes (if vision is enabled)
    """
    current_url: str
    current_title: str
    current_tab_index: int
    tabs: List[Tuple[int, str, str]]
    interactive_elements: str
    informative_elements: str
    scrollable_elements: str
    screenshot: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization."""
        result = {
            'current_url': self.current_url,
            'current_title': self.current_title,
            'current_tab_index': self.current_tab_index,
            'tabs': [{'index': t[0], 'url': t[1], 'title': t[2]} for t in self.tabs],
            'interactive_elements': self.interactive_elements,
            'informative_elements': self.informative_elements,
            'scrollable_elements': self.scrollable_elements,
        }
        if self.screenshot:
            result['screenshot_base64'] = base64.b64encode(self.screenshot).decode('utf-8')
        return result
    
    def to_prompt(self) -> str:
        """
        Convert state to a formatted string for use in AI prompts.
        
        This is useful for providing context to language models about
        the current state of the browser.
        """
        tabs_str = "\n".join([f"  [{t[0]}] {t[2]} - {t[1]}" for t in self.tabs])
        
        return f"""Current Browser State:
====================

Current Tab: [{self.current_tab_index}] {self.current_title}
Current URL: {self.current_url}

Open Tabs:
{tabs_str}

Interactive Elements (clickable, input fields, etc.):
{self.interactive_elements}

Informative Elements (text content):
{self.informative_elements}

Scrollable Elements:
{self.scrollable_elements}
"""
    
    def __str__(self) -> str:
        return self.to_prompt()
