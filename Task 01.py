"""
Task 01 - Network Configuration Data Extraction
"""

import re
import sys
import pandas as pd

INPUT_FILES = ["router_a.txt", "router_b.txt"]
OUTPUT_FILE = "output.xlsx"


def detect_vendor(config_text: str) -> str:

    text = config_text.lower()

    cisco_signals = [
        "show running-config" in text,
        "vrf forwarding" in text,
        "encapsulation dot1q" in text,
        re.search(r"^\S+#", config_text, re.MULTILINE) is not None,
    ]

    huawei_signals = [
        "display current-configuration" in text,
        "ip binding vpn-instance" in text,
        "vlan-type dot1q" in text,
        re.search(r"^[<\[]\S+[>\]]", config_text, re.MULTILINE) is not None,
    ]

    cisco_score = sum(bool(s) for s in cisco_signals)
    huawei_score = sum(bool(s) for s in huawei_signals)

    if cisco_score > huawei_score:
        return "Cisco"
    elif huawei_score > cisco_score:
        return "Huawei"
    else:
        return "Unknown"


def parse_config(config_text: str, vendor: str) -> list[dict]:

    records = []

    interface_blocks = re.split(r"\ninterface\s+", config_text)

    for block in interface_blocks[1:]: 
        lines = block.strip().splitlines()
        if not lines:
            continue

        iface_name = lines[0].strip()
        description = ""
        vrf = ""

        for line in lines[1:]:
            line = line.strip()
 
            if line == "!":
                break

            if line.lower().startswith("description"):
                description = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""

            elif line.lower().startswith("vrf forwarding"):  
                vrf = line.split(None, 2)[2] if len(line.split(None, 2)) > 2 else ""

            elif line.lower().startswith("ip binding vpn-instance"):  
                parts = line.split()
                vrf = parts[-1] if parts else ""

        if iface_name:
            records.append({
                "Main Interface": iface_name,
                "Description": description,
                "VRF": vrf,
                "Vendor": vendor,
            })

    return records


def main():
    all_records = []

    for filepath in INPUT_FILES:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                config_text = f.read()
        except FileNotFoundError:
            print(f"[WARNING] File not found, skipping: {filepath}")
            continue
        except Exception as e:
            print(f"[WARNING] Could not read {filepath}: {e}")
            continue

        if not config_text.strip():
            print(f"[WARNING] File is empty, skipping: {filepath}")
            continue

        vendor = detect_vendor(config_text)
        records = parse_config(config_text, vendor)

        if not records:
            print(f"[WARNING] No interfaces extracted from {filepath}")
        else:
            print(f"[OK] {filepath}: detected vendor = {vendor}, "
                  f"{len(records)} interface(s) extracted")

        all_records.extend(records)

    if not all_records:
        print("[ERROR] No data extracted from any file. Exiting without writing Excel.")
        sys.exit(1)

    df = pd.DataFrame(all_records, columns=["Main Interface", "Description", "VRF", "Vendor"])
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nDone. Wrote {len(df)} row(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
