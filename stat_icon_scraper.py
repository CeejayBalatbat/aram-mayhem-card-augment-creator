import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STAT_ICONS_DIR = os.path.join(BASE_DIR, "assets", "stat_icons")

STAT_ICONS = {
    # Core Shard Icons
    "adaptive_force.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodsadaptiveforceicon.png",
    "armor.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodsarmoricon.png",
    "attack_speed.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodsattackspeedicon.png",
    "ability_haste.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodscdrscalingicon.png",
    "health.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodshealthplusicon.png",
    "magic_resist.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodsmagicresicon.png",
    "movement_speed.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodsmovementspeedicon.png",
    "tenacity.png": "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods/statmodstenacityicon.png",
    "attack_damage.png": "https://raw.communitydragon.org/latest/game/assets/perks/statmods/statmodsattackdamageicon.png",
    "ability_power.png": "https://raw.communitydragon.org/latest/game/assets/perks/statmods/statmodsabilitypowericon.png",

    # Floating Text / Tooltip Stat Icons
    "critical_strike.png": "https://raw.communitydragon.org/latest/game/assets/ux/floatingtext/criticon.png",
}

def main():
    os.makedirs(STAT_ICONS_DIR, exist_ok=True)
    print(f"Downloading stat icons into: {STAT_ICONS_DIR}")

    headers = {"User-Agent": "Mozilla/5.0"}

    for filename, url in STAT_ICONS.items():
        dest = os.path.join(STAT_ICONS_DIR, filename)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(dest, "wb") as out_file:
                out_file.write(response.read())
            print(f"  [OK] {filename}")
        except Exception as e:
            print(f"  [FAIL] {filename} from {url} -> {e}")

    print("\nDownload complete.")

if __name__ == "__main__":
    main()