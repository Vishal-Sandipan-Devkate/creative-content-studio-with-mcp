# Creative Content Studio (Client + Server)

An AI-powered creative content toolkit with a local MCP server and a client that invokes tools to generate multimedia content.

## Features

- `generate_thumbnail`: Text-based thumbnail images  
- `generate_qr_code`: Custom QR codes  
- `create_social_card`: Social media preview cards  
- `create_video_montage`: Image-to-video slideshow (optional)  
- `text_to_speech`: Voiceover audio (optional)

## Requirements

- Python 3.8+
- OpenAI API key
- Packages listed in requirements.txt

## Setup

1) Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Create a .env file in the project root
```env
OPENAI_API_KEY=your_openai_key_here
```

## Run (Server)

Start the MCP server in one terminal:
```bash
python content_studio_server.py
```

## Run (Client)

In a second terminal:
```bash
python content_studio_client_openai.py
```

Example prompts:
```
Create a blue thumbnail saying Hello World
Make a QR code for https://google.com
Generate a Twitter social card for my blog post
```

## Output

Generated files are saved to:
```
content_outputs/
```

## Notes

- Video montage requires moviepy
- Text-to-speech requires pyttsx3
- If optional packages are missing, the tool returns a clear error message