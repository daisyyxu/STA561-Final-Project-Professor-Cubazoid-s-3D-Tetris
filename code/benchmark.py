from solver import solve_final, example_cases


def run_benchmark(timeout_sec=20.0):
    cases = example_cases()

    print(f"\n{'Case':<25} {'Status':<18} {'Runtime(s)':>12} {'N':>4}")
    print("-" * 68)

    solved = 0
    timeout = 0
    no_solution = 0
    invalid = 0

    rows = []

    for name, pieces in cases:
        result = solve_final(pieces, timeout_sec=timeout_sec, verbose=False)
        status = result["status"]
        runtime = result["runtime_sec"]
        N = result["N"]

        rows.append((name, status, runtime, N))
        print(f"{name:<25} {status:<18} {runtime:>12.3f} {str(N):>4}")

        if status == "solved":
            solved += 1
        elif status == "timeout":
            timeout += 1
        elif status == "no_solution":
            no_solution += 1
        else:
            invalid += 1

    print("-" * 68)
    print("Summary:")
    print("  solved       =", solved)
    print("  timeout      =", timeout)
    print("  no_solution  =", no_solution)
    print("  invalid/etc  =", invalid)

    return rows


if __name__ == "__main__":
    run_benchmark(timeout_sec=20.0)
