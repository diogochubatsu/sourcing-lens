---
name: 1688-intel-devops
description: DevOps procedures for the 1688-intel platform — Cloud Run deployment, GCS management, Cloud SQL, secrets, and CI/CD workflows.
version: 1.0.0
metadata:
  hermes:
    tags: [1688, gcp, cloud-run, devops, deployment]
---

# 1688-Intel DevOps Skill

Infrastructure and deployment procedures for the 1688-intel platform.

## Infrastructure Overview

| Component | Name | Details |
|-----------|------|---------|
| Cloud Run | intel-dashboard | Port 3002, 1Gi memory, 1 CPU, max 2 instances |
| Cloud SQL | intel-postgres | PostgreSQL, database: intel_data |
| GCS Bucket | intel-dashboard-images-... | Image cache (SHA256 hash keys), 2.51 GB |
| Secrets | intel-postgres-password, api-key | Secret Manager |
| Decodo | Site Unblocker | unblock.decodo.com:60000 |

## Deployment Procedures

### Deploy Cloud Run Service
```bash
# From repo root
gcloud run services replace manifests/cloudrun-service.yaml --region us-central1 --platform managed

# Check deployment status
gcloud run services describe intel-dashboard --region us-central1 --format="value(status.url)"
```

### Manual Docker Build & Push
```bash
# Build
docker build -t us-central1-docker.pkg.dev/leafy-flash-489319-c7/intel-app/intel-dashboard:latest .

# Push
docker push us-central1-docker.pkg.dev/leafy-flash-489319-c7/intel-app/intel-dashboard:latest

# Deploy
gcloud run services update intel-dashboard --region us-central1 --image us-central1-docker.pkg.dev/leafy-flash-489319-c7/intel-app/intel-dashboard:latest
```

### GitHub Actions Workflows
- `deploy.yml` — Main deployment (triggers on push to master)
- `ci.yml` — TypeScript check, tests, lint
- `deploy-gcs-fix.yml` — GCS bucket IAM repair

## GCS Bucket Management

### Check Bucket Status
```bash
gsutil ls -L -b gs://intel-dashboard-images-leafy-flash-489319-c7/
```

### Fix IAM Permissions
```bash
# Grant public read
gsutil iam ch allUsers:objectViewer gs://intel-dashboard-images-leafy-flash-489319-c7

# Grant Cloud Run SA
gsutil iam ch serviceAccount:github-deployer@leafy-flash-489319-c7.iam.gserviceaccount.com:objectAdmin gs://intel-dashboard-images-leafy-flash-489319-c7
```

## Cloud SQL

### Connect via Cloud SQL Proxy
```bash
cloud-sql-proxy --port 5432 leafy-flash-489319-c7:us-central1:intel-postgres
```

### Check Database
```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d intel_data -c "\dt"
```

## Secrets Management

### List Secrets
```bash
gcloud secrets list --project=leafy-flash-489319-c7
```

### Update Secret
```bash
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Grant Access to Cloud Run SA
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:github-deployer@leafy-flash-489319-c7.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Health Checks

### Cloud Run Health
```bash
curl -s https://intel-dashboard-4766585081.us-central1.run.app/health
curl -s https://intel-dashboard-4766585081.us-central1.run.app/ready
```

### Image Proxy Test
```bash
curl -s -o /dev/null -w "%{http_code}" "https://intel-dashboard-4766585081.us-central1.run.app/api/images?url=https://ae01.alicdn.com/test.jpg"
```

## Troubleshooting

### Cloud Run 403/404 on Images
Run the GCS fix workflow:
```bash
gh workflow run deploy-gcs-fix.yml
```

### Cloud SQL Connection Issues
1. Check Cloud SQL instance is running
2. Verify connection name in env vars
3. Check Cloud Run SA has Cloud SQL Client role

### Deployment Failures
1. Check GitHub Actions logs
2. Verify Docker image builds locally
3. Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=50`
