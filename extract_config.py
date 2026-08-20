"""
Task 01 - Network Configuration Data Extraction
-------------------------------------------------
Reads Cisco and Huawei router configuration text files, detects the vendor
of each file automatically, extracts sub-interface details (interface name,
description, VRF), and writes everything into a single Excel (.xlsx) file.

Usage:
    python extract_config.py

Input files (must be in the same folder as this script, or edit INPUT_FILES
below to point elsewhere):
    router_a.txt   -> Cisco sample config
    router_b.txt   -> Huawei sample config

Output:
    output.xlsx    -> Main Interface | Description | VRF | Vendor
"""

import re
import sys
import pandas as pd

INPUT_FILES = ["router_a.txt", "router_b.txt"]
OUTPUT_FILE = "output.xlsx"


def detect_vendor(config_text: str) -> str:
    """
    Determine whether a configuration belongs to a Cisco or Huawei device.

    Detection is based on vendor-specific CLI signatures found in the
    'show running-config' style output:
      - Cisco:  uses 'vrf forwarding', 'encapsulation dot1Q', ends with 'end',
                prompt ends in '#' (e.g. CISCO-PE01#)
      - Huawei: uses 'ip binding vpn-instance', 'vlan-type dot1q',
                ends with 'return', prompt is wrapped in <> or []
                (e.g. <HUAWEI-PE02>), and uses 'display current-configuration'
    """
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
    """
    Extract (Main Interface, Description, VRF) for every sub-interface block
    found in the configuration text. Works for both Cisco and Huawei syntax.
    Malformed or incomplete blocks are skipped, not fatal.
    """
    records = []

    # Split the text on lines that start a new "interface <name>" block.
    # This keeps everything belonging to that interface together until the
    # next '!' or 'interface' line.
    interface_blocks = re.split(r"\ninterface\s+", config_text)

    for block in interface_blocks[1:]:  # first chunk is header, skip it
        lines = block.strip().splitlines()
        if not lines:
            continue

        iface_name = lines[0].strip()
        description = ""
        vrf = ""

        for line in lines[1:]:
            line = line.strip()

            # Stop reading this block once we hit the closing '!'
            if line == "!":
                break

            if line.lower().startswith("description"):
                description = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""

            elif line.lower().startswith("vrf forwarding"):  # Cisco
                vrf = line.split(None, 2)[2] if len(line.split(None, 2)) > 2 else ""

            elif line.lower().startswith("ip binding vpn-instance"):  # Huawei
                parts = line.split()
                vrf = parts[-1] if parts else ""

        # Only keep it if we actually found a usable interface name.
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
