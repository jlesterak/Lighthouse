#!/usr/bin/env python3
"""
pdf2zim: turn a big PDF with bookmarks (a service manual, a device manual) into a Kiwix ZIM.

Each bookmark leaf becomes one article: the PDF pages it covers, shown as page images (so
diagrams, tables and wiring stay exactly as printed), with each page's text underneath so
Kiwix's full-text search finds it. Index pages follow the bookmark tree. Opens in kiwix-serve,
Kiwix desktop and the Kiwix Android app (so it works on a phone with no network).

    pip install pymupdf libzim pillow
    tools/pdf2zim.py MANUAL.pdf --out manual.zim --name ford_f150_2015-2017 \
        --title "Ford F-150 2015-2017 Service Manual" --description "Workshop manual"
    # quick trial on the first pages:  --pages 300

Only for content you are entitled to keep a copy of; don't publish what isn't yours to share.
"""
import argparse
import datetime
import html
import io
import multiprocessing
import os
import sys

import pymupdf
from PIL import Image
from libzim.writer import Creator, FileProvider, Hint, Item, StringProvider  # noqa: F401

CSS = """
body{font:16px/1.45 system-ui,sans-serif;margin:0;padding:12px;max-width:980px;margin:auto;color:#1e2124;background:#fff}
a{color:#0b5cad} h1{font-size:1.3rem;margin:.2rem 0 .6rem} .crumb{color:#5f6670;font-size:.9rem}
figure{margin:12px 0;border:1px solid #ddd} figure img{width:100%;height:auto;display:block}
figcaption{font-size:.8rem;color:#5f6670;padding:4px 8px} details{margin:4px 0 16px}
pre{white-space:pre-wrap;font:13px/1.4 ui-monospace,monospace;background:#f6f6f6;padding:8px}
ul{padding-left:1.2rem} li{margin:.15rem 0}
@media (prefers-color-scheme:dark){body{background:#16181b;color:#e8e6e1}a{color:#7fb0e8}pre{background:#1f2226}figure{border-color:#333}}
"""


class Page(Item):
    def __init__(self, path, title, content, mimetype="text/html", front=False):
        super().__init__()
        self._p, self._t, self._c, self._m, self._f = path, title, content, mimetype, front

    def get_path(self): return self._p
    def get_title(self): return self._t
    def get_mimetype(self): return self._m
    def get_contentprovider(self): return StringProvider(self._c)
    def get_hints(self): return {Hint.FRONT_ARTICLE: self._f, Hint.COMPRESS: self._m.startswith("text")}


def doc(title, body, depth):
    up = "../" * depth
    return (f"<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><link rel=stylesheet href='{up}style.css'></head><body>{body}</body></html>")


def leaves(toc):
    """Bookmark leaves with their ancestor titles: [(index, start_page, end_page, [ancestors], title)]."""
    out, stack = [], []
    for i, (lvl, title, page) in enumerate(toc):
        stack = stack[:lvl - 1] + [title]
        nxt = toc[i + 1] if i + 1 < len(toc) else None
        if nxt and nxt[0] > lvl:
            continue                      # has children: not a leaf
        out.append([i, page, None, stack[:-1], title])
    for k, leaf in enumerate(out):
        nxt_start = out[k + 1][1] if k + 1 < len(out) else None
        # the procedure runs until the next one starts (its first page included: it may finish there)
        leaf[2] = max(leaf[1], nxt_start) if nxt_start else leaf[1]
    return out


_doc = None
def _render(args):
    global _doc
    path, pno, dpi, quality = args
    if _doc is None:
        _doc = pymupdf.open(path)
    page = _doc[pno - 1]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)   # manuals are black and white: gray is ~3x smaller
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=quality, method=4)
    return pno, buf.getvalue(), page.get_text()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True, help="short id, e.g. ford_f150_2015-2017")
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--creator", default="")
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--dpi", type=int, default=100)
    ap.add_argument("--quality", type=int, default=55)
    ap.add_argument("--pages", type=int, default=0, help="only the first N pages (trial run)")
    ap.add_argument("--jobs", type=int, default=max(1, os.cpu_count() - 1))
    a = ap.parse_args()

    src = pymupdf.open(a.pdf)
    npages = min(a.pages or src.page_count, src.page_count)
    toc = [t for t in src.get_toc(simple=True) if t[2] <= npages]
    if not toc:
        sys.exit("the PDF has no bookmarks in range; pdf2zim needs them to build articles")
    items = leaves(toc)
    for leaf in items:
        leaf[2] = min(leaf[2], npages)
    print(f"{npages} pages, {len(items)} articles", flush=True)

    with Creator(a.out).config_indexing(True, a.lang) as z:
        z.set_mainpath("index")
        z.add_metadata("Title", a.title[:30])
        z.add_metadata("Description", (a.description or a.title)[:80])
        z.add_metadata("LongDescription", f"{a.title}. {a.description}"[:4000])
        z.add_metadata("Language", a.lang)
        z.add_metadata("Name", a.name)
        z.add_metadata("Creator", a.creator or "unknown")
        z.add_metadata("Publisher", "Lighthouse pdf2zim")
        z.add_metadata("Date", datetime.date.today().isoformat())
        icon = io.BytesIO(); Image.new("RGB", (48, 48), (47, 111, 94)).save(icon, "PNG")
        z.add_illustration(48, icon.getvalue())
        z.add_item(Page("style.css", "", CSS, "text/css"))

        # page images + text, rendered in parallel
        text = {}
        with multiprocessing.Pool(a.jobs) as pool:
            for n, (pno, webp, txt) in enumerate(pool.imap_unordered(
                    _render, [(a.pdf, p, a.dpi, a.quality) for p in range(1, npages + 1)], chunksize=8), 1):
                z.add_item(Page(f"img/{pno}.webp", "", webp, "image/webp"))
                text[pno] = txt
                if n % 500 == 0:
                    print(f"  rendered {n}/{npages}", flush=True)

        # one article per bookmark leaf
        tree = {}
        for idx, start, end, anc, title in items:
            crumb = " › ".join(anc[1:])            # skip the book-level root
            # Bookmarks like "REMOVAL AND INSTALLATION > BRAKE PADS > REMOVAL": the first part is the
            # kind of entry, the rest says what it is. Title it "Front Disc Brake: Brake Pads › Removal".
            parts = [p.strip() for p in title.split(" > ") if p.strip()]
            kind = parts[0].title() if len(parts) > 1 else ""
            name = " › ".join(x.title() for x in (parts[1:] if len(parts) > 1 else parts))
            section = anc[-1].title() if anc else ""
            full = f"{section}: {name}" if section else name
            pages = range(start, end + 1)
            body = (f"<p class=crumb><a href='../index'>Contents</a> › {html.escape(crumb)}</p>"
                    f"<h1>{html.escape(name)}</h1>"
                    + (f"<p class=crumb>{html.escape(kind)} · pages {start}-{end}</p>" if kind else f"<p class=crumb>pages {start}-{end}</p>")
                    + "".join(f"<figure><img loading=lazy src='../img/{p}.webp' alt='Page {p}'>"
                              f"<figcaption>Page {p}</figcaption></figure>"
                              f"<details><summary>Page {p} text</summary><pre>{html.escape(text.get(p, ''))}</pre></details>"
                              for p in pages))
            z.add_item(Page(f"p/{idx}", full, doc(full, body, 1), front=True))
            node = tree
            for t in anc[1:]:
                node = node.setdefault(t, {})
            node.setdefault("__leaves__", []).append((idx, name, kind))

        def render_tree(node, depth):
            out = ["<ul>"]
            for k, v in node.items():
                if k == "__leaves__":
                    continue
                out.append(f"<li><details><summary>{html.escape(k)}</summary>{render_tree(v, depth)}</details></li>")
            for idx, name, kind in node.get("__leaves__", []):
                out.append(f"<li><a href='p/{idx}'>{html.escape(name)}</a>"
                           + (f" <span class=crumb>({html.escape(kind.lower())})</span>" if kind else "") + "</li>")
            out.append("</ul>")
            return "".join(out)

        z.add_item(Page("index", a.title, doc(a.title,
            f"<h1>{html.escape(a.title)}</h1><p class=crumb>{npages} pages · {len(items)} procedures. "
            "Use Kiwix search for a part, symptom, trouble code or connector.</p>" + render_tree(tree, 0), 0), front=True))
    print(f"done: {a.out} ({os.path.getsize(a.out) / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
