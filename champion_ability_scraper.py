import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_FILE = os.path.join(BASE_DIR, "champion_abilities.json")
ABILITY_ICONS_DIR = os.path.join(BASE_DIR, "assets", "ability_icons")
CHAMPION_ICONS_DIR = os.path.join(BASE_DIR, "assets", "champion_icons")

DDRAGON = "https://ddragon.leagueoflegends.com"
LANGUAGE = "en_US"

# Data Dragon lists a champion's spells in this order
ABILITY_KEYS = ["Q", "W", "E", "R"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

MAX_WORKERS = 16


# ============================================================
# HTTP
# ============================================================


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
    with open(dest, "wb") as out_file:
        out_file.write(data)


# ============================================================
# CHAMPIONS
# ============================================================


def fetch_champion(version, champion_id):
    url = (
        f"{DDRAGON}/cdn/{version}/data/{LANGUAGE}/champion/{champion_id}.json"
    )
    champion = fetch_json(url)["data"][champion_id]

    abilities = {}
    for key, spell in zip(ABILITY_KEYS, champion["spells"]):
        abilities[key] = {
            "name": spell["name"],
            "icon": spell["image"]["full"],
        }

    return champion_id, {
        "name": champion["name"],
        "icon": champion["image"]["full"],
        "abilities": abilities,
    }


def download_icons(label, icons, base_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    missing = [
        icon
        for icon in icons
        if not os.path.exists(os.path.join(output_dir, icon))
    ]
    print(
        f"{label}: {len(icons)} total, "
        f"{len(icons) - len(missing)} already downloaded, "
        f"{len(missing)} to download"
    )

    failed = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(
                download_file,
                f"{base_url}/{icon}",
                os.path.join(output_dir, icon),
            ): icon
            for icon in missing
        }
        for future in as_completed(futures):
            icon = futures[future]
            try:
                future.result()
            except Exception as e:
                failed.append(icon)
                print(f"  [FAIL] {icon} -> {e}")

    return failed


# ============================================================
# MAIN
# ============================================================


def main():
    version = fetch_json(f"{DDRAGON}/api/versions.json")[0]
    print(f"Data Dragon version: {version}")

    champion_list = fetch_json(
        f"{DDRAGON}/cdn/{version}/data/{LANGUAGE}/champion.json"
    )["data"]
    print(f"Found {len(champion_list)} champions")

    # ---- Ability data ----
    champions = {}
    failed = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(fetch_champion, version, champion_id): champion_id
            for champion_id in champion_list
        }
        for future in as_completed(futures):
            champion_id = futures[future]
            try:
                champion_id, champion = future.result()
                champions[champion_id] = champion
            except Exception as e:
                failed.append(champion_id)
                print(f"  [FAIL] {champion_id} -> {e}")

    champions = dict(
        sorted(champions.items(), key=lambda item: item[1]["name"])
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"version": version, "champions": champions},
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Saved {len(champions)} champions to {OUTPUT_FILE}")

    # ---- Icons (skips ones already downloaded) ----
    ability_icons = [
        ability["icon"]
        for champion in champions.values()
        for ability in champion["abilities"].values()
    ]
    champion_icons = [
        champion["icon"]
        for champion in champions.values()
    ]

    icon_failed = download_icons(
        "Ability icons",
        ability_icons,
        f"{DDRAGON}/cdn/{version}/img/spell",
        ABILITY_ICONS_DIR,
    )
    icon_failed += download_icons(
        "Champion icons",
        champion_icons,
        f"{DDRAGON}/cdn/{version}/img/champion",
        CHAMPION_ICONS_DIR,
    )

    print("\nDone.")
    if failed:
        print(f"Champions failed: {', '.join(failed)}")
    if icon_failed:
        print(f"Icons failed: {', '.join(icon_failed)}")


if __name__ == "__main__":
    main()
