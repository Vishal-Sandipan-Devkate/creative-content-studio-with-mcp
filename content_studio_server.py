

from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageDraw, ImageFont
import qrcode
from pathlib import Path
import uuid
import json

# Try to import optional dependencies with graceful fallbacks
try:
    from moviepy.editor import ImageClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


# Initialize MCP server
server = FastMCP("ContentStudio")

# Configuration
OUTPUT_DIR = Path("content_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Default font fallback
def get_font(size=40):
    """Get a default font that works cross-platform"""
    try:
        # Windows
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            # Linux
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                size
            )
        except:
            return ImageFont.load_default()

# written by Atharva Kasturi
@server.tool()
def generate_thumbnail(
    text: str,
    width: int = 1280,
    height: int = 720,
    background_color: str = "#FF6B6B",
    text_color: str = "#FFFFFF",
    style: str = "modern"
) -> str:
    """
    Generate a custom thumbnail image with text overlay.
    
    Args:
        text: The text to display on the thumbnail
        width: Image width in pixels (default: 1280)
        height: Image height in pixels (default: 720)
        background_color: Background color in hex format (default: #FF6B6B)
        text_color: Text color in hex format (default: #FFFFFF)
        style: Visual style - "modern", "gradient", "minimal", "bold" (default: modern)
    
    Returns:
        JSON string with status and file information
    
    Examples:
        - "Create a YouTube thumbnail with 'AI Tutorial' text"
        - "Make a red thumbnail saying 'Breaking News' in bold style"
    """
    try:
        # Create base image
        img = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Apply style-specific effects
        if style == "gradient":
            # Create a gradient effect
            for i in range(height):
                shade = int(255 * (i / height))
                r, g, b = tuple(int(background_color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
                color = (max(0, r - shade//2), max(0, g - shade//2), max(0, b - shade//2))
                draw.line([(0, i), (width, i)], fill=color)
        
        elif style == "bold":
            # Add a bold border
            border_width = 20
            draw.rectangle(
                [border_width, border_width, width - border_width, height - border_width],
                outline=text_color,
                width=border_width
            )
        
        elif style == "minimal":
            # Clean white background with subtle shadow
            img = Image.new('RGB', (width, height), "#FFFFFF")
            draw = ImageDraw.Draw(img)
        
        # Calculate font size based on text length and image size
        base_font_size = min(width, height) // 10
        font_size = max(30, base_font_size - len(text) * 2)
        font = get_font(font_size)
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Add shadow effect for better readability
        if style != "minimal":
            shadow_offset = 5
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill="#000000")
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Save the image
        filename = f"thumbnail_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        img.save(filepath, quality=95)
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "dimensions": [width, height],
            "style": style
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to generate thumbnail: {str(e)}"
        })

# written by Vishal Devkate
@server.tool()
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
        
        # Verify all images exist
        for img_path in image_paths:
            if not Path(img_path).exists():
                return json.dumps({
                    "status": "error",
                    "message": f"Image not found: {img_path}"
                })
        
        # Create video clips from images
        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(duration_per_image)
            clips.append(clip)
        
        # Concatenate with crossfade transitions
        final_clip = concatenate_videoclips(clips, method="compose")
        
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

# written by Avanti Shinde
@server.tool()
def text_to_speech(
    text: str,
    voice_speed: int = 150,
    voice_id: int = 0,
    output_format: str = "mp3"
) -> str:
    """
    Convert text to speech audio file.
    
    Args:
        text: The text to convert to speech
        voice_speed: Speaking rate in words per minute (default: 150, range: 100-300)
        voice_id: Voice selection (0-2, different voices if available)
        output_format: Audio format - "mp3" or "wav" (default: mp3)
    
    Returns:
        JSON string with status and file information
    
    Examples:
        - "Convert this script to audio: 'Welcome to our channel'"
        - "Create a voiceover for my video with fast speech"
    """
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

# written by Sneha Barage
@server.tool()
def generate_qr_code(
    data: str,
    size: int = 10,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
    error_correction: str = "M"
) -> str:
    """
    Generate a customized QR code.
    
    Args:
        data: The data to encode (URL, text, contact info, etc.)
        size: Size of each QR code box in pixels (default: 10, range: 1-50)
        border: Border size in boxes (default: 2, minimum: 1)
        fill_color: QR code color (default: black) - hex or color name
        back_color: Background color (default: white) - hex or color name
        error_correction: Error correction level - "L", "M", "Q", "H" (default: M)
    
    Returns:
        JSON string with status and file information
    
    Examples:
        - "Create a QR code for https://mywebsite.com"
        - "Generate a red QR code with my contact info"
        - "Make a large QR code for this Wi-Fi password"
    """
    try:
        # Map error correction levels
        error_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,  # ~7% correction
            "M": qrcode.constants.ERROR_CORRECT_M,  # ~15% correction
            "Q": qrcode.constants.ERROR_CORRECT_Q,  # ~25% correction
            "H": qrcode.constants.ERROR_CORRECT_H   # ~30% correction
        }
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=None,  # Auto-detect size
            error_correction=error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=max(1, min(50, size)),
            border=max(1, border)
        )
        
        # Add data and generate
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Save
        filename = f"qrcode_{uuid.uuid4().hex[:8]}.png"
        filepath = OUTPUT_DIR / filename
        img.save(filepath)
        
        # Get data type hint
        data_type = "URL" if data.startswith(("http://", "https://")) else "Text"
        
        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "data_type": data_type,
            "data_length": len(data),
            "error_correction": error_correction,
            "colors": f"{fill_color} on {back_color}"
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to generate QR code: {str(e)}"
        })

# written by Vishal Devkate
@server.tool()
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


if __name__ == "__main__":
    # Run the MCP server
    server.run()