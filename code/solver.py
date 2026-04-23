"""
STA 561 — Professor Cubazoid's 3D Tetris
========================================

Backtracking solver that packs a set of polycubes (3-5 unit cubes each) into
a perfect N x N x N cube, or proves infeasibility.

Pipeline:
    1. Input validation (binary, 3D, connected)
    2. Volume check (total cells must be a perfect cube)
    3. Parity pruning (3D checkerboard feasibility)
    4. Most-constrained-first piece ordering
    5. Backtracking with:
         - lex-order first-empty-cell pointer
         - anchor-at-lex-min orientation canonicalisation
         - identical-piece symmetry breaking (canonical form)
         - connectivity + subset-sum pruning on free-region components

Improvements over the original draft:
    * first_empty_cell is now a running index instead of an O(N^3) rescan
    * each orientation is anchored only at its lex-minimum cell, removing a
      ~4x redundant inner loop
    * parity signatures include the offset-parity flip (fixes false rejects)
    * placements are returned in solver placement order (preserves a
      meaningful piece-by-piece animation); a piece-id-sorted view is also
      provided separately
"""

import time
from itertools import product
from typing import List, Tuple, Dict, Optional

import numpy as np


# ============================================================
# 1. 24 rotations in 3D
# ============================================================

def rotation_matrices() -> List[np.ndarray]:
    """Build the 24 proper rotations of the cube (no reflections)."""
    mats = set()

    def rx(m):
        return m @ np.array([[1, 0, 0],
                             [0, 0, -1],
                             [0, 1, 0]], dtype=int)

    def ry(m):
        return m @ np.array([[0, 0, 1],
                             [0, 1, 0],
                             [-1, 0, 0]], dtype=int)

    def rz(m):
        return m @ np.array([[0, -1, 0],
                             [1, 0, 0],
                             [0, 0, 1]], dtype=int)

    for a in range(4):
        for b in range(4):
            for c in range(4):
                m = np.eye(3, dtype=int)
                for _ in range(a):
                    m = rx(m)
                for _ in range(b):
                    m = ry(m)
                for _ in range(c):
                    m = rz(m)
                mats.add(tuple(m.flatten()))

    # sort for deterministic orientation order (reproducible solutions)
    return [np.array(x, dtype=int).reshape(3, 3) for x in sorted(mats)]


ROTATIONS = rotation_matrices()
assert len(ROTATIONS) == 24, "expected 24 proper rotations"


# ============================================================
# 2. Basic utilities
# ============================================================

def tensor_to_cells(tensor: np.ndarray) -> List[Tuple[int, int, int]]:
    return [tuple(idx) for idx in np.argwhere(tensor == 1)]


def normalize_cells(cells) -> Tuple[Tuple[int, int, int], ...]:
    """Translate so min-per-axis is 0, then sort cells in lex order."""
    arr = np.array(cells, dtype=int)
    arr = arr - arr.min(axis=0)
    return tuple(sorted(map(tuple, arr.tolist())))


def canonical_form(tensor: np.ndarray) -> Tuple[Tuple[int, int, int], ...]:
    """Minimum normalized cell-list over all 24 rotations.

    Two pieces share a canonical_form iff they are rotationally equivalent.
    """
    cells = tensor_to_cells(tensor)
    return min(
        normalize_cells([tuple((R @ np.array(c)).tolist()) for c in cells])
        for R in ROTATIONS
    )


def all_rotations_of_cells(cells) -> List[Tuple[Tuple[int, int, int], ...]]:
    """Return the unique normalized orientations of this piece."""
    seen = set()
    out = []
    for R in ROTATIONS:
        rotated = [tuple((R @ np.array(c)).tolist()) for c in cells]
        norm = normalize_cells(rotated)
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


def make_piece(coords: List[Tuple[int, int, int]]) -> np.ndarray:
    """Build a tight 3D binary tensor from a list of cell coordinates."""
    coords = np.array(coords, dtype=int)
    coords = coords - coords.min(axis=0)
    shape = tuple(coords.max(axis=0) + 1)
    tensor = np.zeros(shape, dtype=int)
    for c in coords:
        tensor[tuple(c)] = 1
    return tensor


# ============================================================
# 3. Input validation
# ============================================================

def _is_binary_tensor(t: np.ndarray) -> bool:
    vals = set(np.unique(t).tolist())
    return vals.issubset({0, 1})


def _is_connected_piece(tensor: np.ndarray) -> bool:
    cells = tensor_to_cells(tensor)
    if not cells:
        return False

    cells_set = set(cells)
    seen = {cells[0]}
    stack = [cells[0]]
    dirs = [(1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0),
            (0, 0, 1), (0, 0, -1)]

    while stack:
        x, y, z = stack.pop()
        for dx, dy, dz in dirs:
            nb = (x + dx, y + dy, z + dz)
            if nb in cells_set and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    return len(seen) == len(cells)


def validate_pieces(pieces: List[np.ndarray]) -> None:
    """Raise a descriptive error if the piece list is malformed."""
    if not isinstance(pieces, list) or len(pieces) == 0:
        raise ValueError("pieces must be a non-empty list of 3D numpy arrays")

    for i, p in enumerate(pieces):
        if not isinstance(p, np.ndarray):
            raise TypeError(f"piece {i} is not a numpy array")
        if p.ndim != 3:
            raise ValueError(f"piece {i} must be a 3D tensor")
        if not _is_binary_tensor(p):
            raise ValueError(f"piece {i} must be binary (0/1)")
        if int(p.sum()) <= 0:
            raise ValueError(f"piece {i} is empty")
        if not _is_connected_piece(p):
            raise ValueError(f"piece {i} is not 6-connected")
        volume = int(p.sum())
        if not (3 <= volume <= 5):
            raise ValueError(
                f"piece {i} has {volume} cells; each piece must have 3–5 cells"
            )


# ============================================================
# 4. Fast feasibility checks
# ============================================================

def _infer_cube_size(pieces: List[np.ndarray]) -> Optional[int]:
    total = int(sum(int(p.sum()) for p in pieces))
    if total <= 0:
        return None
    N = round(total ** (1 / 3))
    return N if N ** 3 == total else None


def _checkerboard_counts_for_cube(N: int) -> Tuple[int, int]:
    even = 0
    odd = 0
    for x, y, z in product(range(N), repeat=3):
        if (x + y + z) % 2 == 0:
            even += 1
        else:
            odd += 1
    return even, odd


def _piece_parity_signatures(piece: np.ndarray) -> List[Tuple[int, int]]:
    """
    (#even_cells, #odd_cells) signatures a piece can contribute.

    For every unique orientation we compute (e, o) under normalised
    coordinates AND also include (o, e) to account for the parity flip
    that an odd-sum translation induces.  This keeps the DP tight but
    avoids false rejections that the naive normalised-only version
    suffered from.
    """
    sigs = set()
    base_cells = tensor_to_cells(piece)
    for orient in all_rotations_of_cells(base_cells):
        even = sum((x + y + z) % 2 == 0 for x, y, z in orient)
        odd = len(orient) - even
        sigs.add((even, odd))
        sigs.add((odd, even))
    return sorted(sigs)


def parity_feasible(pieces: List[np.ndarray], N: int) -> bool:
    """
    3D checkerboard feasibility screen.

    Runs a small DP over piece signatures to check if we can match the
    cube's (even, odd) cell totals.  A fast and cheap pre-filter that
    catches many infeasible mixtures.
    """
    target_even, target_odd = _checkerboard_counts_for_cube(N)
    dp = {(0, 0)}

    for piece in pieces:
        sigs = _piece_parity_signatures(piece)
        nxt = set()
        for e0, o0 in dp:
            for e1, o1 in sigs:
                ne, no = e0 + e1, o0 + o1
                if ne <= target_even and no <= target_odd:
                    nxt.add((ne, no))
        dp = nxt
        if not dp:
            return False

    return (target_even, target_odd) in dp


# ============================================================
# 5. Placement counting / ordering
# ============================================================

def _count_valid_placements(piece: np.ndarray, N: int) -> int:
    """Number of (orientation, translation) placements that fit inside NxNxN."""
    count = 0
    base = tensor_to_cells(piece)
    for orient in all_rotations_of_cells(base):
        arr = np.array(orient, dtype=int)
        maxs = arr.max(axis=0)
        # once normalised, arr.min axis == 0
        for dx in range(N - maxs[0]):
            for dy in range(N - maxs[1]):
                for dz in range(N - maxs[2]):
                    count += 1
    return count


def order_pieces_most_constrained_first(
    pieces: List[np.ndarray], N: int
) -> Tuple[List[np.ndarray], List[int]]:
    """
    Place the pieces with the fewest orientations/positions first
    (the classic "most constrained variable" heuristic), with larger
    pieces as a tie-breaker.
    """
    stats = []
    for idx, piece in enumerate(pieces):
        placements = _count_valid_placements(piece, N)
        volume = int(piece.sum())
        stats.append((placements, -volume, idx, piece))
    stats.sort()

    ordered_pieces = [x[3] for x in stats]
    original_indices = [x[2] for x in stats]
    return ordered_pieces, original_indices


# ============================================================
# 6. Connectivity pruning
# ============================================================

DIRS6 = [(1, 0, 0), (-1, 0, 0),
         (0, 1, 0), (0, -1, 0),
         (0, 0, 1), (0, 0, -1)]


def _bfs_component_sizes(free_cells: set) -> List[int]:
    """Component sizes of the 6-connected free region."""
    seen = set()
    sizes = []

    for start in free_cells:
        if start in seen:
            continue
        q = [start]
        seen.add(start)
        size = 0
        head = 0

        while head < len(q):
            x, y, z = q[head]
            head += 1
            size += 1
            for dx, dy, dz in DIRS6:
                nb = (x + dx, y + dy, z + dz)
                if nb in free_cells and nb not in seen:
                    seen.add(nb)
                    q.append(nb)

        sizes.append(size)

    return sizes


def _subset_sum_possible(target: int, sizes: List[int]) -> bool:
    """Can some subset of `sizes` sum exactly to `target`?"""
    if target == 0:
        return True
    reachable = {0}
    for s in sizes:
        reachable |= {x + s for x in list(reachable) if x + s <= target}
    return target in reachable


def _free_regions_fillable(free_cells: set, remaining_piece_sizes: List[int]) -> bool:
    """Each free-region component must be exactly fillable by some subset."""
    if not free_cells:
        return True
    total_remaining = sum(remaining_piece_sizes)
    component_sizes = _bfs_component_sizes(free_cells)

    for comp in component_sizes:
        if comp > total_remaining:
            return False
        if not _subset_sum_possible(comp, remaining_piece_sizes):
            return False
    return True


# ============================================================
# 7. Main solver
# ============================================================

def solve_final(
    pieces: List[np.ndarray],
    timeout_sec: float = 15.0,
    verbose: bool = False,
) -> Dict:
    """
    Public API.

    Returns a dict with:
        status: one of
            "solved", "no_solution", "timeout",
            "invalid_volume", "parity_rejected", "invalid_input"
        N: cube side length (or None)
        runtime_sec
        grid: final N x N x N tensor (cell -> piece_idx+1), or None
        placements: list of dicts in *solver placement order* (rank order),
                    each with keys {piece_rank, piece_idx, cells}
        placements_by_piece_idx: same list sorted by piece_idx (convenience)
        ordered_original_indices: mapping rank -> original piece index
        message: human-readable error message, if any
    """
    t0 = time.time()

    # ---- validation -------------------------------------------------------
    try:
        validate_pieces(pieces)
    except Exception as e:
        return _fail("invalid_input", str(e), t0, None, pieces)

    N = _infer_cube_size(pieces)
    if N is None:
        return _fail(
            "invalid_volume",
            "Total volume is not a perfect cube.",
            t0, None, pieces,
        )

    if verbose:
        print(f"[*] pieces={len(pieces)} | target cube = {N}x{N}x{N}")

    # ---- parity pre-check -------------------------------------------------
    if not parity_feasible(pieces, N):
        return _fail(
            "parity_rejected",
            "Parity feasibility check failed.",
            t0, N, pieces,
        )

    # ---- piece ordering ---------------------------------------------------
    ordered_pieces, original_indices = order_pieces_most_constrained_first(pieces, N)

    if verbose:
        print("[*] Piece ordering (most constrained first):")
        for rank, (orig_idx, piece) in enumerate(zip(original_indices, ordered_pieces)):
            print(
                f"    rank={rank:2d} | original_idx={orig_idx:2d} | "
                f"size={int(piece.sum())} | "
                f"placements={_count_valid_placements(piece, N)}"
            )

    piece_orientations = []
    piece_canonical = []
    piece_sizes = []

    for p in ordered_pieces:
        base = tensor_to_cells(p)
        piece_orientations.append(all_rotations_of_cells(base))
        piece_canonical.append(canonical_form(p))
        piece_sizes.append(int(p.sum()))

    # ---- backtracking state ----------------------------------------------
    grid = np.zeros((N, N, N), dtype=int)
    free_cells = set(product(range(N), repeat=3))
    placed = [False] * len(ordered_pieces)
    placements_by_rank: List[Optional[List[Tuple[int, int, int]]]] = \
        [None] * len(ordered_pieces)

    # pre-build lex-order cell list so we can use a running "first empty" pointer
    all_cells_lex: Tuple[Tuple[int, int, int], ...] = tuple(
        (x, y, z) for x in range(N) for y in range(N) for z in range(N)
    )
    total_cells = len(all_cells_lex)

    deadline = t0 + timeout_sec
    found_solution = [False]
    timed_out = [False]

    # node counter for optional diagnostics
    stats = {"nodes": 0, "places": 0, "prunes_connectivity": 0}

    def backtrack(start_idx: int) -> bool:
        if time.time() > deadline:
            timed_out[0] = True
            return False
        stats["nodes"] += 1

        # advance past cells that are already filled
        while start_idx < total_cells and grid[all_cells_lex[start_idx]] != 0:
            start_idx += 1

        if start_idx == total_cells:
            found_solution[0] = True
            return True

        cx, cy, cz = all_cells_lex[start_idx]

        # symmetry breaking: don't try two rotationally-identical unplaced pieces
        tried_canon = set()

        for pi, orientations in enumerate(piece_orientations):
            if placed[pi]:
                continue

            cf = piece_canonical[pi]
            if cf in tried_canon:
                continue
            tried_canon.add(cf)

            for orient in orientations:
                # the current cell MUST be the lex-smallest cell of the piece
                # (everything smaller in lex order is already filled),
                # so we anchor orient[0] at (cx, cy, cz).
                ref = orient[0]
                dx = cx - ref[0]
                dy = cy - ref[1]
                dz = cz - ref[2]
                shifted = [(x + dx, y + dy, z + dz) for x, y, z in orient]

                ok = True
                for x, y, z in shifted:
                    if not (0 <= x < N and 0 <= y < N and 0 <= z < N):
                        ok = False
                        break
                    if grid[x, y, z] != 0:
                        ok = False
                        break
                if not ok:
                    continue

                # place
                for x, y, z in shifted:
                    grid[x, y, z] = pi + 1
                    free_cells.remove((x, y, z))

                placed[pi] = True
                placements_by_rank[pi] = shifted
                stats["places"] += 1

                remaining_sizes = [
                    piece_sizes[j] for j in range(len(piece_sizes)) if not placed[j]
                ]
                if _free_regions_fillable(free_cells, remaining_sizes):
                    if backtrack(start_idx + 1):
                        return True
                else:
                    stats["prunes_connectivity"] += 1

                # undo
                for x, y, z in shifted:
                    grid[x, y, z] = 0
                    free_cells.add((x, y, z))
                placed[pi] = False
                placements_by_rank[pi] = None

        return False

    solved = backtrack(0)
    runtime = time.time() - t0

    if not solved:
        status = "timeout" if timed_out[0] else "no_solution"
        return {
            "status": status,
            "message": None,
            "runtime_sec": runtime,
            "N": N,
            "grid": None,
            "placements": None,
            "placements_by_piece_idx": None,
            "ordered_original_indices": original_indices,
            "pieces": pieces,
            "stats": stats,
        }

    # ---- package solution -------------------------------------------------
    final_grid = np.zeros((N, N, N), dtype=int)
    placements = []

    for rank, cells in enumerate(placements_by_rank):
        orig_idx = original_indices[rank]
        placements.append({
            "piece_rank": rank,
            "piece_idx": orig_idx,
            "cells": cells,
        })
        for c in cells:
            final_grid[c] = orig_idx + 1

    # IMPORTANT: keep `placements` in rank order (= solver placement order).
    # This is what the animation needs to show a meaningful construction.
    # A piece-id-sorted view is provided separately.
    placements_by_piece_idx = sorted(placements, key=lambda d: d["piece_idx"])

    return {
        "status": "solved",
        "message": None,
        "runtime_sec": runtime,
        "N": N,
        "grid": final_grid,
        "placements": placements,
        "placements_by_piece_idx": placements_by_piece_idx,
        "ordered_original_indices": original_indices,
        "pieces": pieces,
        "stats": stats,
    }


# ============================================================
# 7b. Spec-compliant public entry point
# ============================================================
#
# The course spec ("Professor Cubazoid's 3D Tetris") states:
#   > "gives as output a configuration of the objects that forms a
#   >  perfect cube if such a configuration exists and it returns null
#   >  otherwise."
#
# `solve()` is the thin, permissive wrapper that matches that contract
# exactly: return an N x N x N numpy array labelled with piece IDs on
# success, or None otherwise. `solve_final()` (above) remains the
# full-featured API used by our test suite, notebook, and visualiser.

def solve(pieces, timeout_sec: float = 30.0):
    """
    Spec-compliant entry point for Professor Cubazoid's 3D Tetris.

    Parameters
    ----------
    pieces : iterable of 3D array-likes
        Each item is a 3D binary tensor (numpy array, nested Python list,
        boolean array, or 0/1 float array all accepted). Each piece must
        describe a 6-connected polycube of 3-5 unit cubes.
    timeout_sec : float, default 30
        Hard time budget for the search.

    Returns
    -------
    numpy.ndarray of shape (N, N, N), dtype int
        A labelled configuration of the input pieces that tiles the
        N x N x N cube. Cell value k > 0 means the cell is occupied by
        input piece number k-1 (so piece ids are 1-indexed in the grid).
    None
        If no such configuration exists, the input is invalid, or the
        solver exceeded ``timeout_sec``.

    Notes
    -----
    For diagnostic information (status string, runtime, placement
    order, per-piece cells for visualisation) call :func:`solve_final`
    instead -- this wrapper discards that metadata to match the spec
    return contract.
    """
    try:
        coerced = _coerce_pieces(pieces)
    except Exception:
        return None

    result = solve_final(coerced, timeout_sec=timeout_sec, verbose=False)
    if result["status"] == "solved":
        return result["grid"]
    return None


def _coerce_pieces(pieces) -> List[np.ndarray]:
    """
    Permissive input coercion for :func:`solve`.

    Accepts any iterable of 3D array-likes with numeric or boolean
    entries; returns a list of int ndarrays with values in {0, 1}
    (nonzero -> 1). Raises ``ValueError`` / ``TypeError`` on anything
    that cannot plausibly be interpreted as a list of 3D binary tensors.
    """
    if pieces is None:
        raise TypeError("pieces is None")
    try:
        items = list(pieces)
    except TypeError:
        raise TypeError("pieces must be iterable")

    coerced: List[np.ndarray] = []
    for i, p in enumerate(items):
        arr = np.asarray(p)
        if arr.ndim != 3:
            raise ValueError(f"piece {i} must be a 3D tensor; got ndim={arr.ndim}")
        if arr.dtype == bool:
            arr = arr.astype(int)
        elif np.issubdtype(arr.dtype, np.floating):
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"piece {i} contains non-finite values")
            arr = (arr != 0).astype(int)
        elif np.issubdtype(arr.dtype, np.integer):
            arr = (arr != 0).astype(int)
        else:
            raise TypeError(
                f"piece {i} has unsupported dtype {arr.dtype}; "
                "expected bool, int, or float"
            )
        coerced.append(arr)
    return coerced


def _fail(status: str, message: str, t0: float, N, pieces) -> Dict:
    return {
        "status": status,
        "message": message,
        "runtime_sec": time.time() - t0,
        "N": N,
        "grid": None,
        "placements": None,
        "placements_by_piece_idx": None,
        "ordered_original_indices": None,
        "pieces": pieces,
        "stats": None,
    }


# ============================================================
# 8. Convenience: solution summary
# ============================================================

def solution_summary(result: Dict) -> str:
    """Human-readable one-line summary of a solver result."""
    s = result["status"]
    if s == "solved":
        return (
            f"SOLVED  N={result['N']}  pieces={len(result['placements'])}  "
            f"t={result['runtime_sec']:.3f}s"
        )
    if s == "timeout":
        return f"TIMEOUT N={result['N']}  t={result['runtime_sec']:.3f}s"
    if s == "no_solution":
        return f"NO_SOLUTION  N={result['N']}  t={result['runtime_sec']:.3f}s"
    return f"{s.upper()}  msg={result.get('message')}"


# ============================================================
# 9. Example cases (kept for backward compatibility with benchmark.py)
# ============================================================

def example_cases() -> List[Tuple[str, List[np.ndarray]]]:
    cases = []

    A = make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    B = make_piece([(1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)])
    cases.append(("2^3_two_tetracubes", [A, B]))

    soma = [
        make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0)]),
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)]),
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0)]),
        make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)]),
        make_piece([(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0)]),
        make_piece([(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 0, 1)]),
        make_piece([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 1, 1)]),
    ]
    cases.append(("3^3_soma_like", soma))

    L4 = make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)])
    cases.append(("4^3_L4_x16", [L4] * 16))

    p1 = make_piece([(0, 0, 0), (1, 0, 0), (2, 0, 0)])
    p2 = make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    cases.append(("impossible_volume_7", [p1, p2]))

    return cases


if __name__ == "__main__":
    print(f"\n{'Case':<25} {'Status':<18} {'Time(s)':>10}")
    print("-" * 58)
    for name, pieces in example_cases():
        result = solve_final(pieces, timeout_sec=20.0, verbose=False)
        print(f"{name:<25} {result['status']:<18} {result['runtime_sec']:>10.3f}")
    print("-" * 58)
