"""
Example: Using WebNavigator with your own AI

This example demonstrates how to integrate the WebNavigator tool with any AI system.
The WebNavigator provides all the web navigation commands that your AI can use
to browse the web and interact with websites.

Usage:
    python examples/navigator_example.py
"""

import asyncio
from src.navigator import WebNavigator, NavigatorConfig


async def simple_navigation_example():
    """
    Simple example showing basic navigation commands.
    """
    print("=" * 60)
    print("Simple Navigation Example")
    print("=" * 60)
    
    # Create navigator with custom configuration
    config = NavigatorConfig(
        browser='chrome',  # or 'edge', 'firefox'
        headless=False,    # Set True for headless mode
        use_vision=False   # Set True to capture screenshots
    )
    
    async with WebNavigator(config) as nav:
        # Navigate to a website
        result = await nav.goto("https://www.example.com")
        print(f"Navigation: {result}")
        
        # Get the current state
        state = await nav.get_state()
        print(f"\nCurrent Page: {state.current_title}")
        print(f"URL: {state.current_url}")
        print(f"\nInteractive Elements:\n{state.interactive_elements}")
        
        # Wait a bit to see the result
        await nav.wait(2)


async def ai_integration_example():
    """
    Example showing how an AI would use the navigator.
    
    This simulates how your AI would:
    1. Get the page state
    2. Analyze the elements
    3. Decide on an action
    4. Execute the action
    5. Repeat until task is complete
    """
    print("\n" + "=" * 60)
    print("AI Integration Example")
    print("=" * 60)
    
    config = NavigatorConfig(
        browser='chrome',
        headless=False,
        use_vision=False
    )
    
    async with WebNavigator(config) as nav:
        # Step 1: Navigate to Google
        await nav.goto("https://www.google.com")
        
        # Step 2: Get the current state (this is what you'd send to your AI)
        state = await nav.get_state()
        
        # Your AI would analyze this state and decide what to do
        # For this example, we'll just print what the AI would see
        print("\n--- STATE SENT TO AI ---")
        print(state.to_prompt()[:1500] + "...")  # Truncated for readability
        
        # Step 3: Your AI would return a command like:
        # {"command": "type", "params": {"index": 3, "text": "Hello", "press_enter": True}}
        
        # Step 4: Execute the command
        # In a real integration, you'd parse the AI's response
        # result = await nav.execute_command("type", {"index": 3, "text": "Hello", "press_enter": True})
        
        print("\n--- AI WOULD NOW ANALYZE AND RESPOND ---")
        print("Your AI analyzes the state and returns actions to execute")
        
        await nav.wait(2)


async def command_execution_example():
    """
    Example showing how to execute commands by name.
    
    This is useful when your AI returns commands as strings.
    """
    print("\n" + "=" * 60)
    print("Command Execution Example")
    print("=" * 60)
    
    async with WebNavigator() as nav:
        # Navigate using the execute_command method
        # This is how you'd execute commands from AI output
        
        result = await nav.execute_command("goto", {"url": "https://www.example.com"})
        print(f"Result: {result}")
        
        # Get available tools description (to include in AI prompt)
        tools = await nav.get_tools_description()
        print(f"\n--- TOOLS AVAILABLE FOR AI ---\n{tools[:500]}...")
        
        await nav.wait(2)


async def full_workflow_example():
    """
    Complete example of an AI-driven web automation workflow.
    
    This shows how you would structure a loop where:
    1. You get the browser state
    2. Send it to your AI with a task
    3. Get the AI's response (command to execute)
    4. Execute the command
    5. Repeat until done
    """
    print("\n" + "=" * 60)
    print("Full AI Workflow Example")
    print("=" * 60)
    
    async with WebNavigator() as nav:
        # Get tools description for AI context
        tools_description = await nav.get_tools_description()
        
        # This is what you'd include in your AI's system prompt
        system_prompt = f"""
You are a web navigation assistant. You can use these tools to browse the web:

{tools_description}

When given a task and the current browser state, respond with the next action to take.
Format your response as: {{"command": "<command_name>", "params": {{...}}}}
When the task is complete, respond with: {{"done": true, "result": "<summary>"}}
"""
        
        print("System Prompt for AI:")
        print("-" * 40)
        print(system_prompt[:800] + "...")
        
        # Example task
        task = "Go to example.com and tell me the main heading"
        
        # Navigation loop (simplified)
        print(f"\nTask: {task}")
        print("-" * 40)
        
        # Step 1: Execute initial navigation
        result = await nav.goto("https://www.example.com")
        print(f"Action: goto -> {result}")
        
        # Step 2: Get state for AI
        state = await nav.get_state()
        
        # In a real scenario, you'd send this to your AI:
        # user_message = f"Task: {task}\n\nCurrent State:\n{state.to_prompt()}"
        # ai_response = your_ai.generate(system_prompt + user_message)
        
        # Step 3: Execute scrape to get content
        content = await nav.scrape()
        print(f"Action: scrape -> Got {len(content)} characters of content")
        
        # The AI would analyze and determine the task is complete
        print("\nTask completed! The main heading on example.com is 'Example Domain'")
        
        await nav.wait(2)


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("WebNavigator Examples")
    print("=" * 60)
    print("\nThese examples show how to integrate WebNavigator with your AI.\n")
    
    # Run only the simple example to demonstrate functionality
    # Comment out the examples you don't want to run
    asyncio.run(simple_navigation_example())
    # asyncio.run(ai_integration_example())
    # asyncio.run(command_execution_example())
    # asyncio.run(full_workflow_example())


if __name__ == "__main__":
    main()
