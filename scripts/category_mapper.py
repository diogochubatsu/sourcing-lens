#!/usr/bin/env python3
"""Category Mapper — CRUD operations for category_mappings table.

Usage:
    python3 scripts/category_mapper.py list                          # List all mappings
    python3 scripts/category_mapper.py list --platform ml            # Filter by platform
    python3 scripts/category_mapper.py import                        # Import from category_ids.json
    python3 scripts/category_mapper.py add --our-l1 Audio --our-l2 Microphones --our-l3 "Lapela Sem Fio" \\
        --platform ml --platform-id MLB3835 --platform-name "Áudio" \\
        --bestsellers-url "https://www.mercadolivre.com.br/mais-vendidos/MLB3835"
    python3 scripts/category_mapper.py stats                         # Show statistics
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute, execute_returning


def list_mappings(platform=None, verified=None):
    """List category mappings."""
    conditions = ["1=1"]
    params = []
    
    if platform:
        conditions.append("platform = %s")
        params.append(platform)
    if verified is not None:
        conditions.append("verified = %s")
        params.append(verified)
    
    where = " AND ".join(conditions)
    rows = query(f"""
        SELECT id, our_l1, our_l2, our_l3, platform, platform_category_id,
               platform_category_name, bestsellers_url, confidence, verified,
               product_count, last_scraped
        FROM category_mappings
        WHERE {where}
        ORDER BY our_l1, our_l2, our_l3, platform
    """, tuple(params))
    
    return rows


def add_mapping(our_l1, our_l2, our_l3, platform, platform_id=None,
                platform_name=None, platform_path=None, bestsellers_url=None,
                confidence=0.5):
    """Add or update a category mapping."""
    try:
        result = execute_returning("""
            INSERT INTO category_mappings 
                (our_l1, our_l2, our_l3, platform, platform_category_id,
                 platform_category_name, platform_category_path, bestsellers_url, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (our_l1, our_l2, our_l3, platform) 
            DO UPDATE SET
                platform_category_id = COALESCE(EXCLUDED.platform_category_id, category_mappings.platform_category_id),
                platform_category_name = COALESCE(EXCLUDED.platform_category_name, category_mappings.platform_category_name),
                platform_category_path = COALESCE(EXCLUDED.platform_category_path, category_mappings.platform_category_path),
                bestsellers_url = COALESCE(EXCLUDED.bestsellers_url, category_mappings.bestsellers_url),
                confidence = GREATEST(EXCLUDED.confidence, category_mappings.confidence),
                updated_at = NOW()
            RETURNING id
        """, (our_l1, our_l2, our_l3, platform, platform_id,
              platform_name, platform_path, bestsellers_url, confidence))
        return result[0]['id'] if result else None
    except Exception as e:
        print(f"Error adding mapping: {e}")
        return None


def import_from_json():
    """Import existing mappings from category_ids.json."""
    json_path = os.path.join(os.path.dirname(__file__), 'category_ids.json')
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return 0
    
    with open(json_path) as f:
        data = json.load(f)
    
    count = 0
    
    # Internal category mapping (what maps to what)
    # This is the manual part - mapping platform categories to YOUR categories
    internal_map = {
        'microphones': ('Audio', 'Microphones', 'Geral'),
        'headphones': ('Audio', 'Headphones', 'Geral'),
        'ring_lights': ('Lighting', 'Ring Lights', 'Geral'),
        'tripods': ('Photography', 'Tripods', 'Geral'),
        'led_panels': ('Lighting', 'LED Panels', 'Geral'),
        'home_organization': ('Home', 'Organization', 'Geral'),
        'sports': ('Sports', 'Geral', 'Geral'),
        'bluetooth_speaker': ('Audio', 'Speakers', 'Bluetooth'),
        'smartwatch': ('Tech', 'Wearables', 'Smartwatch'),
        'automotive_tool': ('Tools', 'Automotive', 'Geral'),
        'phone_holder': ('Tech', 'Accessories', 'Phone Holder'),
    }
    
    for platform in ['amazon_br', 'amazon_us']:
        platform_data = data.get(platform, {})
        for cat_key, cat_info in platform_data.items():
            if cat_key not in internal_map:
                print(f"  Skipping {cat_key} (no internal mapping)")
                continue
            
            our_l1, our_l2, our_l3 = internal_map[cat_key]
            bestsellers_url = cat_info.get('bestsellers_url', '')
            platform_name = cat_info.get('name_pt') or cat_info.get('name_en', '')
            platform_id = cat_info.get('id', '')
            
            result = add_mapping(
                our_l1=our_l1,
                our_l2=our_l2,
                our_l3=our_l3,
                platform=platform,
                platform_id=platform_id,
                platform_name=platform_name,
                bestsellers_url=bestsellers_url,
                confidence=0.8
            )
            if result:
                count += 1
                print(f"  Imported: {our_l1}/{our_l2}/{our_l3} -> {platform}: {platform_name}")
    
    # ML categories (from sales_pipeline.py)
    ml_cats = [
        ('Audio', 'Microphones', 'Geral', 'MLB3835', 'Áudio'),
        ('Tools', 'Geral', 'Geral', 'MLB263532', 'Ferramentas'),
        ('Sports', 'Geral', 'Geral', 'MLB1276', 'Esportes'),
        ('Tech', 'Accessories', 'Phone Holder', 'MLB3813', 'Acessórios para Celular'),
        ('Tech', 'Wearables', 'Smartwatch', 'MLB417704', 'Smartwatches'),
        ('Home', 'Geral', 'Geral', 'MLB1574', 'Casa e Decoração'),
        ('Beach', 'Geral', 'Geral', 'MLB1132', 'Praia e Lazer'),
        ('Photography', 'Geral', 'Geral', 'MLB1039', 'Câmeras e Fotografia'),
        ('Lighting', 'Geral', 'Geral', 'MLB430378', 'Iluminação'),
        ('Fashion', 'Geral', 'Geral', 'MLB1430', 'Roupas, Calçados e Acessórios'),
    ]
    
    for our_l1, our_l2, our_l3, mlb_id, ml_name in ml_cats:
        bestsellers_url = f"https://www.mercadolivre.com.br/mais-vendidos/MLB{mlb_id}"
        result = add_mapping(
            our_l1=our_l1,
            our_l2=our_l2,
            our_l3=our_l3,
            platform='ml',
            platform_id=f'MLB{mlb_id}',
            platform_name=ml_name,
            bestsellers_url=bestsellers_url,
            confidence=0.8
        )
        if result:
            count += 1
            print(f"  Imported: {our_l1}/{our_l2}/{our_l3} -> ML: {ml_name}")
    
    return count


def show_stats():
    """Show category mapping statistics."""
    stats = query("""
        SELECT 
            platform,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE verified = TRUE) as verified,
            COUNT(*) FILTER (WHERE bestsellers_url IS NOT NULL) as with_url,
            SUM(COALESCE(product_count, 0)) as total_products
        FROM category_mappings
        GROUP BY platform
        ORDER BY platform
    """)
    
    total = query("SELECT COUNT(*) as c FROM category_mappings")[0]['c']
    internal = query("SELECT COUNT(DISTINCT our_l1 || '/' || our_l2 || '/' || our_l3) as c FROM category_mappings")[0]['c']
    
    print(f"\nCategory Mapping Statistics")
    print(f"{'='*60}")
    print(f"{'Platform':<15} {'Total':>8} {'Verified':>10} {'With URL':>10} {'Products':>10}")
    print(f"{'-'*60}")
    for s in stats:
        print(f"{s['platform']:<15} {s['total']:>8} {s['verified']:>10} {s['with_url']:>10} {s['total_products'] or 0:>10}")
    print(f"{'-'*60}")
    print(f"{'TOTAL':<15} {total:>8}")
    print(f"\nInternal categories: {internal}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Category Mapper')
    subparsers = parser.add_subparsers(dest='command')
    
    # List
    list_parser = subparsers.add_parser('list', help='List mappings')
    list_parser.add_argument('--platform', choices=['amazon_br', 'amazon_us', 'ml'])
    list_parser.add_argument('--verified', action='store_true')
    
    # Import
    subparsers.add_parser('import', help='Import from category_ids.json')
    
    # Add
    add_parser = subparsers.add_parser('add', help='Add mapping')
    add_parser.add_argument('--our-l1', required=True)
    add_parser.add_argument('--our-l2', required=True)
    add_parser.add_argument('--our-l3', required=True)
    add_parser.add_argument('--platform', required=True, choices=['amazon_br', 'amazon_us', 'ml'])
    add_parser.add_argument('--platform-id')
    add_parser.add_argument('--platform-name')
    add_parser.add_argument('--platform-path')
    add_parser.add_argument('--bestsellers-url')
    add_parser.add_argument('--confidence', type=float, default=0.5)
    
    # Stats
    subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        mappings = list_mappings(platform=args.platform, verified=args.verified if args.verified else None)
        for m in mappings:
            url_short = m['bestsellers_url'][:50] + '...' if m.get('bestsellers_url') and len(m['bestsellers_url']) > 50 else m.get('bestsellers_url', '-')
            print(f"[{m['id']}] {m['our_l1']}/{m['our_l2']}/{m['our_l3']} -> {m['platform']}: {m['platform_category_name'] or '-'} ({m['platform_category_id'] or '-'})")
            print(f"    URL: {url_short}")
            print(f"    Confidence: {m['confidence']}, Verified: {m['verified']}, Products: {m['product_count'] or 0}")
            print()
    
    elif args.command == 'import':
        count = import_from_json()
        print(f"\nImported {count} mappings")
    
    elif args.command == 'add':
        result = add_mapping(
            our_l1=args.our_l1,
            our_l2=args.our_l2,
            our_l3=args.our_l3,
            platform=args.platform,
            platform_id=args.platform_id,
            platform_name=args.platform_name,
            platform_path=args.platform_path,
            bestsellers_url=args.bestsellers_url,
            confidence=args.confidence
        )
        if result:
            print(f"Added mapping id={result}")
        else:
            print("Failed to add mapping")
    
    elif args.command == 'stats':
        show_stats()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
