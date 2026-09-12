import json
import sys
from datetime import date

PROGRESS_FILE = "progress.json"


def load_tasks():
    with open(PROGRESS_FILE, "r") as f:
        data = json.load(f)
    return data["tasks"]


def save_tasks(tasks):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"tasks": tasks}, f, indent=2)


def show_status(tasks):
    done_count = sum(1 for t in tasks if t["done"])
    total = len(tasks)

    print(f"\nScriptlyAI Progress — {done_count}/{total} days complete\n")

    for t in tasks:
        mark = "✅" if t["done"] else "⬜"
        print(f"{mark} Day {t['day']:>2}: {t['title']}")

    percent = round((done_count / total) * 100) if total else 0
    print(f"\n{percent}% complete\n")


def mark_task(tasks, day_number, done_value):
    found = False

    for t in tasks:
        if t["day"] == day_number:
            t["done"] = done_value
            found = True

    if not found:
        print(f"No task found for Day {day_number}.")
        return False

    return True


def main():
    tasks = load_tasks()

    if len(sys.argv) == 1:
        show_status(tasks)
        return

    command = sys.argv[1]

    if command == "done" and len(sys.argv) == 3:
        day_number = int(sys.argv[2])
        if mark_task(tasks, day_number, True):
            save_tasks(tasks)
            print(f"Marked Day {day_number} as done. ✅")

    elif command == "undo" and len(sys.argv) == 3:
        day_number = int(sys.argv[2])
        if mark_task(tasks, day_number, False):
            save_tasks(tasks)
            print(f"Marked Day {day_number} as not done. ⬜")

    else:
        print("Usage:")
        print("  python progress_tracker.py            → show status")
        print("  python progress_tracker.py done 3      → mark Day 3 complete")
        print("  python progress_tracker.py undo 3      → unmark Day 3")


if __name__ == "__main__":
    main()