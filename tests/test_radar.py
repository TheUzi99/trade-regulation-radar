import json, shutil, tempfile, unittest
from pathlib import Path
from unittest import mock
from radar import collect, build_site

FIX = Path(__file__).parent / "fixtures"
CSV1 = b"id,name,schema\nA,Alpha Shipping,Company\nB,Beta Vessel,Vessel\n"
CSV2 = b"id,name,schema\nA,Alpha Shipping Ltd,Company\nC,Gamma Trading,Company\n"

class RadarTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        cfg = {"sources": [
            {"id": "feed", "name": "Feed", "kind": "feed", "jurisdiction": "EU", "url": "http://x/feed", "licence": "L", "topic": "t", "keywords": ["restrictive measures"]},
            {"id": "list", "name": "List", "kind": "csv", "jurisdiction": "EU", "url": "http://x/list", "key": "id", "licence": "L", "topic": "s"},
            {"id": "todo", "name": "Todo", "kind": "feed", "jurisdiction": "EU", "url": "", "licence": "L", "topic": "t"}]}
        (self.dir / "sources.json").write_text(json.dumps(cfg))
        self.payload = {"http://x/feed": (FIX / "feed.xml").read_bytes(), "http://x/list": CSV1}

    def tearDown(self): shutil.rmtree(self.dir)

    def run_once(self):
        with mock.patch.object(collect, "fetch", side_effect=lambda u, timeout=60: self.payload[u]):
            return collect.run(self.dir)

    def items(self): return json.loads((self.dir / "data/items.json").read_text())

    def test_feed_keyword_filter_and_dedup(self):
        self.run_once(); first = self.items()
        self.assertEqual([i["title"][:16] for i in first if i["source"] == "feed"], ["Council Regulati"])
        self.run_once(); self.assertEqual(len(self.items()), len(first))

    def test_csv_baseline_then_diff(self):
        st = self.run_once()
        self.assertIn("baseline 2", [s["detail"] for s in st if s["source"] == "list"][0])
        self.payload["http://x/list"] = CSV2; self.run_once()
        kinds = sorted(i["change"] for i in self.items() if i["source"] == "list")
        self.assertEqual(kinds, ["added", "changed", "removed"])

    def test_missing_and_failing_sources_are_reported(self):
        self.payload["http://x/feed"] = b"<not xml"
        st = {s["source"]: s for s in self.run_once()}
        self.assertFalse(st["todo"]["ok"]); self.assertFalse(st["feed"]["ok"]); self.assertTrue(st["list"]["ok"])

    def test_site_is_bilingual_and_escaped(self):
        self.payload["http://x/list"] = CSV1; self.run_once()
        self.payload["http://x/list"] = b"id,name\nA,<script>x</script>\n"; self.run_once()
        build_site.build(self.dir)
        en = (self.dir / "site/index.html").read_text(); de = (self.dir / "site/de/index.html").read_text()
        self.assertIn("Trade Regulation Radar", en); self.assertIn("Handelsrecht-Radar", de)
        self.assertIn("Ticaret Mevzuatı Radarı", (self.dir / "site/tr/index.html").read_text())
        self.assertIn("Радар торгового регулирования", (self.dir / "site/ru/index.html").read_text())
        self.assertIn("Radar de la réglementation commerciale", (self.dir / "site/fr/index.html").read_text())
        self.assertNotIn("<script>x", en); self.assertIn("&lt;script&gt;", en)

if __name__ == "__main__": unittest.main()
