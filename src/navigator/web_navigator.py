# src/navigator/web_navigator.py
"""
WebNavigator - A standalone tool for applying web navigation commands to any AI.

This class provides a simple interface for browser automation that can be easily
integrated into any AI system. It exposes all web navigation commands as methods
that return results suitable for AI consumption.
"""

from src.agent.web.browser.config import BrowserConfig
from src.agent.web.browser import Browser
from src.agent.web.context import Context
from src.navigator.config import NavigatorConfig
from src.navigator.views import NavigatorState, ElementInfo
from markdownify import markdownify
from typing import Literal, Optional, List, Dict, Any
from pathlib import Path
from asyncio import sleep
from os import getcwd
import httpx
import asyncio
import json


class WebNavigator:
    """
    A standalone web navigation tool that can be integrated with any AI system.
    
    This class wraps the browser context and provides all web navigation commands
    as simple async methods. Each method returns a result suitable for AI consumption.
    
    Example usage:
        # Async context manager usage (recommended)
        async with WebNavigator() as nav:
            await nav.goto("https://google.com")
            state = await nav.get_state()
            await nav.type(index=3, text="Hello World", press_enter=True)
        
        # Manual lifecycle management
        nav = WebNavigator()
        await nav.start()
        try:
            await nav.goto("https://google.com")
            state = await nav.get_state()
        finally:
            await nav.close()
    
    Attributes:
        config: Navigator configuration
        browser: Browser instance
        context: Browser context
        use_vision: Whether to capture screenshots
    """
    
    def __init__(self, config: NavigatorConfig = None):
        """
        Initialize the WebNavigator.
        
        Args:
            config: Navigator configuration. If None, uses default settings.
        """
        self.config = config or NavigatorConfig()
        self.browser: Browser = None
        self.context: Context = None
        self.use_vision = self.config.use_vision
        self._started = False
    
    async def __aenter__(self):
        """Async context manager entry - starts the browser."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes the browser."""
        await self.close()
    
    async def start(self):
        """
        Start the browser and initialize the context.
        
        This method must be called before using any navigation commands
        when not using the async context manager.
        """
        if self._started:
            return
        
        browser_config = BrowserConfig(
            browser=self.config.browser,
            headless=self.config.headless,
            downloads_dir=self.config.downloads_dir,
            browser_instance_dir=self.config.browser_instance_dir,
            user_data_dir=self.config.user_data_dir,
            device=self.config.device,
            wss_url=self.config.wss_url,
            timeout=self.config.timeout,
            slow_mo=self.config.slow_mo
        )
        
        self.browser = Browser(config=browser_config)
        self.context = Context(browser=self.browser)
        await self.context.init_session()
        self._started = True
    
    async def close(self):
        """
        Close the browser and clean up resources.
        
        This method should be called when done using the navigator
        when not using the async context manager.
        """
        if not self._started:
            return
        
        try:
            if self.context:
                await self.context.close_session()
            if self.browser:
                await self.browser.close_browser()
        except Exception as e:
            print(f'Failed to close navigator: {e}')
        finally:
            self.context = None
            self.browser = None
            self._started = False
    
    # ==================== STATE METHODS ====================
    
    async def get_state(self, use_vision: bool = None) -> NavigatorState:
        """
        Get the current state of the browser.
        
        This is the primary method for AI to understand the current page state.
        Returns information about interactive elements, informative elements,
        scrollable elements, tabs, and optionally a screenshot.
        
        Args:
            use_vision: Whether to include screenshot. If None, uses config setting.
        
        Returns:
            NavigatorState containing all relevant page information
        """
        if use_vision is None:
            use_vision = self.use_vision
        
        browser_state = await self.context.get_state(use_vision=use_vision)
        
        return NavigatorState(
            current_url=browser_state.current_tab.url,
            current_title=browser_state.current_tab.title,
            current_tab_index=browser_state.current_tab.id,
            tabs=[(tab.id, tab.url, tab.title) for tab in browser_state.tabs],
            interactive_elements=browser_state.dom_state.interactive_elements_to_string(),
            informative_elements=browser_state.dom_state.informative_elements_to_string(),
            scrollable_elements=browser_state.dom_state.scrollable_elements_to_string(),
            screenshot=browser_state.screenshot if use_vision else None
        )
    
    async def get_state_as_dict(self, use_vision: bool = None) -> Dict[str, Any]:
        """
        Get the current state as a dictionary (for JSON serialization).
        
        Args:
            use_vision: Whether to include screenshot. If None, uses config setting.
        
        Returns:
            Dictionary containing all relevant page information
        """
        state = await self.get_state(use_vision=use_vision)
        return state.to_dict()
    
    async def get_tools_description(self) -> str:
        """
        Get a description of all available navigation commands/tools.
        
        This is useful for providing tool descriptions to an AI model.
        
        Returns:
            String containing descriptions of all available tools
        """
        return TOOLS_DESCRIPTION
    
    # ==================== NAVIGATION COMMANDS ====================
    
    async def click(self, index: int) -> str:
        """
        Click on an interactive element.
        
        Args:
            index: The index/label of the element to click (from get_state)
        
        Returns:
            Result message describing what was clicked
        """
        page = await self.context.get_current_page()
        await page.wait_for_load_state('load')
        element = await self.context.get_element_by_index(index=index)
        handle = await self.context.get_handle_by_xpath(element.xpath)
        is_hidden = await handle.is_hidden()
        if not is_hidden:
            await handle.scroll_into_view_if_needed()
        await handle.click(force=True)
        return f'Clicked on element at index {index}'
    
    async def type(
        self, 
        index: int, 
        text: str, 
        clear: bool = False, 
        press_enter: bool = False
    ) -> str:
        """
        Type text into an input field.
        
        Args:
            index: The index/label of the input element
            text: The text to type
            clear: Whether to clear existing text before typing
            press_enter: Whether to press Enter after typing
        
        Returns:
            Result message describing what was typed
        """
        page = await self.context.get_current_page()
        element = await self.context.get_element_by_index(index=index)
        handle = await self.context.get_handle_by_xpath(element.xpath)
        await page.wait_for_load_state('load')
        is_hidden = await handle.is_hidden()
        if not is_hidden:
            await handle.scroll_into_view_if_needed()
        await handle.click(force=True)
        if clear:
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Backspace')
        await page.keyboard.type(text, delay=80)
        if press_enter:
            await page.keyboard.press('Enter')
        return f'Typed "{text}" in element at index {index}'
    
    async def scroll(
        self, 
        direction: Literal['up', 'down'] = 'down',
        index: int = None,
        amount: int = 500
    ) -> str:
        """
        Scroll the page or a specific element.
        
        Args:
            direction: 'up' or 'down'
            index: Index of scrollable element, or None for page scroll
            amount: Pixels to scroll
        
        Returns:
            Result message describing the scroll action
        """
        page = await self.context.get_current_page()
        if index is not None:
            element = await self.context.get_element_by_index(index=index)
            handle = await self.context.get_handle_by_xpath(xpath=element.xpath)
            if direction == 'up':
                await page.evaluate(f'(element)=> element.scrollBy(0,{-amount})', handle)
            elif direction == 'down':
                await page.evaluate(f'(element)=> element.scrollBy(0,{amount})', handle)
            else:
                raise ValueError('Invalid direction')
            return f'Scrolled {direction} inside element at index {index} by {amount}px'
        else:
            scroll_y_before = await self.context.execute_script(page, "() => window.scrollY")
            max_scroll_y = await self.context.execute_script(page, "() => document.documentElement.scrollHeight - window.innerHeight")
            
            if scroll_y_before >= max_scroll_y and direction == 'down':
                return "Already at the bottom, cannot scroll further."
            elif scroll_y_before == 0 and direction == 'up':
                return "Already at the top, cannot scroll further."
            
            if direction == 'up':
                await page.mouse.wheel(0, -amount)
            elif direction == 'down':
                await page.mouse.wheel(0, amount)
            else:
                raise ValueError('Invalid direction')
            
            scroll_y_after = await self.context.execute_script(page, "() => window.scrollY")
            if scroll_y_before == scroll_y_after:
                return "Scrolling has no effect, the entire content fits within the viewport."
            
            return f'Scrolled {direction} by {amount}px'
    
    async def goto(self, url: str) -> str:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to (must include protocol like https://)
        
        Returns:
            Result message describing the navigation
        """
        page = await self.context.get_current_page()
        await page.goto(url=url, wait_until='domcontentloaded')
        await page.wait_for_timeout(2.5 * 1000)
        return f'Navigated to {url}'
    
    async def back(self) -> str:
        """
        Navigate back in browser history.
        
        Returns:
            Result message
        """
        page = await self.context.get_current_page()
        await page.go_back()
        await page.wait_for_load_state('load')
        return 'Navigated to previous page'
    
    async def forward(self) -> str:
        """
        Navigate forward in browser history.
        
        Returns:
            Result message
        """
        page = await self.context.get_current_page()
        await page.go_forward()
        await page.wait_for_load_state('load')
        return 'Navigated to next page'
    
    async def press_key(self, keys: str, times: int = 1) -> str:
        """
        Press keyboard keys or key combinations.
        
        Args:
            keys: Key or key combination (e.g., "Enter", "Control+A", "Escape")
            times: Number of times to press
        
        Returns:
            Result message
        """
        page = await self.context.get_current_page()
        await page.wait_for_load_state('domcontentloaded')
        for _ in range(times):
            await page.keyboard.press(keys)
        return f'Pressed {keys}'
    
    async def wait(self, seconds: int) -> str:
        """
        Wait for a specified number of seconds.
        
        Args:
            seconds: Number of seconds to wait
        
        Returns:
            Result message
        """
        await sleep(seconds)
        return f'Waited for {seconds}s'
    
    async def scrape(self) -> str:
        """
        Scrape the current page content as markdown.
        
        Returns:
            Page content in markdown format
        """
        page = await self.context.get_current_page()
        await page.wait_for_load_state('domcontentloaded')
        html = await page.content()
        content = markdownify(html)
        return f'Scraped content:\n{content}'
    
    async def download(self, url: str, filename: str) -> str:
        """
        Download a file from a URL.
        
        Args:
            url: URL of the file to download
            filename: Name to save the file as
        
        Returns:
            Result message with file path
        """
        folder_path = Path(self.config.downloads_dir)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        path = folder_path.joinpath(filename)
        with open(path, 'wb') as f:
            f.write(response.content)
        return f'Downloaded {filename} from {url} and saved to {path}'
    
    async def tab(
        self, 
        mode: Literal['open', 'close', 'switch'],
        tab_index: int = None
    ) -> str:
        """
        Manage browser tabs.
        
        Args:
            mode: 'open' to open new tab, 'close' to close current, 'switch' to switch tabs
            tab_index: Tab index to switch to (required for 'switch' mode)
        
        Returns:
            Result message
        """
        session = await self.context.get_session()
        pages = session.context.pages
        
        if mode == 'open':
            page = await session.context.new_page()
            session.current_page = page
            await page.wait_for_load_state('load')
            return 'Opened a new blank tab and switched to it.'
        elif mode == 'close':
            if len(pages) == 1:
                return 'Cannot close the last remaining tab.'
            page = session.current_page
            await page.close()
            pages = session.context.pages
            session.current_page = pages[-1]
            await session.current_page.bring_to_front()
            await session.current_page.wait_for_load_state('load')
            return 'Closed current tab and switched to the last tab.'
        elif mode == 'switch':
            if tab_index is None or tab_index < 0 or tab_index >= len(pages):
                raise IndexError(f'Tab index {tab_index} is out of range. Available tabs: {len(pages)}')
            session.current_page = pages[tab_index]
            await session.current_page.bring_to_front()
            await session.current_page.wait_for_load_state('load')
            return f'Switched to tab {tab_index} (Total tabs: {len(pages)}).'
        else:
            raise ValueError("Invalid mode. Use 'open', 'close', or 'switch'.")
    
    async def upload(self, index: int, filenames: List[str]) -> str:
        """
        Upload files to a file input element.
        
        Args:
            index: Index of the file input element
            filenames: List of filenames from the ./uploads directory
        
        Returns:
            Result message
        """
        element = await self.context.get_element_by_index(index=index)
        handle = await self.context.get_handle_by_xpath(element.xpath)
        files = [Path(getcwd()).joinpath('./uploads', filename) for filename in filenames]
        page = await self.context.get_current_page()
        async with page.expect_file_chooser() as file_chooser_info:
            await handle.click()
        file_chooser = await file_chooser_info.value
        handle = file_chooser.element
        if file_chooser.is_multiple():
            await handle.set_input_files(files=files)
        else:
            await handle.set_input_files(files=files[0])
        await page.wait_for_load_state('load')
        return f'Uploaded {filenames} to element at index {index}'
    
    async def select(self, index: int, labels: List[str]) -> str:
        """
        Select options from a dropdown/select element.
        
        Args:
            index: Index of the select element
            labels: List of option labels to select
        
        Returns:
            Result message
        """
        element = await self.context.get_element_by_index(index=index)
        handle = await self.context.get_handle_by_xpath(element.xpath)
        label = labels if len(labels) > 1 else labels[0]
        await handle.select_option(label=label)
        labels_str = ", ".join(labels)
        return f'Selected {labels_str} from dropdown at index {index}'
    
    async def execute_script(self, script: str) -> str:
        """
        Execute JavaScript on the page.
        
        Args:
            script: JavaScript code to execute
        
        Returns:
            Result of the script execution
        """
        page = await self.context.get_current_page()
        result = await self.context.execute_script(page, script)
        return f"Script result: {result}"
    
    # ==================== HELPER METHODS ====================
    
    async def execute_command(self, command: str, params: Dict[str, Any]) -> str:
        """
        Execute a navigation command by name.
        
        This is useful for AI systems that output command names and parameters.
        
        Args:
            command: Name of the command (e.g., 'click', 'type', 'goto')
            params: Dictionary of parameters for the command
        
        Returns:
            Result of the command execution
        """
        command_map = {
            'click': self.click,
            'type': self.type,
            'scroll': self.scroll,
            'goto': self.goto,
            'back': self.back,
            'forward': self.forward,
            'key': self.press_key,
            'press_key': self.press_key,
            'wait': self.wait,
            'scrape': self.scrape,
            'download': self.download,
            'tab': self.tab,
            'upload': self.upload,
            'select': self.select,
            'menu': self.select,
            'script': self.execute_script,
            'execute_script': self.execute_script,
        }
        
        if command not in command_map:
            raise ValueError(f"Unknown command: {command}. Available commands: {list(command_map.keys())}")
        
        return await command_map[command](**params)
    
    def run_sync(self, coro):
        """
        Run an async coroutine synchronously.
        
        This is a convenience method for using the navigator in synchronous code.
        
        Args:
            coro: Async coroutine to run
        
        Returns:
            Result of the coroutine
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


# Tool descriptions for AI systems
TOOLS_DESCRIPTION = """
Available Web Navigation Commands:

1. click(index: int)
   Click on an interactive element by its index.
   Example: click(index=5)

2. type(index: int, text: str, clear: bool = False, press_enter: bool = False)
   Type text into an input field.
   Example: type(index=3, text="Hello World", press_enter=True)

3. scroll(direction: 'up' | 'down' = 'down', index: int = None, amount: int = 500)
   Scroll the page or a specific element.
   Example: scroll(direction='down', amount=300)

4. goto(url: str)
   Navigate to a URL.
   Example: goto(url="https://google.com")

5. back()
   Navigate back in browser history.

6. forward()
   Navigate forward in browser history.

7. press_key(keys: str, times: int = 1)
   Press keyboard keys or combinations.
   Example: press_key(keys="Enter") or press_key(keys="Control+A")

8. wait(seconds: int)
   Wait for a specified number of seconds.
   Example: wait(seconds=3)

9. scrape()
   Get the current page content as markdown.

10. download(url: str, filename: str)
    Download a file from a URL.
    Example: download(url="https://example.com/file.pdf", filename="doc.pdf")

11. tab(mode: 'open' | 'close' | 'switch', tab_index: int = None)
    Manage browser tabs.
    Example: tab(mode='open') or tab(mode='switch', tab_index=1)

12. upload(index: int, filenames: list[str])
    Upload files to a file input element.
    Example: upload(index=5, filenames=["document.pdf"])

13. select(index: int, labels: list[str])
    Select options from a dropdown.
    Example: select(index=7, labels=["Option A"])

14. execute_script(script: str)
    Execute JavaScript on the page.
    Example: execute_script(script="document.title")

15. get_state()
    Get the current page state including all interactive elements.
    Returns: NavigatorState with current URL, title, tabs, and elements.
"""
