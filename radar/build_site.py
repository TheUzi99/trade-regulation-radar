"""Render data/*.json into a static, bilingual (EN/DE) site in site/."""
import html, json, sys
from pathlib import Path

T = {"en": {"title": "Trade Regulation Radar", "tag": "Daily changes in EU trade law, sanctions and policy affecting Türkiye, the CIS and Central Asia.",
            "latest": "Latest changes", "status": "Source status", "run": "Last run", "none": "No changes recorded yet.",
            "src": "Source", "chg": "Change", "date": "Collected", "about": "About", "aboutText": "An independent, non-commercial portfolio project by Said Maruf Özbek. It uses public sources only and is not affiliated with any employer or institution. Always check the linked official text.",
            "licences": "Sources and licences", "other": "Deutsch"},
     "de": {"title": "Handelsrecht-Radar", "tag": "Tägliche Änderungen im EU-Handelsrecht, bei Sanktionen und in der Politik mit Bezug zur Türkei, GUS und Zentralasien.",
            "latest": "Neueste Änderungen", "status": "Quellenstatus", "run": "Letzter Lauf", "none": "Noch keine Änderungen erfasst.",
            "src": "Quelle", "chg": "Änderung", "date": "Erfasst", "about": "Über", "aboutText": "Ein unabhängiges, nicht-kommerzielles Portfolio-Projekt von Said Maruf Özbek. Es nutzt ausschließlich öffentliche Quellen und steht in keiner Verbindung zu einem Arbeitgeber oder einer Institution. Bitte immer den verlinkten amtlichen Text prüfen.",
            "licences": "Quellen und Lizenzen", "other": "English"},
     "tr": {"title": "Ticaret Mevzuatı Radarı", "tag": "Türkiye, BDT ve Orta Asya'yı etkileyen AB ticaret hukuku, yaptırım ve politika değişiklikleri, her gün.",
            "latest": "Son değişiklikler", "status": "Kaynak durumu", "run": "Son çalışma", "none": "Henüz kayıtlı değişiklik yok.",
            "src": "Kaynak", "chg": "Değişiklik", "date": "Toplandı", "about": "Hakkında", "aboutText": "Said Maruf Özbek'in bağımsız ve ticari olmayan portföy projesidir. Yalnızca kamuya açık kaynakları kullanır; hiçbir işveren veya kurumla bağlantısı yoktur. Her zaman bağlantıdaki resmî metni kontrol edin.",
            "licences": "Kaynaklar ve lisanslar", "other": ""},
     "ru": {"title": "Радар торгового регулирования", "tag": "Ежедневные изменения в торговом праве ЕС, санкциях и политике, касающиеся Турции, СНГ и Центральной Азии.",
            "latest": "Последние изменения", "status": "Статус источников", "run": "Последний запуск", "none": "Изменений пока нет.",
            "src": "Источник", "chg": "Изменение", "date": "Собрано", "about": "О проекте", "aboutText": "Независимый некоммерческий портфолио-проект Саида Маруфа Озбека. Использует только открытые источники и не связан ни с одним работодателем или учреждением. Всегда проверяйте официальный текст по ссылке.",
            "licences": "Источники и лицензии", "other": ""},
     "fr": {"title": "Radar de la réglementation commerciale", "tag": "Les évolutions quotidiennes du droit commercial de l'UE, des sanctions et des politiques concernant la Türkiye, la CEI et l'Asie centrale.",
            "latest": "Dernières évolutions", "status": "État des sources", "run": "Dernière exécution", "none": "Aucune évolution enregistrée pour le moment.",
            "src": "Source", "chg": "Évolution", "date": "Collecté", "about": "À propos", "aboutText": "Un projet de portfolio indépendant et non commercial de Said Maruf Özbek. Il utilise uniquement des sources publiques et n'est lié à aucun employeur ni à aucune institution. Vérifiez toujours le texte officiel en lien.",
            "licences": "Sources et licences", "other": ""}}
CHG = {"en": {"new": "New", "added": "Added", "removed": "Removed", "changed": "Changed"},
       "de": {"new": "Neu", "added": "Hinzugefügt", "removed": "Entfernt", "changed": "Geändert"},
       "tr": {"new": "Yeni", "added": "Eklendi", "removed": "Çıkarıldı", "changed": "Değişti"},
       "ru": {"new": "Новое", "added": "Добавлено", "removed": "Удалено", "changed": "Изменено"},
       "fr": {"new": "Nouveau", "added": "Ajouté", "removed": "Supprimé", "changed": "Modifié"}}
LANGS = {"en": "English", "de": "Deutsch", "tr": "Türkçe", "ru": "Русский", "fr": "Français"}
CSS = """:root{--bg:#f7f7f4;--fg:#1b1d22;--mute:#5d6270;--line:#dcdcd6;--card:#fff;--acc:#1f4fd1;--ok:#1d7a46;--bad:#b3261e}
@media(prefers-color-scheme:dark){:root{--bg:#121417;--fg:#e9e9ec;--mute:#a1a5b0;--line:#2b2f36;--card:#1a1d22;--acc:#8fb0ff;--ok:#5fcf8f;--bad:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
header,main,footer{max-width:960px;margin:0 auto;padding:16px}header{border-bottom:1px solid var(--line)}h1{margin:.2em 0;font-size:1.8rem}
.tag{color:var(--mute);margin:0}nav{display:flex;gap:16px;margin-top:8px;flex-wrap:wrap}a{color:var(--acc)}
.item{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.meta{color:var(--mute);font-size:.85rem;display:flex;gap:10px;flex-wrap:wrap}.pill{border:1px solid var(--line);border-radius:999px;padding:0 8px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:6px;border-bottom:1px solid var(--line);font-size:.9rem;vertical-align:top}
.ok{color:var(--ok)}.bad{color:var(--bad)}footer{color:var(--mute);font-size:.85rem;border-top:1px solid var(--line)}"""

def esc(v): return html.escape(str(v or ""))

def page(lang, items, status, sources):
    t, c = T[lang], CHG[lang]
    up = "" if lang == "en" else "../"
    css = up + "style.css"
    switch = "".join(f'<a href="{up}{"" if k == "en" else k + "/"}index.html"{" aria-current=page" if k == lang else ""}>{v}</a>' for k, v in LANGS.items())
    names = {s["id"]: s["name"] for s in sources}
    rows = "".join(
        f'<article class="item"><a href="{esc(i["link"])}" rel="noopener">{esc(i["title"])}</a>'
        f'<div class="meta"><span class="pill">{esc(c.get(i["change"], i["change"]))}</span><span>{esc(names.get(i["source"], i["source"]))}</span>'
        f'<span>{esc(i["jurisdiction"])}</span><span>{esc((i.get("collected") or "")[:10])}</span></div></article>'
        for i in items[:200]) or f"<p>{t['none']}</p>"
    st = "".join(f'<tr><td>{esc(names.get(s["source"], s["source"]))}</td><td class="{"ok" if s["ok"] else "bad"}">{"✓" if s["ok"] else "✕"} {esc(s["detail"])}</td></tr>' for s in status.get("sources", []))
    lic = "".join(f"<li>{esc(s['name'])}: {esc(s['licence'])}</li>" for s in sources)
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t['title']}</title><link rel="stylesheet" href="{css}"></head><body>
<header><h1>{t['title']}</h1><p class="tag">{t['tag']}</p><nav><a href="#latest">{t['latest']}</a><a href="#status">{t['status']}</a><a href="#about">{t['about']}</a>{switch}</nav></header>
<main><section id="latest"><h2>{t['latest']}</h2>{rows}</section>
<section id="status"><h2>{t['status']}</h2><p>{t['run']}: {esc(status.get('run', '—'))}</p><table>{st}</table></section>
<section id="about"><h2>{t['about']}</h2><p>{t['aboutText']}</p><h3>{t['licences']}</h3><ul>{lic}</ul></section></main>
<footer>© Said Maruf Özbek · Data: EUR-Lex, European Commission, OpenSanctions</footer></body></html>"""

def build(root):
    root = Path(root); data = root / "data"; out = root / "site"
    items = json.loads((data / "items.json").read_text("utf-8")) if (data / "items.json").exists() else []
    status = json.loads((data / "status.json").read_text("utf-8")) if (data / "status.json").exists() else {}
    sources = json.loads((root / "sources.json").read_text("utf-8"))["sources"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "style.css").write_text(CSS, "utf-8")
    for lang in LANGS:
        target = out if lang == "en" else out / lang
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(page(lang, items, status, sources), "utf-8")
    (out / "items.json").write_text(json.dumps(items, ensure_ascii=False), "utf-8")

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
