# ============================================================
# ChroniKeeper – Unified Test Runner (Stable Final Version)
# Simple, reliable, and clean.
# ============================================================

import os
import sys
import importlib
import traceback
from io import StringIO
from datetime import datetime

TEST_DIR = "tests"
LOG_DIR = "logs"
AUTO_REFRESH = False  # toggled in runtime or via --auto


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def list_tests():
    if not os.path.exists(TEST_DIR):
        print(f"[ERROR] Missing '{TEST_DIR}' directory.")
        return []
    files = [f for f in os.listdir(TEST_DIR)
             if f.startswith("test_") and f.endswith(".py")]
    return sorted(os.path.splitext(f)[0] for f in files)


def save_log(test_name: str, content: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(LOG_DIR, f"test_{test_name}_{ts}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[LOG] Saved output to {path}\n")


class MultiOut:
    """Duplicates stdout to a StringIO buffer."""
    def __init__(self, stream1, stream2):
        self.stream1, self.stream2 = stream1, stream2
    def write(self, data):
        self.stream1.write(data)
        self.stream2.write(data)
    def flush(self):
        self.stream1.flush()
        self.stream2.flush()


def run_test(test_name, buffered=False):
    """Import and run a test, capturing output for logs."""
    try:
        module = importlib.import_module(f"{TEST_DIR}.{test_name}")
        print(f"\n=== Running {test_name} ===\n")

        output = ""
        if hasattr(module, "main"):
            buffer = StringIO()
            if buffered:
                old_stdout = sys.stdout
                sys.stdout = buffer
                try:
                    module.main()
                finally:
                    sys.stdout = old_stdout
                output = buffer.getvalue()
                print(output)
            else:
                old_stdout = sys.stdout
                sys.stdout = MultiOut(sys.stdout, buffer)
                try:
                    module.main()
                finally:
                    sys.stdout = old_stdout
                output = buffer.getvalue()
        else:
            output = f"[WARN] {test_name} has no main() function.\n"
            print(output)

    except Exception:
        output = traceback.format_exc()
        print(output)

    save_log(test_name, output)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_menu(tests, buffered):
    clear_screen()
    print("=== ChroniKeeper Test Launcher ===")
    print(f"Output mode: {'Buffered (o=live next)' if buffered else 'Live (o=buffered next)'}")
    print(f"Auto-refresh: {'ON' if AUTO_REFRESH else 'OFF'}")
    print("r - Refresh list | o - Toggle output | a - Toggle auto-refresh | "
          "c - Clear screen | 0 - Exit\n")
    for i, name in enumerate(tests, start=1):
        print(f"{i}. {name}")
    print()


def print_controls(buffered):
    print("=" * 60)
    print(f"[r] Refresh list  |  [o] Toggle output (now {'buffered' if buffered else 'live'})")
    print("[a] Toggle auto-refresh  |  [c] Clear screen  |  [0] Exit launcher")
    print("=" * 60 + "\n")


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
def main():
    global AUTO_REFRESH
    # check CLI args
    if "--auto" in sys.argv:
        AUTO_REFRESH = True

    buffered = False
    tests = list_tests()
    print_menu(tests, buffered)

    while True:
        if AUTO_REFRESH:
            tests = list_tests()
            print_menu(tests, buffered)

        cmd = input("Select test number (or command): ").strip().lower()

        if cmd == "0":
            print("Exiting test launcher.")
            break
        elif cmd == "r":
            tests = list_tests()
            print_menu(tests, buffered)
            print("[INFO] Test list refreshed.\n")
        elif cmd == "a":
            AUTO_REFRESH = not AUTO_REFRESH
            print(f"[INFO] Auto-refresh is now {'ON' if AUTO_REFRESH else 'OFF'}.\n")
        elif cmd == "c":
            clear_screen()
        elif cmd == "o":
            buffered = not buffered
            print(f"[INFO] Output mode set to {'buffered' if buffered else 'live'}.\n")
        else:
            try:
                num = int(cmd)
                if 1 <= num <= len(tests):
                    run_test(tests[num - 1], buffered=buffered)
                    print_controls(buffered)
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Enter a valid number or command (r/a/o/c/0).")


if __name__ == "__main__":
    main()
