# Network Automation Internship Assignment - Submission

## Contents
- `router_a.txt` - Sample Cisco configuration (provided in assignment, Page 4)
- `router_b.txt` - Sample Huawei configuration (provided in assignment, Page 5)
- `Task 01.py` - Task 01 script: reads the configs, detects vendor, extracts interface data, writes `output.xlsx`
- `output.xlsx` - Task 01 generated output
- `Task 02.md` - Task 02: prompt engineering deliverable

## How to run Task 01

**Requirements:** Python 3, `pandas`, `openpyxl`

```bash
pip install pandas openpyxl
python extract_config.py
```

This reads `router_a.txt` and `router_b.txt` (must be in the same folder as
the script) and produces `output.xlsx` with four columns:
`Main Interface | Description | VRF | Vendor`.

## Vendor detection logic

The script scores each config file against a set of vendor-specific CLI
signatures rather than relying on a single keyword, so it stays robust even
if one line is missing or reordered:

**Cisco signals:**
- Contains `show running-config`
- Contains `vrf forwarding`
- Contains `encapsulation dot1Q`
- Command prompt ends in `#` (e.g. `CISCO-PE01#`)

**Huawei signals:**
- Contains `display current-configuration`
- Contains `ip binding vpn-instance`
- Contains `vlan-type dot1q`
- Command prompt is wrapped in `<>` or `[]` (e.g. `<HUAWEI-PE02>`)

Whichever vendor has more matching signals is chosen. This avoids false
positives from a single ambiguous line.

## Parsing logic

The script splits each config on `interface <name>` blocks, then scans each
block line-by-line until the closing `!`, pulling out:
- The interface name (from the `interface` line itself)
- The `description` line
- The VRF binding (`vrf forwarding` for Cisco, `ip binding vpn-instance` for Huawei)

## Assumptions made

1. Each sub-interface block contains at most one `description` line and one
   VRF-binding line - the last one found is what's recorded (matches the
   sample configs given).
2. A block is only written to the output if a valid interface name was found;
   missing description/VRF values are left as empty strings rather than
   crashing the script.
3. Unreadable or missing files are skipped with a warning printed to the
   console, and the script continues processing the remaining files.
4. Input files are plain text `show running-config` / `display
   current-configuration` style dumps, as given in the assignment appendix.

## Sample output

| Main Interface | Description | VRF | Vendor |
|---|---|---|---|
| GigabitEthernet0/0/0.100 | CUST_ALPHA_SERVICE_455023849 | CUSTOMER_ALPHA | Cisco |
| GigabitEthernet0/0/0.200 | CUST_BETA_SERVICE_452397680 | CUSTOMER_BETA | Cisco |
| GigabitEthernet0/0/1.300 | CUST_GAMMA_SERVICE_298765432 | CUSTOMER_GAMMA | Huawei |
| GigabitEthernet0/0/1.400 | CUST_DELTA_SERVICE_099876543 | CUSTOMER_DELTA | Huawei |
