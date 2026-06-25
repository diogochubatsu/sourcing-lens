#!/usr/bin/env python3
"""
Category Resolver — shared utility for all agents.

Usage:
    from category_resolver import resolve_category, ensure_category
    
    # Resolve a product's platform category to silver_category_id
    result = resolve_category(conn, platform='1688', l1='7', l2='50911', l3='1033986')
    # Returns: {'silver_category_id': 3, 'confidence': 0.7, 'l1': 'Eletrônicos', ...}
    
    # Ensure a category exists in silver_categories (for new L2/L3)
    cat_id = ensure_category(conn, l1='Eletrônicos', l2='Celular', l3='Capa')
"""
import psycopg2


def resolve_category(conn, platform, l1=None, l2=None, l3=None):
    """
    Resolve platform category IDs to silver_category_id.
    
    Tries exact match first (L3), then L2, then L1.
    Returns dict with silver_category_id, confidence, l1, l2, l3.
    """
    cur = conn.cursor()
    
    # Try L3 first (most specific)
    if l3:
        cur.execute("""
            SELECT scm.silver_category_id, scm.confidence, sc.l1, sc.l2, sc.l3
            FROM silver_categories_map scm
            JOIN silver_categories sc ON scm.silver_category_id = sc.id
            WHERE scm.platform = %s AND scm.platform_l1_id = %s 
              AND scm.platform_l2_id = %s AND scm.platform_l3_id = %s
        """, (platform, str(l1), str(l2), str(l3)))
        row = cur.fetchone()
        if row:
            return {
                'silver_category_id': row[0],
                'confidence': float(row[1]),
                'l1': row[2], 'l2': row[3], 'l3': row[4],
                'match_level': 'L3'
            }
    
    # Try L2
    if l2:
        cur.execute("""
            SELECT scm.silver_category_id, scm.confidence, sc.l1, sc.l2
            FROM silver_categories_map scm
            JOIN silver_categories sc ON scm.silver_category_id = sc.id
            WHERE scm.platform = %s AND scm.platform_l1_id = %s 
              AND scm.platform_l2_id = %s AND scm.platform_l3_id IS NULL
        """, (platform, str(l1), str(l2)))
        row = cur.fetchone()
        if row:
            return {
                'silver_category_id': row[0],
                'confidence': float(row[1]),
                'l1': row[2], 'l2': row[3], 'l3': None,
                'match_level': 'L2'
            }
    
    # Try L1 (least specific)
    if l1:
        cur.execute("""
            SELECT scm.silver_category_id, scm.confidence, sc.l1
            FROM silver_categories_map scm
            JOIN silver_categories sc ON scm.silver_category_id = sc.id
            WHERE scm.platform = %s AND scm.platform_l1_id = %s 
              AND scm.platform_l2_id IS NULL AND scm.platform_l3_id IS NULL
        """, (platform, str(l1)))
        row = cur.fetchone()
        if row:
            return {
                'silver_category_id': row[0],
                'confidence': float(row[1]),
                'l1': row[2], 'l2': None, 'l3': None,
                'match_level': 'L1'
            }
    
    return None


def ensure_category(conn, l1, l2=None, l3=None, l4=None):
    """
    Ensure a category exists in silver_categories. Returns the id.
    Creates intermediate levels if needed.
    """
    cur = conn.cursor()
    
    # Ensure L1 exists
    cur.execute("SELECT id FROM silver_categories WHERE l1 = %s AND l2 IS NULL AND l3 IS NULL", (l1,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO silver_categories (l1) VALUES (%s) RETURNING id",
            (l1,)
        )
        l1_id = cur.fetchone()[0]
    else:
        l1_id = row[0]
    
    if not l2:
        return l1_id
    
    # Ensure L2 exists
    cur.execute(
        "SELECT id FROM silver_categories WHERE l1 = %s AND l2 = %s AND l3 IS NULL",
        (l1, l2)
    )
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO silver_categories (l1, l2) VALUES (%s, %s) RETURNING id",
            (l1, l2)
        )
        l2_id = cur.fetchone()[0]
    else:
        l2_id = row[0]
    
    if not l3:
        return l2_id
    
    # Ensure L3 exists
    cur.execute(
        "SELECT id FROM silver_categories WHERE l1 = %s AND l2 = %s AND l3 = %s",
        (l1, l2, l3)
    )
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO silver_categories (l1, l2, l3) VALUES (%s, %s, %s) RETURNING id",
            (l1, l2, l3)
        )
        l3_id = cur.fetchone()[0]
    else:
        l3_id = row[0]
    
    return l3_id


def add_platform_mapping(conn, platform, l1_id, l2_id=None, l3_id=None, 
                          silver_category_id=None, category_name=None, confidence=0.8):
    """
    Add or update a platform category mapping.
    If silver_category_id is None, uses resolve_category to find it.
    """
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO silver_categories_map 
            (platform, platform_l1_id, platform_l2_id, platform_l3_id, 
             silver_category_id, platform_category_name, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (platform, platform_l1_id, platform_l2_id, platform_l3_id) 
        DO UPDATE SET 
            silver_category_id = EXCLUDED.silver_category_id,
            platform_category_name = EXCLUDED.platform_category_name,
            confidence = GREATEST(EXCLUDED.confidence, silver_categories_map.confidence),
            updated_at = NOW()
    """, (
        platform, str(l1_id) if l1_id else None,
        str(l2_id) if l2_id else None, str(l3_id) if l3_id else None,
        silver_category_id, category_name, confidence
    ))
    
    return cur.rowcount > 0


def get_category_stats(conn, source=None):
    """Get category distribution stats."""
    cur = conn.cursor()
    
    where = "WHERE bp.silver_category_id IS NOT NULL"
    params = []
    if source:
        where += " AND bp.source = %s"
        params.append(source)
    
    cur.execute(f"""
        SELECT sc.l1, COUNT(*) as cnt
        FROM bronze_products bp
        JOIN silver_categories sc ON bp.silver_category_id = sc.id
        {where}
        GROUP BY sc.l1
        ORDER BY COUNT(*) DESC
    """, tuple(params))
    
    return cur.fetchall()


# Example usage for other agents:
if __name__ == '__main__':
    import sys
    
    conn = psycopg2.connect(
        host='34.170.210.220', port=5432,
        dbname='importasimples_products',
        user='importasimples', password='R{[{f<VajbC{<kvU',
        sslmode='require'
    )
    
    # Example: ML agent maps MLB3835 → Audio
    add_platform_mapping(
        conn, 
        platform='ml',
        l1_id='MLB3835',
        silver_category_id=1,  # Audio
        category_name='Áudio',
        confidence=0.9
    )
    conn.commit()
    
    # Example: Amazon agent maps 2407760 → Eletrônicos
    add_platform_mapping(
        conn,
        platform='amazon',
        l1_id='2407760',
        silver_category_id=3,  # Eletrônicos
        category_name='Electronics',
        confidence=0.9
    )
    conn.commit()
    
    print("Mappings added successfully")
    
    # Show stats
    stats = get_category_stats(conn, source='arbitlens_china')
    print("\nCategory distribution:")
    for l1, cnt in stats:
        print(f"  {l1}: {cnt}")
    
    conn.close()
