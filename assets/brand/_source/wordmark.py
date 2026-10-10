import json, sys, io
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb
src, out = sys.argv[1], sys.argv[2]
f = TTFont(src); f = instancer.instantiateVariableFont(f, {'wght': 700})
f.flavor = None; buf = io.BytesIO(); f.save(buf); data = buf.getvalue()
face = hb.Face(data); font = hb.Font(face)
upem = f['head'].unitsPerEm; gs = f.getGlyphSet(); order = f.getGlyphOrder()
def shape(text):
    b = hb.Buffer(); b.add_str(text); b.guess_segment_properties(); hb.shape(font, b, {'kern': True})
    x = 0; parts = []
    for info, pos in zip(b.glyph_infos, b.glyph_positions):
        name = order[info.codepoint]; pen = SVGPathPen(gs)
        tp = TransformPen(pen, (1, 0, 0, -1, x + pos.x_offset, -pos.y_offset)); gs[name].draw(tp)
        parts.append(pen.getCommands()); x += pos.x_advance
    return ' '.join(parts), x
res = {}
for key, text in (('story','Story'),('bound','bound'),('full','Storybound')):
    d, w = shape(text); res[key] = {'d': d, 'w': w}
res['upem'] = upem; res['asc'] = f['hhea'].ascent; res['desc'] = f['hhea'].descent
json.dump(res, open(out,'w'))
print({k:(v['w'] if isinstance(v,dict) else v) for k,v in res.items()})
