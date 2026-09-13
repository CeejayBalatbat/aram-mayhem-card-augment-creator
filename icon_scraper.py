from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import requests

# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "aram_mayhem_augments_raw.json"
OUTPUT_DIR = "assets/icons"

# The multiple locations CDragon uses for augment and item icons
URL_CANDIDATES = [
    (
        "https://raw.communitydragon.org/latest/game/assets/ux/kiwi/augments/icons/"
    ),
    (
        "https://raw.communitydragon.org/latest/game/assets/ux/cherry/augments/icons/"
    ),
    "https://raw.communitydragon.org/latest/game/assets/items/icons2d/",
    "https://raw.communitydragon.org/latest/game/",
]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}


# ============================================================
# FILENAME
# ============================================================


def sanitize_filename(name):
  """Makes the augment name match the format used by main.py."""
  name = str(name).strip()
  name = re.sub(r'[<>:"/\\|?*]', "", name)
  name = re.sub(r"\s+", "_", name)
  return name


# ============================================================
# LOAD METADATA
# ============================================================


def load_augments():
  with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

  if "metadata" in data:
    metadata = data["metadata"]
  elif "raw" in data and "metadata" in data["raw"]:
    metadata = data["raw"]["metadata"]
  else:
    raise ValueError("Could not find augment metadata in the JSON file.")

  augments = []

  for augment in metadata.values():
    if not isinstance(augment, dict):
      continue

    augment_id = augment.get("id")
    name = augment.get("name")
    icon = augment.get("iconLarge")

    if not augment_id or not name or not icon:
      continue

    augments.append({"id": augment_id, "name": name, "icon": icon})

  return augments


# ============================================================
# DOWNLOAD (WITH MULTI-ENDPOINT FALLBACK)
# ============================================================


def download_icon(augment):
  augment_id = augment["id"]
  name = augment["name"]
  icon = augment["icon"]  # e.g., "goliath_large.png"

  safe_name = sanitize_filename(name)
  filename = f"{int(augment_id):04d}_{safe_name}_large.png"
  output_path = os.path.join(OUTPUT_DIR, filename)

  # Don't re-download what you already have
  if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
    return "skipped", augment

  # Strip leading slashes if present
  clean_icon = icon.lstrip("/")

  # Iterate through candidate URLs until one responds with 200 OK
  for base_url in URL_CANDIDATES:
    url = base_url + clean_icon
    try:
      response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
      if response.status_code == 200:
        with open(output_path, "wb") as f:
          f.write(response.content)
        return "downloaded", augment
    except Exception:
      continue

  return "404", augment


# ============================================================
# MAIN
# ============================================================


def main():
  os.makedirs(OUTPUT_DIR, exist_ok=True)

  print("Loading augment metadata...")
  augments = load_augments()
  print(f"Found {len(augments)} augment icons to verify/download.")
  print("\nDownloading missing icons across Kiwi & Cherry CDragon paths...\n")

  downloaded = 0
  skipped = 0
  not_found = 0
  failed = 0

  with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(download_icon, aug) for aug in augments]

    for future in as_completed(futures):
      result, augment = future.result()

      if result == "downloaded":
        downloaded += 1
        print(f"[OK] {augment['id']} {augment['name']}")
      elif result == "skipped":
        skipped += 1
      elif result == "404":
        not_found += 1
        print(f"[404 NOT FOUND] {augment['id']} {augment['name']}")
      elif result == "failed":
        failed += 1

  print("\n================================")
  print("Download Summary")
  print("================================")
  print(f"Total entries: {len(augments)}")
  print(f"Newly Downloaded: {downloaded}")
  print(f"Already Present (Skipped): {skipped}")
  print(f"Missing (404): {not_found}")
  print(f"Failed: {failed}")
  print(f"\nIcons directory: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
  main()