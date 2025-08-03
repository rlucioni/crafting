#!/usr/bin/env python3
"""
Convert an A4-tiled sewing pattern into A0 sheets.
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


def main(src: Path, dst: Path, a4_rows: int, a4_cols: int, crop_t_mm: float, crop_b_mm: float, crop_l_mm: float, crop_r_mm: float) -> None:
    reader = PdfReader(str(src))
    if len(reader.pages) != a4_rows * a4_cols:
        sys.exit(f"Expected {a4_rows} x {a4_cols} = {a4_rows * a4_cols} pages.")

    a0_rows = math.ceil(a4_rows / 4)
    a0_cols = math.ceil(a4_cols / 4)

    # Crop amount in mm and points
    crop_t_pt = crop_t_mm * MM2PT
    crop_b_pt = crop_b_mm * MM2PT
    crop_l_pt = crop_l_mm * MM2PT
    crop_r_pt = crop_r_mm * MM2PT

    writer = PdfWriter()
    for _ in range(a0_rows * a0_cols):
        writer.add_blank_page(width=A0_W_PT, height=A0_H_PT)

    for idx, page in enumerate(reader.pages):
        # check size
        tile_w = float(page.mediabox.width)
        tile_h = float(page.mediabox.height)

        print(f"Tile size: {tile_w} x {tile_h}")

        if abs(tile_w - A4_expected_w) < 0.3 and abs(tile_h - A4_expected_h) < 0.3:
            print("Original included margins")
        elif (A4_expected_w - tile_w) > 0.3 or (A4_expected_h - tile_h) > 0.3:
            print("Warning: Original excluded margins")
        else:
            sys.exit(f"Expected tile dimensions to be {A4_expected_w}mm x {A4_expected_h}mm, got {tile_w}mm x {tile_h}mm")
        
        # Cropped tile dimensions
        cropped_tile_w = tile_w - crop_l_pt - crop_r_pt
        cropped_tile_h = tile_h - crop_t_pt - crop_b_pt

        new_w_margin = (A0_W_PT - (4 * cropped_tile_w)) / 2
        new_h_margin = (A0_H_PT - (4 * cropped_tile_h)) / 2

        if new_w_margin < MARGIN_PT or new_h_margin < MARGIN_PT:
            sys.exit(f"New margins are too small: {new_w_margin}pt x {new_h_margin}pt")

        a4_row, a4_col = divmod(idx, a4_cols)
        a0_row, a0_col = a4_row // 4, a4_col // 4
        within_page_row = a4_row % 4
        within_page_col = a4_col % 4

        target_page = writer.pages[a0_row * a0_cols + a0_col]

        if within_page_col == 0:
            lx = new_w_margin
            crop_left = False
        else:
            lx = new_w_margin + cropped_tile_w * within_page_col
            crop_left = True

        if (within_page_row == 3):
            ly = new_h_margin
            crop_bottom = False
        else:
            ly = new_h_margin + cropped_tile_h * (3 - within_page_row)
            crop_bottom = True

        if a4_row == (a4_rows - 1):  # account for if this is the last row
            crop_bottom = False

        if (within_page_col == 3) or (a4_col == (a4_cols - 1)):  # account for if this is the last column
            crop_right = False
        else:
            crop_right = True

        if within_page_row == 0:
            crop_top = False
        else:
            crop_top = True

        cropped_page = page
        
        # Apply cropping based on position
        if crop_top:
            cropped_page.mediabox.upper_right = (
                cropped_page.mediabox.upper_right[0],
                cropped_page.mediabox.upper_right[1] - crop_t_pt
            )
        if crop_bottom:
            cropped_page.mediabox.lower_left = (
                cropped_page.mediabox.lower_left[0],
                cropped_page.mediabox.lower_left[1] + crop_b_pt
            )
        if crop_left:
            cropped_page.mediabox.lower_left = (
                cropped_page.mediabox.lower_left[0] + crop_l_pt,
                cropped_page.mediabox.lower_left[1]
            )
        if crop_right:
            cropped_page.mediabox.upper_right = (
                cropped_page.mediabox.upper_right[0] - crop_r_pt,
                cropped_page.mediabox.upper_right[1]
            )
        
        # Place the cropped tile
        target_page.merge_transformed_page(
            cropped_page,
            Transformation().translate(tx=lx, ty=ly)
        )

    with open(dst, "wb") as fh:
        writer.write(fh)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]))
