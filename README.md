# Creative Content Studio

An AI-powered creative content toolkit that uses OpenAI's GPT models to generate multimedia content through an interactive chat interface. 

## Features

- 📸 **Generate Thumbnail**: Create eye-catching thumbnail images with custom text and colors
- 🔗 **Generate QR Code**: Generate customizable QR codes for URLs or text data
- 🎨 **Create Social Card**: Design social media preview cards (Open Graph/Twitter Card style)
- 🎬 **Create Video Montage**: Transform images into video slideshows with transitions *(optional)*
- 🔊 **Text-to-Speech**: Convert text into audio voiceovers *(optional)*

## Projuect Structure

```
con_sol_stu/
├── .venv/                              # Virtual environment
├── content_outputs/                    # Generated content (auto-created)
├── content_studio_server.py            # MCP server with 5 tools
├── content_studio_client_openai.py     # AI agent client 
├── demo.py                             # Test script
├── requirements.txt                    # Python dependencies
├── .env                                # Your API key
└── README.md                           # This file
```
## Requirements


### Core Dependencies
- **Python 3.8+** (tested with 3.11)
- **OpenAI API key** with available credits

### Required Packages
```
openai>=2.16.0          # OpenAI API client
pillow>=11.3.0          # Image processing
qrcode>=8.2             # QR code generation
python-dotenv>=1.2.1    # Environment variable management
```

### Optional Packages
```
moviepy>=2.2.1          # For video montage feature
pyttsx3>=2.99           # For text-to-speech feature
```

### Complete Dependency Tree
Based on the installed packages, here are the full dependencies:

**Core Runtime:**
- `openai v2.16.0` → httpx, pydantic, jiter, distro, anyio
- `pillow v11.3.0` → (standalone, used by qrcode and moviepy)
- `qrcode v8.2` → colorama
- `python-dotenv v1.2.1` → (standalone)

**Optional - Video Generation:**
- `moviepy v2.2.1` → imageio, imageio-ffmpeg, numpy, decorator, proglog

**Optional - Text-to-Speech:**
- `pyttsx3 v2.99` → pywin32, comtypes (Windows-specific)

**Development Tools (if needed):**
- `pytest v9.0.2` → for testing
- `black v26.1.0` → for code formatting
- `anthropic v0.77.0` → if using Claude API instead

## Installation

### 1. Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Core Dependencies


Ensure you have these files:
```
con_sol_stu/
├── content_studio_server.py
├── content_studio_client_openai.py
├── demo.py
├── requirements.txt
├── .env
└── README.md
```

**Minimal Installation (thumbnails + QR codes only):**
```bash
pip install openai pillow qrcode python-dotenv
```

**Full Installation (all features):**
```bash
pip install openai pillow qrcode python-dotenv moviepy pyttsx3
```

**Or use requirements file:**
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Get your API key:**
- Visit https://platform.openai.com/api-keys
- Create a new secret key
- Ensure your account has available credits

## Usage

### Start the Application

```bash
python demo.py
```

### Interactive Mode

Once started, you'll see:
```

What would you like to create?

Examples:
  * 'Create a blue thumbnail saying Hello World'
  * 'Make a QR code for https://google.com'
  * 'Generate a red thumbnail for AI Tutorial'

Type 'quit' to exit
```

### Example Commands

**Thumbnails:**
```
You: Create a thumbnail with "New Video" in red text
You: Make a 1920x1080 thumbnail saying "Subscribe Now"
You: Generate a blue thumbnail for my coding tutorial
```

**QR Codes:**
```
You: Generate a QR code for https://example.com
You: Create a red QR code for my website
You: Make a large QR code with the text "Contact: +1234567890"
```

**Social Media Cards:**
```
You: Create a Twitter card for my blog post about AI
You: Make a dark-themed LinkedIn card saying "Join Our Team"
You: Generate a Facebook preview card with colorful theme
```

**Video Montages** *(requires moviepy)*:
```
You: Create a video from these 3 images with 2 seconds per image
You: Make a slideshow video with smooth transitions
```

**Text-to-Speech** *(requires pyttsx3)*:
```
You: Convert this to audio: "Welcome to my channel"
You: Generate voiceover with fast speech for this script
```

## Output

All generated files are saved to:
```
content_outputs/
├── thumbnail_abc12345.png
├── qrcode_def67890.png
├── social_card_twitter_ghi11223.png
├── montage_jkl44556.mp4
└── speech_mno77889.mp3
```

File naming convention: `{type}_{unique_id}.{ext}`


### Key Components

**1. Tool Implementations** (`TOOLS` dictionary)
- Each function returns JSON with status and file information
- Error handling built into each tool
- Graceful degradation for missing optional dependencies

**2. AI Agent** (`DirectContentStudioAgent`)
- Uses OpenAI's function calling feature
- Manages multi-turn conversations
- Handles tool execution and result formatting

**3. OpenAI Integration**
- Model: `gpt-4o-mini` (configurable)
- Function calling with automatic tool selection
- Iterative processing for complex requests

## Troubleshooting

### API Key Issues

**Error: `OPENAI_API_KEY not found in .env`**
```bash
# Ensure .env file exists in project root
# Verify it contains: OPENAI_API_KEY=sk-...
```

**Error: `insufficient_quota`**
```bash
# Your OpenAI account is out of credits
# Visit: https://platform.openai.com/usage
# Add billing method or purchase credits
```

### Missing Dependencies

**Error: `moviepy library not installed`**
```bash
pip install moviepy
```

**Error: `pyttsx3 library not installed`**
```bash
pip install pyttsx3
```

**Windows TTS Issues:**
```bash
# pyttsx3 requires Windows-specific packages
pip install pywin32 comtypes
```

### Font Issues

If thumbnails have font rendering problems:

**Windows:**
- Ensure Arial font is available (default on Windows)
- Install additional fonts if needed

**Linux:**
```bash
sudo apt-get install fonts-dejavu-core
```

**Mac:**
- System fonts should work by default

### Permission Errors

**Error: Cannot create output directory**
```bash
# Ensure write permissions in project folder
# Try running terminal as administrator (Windows)
# Or use sudo on Linux/Mac if needed
```

## Configuration

### Model Selection

Change the AI model in the code:
```python
class DirectContentStudioAgent:
    def __init__(self):
        self.model_name = "gpt-4o-mini"  # or "gpt-4o", "gpt-4-turbo"
```

### Output Directory

Change output location:
```python
OUTPUT_DIR = Path("content_outputs")  # Change to your preferred path
```

### Default Dimensions

Modify default image sizes:
```python
def generate_thumbnail(
    text: str,
    width: int = 1280,  # Change default width
    height: int = 720,  # Change default height
    ...
)
```

## API Costs

Approximate costs with `gpt-4o-mini`:
- Simple request (1 tool call): ~$0.001
- Complex request (5 tool calls): ~$0.005

**Monitor usage:** https://platform.openai.com/usage


## Limitations

- **No persistent memory**: Each session starts fresh
- **Rate limits**: Subject to OpenAI API rate limits
- **File size**: Large images may slow processing
- **Video encoding**: Requires sufficient disk space
- **Windows paths**: Works best with absolute paths on Windows


## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request



## Credits

- **OpenAI**: GPT models and API
- **Pillow**: Image processing library
- **qrcode**: QR code generation
- **moviepy**: Video editing capabilities
- **pyttsx3**: Text-to-speech engine

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [QRCode Documentation](https://github.com/lincolnloop/python-qrcode)
