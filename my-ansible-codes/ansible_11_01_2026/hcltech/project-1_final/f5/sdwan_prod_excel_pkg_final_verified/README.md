# SD-WAN Customer Package

Excel-driven Cisco SD-WAN / vManage automation for:

- `uc1` Use Case 1: Tracker Enable
- `uc2` Use Case 2: SIG Template
- `uc3` Use Case 3: Create a Firewall Transit Interface
- `uc4` Use Case 4: Create a Firewall Transit Interface

## What Changed

- Preserved the Engineer-1 style execution flow: login, fetch template, modify template, fetch inputs, attach, deploy, poll.
- Switched the package to customer Excel input using `configs/sdwan_config.xlsx`.
- Corrected UC2 so SIG is attached under VPN 0 and SIG credentials are attached at top level.
- Corrected UC3 so the VPN 0 no-IP template is attached to the actual VPN 0 feature block, not just the first VPN block.

## Files

- `main.py`: CLI entry point
- `configs/sdwan_config.xlsx`: customer input workbook
- `configs/sdwan_config_lab.xlsx`: lab-prefilled workbook for the shared vManage lab
- `src/services/excel_config_loader.py`: Excel parser
- `src/usecases/`: UC1-UC4 implementation
- `tests/`: unit tests

## Install

```powershell
pip install -r requirements.txt
```

## Usage

```bash
export VMANAGE_PASSWORD="your_password"
python3 main.py --run-all --dry-run
python3 main.py --uc 1 2
python3 main.py --uc 3 4
python3 main.py --status
python3 main.py --run-all --dry-run --vmanage-host https://172.17.152.161 --username admin
python3 main.py --uc 2 --dry-run --excel configs/sdwan_config_lab.xlsx
```

## Excel Notes

- Fill `configs/sdwan_config.xlsx`
- For the shared lab, start with `configs/sdwan_config_lab.xlsx`
- `connection` sheet: vManage host and username
- `UC1 IDs`, `UC2 IDs`, `UC3 IDs`: template IDs and device identifiers
- `UC1 Variables`, `UC2 Variables`, `UC3 Variables`, `UC4 Variables`: variable values

## Live Validation Status

This package was prepared in the local workspace, but live validation against `172.17.152.161` is still blocked from this environment because the TLS handshake could not be completed here and the jump server access details were not available in this session.
