# ZB Front · Node.js Logs

## Production processes

| Process | Port | stdout | stderr |
|---|---:|---|---|
| `zb_node_front_release_00` | 3000 | `/var/log/supervisor/node_front-release-00-out.log` | `/var/log/supervisor/node_front-release-00-err.log` |
| `zb_node_front_release_01` | 3001 | `/var/log/supervisor/node_front-release-01-out.log` | `/var/log/supervisor/node_front-release-01-err.log` |
| `zb_node_front_release_02` | 3002 | `/var/log/supervisor/node_front-release-02-out.log` | `/var/log/supervisor/node_front-release-02-err.log` |

Candidate on port `3010`:

```text
/var/log/supervisor/node_front-candidate-out.log
/var/log/supervisor/node_front-candidate-err.log
```

## Follow logs

```bash
sudo tail -F /var/log/supervisor/node_front-release-0{0,1,2}-err.log
```

```bash
sudo tail -F \
  /var/log/nginx/zhilibyli.error.log \
  /var/log/supervisor/node_front-release-0{0,1,2}-err.log
```

## Find important errors

```bash
sudo grep -Ein \
  'error|fatal|exception|heap out of memory|unhandled|ENOMEM|EADDRINUSE' \
  /var/log/supervisor/node_front-release-0{0,1,2}-err.log
```

```bash
sudo grep -E \
  'no live upstreams|connect\(\) failed|upstream timed out' \
  /var/log/nginx/zhilibyli.error.log \
  | tail -n 50
```

## Health checks

```bash
for port in 3000 3001 3002; do
  curl -fsS -o /dev/null \
    -w "port_${port}: HTTP %{http_code} · %{time_total}s\n" \
    -H 'Host: zhilibyli.ru' \
    "http://127.0.0.1:${port}/api/health"
done
```

```bash
curl -fsS https://zhilibyli.ru/api/health
curl -fsS http://127.0.0.1:9107/health
```

## Resources

```bash
ps -eo pid,ppid,pcpu,pmem,rss,etimes,comm --sort=-rss \
  | awk 'NR==1 || /next-server/'
uptime
free -h
```

## Incident checklist

1. Check Supervisor status.
2. Check ports `3000`, `3001`, `3002` and public health.
3. Inspect Nginx upstream errors.
4. Inspect stderr for all three processes.
5. Record CPU, RSS, memory and Redis metrics before restarting anything.
6. Correlate timestamps between Nginx and Node.js logs.
