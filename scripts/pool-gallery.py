#!/usr/bin/env python3
"""Render the Canva template pool as a standalone HTML gallery.

Reads .claude/skills/jetaasc-canva-flyer/templates.md and the thumbnails in
the sibling thumbs/ folder (one <template id>.jpg per entry, saved by the
scout skill), embeds the images, and writes the page to the path given as
the first argument (default: pool-gallery.html in the current directory).
Publish the result with the Artifact tool.
"""
import base64, html, json, re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
skill = root / '.claude/skills/jetaasc-canva-flyer'
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'pool-gallery.html')

pool, sec = [], None
for line in (skill / 'templates.md').read_text().splitlines():
    if line.startswith('## '): sec = line[3:].strip()
    elif line.startswith('### '): pool.append({'section': sec, 'name': line[4:].strip()})
    elif pool and line.startswith('- '):
        key, _, val = line[2:].partition(':')
        pool[-1][key.strip().lower()] = val.strip()
for o in pool:
    m = re.search(r'[?&]template=([^&]+)', o.get('editor', ''))
    o['id'] = m.group(1) if m else re.search(r'templates/([A-Za-z0-9_-]+?)-[a-z]', o['template']).group(1)

sections = []
for o in pool:
    if not sections or sections[-1][0] != o['section']: sections.append((o['section'], []))
    sections[-1][1].append(o)

def card(o):
    img = skill / 'thumbs' / f"{o['id']}.jpg"
    if img.exists():
        src = 'data:image/jpeg;base64,' + base64.b64encode(img.read_bytes()).decode()
        thumb = f'<a class="thumb" href="{html.escape(o["template"])}" target="_blank" rel="noopener"><img src="{src}" alt="{html.escape(o["name"])} preview"></a>'
    else:
        thumb = '<div class="thumb missing">No thumbnail yet</div>'
    last = o.get('last used', '')
    used = f'<span class="used">Last used {html.escape(last)}</span>' if last else '<span class="used fresh">Not used yet</span>'
    flag = ' <span class="flag">Weak style fit</span>' if 'eak style fit' in o.get('look', '') else ''
    return f'''<article class="card">
  {thumb}
  <div class="body">
    <h3>{html.escape(o['name'])}{flag}</h3>
    {used}
    <p class="look">{html.escape(o.get('look', ''))}</p>
    <details><summary>Slots and traps</summary>
      <p><strong>Slots.</strong> {html.escape(o.get('slots', ''))}</p>
      <p><strong>Watch.</strong> {html.escape(o.get('watch', ''))}</p>
    </details>
    <p class="links"><a href="{html.escape(o['template'])}" target="_blank" rel="noopener">Template page</a><a href="{html.escape(o.get('editor', '#'))}" target="_blank" rel="noopener">Open in editor</a><code>{o['id']}</code></p>
  </div>
</article>'''

secs = ''.join(
    f'<section><h2>{html.escape(name)}<span class="count">{len(items)}</span></h2><div class="grid">{"".join(card(o) for o in items)}</div></section>'
    for name, items in sections)

page = f'''<title>JETAASC Template Pool</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@500;700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--bg:#F4F3EE;--ink:#1E2229;--muted:#5F6672;--rule:#D9D6CE;--card:#FFFFFF;--accent:#2B4C7E;--flag:#8A4B12;--flag-bg:#F6E7D4;--fresh:#2E6B3F;--fresh-bg:#DFF0E2}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#15171B;--ink:#E7E5DF;--muted:#A3A7AF;--rule:#2C3037;--card:#1E2126;--accent:#8FB4EA;--flag:#F0C08A;--flag-bg:#3A2A17;--fresh:#9BD6A8;--fresh-bg:#1E3324}}}}
:root[data-theme="dark"]{{--bg:#15171B;--ink:#E7E5DF;--muted:#A3A7AF;--rule:#2C3037;--card:#1E2126;--accent:#8FB4EA;--flag:#F0C08A;--flag-bg:#3A2A17;--fresh:#9BD6A8;--fresh-bg:#1E3324}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Source Sans 3",system-ui,sans-serif;padding-inline:clamp(16px,4vw,48px);padding-block:32px 64px}}
header{{max-width:72ch;margin-bottom:40px}}
h1{{font-family:"Zen Kaku Gothic New",system-ui,sans-serif;font-weight:700;font-size:2rem;margin:0 0 8px;text-wrap:balance}}
header p{{margin:0 0 8px;color:var(--muted)}}
.bar{{display:flex;flex-wrap:wrap;gap:8px 24px;font-size:.9rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;margin-top:16px}}
h2{{font-family:"Zen Kaku Gothic New",system-ui,sans-serif;font-weight:500;font-size:1.25rem;margin:40px 0 16px;display:flex;align-items:baseline;gap:10px}}
.count{{font-size:.8rem;color:var(--muted);letter-spacing:.04em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}}
.card{{display:grid;grid-template-columns:150px 1fr;gap:16px;background:var(--card);border:1px solid var(--rule);padding:14px}}
.thumb img{{display:block;width:100%;max-width:100%;height:auto;border:1px solid var(--rule)}}
.thumb.missing{{aspect-ratio:17/22;border:1px dashed var(--rule);color:var(--muted);font-size:.85rem;display:grid;place-items:center;text-align:center;padding:8px}}
.body{{min-width:0;display:flex;flex-direction:column;gap:8px}}
h3{{font-family:"Zen Kaku Gothic New",system-ui,sans-serif;font-weight:500;font-size:1.05rem;line-height:1.3;margin:0;text-wrap:balance}}
.flag,.used{{display:inline-block;font-size:.72rem;letter-spacing:.05em;text-transform:uppercase;padding:2px 8px;border-radius:2px;font-weight:600}}
.flag{{color:var(--flag);background:var(--flag-bg);margin-left:8px;vertical-align:middle}}
.used{{color:var(--muted);background:var(--bg);align-self:flex-start}}
.used.fresh{{color:var(--fresh);background:var(--fresh-bg)}}
.look{{margin:0;font-size:.95rem}}
details{{font-size:.9rem;color:var(--muted)}}
summary{{cursor:pointer;color:var(--accent);font-weight:600}}
details p{{margin:8px 0 0}}
.links{{margin:auto 0 0;display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:.9rem}}
.links a{{color:var(--accent);font-weight:600;text-decoration:none;border-bottom:1px solid transparent}}
.links a:hover,.links a:focus-visible{{border-bottom-color:var(--accent);outline:none}}
code{{font:.8rem ui-monospace,Menlo,monospace;color:var(--muted)}}
@media (max-width:440px){{.card{{grid-template-columns:1fr}}.thumb{{max-width:200px}}}}
</style>
<header>
<h1>JETAASC Template Pool</h1>
<p>Every Canva template the flyer skill may pick from, grouped by the event type it suits. Click a thumbnail for the template page; "Open in editor" starts a fresh design from it.</p>
<div class="bar"><span>{len(pool)} templates</span><span>All free, single page, no headshot slot</span><span>Style bar: casual and Japan-oriented, never corporate</span></div>
</header>
{secs}
'''
out.write_text(page)
print(f'{out} ({len(page)//1024} KB, {len(pool)} templates)')
