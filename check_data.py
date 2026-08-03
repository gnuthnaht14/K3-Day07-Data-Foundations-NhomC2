import csv
import re
import sys
from pathlib import Path

# Thư mục kiểm tra mặc định (có thể truyền qua argument: python3 check_data.py data/k3_university)
target_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/rmit'
D = Path(target_dir)

REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version']

print(f"=== ĐANG KIỂM TRA THƯ MỤC: {D} ===")
if not D.exists():
    print(f"❌ Error: Không tìm thấy thư mục {D}")
    sys.exit(1)

mds = sorted(D.glob('*.md'))
sources_file = D / 'sources.csv'

if not sources_file.exists():
    print(f"❌ Error: Không tìm thấy file {sources_file}")
    sys.exit(1)

with open(sources_file, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = [{k.strip(): v.strip() for k, v in r.items() if k} for r in reader]

ids, roles = [], {}
KEY = 'audience'

for p in mds:
    parts = p.read_text(encoding='utf-8').split('---')
    fm = dict(re.findall(r'^(\w+):\s*\"?([^\n\"]+)\"?$', parts[1], re.M)) if len(parts) > 1 else {}
    doc_id = fm.get('doc_id')
    ids.append(doc_id)
    if fm.get(KEY):
        roles[fm.get(KEY)] = roles.get(fm.get(KEY), 0) + 1
    ok = all(k in fm for k in REQ) and KEY in fm and doc_id == p.stem
    status = 'OK' if ok else 'THIEU METADATA'
    print(f'{p.name:40} {status}')

print('----------------------------------------')
print('So file :', len(mds), '(can 5-10)')
print('CSV     :', 'KHOP' if sorted(r.get('doc_id') for r in rows) == sorted(ids) else 'LECH')
print(KEY, '    :', roles)