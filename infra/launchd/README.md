# launchd — nightly + post-review pipeline triggers

## eu.parei.dashboard.nightly.plist

Runs `dashboard-pipeline push` once per day at 23:00 local time. Reads
review counts from AnkiConnect (port 8765) and pushes them to the
dashboard backend.

**Install:**

```bash
cp infra/launchd/eu.parei.dashboard.nightly.plist ~/Library/LaunchAgents/
# Edit the copy — replace REPLACE_WITH_PROD_KEY with the real PIPELINE_API_KEY
launchctl load ~/Library/LaunchAgents/eu.parei.dashboard.nightly.plist
```

**Verify:**

```bash
launchctl list | grep eu.parei.dashboard
# Manual run (skip schedule):
launchctl start eu.parei.dashboard.nightly
tail -f /tmp/dashboard-pipeline.out.log /tmp/dashboard-pipeline.err.log
```

**Uninstall:**

```bash
launchctl unload ~/Library/LaunchAgents/eu.parei.dashboard.nightly.plist
rm ~/Library/LaunchAgents/eu.parei.dashboard.nightly.plist
```

## Post-Review-Hook

After every `python -m tools.anki_orchestrator` run in the
`friedrich-schule` repo, a separate hook calls
`dashboard-pipeline push` so the dashboard reflects the new reviews
within seconds (instead of waiting for the nightly cron).

See `friedrich-schule/scripts/dashboard-post-review-hook.sh`.
