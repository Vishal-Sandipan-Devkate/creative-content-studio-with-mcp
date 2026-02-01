import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import qrcode
import uuid

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import OpenAI
try:
    from openai import OpenAI
    print(">> OpenAI package imported")
except ImportError:
    print("ERROR: openai not installed")
    print("Run: pip install openai")
    import sys
    sys.exit(1)

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env")
    import sys
    sys.exit(1)

print(">> API key found")

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
print(">> OpenAI client created")

# Configuration
OUTPUT_DIR = Path("content_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
def get_font(size=40):
    """Get default font"""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()


def generate_thumbnail(
    text: str,
    width: int = 1280,
    height: int = 720,
    background_color: str = "#FF6B6B",
    text_color: str = "#FFFFFF",
    **kwargs
) -> str:
    """Generate a thumbnail image"""
    try:
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        base_font_size = min(width, height) // 10
        font_size = max(30, base_font_size - len(text) * 2)
        font = get_font(font_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x + 5, y + 5), text, font=font, fill="#000000")
        draw.text((x, y), text, font=font, fill=text_color)
        
        filename = f"thumbnail_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        img.save(filepath, quality=95)
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "dimensions": [width, height]
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed: {str(e)}"
        })


def generate_qr_code(
    data: str,
    size: int = 10,
    fill_color: str = "black",
    back_color: str = "white",
    **kwargs
) -> str:
    """Generate a QR code"""
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=max(1, min(50, size)),
            border=2
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        filename = f"qrcode_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        img.save(filepath)
        
        data_type = "URL" if data.startswith(("http://", "https://")) else "Text"
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "data_type": data_type
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed: {str(e)}"
        })

def create_social_card(
    title: str,
    subtitle: str = "",
    image_path: str = "",
    platform: str = "twitter",
    theme: str = "dark"
) -> str:
    """
    Create a social media preview card (Open Graph/Twitter Card style).
    
    Args:
        title: Main heading text
        subtitle: Secondary text (optional)
        image_path: Path to background/feature image (optional)
        platform: Target platform - "twitter", "facebook", "linkedin" (affects dimensions)
        theme: Color theme - "dark", "light", "colorful" (default: dark)
    
    Returns:
        JSON string with status and file information
    
    Examples:
        - "Create a Twitter card for my blog post about AI"
        - "Make a LinkedIn social card with dark theme"
        - "Generate a Facebook preview card for this announcement"
    """
    try:
        # Platform-specific dimensions (optimized for each platform)
        dimensions = {
            "twitter": (1200, 675),   # 16:9 ratio
            "facebook": (1200, 630),  # ~1.91:1 ratio
            "linkedin": (1200, 627),  # ~1.91:1 ratio
            "instagram": (1080, 1080) # 1:1 square
        }
        
        width, height = dimensions.get(platform.lower(), (1200, 630))
        
        # Theme colors
        themes = {
            "dark": {
                "bg": "#1a1a2e",
                "title": "#ffffff",
                "subtitle": "#aaaaaa",
                "accent": "#4ECDC4"
            },
            "light": {
                "bg": "#f8f9fa",
                "title": "#2c3e50",
                "subtitle": "#7f8c8d",
                "accent": "#3498db"
            },
            "colorful": {
                "bg": "#FF6B6B",
                "title": "#ffffff",
                "subtitle": "#ffe66d",
                "accent": "#4ECDC4"
            }
        }
        
        colors = themes.get(theme, themes["dark"])
        
        # Create base image
        img = Image.new('RGB', (width, height), colors["bg"])
        draw = ImageDraw.Draw(img)
        
        # Add background image if provided
        if image_path and Path(image_path).exists():
            try:
                bg_img = Image.open(image_path)
                # Resize and blend
                bg_img = bg_img.resize((width, height))
                # Darken for text readability
                img = Image.blend(img, bg_img, alpha=0.3)
                draw = ImageDraw.Draw(img)
            except:
                pass  # Use solid color background if image fails
        
        # Add accent line
        draw.rectangle([50, height - 150, 150, height - 140], fill=colors["accent"])
        
        # Add title
        title_font = get_font(60)
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        
        # Wrap title if too long
        if title_width > width - 100:
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_bbox = draw.textbbox((0, 0), test_line, font=title_font)
                if test_bbox[2] - test_bbox[0] < width - 100:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            y_position = height // 3
            for line in lines[:2]:  # Limit to 2 lines
                draw.text((60, y_position), line, font=title_font, fill=colors["title"])
                y_position += 80
        else:
            draw.text((60, height // 3), title, font=title_font, fill=colors["title"])
        
        # Add subtitle if provided
        if subtitle:
            subtitle_font = get_font(30)
            draw.text((60, height // 2 + 50), subtitle, font=subtitle_font, fill=colors["subtitle"])
        
        # Add platform badge
        platform_font = get_font(20)
        draw.text((60, height - 80), f"Optimized for {platform.title()}", 
                 font=platform_font, fill=colors["subtitle"])
        
        # Save
        filename = f"social_card_{platform}_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        img.save(filepath, quality=95)
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "platform": platform,
            "dimensions": [width, height],
            "theme": theme
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to create social card: {str(e)}"
        })

def create_video_montage(
    image_paths: list[str],
    duration_per_image: float = 3.0,
    transition_duration: float = 0.5,
    output_fps: int = 24
) -> str:
    """
    Create a video montage from a list of images with smooth transitions.
    
    Args:
        image_paths: List of paths to images to include in the video
        duration_per_image: How long each image is displayed in seconds (default: 3.0)
        transition_duration: Duration of fade transitions in seconds (default: 0.5)
        output_fps: Frames per second for output video (default: 24)
    
    Returns:
        JSON string with status and file information
    
    Examples:
        - "Create a video from these 5 product images"
        - "Make a slideshow video with 2 seconds per image"
    """
    if not MOVIEPY_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": "moviepy library not installed. Run: pip install moviepy"
        })
    
    try:
        # Validate inputs
        if not image_paths or len(image_paths) < 2:
            return json.dumps({
                "status": "error",
                "message": "Need at least 2 images to create a video montage"
            })

        # Clamp transition to a safe value
        safe_transition = max(0.0, min(transition_duration, duration_per_image / 2))

        # Verify all images exist
        for img_path in image_paths:
            if not Path(img_path).exists():
                return json.dumps({
                    "status": "error",
                    "message": f"Image not found: {img_path}"
                })

        # Create video clips from images
        clips = []
        for idx, img_path in enumerate(image_paths):
            clip = ImageClip(img_path).set_duration(duration_per_image)
            if idx > 0 and safe_transition > 0:
                clip = clip.crossfadein(safe_transition)
            clips.append(clip)

        # Concatenate with crossfade transitions
        padding = -safe_transition if safe_transition > 0 else 0
        final_clip = concatenate_videoclips(clips, method="compose", padding=padding)

        # Save video
        filename = f"montage_{uuid.uuid4().hex[:8]}.mp4"
        filepath = OUTPUT_DIR / filename
        
        final_clip.write_videofile(
            str(filepath),
            fps=output_fps,
            codec='libx264',
            audio=False,
            verbose=False,
            logger=None
        )
        
        # Clean up
        final_clip.close()
        for clip in clips:
            clip.close()
        
        total_duration = len(image_paths) * duration_per_image
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "num_images": len(image_paths),
            "total_duration": f"{total_duration:.1f}s",
            "fps": output_fps
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to create video montage: {str(e)}"
        })

def text_to_speech(
    text: str,
    voice_speed: int = 150,
    voice_id: int = 0,
    output_format: str = "mp3"
) -> str:
    
    if not TTS_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": "pyttsx3 library not installed. Run: pip install pyttsx3"
        })
    
    try:
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        voices = engine.getProperty('voices')
        if voice_id < len(voices):
            engine.setProperty('voice', voices[voice_id].id)
        
        # Set speech rate (constrain to reasonable range)
        speed = max(100, min(300, voice_speed))
        engine.setProperty('rate', speed)
        
        # Generate filename
        extension = "mp3" if output_format == "mp3" else "wav"
        filename = f"speech_{uuid.uuid4().hex[:8]}.{extension}"
        filepath = OUTPUT_DIR / filename
        
        # Save to file
        engine.save_to_file(text, str(filepath))
        engine.runAndWait()
        
        # Get word count for duration estimate
        word_count = len(text.split())
        estimated_duration = (word_count / speed) * 60  # Convert to seconds
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "word_count": word_count,
            "estimated_duration": f"{estimated_duration:.1f}s",
            "voice_speed": speed,
            "format": extension
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to generate speech: {str(e)}"
        })

# Optional dependencies (safe guards)
try:
    from moviepy.editor import ImageClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except Exception:
    MOVIEPY_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

# Map tool names to functions
TOOLS = {
    "generate_thumbnail": generate_thumbnail,
    "generate_qr_code": generate_qr_code,
    "create_social_card": create_social_card,
    "create_video_montage": create_video_montage,
    "text_to_speech": text_to_speech
}


class DirectContentStudioAgent:

    def __init__(self):
        self.model_name = "gpt-4o-mini"
        print(f">> Using model: {self.model_name}")
        print(f">> Available tools: {list(TOOLS.keys())}")
    
    def get_tool_definitions(self):
        """Get OpenAI function definitions"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_thumbnail",
                    "description": "Generate a custom thumbnail image with text overlay",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "The text to display on the thumbnail"},
                            "width": {"type": "integer", "description": "Image width in pixels", "default": 1280},
                            "height": {"type": "integer", "description": "Image height in pixels", "default": 720},
                            "background_color": {"type": "string", "description": "Background color in hex format", "default": "#FF6B6B"},
                            "text_color": {"type": "string", "description": "Text color in hex format", "default": "#FFFFFF"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_qr_code",
                    "description": "Generate a customized QR code for URLs or text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "string", "description": "The data to encode (URL, text, etc.)"},
                            "size": {"type": "integer", "description": "Size of each QR code box in pixels", "default": 10},
                            "fill_color": {"type": "string", "description": "QR code color", "default": "black"},
                            "back_color": {"type": "string", "description": "Background color", "default": "white"}
                        },
                        "required": ["data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_social_card",
                    "description": "Create a social media preview card image",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Main heading text"},
                            "subtitle": {"type": "string", "description": "Secondary text", "default": ""},
                            "image_path": {"type": "string", "description": "Path to background image", "default": ""},
                            "platform": {"type": "string", "description": "twitter, facebook, linkedin, instagram", "default": "twitter"},
                            "theme": {"type": "string", "description": "dark, light, colorful", "default": "dark"}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_video_montage",
                    "description": "Create a video montage from images with transitions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_paths": {"type": "array", "items": {"type": "string"}, "description": "List of image paths"},
                            "duration_per_image": {"type": "number", "description": "Seconds per image", "default": 3.0},
                            "transition_duration": {"type": "number", "description": "Fade transition seconds", "default": 0.5},
                            "output_fps": {"type": "integer", "description": "Frames per second", "default": 24}
                        },
                        "required": ["image_paths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "text_to_speech",
                    "description": "Convert text to a speech audio file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to convert"},
                            "voice_speed": {"type": "integer", "description": "Words per minute", "default": 150},
                            "voice_id": {"type": "integer", "description": "Voice selection index", "default": 0},
                            "output_format": {"type": "string", "description": "mp3 or wav", "default": "mp3"}
                        },
                        "required": ["text"]
                    }
                }
            }
        ]
    
    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool directly"""
        if tool_name in TOOLS:
            return TOOLS[tool_name](**arguments)
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unknown tool: {tool_name}"
            })
    
    async def process_query(self, user_query: str, max_iterations: int = 10) -> str:
        """Process a user query"""
        tools = self.get_tool_definitions()
        messages = [{"role": "user", "content": user_query}]
        
        print(f"\n>> Sending query to OpenAI...")
        
        for iteration in range(max_iterations):
            print(f"\n>> Iteration {iteration + 1}/{max_iterations}")
            
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                )
                
                response_message = response.choices[0].message
                
                if response_message.tool_calls:
                    messages.append(response_message)
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        print(f"   >> Calling: {function_name}")
                        print(f"      Args: {json.dumps(function_args, indent=2)[:150]}...")
                        
                        result = self.call_tool(function_name, function_args)
                        print(f"      >> Done: {result[:150]}...")
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result,
                        })
                    continue
                
                elif response_message.content:
                    print(f"\n>> Completed in {iteration + 1} iterations")
                    return response_message.content
                
                else:
                    return "No response from agent"
                        
            except Exception as e:
                error_str = str(e)
                if "insufficient_quota" in error_str:
                    return "CREDITS: Out of credits! Check https://platform.openai.com/usage"
                elif "rate" in error_str.lower():
                    return "RATE: Rate limit. Wait 1 minute."
                else:
                    return f"ERROR: {error_str[:200]}"
        
        return "Max iterations reached"
    
    async def interactive_mode(self):
        """Run interactive chat mode"""
        print("\n" + "=" * 70)
        print("\nWhat would you like to create?")
        print("\nExamples:")
        print("  * 'Create a blue thumbnail saying Hello World'")
        print("  * 'Make a QR code for https://google.com'")
        print("  * 'Generate a red thumbnail for AI Tutorial'")
        print("\nType 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = await self.process_query(user_input)
                print(f"\n>> Agent: {response}\n")
                print("-" * 70)
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nERROR: {str(e)}\n")


async def main():
    """Main entry point"""
    agent = DirectContentStudioAgent()
    await agent.interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")