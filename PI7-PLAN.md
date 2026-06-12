/usr/bin/bash: warning: setlocale: LC_ALL: cannot change locale (pt_BR.UTF-8)
# PI7-PLAN.md — Server Resiliency & ML Unblock

## Goal
Make the dashboard accessible 24/7 and unblock Mercado Livre data for beach towel clips + matching expansion.

## Sprint Tasks

### Sprint 7.1: Server Resiliency (HIGH)
- [ ] Create systemd service for uvicorn on port 8080 (auto-restart)
- [ ] Create systemd service for cloudflared tunnel (auto-restart, saves URL)
- [ ] Verify both survive reboot and process kills

### Sprint 7.2: Unblock ML via Browser (HIGH, BLOCKED)
- [x] Download chromium browser binary (~200MB) ✅ feito
- [x] Test Playwright with ML product pages ❌ bloqueado
- [ ] BLOCKER: ML detecta IP 34.30.146.117 (GCP datacenter) e bloqueia
- [ ] Fix Decodo proxy credentials (407 Auth Required) — OU —
- [ ] Alternative: Scrape ML from a residential IP machine

### Sprint 7.3: Matching Expansion (MEDIUM)
- [ ] Add ML beach towel clips to DB
- [ ] Run matching engine for beach_towel_clip category
- [ ] Add beach_towel_clip brands to matching_v4.py

### Sprint 7.4: Frontend Polish (LOW)
- [ ] Show matches with images side-by-side
- [ ] Show price difference (R$ savings)
- [ ] Add Amazon US price reference column

## Current State (Start of Sprint)
```
Server:   ❌ Dies every 10-15 min (SIGTERM)
URL:      Changes every restart (trycloudflare)
ML:       ❌ Completely blocked (API 403, Decodo 407)
Matches:  10 valid (headphone 5, microfone 4, led_panel 1)
Towel Clips: 21 products, 0 ML, 0 matches
```

## Success Criteria
- [ ] Dashboard stays up for 24h+ without intervention
- [ ] At least 5 ML beach towel clip products in DB
- [ ] At least 2 new cross-platform matches (any category)
- [ ] Tunnel URL doesn't change on server restart (named tunnel)

## Blockers
- sudo access needed for systemd service
- 200MB download for chromium (bandwidth)
