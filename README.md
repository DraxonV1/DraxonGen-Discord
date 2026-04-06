# MuskServices DTA

A Discord Token Automation platform built for both workers and private users. Generate at scale and monetize efficiently.

---

## Worker System - $0.02 per EV

Start as a worker and generate immediately. No upfront cost, just your key and a stable setup.

- Earn **$0.02** per successful EV
- Windows, Linux, and macOS supported
- Supports ADB, VPN, Proxy, or no rotation

**Affiliate earnings:**
- Invite other workers using your key
- Earn **$0.003** per EV they generate
- Completely passive once set up

---

## Private System - Credits from $0.02

Full private generation access with your own credit balance.

- Access to 3+ domains by default, with support for custom domains
- No limit on credit top-ups
- Each generation attempt uses **1 credit** regardless of outcome

**Credit pricing:**

| Volume | Price per credit |
|--------|-----------------|
| Any amount | $0.02 |
| 2,000+ | $0.018 |
| 5,000+ | $0.015 |

---

## Affiliate System

Invite sub-workers and earn a cut of everything they generate.

- Earn **$0.003** per EV from each referred worker
- Track your stats and earnings via Discord bot commands
- Activity required every **30 days** to stay active

---

## Key Types

| Format | Access |
|--------|--------|
| `OPT-USER-XXXXX` | Worker mode |
| `PRV-USER-XXXXX` | Private mode (up to 10 HWIDs) |

---

## Setup

### Manual (binary directly)

1. Download the binary for your OS from the latest release
2. Place it alongside `config.json` and `license.key`
3. Insert your key into `license.key`
4. Configure `mode` and `ip_rotation` in `config.json`
5. Run the binary

### Via CLI (muskdta launcher)

```
pip install muskdta
muskdta
```

The launcher detects your OS, downloads the correct binary, installs dependencies, and handles config setup. On every run it checks for updates and validates your environment before launching.

**CLI commands:**

```
muskdta                    launch (update check + config check + start)
muskdta update             force re-download latest binary for your OS
muskdta config             re-run config setup in terminal
muskdta config manual      open config.json in your system editor
muskdta auto-update on     enable automatic update checks on launch
muskdta auto-update off    disable automatic update checks
muskdta discord            open the Discord server
muskdta status             show binary, version, config state, data path
```

---

## config.json reference

```json
{
  "browser": "edge", 
  "mode": "private", 
  "proxy_mode": "http",
  "http_lib": "curl",
  "ip_rotation": "none",
  "delay_between_accs": 0,
  "adb_rotate_every": 2,
  "after_create_timer": 0,
  "check_ratelimit": false,
  "notify": false,
  "notification_icon": ""
}
```

| Key | Values | Description |
|-----|--------|-------------|
| `browser` | `edge` / `brave` | Browser to use |
| `mode` | `worker` / `private` | Account generation mode |
| `ip_rotation` | `none` / `adb` / `vpn` / `proxy` | IP rotation method |
| `adb_rotate_every` | number | Rotate ADB every N accounts |
| `delay_between_accs` | seconds | Delay between each account |
| `after_create_timer` | seconds | Wait after account created |

---

## Notes

- Use a stable IP rotation method for best results
- Monitor your stats via the Discord bot
- Scale earnings by bringing in affiliate workers

---

## Access

Keys are issued via direct contact on Discord.

Message **@draxon.v15** and send `work` or `private` to get started.

**Discord:** [MuskServices](https://discord.gg/dpk45Be2e3)
