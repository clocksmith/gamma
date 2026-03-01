import json

def check_row(row):
    try:
        data = json.loads(row)
        if data["pos"] != data["target_pos"]:
            return False, "pos != target_pos"
        if data["neg"] != data["target_neg"]:
            return False, "neg != target_neg"
        if not data["source"] or not data["target_pos"] or not data["target_neg"]:
            return False, "Empty field"
        return True, ""
    except Exception as e:
        return False, str(e)

with open("existing_rows.jsonl", "r") as f:
    lines = f.readlines()

errors = []
for i, line in enumerate(lines):
    is_valid, reason = check_row(line)
    if not is_valid:
        errors.append((i, reason))

print(f"Found {len(errors)} errors in {len(lines)} rows.")
for idx, err in errors[:10]:
    print(f"Row {idx}: {err}")
