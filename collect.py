"""Collect new and changed items from configured sources into data/items.json."""
import csv, hashlib, io, json, sys, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA = "trade-regulation-radar/0.1 (+https://github.com/TheUzi99)"
NS = {"atom": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def parse_feed(raw):
    root = ET.fromstring(raw)
    out = []
    for it in root.iter("item"):
        out.append({"title": (it.findtext("title") or "").strip(), "link": (it.findtext("link") or "").strip(),
                    "date": (it.findtext("pubDate") or it.findtext("dc:date", namespaces=NS) or "").strip(),
                    "summary": (it.findtext("description") or "").strip()})
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link = e.find("atom:link", NS)
        out.append({"title": (e.findtext("atom:title", namespaces=NS) or "").strip(),
                    "link": link.get("href", "") if link is not None else "",
                    "date": (e.findtext("atom:updated", namespaces=NS) or e.findtext("atom:published", namespaces=NS) or "").strip(),
                    "summary": (e.findtext("atom:summary", namespaces=NS) or "").strip()})
    return out

def matches(item, keywords):
    if not keywords:
        return True
    text = f"{item['title']} {item['summary']}".lower()
    return any(k.lower() in text for k in keywords)

def collect_feed(src, raw, known):
    new = []
    for it in parse_feed(raw):
        if not it["link"] or not matches(it, src.get("keywords")):
            continue
        uid = sha(src["id"] + it["link"])
        if uid in known:
            continue
        new.append({"id": uid, "source": src["id"], "jurisdiction": src["jurisdiction"], "topic": src["topic"],
                    "title": it["title"], "link": it["link"], "published": it["date"], "change": "new"})
    return new

def collect_csv(src, raw, snapshot):
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    key = src.get("key", "id")
    current = {r[key]: sha(json.dumps(r, sort_keys=True)) for r in rows if r.get(key)}
    names = {r[key]: r.get("name") or r.get("caption") or r[key] for r in rows if r.get(key)}
    previous = snapshot.get(src["id"])
    changes = []
    if previous is not None:
        for k in current.keys() - previous.keys():
            changes.append(("added", k))
        for k in previous.keys() - current.keys():
            changes.append(("removed", k))
        for k in current.keys() & previous.keys():
            if current[k] != previous[k]:
                changes.append(("changed", k))
    items = [{"id": sha(f"{src['id']}{kind}{k}{current.get(k, previous.get(k) if previous else '')}"), "source": src["id"],
              "jurisdiction": src["jurisdiction"], "topic": src["topic"],
              "title": f"{kind.capitalize()}: {names.get(k, k)}", "link": src["url"], "published": "", "change": kind}
             for kind, k in sorted(changes)]
    snapshot[src["id"]] = current
    return items, len(current), previous is None

def run(root):
    root = Path(root)
    cfg = json.loads((root / "sources.json").read_text("utf-8"))
    data = root / "data"; data.mkdir(exist_ok=True)
    items_path, snap_path, status_path = data / "items.json", data / "snapshot.json", data / "status.json"
    items = json.loads(items_path.read_text("utf-8")) if items_path.exists() else []
    snapshot = json.loads(snap_path.read_text("utf-8")) if snap_path.exists() else {}
    known = {i["id"] for i in items}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = []
    for src in cfg["sources"]:
        if not src.get("url"):
            status.append({"source": src["id"], "ok": False, "detail": "URL not configured yet"}); continue
        try:
            raw = fetch(src["url"])
            if src["kind"] == "feed":
                new = collect_feed(src, raw, known); detail = f"{len(new)} new"
            else:
                new, count, first = collect_csv(src, raw, snapshot)
                detail = f"baseline {count} records" if first else f"{len(new)} changes, {count} records"
            for n in new:
                n["collected"] = now
            items.extend(new); known.update(n["id"] for n in new)
            status.append({"source": src["id"], "ok": True, "detail": detail})
        except Exception as exc:
            status.append({"source": src["id"], "ok": False, "detail": f"{type(exc).__name__}: {exc}"[:300]})
    items.sort(key=lambda i: i.get("collected", ""), reverse=True)
    items_path.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")
    snap_path.write_text(json.dumps(snapshot, sort_keys=True), "utf-8")
    status_path.write_text(json.dumps({"run": now, "sources": status}, ensure_ascii=False, indent=1), "utf-8")
    return status

if __name__ == "__main__":
    for s in run(sys.argv[1] if len(sys.argv) > 1 else "."):
        print(("OK  " if s["ok"] else "ERR ") + s["source"] + ": " + s["detail"])
