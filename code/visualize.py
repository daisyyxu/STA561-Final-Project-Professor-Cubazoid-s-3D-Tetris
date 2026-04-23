"""
STA 561 — 3D Tetris Visualizer
Animated piece-by-piece construction using matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import List, Dict


# ─────────────────────────────────────────────
# Color palette (one per piece, up to 12)
# ─────────────────────────────────────────────
COLORS = [
    '#e63946', '#457b9d', '#2a9d8f', '#e9c46a',
    '#f4a261', '#a8dadc', '#8338ec', '#06d6a0',
    '#fb5607', '#3a86ff', '#ffbe0b', '#ff006e',
]


def cube_faces(x, y, z):
    """Return the 6 faces of a unit cube at position (x,y,z) as lists of vertices."""
    v = [
        (x,   y,   z),   (x+1, y,   z),
        (x+1, y+1, z),   (x,   y+1, z),
        (x,   y,   z+1), (x+1, y,   z+1),
        (x+1, y+1, z+1), (x,   y+1, z+1),
    ]
    faces = [
        [v[0], v[1], v[2], v[3]],  # bottom
        [v[4], v[5], v[6], v[7]],  # top
        [v[0], v[1], v[5], v[4]],  # front
        [v[2], v[3], v[7], v[6]],  # back
        [v[0], v[3], v[7], v[4]],  # left
        [v[1], v[2], v[6], v[5]],  # right
    ]
    return faces


def visualize(result: Dict, interval_ms: int = 600, save_path: str = None):
    """
    Animate the solution piece-by-piece.

    Args:
        result: output from solver.solve()
        interval_ms: milliseconds between frames
        save_path: if set, save animation to this .gif or .mp4 path
    """
    N = result['N']
    placements = result['placements']
    num_pieces = len(placements)

    fig = plt.figure(figsize=(7, 7), facecolor='#1a1a2e')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')

    def style_ax():
        ax.set_xlim(0, N)
        ax.set_ylim(0, N)
        ax.set_zlim(0, N)
        ax.set_xlabel('X', color='white')
        ax.set_ylabel('Y', color='white')
        ax.set_zlabel('Z', color='white')
        ax.tick_params(colors='white')
        for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor('#333355')
        ax.grid(True, color='#333355', linewidth=0.5)

    def draw_frame(frame_idx):
        ax.cla()
        style_ax()

        pieces_to_show = min(frame_idx, num_pieces)
        title_text = (
            "Empty" if frame_idx == 0
            else f"Piece {frame_idx}/{num_pieces}" if frame_idx <= num_pieces
            else f"Complete! ({num_pieces} pieces)"
        )
        ax.set_title(title_text, color='white', fontsize=13, pad=10)

        for i in range(pieces_to_show):
            color = COLORS[placements[i]['piece_idx'] % len(COLORS)]
            for cell in placements[i]['cells']:
                faces = cube_faces(*cell)
                poly = Poly3DCollection(
                    faces, alpha=0.85,
                    facecolor=color,
                    edgecolor='#1a1a2e',
                    linewidth=0.5
                )
                ax.add_collection3d(poly)

    num_frames = num_pieces + 2  # empty + each piece + hold final
    ani = animation.FuncAnimation(
        fig, draw_frame,
        frames=num_frames,
        interval=interval_ms,
        repeat=True
    )

    if save_path:
        # round, not floor: at interval_ms=700 we want ~1.4 fps → 1,
        # but at interval_ms=1200 floor would give 0 (invalid) instead of 1.
        fps = max(1, round(1000 / interval_ms))
        if save_path.endswith('.gif'):
            ani.save(save_path, writer='pillow', fps=fps)
        else:
            ani.save(save_path, fps=fps)
        print(f"[✓] Animation saved to {save_path}")
    else:
        plt.tight_layout()
        plt.show()

    return ani


# ─────────────────────────────────────────────
# Static snapshot (for reports / jupyter)
# ─────────────────────────────────────────────

def visualize_static(result: Dict, save_path: str = None):
    """Show the final solved cube as a static 3D plot."""
    N = result['N']
    placements = result['placements']

    fig = plt.figure(figsize=(7, 7), facecolor='#1a1a2e')
    fig.patch.set_facecolor('#1a1a2e')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1a1a2e')

    for placement in placements:
        color = COLORS[placement['piece_idx'] % len(COLORS)]
        for cell in placement['cells']:
            faces = cube_faces(*cell)
            poly = Poly3DCollection(
                faces, alpha=0.85,
                facecolor=color,
                edgecolor='#1a1a2e',
                linewidth=0.5
            )
            ax.add_collection3d(poly)

    ax.set_xlim(0, N)
    ax.set_ylim(0, N)
    ax.set_zlim(0, N)
    ax.set_title(f"Solved {N}×{N}×{N} Cube", color='white', fontsize=14)
    ax.set_xlabel('X', color='white')
    ax.set_ylabel('Y', color='white')
    ax.set_zlabel('Z', color='white')
    ax.tick_params(colors='white')
    for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        pane.fill = False

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight',
                    facecolor='#1a1a2e')
        print(f"[✓] Saved to {save_path}")
    else:
        plt.show()
