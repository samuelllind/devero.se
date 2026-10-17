"""Checks the site's rules: links resolve, no third-party resources, no "Devero AB", page basics.

Usage: python3 tools/check_site.py [root]   (exit 1 and one line per problem when it fails)
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

# Devero is not a registered company, so "AB" must never follow the name.
DEVERO_AB = re.compile(r'devero\s+ab\b', re.IGNORECASE)
# Attributes that load a resource; an external one would be a third-party request.
RESOURCE_ATTRS = {('script', 'src'), ('link', 'href'), ('img', 'src'), ('source', 'src'),
                  ('iframe', 'src'), ('video', 'src'), ('audio', 'src')}


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = False
        self.title = False
        self.viewport = False
        self.text = []
        self.refs = []  # (tag, url, is_resource)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html' and attrs.get('lang'):
            self.lang = True
        if tag == 'title':
            self.title = True
        if tag == 'meta' and attrs.get('name') == 'viewport':
            self.viewport = True
        for name in ('href', 'src'):
            if attrs.get(name):
                self.refs.append((tag, attrs[name], (tag, name) in RESOURCE_ATTRS))

    def handle_data(self, data):
        self.text.append(data)


def _resolve(root, page, url):
    """The file an internal url points to, or None when the url is malformed (no trailing slash)."""
    path = urlsplit(url).path
    if not path:
        return page  # a bare #fragment or ?query
    base = PurePosixPath('/' + page.relative_to(root).as_posix()).parent
    target = PurePosixPath(path) if path.startswith('/') else base / path
    if path.endswith('/'):
        return root / target.relative_to('/') / 'index.html'
    if not target.suffix:
        return None
    return root / target.relative_to('/')


def check(root):
    root = Path(root)
    problems = []
    for page in sorted(root.rglob('*.html')):
        if any(part.startswith('.') or part == 'node_modules' for part in page.relative_to(root).parts):
            continue
        name = page.relative_to(root).as_posix()
        parser = _Page()
        parser.feed(page.read_text(encoding='utf-8'))
        if not parser.lang:
            problems.append(f'{name}: <html> has no lang')
        if not parser.title:
            problems.append(f'{name}: no <title>')
        if not parser.viewport:
            problems.append(f'{name}: no viewport meta')
        if DEVERO_AB.search(' '.join(parser.text)):
            problems.append(f'{name}: says "Devero AB"; Devero is not a registered company')
        for tag, url, is_resource in parser.refs:
            scheme = urlsplit(url).scheme
            if scheme or url.startswith('//'):
                if is_resource:
                    problems.append(f'{name}: external resource {url}')
                continue
            target = _resolve(root, page, url)
            if target is None:
                problems.append(f'{name}: link {url} needs a trailing slash or a file extension')
            elif not target.is_file():
                problems.append(f'{name}: broken link {url}')
    return problems


def main():
    problems = check(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
