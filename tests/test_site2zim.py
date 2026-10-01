"""
Tests for tools/site2zim.py: reading a site from a .zip and recognizing LEMON manuals.
Skipped when libzim isn't installed (pip install libzim pillow); the end-to-end build test
also needs pillow for the default icon.
"""

import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
try:
    import site2zim
except ImportError:
    site2zim = None

TOP = "2016 Ford F-150 XLT, 4D Pickup Extra Cab, 3.5L Eng VIN G, 4WD/"
INDEX = (b"<html><head><title>Free Service Manual ~ LEMON Manuals</title></head><body>"
         b"<h1>Ford: 2016: F-150 XLT, 4D Pickup Extra Cab, 3.5L Eng VIN G, 4WD</h1>"
         b"<a href='pages/1.html'>Repair</a></body></html>")
PAGE = (b"<html><head><title>Spark Plugs \xe2\x80\x94 2016 Ford F-150 Service Manual ~ LEMON Manuals</title></head>"
        b"<body><h1>Spark Plugs</h1><img src='../images/a.png'>Torque 11 lb-ft</body></html>")
OTHER = b"<html><head><title>Labor Times: Other Variant</title></head><body class='other-variant'></body></html>"


@unittest.skipUnless(site2zim, "libzim not installed")
class Site2Zim(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.zip = os.path.join(self.tmp.name, "lemon.zip")
        with zipfile.ZipFile(self.zip, "w") as z:
            z.writestr(TOP, b"")
            z.writestr(TOP + "index.html", INDEX)
            z.writestr(TOP + "pages/1.html", PAGE)
            z.writestr(TOP + "pages/2.html", OTHER)
            z.writestr(TOP + "images/a.png", b"\x89PNG fake")

    def tearDown(self):
        self.tmp.cleanup()

    def test_zip_drops_single_top_folder(self):
        site = site2zim.Site(self.zip)
        self.assertEqual(site.files, ["images/a.png", "index.html", "pages/1.html", "pages/2.html"])
        self.assertEqual(site.read("pages/1.html"), PAGE)
        self.assertIsNone(site.local("index.html"))

    def test_lemon_preset(self):
        p = site2zim.lemon(site2zim.Site(self.zip), "index.html")
        self.assertEqual(p["title"], "2016 Ford F-150 XLT 3.5L VIN G")
        self.assertLessEqual(len(p["title"]), 30)
        self.assertEqual(p["name"], "lemon_ford-f-150-xlt-2016-3.5l-vin-g-4wd")
        self.assertEqual(p["title_sep"], " — ")
        self.assertEqual(p["not_front"], "other-variant")

    def test_not_lemon(self):
        d = os.path.join(self.tmp.name, "site")
        os.makedirs(d)
        with open(os.path.join(d, "index.html"), "wb") as f:
            f.write(b"<html><h1>My Wiki</h1></html>")
        self.assertIsNone(site2zim.lemon(site2zim.Site(d), "index.html"))

    def test_build_from_zip(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("pillow not installed")
        from libzim.reader import Archive
        out = os.path.join(self.tmp.name, "out.zim")
        sys.argv = ["site2zim", self.zip, "--out", out]
        site2zim.main()
        zim = Archive(out)
        self.assertEqual(zim.main_entry.get_item().path, "index.html")
        self.assertEqual(zim.get_entry_by_path("pages/1.html").title, "Spark Plugs")
        self.assertEqual(bytes(zim.get_entry_by_path("images/a.png").get_item().content), b"\x89PNG fake")


if __name__ == "__main__":
    unittest.main()
