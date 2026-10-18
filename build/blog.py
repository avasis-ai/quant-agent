"""Regenerate the local article from docs/BLOG-FINAL.md, retaining the site's chrome.

Run: python -m build.blog
The small renderer supports the headings, paragraphs, lists, code, links and
captioned images used by this article. It escapes source text and needs no packages.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = "https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/"
TOKEN = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\[[^\]]+\]\(https?://[^)]+\)|(?<!\*)\*[^*]+\*(?!\*))")


def inline(text: str) -> str:
    parts = []
    for token in TOKEN.split(text):
        if token.startswith("`") and token.endswith("`"):
            parts.append("<code>" + html.escape(token[1:-1]) + "</code>")
        elif token.startswith("**") and token.endswith("**"):
            parts.append("<strong>" + inline(token[2:-2]) + "</strong>")
        elif token.startswith("*") and token.endswith("*"):
            parts.append("<em>" + inline(token[1:-1]) + "</em>")
        elif match := re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", token):
            parts.append('<a href="' + html.escape(match[2], quote=True) + '">' + inline(match[1]) + "</a>")
        else:
            parts.append(html.escape(token, quote=False))
    return "".join(parts)


def render(body: str, image_sizes: dict[str, tuple[str, str]]) -> str:
    output, heading = [], 0
    # The byline/cover/caption precede the first heading and live in the hero.
    body = body[body.index("\n## ") + 1:]
    for block in re.split(r"\n\s*\n", body.strip()):
        if block.startswith("## "):
            heading += 1
            title = block.removeprefix("## ").strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            output.append(f'<h2 class="rv" id="{slug}"><span class="n">{heading:02d}</span>{inline(title)}</h2>')
        elif block.startswith("```"):
            lines = block.splitlines()
            if lines[-1] != "```":
                raise ValueError("Unclosed article code block.")
            output.append('<pre class="rv"><code>' + html.escape("\n".join(lines[1:-1])) + "</code></pre>")
        elif block.startswith("- "):
            items = re.split(r"\n- ", block[2:])
            output.append('<ul class="rv">' + "".join("<li>" + inline(item.replace("\n", " ")) + "</li>" for item in items) + "</ul>")
        elif match := re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)(?:\n\*(.*?)\*)?", block, re.S):
            alt, url, caption = match.groups()
            if not url.startswith(IMAGE_ROOT):
                raise ValueError("Article image must use the published image directory.")
            src = "/blog-assets/" + url.removeprefix(IMAGE_ROOT)
            width, height = image_sizes[src]
            cls = "rv art" if src.endswith(".jpg") else "rv"
            output.append(f'<figure class="{cls}"><img src="{html.escape(src)}" alt="{html.escape(alt, quote=True)}" width="{width}" height="{height}" loading="lazy" decoding="async">'
                          + ("<figcaption>" + inline(caption) + "</figcaption>" if caption else "") + "</figure>")
        else:
            output.append('<p class="rv">' + inline(block.replace("\n", " ")) + "</p>")
    return "\n".join(output) + "\n"


def main() -> None:
    source = (ROOT / "docs/BLOG-FINAL.md").read_text()
    _, metadata, body = source.split("---", 2)
    fields = {}
    for line in metadata.strip().splitlines():
        key, value = line.split(":", 1)
        fields[key] = json.loads(value.strip()) if value.strip().startswith('"') else value.strip()
    target = ROOT / "app/static/blog.html"
    template = target.read_text()
    sizes = {}
    for image in re.findall(r"<img\b[^>]+>", template):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', image))
        if attrs.get("src", "").startswith("/blog-assets/"):
            sizes[attrs["src"]] = (attrs["width"], attrs["height"])
    article = render(body, sizes)
    template = re.sub(r'(<main id="story" class="blog-story">\n).*?(</main>)',
                      lambda m: m[1] + article + m[2], template, flags=re.S)
    template = re.sub(r'<title>.*?</title>',
                      lambda _: '<title>' + html.escape(fields['title']) + ' · QuantBase</title>', template)
    template = re.sub(r'<meta property="og:title" content="[^"]*">',
                      lambda _: '<meta property="og:title" content="' + html.escape(fields['title'], quote=True) + '">', template)
    template = re.sub(r'(<h1 id="blog-title">).*?(</h1>)',
                      lambda m: m[1] + inline(fields['title']) + m[2], template)
    for name in ("description", "og:description"):
        attr = "property" if name.startswith("og:") else "name"
        template = re.sub(f'<meta {attr}="{name}" content="[^"]*">',
                          lambda _: f'<meta {attr}="{name}" content="{html.escape(fields["description"], quote=True)}">', template)
    template = re.sub(r'(<p class="lede">).*?(</p>)',
                      lambda m: m[1] + inline(fields["description"]) + m[2], template)
    target.write_text(template)
    print("Regenerated app/static/blog.html from docs/BLOG-FINAL.md")


if __name__ == "__main__":
    main()
