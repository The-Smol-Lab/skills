#!/usr/bin/env python3
"""
Interactive multi-turn image generation and refinement using OpenRouter API.

Usage:
    python multi_turn_chat.py [--output-dir DIR]

This starts an interactive session where you can:
- Generate images from prompts
- Iteratively refine images through conversation
- Load existing images for editing
- Save images at any point

Commands:
    /save [filename]  - Save current image
    /load <path>      - Load an image into the conversation
    /clear            - Start fresh conversation
    /quit             - Exit

Environment:
    OPENROUTER_API_KEY - Required API key
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"


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


class ImageChat:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._history: list[dict] = []
        self.current_image_url: str | None = None
    
    def send(
        self,
        message: str,
        image_path: str | Path | None = None,
    ) -> tuple[str | None, str | None]:
        if image_path:
            image_data_url = encode_image_to_base64(image_path)
            content = [
                {"type": "text", "text": message},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]
        else:
            content = message
        
        self._history.append({"role": "user", "content": content})
        
        payload = {
            "model": self.model,
            "messages": self._history,
            "modalities": ["image", "text"],
        }
        
        response = requests.post(API_URL, headers=self._headers, json=payload)
        
        if response.status_code != 200:
            raise RuntimeError(f"API request failed: {response.text}")
        
        result = response.json()
        
        text = None
        image_url = None
        
        if result.get("choices"):
            message_data = result["choices"][0].get("message", {})
            text = message_data.get("content")
            
            if message_data.get("images"):
                image_url = message_data["images"][0]["image_url"]["url"]
                self.current_image_url = image_url
            
            self._history.append({
                "role": "assistant",
                "content": text if text is not None else "",
            })
        
        return image_url, text
    
    def save_current_image(self, output_path: str | Path) -> Path | None:
        if not self.current_image_url:
            return None
        return save_image(self.current_image_url, output_path)
    
    def reset(self):
        self._history = []
        self.current_image_url = None


class InteractiveChat:
    def __init__(self, output_dir: str = ".", api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENROUTER_API_KEY not set")
        
        self.chat = ImageChat(self.api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_count = 0
        self.loaded_image_path: str | None = None
    
    def save_current(self, filename: str | None = None) -> str | None:
        if not self.chat.current_image_url:
            return None
        
        if filename is None:
            self.image_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}_{self.image_count}.png"
        
        filepath = self.output_dir / filename
        save_image(self.chat.current_image_url, filepath)
        return str(filepath)
    
    def load_image(self, path: str) -> bool:
        path_obj = Path(path)
        if not path_obj.exists():
            return False
        self.loaded_image_path = path
        return True
    
    def send_message(self, message: str) -> tuple[str | None, str | None]:
        image_to_send = None
        if self.loaded_image_path and not self.chat._history:
            image_to_send = self.loaded_image_path
            self.loaded_image_path = None
        
        image_url, text = self.chat.send(message, image_to_send)
        
        saved_path = None
        if image_url:
            saved_path = self.save_current()
        
        return saved_path, text
    
    def clear(self):
        self.chat.reset()
        self.loaded_image_path = None


def main():
    parser = argparse.ArgumentParser(
        description="Interactive multi-turn image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Directory to save images"
    )
    
    args = parser.parse_args()
    
    try:
        chat = InteractiveChat(output_dir=args.output_dir)
    except Exception as e:
        print(f"Error initializing: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("OpenRouter Image Chat (google/gemini-3-pro-image-preview)")
    print("Commands: /save [name], /load <path>, /clear, /quit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == "/quit":
                print("Goodbye!")
                break
            
            elif cmd == "/clear":
                chat.clear()
                print("Conversation cleared.")
                continue
            
            elif cmd == "/save":
                path = chat.save_current(arg)
                if path:
                    print(f"Image saved to: {path}")
                else:
                    print("No image to save.")
                continue
            
            elif cmd == "/load":
                if not arg:
                    print("Usage: /load <path>")
                    continue
                if chat.load_image(arg):
                    print(f"Loaded: {arg}")
                    print("You can now describe edits to make.")
                else:
                    print(f"Error: Image not found: {arg}")
                continue
            
            else:
                print(f"Unknown command: {cmd}")
                continue
        
        try:
            image_path, text = chat.send_message(user_input)
            
            if text:
                print(f"\nGemini: {text}")
            
            if image_path:
                print(f"\n[Image generated: {image_path}]")
            
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
