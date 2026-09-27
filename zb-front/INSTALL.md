# ZB Front · Installation Map

This repository is a safe copy of the deployment infrastructure. It is not a one-command installer.

## Server paths

| Repository file | Server destination | Owner/mode |
|---|---|---|
| `Makefile` | `/var/www/zhilibyli/frontend_releases/Makefile` | `root:root 0644` |
| `README.md` | `/var/www/zhilibyli/frontend_releases/README.md` | `root:root 0644` |
| `config/nginx/zhilibyli.ru.conf` | `/etc/nginx/sites-enabled/zhilibyli.ru` | `root:root 0644` |
| `config/supervisor/zb_node_front_release.conf` | `/etc/supervisor/conf.d/zb_node_front_release.conf` | `root:root 0644` |
| `scripts/zb-front-supervisor` | `/usr/local/sbin/zb-front-supervisor` | `root:root 0755` |
| `scripts/next-rss-health.py` | `/usr/local/libexec/next-rss-health.py` | `root:root 0755` |
| `systemd/next-rss-health.service` | `/etc/systemd/system/next-rss-health.service` | `root:root 0644` |
| `sudoers/zb-front-deploy` | `/etc/sudoers.d/zb-front-deploy` | `root:root 0440` |

The Nginx and Supervisor templates are also stored on the server in:

```text
/var/www/zhilibyli/frontend_releases/config/
```

## Runtime data excluded from Git

```text
frontend_releases/shared/.env.local
frontend_releases/shared/node-v24.14.0/
frontend_releases/releases/
frontend_releases/current
frontend_releases/candidate
frontend_releases/previous
```

## Validation after an intentional installation

```bash
sudo visudo -cf /etc/sudoers.d/zb-front-deploy
sudo nginx -t
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl daemon-reload
sudo systemctl enable --now next-rss-health.service
```

Run operational commands as `zhilibyli`:

```bash
cd /var/www/zhilibyli/frontend_releases
make status
make release
make promote
```

Do not install these files blindly on another project. Adapt repository URL, user, paths, ports, build commands and health checks first.
