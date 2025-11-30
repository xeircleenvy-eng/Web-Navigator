# src/navigator/config.py
"""Configuration for the Web Navigator tool."""

from dataclasses import dataclass, field
from typing import Literal, Optional
from pathlib import Path


@dataclass
class NavigatorConfig:
    """
    Configuration for the WebNavigator.
    
    Attributes:
        browser: Browser type to use ('chrome', 'firefox', 'edge')
        headless: Whether to run browser in headless mode
        downloads_dir: Directory for downloaded files
        browser_instance_dir: Path to browser executable (optional)
        user_data_dir: Path to browser user data directory (optional)
        device: Device emulation profile (optional)
        wss_url: WebSocket URL for remote browser connection (optional)
        timeout: Default timeout in milliseconds
        slow_mo: Slow down operations by this many milliseconds
        use_vision: Whether to capture screenshots for vision-based AI
    """
    browser: Literal['chrome', 'firefox', 'edge'] = 'edge'
    headless: bool = False
    downloads_dir: str = field(default_factory=lambda: (Path.home() / 'Downloads').as_posix())
    browser_instance_dir: Optional[str] = None
    user_data_dir: Optional[str] = None
    device: Optional[str] = None
    wss_url: Optional[str] = None
    timeout: int = 60 * 1000
    slow_mo: int = 300
    use_vision: bool = False
