# Local Windows deployment

This directory contains the official Windows x64 binaries for
`xiaohongshu-mcp` v2.5.0.

## Start and stop

From PowerShell:

```powershell
.\start.ps1
.\stop.ps1
```

The service listens only on the local machine:

- MCP: `http://127.0.0.1:18060/mcp`
- Health check: `http://127.0.0.1:18060/health`

Runtime data is kept under `data/`, images under `images/`, and logs under
`logs/`. These directories are intentionally ignored by Git.

## Login

The server exposes a QR-code login tool through MCP. Alternatively, stop the
service and run the interactive login helper:

```powershell
.\login.ps1
```

The first start downloads the project's pinned Chromium build (roughly
140-190 MB). This happens once and can take several minutes.

Do not use the same account in another web login at the same time; the project
documentation warns that doing so can invalidate the saved session.
