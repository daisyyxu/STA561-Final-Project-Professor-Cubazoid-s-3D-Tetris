#!/usr/bin/env python3
"""
Generate a visual preview + construction animation for every test case.

Usage:
    python make_case_gifs.py

Outputs:
    case_visuals/
        previews/   -- PNG of the input pieces for every case
        gifs/       -- GIF of the construction for every solved case
        index.md    -- human-readable listing
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from test_suite import build_test_cases
from solver import solve_final
from visualize import visualize, COLORS, cube_faces


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "case_visuals")
PREVIEWS_DIR = os.path.join(OUT_DIR, "previews")
GIFS_DIR = os.path.join(OUT_DIR, "gifs")

os.makedirs(PREVIEWS_DIR, exist_ok=True)
os.makedirs(GIFS_DIR, exist_ok=True)


def save_input_preview(pieces, path, title):
    """Render each input piece as a small 3D subplot."""
    if not pieces:
        fig = plt.figure(figsize=(4, 2), facecolor="white")
        plt.text(0.5, 0.5, "(empty piece list)", ha="center", va="center",
                 transform=fig.transFigure, fontsize=12)
        plt.axis("off")
        plt.savefig(path, dpi=80, bbox_inches="tight")
        plt.close()
        return

    n = len(pieces)
    cols = min(n, 6)
    rows = (n + cols - 1) // cols
    fig = plt.figure(figsize=(2.0 * cols, 2.0 * rows + 0.4), facecolor="white")

    for i, p in enumerate(pieces):
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        color = COLORS[i % len(COLORS)]
        try:
            if p.ndim == 3 and set(np.unique(p).tolist()).issubset({0, 1}):
                for (x, y, z) in np.argwhere(p == 1):
                    for face in cube_faces(int(x), int(y), int(z)):
                        ax.add_collection3d(Poly3DCollection(
                            [face], facecolor=color, edgecolor="black",
                            alpha=0.9, linewidth=0.5))
                mx = max(p.shape) or 1
                ax.set_xlim(0, mx); ax.set_ylim(0, mx); ax.set_zlim(0, mx)
                ax.set_title(f"piece {i} ({int(p.sum())})", fontsize=8)
            else:
                ax.text2D(0.5, 0.5, "(invalid)", ha="center", va="center",
                          transform=ax.transAxes)
                ax.set_title(f"piece {i}", fontsize=8)
        except Exception as exc:
            ax.set_title(f"piece {i}", fontsize=8)
            print(f"  [render warning] piece {i}: {exc}")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])

    fig.suptitle(title, fontsize=11, y=0.98)
    plt.tight_layout()
    plt.savefig(path, dpi=80, bbox_inches="tight")
    plt.close()


def main():
    cases = build_test_cases()
    index = []

    header = f'{"Case":<40} {"Status":<20} {"Preview":<8} {"GIF":<8}'
    print(header)
    print("-" * len(header))

    for case in cases:
        name = case["name"]
        pieces = case["pieces"]

        # --- preview ---
        try:
            preview_path = os.path.join(PREVIEWS_DIR, f"{name}.png")
            save_input_preview(pieces, preview_path, f"{name}  (input pieces)")
            preview_ok = "yes"
        except Exception as e:
            print(f"  [preview error] {name}: {e}")
            preview_path = None
            preview_ok = "no"

        # --- solve + animate ---
        try:
            result = solve_final(pieces, timeout_sec=15, verbose=False)
            status = result["status"]
        except Exception as e:
            print(f"  [solver error] {name}: {e}")
            status = "error"
            result = None

        gif_path = None
        if result and result.get("status") == "solved":
            gif_path = os.path.join(GIFS_DIR, f"{name}.gif")
            try:
                n_pieces = len(result["placements"])
                interval = 700 if n_pieces <= 5 else 500 if n_pieces <= 10 else 350
                visualize(result, interval_ms=interval, save_path=gif_path)
                plt.close("all")
                gif_ok = "yes"
            except Exception as e:
                print(f"  [gif error] {name}: {e}")
                gif_path = None
                gif_ok = "error"
        else:
            gif_ok = "n/a"

        print(f"{name:<40} {status:<20} {preview_ok:<8} {gif_ok:<8}")

        index.append({
            "name": name,
            "status": status,
            "preview": os.path.relpath(preview_path, OUT_DIR) if preview_path else "-",
            "gif": os.path.relpath(gif_path, OUT_DIR) if gif_path else "(no gif)",
            "notes": case.get("notes", ""),
        })

    # --- write a human-readable index ---
    index_path = os.path.join(OUT_DIR, "index.md")
    with open(index_path, "w") as f:
        f.write("# Test case visualisations\n\n")
        f.write("Every case in `test_suite.py`, with its input pieces and (if solved)\n")
        f.write("an animated construction.  Open the PNGs and GIFs in a file browser.\n\n")
        for item in index:
            f.write(f"## `{item['name']}`\n\n")
            f.write(f"- **Status**: `{item['status']}`\n")
            f.write(f"- **Notes**: {item['notes']}\n")
            f.write(f"- **Input preview**: `{item['preview']}`\n")
            if item["gif"] != "(no gif)":
                f.write(f"- **Construction animation**: `{item['gif']}`\n")
            f.write("\n")

    print(f"\nDone.  Outputs in ./{OUT_DIR}/   (index: {index_path})")


if __name__ == "__main__":
    main()
