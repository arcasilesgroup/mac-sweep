# mac-sweep JSON API Reference

All commands support `--json` output. JSON goes to stdout, logs to stderr.

## Common Envelope

Every response includes:

| Field       | Type   | Description                  |
|-------------|--------|------------------------------|
| `version`   | string | API version (currently `2.0.0`) |
| `command`   | string | Command name                 |
| `timestamp` | string | ISO 8601 timestamp           |

## `sweep audit --json`

```json
{
  "version": "2.0.0",
  "command": "audit",
  "timestamp": "2026-02-04T12:00:00",
  "hostname": "MacBook.local",
  "summary": {
    "active": 42,
    "occasional": 8,
    "dormant": 5,
    "unknown": 12,
    "infrastructure": 150,
    "total": 217,
    "total_size_bytes": 25000000000,
    "dormant_size_bytes": 3200000000
  },
  "apps": [
    {
      "name": "Slack",
      "source": "Manual Install",
      "status": "Active",
      "size_bytes": 500000000,
      "last_used": "2026-02-01",
      "description": "Team messaging"
    }
  ],
  "formulas": [
    {
      "name": "hugo",
      "install_type": "explicit",
      "status": "Dormant",
      "description": "Static site generator"
    }
  ],
  "npm_packages": [],
  "pipx_packages": [],
  "pip_packages": [],
  "gem_packages": []
}
```

### App Fields

| Field        | Type    | Description                          |
|--------------|---------|--------------------------------------|
| `name`       | string  | Application name                     |
| `source`     | string  | Installation source                  |
| `status`     | string  | Active, Occasional, Dormant, Unknown, Infrastructure |
| `size_bytes` | integer | Application size in bytes (0 if unknown) |
| `last_used`  | string  | Last used date (YYYY-MM-DD or empty) |
| `description`| string  | Human-readable description           |

### Formula Fields

| Field          | Type   | Description                    |
|----------------|--------|--------------------------------|
| `name`         | string | Formula name                   |
| `install_type` | string | `explicit` or `dependency`     |
| `status`       | string | Status classification          |
| `description`  | string | Human-readable description     |

### Package Fields (npm, pipx, pip, gem)

| Field         | Type   | Description              |
|---------------|--------|--------------------------|
| `name`        | string | Package name             |
| `version`     | string | Installed version        |
| `status`      | string | Status classification    |
| `description` | string | Human-readable description |

---

## `sweep cache --json`

### Analyze mode (default)

```json
{
  "version": "2.0.0",
  "command": "cache",
  "timestamp": "2026-02-04T12:00:00",
  "mode": "analyze",
  "caches": [
    {
      "module": "homebrew",
      "label": "Homebrew Cache",
      "available": true,
      "total_bytes": 2500000000,
      "total_human": "2.33 GB",
      "items": 47
    }
  ],
  "total_bytes": 8000000000,
  "total_human": "7.45 GB"
}
```

### Clean mode (`--clean` or `--dry-run`)

Additional fields:

```json
{
  "mode": "dry-run",
  "cleaned": [
    {
      "module": "homebrew",
      "label": "Homebrew Cache",
      "freed_bytes": 1200000000,
      "freed_human": "1.12 GB",
      "items_removed": 23
    }
  ]
}
```

### Cache Entry Fields

| Field         | Type    | Description                     |
|---------------|---------|---------------------------------|
| `module`      | string  | Module identifier               |
| `label`       | string  | Human-readable label            |
| `available`   | boolean | Whether the tool is installed   |
| `total_bytes` | integer | Total cache size in bytes       |
| `total_human` | string  | Human-readable size             |
| `items`       | integer | Number of cached items          |

---

## `sweep status --json`

```json
{
  "version": "2.0.0",
  "command": "status",
  "timestamp": "2026-02-04T12:00:00",
  "has_audit": true,
  "audit_age_hours": 2.5,
  "counts": {
    "gui_apps": 67,
    "formulas": 120,
    "npm": 12,
    "dormant": 5
  },
  "disk": {
    "total_app_bytes": 25000000000,
    "dormant_bytes": 3200000000,
    "cache_bytes": 8000000000,
    "reclaimable_bytes": 11200000000
  }
}
```

---

## `sweep doctor --json`

```json
{
  "version": "2.0.0",
  "command": "doctor",
  "timestamp": "2026-02-04T12:00:00",
  "diagnostics": [
    {
      "check": "disk_pressure",
      "status": "ok",
      "message": "Disk space OK (45 GB free)",
      "details": []
    },
    {
      "check": "broken_symlinks",
      "status": "warning",
      "message": "3 broken symlinks in /opt/homebrew/bin",
      "details": ["/opt/homebrew/bin/foo", "/opt/homebrew/bin/bar"]
    }
  ]
}
```

### Diagnostic Fields

| Field     | Type     | Description                          |
|-----------|----------|--------------------------------------|
| `check`   | string   | Check identifier                     |
| `status`  | string   | `ok`, `warning`, or `error`          |
| `message` | string   | Human-readable summary               |
| `details` | string[] | Additional details (may be empty)    |

---

## `sweep cleanup --json`

```json
{
  "version": "2.0.0",
  "command": "cleanup",
  "timestamp": "2026-02-04T12:00:00",
  "total": 5,
  "candidates": [
    {
      "name": "hugo",
      "category": "Homebrew Formula",
      "description": "Static site generator",
      "status": "Dormant",
      "removal_cmd": "brew uninstall hugo"
    }
  ]
}
```

### Candidate Fields

| Field          | Type   | Description                    |
|----------------|--------|--------------------------------|
| `name`         | string | Item name                      |
| `category`     | string | Category label                 |
| `description`  | string | Human-readable description     |
| `status`       | string | Status classification          |
| `removal_cmd`  | string | Command to remove the item     |

---

## Exit Codes

| Code | Meaning        |
|------|----------------|
| `0`  | Success        |
| `1`  | Error          |
| `2`  | Nothing to do  |
