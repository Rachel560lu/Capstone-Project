import json
import os
from typing import Iterable, List, Union


DATA_JSON_PATH = \
    "/Users/apple/Desktop/VirtualFurnishing/data/model_infos_with_price.json"
OUTPUT_TXT_PATH = \
    "/Users/apple/Desktop/VirtualFurnishing/data_process/modern_model_ids.txt"


def normalize_style(value: Union[str, List[str], None]) -> List[str]:
    """Return a list of lowercase styles for flexible matching."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().lower()]
    if isinstance(value, list):
        normalized: List[str] = []
        for item in value:
            if isinstance(item, str):
                normalized.append(item.strip().lower())
        return normalized
    return []


def extract_model_ids(records: Iterable[dict], target_style: str = "modern") -> List[str]:
    target = target_style.lower()
    results: List[str] = []
    for rec in records:
        # Be tolerant to key typos/case variants
        style_value = (
            rec.get("style")
            or rec.get("Style")
            or rec.get("syle")  # common typo observed in datasets
            or rec.get("Syle")
        )
        styles = normalize_style(style_value)
        if target in styles:
            model_id = (
                rec.get("model_id")
                or rec.get("modelId")
                or rec.get("id")
            )
            if isinstance(model_id, (str, int)):
                results.append(str(model_id))
    return results


def load_records(path: str) -> Iterable[dict]:
    """
    Try loading as a JSON array first; if that fails, fall back to JSON Lines.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    # Try parse as a standard JSON value (likely a list)
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        # If it's a dict with a known container key, try common wrappers
        if isinstance(data, dict):
            for key in ("data", "items", "records", "list"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            # otherwise treat dict itself as a single record
            return [data]
    except json.JSONDecodeError:
        pass

    # Fallback: JSON Lines
    records: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    records.append(obj)
            except json.JSONDecodeError:
                # skip malformed line
                continue
    return records


def main() -> None:
    if not os.path.exists(DATA_JSON_PATH):
        raise FileNotFoundError(f"Input JSON not found: {DATA_JSON_PATH}")

    records = load_records(DATA_JSON_PATH)
    model_ids = extract_model_ids(records, target_style="modern")

    # Deduplicate while preserving order
    seen = set()
    unique_ids: List[str] = []
    for mid in model_ids:
        if mid not in seen:
            seen.add(mid)
            unique_ids.append(mid)

    with open(OUTPUT_TXT_PATH, "w", encoding="utf-8") as out:
        for mid in unique_ids:
            out.write(mid + "\n")

    print(
        f"Exported {len(unique_ids)} model_id(s) with style 'Modern' to: {OUTPUT_TXT_PATH}"
    )


if __name__ == "__main__":
    main()


