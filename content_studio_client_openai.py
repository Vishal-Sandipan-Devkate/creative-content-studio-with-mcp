

import asyncio
import json
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import OpenAI
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: Error: openai not installed")
    print("Run: pip install openai")
    sys.exit(1)

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: Error: OPENAI_API_KEY not found in .env")
    print("\nTo get your API key:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Sign in or create an account (get $5 free credits!)")
    print("3. Click 'Create new secret key'")
    print("4. Add it to your .env file as: OPENAI_API_KEY=sk-...")
    sys.exit(1)

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Get best model
def get_best_model():
    """Get the best OpenAI model to use"""
    model_file = Path('.openai_model')
    if model_file.exists():
        saved_model = model_file.read_text().strip()
        print(f">> Using saved model: {saved_model}")
        return saved_model
    
    # Default to most affordable model
    print(">> Using model: gpt-4o-mini (affordable & capable)")
    return 'gpt-4o-mini'


class ContentStudioAgent:
    """AI Agent that manages creative content generation tasks"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        self._stdio_cm = None
        self._read = None
        self._write = None
        self.model_name = get_best_model()
        
    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server"""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script_path],
            env=None,
        )

        # Keep this context alive
        self._stdio_cm = stdio_client(server_params)
        self._read, self._write = await self._stdio_cm.__aenter__()

        self.session = ClientSession(self._read, self._write)
        await self.session.initialize()

        response = await self.session.list_tools()
        self.available_tools = response.tools

        print(f">>  Connected to MCP server")
        print(f">>  Tools discovered: {[t.name for t in self.available_tools]}")

    def format_tools_for_openai(self) -> list:
        """Convert MCP tools to OpenAI's function calling format"""
        openai_tools = []
        
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools

    async def call_tool(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a tool via MCP and return the result.
        
        FIXED: Better result extraction with multiple fallback methods
        """
        try:
            result = await self.session.call_tool(tool_name, arguments=tool_input)
            
            # Method 1: Try to get text from content array (MCP standard format)
            if hasattr(result, 'content') and result.content:
                if len(result.content) > 0:
                    first_content = result.content[0]
                    # Check if it has a text attribute
                    if hasattr(first_content, 'text'):
                        return first_content.text
                    # Check if it's a dict with 'text' key
                    elif isinstance(first_content, dict) and 'text' in first_content:
                        return first_content['text']
            
            # Method 2: Try direct string conversion
            result_str = str(result)
            if result_str and result_str != 'None':
                return result_str
            
            # Method 3: Try JSON serialization
            try:
                return json.dumps(result)
            except:
                pass
            
            # If all else fails, return error
            return json.dumps({
                "status": "error",
                "message": f"Could not extract result from tool response. Type: {type(result)}"
            })
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            print(f"      ERROR: Error: {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
    
    async def process_query(self, user_query: str, max_iterations: int = 10) -> str:
        """
        Process a user query using the AI agent loop with OpenAI.
        
        Args:
            user_query: The user's creative content request
            max_iterations: Maximum number of agent reasoning loops
        
        Returns:
            Final response from the agent
        """
        # Create tools for OpenAI
        tools = self.format_tools_for_openai()
        
        # Build message history
        messages = [
            {"role": "user", "content": user_query}
        ]
        
        print(f"\n>>  Sending query to OpenAI ({self.model_name})...")
        
        # Agent reasoning loop
        for iteration in range(max_iterations):
            print(f"\n>>  Agent Iteration {iteration + 1}/{max_iterations}")
            
            try:
                # Call OpenAI with function calling
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                )
                
                response_message = response.choices[0].message
                
                # Check if there are tool calls
                if response_message.tool_calls:
                    # Add assistant response to messages
                    messages.append(response_message)
                    
                    # Execute all tool calls
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            print(f"   WARNING:  Warning: Could not parse arguments: {e}")
                            function_args = {}
                        
                        print(f"   >>  Calling tool: {function_name}")
                        args_preview = json.dumps(function_args, indent=2)
                        if len(args_preview) > 200:
                            args_preview = args_preview[:200] + "..."
                        print(f"      Input: {args_preview}")
                        
                        # Execute the tool
                        result = await self.call_tool(function_name, function_args)
                        
                        result_preview = result[:200]
                        if len(result) > 200:
                            result_preview += "..."
                        print(f"      >>  Result: {result_preview}")
                        
                        # Add tool result to messages
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result,
                        })
                    
                    # Continue to get final response
                    continue
                
                # No tool calls - agent has finished
                elif response_message.content:
                    print(f"\n>>  Agent completed task in {iteration + 1} iterations")
                    return response_message.content
                
                else:
                    return "Agent did not provide a response"
                        
            except Exception as e:
                error_str = str(e)
                print(f"\nERROR: Error in iteration {iteration + 1}: {error_str[:200]}")
                
                if "insufficient_quota" in error_str or "quota" in error_str.lower():
                    return "CREDITS: Out of credits! Check https://platform.openai.com/usage"
                elif "rate" in error_str.lower():
                    return "RATE: Rate limit reached. Please wait a minute and try again."
                elif "invalid" in error_str.lower() or "401" in error_str:
                    return "KEY: Invalid API key. Check your .env file."
                else:
                    return f"ERROR: Error: {error_str[:300]}"
        
        return "Agent reached maximum iterations without completing task"
    
    async def cleanup(self):
        """Clean up connections"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
        except Exception as e:
            print(f"Warning: Error closing session: {e}")
            
        try:
            if hasattr(self, "_stdio_cm") and self._stdio_cm:
                await self._stdio_cm.__aexit__(None, None, None)
        except Exception as e:
            print(f"Warning: Error closing stdio: {e}")
    
    async def interactive_mode(self):
        """Run the agent in interactive chat mode"""
        print("=" * 70)
        print(">>  CREATIVE CONTENT STUDIO - AI AGENT (OPENAI) - FIXED VERSION")
        print("=" * 70)
        print(f">>  Using OpenAI API - Model: {self.model_name}")
        print("=" * 70)
        print("\nWhat would you like to create today?")
        print("\nExamples:")
        print("  • 'Create a YouTube thumbnail for my AI tutorial'")
        print("  • 'Make a QR code for my website'")
        print("  • 'Generate a red thumbnail saying Welcome'")
        print("\nType 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process the query
                response = await self.process_query(user_input)
                
                print(f"\n>>  Agent: {response}\n")
                print("-" * 70)
            
            except KeyboardInterrupt:
                print("\n\nGoodbye Goodbye!")
                break
            except Exception as e:
                print(f"\nERROR: Error: {str(e)}\n")


async def main():
    """Main entry point"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Error: OPENAI_API_KEY environment variable not set")
        print("\nTo get your API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Sign in or create an account")
        print("3. Click 'Create new secret key'")
        print("4. Add it to your .env file as: OPENAI_API_KEY=sk-...")
        sys.exit(1)

    # Allow server path to be specified as command line argument
    server_path = sys.argv[1] if len(sys.argv) > 1 else "content_studio_server_fixed.py"

    agent = ContentStudioAgent()
    
    try:
        await agent.connect_to_server(server_path)
        await agent.interactive_mode()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye Goodbye!")