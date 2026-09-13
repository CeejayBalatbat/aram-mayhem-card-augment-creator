import json
import html
import re
from datetime import datetime, timezone

import requests


MAYHEM_API = (
    "https://data.v2.iesdev.com/api/v1/"
    "query_objects/prod/lol/aram_mayhem_augments"
)

MAYHEM_SETS_API = (
    "https://data.v2.iesdev.com/api/v1/"
    "query_objects/prod/lol/aram_mayhem_augment_sets"
)

METADATA_URL = (
    "https://hextech.dtodo.cn/data/"
    "aram-mayhem-augments.en_us.json"
)

OUTPUT_FILE = "augments.json"
RAW_FILE = "aram_mayhem_augments_raw.json"


def sanitize_filename(name):
    """
    Match the filename sanitizing behavior used by main.py.
    """
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name


def fetch_json(url):
    print(f"Fetching: {url}")

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()
    return response.json()


def get_api_stats(api_data):
    """
    Convert the Mayhem API's data array into:

        {
            "1001": {...},
            "1002": {...},
            ...
        }

    The API contains many more records than the actual localized
    augment metadata, so we use it only as supplemental data.
    """

    records = api_data.get("data", [])

    stats_map = {}

    for record in records:
        augment_id = record.get("augment_id")

        if augment_id is None:
            continue

        augment_id = str(augment_id)

        stats_map[augment_id] = {
            "patch": record.get("patch"),
            "date": record.get("dt"),
            "stats": record.get("stats", {})
        }

    return stats_map

MANUAL_TAGS_FILE = "augment_tags_manual.json"


# ---------------------------------------------------------
# Tag heuristics
# ---------------------------------------------------------

TAG_RULES = {
    "Quest": [
        r"\bquest\b",
        r"\bcomplete\b.*\bquest\b",
    ],

    "Damage": [
        r"\bdeal\b.*\bdamage\b",
        r"\bbonus damage\b",
        r"\bincreased damage\b",
        r"\bdamage dealt\b",
        r"\bphysical damage\b",
        r"\bmagic damage\b",
        r"\btrue damage\b",
    ],

    "Defense": [
        r"\barmor\b",
        r"\bmagic resist\b",
        r"\bmr\b",
        r"\bhealth\b",
        r"\bshield\b",
        r"\bdamage reduction\b",
        r"\btenacity\b",
    ],

    "Healing": [
        r"\bheal\b",
        r"\bhealing\b",
        r"\blifesteal\b",
        r"\bomnivamp\b",
        r"\bhealth restored\b",
    ],

    "Attack Speed": [
        r"\battack speed\b",
        r"\battacks? per second\b",
    ],

    "Ability Haste": [
        r"\bability haste\b",
        r"\bcooldown reduction\b",
        r"\bcooldowns?\b",
    ],

    "Crit": [
        r"\bcritical strike\b",
        r"\bcrit(ical)?\b",
    ],

    "On-Hit": [
        r"\bon-hit\b",
        r"\bon hit\b",
        r"\battacks? apply\b",
        r"\bevery \d+ attacks?\b",
    ],

    "Mobility": [
        r"\bmovement speed\b",
        r"\bdash\b",
        r"\bblink\b",
        r"\bspeed\b",
    ],

    "Gold": [
        r"\bgold\b",
        r"\bshop\b",
        r"\bitem cost\b",
        r"\bitems? cost\b",
    ],

    "Summon": [
        r"\bsummon\b",
        r"\bsummoned\b",
        r"\bturret\b",
        r"\bpet\b",
        r"\bminion\b",
    ],

    "Utility": [
        r"\brange\b",
        r"\bvision\b",
        r"\bstealth\b",
        r"\binvisible\b",
        r"\bpolymorph\b",
        r"\bslow\b",
        r"\bstun\b",
        r"\broot\b",
        r"\bsilence\b",
    ],
}


def clean_description(text):
    """
    Convert Riot/HTML-ish description text into something
    suitable for heuristic matching.
    """

    if not text:
        return ""

    text = html.unescape(str(text))

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_heuristic_tags(augment):
    """
    Automatically determine likely augment categories from
    the augment's name and description.

    This is intentionally conservative. Manual overrides can
    correct anything the heuristic gets wrong.
    """

    name = augment.get("name", "")
    description = clean_description(
        augment.get("description", "")
    )

    api_name = augment.get("apiName", "")

    searchable_text = " ".join(
        [
            str(name),
            str(description),
            str(api_name),
        ]
    ).lower()

    tags = []

    for tag, patterns in TAG_RULES.items():

        for pattern in patterns:

            if re.search(pattern, searchable_text):
                tags.append(tag)
                break

    return tags


def load_manual_tags():
    """
    Load optional manual tag corrections.

    Missing file is completely fine.
    """

    try:

        with open(
            MANUAL_TAGS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            print(
                f"Warning: {MANUAL_TAGS_FILE} "
                "must contain a JSON object."
            )

            return {}

        return data

    except FileNotFoundError:

        return {}

    except json.JSONDecodeError as e:

        print(
            f"Warning: Could not parse "
            f"{MANUAL_TAGS_FILE}: {e}"
        )

        return {}


def apply_manual_tags(name, tags, manual_tags):
    """
    Apply manual corrections to automatically generated tags.

    Supported operations:

        {
            "Some Augment": {
                "replace": ["Damage"],
                "add": ["Quest"],
                "remove": ["Utility"]
            }
        }
    """

    override = manual_tags.get(name)

    if not isinstance(override, dict):
        return tags

    result = list(tags)

    # -----------------------------------------------------
    # Replace
    # -----------------------------------------------------

    if "replace" in override:

        replacement = override.get("replace", [])

        if isinstance(replacement, list):
            result = list(replacement)

    # -----------------------------------------------------
    # Add
    # -----------------------------------------------------

    additions = override.get("add", [])

    if isinstance(additions, list):

        for tag in additions:

            if tag not in result:
                result.append(tag)

    # -----------------------------------------------------
    # Remove
    # -----------------------------------------------------

    removals = override.get("remove", [])

    if isinstance(removals, list):

        result = [
            tag
            for tag in result
            if tag not in removals
        ]

    return result

def build_augments(metadata, stats_map, manual_tags):
    """
    Build the clean schema consumed by main.py.

    The metadata endpoint is the authoritative list of actual
    Mayhem augment definitions.
    """

    augments = []

    for augment_id, data in metadata.items():

        # Ignore malformed metadata entries.
        if not isinstance(data, dict):
            continue

        # The metadata key is the actual augment ID.
        augment_id = str(augment_id)

        display_name = data.get("displayName")

        if not display_name:
            continue

        description = data.get("description", "")
        api_name = data.get("name")
        rarity = data.get("rarity")

        # Convert the source rarity to the schema expected by main.py.
        if rarity is None:
            rarity = 0

        # Local icon filename produced by the icon scraper.
        safe_name = sanitize_filename(display_name)

        if augment_id.isdigit():
            icon_prefix = f"{int(augment_id):04d}"
        else:
            icon_prefix = augment_id

        icon_filename = (
            f"{icon_prefix}_{safe_name}_large.png"
        )

        # API statistics are supplemental.
        api_info = stats_map.get(augment_id, {})

        stats = api_info.get("stats", {})

        # Automatically determine tags from the augment text.
        tags = get_heuristic_tags({
            "name": display_name,
            "description": description,
            "apiName": api_name
        })

        # Apply manual corrections if present.
        tags = apply_manual_tags(
            display_name,
            tags,
            manual_tags
        )

        augment = {
            "id": augment_id,
            "name": display_name,
            "apiName": api_name,
            "tier": rarity,
            "rarity": rarity,
            "tags": tags,
            "description": description,
            "icon": icon_filename,

            # Keep the actual Riot source icon name too.
            "sourceIcon": data.get("iconLarge"),

            # Useful metadata from the Mayhem API.
            "enabled": data.get("enabled", True),
            "patch": api_info.get("patch"),
            "stats": stats
        }

        augments.append(augment)

    return augments


def main():

    print("=== ARAM Mayhem Augment Scraper ===")
    print()

    # ---------------------------------------------------------
    # Fetch sources
    # ---------------------------------------------------------

    mayhem_api = fetch_json(MAYHEM_API)
    mayhem_sets = fetch_json(MAYHEM_SETS_API)
    metadata = fetch_json(METADATA_URL)

    # ---------------------------------------------------------
    # Save the raw responses for debugging
    # ---------------------------------------------------------

    raw_data = {
        "source": {
            "mayhem_api": MAYHEM_API,
            "mayhem_sets_api": MAYHEM_SETS_API,
            "metadata": METADATA_URL
        },

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "mayhem_augments": mayhem_api,
        "mayhem_sets": mayhem_sets,
        "metadata": metadata
    }

    with open(
        RAW_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            raw_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(f"Raw data saved to: {RAW_FILE}")

    # ---------------------------------------------------------
    # Validate metadata
    # ---------------------------------------------------------

    if not isinstance(metadata, dict):
        raise RuntimeError(
            "Unexpected metadata format. "
            "Expected a dictionary keyed by augment ID."
        )

    print(f"Metadata entries: {len(metadata)}")

    # ---------------------------------------------------------
    # Parse API statistics
    # ---------------------------------------------------------

    stats_map = get_api_stats(mayhem_api)

    manual_tags = load_manual_tags()

    print(
        f"Manual tag overrides: {len(manual_tags)}"
    )

    print(f"API records: {len(stats_map)}")

    # ---------------------------------------------------------
    # Build clean augment list
    # ---------------------------------------------------------

    augments = build_augments(
        metadata,
        stats_map,
        manual_tags
    )

    # Sort numerically by augment ID when possible.
    augments.sort(
        key=lambda x: (
            0,
            int(x["id"])
        )
        if str(x["id"]).isdigit()
        else (
            1,
            str(x["id"])
        )
    )

    # ---------------------------------------------------------
    # Final output
    # ---------------------------------------------------------

    output = {
        "augments": augments
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    print()
    print("=== Finished ===")
    print(f"Actual augments: {len(augments)}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Show a couple of examples.
    for augment in augments[:5]:
        print(
            f'{augment["id"]}: '
            f'{augment["name"]} | '
            f'rarity={augment["rarity"]} | '
            f'tags={augment["tags"]} | '
            f'icon={augment["icon"]}'
        )

if __name__ == "__main__":
    main()