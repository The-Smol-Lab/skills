---
name: nano-banana-pro
description: Generate and edit images using OpenRouter API with the Gemini image generation model (google/gemini-3-pro-image-preview). Use this skill when creating images from text prompts, editing existing images, applying style transfers, generating logos with text, creating stickers, product mockups, composing multiple images, or any image generation/manipulation task. Supports text-to-image, image editing, multi-turn refinement, and composition from multiple reference images.
---

# Nano Banana Pro

Generate and edit images using OpenRouter API with Google's Gemini model. The environment variable `OPENROUTER_API_KEY` must be set.

## Default Model

| Model | Resolution | Best For |
|-------|------------|----------|
| `google/gemini-3-pro-image-preview` | 1K-4K | All image generation (default) |

## Quick Reference

### Default Settings
- **Model:** `google/gemini-3-pro-image-preview`
- **Resolution:** 1K (default, options: 1K, 2K, 4K)
- **Aspect Ratio:** 1:1 (default)

### Available Aspect Ratios
`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

### Available Resolutions
`1K` (default), `2K`, `4K`

## Core API Pattern

```python
import os
import requests
import json
import base64

api_key = os.environ["OPENROUTER_API_KEY"]

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "google/gemini-3-pro-image-preview",
        "messages": [{"role": "user", "content": "Your prompt here"}],
        "modalities": ["image", "text"],
    }
)

result = response.json()
if result.get("choices"):
    message = result["choices"][0]["message"]
    if message.get("images"):
        for img in message["images"]:
            image_url = img["image_url"]["url"]  # Base64 data URL
            # Decode and save
            base64_data = image_url.split(",", 1)[1]
            with open("output.png", "wb") as f:
                f.write(base64.b64decode(base64_data))
```

## Custom Resolution & Aspect Ratio

```python
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "google/gemini-3-pro-image-preview",
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": "16:9",  # Wide format
            "image_size": "2K"       # Higher resolution
        }
    }
)
```

## Editing Images

Pass existing images as base64 data URLs with text prompts:

```python
import base64

# Encode input image
with open("input.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")
image_url = f"data:image/png;base64,{image_data}"

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "google/gemini-3-pro-image-preview",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Add a sunset to this scene"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        "modalities": ["image", "text"],
    }
)
```

## Multiple Reference Images (Up to 14)

Combine elements from multiple sources:

```python
# Build content with multiple images
content = [{"type": "text", "text": "Create a group photo of these people in an office"}]

for img_path in ["person1.png", "person2.png", "person3.png"]:
    with open(img_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{data}"}
    })

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "google/gemini-3-pro-image-preview",
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
    }
)
```

## CLI Scripts

### Generate Image
```bash
python scripts/generate_image.py "A sunset over mountains" output.png --aspect 16:9 --size 2K
```

### Edit Image
```bash
python scripts/edit_image.py input.png "Add a rainbow in the sky" output.png
```

### Compose Images
```bash
python scripts/compose_images.py "Combine these into a group photo" output.png person1.png person2.png
```

### Interactive Chat
```bash
python scripts/multi_turn_chat.py --output-dir ./images
# Commands: /save [name], /load <path>, /clear, /quit
```

## Prompting Best Practices

### Photorealistic Scenes
Include camera details: lens type, lighting, angle, mood.
> "A photorealistic close-up portrait, 85mm lens, soft golden hour light, shallow depth of field"

### Stylized Art
Specify style explicitly:
> "A kawaii-style sticker of a happy red panda, bold outlines, cel-shading, white background"

### Text in Images
Be explicit about font style and placement:
> "Create a logo with text 'Daily Grind' in clean sans-serif, black and white, coffee bean motif"

### Product Mockups
Describe lighting setup and surface:
> "Studio-lit product photo on polished concrete, three-point softbox setup, 45-degree angle"

## Response Format

OpenRouter returns images as base64-encoded data URLs:

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Here's your image...",
      "images": [{
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,iVBORw0KGgo..."}
      }]
    }
  }]
}
```

## Notes

- Images are returned as PNG format by default
- All generated images include SynthID watermarks
- For editing, describe changes conversationally—the model understands semantic masking
- Default to 1K resolution for speed; use 2K/4K when quality is critical
- Maximum 14 reference images for composition tasks
