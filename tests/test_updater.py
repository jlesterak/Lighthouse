"""
Tests for updater.py. Standard library only, no network access:
run with `python3 -m unittest discover -s tests` from the repo root.
"""

import hashlib
import http.server
import os
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import updater  # noqa: E402

PAYLOAD = bytes(range(256)) * 400  # 100 KiB


class FileHandler(http.server.BaseHTTPRequestHandler):
    """Serves PAYLOAD. Behaviour is switched through class attributes."""
    honor_range = True
    truncate_first_get_at = None  # close the connection early once, after N bytes
    sha256_body = None  # served at <path>.sha256; None means 404
    head_status = 200   # 403 imitates mirrors that refuse HEAD but serve GET
    range_probe_status = None  # if set, a "bytes=0-0" size probe gets this error instead
    gets = 0

    def log_message(self, *args):
        pass

    user_agents = []

    def do_HEAD(self):
        type(self).user_agents.append(self.headers.get("User-Agent", ""))
        if type(self).head_status != 200:
            self.send_error(type(self).head_status)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()

    def do_GET(self):
        cls = type(self)
        cls.user_agents.append(self.headers.get("User-Agent", ""))
        if self.path.endswith(".sha256"):
            if cls.sha256_body is None:
                self.send_error(404)
                return
            body = cls.sha256_body.encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        range_header = self.headers.get("Range")
        if range_header == "bytes=0-0":  # get_remote_size's fallback probe, not a download
            if cls.range_probe_status:
                self.send_error(cls.range_probe_status)
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes 0-0/{len(PAYLOAD)}")
            self.send_header("Content-Length", "1")
            self.end_headers()
            self.wfile.write(PAYLOAD[:1])
            return
        cls.gets += 1
        start = 0
        if range_header and cls.honor_range:
            start = int(range_header.split("=")[1].rstrip("-"))
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(PAYLOAD) - 1}/{len(PAYLOAD)}")
        else:
            self.send_response(200)
        body = PAYLOAD[start:]
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if cls.truncate_first_get_at is not None and cls.gets == 1:
            self.wfile.write(body[:cls.truncate_first_get_at])
            return  # handler returns, server closes the socket mid-body
        self.wfile.write(body)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        FileHandler.honor_range = True
        FileHandler.truncate_first_get_at = None
        FileHandler.sha256_body = None
        FileHandler.head_status = 200
        FileHandler.user_agents = []
        FileHandler.range_probe_status = None
        FileHandler.gets = 0
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FileHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/file.zim"
        self.tmp = tempfile.TemporaryDirectory()
        self.target = os.path.join(self.tmp.name, "file.zim")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def download(self, **kwargs):
        with redirect_stdout(StringIO()):
            return updater.download_file(self.url, self.target, max_backoff=0, **kwargs)

    def read_target(self):
        with open(self.target, "rb") as f:
            return f.read()

    def write_part(self, data):
        with open(self.target + ".part", "wb") as f:
            f.write(data)

    def test_head_forbidden_falls_back_to_range_probe(self):
        # Some Kiwix mirrors answer HEAD with 403 but serve the file; that must not stall the queue
        FileHandler.head_status = 403
        self.assertEqual(updater.get_remote_size(self.url), len(PAYLOAD))
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)

    def test_requests_identify_as_lighthouse(self):
        # Wikimedia's dump servers 403 the default Python-urllib user agent
        self.assertTrue(self.download())
        self.assertTrue(FileHandler.user_agents)
        for ua in FileHandler.user_agents:
            self.assertTrue(ua.startswith("Lighthouse-updater/"), ua)

    def test_size_unknown_still_downloads(self):
        FileHandler.head_status = 403
        FileHandler.range_probe_status = 403
        self.assertIsNone(updater.get_remote_size(self.url))
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)

    def test_fresh_download(self):
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)
        self.assertFalse(os.path.exists(self.target + ".part"))

    def test_resumes_partial_file(self):
        self.write_part(PAYLOAD[:1000])
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)

    def test_server_ignoring_range_restarts_instead_of_appending(self):
        FileHandler.honor_range = False
        self.write_part(PAYLOAD[:1000])
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)

    def test_early_close_is_retried_not_renamed(self):
        FileHandler.truncate_first_get_at = 5000
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)
        self.assertEqual(FileHandler.gets, 2)

    def test_gives_up_after_max_retries_and_keeps_part(self):
        self.url = "http://127.0.0.1:9/unreachable.zim"
        self.write_part(PAYLOAD[:1000])
        self.assertFalse(self.download(max_retries=1))
        self.assertFalse(os.path.exists(self.target))
        self.assertTrue(os.path.exists(self.target + ".part"))

    def test_complete_part_file_is_finalised(self):
        self.write_part(PAYLOAD)
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)
        self.assertEqual(FileHandler.gets, 0)

    def test_matching_checksum_is_accepted(self):
        FileHandler.sha256_body = hashlib.sha256(PAYLOAD).hexdigest() + "  file.zim\n"
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)

    def test_checksum_mismatch_deletes_download(self):
        FileHandler.sha256_body = "0" * 64 + "  file.zim\n"
        self.assertFalse(self.download())
        self.assertFalse(os.path.exists(self.target))
        self.assertFalse(os.path.exists(self.target + ".part"))

    def test_replaces_existing_target(self):
        with open(self.target, "wb") as f:
            f.write(b"old")
        self.assertTrue(self.download())
        self.assertEqual(self.read_target(), PAYLOAD)


OPDS_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Wikipedia</title>
    <summary>Maxi</summary>
    <name>wikipedia_en_all</name>
    <flavour>maxi</flavour>
    <link rel="http://opds-spec.org/acquisition/open-access" type="application/x-zim"
          href="https://lb.download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi_2026-08.zim.meta4"
          length="127418088448"/>
  </entry>
  <entry>
    <title>Wikipedia</title>
    <summary>No pictures</summary>
    <name>wikipedia_en_all</name>
    <flavour>nopic</flavour>
    <link rel="http://opds-spec.org/acquisition/open-access" type="application/x-zim"
          href="https://lb.download.kiwix.org/zim/wikipedia/wikipedia_en_all_nopic_2026-06.zim.meta4"
          length="52690707456"/>
  </entry>
  <entry>
    <title>Medicine</title>
    <name>zimgit-medicine_en</name>
    <flavour></flavour>
    <link rel="http://opds-spec.org/acquisition/open-access" type="application/x-zim"
          href="https://lb.download.kiwix.org/zim/other/zimgit-medicine_en_2024-08.zim.meta4"/>
  </entry>
  <entry>
    <title>No download link</title>
    <name>broken</name>
  </entry>
</feed>
"""


class CatalogTests(unittest.TestCase):
    def test_parse_opds_entries(self):
        entries = updater.parse_opds_entries(OPDS_FEED)
        self.assertEqual(len(entries), 3)
        maxi = entries[0]
        self.assertEqual(maxi["catalog_name"], "wikipedia_en_all")
        self.assertEqual(maxi["flavour"], "maxi")
        self.assertEqual(maxi["url"], "https://lb.download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi_2026-08.zim")
        self.assertEqual(maxi["filename"], "wikipedia_en_all_maxi_2026-08.zim")
        self.assertEqual(maxi["size_approx"], "118.67 GB")
        self.assertEqual(entries[2]["flavour"], "")
        self.assertEqual(entries[2]["size_approx"], "Unknown size")

    def test_resolve_picks_matching_flavour(self):
        original = updater.fetch_catalog
        updater.fetch_catalog = lambda params, timeout=30: updater.parse_opds_entries(OPDS_FEED)
        try:
            with redirect_stdout(StringIO()):
                self.assertEqual(updater.resolve_catalog_item("wikipedia_en_all", "nopic")[1],
                                 "wikipedia_en_all_nopic_2026-06.zim")
                self.assertEqual(updater.resolve_catalog_item("zimgit-medicine_en")[1],
                                 "zimgit-medicine_en_2024-08.zim")
                self.assertEqual(updater.resolve_catalog_item("wikipedia_en_all", "mini"), (None, None))
        finally:
            updater.fetch_catalog = original

    def test_manifest_items_are_well_formed(self):
        manifest = updater.load_manifest()
        ids = set()
        for category in manifest["categories"]:
            for item in category["items"]:
                for key in ("id", "name", "description", "catalog_name", "flavour", "size_approx"):
                    self.assertIn(key, item, f"{item.get('id')} missing {key}")
                self.assertNotIn(item["id"], ids)
                ids.add(item["id"])


class VersionTests(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(updater.get_version(), r"^\d+\.\d+\.\d+$")

    def test_changelog_top_entry_matches_version(self):
        changelog = os.path.join(updater.BASE_DIR, "CHANGELOG.md")
        with open(changelog, encoding="utf-8") as f:
            for line in f:
                # An [Unreleased] section may sit above the current release
                if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                    self.assertEqual(line[4:line.index("]")], updater.get_version(),
                                     "bump CHANGELOG.md together with VERSION")
                    return
        self.fail("CHANGELOG.md has no version entries")


class FormatBytesTests(unittest.TestCase):
    def test_units(self):
        self.assertEqual(updater.format_bytes(500), "500.00 B")
        self.assertEqual(updater.format_bytes(1536), "1.50 KB")
        self.assertEqual(updater.format_bytes(3 * 2**40), "3.00 TB")
        self.assertEqual(updater.format_bytes(2**52), "4096.00 TB")


if __name__ == "__main__":
    unittest.main()
