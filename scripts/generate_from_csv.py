import os
import json
import csv

def generate_api_from_csv():
    csv_file = 'wilayahindo2006.csv'
    output_dir = 'apiv2'

    # Create output directory and subdirectories if they don't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for sub in ['regencies', 'districts', 'villages']:
        path = os.path.join(output_dir, sub)
        if not os.path.exists(path):
            os.makedirs(path)

    print(f"Reading {csv_file}...")

    # Data structures to hold the information
    provinces = []  # List of province objects
    regencies = {}  # prov_id -> list of regency objects
    districts = {}  # reg_id -> list of district objects
    villages = {}   # dist_id -> list of village objects

    # Read CSV file
    with open(csv_file, 'r', encoding='utf-8') as f:
        # Skip the first 3 header lines
        for _ in range(3):
            next(f)

        reader = csv.reader(f, delimiter=';')
        count = 0

        for row in reader:
            if len(row) < 10:  # Skip incomplete rows
                continue

            # Extract data from CSV columns
            # No;Kode Wilayah;Kode_Prov;Kode_Kab;Kode_Kec;Kode_Kel/Desa;Provinsi;Kabupaten/Kota;Kecamatan;Kelurahan/Desa;TIPE
            kode_wilayah = row[1].strip()  # Full code like 11.01.01.2001
            kode_prov = row[2].strip()     # Province code like 11.
            kode_kab = row[3].strip()      # Regency code like 11.01.
            kode_kec = row[4].strip()      # District code like 11.01.01.
            kode_kel = row[5].strip()      # Village code like 11.01.01.2001
            provinsi = row[6].strip()      # Province name
            kabupaten = row[7].strip()     # Regency name
            kecamatan = row[8].strip()     # District name
            kelurahan = row[9].strip()     # Village name
            tipe = row[10].strip() if len(row) > 10 else ""  # Village type

            # Clean codes by removing dots and trailing zeros
            prov_id = kode_prov.replace('.', '')
            reg_id = (kode_prov + kode_kab).replace('.', '')  # Combine prov and kab
            dist_id = (kode_prov + kode_kab + kode_kec).replace('.', '')  # Combine prov, kab, kec
            vill_id = (kode_prov + kode_kab + kode_kec + kode_kel).replace('.', '')  # Combine all

            count += 1

            # Add province if not already added
            if prov_id not in [p['id'] for p in provinces]:
                provinces.append({"id": prov_id, "name": provinsi.upper()})

            # Add regency if not already added
            if reg_id not in [r['id'] for r in regencies.get(prov_id, [])]:
                if prov_id not in regencies:
                    regencies[prov_id] = []
                regencies[prov_id].append({
                    "id": reg_id,
                    "province_id": prov_id,
                    "name": kabupaten.upper()
                })

            # Add district if not already added
            if dist_id not in [d['id'] for d in districts.get(reg_id, [])]:
                if reg_id not in districts:
                    districts[reg_id] = []
                districts[reg_id].append({
                    "id": dist_id,
                    "regency_id": reg_id,
                    "name": kecamatan.upper()
                })

            # Add village if not already added
            if vill_id not in [v['id'] for v in villages.get(dist_id, [])]:
                if dist_id not in villages:
                    villages[dist_id] = []
                villages[dist_id].append({
                    "id": vill_id,
                    "district_id": dist_id,
                    "name": kelurahan.upper()
                })

    print(f"Parsed {count} entries.")

    # Save provinces.json
    provinces_file = os.path.join(output_dir, 'provinces.json')
    with open(provinces_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(provinces, key=lambda x: x['id']), f, ensure_ascii=False, indent=2)
    print(f"Saved {provinces_file}")

    # Save regencies files
    for prov_id, data in regencies.items():
        reg_file = os.path.join(output_dir, 'regencies', f"{prov_id}.json")
        with open(reg_file, 'w', encoding='utf-8') as f:
            json.dump(sorted(data, key=lambda x: x['id']), f, ensure_ascii=False, indent=2)
        print(f"Saved {reg_file}")

    # Save districts files
    for reg_id, data in districts.items():
        dist_file = os.path.join(output_dir, 'districts', f"{reg_id}.json")
        with open(dist_file, 'w', encoding='utf-8') as f:
            json.dump(sorted(data, key=lambda x: x['id']), f, ensure_ascii=False, indent=2)
        print(f"Saved {dist_file}")

    # Save villages files
    for dist_id, data in villages.items():
        vill_file = os.path.join(output_dir, 'villages', f"{dist_id}.json")
        with open(vill_file, 'w', encoding='utf-8') as f:
            json.dump(sorted(data, key=lambda x: x['id']), f, ensure_ascii=False, indent=2)
        print(f"Saved {vill_file}")

    print(f"Success! API generated/updated in {output_dir}/")

if __name__ == "__main__":
    generate_api_from_csv()