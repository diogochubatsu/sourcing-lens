# 1688 Scraping API

> Built on the 1688-intel app. Use this to get 1688 product data for ArbitLens.

## Endpoint

```
https://intel-dashboard-4766585081.us-central1.run.app/api/scrape
```

## 1. Request a Scrape (POST)

```bash
curl -s -X POST https://intel-dashboard-4766585081.us-central1.run.app/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "无线领夹麦克风 Type-C",
    "requested_by": "arbitlens",
    "limit": 20
  }'
```

Returns:
```json
{
  "message": "Scrape completed",
  "request_id": 42,
  "result_count": 20
}
```

Duplicate queries within 1 hour return existing results instead of re-scraping.

## 2. Get Results (GET)

```bash
curl -s "https://intel-dashboard-4766585081.us-central1.run.app/api/scrape?request_id=42"
```

Returns:
```json
{
  "request": { "id": 42, "query": "...", "status": "done", ... },
  "results": [
    {
      "offer_id": "740647797173",
      "title": "产品标题...",
      "price_cny": 25.50,
      "image_url": "https://cbu01.alicdn.com/...",
      "supplier_name": "供应商名称",
      "moq": "2 pieces",
      "repurchase_rate": null,
      "sales_volume_estimate": 1200
    }
  ]
}
```

## 3. List Recent Requests

```bash
curl -s "https://intel-dashboard-4766585081.us-central1.run.app/api/scrape?requested_by=arbitlens&limit=10"
```

## 4. DB Tables (direct SQL access if needed)

```sql
-- Requests
SELECT * FROM scrape_requests WHERE requested_by = 'arbitlens' ORDER BY requested_at DESC;

-- Results
SELECT * FROM scrape_results WHERE request_id = 42;
```

## Fields Available

| Field | Type | Description |
|-------|------|-------------|
| offer_id | text | 1688 product ID |
| title | text | Chinese title |
| price_cny | numeric | Price in CNY |
| image_url | text | Main product image from alicdn |
| supplier_name | text | Shop name |
| moq | text | Minimum order quantity |
| repurchase_rate | integer | Only on detail pages (null for search) |
| sales_volume_estimate | integer | Parsed from "1.2万件" format |

## Status (2026-05-27)

- API is reachable at the Cloud Run URL
- Scrape POST endpoint returns "Internal error" — needs debugging by 1688-intel team
- GET endpoint works (returns empty results list)

## Integration Plan

Once the scrape endpoint works:
1. POST query → get request_id
2. GET results by request_id
3. For each result: download image, compute SigLIP2 embedding + pHash
4. Insert into arbitlens_products with platform='1688'
