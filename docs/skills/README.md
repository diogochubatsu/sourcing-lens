# 1688-Intel Agent Skills

This directory contains skill definitions for the Hermes Agent profiles that work on the 1688-intel project.

## Available Skills

### Project-Wide
- [1688-intel-project](1688-intel-project.md) — Project overview, architecture, conventions, data pipeline

### Profile-Specific
- [1688-intel-devops](1688-intel-devops.md) — Infrastructure, deployment, GCP, Docker, CI/CD
- [1688-intel-frontend](1688-intel-frontend.md) — Frontend code, React, Next.js, UI/UX, design system
- [1688-intel-translator](1688-intel-translator.md) — Translation, localization (PT/EN/ZH)

## Profile Roles

| Profile | Responsibility | Workspace |
|---------|---------------|-----------|
| `orchestrator` | Decomposes work, routes to specialists via Kanban | — |
| `1688devops` | Infrastructure, deployment, GCP, Docker, CI/CD | `/mnt/ssd/1688-intel` |
| `1688front` | Frontend code, React, Next.js, UI/UX | `/mnt/ssd/1688-intel` |
| `1688-scraping-agent` | Web scraping, data extraction, 1688.com | `/mnt/ssd/1688-intel` |
| `1688-translator` | Translation, localization (PT/EN/ZH) | `scratch` |

## Usage

### Via Orchestrator (Recommended)
```bash
# Start orchestrator
hermes chat --profile orchestrator

# Give it a goal
> "Deploy the latest changes to Cloud Run and verify the image pipeline"
```

### Direct to Specialist
```bash
# DevOps task
hermes chat --profile 1688devops -q "Check Cloud Run deployment status"

# Frontend task
hermes chat --profile 1688front -q "Add a new chart to the dashboard"
```

### Via Kanban Board
```bash
# Create task for orchestrator to decompose
hermes kanban create "Deploy and verify infrastructure" --assignee orchestrator --body "Check all infrastructure components and deploy latest changes"

# Or create directly for specialist
hermes kanban create "Fix GCS bucket permissions" --assignee 1688devops
```

## Syncing Skills

Skills are stored in each profile's `skills/` directory. To sync:
```bash
# Copy to profile
cp docs/skills/1688-intel-devops.md ~/.hermes/profiles/1688devops/skills/devops/1688-intel-devops/SKILL.md

# Or use hermes skills install
hermes skills install /path/to/skill --profile profile-name
```
