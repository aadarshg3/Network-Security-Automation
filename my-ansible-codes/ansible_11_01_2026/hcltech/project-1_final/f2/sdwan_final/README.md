# SD-WAN Zscaler Automation

UC1 (Tracker + NAT), UC2 (SIG Tunnel), UC3 (Service VPN + BGP)

---

## Project Structure

```
sdwan_pkg/
    main.py
    requirements.txt
    configs/
        newvalues.xlsx        <- Customer fills this - all IDs and variables here
    templates/
        variables.j2          <- Jinja2 template rendered per UC for variable injection
    src/
        excel_loader.py       <- Reads all 7 sheets from newvalues.xlsx
        vmanage_client.py     <- vManage REST session, login, CSRF, rollback
        state.py              <- Idempotency tracker (sdwan_state.json)
        backup.py             <- Template snapshot before each UC
        diff_report.py        <- Before/After diff + colored Excel report
        uc1_tracker.py        <- UC1: Tracker + NAT
        uc2_sig.py            <- UC2: Zscaler SIG Tunnel
        uc3_service_vpn.py    <- UC3: PEPguest/PEPiNET/Corporate VPN + BGP
    outputs/                  <- Auto-created: before/after configs, diff, Excel
    backups/                  <- Auto-created: template JSON snapshots
    logs/                     <- Auto-created: timestamped run logs
    sdwan_state.json          <- Auto-created: records which UCs have been deployed
```

---

## Setup

```bash
pip install -r requirements.txt
```

---

## How to Fill the Excel

Open `configs/newvalues.xlsx` and fill all yellow cells.

| Sheet       | What to Fill |
|-------------|-------------|
| connection  | vManage host URL and username |
| uc1_ids     | DEVICE_TEMPLATE_ID, DEVICE_UUID, TRACKER_TEMPLATE_ID, NAT_TEMPLATE_ID |
| uc1_vars    | /0/0/vpn-instance/tracker-src-ip value |
| uc2_ids     | DEVICE_TEMPLATE_ID, DEVICE_UUID, SIG_TEMPLATE_ID, CISCO_SIG_CRED |
| uc2_vars    | All GRE tunnel variable key/value pairs |
| uc3_ids     | All 9 template IDs for VPN10/VPN20/VPN30/Subifs/BGP |
| uc3_vars    | All interface names, IP addresses, BGP values |

Password is never stored in the Excel. Enter at runtime or set environment variable.

---

## Run

```bash
# Run a single use case
python3 main.py --uc 1
python3 main.py --uc 2
python3 main.py --uc 3

# Run all three in sequence
python3 main.py --uc 1 2 3

# Preview diff only - no deploy
python3 main.py --uc 3 --dry-run

# Check what has already been deployed
python3 main.py --uc 1 --status

# Force re-run even if already deployed
python3 main.py --uc 3 --force

# Set password via environment variable
export VMANAGE_PASSWORD="yourpassword"
python3 main.py --uc 3
```

---

## Idempotency

After a successful deploy, the UC is recorded in `sdwan_state.json`:

```json
{
  "uc3": {
    "status": "deployed",
    "template_id": "b4a36a7a-...",
    "device_uuid": "C8K-73E89...",
    "deployed_at": "2026-03-11 10:22:33"
  }
}
```

On the next run, the UC prints `ALREADY DEPLOYED` and exits immediately without making any changes. Use `--force` to override.

---

## Rollback

On any deploy failure or timeout, the script automatically:

1. Loads the backup JSON saved before the change
2. PUTs it back to vManage
3. Prints `ROLLBACK SUCCESSFUL`

Rollback is triggered on: deploy API error, device failure during push, or 180s timeout.

---

## Outputs per Run

| File | Description |
|------|-------------|
| `outputs/TIMESTAMP_pre.txt`         | Router config before change |
| `outputs/TIMESTAMP_post.txt`        | Router config after change |
| `outputs/TIMESTAMP_diff.txt`        | Unified diff |
| `outputs/TIMESTAMP_diff_report.xlsx`| Color-coded Excel (red=removed, green=added) |
| `backups/TIMESTAMP_ucN_before.json` | Template JSON snapshot for rollback |
| `logs/TIMESTAMP_sdwan.log`          | Full timestamped log |
| `sdwan_state.json`                  | Deployment state record |
