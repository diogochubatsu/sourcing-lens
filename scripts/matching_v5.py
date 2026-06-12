#!/usr/bin/env python3
"""Matching v5 - amazon_br vs amazon_us cross-border matching.

Compares amazon_br (BRL) with amazon_us (USD) products using:
- Image similarity (80%)
- Model match (10%)
- Brand match (5%)
- Title word overlap (5%)

Score >= 50 required. Strict 1-to-1 dedup on both sides.
"""
import re
import sys
import numpy as np
sys.path.insert(0, '.')
import imagehash
from scripts.db import query, execute

BRANDS = {
    'hollyland': ['hollyland'], 'boya': ['boya'], 'kaidi': ['kaidi'],
    'micgeek': ['micgeek'], 'agold': ["a'gold", 'agold'], 'mymotors': ['mymotors', 'mymotiv'],
    'maono': ['maono'], 'fifine': ['fifine'], 'rode': ['rode'], 'shure': ['shure'],
    'saramonic': ['saramonic'], 'maxnova': ['maxnova'], 'basike': ['basike'],
    'bmad': ['bmad'], 'voltion': ['voltion'], 'hmaston': ['hmaston'],
    'eletro': ['eletro mex', 'eletro-mex'], 'kaifi': ['kaifi'], 'zcco': ['zcco'],
    'leveller': ['leveller'], 'j6': ['j6 ima', 'j6-ima'],
    'jbl': ['jbl'], 'sony': ['sony'], 'edifier': ['edifier'],
    'anker': ['anker', 'soundcore'], 'beats': ['beats'], 'bose': ['bose'],
    'philips': ['philips', 'philco'], 'samsung': ['samsung'], 'apple': ['apple', 'airpods'],
    'logitech': ['logitech'], 'hyperx': ['hyperx'], 'razer': ['razer'],
    'skullcandy': ['skullcandy'], 'oneodio': ['oneodio'], 'havit': ['havit'],
    'kz': ['kz '], 'moondrop': ['moondrop'], 'lenovo': ['lenovo', 'thinkplus'],
    'qcy': ['qcy'], 'haylou': ['haylou'], 'redmi': ['redmi'], 'realme': ['realme'],
    'neewer': ['neewer'], 'yongnuo': ['yongnuo'], 'godox': ['godox'],
    'ulanzi': ['ulanzi'], 'dji': ['dji'], 'manfrotto': ['manfrotto'],
    'benro': ['benro'], 'sirui': ['sirui'], 'yunteng': ['yunteng'],
    'esddi': ['esddi'], 'viltrox': ['viltrox'], 'zhiyun': ['zhiyun'],
    'gvm': ['gvm'], 'aputure': ['aputure', 'amaran'],
}

STOPWORDS = {
    'de','para','com','e','o','a','os','as','um','uma','no','na','em','por','sem',
    'fio','tipo','preto','novo','branco','vermelho','azul','preta','original',
    'profissional','the','and','for','with','from','this','that','you','your',
    'not','are','can','has','have','its','all','w','x','y','z','2','s','t',
    'mini','pack','kit','compatible','wireless','bluetooth','usb',
}

def extract_model(title):
    t = title.upper()
    h = re.findall(r'LARK\s*(M\d+[A-Z]*|A\d+)', t)
    if h: return f"hollyland_{h[0]}"
    b = re.findall(r'BY-?([A-Z]+\d+)', t)
    if b: return f"boya_{b[0]}"
    k = re.findall(r'KMF-?([A-Z]?\d+)', t)
    if k: return f"kaidi_{k[0]}"
    m = re.findall(r'(WH|WF|MDR|CHB|TWS|TUNE|LIVE|FREEBUDS?)\s*-?\s*(\d+[A-Z]*)', t)
    if m: return f"{m[0][0]}_{m[0][1]}"
    sku = re.findall(r'\b([A-Z]{2,}[\-]?\d{3,}[A-Z]?)\b', t)
    if sku: return sku[0]
    return None

def extract_brand(title):
    tl = title.lower()
    for brand, aliases in BRANDS.items():
        for a in aliases:
            if a in tl:
                return brand
    return None

def _resize_hash(h, target_size):
    arr = h.hash.astype(int)
    src_size = arr.shape[0]
    if src_size == target_size:
        return h
    factor = src_size // target_size
    small = arr.reshape(target_size, factor, target_size, factor).mean(axis=(1, 3)) > 0.5
    return imagehash.ImageHash(small)

def image_sim(h1_str, h2_str):
    if not h1_str or not h2_str:
        return 0
    try:
        h1 = imagehash.hex_to_hash(h1_str)
        h2 = imagehash.hex_to_hash(h2_str)
        size1, size2 = h1.hash.shape[0], h2.hash.shape[0]
        if size1 != size2:
            target = min(size1, size2)
            h1 = _resize_hash(h1, target)
            h2 = _resize_hash(h2, target)
        dist = h1 - h2
        bits = len(h1.hash.flatten())
        return max(0, (1 - dist / bits) * 100)
    except Exception:
        return 0

def match_score(br, us):
    """Weighted scoring: image 80%, model 10%, brand 5%, title 5%."""
    s = 0
    # Image: 80%
    s += image_sim(br.get('image_hash'), us.get('image_hash')) * 0.8
    m1 = extract_model(br['title'])
    m2 = extract_model(us['title'])
    if m1 and m2:
        s += 10 if m1 == m2 else -6
    elif (m1 and not m2) or (m2 and not m1):
        b1 = extract_brand(br['title'])
        b2 = extract_brand(us['title'])
        if b1 and b2 and b1 == b2:
            s += 4
    else:
        s += 3
    b1 = extract_brand(br['title'])
    b2 = extract_brand(us['title'])
    if b1 and b2:
        s += 5 if b1 == b2 else -3
    w1 = set(br['title'].lower().split()) - STOPWORDS
    w2 = set(us['title'].lower().split()) - STOPWORDS
    if w1 and w2:
        s += (len(w1 & w2) / len(w1 | w2)) * 5
    return s

def run_matching(category):
    br = query(
        "SELECT id, platform_id, title, price, image_hash, url "
        "FROM products WHERE platform='amazon_br' AND category=%s AND image_hash IS NOT NULL",
        (category,)
    )
    us = query(
        "SELECT id, platform_id, title, price, image_hash, url "
        "FROM products WHERE platform='amazon_us' AND category=%s",
        (category,)
    )
    print(f'\n{category}: Amazon BR={len(br)}, Amazon US={len(us)}')
    if not br or not us:
        print(f'  SKIP - need products on both platforms')
        return []
    all_scores = []
    for a in br:
        for u in us:
            score = match_score(a, u)
            all_scores.append((
                a['id'], u['id'], score,
                a['title'], u['title'],
                float(a['price'] or 0), float(u['price'] or 0),
                a['platform_id'], u['platform_id'],
            ))
    good = [x for x in all_scores if x[2] >= 50]
    good.sort(key=lambda x: x[2], reverse=True)
    seen_br = set()
    seen_us = set()
    final = []
    for m in good:
        br_id, us_id = m[0], m[1]
        if br_id not in seen_br and us_id not in seen_us:
            seen_br.add(br_id)
            seen_us.add(us_id)
            final.append(m)
    print(f'  Total pairs: {len(all_scores)}, score>=50: {len(good)}, deduped 1-to-1: {len(final)}')
    for i, (br_id, us_id, sc, br_title, us_title, br_price, us_price, br_pid, us_pid) in enumerate(final):
        print(f'  {i+1}. Score:{sc:.0f} | BR R${br_price:.0f} vs US US${us_price:.2f} | {br_pid} vs {us_pid}')
    return final

def main():
    cat_query = query("""
        SELECT DISTINCT a.category
        FROM products a
        JOIN products u ON a.category = u.category
        WHERE a.platform='amazon_br' AND u.platform='amazon_us' AND a.is_active=true AND u.is_active=true
        ORDER BY a.category
    """)
    categories = [c['category'] for c in cat_query]
    print(f"Amazon BR vs Amazon US cross-border matching")
    print(f"Categories with both platforms: {categories}")
    print(f"{'='*60}")

    execute("DELETE FROM matches WHERE match_method='amazon_br_vs_us'")
    total_saved = 0
    for cat in categories:
        matches = run_matching(cat)
        for br_id, us_id, sc, br_title, us_title, br_price, us_price, br_pid, us_pid in matches:
            execute(
                "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
                "VALUES (%s, %s, %s, 'amazon_br_vs_us')",
                (int(br_id), int(us_id), float(sc / 100))
            )
        total_saved += len(matches)

    print(f"\n{'='*60}")
    print(f"Total matches saved: {total_saved}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
