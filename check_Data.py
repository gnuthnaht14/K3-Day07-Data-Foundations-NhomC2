import csv
import re
from pathlib import Path

D = Path("data/k3_university")
# Nếu làm K4:
# D = Path("data/k4_ecommerce")

REQ = [
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
]

KEY = "audience"
# Nếu làm K4:
# KEY = "customer_role"

if not D.exists():
    raise FileNotFoundError(f"Không tìm thấy thư mục: {D}")

sources_path = D / "sources.csv"

if not sources_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {sources_path}")

mds = sorted(D.glob("*.md"))

with sources_path.open(encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))

ids = []
roles = {}

for path in mds:
    content = path.read_text(encoding="utf-8")

    # Kiểm tra YAML front matter
    parts = content.split("---", 2)

    if len(parts) < 3:
        print(f"{path.name:40} THIEU FRONT MATTER")
        continue

    front_matter = parts[1]

    fm = dict(
        re.findall(
            r"^([\w-]+):\s*(.*?)\s*$",
            front_matter,
            re.MULTILINE,
        )
    )

    doc_id = fm.get("doc_id")
    role = fm.get(KEY)

    ids.append(doc_id)
    roles[role] = roles.get(role, 0) + 1

    missing = [key for key in REQ if not fm.get(key)]

    if not fm.get(KEY):
        missing.append(KEY)

    if doc_id != path.stem:
        missing.append(
            f"doc_id phải là '{path.stem}', hiện tại là '{doc_id}'"
        )

    if missing:
        print(
            f"{path.name:40} THIEU/SAI: {', '.join(missing)}"
        )
    else:
        print(f"{path.name:40} OK")

csv_ids = [
    row.get("doc_id")
    for row in rows
    if row.get("doc_id")
]

valid_ids = [
    doc_id
    for doc_id in ids
    if doc_id is not None
]

print()
print("so file :", len(mds), "(can 5-10)")
print(
    "csv     :",
    "khop" if sorted(csv_ids) == sorted(valid_ids) else "LECH",
)
print(KEY, ":", roles)