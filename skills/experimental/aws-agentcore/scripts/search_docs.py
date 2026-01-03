#!/usr/bin/env python3
"""
Search AgentCore documentation and return ranked results.

Adapted from the amazon-bedrock-agentcore-mcp-server implementation.
Uses TF-IDF scoring with Markdown-aware weighting.

Usage:
    python search_docs.py "your query" [--k 5]

Examples:
    python search_docs.py "memory integration"
    python search_docs.py "deployment guide" --k 10
    python search_docs.py "bedrock agentcore runtime"
"""

import argparse
import html
import json
import math
import re
import sys
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# Configuration
LLMS_TXT_URL = 'https://aws.github.io/bedrock-agentcore-starter-toolkit/llms.txt'
TIMEOUT = 30.0
USER_AGENT = 'agentcore-skill-docs/1.0'
SNIPPET_HYDRATE_MAX = 5

# Allowed domain prefixes for URL validation
ALLOWED_DOMAINS = [
    'https://aws.github.io/bedrock-agentcore-starter-toolkit',
    'https://strandsagents.com/',
    'https://docs.aws.amazon.com/',
    'https://boto3.amazonaws.com/v1/documentation/',
]

# Regex patterns
_TOKEN = re.compile(r'[A-Za-z0-9_]+')
_MD_HEADER = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
_MD_CODE_BLOCK = re.compile(r'```[\w]*\n([\s\S]*?)```')
_MD_LINK = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
_MD_LINK_TEXT = re.compile(r'\[([^\]]+)\]\([^)]+\)')
_HTML_BLOCK = re.compile(r'(?is)<(script|style|noscript).*?>.*?</\1>')
_TAG = re.compile(r'(?s)<[^>]+>')
_TITLE_TAG = re.compile(r'(?is)<title[^>]*>(.*?)</title>')
_WHITESPACE = re.compile(r'\s+')
_CODE_FENCE = re.compile(r'```.*?```', re.S)

# Title boost constants
_TITLE_BOOST_EMPTY = 8
_TITLE_BOOST_SHORT = 5
_TITLE_BOOST_LONG = 3
_SHORT_PAGE_THRESHOLD = 800


@dataclass
class Page:
    """Represents a fetched documentation page."""
    url: str
    title: str
    content: str


@dataclass
class Doc:
    """A single indexed document."""
    uri: str
    display_title: str
    content: str
    index_title: str


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


def parse_llms_txt(url: str) -> List[Tuple[str, str]]:
    """Parse an llms.txt file and extract document links."""
    txt = fetch_url(url)
    links = []
    for match in _MD_LINK.finditer(txt):
        title = match.group(1).strip() or match.group(2).strip()
        doc_url = normalize_url(match.group(2).strip())
        if doc_url:
            links.append((title, doc_url))
    return links


def html_to_text(raw_html: str) -> str:
    """Convert HTML to plain text."""
    stripped = _HTML_BLOCK.sub('', raw_html)
    stripped = _TAG.sub(' ', stripped)
    stripped = html.unescape(stripped)
    lines = [ln.strip() for ln in stripped.splitlines()]
    return '\n'.join(ln for ln in lines if ln)


def extract_html_title(raw_html: str) -> Optional[str]:
    """Extract title from HTML content."""
    match = _TITLE_TAG.search(raw_html)
    if match:
        return html.unescape(match.group(1)).strip()
    return None


def fetch_and_clean(page_url: str) -> Optional[Page]:
    """Fetch a web page and return cleaned content."""
    url = normalize_url(page_url)
    if not url:
        return None
    try:
        raw = fetch_url(url)
        lower = raw.lower()
        if '<html' in lower or '<head' in lower or '<body' in lower:
            title = extract_html_title(raw) or url.rsplit('/', 1)[-1]
            content = html_to_text(raw)
        else:
            title = url.rsplit('/', 1)[-1] or url
            content = raw
        return Page(url=url, title=title, content=content)
    except Exception:
        return None


def normalize(s: str) -> str:
    """Normalize whitespace in a string."""
    return _WHITESPACE.sub(' ', s).strip()


def title_from_url(url: str) -> str:
    """Generate a human-readable title from a URL path."""
    path = url.split('://', 1)[-1]
    parts = [p for p in path.split('/') if p]
    if parts and parts[-1].startswith('index.'):
        parts = parts[:-1]
    slug = parts[-1] if parts else path
    slug = slug.replace('-', ' ').replace('_', ' ').strip()
    return slug.title() or 'Documentation'


def make_snippet(page: Optional[Page], display_title: str, max_chars: int = 300) -> str:
    """Create a contextual snippet from page content."""
    if not page or not page.content:
        return display_title

    text = page.content.strip()
    text = _CODE_FENCE.sub('', text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        first = lines[0]
        if first.startswith('#') or normalize(first).lower().startswith(normalize(display_title).lower()):
            lines = lines[1:]

    paras = []
    buf = []
    for line in lines:
        no_leading = line.lstrip()
        if no_leading.startswith('#') or no_leading.startswith(('-', '*')) or re.match(r'^\d+\.', no_leading):
            if buf:
                break
            continue
        buf.append(line)
        if len(' '.join(buf)) >= 120 or line.endswith('.'):
            paras.append(' '.join(buf))
            break

    if not paras and buf:
        paras.append(' '.join(buf))

    snippet = paras[0] if paras else display_title
    snippet = ' '.join(snippet.split())
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars - 1].rstrip() + '...'
    return snippet


class IndexSearch:
    """Lightweight inverted index with TF-IDF scoring."""

    def __init__(self):
        self.docs: List[Doc] = []
        self.doc_frequency: Dict[str, int] = {}
        self.doc_indices: Dict[str, List[int]] = {}

    def add(self, doc: Doc) -> None:
        """Add a document to the index."""
        idx = len(self.docs)
        self.docs.append(doc)
        seen = set()

        content = doc.content.lower()
        title_text = doc.index_title.lower()
        headers = ' '.join(_MD_HEADER.findall(doc.content))
        code_blocks = ' '.join(_MD_CODE_BLOCK.findall(doc.content))
        link_text = ' '.join(_MD_LINK_TEXT.findall(doc.content))

        haystack = ' '.join([
            title_text, headers.lower(), link_text.lower(),
            code_blocks.lower(), content
        ])

        for tok in _TOKEN.findall(haystack):
            self.doc_indices.setdefault(tok, []).append(idx)
            if tok not in seen:
                self.doc_frequency[tok] = self.doc_frequency.get(tok, 0) + 1
                seen.add(tok)

    def search(self, query: str, k: int = 8) -> List[Tuple[float, Doc]]:
        """Search the index and return ranked results."""

        def _title_boost_for(doc: Doc) -> int:
            n = len(doc.content)
            if n == 0:
                return _TITLE_BOOST_EMPTY
            if n < _SHORT_PAGE_THRESHOLD:
                return _TITLE_BOOST_SHORT
            return _TITLE_BOOST_LONG

        def _calculate_md_score(doc: Doc, token: str) -> float:
            content_lower = doc.content.lower()
            title_lower = doc.index_title.lower()
            content_tf = content_lower.count(token)
            title_tf = title_lower.count(token) * _title_boost_for(doc)
            header_tf = sum(h.lower().count(token) * 4 for h in _MD_HEADER.findall(doc.content))
            code_tf = sum(c.lower().count(token) * 2 for c in _MD_CODE_BLOCK.findall(doc.content))
            link_tf = sum(l.lower().count(token) * 2 for l in _MD_LINK_TEXT.findall(doc.content))
            return float(content_tf + title_tf + header_tf + code_tf + link_tf)

        q_tokens = [t.lower() for t in _TOKEN.findall(query)]
        scores: Dict[int, float] = {}
        N = max(len(self.docs), 1)

        for qt in q_tokens:
            for idx in self.doc_indices.get(qt, []):
                d = self.docs[idx]
                tf = _calculate_md_score(d, qt)
                idf = math.log((N + 1) / (1 + self.doc_frequency.get(qt, 0))) + 1.0
                scores[idx] = scores.get(idx, 0.0) + tf * idf

        ranked = sorted(
            ((score, self.docs[i]) for i, score in scores.items()),
            key=lambda x: x[0],
            reverse=True,
        )
        return ranked[:k]


def search_agentcore_docs(query: str, k: int = 5) -> List[Dict]:
    """
    Search curated AgentCore documentation and return ranked results.

    Args:
        query: Search query string
        k: Maximum number of results to return

    Returns:
        List of dicts with url, title, score, snippet
    """
    # Load and index documents
    index = IndexSearch()
    url_titles: Dict[str, str] = {}
    url_cache: Dict[str, Optional[Page]] = {}

    print(f"Loading documentation index from {LLMS_TXT_URL}...", file=sys.stderr)

    for title, url in parse_llms_txt(LLMS_TXT_URL):
        url_titles[url] = title
        url_cache[url] = None
        display_title = normalize(title)
        index_title = f"{display_title} {title_from_url(url)}"
        index.add(Doc(uri=url, display_title=display_title, content='', index_title=index_title))

    print(f"Indexed {len(index.docs)} documents. Searching...", file=sys.stderr)

    # Search
    results = index.search(query, k=k)

    # Hydrate top results with content for snippets
    for i, (_, doc) in enumerate(results[:SNIPPET_HYDRATE_MAX]):
        if url_cache.get(doc.uri) is None:
            page = fetch_and_clean(doc.uri)
            if page:
                url_cache[doc.uri] = page

    # Build response
    return_docs = []
    for score, doc in results:
        page = url_cache.get(doc.uri)
        snippet = make_snippet(page, doc.display_title)
        return_docs.append({
            'url': doc.uri,
            'title': doc.display_title,
            'score': round(score, 3),
            'snippet': snippet,
        })

    return return_docs


def main():
    parser = argparse.ArgumentParser(
        description='Search AgentCore documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python search_docs.py "memory integration"
    python search_docs.py "deployment guide" --k 10
    python search_docs.py "bedrock agentcore runtime" --k 3
        '''
    )
    parser.add_argument('query', help='Search query string')
    parser.add_argument('--k', type=int, default=5, help='Number of results (default: 5)')

    args = parser.parse_args()

    results = search_agentcore_docs(args.query, k=args.k)

    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
