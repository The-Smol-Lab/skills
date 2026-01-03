#!/usr/bin/env python3
"""
Edit existing images using OpenRouter API.

Usage:
    python edit_image.py input.png "edit instruction" output.png [options]

Examples:
    python edit_image.py photo.png "Add a rainbow in the sky" edited.png
    python edit_image.py room.jpg "Change the sofa to red leather" room_edited.jpg
    python edit_image.py portrait.png "Make it look like a Van Gogh painting" artistic.png

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


def encode_image_to_base64(file_path: str | Path) -> str:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Image not found: {file_path}")
    
    mime_type = get_mime_type(file_path)
    
    with open(file_path, "rb") as f:
        image_data = f.read()
    
    base64_data = base64.b64encode(image_data).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


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
        description="Edit images using OpenRouter API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("instruction", help="Edit instruction")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--aspect", "-a",
        choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        help="Output aspect ratio"
    )
    parser.add_argument(
        "--size", "-s",
        choices=["1K", "2K", "4K"],
        help="Output resolution"
    )
    
    args = parser.parse_args()
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    input_image = Path(args.input)
    if not input_image.exists():
        raise FileNotFoundError(f"Input image not found: {input_image}")
    
    try:
        image_data_url = encode_image_to_base64(input_image)
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": args.instruction},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        }]
        
        payload = {
            "model": DEFAULT_MODEL,
            "messages": messages,
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
            raise RuntimeError("No image was generated. Check your instruction and try again.")
        
        path = save_image(images[0], args.output)
        
        print(f"Edited image saved to: {path}")
        if text:
            print(f"Model response: {text}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
