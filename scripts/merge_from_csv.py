"""Additive merge: tambahkan wilayah dari wilayahindo2006.csv ke apiv2/.

- Pertahankan nama wilayah yang sudah ada di apiv2/ (mis. "DKI. Jakarta" tidak
  ditimpa oleh "DKI Jakarta" dari CSV).
- Hanya append entry yang ID-nya belum ada di apiv2/.
- Nama entry baru di-uppercase agar konsisten dengan style apiv2/.
- Tulis 4 markdown tracking di root proyek: provinsi/kabupaten/kecamatan/desa_tambahan.md.
- Idempoten: run kedua kali tidak menghasilkan perubahan.

Usage:
    python3 scripts/merge_from_csv.py            # eksekusi nyata
    python3 scripts/merge_from_csv.py --dry-run  # preview tanpa nulis file
"""
import argparse
import csv
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(ROOT, 'wilayahindo2006.csv')
APIV2_DIR = os.path.join(ROOT, 'apiv2')


def load_existing():
    provinces = {}
    with open(os.path.join(APIV2_DIR, 'provinces.json'), encoding='utf-8') as f:
        for entry in json.load(f):
            provinces[entry['id']] = entry

    def load_dir(subdir):
        bucket = {}
        path = os.path.join(APIV2_DIR, subdir)
        for fname in os.listdir(path):
            if not fname.endswith('.json'):
                continue
            key = fname[:-5]
            with open(os.path.join(path, fname), encoding='utf-8') as f:
                bucket[key] = {e['id']: e for e in json.load(f)}
        return bucket

    return (
        provinces,
        load_dir('regencies'),
        load_dir('districts'),
        load_dir('villages'),
    )


def parse_csv():
    """Yield (prov_id, prov_name, reg_id, reg_name, dist_id, dist_name, vill_id, vill_name)."""
    with open(CSV_FILE, encoding='utf-8') as f:
        for _ in range(3):
            next(f)
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) < 10:
                continue
            kode_prov = row[2].strip()
            kode_kab = row[3].strip()
            kode_kec = row[4].strip()
            kode_kel = row[5].strip()
            provinsi = row[6].strip()
            kabupaten = row[7].strip()
            kecamatan = row[8].strip()
            kelurahan = row[9].strip()

            prov_id = kode_prov.replace('.', '')
            reg_id = (kode_prov + kode_kab).replace('.', '')
            dist_id = (kode_prov + kode_kab + kode_kec).replace('.', '')
            vill_id = (kode_prov + kode_kab + kode_kec + kode_kel).replace('.', '')

            yield (
                prov_id, provinsi,
                reg_id, kabupaten,
                dist_id, kecamatan,
                vill_id, kelurahan,
            )


def merge(provinces, regencies, districts, villages):
    added = {
        'provinces': [],
        'regencies': [],
        'districts': [],
        'villages': [],
    }
    dirty = {
        'provinces': False,
        'regencies': set(),
        'districts': set(),
        'villages': set(),
    }

    for prov_id, prov_name, reg_id, reg_name, dist_id, dist_name, vill_id, vill_name in parse_csv():
        if prov_id not in provinces:
            entry = {'id': prov_id, 'name': prov_name.upper()}
            provinces[prov_id] = entry
            added['provinces'].append(entry)
            dirty['provinces'] = True

        reg_bucket = regencies.setdefault(prov_id, {})
        if reg_id not in reg_bucket:
            entry = {'id': reg_id, 'province_id': prov_id, 'name': reg_name.upper()}
            reg_bucket[reg_id] = entry
            added['regencies'].append(entry)
            dirty['regencies'].add(prov_id)

        dist_bucket = districts.setdefault(reg_id, {})
        if dist_id not in dist_bucket:
            entry = {'id': dist_id, 'regency_id': reg_id, 'name': dist_name.upper()}
            dist_bucket[dist_id] = entry
            added['districts'].append(entry)
            dirty['districts'].add(reg_id)

        vill_bucket = villages.setdefault(dist_id, {})
        if vill_id not in vill_bucket:
            entry = {'id': vill_id, 'district_id': dist_id, 'name': vill_name.upper()}
            vill_bucket[vill_id] = entry
            added['villages'].append(entry)
            dirty['villages'].add(dist_id)

    return added, dirty


def write_apiv2(provinces, regencies, districts, villages, dirty):
    files_written = 0

    if dirty['provinces']:
        path = os.path.join(APIV2_DIR, 'provinces.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                sorted(provinces.values(), key=lambda x: x['id']),
                f, ensure_ascii=False, indent=2,
            )
        files_written += 1

    for prov_id in dirty['regencies']:
        path = os.path.join(APIV2_DIR, 'regencies', f'{prov_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                sorted(regencies[prov_id].values(), key=lambda x: x['id']),
                f, ensure_ascii=False, indent=2,
            )
        files_written += 1

    for reg_id in dirty['districts']:
        path = os.path.join(APIV2_DIR, 'districts', f'{reg_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                sorted(districts[reg_id].values(), key=lambda x: x['id']),
                f, ensure_ascii=False, indent=2,
            )
        files_written += 1

    for dist_id in dirty['villages']:
        path = os.path.join(APIV2_DIR, 'villages', f'{dist_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                sorted(villages[dist_id].values(), key=lambda x: x['id']),
                f, ensure_ascii=False, indent=2,
            )
        files_written += 1

    return files_written


def write_markdown(filename, title, header_row, rows):
    today = date.today().isoformat()
    path = os.path.join(ROOT, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write(f'Daftar yang ditambahkan dari `wilayahindo2006.csv` (KEPMENDAGRI 300.2.2-2138/2025) pada **{today}**.\n\n')
        if not rows:
            f.write('Tidak ada penambahan.\n')
            return
        f.write('| ' + ' | '.join(header_row) + ' |\n')
        f.write('|' + '|'.join(['---'] * len(header_row)) + '|\n')
        for i, row in enumerate(rows, 1):
            f.write('| ' + ' | '.join([str(i)] + [str(c) for c in row]) + ' |\n')
        f.write(f'\n**Total: {len(rows)}**\n')


def write_tracking(added):
    write_markdown(
        'provinsi_tambahan.md',
        'Provinsi Tambahan',
        ['No', 'ID', 'Nama'],
        [(p['id'], p['name']) for p in sorted(added['provinces'], key=lambda x: x['id'])],
    )
    write_markdown(
        'kabupaten_tambahan.md',
        'Kabupaten/Kota Tambahan',
        ['No', 'ID', 'Nama', 'ID Provinsi'],
        [(r['id'], r['name'], r['province_id']) for r in sorted(added['regencies'], key=lambda x: x['id'])],
    )
    write_markdown(
        'kecamatan_tambahan.md',
        'Kecamatan Tambahan',
        ['No', 'ID', 'Nama', 'ID Kabupaten'],
        [(d['id'], d['name'], d['regency_id']) for d in sorted(added['districts'], key=lambda x: x['id'])],
    )
    write_villages_md(added['villages'])


def write_villages_md(villages_added):
    today = date.today().isoformat()
    path = os.path.join(ROOT, 'desa_tambahan.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Desa/Kelurahan Tambahan\n\n')
        f.write(f'Daftar yang ditambahkan dari `wilayahindo2006.csv` (KEPMENDAGRI 300.2.2-2138/2025) pada **{today}**.\n\n')
        if not villages_added:
            f.write('Tidak ada penambahan.\n')
            return
        f.write('| No | ID Desa | Nama Desa | ID Kecamatan | File Villages |\n')
        f.write('|---|---|---|---|---|\n')
        for i, v in enumerate(sorted(villages_added, key=lambda x: x['id']), 1):
            f.write(f"| {i} | {v['id']} | {v['name']} | {v['district_id']} | `villages/{v['district_id']}.json` |\n")
        f.write(f'\n**Total: {len(villages_added)}**\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='Preview tanpa nulis file')
    args = ap.parse_args()

    print('Loading apiv2/...')
    provinces, regencies, districts, villages = load_existing()
    print(f'  provinces: {len(provinces)}')
    print(f'  regencies files: {len(regencies)}')
    print(f'  districts files: {len(districts)}')
    print(f'  villages files: {len(villages)}')

    print(f'Parsing {os.path.basename(CSV_FILE)}...')
    added, dirty = merge(provinces, regencies, districts, villages)

    print('\n=== Penambahan ===')
    print(f'  provinsi   : {len(added["provinces"])}')
    print(f'  kabupaten  : {len(added["regencies"])}')
    print(f'  kecamatan  : {len(added["districts"])}')
    print(f'  desa       : {len(added["villages"])}')

    if args.dry_run:
        print('\n[DRY RUN] tidak menulis ke disk.')
        return

    files_written = write_apiv2(provinces, regencies, districts, villages, dirty)
    write_tracking(added)
    print(f'\nApiv2 files rewritten: {files_written}')
    print('Tracking markdown ditulis: provinsi_tambahan.md, kabupaten_tambahan.md, kecamatan_tambahan.md, desa_tambahan.md')


if __name__ == '__main__':
    main()
