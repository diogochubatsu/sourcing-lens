#!/bin/bash
# Daily scraping cron job
# Run: 0 2 * * * /mnt/ssd/1688-intel/scripts/arbitlens/daily_scrape.sh

export DATABASE_URL="postgresql://hermes1688:Lndgcp%40%2312@localhost:5432/intel_data"
cd /mnt/ssd/1688-intel

# Log start
echo "$(date): Starting daily scrape" >> scripts/arbitlens/output/scrape.log

# Scrape all categories
python3 scripts/arbitlens/batch_expand.py --all --limit 5 >> scripts/arbitlens/output/scrape.log 2>&1

# Update taxonomy counts
python3 -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = conn.cursor()
cursor.execute('''UPDATE taxonomy SET product_count = (
    SELECT COUNT(*) FROM arbitlens_products p
    WHERE p.is_active = true
    AND (p.category = taxonomy.slug OR p.category_n2 = taxonomy.slug)
)''')
conn.commit()
conn.close()
" >> scripts/arbitlens/output/scrape.log 2>&1

echo "$(date): Daily scrape complete" >> scripts/arbitlens/output/scrape.log
