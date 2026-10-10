import base64, io, json, math, os, subprocess, sys
from PIL import Image

A = 'D:/neatlogs/assets'                      # assets root
S = sys.argv[1]                               # scratch dir
B = A + '/brand'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
INK, CREAM, PAPER2 = '#2A2745', '#FFF8EA', '#FDEFD3'
SUN, TANG, TANGD, BERRY, SKY, LEAF, GRAPE = '#FFC93C', '#FF9A3C', '#E8710A', '#FF7096', '#59B8F3', '#6CC57A', '#8F73E0'
for d in ('logo', 'favicon', 'social', 'video'):
    os.makedirs(f'{B}/{d}', exist_ok=True)
WM = json.load(open(S + '/brandgen/wordmark.json'))
FU = 'file:///' + A                           # file URL root for assets
BU = 'file:///' + B


def w(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def shot(html_path, out, W, H, transparent=False):
    args = [EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
            f'--window-size={W},{H}', '--virtual-time-budget=4000', f'--screenshot={out}']
    if transparent:
        args.append('--default-background-color=00000000')
    args.append('file:///' + html_path)
    subprocess.run(args, capture_output=True)
    im = Image.open(out)
    if im.size != (W, H):                     # headless can pad: crop to exact size
        im.crop((0, 0, W, H)).save(out)


# ---------------------------------------------------------------- wordmark
def wordmark_svg(c1, c2):
    wd = WM['full']['w']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -790 {wd + 60} 1000" role="img" aria-label="Storybound">'
            f'<title>Storybound</title><path fill="{c1}" d="{WM["story"]["d"]}"/>'
            f'<path fill="{c2}" transform="translate({WM["story"]["w"]},0)" d="{WM["bound"]["d"]}"/></svg>')


WM_RATIO = (WM['full']['w'] + 60) / 1000      # width / height of the wordmark viewBox


# ---------------------------------------------------------------- mark (seal badge + Pip)
def owl_b64():
    im = Image.open(A + '/animation/owl-stills/owl-01-happy-flap.png').convert('RGBA').crop((60, 0, 720, 660)).resize((520, 520), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return base64.b64encode(b.getvalue()).decode()


def seal_path(cx, cy, R, n=22, a=11):
    pts = []
    for i in range(720):
        t = 2 * math.pi * i / 720
        r = R + a * abs(math.cos(n * t / 2))
        pts.append(f'{cx + r * math.cos(t):.1f},{cy + r * math.sin(t):.1f}')
    return 'M' + ' L'.join(pts) + 'Z'


def star(cx, cy, r, fill=SUN):
    k = r * 0.28
    return (f'<path d="M{cx},{cy - r} Q{cx + k},{cy - k} {cx + r},{cy} Q{cx + k},{cy + k} {cx},{cy + r} Q{cx - k},{cy + k} {cx - r},{cy} '
            f'Q{cx - k},{cy - k} {cx},{cy - r}Z" fill="{fill}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')


def mark_svg():
    cx, cy = 320, 330
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 640 730" role="img" aria-label="Storybound mark">
<title>Storybound</title>
<defs><filter id="sh" x="-15%" y="-15%" width="130%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="8" flood-color="{INK}" flood-opacity="0.28"/></filter>
<clipPath id="cp"><circle cx="{cx}" cy="{cy}" r="205"/><rect x="{cx - 205}" y="-40" width="410" height="{cy + 40}"/></clipPath></defs>
<path d="M232 520 L196 700 L252 668 L290 716 L318 560Z" fill="{TANG}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>
<path d="M408 520 L444 700 L388 668 L350 716 L322 560Z" fill="{BERRY}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>
<g filter="url(#sh)"><path d="{seal_path(cx, cy, 282, a=12)}" fill="#FFFFFF"/></g>
<path d="{seal_path(cx, cy, 262)}" fill="{SUN}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>
<circle cx="{cx}" cy="{cy}" r="205" fill="#FFF1B8" stroke="{INK}" stroke-width="8"/>
<path d="M170 215 A165 165 0 0 1 300 150" fill="none" stroke="#FFFFFF" stroke-opacity="0.8" stroke-width="12" stroke-linecap="round"/>
<g clip-path="url(#cp)"><image x="{cx - 250}" y="{cy - 262}" width="500" height="500" xlink:href="data:image/png;base64,{owl_b64()}"/></g>
{star(70, 110, 30)}{star(578, 96, 24)}{star(594, 372, 16)}
</svg>'''


w(f'{B}/logo/storybound-mark.svg', mark_svg())
for nm, c1, c2 in (('color', INK, TANGD), ('ink', INK, INK), ('white', '#FFFFFF', '#FFFFFF'), ('on-dark', '#FFFFFF', TANG)):
    w(f'{B}/logo/storybound-wordmark-{nm}.svg', wordmark_svg(c1, c2))


def lockup_h(c1, c2):
    mh, mw = 330, 330 * 640 / 730                 # mark scaled
    wh = 190                                      # wordmark height
    ww = wh * WM_RATIO
    gap = 30
    W = mw + gap + ww; H = 330
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W:.0f} {H}" role="img" aria-label="Storybound"><title>Storybound</title>'
            f'<svg x="0" y="0" width="{mw:.0f}" height="{mh}" viewBox="0 0 640 730">{mark_svg().split(">", 1)[1].rsplit("</svg>", 1)[0]}</svg>'
            f'<svg x="{mw + gap:.0f}" y="{(H - wh) / 2 - 8:.0f}" width="{ww:.0f}" height="{wh}" viewBox="-30 -790 {WM["full"]["w"] + 60} 1000">'
            f'<path fill="{c1}" d="{WM["story"]["d"]}"/><path fill="{c2}" transform="translate({WM["story"]["w"]},0)" d="{WM["bound"]["d"]}"/></svg></svg>'), W, H


def lockup_v(c1, c2):
    mh, mw = 520, 520 * 640 / 730
    wh = 200; ww = wh * WM_RATIO
    W = max(mw, ww) + 40; H = mh + wh + 20
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Storybound"><title>Storybound</title>'
            f'<svg x="{(W - mw) / 2:.0f}" y="0" width="{mw:.0f}" height="{mh}" viewBox="0 0 640 730">{mark_svg().split(">", 1)[1].rsplit("</svg>", 1)[0]}</svg>'
            f'<svg x="{(W - ww) / 2:.0f}" y="{mh + 10}" width="{ww:.0f}" height="{wh}" viewBox="-30 -790 {WM["full"]["w"] + 60} 1000">'
            f'<path fill="{c1}" d="{WM["story"]["d"]}"/><path fill="{c2}" transform="translate({WM["story"]["w"]},0)" d="{WM["bound"]["d"]}"/></svg></svg>'), W, H


LH, LHW, LHH = lockup_h(INK, TANGD)
LHD, _, _ = lockup_h('#FFFFFF', TANG)
LV, LVW, LVH = lockup_v(INK, TANGD)
LVD, _, _ = lockup_v('#FFFFFF', TANG)
w(f'{B}/logo/storybound-lockup-horizontal.svg', LH)
w(f'{B}/logo/storybound-lockup-horizontal-on-dark.svg', LHD)
w(f'{B}/logo/storybound-lockup-stacked.svg', LV)
w(f'{B}/logo/storybound-lockup-stacked-on-dark.svg', LVD)

# PNG exports of the logo files
def svg_png(svg_file, out, W, H, bg=None):
    html = f'<!doctype html><meta charset="utf-8"><body style="margin:0;background:{bg or "transparent"}"><img src="file:///{svg_file}" style="width:{W}px;height:{H}px;display:block;object-fit:contain">'
    hp = f'{S}/brandgen/_t.html'; w(hp, html); shot(hp, out, W, H, transparent=bg is None)


mk_w = 1024
svg_png(f'{B}/logo/storybound-mark.svg', f'{B}/logo/storybound-mark-1024.png', 1024, 1168)
svg_png(f'{B}/logo/storybound-mark.svg', f'{B}/logo/storybound-mark-512.png', 512, 584)
svg_png(f'{B}/logo/storybound-lockup-horizontal.svg', f'{B}/logo/storybound-lockup-horizontal.png', 1600, round(1600 * LHH / LHW))
svg_png(f'{B}/logo/storybound-lockup-horizontal-on-dark.svg', f'{B}/logo/storybound-lockup-horizontal-on-dark.png', 1600, round(1600 * LHH / LHW))
svg_png(f'{B}/logo/storybound-lockup-stacked.svg', f'{B}/logo/storybound-lockup-stacked.png', 1200, round(1200 * LVH / LVW))
svg_png(f'{B}/logo/storybound-lockup-stacked-on-dark.svg', f'{B}/logo/storybound-lockup-stacked-on-dark.png', 1200, round(1200 * LVH / LVW))
svg_png(f'{B}/logo/storybound-wordmark-color.svg', f'{B}/logo/storybound-wordmark-color.png', 1600, round(1600 / WM_RATIO))
svg_png(f'{B}/logo/storybound-wordmark-on-dark.svg', f'{B}/logo/storybound-wordmark-on-dark.png', 1600, round(1600 / WM_RATIO))

# ---------------------------------------------------------------- favicon (simplified vector Pip, readable at 16 px)
FAV = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Storybound"><title>Storybound</title>
<rect width="512" height="512" rx="112" fill="{SUN}"/>
<path d="M118 200 L96 92 L204 152Z" fill="#8A5530" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>
<path d="M394 200 L416 92 L308 152Z" fill="#8A5530" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>
<ellipse cx="256" cy="300" rx="178" ry="160" fill="#B9794F" stroke="{INK}" stroke-width="14"/>
<circle cx="184" cy="268" r="78" fill="#F6E7C6" stroke="{INK}" stroke-width="10"/>
<circle cx="328" cy="268" r="78" fill="#F6E7C6" stroke="{INK}" stroke-width="10"/>
<circle cx="190" cy="274" r="40" fill="#5A3418"/><circle cx="322" cy="274" r="40" fill="#5A3418"/>
<circle cx="204" cy="258" r="13" fill="#FFFFFF"/><circle cx="336" cy="258" r="13" fill="#FFFFFF"/>
<path d="M226 322 L286 322 L256 376Z" fill="#F5A33A" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>
</svg>'''
w(f'{B}/favicon/favicon.svg', FAV)
FAV_MASK = FAV.replace('<rect width="512" height="512" rx="112" fill="%s"/>' % SUN, '<rect width="512" height="512" fill="%s"/>' % SUN)
# maskable: full-bleed background, art inside the central 80%
w(f'{B}/favicon/_maskable.svg', FAV_MASK.replace('<path d="M118', '<g transform="translate(51 51) scale(0.8)"><path d="M118', 1).replace('</svg>', '</g></svg>'))
for size in (16, 32, 48, 180, 192, 512):
    svg_png(f'{B}/favicon/favicon.svg', f'{B}/favicon/favicon-{size}.png', size, size)
svg_png(f'{B}/favicon/_maskable.svg', f'{B}/favicon/maskable-512.png', 512, 512)
Image.open(f'{B}/favicon/favicon-180.png').save(f'{B}/favicon/apple-touch-icon.png')
Image.open(f'{B}/favicon/favicon-192.png').save(f'{B}/favicon/android-chrome-192.png')
Image.open(f'{B}/favicon/favicon-512.png').save(f'{B}/favicon/android-chrome-512.png')
Image.open(f'{B}/favicon/favicon-48.png').save(f'{B}/favicon/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
os.remove(f'{B}/favicon/_maskable.svg')
w(f'{B}/favicon/site.webmanifest', json.dumps({'name': 'Storybound', 'short_name': 'Storybound', 'start_url': '/', 'display': 'standalone', 'background_color': CREAM, 'theme_color': SUN,
    'icons': [{'src': 'android-chrome-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': 'android-chrome-512.png', 'sizes': '512x512', 'type': 'image/png'},
              {'src': 'maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}, indent=1))
w(f'{B}/favicon/head-snippet.html', '''<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#FFC93C">
<meta property="og:image" content="/og-1200x630.png">
''')

# ---------------------------------------------------------------- social + video pages
OWL = {n: f'{FU}/animation/owl-stills/owl-{n}.png' for n in ()}
import glob
for p in glob.glob(A + '/animation/owl-stills/owl-*.png'):
    OWL[int(os.path.basename(p)[4:6])] = 'file:///' + p.replace('\\', '/')
STK = {k: f'{FU}/art/stickers/promise/{k}.svg' for k in ('safe', 'hero-name', 'one-answer', 'lesson', 'pictures', 'voice', 'polished')}
GRASS = f'{FU}/art/nature/grass-1-cutout.webp'
LOGO_H = f'{BU}/logo/storybound-lockup-horizontal.svg'
LOGO_V = f'{BU}/logo/storybound-lockup-stacked.svg'
MARK = f'{BU}/logo/storybound-mark.svg'
SP = f'{FU}/brand/sponsors'
CSS = f'''
@font-face{{font-family:Fredoka;src:url({FU}/fonts/Fredoka-Variable.woff2);font-weight:300 700}}
@font-face{{font-family:Atkinson;src:url({FU}/fonts/AtkinsonHyperlegible-Regular.woff2);font-weight:400}}
@font-face{{font-family:Atkinson;src:url({FU}/fonts/AtkinsonHyperlegible-Bold.woff2);font-weight:700}}
*{{box-sizing:border-box}} body{{margin:0;overflow:hidden;position:relative;color:{INK};font-family:Atkinson,sans-serif}}
.f{{font-family:Fredoka,sans-serif;font-weight:700}} .abs{{position:absolute}}
.dots{{background:{CREAM} radial-gradient(circle,rgba(42,39,69,.07) 2.4px,transparent 2.6px) 0 0/40px 40px}}
.grass{{position:absolute;left:0;right:0;bottom:-6px;height:100px;background:url({GRASS}) repeat-x bottom/auto 100px}}
.pill{{display:inline-block;background:{INK};color:{CREAM};border-radius:999px;padding:10px 26px;font-family:Fredoka;font-weight:700}}
'''


def page(W, H, body, name, folder, transparent=False, cls='dots'):
    html = f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><body class="{"" if transparent else cls}" style="width:{W}px;height:{H}px;background-color:{"transparent" if transparent else CREAM}">{body}</body>'
    hp = f'{S}/brandgen/{name}.html'; w(hp, html)
    out = f'{B}/{folder}/{name}.png'; shot(hp, out, W, H, transparent); return out


def img(src, x, y, h=None, wd=None, extra=''):
    st = f'left:{x}px;top:{y}px;' + (f'height:{h}px;' if h else '') + (f'width:{wd}px;' if wd else '') + extra
    return f'<img class="abs" src="{src}" style="{st}">'


def stickers(positions, size):
    keys = ['safe', 'hero-name', 'one-answer', 'lesson', 'pictures', 'voice']
    return ''.join(img(STK[k], x, y, size, size) for k, (x, y) in zip(keys, positions))


def hero(W, H, ox=0, oy=0):
    """OG-style composition inside a 1200x630 stage, offset for other canvases."""
    body = f'<div class="abs" style="left:{ox}px;top:{oy}px;width:1200px;height:630px">'
    body += f'<div class="abs" style="left:640px;top:70px;width:520px;height:520px;border-radius:50%;background:{SUN}"></div>'
    body += img(LOGO_H, 60, 50, 118)
    body += f'<div class="f abs" style="left:64px;top:218px;width:560px;font-size:62px;line-height:1.08">A story agent that keeps its <span style="color:{TANGD}">promises.</span></div>'
    body += f'<div class="abs" style="left:66px;top:430px;width:540px;font-size:31px;line-height:1.25">Draw a picture, pick a lesson, get a story checked page by page.</div>'
    body += f'<div class="abs pill" style="left:66px;top:540px;font-size:30px">#neatHack</div>'
    body += img(OWL[1], 700, 90, 440)
    body += stickers([(640, 40), (1040, 30), (1075, 270), (1020, 470), (650, 480), (590, 250)], 112)
    return body + '</div>'


# OG 1200x630 and GitHub 1280x640
def hero(W, H, ox=0, oy=0):
    body = f'<div class="abs" style="left:{ox}px;top:{oy}px;width:1200px;height:630px">'
    body += f'<div class="abs" style="left:650px;top:70px;width:500px;height:500px;border-radius:50%;background:{SUN}"></div>'
    body += img(LOGO_H, 60, 44, 118)
    body += f'<div class="f abs" style="left:64px;top:196px;width:560px;font-size:56px;line-height:1.1">A story agent that keeps its <span style="color:{TANGD}">promises.</span></div>'
    body += f'<div class="abs" style="left:66px;top:350px;width:520px;font-size:30px;line-height:1.25">Draw a picture, pick a lesson, get a story checked page by page.</div>'
    body += f'<div class="abs pill" style="left:66px;top:446px;font-size:30px">#neatHack</div>'
    body += img(OWL[1], 710, 90, 430)
    keys = ['safe', 'hero-name', 'one-answer', 'lesson', 'pictures', 'voice']
    pos = [(650, 40, 112), (1050, 30, 112), (1085, 270, 112), (1020, 420, 112), (640, 420, 112), (612, 236, 96)]
    for k, (x, y, s) in zip(keys, pos):
        body += img(STK[k], x, y, s, s)
    return body + '</div>'


page(1200, 630, '<div class="grass"></div>' + hero(1200, 630), 'og-1200x630', 'social')
page(1280, 640, '<div class="grass"></div>' + hero(1280, 640, 40, 5), 'github-social-1280x640', 'social')

# X post: the oath
card = f'<div class="abs" style="left:720px;top:96px;width:420px;height:470px;background:{PAPER2};border:8px solid {INK};border-radius:30px;transform:rotate(2deg);box-shadow:0 12px 0 rgba(42,39,69,.2)"></div>'
card += f'<div class="f abs" style="left:756px;top:122px;font-size:40px;transform:rotate(2deg)">The oath</div>'
rows = [('safe', 'Safe and kind'), ('hero-name', "Hero's name, every page"), ('one-answer', 'One right answer'), ('lesson', 'The lesson, every page'), ('pictures', 'Pictures match the hero'), ('voice', 'Reads aloud')]
for i, (k, t) in enumerate(rows):
    y = 184 + i * 62
    card += f'<div class="abs" style="left:{756 + i * 0.5}px;top:{y}px;transform:rotate(2deg);display:flex;align-items:center;gap:14px;font-size:24px;font-weight:700;white-space:nowrap"><img src="{STK[k]}" style="height:54px"><span>{t}</span></div>'
body = '<div class="grass"></div>' + img(OWL[2], 930, 0, 190)
body += img(MARK, 64, 52, 96)
body += f'<div class="f abs" style="left:64px;top:190px;width:600px;font-size:92px;line-height:1.02">Write the <span style="color:{TANGD}">oath</span> first.</div>'
body += f'<div class="abs" style="left:68px;top:410px;width:560px;font-size:34px;line-height:1.25">Before a single page exists, Storybound lists what it owes the child.</div>'
body += f'<div class="abs pill" style="left:68px;top:560px;font-size:30px">#neatHack</div>' + card
page(1200, 675, body, 'x-post-idea-1200x675', 'social')


# X post: caught before the child saw it (illustration)
def pagecard(x, chip, chipbg, chipfg, icon):
    c = f'<div class="abs" style="left:{x}px;top:230px;width:340px;height:300px;background:#FFFFFF;border:8px solid {INK};border-radius:28px;box-shadow:0 12px 0 rgba(42,39,69,.2)">'
    c += f'<div class="f" style="position:absolute;left:24px;top:16px;font-size:32px">Page 5</div>'
    c += ''.join(f'<div style="position:absolute;left:24px;top:{74 + i * 32}px;width:{[260, 280, 220, 250][i]}px;height:16px;border-radius:8px;background:#E3DEF0"></div>' for i in range(4))
    c += f'<div style="position:absolute;left:16px;bottom:16px;white-space:nowrap;background:{chipbg};color:{chipfg};border:5px solid {INK};border-radius:999px;padding:5px 16px;font-size:22px;font-weight:700">{icon} {chip}</div></div>'
    return c


arrow = f'<svg class="abs" style="left:430px;top:300px" width="150" height="90" viewBox="0 0 120 100"><path d="M10 50 H92 M64 18 L96 50 L64 82" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg>'
body = '<div class="grass"></div>'
body += f'<div class="f abs" style="left:64px;top:50px;width:1100px;font-size:70px;line-height:1.02">Caught <span style="color:{TANGD}">before</span> the child saw it.</div>'
body += pagecard(60, "Hero's name missing", GRAPE, '#FFFFFF', '?') + arrow + pagecard(690, 'Promise kept', LEAF, INK, '&#10003;')
body += img(OWL[7], 430, 420, 215) + img(OWL[4], 1010, 400, 215)
body += f'<div class="abs" style="left:68px;top:150px;font-size:30px;width:900px">Illustration: the page is rewritten before it is shown.  #neatHack</div>'
page(1200, 675, body, 'x-post-trace-1200x675', 'social')


# X post: numbers (TEMPLATE, not real data)
def bar(y, label, wd, color, val):
    return (f'<div class="abs f" style="left:64px;top:{y}px;font-size:36px;width:300px">{label}</div>'
            f'<div class="abs" style="left:360px;top:{y - 4}px;width:{wd}px;height:64px;background:{color};border:6px solid {INK};border-radius:32px"></div>'
            f'<div class="abs f" style="left:{360 + wd + 24}px;top:{y - 2}px;font-size:46px">{val}</div>')


body = '<div class="grass"></div>'
body += f'<div class="f abs" style="left:64px;top:50px;width:1100px;font-size:70px;line-height:1.02">Same oath. <span style="color:{TANGD}">Same drawings.</span></div>'
body += f'<div class="abs pill" style="left:68px;top:160px;font-size:28px;background:{BERRY};color:{INK}">TEMPLATE: numbers are not real</div>'
body += bar(290, 'Observe only', 560, BERRY, '?? of ??') + bar(400, 'Gated', 180, LEAF, '?? of ??')
body += f'<div class="abs" style="left:68px;top:500px;font-size:28px;width:720px;line-height:1.25">Stories that shipped with a broken promise. Fill the numbers from the ledger before posting.</div>'
body += img(OWL[14], 880, 380, 270, extra='z-index:3')
page(1200, 675, body, 'x-post-numbers-TEMPLATE-1200x675', 'social')

# X header 1500x500, avatar 400, README banner 1600x400
body = '<div class="grass"></div>' + img(LOGO_H, 372, 100, 160)
body += f'<div class="abs f" style="left:0;width:1500px;top:300px;text-align:center;font-size:44px">A story agent that keeps its promises.</div>'
body += img(OWL[14], 70, 30, 270) + img(OWL[4], 1190, 80, 260)
page(1500, 500, body, 'x-header-1500x500', 'social')
page(400, 400, f'<div class="abs" style="left:0;top:0;width:400px;height:400px;background:{SUN}"></div>' + img(MARK, 62, 34, 340), 'x-avatar-400x400', 'social')
body = '<div class="grass"></div>' + img(LOGO_H, 60, 60, 170) + f'<div class="abs f" style="left:62px;top:262px;font-size:40px;width:780px">A story agent that keeps its promises.</div>'
keys = ['safe', 'hero-name', 'one-answer', 'lesson', 'pictures', 'voice']
for i, k in enumerate(keys):
    body += img(STK[k], 900 + (i % 3) * 124, 40 + (i // 3) * 124, 112, 112)
body += img(OWL[1], 1310, 24, 300)
page(1600, 400, body, 'readme-banner-1600x400', 'social')

# video: title card, end card, thumbnail
body = '<div class="grass"></div>' + img(LOGO_V, 425, 30, 700)
body += f'<div class="abs f" style="left:0;width:1920px;top:770px;text-align:center;font-size:58px">A story agent that keeps its <span style="color:{TANGD}">promises.</span></div>'
body += f'<div class="abs pill" style="left:780px;top:880px;font-size:38px">neatHack 2026</div>' + img(OWL[1], 20, 440, 380) + img(OWL[15], 1500, 450, 380)
page(1920, 1080, body, 'title-card-1920x1080', 'video')


def chip(src, h=64):
    return f'<div style="display:flex;align-items:center;justify-content:center;background:#FFFFFF;border:6px solid {INK};border-radius:28px;padding:22px 30px;height:{h + 44 + 12}px"><img src="{src}" style="height:{h}px"></div>'


SPONS = [f'{SP}/neatlogs-icon-256.png', f'{SP}/entire-brand-kit/entire-brand-kit/lockup/entire-lockup-dark.svg', f'{SP}/cfo-ai-mark.svg']
body = '<div class="grass"></div>' + img(LOGO_V, 90, 150, 520)
body += f'<div class="f abs" style="left:960px;top:150px;font-size:60px;width:800px">Built in 48 hours with</div>'
body += f'<div class="abs" style="left:960px;top:260px;display:flex;gap:36px;align-items:center">{"".join(chip(s) for s in SPONS)}</div>'
body += f'<div class="abs" style="left:960px;top:470px;font-size:40px;width:760px;line-height:1.3">The repo, the traces, the checkpoints and the model are linked below.</div>'
body += f'<div class="abs pill" style="left:960px;top:650px;font-size:48px">#neatHack</div>' + img(OWL[14], 1480, 620, 400)
page(1920, 1080, body, 'end-card-1920x1080', 'video')

body = '<div class="grass"></div>' + f'<div class="f abs" style="left:60px;top:70px;width:700px;font-size:104px;line-height:1">A story agent that <span style="color:{TANGD}">keeps its promises</span></div>'
body += f'<div class="abs pill" style="left:64px;top:550px;font-size:40px">#neatHack</div>'
body += f'<div class="abs" style="left:780px;top:70px;width:440px;height:440px;border-radius:50%;background:{SUN}"></div>' + img(OWL[4], 800, 100, 430)
keys = ['safe', 'hero-name', 'one-answer', 'lesson', 'pictures', 'voice']
pos = [(760, 20), (1120, 40), (1140, 300), (1060, 470), (700, 450), (690, 260)]
for k, (x, y) in zip(keys, pos):
    body += img(STK[k], x, y, 120, 120)
page(1280, 720, body, 'thumbnail-1280x720', 'video')

# video: lower thirds (transparent) and five-point bars (transparent)
for nm, src, title, role in (('neatlogs', SPONS[0], 'neatlogs', 'the flight recorder'), ('entire', f'{SP}/entire-brand-kit/entire-brand-kit/symbol/entire-symbol-dark.svg', 'Entire', 'the memory of the build'), ('cfo-ai', SPONS[2], 'cfo.ai', 'the business model')):
    body = (f'<div class="abs" style="left:80px;top:870px;display:flex;align-items:center;gap:28px;background:{CREAM};border:8px solid {INK};border-radius:40px;padding:22px 44px 22px 26px;box-shadow:0 10px 0 rgba(42,39,69,.25)">'
            f'<img src="{src}" style="height:92px;border-radius:18px"><div><div class="f" style="font-size:58px;line-height:1">{title}</div><div style="font-size:32px;margin-top:6px">{role}</div></div></div>')
    page(1920, 1080, body, f'lower-third-{nm}-1920x1080', 'video', transparent=True)
pts = ['Architecture', 'Implementation', 'Runtime', 'Reasoning', 'Result']
for i, p in enumerate(pts):
    chips = ''.join(f'<div class="f" style="background:{SUN if j == i else "rgba(255,248,234,.88)"};border:6px solid {INK};border-radius:999px;padding:10px 28px;font-size:36px;opacity:{1 if j == i else .85}">{j + 1}  {q}</div>' for j, q in enumerate(pts))
    page(1920, 1080, f'<div class="abs" style="left:80px;top:56px;display:flex;gap:14px">{chips}</div>', f'five-points-{i + 1}-{p.lower()}-1920x1080', 'video', transparent=True)
print('done')
