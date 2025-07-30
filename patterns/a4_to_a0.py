#!/usr/bin/env python3
"""
Convert a 42-page (7 × 6) A4-tiled sewing pattern into 4 portrait-A0 sheets,
preserving the intended 10 mm overlaps marked by green diamonds.

Compatible with pypdf >= 3.10 (the successor to PyPDF2).
"""

import sys
from pathlib import Path

# ----  use pypdf (pip install pypdf)  ----------------------------------------
from pypdf import PdfReader, PdfWriter, Transformation

# ISO-216 sizes in PostScript points
MM2PT = 72 / 25.4
A0_W_PT = 841 * MM2PT           # ≈ 2384 pt
A0_H_PT = 1189 * MM2PT          # ≈ 3370 pt

ROWS, COLS        = 6, 7        # full tiling grid
ROWS_PER_BLOCK    = 3           # 3 rows per A0
COLS_PER_BLOCK    = (4, 3)      # 4 cols on the left, 3 on the right


def main(src: Path, dst: Path) -> None:
    reader = PdfReader(str(src))
    if len(reader.pages) != 42:
        sys.exit("❌  Expected exactly 42 pages laid out 7 × 6.")

    # true trimmed-tile size (page 0 is representative)
    tile_w = float(reader.pages[0].mediabox.width)
    tile_h = float(reader.pages[0].mediabox.height)

    # Crop amount in mm and points
    crop_mm = 3.2
    crop_pt = crop_mm * MM2PT
    
    # Padding around each A0 tile in mm and points
    padding_mm = 5
    padding_pt = padding_mm * MM2PT
    
    # Cropped tile dimensions
    cropped_tile_w = tile_w - 2 * crop_pt  # 3mm from left and right
    cropped_tile_h = tile_h - 2 * crop_pt  # 3mm from top and bottom

    # margins so adjoining sheets butt exactly at the overlap marks
    # Account for variable cropping: interior tiles are cropped, peripheral tiles are not
    effective_width = COLS_PER_BLOCK[0] * tile_w - (COLS_PER_BLOCK[0] - 1) * crop_pt  # Left block: 4 tiles, 3 interior gaps
    effective_height = ROWS_PER_BLOCK * tile_h - (ROWS_PER_BLOCK - 1) * crop_pt  # 3 tiles, 2 interior gaps
    
    # Add padding around each A0 tile
    LEFT_BLOCK_MARGIN_X   = padding_pt + (A0_W_PT - effective_width - 2 * padding_pt) / 2
    RIGHT_BLOCK_MARGIN_X  = padding_pt
    TOP_BLOCK_MARGIN_Y    = padding_pt + (A0_H_PT - effective_height - 2 * padding_pt) / 2
    BOTTOM_BLOCK_MARGIN_Y = padding_pt

    writer = PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=A0_W_PT, height=A0_H_PT)

    for idx, page in enumerate(reader.pages):
        row, col = divmod(idx, COLS)          # 0-based
        col_block = 0 if col < 4 else 1       # 0 = left-hand A0, 1 = right-hand
        row_block = 0 if row < 3 else 1       # 0 = top A0, 1 = bottom A0
        a0_idx    = row_block * 2 + col_block
        target    = writer.pages[a0_idx]

        # ----- global coordinates in the 7×6 canvas --------------------------
        # Calculate position based on original tile dimensions, accounting for cropping
        gx = col * tile_w
        gy = (ROWS - 1 - row) * tile_h        # origin bottom-left
        
        # Adjust for cropping on left and bottom edges
        if col > 0:  # Not leftmost column
            gx -= 2 * col * crop_pt  # Account for left cropping of all tiles to the left
        if row < ROWS - 1:  # Not bottommost row
            gy -= 2 *(ROWS - 1 - row) * crop_pt  # Account for bottom cropping of all tiles below

        # ----- convert to local coords inside this A0 block ------------------
        block_x0 = 0 if col_block == 0 else 4 * tile_w - 8 * crop_pt  # Account for cropping in left block
        block_y0 = 3 * tile_h - 6 * crop_pt if row_block == 0 else 0  # Account for cropping in top block
        lx = gx - block_x0
        ly = gy - block_y0

        # ----- add margins so patterns meet at sheet edges -------------------
        lx += LEFT_BLOCK_MARGIN_X  if col_block == 0 else RIGHT_BLOCK_MARGIN_X
        ly += TOP_BLOCK_MARGIN_Y   if row_block == 0 else BOTTOM_BLOCK_MARGIN_Y

        # Crop 3.2mm from all 4 sides of each tile, except for peripheral tiles
        # Create a cropped version of the page by adjusting the mediabox
        cropped_page = page
        
        # Determine which edges to crop based on position
        crop_left = col > 0  # Don't crop left edge of leftmost tiles
        crop_right = col < COLS - 1  # Don't crop right edge of rightmost tiles
        crop_top = row > 0  # Don't crop top edge of topmost tiles
        crop_bottom = row < ROWS - 1  # Don't crop bottom edge of bottommost tiles
        
        # Apply cropping based on position
        if crop_left:
            cropped_page.mediabox.lower_left = (
                cropped_page.mediabox.lower_left[0] + crop_pt,
                cropped_page.mediabox.lower_left[1]
            )
        if crop_right:
            cropped_page.mediabox.upper_right = (
                cropped_page.mediabox.upper_right[0] - crop_pt,
                cropped_page.mediabox.upper_right[1]
            )
        if crop_bottom:
            cropped_page.mediabox.lower_left = (
                cropped_page.mediabox.lower_left[0],
                cropped_page.mediabox.lower_left[1] + crop_pt
            )
        if crop_top:
            cropped_page.mediabox.upper_right = (
                cropped_page.mediabox.upper_right[0],
                cropped_page.mediabox.upper_right[1] - crop_pt
            )
        
        # Place the cropped tile
        target.merge_transformed_page(
            cropped_page,
            Transformation().translate(tx=lx, ty=ly)
        )

    with open(dst, "wb") as fh:
        writer.write(fh)
    print(f"✅  Wrote “{dst}” – four portrait-A0 pages, ready for 100 % printing.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python a4_to_a0.py input.pdf output_a0.pdf")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
