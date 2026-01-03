#!/usr/bin/env python3
"""
Generate images from text prompts using OpenRouter API.

Usage:
    python generate_image.py "prompt" output.png [--aspect RATIO] [--size SIZE]

Examples:
    python generate_image.py "A cat in space" cat.png
    python generate_image.py "A logo for Acme Corp" logo.png --aspect 1:1
    python generate_image.py "Epic landscape" landscape.png --aspect 16:9 --size 2K

Environment:
    OPENROUTER_API_KEY - Required API key
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Literal

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"
AspectRatio = Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
ImageSize = Literal["1K", "2K", "4K"]


def get_mime_type(file_path: str | Path) -> str:
    file_path = str(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/png")
    return mime_type


def decode_base64_image(data_url: str) -> tuple[bytes, str]:
    if data_url.startswith("data:"):
        header, base64_data = data_url.split(",", 1)
        mime_part = header.split(";")[0]
        mime_type = mime_part.replace("data:", "")
    else:
        base64_data = data_url
        mime_type = "image/png"
    
    ext_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
    }
    extension = ext_map.get(mime_type, ".png")
    
    binary_data = base64.b64decode(base64_data)
    return binary_data, extension


def save_image(data_url: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    binary_data, _ = decode_base64_image(data_url)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        f.write(binary_data)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images from text prompts using OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("prompt", help="Text prompt describing the image")
    parser.add_argument("output", help="Output file path (e.g., output.png)")
    parser.add_argument(
        "--aspect", "-a",
        choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        help="Aspect ratio"
    )
    parser.add_argument(
        "--size", "-s",
        choices=["1K", "2K", "4K"],
        help="Image resolution"
    )
    
    args = parser.parse_args()
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [{"role": "user", "content": args.prompt}],
            "modalities": ["image", "text"],
        }
        
        image_config = {}
        if args.aspect:
            image_config["aspect_ratio"] = args.aspect
        if args.size:
            image_config["image_size"] = args.size
        
        if image_config:
            payload["image_config"] = image_config
        
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://opencode.ai",
                "X-Title": "OpenCode CLI Agent",
            },
            json=payload,
        )
        
        if response.status_code != 200:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error']}"
            except (json.JSONDecodeError, KeyError):
                error_msg += f": {response.text}"
            raise RuntimeError(error_msg)
        
        result = response.json()
        text = None
        images = []
        
        if result.get("choices"):
            message = result["choices"][0].get("message", {})
            text = message.get("content")
            
            if message.get("images"):
                for img in message["images"]:
                    if "image_url" in img and "url" in img["image_url"]:
                        images.append(img["image_url"]["url"])
        
        if not images:
            raise RuntimeError("No image was generated. Check your prompt and try again.")
        
        path = save_image(images[0], args.output)
        
        print(f"Image saved to: {path}")
        if text:
            print(f"Model response: {text}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
