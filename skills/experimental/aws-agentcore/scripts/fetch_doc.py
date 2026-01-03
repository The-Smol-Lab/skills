#!/usr/bin/env python3
"""
Fetch full AgentCore documentation by URL.

Adapted from the amazon-bedrock-agentcore-mcp-server implementation.

Usage:
    python fetch_doc.py <url>

Examples:
    python fetch_doc.py "https://aws.github.io/bedrock-agentcore-starter-toolkit/getting-started/"
    python fetch_doc.py "/getting-started/deploy-agent/"
"""

import argparse
import html
import json
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Dict, Optional


# Configuration
TIMEOUT = 30.0
USER_AGENT = 'agentcore-skill-docs/1.0'

# Allowed domain prefixes for URL validation
ALLOWED_DOMAINS = [
    'https://aws.github.io/bedrock-agentcore-starter-toolkit',
    'https://strandsagents.com/',
    'https://docs.aws.amazon.com/',
    'https://boto3.amazonaws.com/v1/documentation/',
]

# Regex patterns
_HTML_BLOCK = re.compile(r'(?is)<(script|style|noscript).*?>.*?</\1>')
_TAG = re.compile(r'(?s)<[^>]+>')
_TITLE_TAG = re.compile(r'(?is)<title[^>]*>(.*?)</title>')
_H1_TAG = re.compile(r'(?is)<h1[^>]*>(.*?)</h1>')
_META_OG = re.compile(r'(?is)<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']')
_WHITESPACE = re.compile(r'\s+')


@dataclass
class Page:
    """Represents a fetched documentation page."""
    url: str
    title: str
    content: str


def is_url_allowed(url: str) -> bool:
    """Check if URL is from an allowed domain."""
    if not url or not isinstance(url, str):
        return False
    for prefix in ALLOWED_DOMAINS:
        if url.startswith(prefix):
            return True
    return False


def normalize_url(url: str) -> Optional[str]:
    """Normalize and validate a URL."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://aws.github.io/bedrock-agentcore-starter-toolkit' + url
    return url if is_url_allowed(url) else None


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode('utf-8', errors='ignore')


def html_to_text(raw_html: str) -> str:
    """Convert HTML to plain text."""
    stripped = _HTML_BLOCK.sub('', raw_html)
    stripped = _TAG.sub(' ', stripped)
    stripped = html.unescape(stripped)
    lines = [ln.strip() for ln in stripped.splitlines()]
    return '\n'.join(ln for ln in lines if ln)


def extract_html_title(raw_html: str) -> Optional[str]:
    """Extract title from HTML content using multiple strategies."""
    match = _TITLE_TAG.search(raw_html)
    if match:
        return html.unescape(match.group(1)).strip()
    match = _META_OG.search(raw_html)
    if match:
        return html.unescape(match.group(1)).strip()
    match = _H1_TAG.search(raw_html)
    if match:
        inner = _TAG.sub(' ', match.group(1))
        return html.unescape(inner).strip()
    return None


def title_from_url(url: str) -> str:
    """Generate a human-readable title from a URL path."""
    path = url.split('://', 1)[-1]
    parts = [p for p in path.split('/') if p]
    if parts and parts[-1].startswith('index.'):
        parts = parts[:-1]
    slug = parts[-1] if parts else path
    slug = slug.replace('-', ' ').replace('_', ' ').strip()
    return slug.title() or 'Documentation'


def fetch_agentcore_doc(uri: str) -> Dict:
    """
    Fetch full document content by URL.

    Args:
        uri: Document URI (supports http/https URLs or relative paths)

    Returns:
        Dictionary with url, title, content (or error if failed)
    """
    url = normalize_url(uri)

    if not url:
        return {
            'error': f'URL not allowed. Must be from: {", ".join(ALLOWED_DOMAINS)}',
            'url': uri
        }

    try:
        raw = fetch_url(url)
        lower = raw.lower()

        if '<html' in lower or '<head' in lower or '<body' in lower:
            extracted_title = extract_html_title(raw)
            content = html_to_text(raw)
            title = extracted_title or title_from_url(url)
        else:
            title = title_from_url(url)
            content = raw

        return {
            'url': url,
            'title': title,
            'content': content,
        }

    except urllib.error.HTTPError as e:
        return {
            'error': f'HTTP error {e.code}: {e.reason}',
            'url': url
        }
    except urllib.error.URLError as e:
        return {
            'error': f'URL error: {e.reason}',
            'url': url
        }
    except Exception as e:
        return {
            'error': f'Fetch failed: {str(e)}',
            'url': url
        }


def main():
    parser = argparse.ArgumentParser(
        description='Fetch full AgentCore documentation by URL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python fetch_doc.py "https://aws.github.io/bedrock-agentcore-starter-toolkit/getting-started/"
    python fetch_doc.py "/getting-started/deploy-agent/"
    python fetch_doc.py "/platform/memory/"

Allowed domains:
    - https://aws.github.io/bedrock-agentcore-starter-toolkit
    - https://strandsagents.com/
    - https://docs.aws.amazon.com/
    - https://boto3.amazonaws.com/v1/documentation/
        '''
    )
    parser.add_argument('url', help='Document URL (absolute or relative to AgentCore docs)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    result = fetch_agentcore_doc(args.url)

    if args.json or 'error' in result:
        print(json.dumps(result, indent=2))
    else:
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print("-" * 60)
        print(result['content'])


if __name__ == '__main__':
    main()
