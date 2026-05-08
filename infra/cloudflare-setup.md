# Cloudflare-Setup — friedrich-anki-dashboard (Phase 4.1a)

Runbook für die Cloudflare-Tunnel + Access-Konfiguration des Robert-Dashboards.
Reuse-Pattern für 4.1b (Jenni) und 4.1c (Friedrich).

## Status (2026-05-08)

- Hostname: `https://robert.parei-stuttgart.de`
- Zone: `parei-stuttgart.de` (Cloudflare-verwaltet)
- Tunnel: `b0480612-40e6-4088-ace5-fe3e0528dc6f` (cloudflared systemd auf VPS)
- Access-App: `friedrich-anki-dashboard-robert` (ID: `e2d4ec48-ab22-4e98-a674-4eb8cefdd222`)
- Service-Token: `friedrich-anki-pipeline-mac` (ID: `e922c50b-041a-402d-8d21-59fdf6721738`)
- IdP: One-time PIN (Cloudflare-default, keine extra Konfig)

## Architektur

```
Browser (iPad/Mac)              Mac-Pipeline
        |                              |
        | Email-OTP                    | CF-Access-Client-Id +
        | (rpa-systems.cf-access)      | CF-Access-Client-Secret +
        |                              | Bearer Pipeline-API-Key
        v                              v
+--------------------------------------------------+
|  Cloudflare Edge: robert.parei-stuttgart.de       |
|  - Policy 1: allow-robert-email (ALLOW)           |
|  - Policy 2: pipeline-mac-bypass (SERVICE AUTH)   |
+--------------------------------------------------+
                       |
                       | Cloudflare Tunnel
                       v
+--------------------------------------------------+
|  VPS openclaw (Strato): cloudflared systemd      |
|  ingress: robert.parei-stuttgart.de              |
|           -> http://127.0.0.1:8000               |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  Docker: friedrich-anki-dashboard (FastAPI)       |
|  bind 127.0.0.1:8000 (nicht public)              |
+--------------------------------------------------+
```

## VPS-Konfiguration

### Tunnel-Ingress (`/etc/cloudflared/config.yml`)

Eintrag vor `- service: http_status:404`:

```yaml
  - hostname: robert.parei-stuttgart.de
    service: http://127.0.0.1:8000
```

Reload:

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared
```

> Anmerkung: cloudflared unterstützt kein `reload`, nur `restart`.

### DNS-Record (Cloudflare-managed)

Per CLI angelegt — cert.pem ist für `parei-stuttgart.de`-Zone:

```bash
sudo TUNNEL_ORIGIN_CERT=/home/openclaw/.cloudflared/cert.pem \
  cloudflared tunnel route dns b0480612-40e6-4088-ace5-fe3e0528dc6f robert.parei-stuttgart.de
```

Resultat: CNAME `robert` → `b0480612-40e6-4088-ace5-fe3e0528dc6f.cfargotunnel.com` (proxied).

### Container-Deployment

```bash
cd ~/friedrich-anki-dashboard
# .env mit Secrets (chmod 600) — siehe .env.example
# docker-compose.override.yml bindet Port nur an 127.0.0.1
docker compose --env-file .env up -d --build
```

`docker-compose.override.yml`:

```yaml
services:
  dashboard:
    ports: !override
      - "127.0.0.1:8000:8000"
```

Healthcheck: `curl http://127.0.0.1:8000/healthz` → `{"status":"ok"}`.

## Cloudflare Access Application

**Zugriffssteuerungen → Anwendungen → Selbst gehostet und privat**

- Name: `friedrich-anki-dashboard-robert`
- Hostname: `robert.parei-stuttgart.de` (Subdomain `robert` + Domäne `parei-stuttgart.de`)
- Sitzungsdauer: 1 Monat
- 2 Policies (siehe unten)

### Policy 1: `allow-robert-email`

- Aktion: Erlauben (ALLOW)
- Selektor: E-Mails (exakter Match, nicht „mit der Endung")
- Wert: `robert.parei@parei.eu`

### Policy 2: `pipeline-mac-bypass`

- Aktion: Service-Authentifizierung (SERVICE AUTH)
- Selektor: Service Token
- Wert: `friedrich-anki-pipeline-mac`

> CF Access wertet Bypass + Service-Auth zuerst aus, danach normale Allow/Deny.

## Service-Token

**Zugriffssteuerungen → Dienstanmeldeinformationen**

Token-Werte werden **nur einmal** beim Erstellen angezeigt. Pipeline-Konfig:

- Header `CF-Access-Client-Id: <client-id>.access`
- Header `CF-Access-Client-Secret: <secret>`

Lokal gespeichert in `friedrich-anki-dashboard/.env.prod-pipeline` (gitignored).

## Mac-Pipeline-Konfiguration

`~/Library/LaunchAgents/eu.parei.dashboard.nightly.plist` mit ENV:

| Key | Value |
|---|---|
| `DASHBOARD_API_URL` | `https://robert.parei-stuttgart.de` |
| `PIPELINE_API_KEY` | aus VPS `~/friedrich-anki-dashboard/.env` |
| `CF_ACCESS_CLIENT_ID` | aus CF-Service-Token (Header: …`.access`) |
| `CF_ACCESS_CLIENT_SECRET` | aus CF-Service-Token |
| `ANKI_CONNECT_URL` | `http://127.0.0.1:8765` |
| `TIMEZONE` | `Europe/Berlin` |

Install:

```bash
launchctl load ~/Library/LaunchAgents/eu.parei.dashboard.nightly.plist
launchctl start eu.parei.dashboard.nightly  # manueller Test
cat /tmp/dashboard-pipeline.out.log
```

Post-Review-Hook (`friedrich-schule/scripts/dashboard-post-review-hook.sh`) liest dieselben ENV-Vars
oder bekommt sie vom Caller injiziert.

## Verifikation

End-to-End-Tests nach Setup:

```bash
# 1. Public ohne Auth → 302 zu Access-Login
curl -fsS -I https://robert.parei-stuttgart.de/

# 2. Mit Service-Token → 200
curl -fsS -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET" \
        https://robert.parei-stuttgart.de/healthz

# 3. Pipeline-Push end-to-end
cd ~/Projekte/Claude_Code_Workspace/friedrich-anki-dashboard
set -a && source .env.prod-pipeline && set +a
uv run python -m dashboard.pipeline.cli push --user robert --subject englisch

# 4. Browser: https://robert.parei-stuttgart.de → Email-OTP-Login mit robert.parei@parei.eu
```

## Reuse für 4.1b/c

Pro neuem User (Jenni → 4.1b, Friedrich → 4.1c):

1. **Container-Seite (gemeinsam):** Brawler-Slot anlegen via Migration; bestehender Container reicht aus.
2. **Tunnel-Ingress:** zweiter Hostname-Eintrag (z.B. `jenni.parei-stuttgart.de` → selber Container).
3. **DNS:** `cloudflared tunnel route dns <tunnel-uuid> jenni.parei-stuttgart.de`.
4. **Access-App:** neue App `friedrich-anki-dashboard-jenni` mit eigenem Hostname + Policy `allow-jenni-email`.
5. **Pipeline:** zweiter Service-Token `friedrich-anki-pipeline-mac-jenni` (oder shared bleibt — Multi-User-DB im Backend erlaubt User-Switch über Pipeline-Argumente).

## Known Issues / Quirks

- IdP One-time PIN Mails kommen von `noreply@notify.cloudflare.com` — bei Mail-Filtern Spam-Ordner prüfen
- React-Dropdowns im CF-Dashboard brauchen `focus + type + ArrowDown + Enter`; reines `form_input` setzt DOM-Wert, feuert aber kein React-Event
- Erste Policy beim App-Anlegen wurde durch UI-Bug **nicht** persistiert — Policies nach Speichern via App-Detail-View prüfen
- `cloudflared tunnel route dns` braucht passendes cert.pem — bei falscher Zone wird CNAME als `host.zone` statt nur `host` angelegt
