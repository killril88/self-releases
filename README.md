# Self Releases

Infrastructure-as-code snapshots and operational documentation for safe application releases.

## Projects

| Project | Purpose |
|---|---|
| [`zb-front`](./zb-front/) | Zhilibyli Next.js safe self-deploy with candidate validation, atomic symlink promotion, rollback and three production instances |

## Security

This repository intentionally excludes:

- `.env.local` and all application secrets;
- SSH private keys and deploy keys;
- TLS private keys and certificates;
- built releases, dependencies and Node.js binaries;
- runtime symlinks and server backups.

Only templates, service configuration, scripts and documentation are versioned.

## Workflow

```text
GitHub master
    ↓
make release
    ↓
isolated releases/<timestamp>-<commit>
    ↓
candidate :3010 + health checks
    ↓
make promote
    ↓
current → three Node.js instances → Nginx
```
