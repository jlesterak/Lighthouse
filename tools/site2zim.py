#!/usr/bin/env python3
"""
site2zim: turn a static HTML site (a folder, or a .zip of one) into a Kiwix ZIM.

Every file goes in at its relative path, so the site's own relative links, images, CSS and JS keep
working. HTML pages become articles titled from their <title> (cut at --title-sep); pages
containing --not-front stay readable and full-text searchable but are left out of title
suggestions. A .zip is read in place (no extraction), and a single top-level folder in it is
dropped. Opens in kiwix-serve, Kiwix desktop and the Kiwix Android app.

LEMON Manuals (https://lemon-manuals.la) offline zips are detected and need no options: the
title, name, description and output file come from the manual's front page, the
"~ LEMON Manuals" suffix is cut from page titles, and pages about other trims (which LEMON marks
"other-variant") are kept out of title suggestions.

    pip install libzim pillow
    tools/site2zim.py "LEMON 2016 Ford F-150 XLT, ..., 3.5L Eng VIN G, 4WD.zip"
    tools/site2zim.py exported-wiki/ --out wiki.zim --name my_wiki --title "My Wiki"

Only for content you are entitled to keep a copy of; don't publish what isn't yours to share.
"""
import argparse
import datetime
import html
import io
import mimetypes
import os
import re
import sys
import zipfile

from libzim.writer import Creator, FileProvider, Hint, Item, StringProvider

mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")
TITLE = re.compile(rb"<title>(.*?)</title>", re.S | re.I)
H1 = re.compile(rb"<h1>(.*?)</h1>", re.S | re.I)


class File(Item):
    def __init__(self, path, title, mimetype, front, content=None, src=None):
        super().__init__()
        self._p, self._t, self._m, self._f, self._c, self._s = path, title, mimetype, front, content, src

    def get_path(self): return self._p
    def get_title(self): return self._t
    def get_mimetype(self): return self._m
    def get_contentprovider(self): return FileProvider(self._s) if self._s else StringProvider(self._c)
    def get_hints(self): return {Hint.FRONT_ARTICLE: self._f, Hint.COMPRESS: self._m.startswith(("text", "image/svg"))}


class Site:
    """A folder or a .zip, read as {relative path: bytes}; local files are streamed from disk."""

    def __init__(self, src):
        self.zip = zipfile.ZipFile(src) if zipfile.is_zipfile(src) else None
        if self.zip:
            names = [n for n in self.zip.namelist() if not n.endswith("/")]
            tops = {n.split("/", 1)[0] for n in names}
            self.prefix = tops.pop() + "/" if len(tops) == 1 and all("/" in n for n in names) else ""
            self.files = sorted(n[len(self.prefix):] for n in names)
        else:
            self.root = os.path.abspath(src)
            self.files = sorted(os.path.relpath(os.path.join(d, f), self.root).replace(os.sep, "/")
                                for d, _, fs in os.walk(self.root) for f in fs)

    def read(self, path):
        if self.zip:
            return self.zip.read(self.prefix + path)
        with open(os.path.join(self.root, path), "rb") as f:
            return f.read()

    def local(self, path):
        return None if self.zip else os.path.join(self.root, path)


def text(b):
    return html.unescape(re.sub(r"<[^>]+>", "", b.decode("utf-8", "replace"))).strip()


def lemon(site, main):
    """Settings for a LEMON Manuals download, or None if this isn't one."""
    try:
        index = site.read(main)
    except KeyError:
        return None
    if b"LEMON Manuals" not in index or not H1.search(index):
        return None
    # front page heading: "Ford: 2016: F-150 XLT, 4D Pickup Extra Cab, 3.5L Eng VIN G, 4WD"
    make, year, model = (text(H1.search(index).group(1)).split(": ", 2) + ["", ""])[:3]
    full = f"{year} {make} {model}".strip()
    eng = re.search(r"(\d\.\d)L Eng VIN (\w)", model)
    short = f"{year} {make} {model.split(',')[0]}" + (f" {eng[1]}L VIN {eng[2]}" if eng else "")
    slug = re.sub(r"[^a-z0-9.]+", "-", (f"{make} {model.split(',')[0]} {year}" + (f" {eng[1]}l vin {eng[2]}" if eng else "")
                                        + (" 4wd" if "4WD" in model else "")).lower()).strip("-")
    return {"title": short[:30], "name": f"lemon_{slug}", "description": f"{full} service manual (LEMON)",
            "creator": "LEMON Manuals", "title_sep": " — ", "not_front": "other-variant"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", help="folder or .zip holding the site (its main page at the top)")
    ap.add_argument("--out", help="default: <name>.zim")
    ap.add_argument("--name", help="ZIM Name, e.g. my_wiki (required unless it's a LEMON manual)")
    ap.add_argument("--title", help="library title, 30 chars max (required unless it's a LEMON manual)")
    ap.add_argument("--description", default=None)
    ap.add_argument("--creator", default=None)
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--main", default="index.html", help="main page, relative to the site root")
    ap.add_argument("--title-sep", default=None, help="cut page titles at this separator (drops a site-wide suffix)")
    ap.add_argument("--not-front", default=None, help="pages containing this text are not front articles")
    ap.add_argument("--icon", default="", help="48x48 PNG for the library (default: plain green square)")
    a = ap.parse_args()

    site = Site(a.site)
    preset = lemon(site, a.main) or {}
    if preset:
        print(f"LEMON manual: {preset['description']}", flush=True)
    for k, v in preset.items():
        if getattr(a, k) is None:
            setattr(a, k, v)
    if not (a.name and a.title):
        sys.exit("--name and --title are required (they're only automatic for LEMON manuals)")
    a.out = a.out or f"{a.name}.zim"
    not_front = (a.not_front or "").encode()
    print(f"{len(site.files)} files", flush=True)

    with Creator(a.out).config_indexing(True, a.lang) as z:
        z.set_mainpath(a.main)
        z.add_metadata("Title", a.title[:30])
        z.add_metadata("Description", (a.description or a.title)[:80])
        z.add_metadata("LongDescription", f"{a.title}. {a.description or ''}"[:4000])
        z.add_metadata("Language", a.lang)
        z.add_metadata("Name", a.name)
        z.add_metadata("Creator", a.creator or "unknown")
        z.add_metadata("Publisher", "Lighthouse site2zim")
        z.add_metadata("Date", datetime.date.today().isoformat())
        if a.icon:
            with open(a.icon, "rb") as f:
                icon = f.read()
        else:
            from PIL import Image
            buf = io.BytesIO(); Image.new("RGB", (48, 48), (47, 111, 94)).save(buf, "PNG"); icon = buf.getvalue()
        z.add_illustration(48, icon)

        pages = hidden = 0
        for n, path in enumerate(site.files, 1):
            mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
            if mime == "text/html":
                data = site.read(path)
                m = TITLE.search(data)
                title = text(m.group(1)) if m else path
                if a.title_sep:
                    title = title.split(a.title_sep)[0].strip()
                front = not (not_front and not_front in data) and path != "404.html"
                z.add_item(File(path, title, mime, front, content=data))
                pages += 1
                hidden += not front
            else:
                src = site.local(path)
                z.add_item(File(path, "", mime, False, content=None if src else site.read(path), src=src))
            if n % 5000 == 0:
                print(f"  added {n}/{len(site.files)}", flush=True)
        print(f"{pages} pages ({pages - hidden} in title search), {len(site.files) - pages} assets", flush=True)
    print(f"done: {a.out} ({os.path.getsize(a.out) / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
