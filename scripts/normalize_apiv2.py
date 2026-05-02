"""Normalize semua JSON di apiv2/ jadi pretty-printed (indent=2).

Tujuan: supaya diff per baris (mis. penambahan dari merge_from_csv.py) gampang
di-review di git. Sebelum normalize, file json di apiv2/ ditulis dalam satu
baris panjang sehingga diff tidak terbaca.

Hanya re-write file yang perubahan format-nya berubah (skip kalau sudah
indent=2). Tidak mengubah isi data, hanya formatting.

Usage:
    python3 scripts/normalize_apiv2.py            # eksekusi nyata
    python3 scripts/normalize_apiv2.py --dry-run  # preview tanpa nulis
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APIV2_DIR = os.path.join(ROOT, 'apiv2')


def normalize_file(path):
    """Re-dump JSON dengan indent=2. Return True kalau file berubah."""
    with open(path, encoding='utf-8') as f:
        original = f.read()
        data = json.loads(original)

    formatted = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if original == formatted:
        return False
    return formatted


def collect_files():
    yield os.path.join(APIV2_DIR, 'provinces.json')
    for sub in ('regencies', 'districts', 'villages'):
        path = os.path.join(APIV2_DIR, sub)
        for fname in sorted(os.listdir(path)):
            if fname.endswith('.json'):
                yield os.path.join(path, fname)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='Preview tanpa nulis file')
    args = ap.parse_args()

    files = list(collect_files())
    print(f'Total file JSON di apiv2/: {len(files)}')

    changed = 0
    for path in files:
        result = normalize_file(path)
        if result is False:
            continue
        changed += 1
        if not args.dry_run:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(result)

    if args.dry_run:
        print(f'[DRY RUN] {changed} file akan di-reformat.')
    else:
        print(f'{changed} file di-reformat ke indent=2.')


if __name__ == '__main__':
    main()
