#!/usr/bin/env python3
"""Matching v4 - filtered and deduplicated. Runs ALL categories."""
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
            if a in tl: return brand
    return None

def _resize_hash(h, target_size):
    arr = h.hash.astype(int)
    src_size = arr.shape[0]
    if src_size == target_size: return h
    factor = src_size // target_size
    small = arr.reshape(target_size, factor, target_size, factor).mean(axis=(1, 3)) > 0.5
    return imagehash.ImageHash(small)

def image_sim(h1_str, h2_str):
    if not h1_str or not h2_str: return 0
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
    except:
        return 0

def match_score(amz, ml):
    """Weighted: image 80%, model 10%, brand 5%, title 5%."""
    s = 0
    # Image: 80% — dominant signal, works for both branded and generic products
    s += image_sim(amz.get('image_hash'), ml.get('image_hash')) * 0.8
    m1, m2 = extract_model(amz['title']), extract_model(ml['title'])
    if m1 and m2:
        s += 10 if m1 == m2 else -6
    elif (m1 and not m2) or (m2 and not m1):
        b1 = extract_brand(amz['title'])
        b2 = extract_brand(ml['title'])
        if b1 and b2 and b1 == b2:
            s += 4
    else:
        s += 3
    b1, b2 = extract_brand(amz['title']), extract_brand(ml['title'])
    if b1 and b2:
        s += 5 if b1 == b2 else -3
    stopwords = {'de','para','com','e','o','a','os','as','um','uma','no','na','em','por','sem',
                 'fio','tipo','preto','novo','branco','vermelho','azul','preta','original',
                 'profissional'}
    w1 = set(amz['title'].lower().split()) - stopwords
    w2 = set(ml['title'].lower().split()) - stopwords
    if w1 and w2:
        s += (len(w1 & w2) / len(w1 | w2)) * 5
    return s

def run_matching(category):
    amz = query("SELECT id, platform_id, title, price, sales_30d, image_hash, image_urls, url FROM products WHERE platform='amazon_br' AND category=%s AND image_hash IS NOT NULL", (category,))
    ml = query("SELECT id, platform_id, title, price, sales_30d, image_hash, image_urls, url, supplier_name FROM products WHERE platform='ml' AND category=%s AND image_hash IS NOT NULL", (category,))
    print(f'{category}: Amazon BR={len(amz)}, ML={len(ml)}')
    if not amz or not ml:
        print(f'  SKIP - need both platforms')
        return []
    all_scores = []
    for a in amz:
        for m in ml:
            score = match_score(a, m)
            all_scores.append((a['id'], m['id'], score,
                float(a['price'] or 0) - float(m['price'] or 0),
                a['title'], m['title'],
                float(a['price'] or 0), float(m['price'] or 0),
                a['platform_id'], m['platform_id']))
    good = [x for x in all_scores if x[2] >= 50]
    good.sort(key=lambda x: x[2], reverse=True)
    seen_amz = set()
    seen_ml = set()
    final = []
    for m in good:
        amz_id, ml_id = m[0], m[1]
        if amz_id not in seen_amz and ml_id not in seen_ml:
            seen_amz.add(amz_id)
            seen_ml.add(ml_id)
            final.append(m)
    print(f'  Total pairs: {len(all_scores)}, score>=50: {len(good)}, deduped 1-to-1: {len(final)}')
    for i, (aid, mid, sc, diff, at, mt, ap, mp, a_pid, m_pid) in enumerate(final):
        print(f'  {i+1}. Score:{sc:.0f} | R${ap:.0f} vs R${mp:.0f} (diff R${diff:.0f}) | {a_pid} vs {m_pid}')
    return final

cats = query("""
    SELECT DISTINCT a.category
    FROM products a
    JOIN products m ON a.category = m.category
    WHERE a.platform='amazon_br' AND m.platform='ml' AND a.is_active=true AND m.is_active=true
    ORDER BY a.category
""")
categories = [c['category'] for c in cats]
print(f"Categories with both platforms: {categories}")

execute("DELETE FROM matches")
total_saved = 0
for cat in categories:
    matches = run_matching(cat)
    for aid, mid, sc, diff, at, mt, ap, mp, a_pid, m_pid in matches:
        execute("INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) VALUES (%s, %s, %s, 'image_title_brand')",
                (int(aid), int(mid), float(sc / 100)))
    total_saved += len(matches)
    print()

print(f"{'=' * 60}")
print(f"Total matches saved: {total_saved}")
