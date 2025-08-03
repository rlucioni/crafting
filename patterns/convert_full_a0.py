#!/usr/bin/env python3
"""
Convert an A0 file with live only pages into a full A0 file.
"""
import math
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation

# constants
MM2PT = 72 / 25.4

A4_expected_w = 210 * MM2PT
A4_expected_h = 297 * MM2PT

A0_W_PT = A4_expected_w * 4
A0_H_PT = A4_expected_h * 4

MARGIN_MM = 10
MARGIN_PT = MARGIN_MM * MM2PT

print(A4_expected_w - 2 * MARGIN_PT)
print(A4_expected_h - 2 * MARGIN_PT)


def main(src: Path, dst: Path) -> None:
    reader = PdfReader(str(src))
    num_pages = len(reader.pages)

    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=A0_W_PT, height=A0_H_PT)

    for idx, page in enumerate(reader.pages):
        tile_w = float(page.mediabox.width)
        tile_h = float(page.mediabox.height)

        print(f"Tile size: {tile_w} x {tile_h}")

        if (A0_W_PT - tile_w) < (2 * MARGIN_PT) or (A0_H_PT - tile_h) < (2 * MARGIN_PT):
            sys.exit(f"Original pages have dimensions {tile_w}pt x {tile_h}pt, which is too big to pad")
        
        new_w_margin = (A0_W_PT - tile_w) / 2
        new_h_margin = (A0_H_PT - tile_h) / 2
        
        target_page = writer.pages[idx]

        # Place the cropped tile
        target_page.merge_transformed_page(
            page,
            Transformation().translate(tx=new_w_margin, ty=new_h_margin)
        )

    with open(dst, "wb") as fh:
        writer.write(fh)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
