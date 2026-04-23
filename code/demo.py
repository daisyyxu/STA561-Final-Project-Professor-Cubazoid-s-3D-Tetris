from solver import make_piece, solve_final
from visualize import visualize, visualize_static


def build_demo_case():
    # stable 2x2x2 example
    A = make_piece([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])
    B = make_piece([(1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)])
    return [A, B]


if __name__ == "__main__":
    pieces = build_demo_case()

    result = solve_final(pieces, timeout_sec=10.0, verbose=True)

    print("\n===== RESULT =====")
    print("status:", result["status"])
    print("runtime_sec:", round(result["runtime_sec"], 4))
    print("N:", result["N"])

    if result["status"] != "solved":
        print("No visualization because solver did not return a solution.")
    else:
        print("Placements:")
        for item in result["placements"]:
            print(f"piece_idx={item['piece_idx']}, cells={item['cells']}")

        # 1) static snapshot
        visualize_static(result)

        # 2) animation
        visualize(result, interval_ms=700)