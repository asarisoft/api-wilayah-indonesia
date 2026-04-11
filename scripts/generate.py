import os
import json
import re

def generate_api():
    sql_file = 'wilayah.sql'
    output_dir = 'apiv2'  # Changed from api/v2 to apiv2
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for sub in ['regencies', 'districts', 'villages']:
        path = os.path.join(output_dir, sub)
        if not os.path.exists(path):
            os.makedirs(path)

    print(f"Reading {sql_file}...")
    provinces = []
    regencies = {} # prov_id -> list
    districts = {} # reg_id -> list
    villages = {}  # dist_id -> list
    
    # Regex to find ('CODE', 'NAME')
    pattern = re.compile(r"\('([0-9.]+)',\s*'(.+?)'\)")

    count = 0
    with open(sql_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                code, name = match.groups()
                name = name.replace("''", "'")
                
                parts = code.split('.')
                clean_id = code.replace('.', '')
                
                count += 1
                if len(parts) == 1:
                    provinces.append({"id": clean_id, "name": name.upper()})
                elif len(parts) == 2:
                    prov_id = parts[0]
                    if prov_id not in regencies:
                        regencies[prov_id] = []
                    regencies[prov_id].append({"id": clean_id, "province_id": prov_id, "name": name.upper()})
                elif len(parts) == 3:
                    reg_id = "".join(parts[:2])
                    if reg_id not in districts:
                        districts[reg_id] = []
                    districts[reg_id].append({"id": clean_id, "regency_id": reg_id, "name": name.upper()})
                elif len(parts) == 4:
                    dist_id = "".join(parts[:3])
                    if dist_id not in villages:
                        villages[dist_id] = []
                    villages[dist_id].append({"id": clean_id, "district_id": dist_id, "name": name.upper()})

    print(f"Parsed {count} entries.")

    with open(os.path.join(output_dir, 'provinces.json'), 'w', encoding='utf-8') as f:
        json.dump(provinces, f, ensure_ascii=False)

    for prov_id, data in regencies.items():
        with open(os.path.join(output_dir, 'regencies', f"{prov_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    for reg_id, data in districts.items():
        with open(os.path.join(output_dir, 'districts', f"{reg_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    for dist_id, data in villages.items():
        with open(os.path.join(output_dir, 'villages', f"{dist_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    print(f"Success! API generated in {output_dir}/")

if __name__ == "__main__":
    generate_api()
