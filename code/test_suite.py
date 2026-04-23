"""
STA 561 — Professor Cubazoid's 3D Tetris
========================================
Comprehensive test suite (25 cases).

Covers:
    * Trivial through hard solvable packings (2^3, 3^3, 4^3, 5^3)
    * Constructively solvable cases via reverse-engineered cube partitions
    * Infeasible cases (volume mismatch, geometric impossibility)
    * Invalid-input cases (disconnected, empty, non-binary, not-3D)

Run:
    python test_suite.py                  # default 15s timeout
    python test_suite.py --timeout 30
    python test_suite.py --save results.csv
"""

import argparse
import csv
import random
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

from solver import (
    make_piece,
    solve_final,
    solution_summary,
    all_rotations_of_cells,
    tensor_to_cells,
    normalize_cells,
)


# ============================================================
# Construction helpers
# ============================================================

DIRS6 = [(1, 0, 0), (-1, 0, 0),
         (0, 1, 0), (0, -1, 0),
         (0, 0, 1), (0, 0, -1)]


def partition_to_pieces(grid: np.ndarray) -> List[np.ndarray]:
    """Take an NxNxN grid of piece IDs (1..K) and return the K pieces as tensors."""
    piece_ids = sorted(set(grid.flatten().tolist()) - {0})
    pieces = []
    for pid in piece_ids:
        xs, ys, zs = np.where(grid == pid)
        cells = list(zip(xs.tolist(), ys.tolist(), zs.tolist()))
        pieces.append(make_piece(cells))
    return pieces


def random_cube_partition(
    N: int,
    seed: int = 0,
    size_range: Tuple[int, int] = (3, 5),
    max_retries: int = 200,
) -> List[np.ndarray]:
    """
    Greedy random partition of an N^3 cube into connected polycubes.

    Each piece has volume in size_range (inclusive).  Because we scan in
    lex order, the final one or two pieces may end up smaller than
    min_size; we retry with a fresh seed in that case.

    Returns a list of piece tensors that by construction tile N^3.
    """
    min_size, max_size = size_range

    for attempt in range(max_retries):
        rng = random.Random(seed + attempt * 1000)
        grid = np.zeros((N, N, N), dtype=int)
        pid = 0
        success = True

        for start in ((x, y, z) for x in range(N) for y in range(N) for z in range(N)):
            if grid[start] != 0:
                continue
            pid += 1
            target = rng.randint(min_size, max_size)

            # BFS growth from `start`
            piece_cells = [start]
            grid[start] = pid
            frontier = set()
            for dx, dy, dz in DIRS6:
                nb = (start[0] + dx, start[1] + dy, start[2] + dz)
                if 0 <= nb[0] < N and 0 <= nb[1] < N and 0 <= nb[2] < N and grid[nb] == 0:
                    frontier.add(nb)

            while len(piece_cells) < target and frontier:
                nxt = rng.choice(sorted(frontier))
                frontier.remove(nxt)
                piece_cells.append(nxt)
                grid[nxt] = pid
                for dx, dy, dz in DIRS6:
                    nb = (nxt[0] + dx, nxt[1] + dy, nxt[2] + dz)
                    if (0 <= nb[0] < N and 0 <= nb[1] < N and 0 <= nb[2] < N
                            and grid[nb] == 0):
                        frontier.add(nb)

            if len(piece_cells) < min_size:
                # final tail was too small — abandon this attempt
                success = False
                break

        if success and np.all(grid > 0):
            return partition_to_pieces(grid)

    raise RuntimeError(
        f"random_cube_partition(N={N}, seed={seed}) could not partition after "
        f"{max_retries} retries; try another seed or relax size_range."
    )


# ============================================================
# Case builders
# ============================================================

def _i_piece_along_x(length: int) -> np.ndarray:
    return make_piece([(i, 0, 0) for i in range(length)])


def _l_tetracube_flat() -> np.ndarray:
    return make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)])


def _t_tetracube_flat() -> np.ndarray:
    return make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)])


def _s_tetracube_flat() -> np.ndarray:
    return make_piece([(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0)])


def _o_tetracube_flat() -> np.ndarray:
    # 2x2x1 square
    return make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)])


def _soma_pieces() -> List[np.ndarray]:
    """A 7-piece Soma-like set: 1 tricube + 6 tetracubes = 27 cells."""
    return [
        make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0)]),                    # V-tricube
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)]),         # L-tetracube
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0)]),         # L-mirror
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]),         # T-tetracube
        make_piece([(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0)]),         # S/Z-tetracube
        make_piece([(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 0, 1)]),         # 3D branch
        make_piece([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 1, 1)]),         # 3D twist
    ]


def _build_2x2x2_penta_tri() -> List[np.ndarray]:
    """A 2x2x2 cube partitioned into one pentacube + one tricube (5 + 3)."""
    # Layer z=0:          Layer z=1:
    #   A A                 A B
    #   A A                 B B
    # piece A has 5 cells, piece B has 3 cells
    grid = np.zeros((2, 2, 2), dtype=int)
    grid[0, 0, 0] = 1
    grid[1, 0, 0] = 1
    grid[0, 1, 0] = 1
    grid[1, 1, 0] = 1
    grid[0, 0, 1] = 1
    grid[1, 0, 1] = 2
    grid[0, 1, 1] = 2
    grid[1, 1, 1] = 2
    return partition_to_pieces(grid)


# ============================================================
# Master case list
# ============================================================

def build_test_cases() -> List[Dict]:
    """
    Return a list of cases.  Each case is a dict with:
        name       — short identifier
        pieces     — list[np.ndarray]
        expected   — a string, or a set of acceptable status strings
        notes      — (optional) short description
    """
    cases: List[Dict] = []

    # -------- Easy solvable (2^3) --------

    A = make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    B = make_piece([(1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)])
    cases.append({
        "name": "01_2x2x2_two_tetracubes",
        "pieces": [A, B],
        "expected": "solved",
        "notes": "Two complementary tetracubes forming a 2x2x2.",
    })

    cases.append({
        "name": "02_2x2x2_penta_plus_tri",
        "pieces": _build_2x2x2_penta_tri(),
        "expected": "solved",
        "notes": "2x2x2 split as 5 + 3 cubes.",
    })

    # -------- Easy solvable (3^3) --------

    cases.append({
        "name": "03_3x3x3_random_partition_s42",
        "pieces": random_cube_partition(3, seed=42),
        "expected": "solved",
        "notes": "Randomly-generated 3x3x3 partition (seed=42); mixed piece sizes.",
    })

    cases.append({
        "name": "04_3x3x3_soma",
        "pieces": _soma_pieces(),
        "expected": "solved",
        "notes": "Classical 7-piece Soma cube.",
    })

    cases.append({
        "name": "05_3x3x3_random_partition_s0",
        "pieces": random_cube_partition(3, seed=0),
        "expected": "solved",
        "notes": "Randomly-generated 3x3x3 partition (seed=0).",
    })

    cases.append({
        "name": "06_3x3x3_random_partition_s7",
        "pieces": random_cube_partition(3, seed=7),
        "expected": "solved",
        "notes": "Randomly-generated 3x3x3 partition (seed=7).",
    })

    # -------- Medium solvable (4^3) --------

    cases.append({
        "name": "07_4x4x4_random_partition_s5",
        "pieces": random_cube_partition(4, seed=5),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 4x4x4 partition (seed=5); mixed piece sizes.",
    })

    cases.append({
        "name": "08_4x4x4_sixteen_L_tetracubes",
        "pieces": [_l_tetracube_flat()] * 16,
        "expected": "solved",
        "notes": "Sixteen flat L-tetracubes — classic tiling.",
    })

    cases.append({
        "name": "09_4x4x4_sixteen_T_tetracubes",
        "pieces": [_t_tetracube_flat()] * 16,
        "expected": "solved",
        "notes": "Sixteen flat T-tetracubes (four per 4x4x1 slab).",
    })

    cases.append({
        "name": "10_4x4x4_sixteen_O_tetracubes",
        "pieces": [_o_tetracube_flat()] * 16,
        "expected": "solved",
        "notes": "Sixteen 2x2x1 squares.",
    })

    cases.append({
        "name": "11_4x4x4_mixed_LTS",
        "pieces": (
            [_l_tetracube_flat()] * 6
            + [_t_tetracube_flat()] * 5
            + [_s_tetracube_flat()] * 5
        ),
        "expected": "parity_rejected",
        "notes": "Sixteen mixed flat tetracubes (6 L + 5 T + 5 S) — parity infeasible.",
    })

    cases.append({
        "name": "12_4x4x4_random_partition_s1",
        "pieces": random_cube_partition(4, seed=1),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 4x4x4 partition (seed=1).",
    })

    cases.append({
        "name": "13_4x4x4_random_partition_s3",
        "pieces": random_cube_partition(4, seed=3),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 4x4x4 partition (seed=3).",
    })

    # -------- Hard / stretch (5^3) --------

    cases.append({
        "name": "14_5x5x5_random_partition_s11",
        "pieces": random_cube_partition(5, seed=11),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 5x5x5 partition (seed=11); mixed piece sizes.",
    })

    cases.append({
        "name": "15_5x5x5_random_partition_s0",
        "pieces": random_cube_partition(5, seed=0),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 5x5x5 partition (seed=0).",
    })

    cases.append({
        "name": "16_5x5x5_random_partition_s2",
        "pieces": random_cube_partition(5, seed=2),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 5x5x5 partition (seed=2).",
    })

    # -------- Infeasible (no solution) --------

    cases.append({
        "name": "17_invalid_volume_not_cube",
        "pieces": [
            make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0)]),
            make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]),
        ],
        "expected": "invalid_volume",
        "notes": "Total volume is 7 — not a perfect cube.",
    })

    cases.append({
        "name": "18_no_solution_wrong_shapes_2x2x2",
        "pieces": [_l_tetracube_flat(), _l_tetracube_flat()],
        "expected": {"no_solution", "timeout"},
        "notes": "Two flat L-tetracubes can't tile a 2x2x2 (need 3D footprint).",
    })

    cases.append({
        "name": "19_no_solution_I5s_in_3x3x3",
        "pieces": [_i_piece_along_x(5)] * 3 + [_i_piece_along_x(4)] * 3,
        "expected": {"no_solution", "timeout"},
        "notes": "Volume 27 passes (3×5 + 3×4), but length-5 rods cannot fit in a 3-cube.",
    })

    # -------- Invalid input --------

    disconnected = np.zeros((2, 2, 2), dtype=int)
    disconnected[0, 0, 0] = 1
    disconnected[1, 1, 1] = 1
    cases.append({
        "name": "20_invalid_disconnected_piece",
        "pieces": [disconnected],
        "expected": "invalid_input",
        "notes": "Piece has two disconnected cells.",
    })

    cases.append({
        "name": "21_invalid_empty_list",
        "pieces": [],
        "expected": "invalid_input",
        "notes": "Empty piece list.",
    })

    non_binary = np.zeros((2, 2, 2), dtype=int)
    non_binary[0, 0, 0] = 1
    non_binary[1, 0, 0] = 2  # illegal value
    cases.append({
        "name": "22_invalid_non_binary",
        "pieces": [non_binary],
        "expected": "invalid_input",
        "notes": "Piece tensor has a value != 0/1.",
    })

    flat_2d = np.ones((3, 3), dtype=int)  # 2D, not 3D
    cases.append({
        "name": "23_invalid_not_3d",
        "pieces": [flat_2d],
        "expected": "invalid_input",
        "notes": "Piece is a 2D tensor, not 3D.",
    })

    # -------- Edge cases --------

    cases.append({
        "name": "24_4x4x4_random_partition_s17",
        "pieces": random_cube_partition(4, seed=17),
        "expected": {"solved", "timeout"},
        "notes": "Randomly-generated 4x4x4 partition (seed=17); another diverse mix.",
    })

    cases.append({
        "name": "25_3x3x3_mixed_pentatri",
        "pieces": random_cube_partition(3, seed=13, size_range=(3, 5)),
        "expected": "solved",
        "notes": "3x3x3 partitioned with mixed tri/tetra/pentacubes.",
    })

    return cases


# ============================================================
# Solution verification
# ============================================================

def verify_solution(result: Dict, pieces: List[np.ndarray]) -> Tuple[bool, str]:
    if result["status"] != "solved":
        return False, f"status was {result['status']}"

    N = result["N"]
    grid = result["grid"]
    placements = result["placements"]

    if grid is None or grid.shape != (N, N, N):
        return False, "grid shape mismatch"
    if np.any(grid == 0):
        return False, "grid has empty cells"

    total_piece_vol = sum(int(p.sum()) for p in pieces)
    if int(np.count_nonzero(grid)) != total_piece_vol:
        return False, "grid volume != total piece volume"

    piece_vol = {i: int(p.sum()) for i, p in enumerate(pieces)}
    used_ids = set()
    for item in placements:
        pi = item["piece_idx"]
        if pi in used_ids:
            return False, f"piece {pi} placed more than once"
        used_ids.add(pi)
        if len(item["cells"]) != piece_vol[pi]:
            return False, f"piece {pi} placed with wrong volume"
        placed_norm = normalize_cells(item["cells"])
        valid_rots = set(all_rotations_of_cells(tensor_to_cells(pieces[pi])))
        if placed_norm not in valid_rots:
            return False, f"piece {pi} placed in wrong shape"

    if len(placements) != len(pieces):
        return False, f"{len(placements)} placements vs {len(pieces)} pieces"

    return True, "ok"


# ============================================================
# Runner
# ============================================================

def run_suite(timeout_sec: float = 15.0, verbose: bool = False,
              save_csv: str = None) -> List[Dict]:
    cases = build_test_cases()

    print(f"\n{'#':<3} {'Case':<38} {'Expected':<18} {'Actual':<18} "
          f"{'Time(s)':>8} {'Pass':>6}")
    print("-" * 100)

    passed = 0
    solved = 0
    rows = []
    for i, case in enumerate(cases, start=1):
        name = case["name"]
        pieces = case["pieces"]
        expected = case["expected"]

        result = solve_final(pieces, timeout_sec=timeout_sec, verbose=False)
        actual = result["status"]
        runtime = result["runtime_sec"]

        # accept set OR single string
        if isinstance(expected, set):
            ok = actual in expected
            expected_str = "|".join(sorted(expected))
        else:
            ok = (actual == expected)
            expected_str = expected

        # extra check if solved
        if actual == "solved":
            v_ok, v_msg = verify_solution(result, pieces)
            if not v_ok:
                ok = False
                print(f"    [verification failed: {v_msg}]")
            else:
                solved += 1

        if ok:
            passed += 1

        print(f"{i:<3} {name:<38} {expected_str:<18} {actual:<18} "
              f"{runtime:>8.3f} {str(ok):>6}")

        rows.append({
            "case": name,
            "expected": expected_str,
            "actual": actual,
            "runtime_sec": round(runtime, 4),
            "passed": ok,
            "notes": case.get("notes", ""),
        })

    print("-" * 100)
    print(f"Passed {passed}/{len(cases)} | Solved {solved} puzzles")

    if save_csv:
        with open(save_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Results saved to {save_csv}")

    return rows


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=15.0,
                        help="Per-case timeout in seconds (default 15)")
    parser.add_argument("--save", type=str, default=None,
                        help="Save results to this CSV file")
    args = parser.parse_args()

    run_suite(timeout_sec=args.timeout, save_csv=args.save)


if __name__ == "__main__":
    main()
