"""Spec + resolved claims + narration audio -> a HyperFrames project (one index.html, seeked GSAP timeline)."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .claims import ROOT
from .spec import Spec

HARNESS = ROOT / "video" / "harness"
TAIL_S = 1.0
LEAD_S = 0.4

FONTS = """
@font-face{font-family:'Atkinson Hyperlegible';font-weight:400;src:url(assets/fonts/AtkinsonHyperlegible-Regular.woff2) format('woff2')}
@font-face{font-family:'Atkinson Hyperlegible';font-weight:700;src:url(assets/fonts/AtkinsonHyperlegible-Bold.woff2) format('woff2')}
@font-face{font-family:Fredoka;font-weight:300 700;src:url(assets/fonts/Fredoka-Variable.woff2) format('woff2')}
"""
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#FFF8EA}
#root{width:1920px;height:1080px;position:relative;font-family:'Atkinson Hyperlegible',ui-sans-serif,system-ui,sans-serif;color:#2A2745}
.scene{position:absolute;left:0;top:0;width:1920px;height:1080px;background:#FFF8EA;overflow:hidden}
.band{position:absolute;left:0;top:0;width:1920px;height:14px;background:linear-gradient(90deg,#FFC93C,#FF9A3C,#FF7096,#8F73E0,#59B8F3,#6CC57A)}
.logo{position:absolute;left:120px;top:52px;height:76px}
.body{position:absolute;left:120px;top:170px;width:1180px;height:790px;display:flex;flex-direction:column;justify-content:center;gap:40px}
.pip{position:absolute;right:90px;bottom:70px;height:560px}
.foot{position:absolute;left:120px;bottom:40px;font-size:26px;color:#5b5878}
h1{font-family:Fredoka,sans-serif;font-size:104px;font-weight:700;line-height:1.05;letter-spacing:-.01em}
p.t{font-size:56px;font-weight:400;line-height:1.28}
.claim{display:flex;flex-direction:column;gap:2px}
.claim .num{font-family:Fredoka,sans-serif;font-size:170px;font-weight:700;line-height:1.05;color:#2F7D4A}
.claim .lab{font-size:44px;font-weight:700;line-height:1.2}
.src{font-size:26px;color:#5b5878}
.row{display:flex;align-items:center;gap:30px}
.rl{width:380px;font-size:44px;font-weight:700;line-height:1.1}
.track{width:560px;height:68px;background:#EFE3C8;border-radius:18px;overflow:hidden;flex:none}
.fill{height:68px;min-width:10px;border-radius:18px}
.rv{font-family:Fredoka,sans-serif;font-size:64px;font-weight:700;width:190px}
.good{background:#6CC57A;color:#2F7D4A}.bad{background:#FF7096;color:#B3363F}
.rv.good,.rv.bad{background:none}
ul{list-style:none;display:flex;flex-direction:column;gap:26px}
li{font-size:52px;font-weight:700;line-height:1.2;display:flex;align-items:flex-start;gap:26px}
li:before{content:"";width:28px;height:28px;margin-top:16px;border-radius:50%;background:#FFC93C;flex:none}
img.pic{max-height:560px;border-radius:24px;align-self:flex-start}
.left{position:absolute;left:120px;top:170px;width:780px;height:780px;display:flex;align-items:center;justify-content:center}
img.pic.big{width:760px;height:760px;object-fit:cover;border-radius:40px;box-shadow:0 20px 44px rgba(42,39,69,.28)}
.body.split{left:960px;width:840px;height:660px;top:170px;gap:30px}
.pip.small{height:230px;right:60px;bottom:36px}
.choices{display:flex;flex-direction:column;gap:20px}
.choice{font-size:40px;font-weight:700;line-height:1.2;padding:22px 30px;border-radius:26px;background:#fff;border:6px solid #EFE3C8}
.choice.correct{border-color:#6CC57A;background:#E7F6E9}
.split p.t{font-size:46px}
"""


def _spoken(narration: str, resolved: dict[str, dict]) -> str:
    out = narration
    for cid, r in resolved.items():
        out = out.replace("{" + cid + "}", r["spoken"])
    return out


def spoken_text(spec: Spec, resolved: dict[str, dict]) -> dict[str, str]:
    return {s.id: _spoken(s.narration, resolved) for s in spec.scenes}


def _sources(cids: list[str], resolved: dict[str, dict]) -> str:
    seen: list[str] = []
    for cid in cids:
        for s in resolved[cid]["sources"]:
            tag = s["ref"].split(":", 1)[1].split("#", 1)[0] if s["ref"].startswith("report:") else Path(s["file"]).name
            if tag not in seen:
                seen.append(tag)
    return html.escape("source: evidence/reports · " + " · ".join(seen))


def build(spec: Spec, resolved: dict[str, dict], audio: dict[str, tuple[Path, float]], out: Path) -> dict:
    """Write the project into `out`. `audio[scene id] = (mp3 path, seconds)`. Returns the timeline."""
    out.mkdir(parents=True, exist_ok=True)
    for f in ("hyperframes.json", "package.json"):
        shutil.copy(HARNESS / "template" / f, out / f)
    (out / "meta.json").write_text(json.dumps({"id": spec.title, "name": spec.title}), encoding="utf-8")
    (out / "vendor").mkdir(exist_ok=True)
    shutil.copy(HARNESS / "vendor" / "gsap.min.js", out / "vendor" / "gsap.min.js")
    (out / "audio").mkdir(exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets/brand/logo/storybound-lockup-horizontal.png", out / "assets" / "logo.png")
    shutil.copytree(ROOT / "assets" / "fonts", out / "assets" / "fonts", dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.txt", "Andika*"))
    for m in {sc.mood for sc in spec.scenes}:
        pose = sorted((ROOT / "assets/animation/owl-stills").glob(f"owl-*-{m}.png")) or sorted((ROOT / "assets/animation/owl-stills").glob("owl-01-*.png"))
        shutil.copy(pose[0], out / "assets" / f"pip-{m}.png")

    t, scenes, parts, audio_tags, js = 0.0, [], [], [], []
    for i, sc in enumerate(spec.scenes):
        mp3, vo = audio[sc.id]
        dur = max(sc.min_seconds, vo + LEAD_S + sc.pause)
        scenes.append({"id": sc.id, "start": round(t, 3), "dur": round(dur, 3), "vo": round(vo, 3)})
        shutil.copy(mp3, out / "audio" / f"vo-{i}.mp3")
        audio_tags.append(
            f'<audio id="vo-{i}" data-start="{t + LEAD_S:.3f}" data-duration="{vo:.3f}" '
            f'data-track-index="{10 + i}" src="audio/vo-{i}.mp3" data-volume="1"></audio>'
        )
        split = sc.layout == "split"
        head = [f'<div class="band" id="s{i}-band"></div><img class="logo" id="s{i}-brand" src="assets/logo.png"/>',
                f'<img class="pip{" small" if split else ""}" id="s{i}-pip" src="assets/pip-{sc.mood}.png"/>']
        left: list[str] = []
        body: list[str] = []
        js.append(f'tl.from("#s{i}-brand",{{opacity:0,duration:.4}},{t:.3f});')
        js.append(f'tl.from("#s{i}-pip",{{opacity:0,y:120,rotate:-6,duration:.7,ease:"back.out(1.6)"}},{t + 0.2:.3f});')
        for j, b in enumerate(sc.blocks):
            bid, at = f"s{i}b{j}", t + LEAD_S + (b.at_frac * vo if b.at_frac is not None else 0.35 * j)
            if b.type == "title":
                body.append(f'<h1 id="{bid}">{html.escape(b.text)}</h1>')
            elif b.type == "text":
                body.append(f'<p class="t" id="{bid}">{html.escape(b.text)}</p>')
            elif b.type == "claim":
                r = resolved[b.claim]
                body.append(
                    f'<div class="claim" id="{bid}"><div class="num">{html.escape(r["display"])}</div>'
                    f'<div class="lab">{html.escape(r["label"])}</div>'
                    f'<div class="src">{_sources([b.claim], resolved)}</div></div>'
                )
            elif b.type == "bars":
                rows, cids = [], []
                for k, it in enumerate(b.items):
                    r = resolved[it["claim"]]
                    cids.append(it["claim"])
                    tone = it.get("tone", "good")
                    pct = round(100 * (r["ratio"] or 0), 1)
                    rows.append(
                        f'<div class="row" id="{bid}r{k}"><div class="rl">{html.escape(it["label"])}</div>'
                        f'<div class="track"><div class="fill {tone}" id="{bid}f{k}" style="width:{pct}%"></div></div>'
                        f'<div class="rv {tone}">{html.escape(r["display"])}</div></div>'
                    )
                    js.append(
                        f'tl.from("#{bid}f{k}",{{width:"0%",duration:1.1,ease:"power2.out"}},{at + 0.3 + 0.25 * k:.3f});'
                    )
                body.append(f'<div id="{bid}" style="display:flex;flex-direction:column;gap:30px">{"".join(rows)}'
                            f'<div class="src">{_sources(cids, resolved)}</div></div>')  # fmt: skip
            elif b.type == "list":
                lis = "".join(f"<li>{html.escape(str(x))}</li>" for x in b.items)
                body.append(f'<ul id="{bid}">{lis}</ul>')
            elif b.type == "image":
                src = Path(b.src)
                (out / "assets").mkdir(exist_ok=True)
                shutil.copy(ROOT / src, out / "assets" / src.name)
                (left if split else body).append(f'<img class="pic{" big" if split else ""}" id="{bid}" src="assets/{src.name}"/>')
            elif b.type == "choices":
                cards = []
                for k, it in enumerate(b.items):
                    st = it.get("state", "neutral")
                    cards.append(f'<div class="choice {st}" id="{bid}c{k}">{html.escape(it["text"])}</div>')
                    if st == "wrong":
                        js.append(f'tl.to("#{bid}c{k}",{{opacity:.4,duration:.5}},{t + LEAD_S + 0.6:.3f});')
                    elif st == "correct":
                        js.append(f'tl.fromTo("#{bid}c{k}",{{scale:1}},{{scale:1.04,duration:.4,yoyo:true,repeat:1}},{t + LEAD_S + 0.3:.3f});')
                body.append(f'<div class="choices" id="{bid}">{"".join(cards)}</div>')
            js.append(f'tl.from("#{bid}",{{opacity:0,y:44,duration:.6,ease:"power2.out"}},{at:.3f});')
        foot = f'<div class="foot" id="s{i}-foot">#neatHack · every number on screen is read from an evidence file</div>' if sc.kind == "claim" else ""
        parts.append(
            f'<section id="scene-{i}" class="clip scene" data-start="{t:.3f}" data-duration="{dur:.3f}" data-track-index="1">'
            f'{"".join(head)}{"".join(left)}<div class="body{" split" if split else ""}" id="s{i}-body">{"".join(body)}</div>{foot}</section>'
        )
        t += dur
    total = round(t + TAIL_S, 3)
    doc = (
        '<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/>'
        f'<script src="vendor/gsap.min.js"></script><style>{FONTS}{CSS}</style></head><body>'
        f'<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">'
        f'{"".join(parts)}{"".join(audio_tags)}</div>'
        f'<script>const tl=gsap.timeline({{paused:true}});{"".join(js)}window.__timelines["main"]=tl;tl.seek(0);</script></body></html>'
    )
    (out / "index.html").write_text(doc, encoding="utf-8")
    return {"scenes": scenes, "total": total}
