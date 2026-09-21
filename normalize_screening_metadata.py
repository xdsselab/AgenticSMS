"""Mark contradictory legacy IC placeholders as unresolved, retaining an audit log.

This is metadata cleanup, not a new eligibility assessment. Original values are
preserved in the audit CSV and the pre-revision backup.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [ROOT / "data/all_summary_final_665.csv",
           ROOT / "database for github/data/all_summary_final_665.csv"]
FIELDS = [f"IC{i}_pass" for i in range(1, 8)]
AUDIT = ROOT / "elsarticle/figures/data/screening_metadata_audit.csv"

def main():
    audit = []
    for path in TARGETS:
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            rows = list(reader)
        changed = 0
        for row in rows:
            # All seven flags are identical negatives despite final inclusion.
            # Do not treat these as verified passes or alter substantive coding.
            if row.get("included", "").lower() == "true" and all(row.get(k) == "no" for k in FIELDS):
                for key in FIELDS:
                    audit.append({"file": str(path.relative_to(ROOT)), "key": row["key"],
                                  "field": key, "old_value": row[key], "new_value": "not_recorded",
                                  "reason": "uniform negative legacy flags conflict with included=True; suspected defaults, not independently verified"})
                    row[key] = "not_recorded"
                changed += 1
        if changed:
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        print(f"{path.relative_to(ROOT)}: {changed} records normalized")
    if audit:
        # Refuse to overwrite an existing audit trail from another revision.
        with AUDIT.open("x", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(audit[0]))
            writer.writeheader()
            writer.writerows(audit)

if __name__ == "__main__":
    main()
