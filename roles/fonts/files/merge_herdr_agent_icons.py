# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools"]
# ///
"""Copy the Herdr agent icon glyphs into a base font and rename its family.

Alacritty on macOS only falls back to the system Core Text font list, so it
never finds the separately installed Herdr agent icon font. A merged font
carries the icons itself.

Usage: merge_herdr_agent_icons.py BASE_FONT ICON_FONT OUTPUT FAMILY

Prints "changed" when it writes OUTPUT and "unchanged" when OUTPUT is newer
than both inputs.
"""

import os
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ICON_FIRST = 0xE1A0
ICON_LAST = 0xE1BA

# Tables that hold per-glyph data for a fixed glyph count. Adding glyphs makes
# them invalid, and renderers do not need them.
STALE_TABLES = ("hdmx", "LTSH", "VDMX")


def is_up_to_date(output, inputs):
    if not os.path.exists(output):
        return False
    output_mtime = os.path.getmtime(output)
    return all(os.path.getmtime(path) < output_mtime for path in inputs)


def copy_icons(base, icons):
    scale = base["head"].unitsPerEm / icons["head"].unitsPerEm
    icon_glyphs = icons.getGlyphSet()
    glyph_order = list(base.getGlyphOrder())
    unicode_cmaps = [table for table in base["cmap"].tables if table.isUnicode()]

    for codepoint, icon_name in sorted(icons.getBestCmap().items()):
        if not ICON_FIRST <= codepoint <= ICON_LAST:
            continue

        recording = DecomposingRecordingPen(icon_glyphs)
        icon_glyphs[icon_name].draw(recording)
        pen = TTGlyphPen(None)
        recording.replay(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))

        name = f"herdr.uni{codepoint:04X}"
        advance, left_side_bearing = icons["hmtx"][icon_name]
        base["glyf"][name] = pen.glyph()
        base["hmtx"][name] = (round(advance * scale), round(left_side_bearing * scale))
        glyph_order.append(name)
        for table in unicode_cmaps:
            table.cmap[codepoint] = name

    base.setGlyphOrder(glyph_order)
    for tag in STALE_TABLES:
        if tag in base:
            del base[tag]


def rename_family(font, family):
    names = font["name"]
    style = names.getDebugName(2) or "Regular"
    postscript_family = family.replace(" ", "")
    version = names.getDebugName(5) or ""

    # Typographic family and subfamily names override nameID 1 and 2 in some
    # renderers, so remove them to keep the new family name in effect.
    names.removeNames(nameID=16)
    names.removeNames(nameID=17)

    values = {
        1: family,
        3: f"{family} {style} {version}".strip(),
        4: f"{family} {style}",
        6: f"{postscript_family}-{style}",
    }
    for name_id, value in values.items():
        names.setName(value, name_id, 3, 1, 0x409)
        if names.getName(name_id, 1, 0, 0):
            names.setName(value, name_id, 1, 0, 0)


def main(argv):
    if len(argv) != 5:
        sys.exit(__doc__)
    base_path, icon_path, output, family = argv[1:]

    if is_up_to_date(output, (base_path, icon_path, __file__)):
        print("unchanged")
        return

    base = TTFont(base_path)
    copy_icons(base, TTFont(icon_path))
    rename_family(base, family)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    base.save(output)
    print("changed")


if __name__ == "__main__":
    main(sys.argv)
