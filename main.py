import argparse
import os
import subprocess
import sys
import time

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Order matters: icon_scraper.py reads the raw file that
# scrape_mayhem.py writes.
STEPS = [
    {
        "script": "scrape_mayhem.py",
        "label": "Augment data (augments.json)",
    },
    {
        "script": "icon_scraper.py",
        "label": "Augment icons (assets/icons)",
        "requires": "scrape_mayhem.py",
    },
    {
        "script": "champion_ability_scraper.py",
        "label": "Champion abilities (champion_abilities.json)",
    },
]

# Opt-in only: re-downloads and overwrites the stat icons.
STAT_ICONS_STEP = {
    "script": "stat_icon_scraper.py",
    "label": "Stat icons (assets/stat_icons)",
}


# ============================================================
# RUN
# ============================================================


def run_step(step):
    print()
    print("=" * 60)
    print(f"  {step['label']}")
    print(f"  python {step['script']}")
    print("=" * 60)

    # Flush so this header prints before the script's own output.
    sys.stdout.flush()

    start = time.time()

    # The older scrapers use relative paths, so always run
    # from the project folder.
    result = subprocess.run(
        [sys.executable, step["script"]],
        cwd=BASE_DIR,
    )

    elapsed = time.time() - start

    return result.returncode == 0, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Update all scraped data to the latest version."
    )
    parser.add_argument(
        "--stat-icons",
        action="store_true",
        help="Also re-download the stat icons (overwrites them).",
    )
    args = parser.parse_args()

    steps = list(STEPS)
    if args.stat_icons:
        steps.append(STAT_ICONS_STEP)

    results = {}

    for step in steps:
        required = step.get("requires")

        if required and not results.get(required, (False,))[0]:
            print()
            print(f"Skipping {step['script']}: {required} failed.")
            results[step["script"]] = (False, 0)
            continue

        results[step["script"]] = run_step(step)

    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)

    for step in steps:
        ok, elapsed = results[step["script"]]
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] {step['script']:<30} {elapsed:5.1f}s")

    if not all(ok for ok, _ in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
