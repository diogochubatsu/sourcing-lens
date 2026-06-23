#!/usr/bin/env python3
"""
arbitlens Categories — real-world product categories for ML sellers.
Each category has PT/CN/EN queries + exclude terms to filter noise.

Usage:
  python3 categories.py --list
  python3 categories.py --search audio
  python3 categories.py --search all
"""
import json
import os
import sys
import time
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from search import search_all, PLATFORM_LABELS

CATEGORIES = {
    "audio": {
        "name": "Áudio & Microfones",
        "icon": "🎙️",
        "queries": {
            "pt": ["microfone lapela", "microfone sem fio", "caixa de som portátil", "fone bluetooth"],
            "cn": ["领夹麦克风", "无线麦克风", "蓝牙耳机", "蓝牙音箱"],
            "en": ["lapel microphone", "wireless microphone", "bluetooth speaker", "wireless earbuds"],
        },
        "exclude": ["meia", "sock", "calça", "camisa", "shoe", "tênis"],
    },
    "wearables": {
        "name": "Wearables & Smartwatches",
        "icon": "⌚",
        "queries": {
            "pt": ["relógio smart", "smartwatch", "pulseira inteligente", "fone bluetooth"],
            "cn": ["智能手表", "智能手环", "蓝牙耳机", "运动手表"],
            "en": ["smart watch", "smart band", "fitness tracker", "wireless earphone"],
        },
        "exclude": ["meia", "sock", "calça", "pants", "camisa", "tênis", "sapato"],
    },
    "carregadores": {
        "name": "Carregadores & Power Banks",
        "icon": "🔋",
        "queries": {
            "pt": ["carregador portátil", "power bank", "carregador sem fio", "carregador veicular"],
            "cn": ["充电宝", "无线充电器", "车载充电器", "快充充电器"],
            "en": ["power bank", "wireless charger", "fast charger", "car charger"],
        },
        "exclude": ["capa", "case", "fone", "meia"],
    },
    "camera": {
        "name": "Câmeras & Webcams",
        "icon": "📷",
        "queries": {
            "pt": ["câmera segurança", "webcam", "action cam", "câmera esportiva"],
            "cn": ["摄像头", "网络摄像头", "运动相机", "监控摄像头"],
            "en": ["security camera", "webcam", "action camera", "sports camera"],
        },
        "exclude": ["microfone", "fone", "meia"],
    },
    "fones": {
        "name": "Fones & Auscultadores",
        "icon": "🎧",
        "queries": {
            "pt": ["fone bluetooth", "fone sem fio", "headphone", "airpods"],
            "cn": ["蓝牙耳机", "无线耳机", "头戴式耳机", "降噪耳机"],
            "en": ["bluetooth earphone", "wireless headphone", "noise cancelling headphone", "earbuds"],
        },
        "exclude": ["meia", "camisa", "sapato", "calça"],
    },
    "cabos": {
        "name": "Cabos & Adaptadores",
        "icon": "🔌",
        "queries": {
            "pt": ["cabo usb", "cabo type c", "adaptador tomada", "carregador"],
            "cn": ["USB数据线", "Type-C数据线", "充电器", "转换插头"],
            "en": ["usb cable", "type c cable", "charger adapter", "power adapter"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "gadgets": {
        "name": "Gadgets & Eletrônicos",
        "icon": "💡",
        "queries": {
            "pt": ["lanterna led", "controle remoto", "suporte celular", "mouse sem fio"],
            "cn": ["LED手电筒", "遥控器", "手机支架", "无线鼠标"],
            "en": ["led flashlight", "remote control", "phone holder", "wireless mouse"],
        },
        "exclude": ["meia", "camisa", "calça", "tênis"],
    },
    "iluminacao": {
        "name": "Iluminação LED",
        "icon": "💡",
        "queries": {
            "pt": ["lâmpada led", "fita led", "luz noturna", "luz smart"],
            "cn": ["LED灯泡", "LED灯带", "小夜灯", "智能灯"],
            "en": ["led bulb", "led strip", "night light", "smart light"],
        },
        "exclude": ["microfone", "fone", "meia"],
    },
}


def list_categories():
    """Print all available categories."""
    print(f"\n{'Category':20s} | {'Name':30s} | {'Queries (PT)':40s}")
    print("-" * 95)
    for slug, cat in sorted(CATEGORIES.items()):
        pts = ", ".join(cat["queries"]["pt"][:2])
        print(f"{slug:20s} | {cat['name']:30s} | {pts:40s}")
    print(f"\nTotal: {len(CATEGORIES)} categories")


def search_category(slug, max_results=30):
    """Search all queries for a category, return merged results."""
    if slug == "all":
        cats = list(CATEGORIES.keys())
    elif slug in CATEGORIES:
        cats = [slug]
    else:
        print(f"Category '{slug}' not found. Use --list to see available.")
        return {}

    all_results = {}
    start = time.time()

    for cat_slug in cats:
        cat = CATEGORIES[cat_slug]
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  {cat['name']} ({cat_slug})", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        platform_results = []
        exclude = set(cat.get("exclude", []))

        # Run all queries in parallel
        all_queries = []
        for lang, queries in cat["queries"].items():
            for q in queries:
                all_queries.append(q)

        print(f"  Running {len(all_queries)} queries in parallel...", file=sys.stderr)

        # Collect + deduplicate
        seen_urls = set()
        merged = []
        sources = []

        def search_single(q):
            try:
                return search_all(q, max_results_per_platform=max(5, max_results // max(1, len(all_queries))))
            except Exception as e:
                return {"error": str(e), "products": []}

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(all_queries))) as ex:
            futures = {ex.submit(search_single, q): q for q in all_queries}
            for f in concurrent.futures.as_completed(futures):
                q = futures[f]
                try:
                    res = f.result()
                    n = len(res.get("products", []))
                    print(f"    '{q}' -> {n} products", file=sys.stderr)
                    if n > 0:
                        sources.append(res)
                        for p in res["products"]:
                            url = p.get("product_url", "")
                            name = p.get("product_name", "").lower()
                            if any(excl in name for excl in exclude):
                                continue
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                merged.append(p)
                except Exception as e:
                    print(f"    '{q}' -> error: {e}", file=sys.stderr)

        # Sort by price
        merged.sort(key=lambda x: x.get("price_brl") or 0)

        # Aggregate platform counts
        plat_counts = {}
        for s in sources:
            for plat, count in s.get("platforms", {}).items():
                plat_counts[plat] = plat_counts.get(plat, 0) + count

        result = {
            "category": cat_slug,
            "category_name": cat["name"],
            "icon": cat["icon"],
            "total_products": len(merged),
            "products": merged,
            "platforms": plat_counts,
            "search_time_ms": int((time.time() - start) * 1000),
        }
        all_results[cat_slug] = result

        print(f"\n  Total: {len(merged)} unique products across {len(plat_counts)} platforms", file=sys.stderr)
        print(f"  Platforms: {json.dumps(plat_counts, ensure_ascii=False)}", file=sys.stderr)
        print(f"  Time: {result['search_time_ms']}ms", file=sys.stderr)

        # Show top 5 by price
        print(f"\n  Top 5 cheapest:", file=sys.stderr)
        for p in merged[:5]:
            print(f"    R${p.get('price_brl',0):>7.2f} | {p.get('platform','?'):20s} | {p.get('product_name','')[:50]}", file=sys.stderr)

    return all_results


if __name__ == "__main__":
    if "--list" in sys.argv:
        list_categories()
        sys.exit(0)

    if "--search" in sys.argv:
        idx = sys.argv.index("--search")
        slug = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "all"
        max_res = int(sys.argv[idx + 2]) if len(sys.argv) > idx + 2 else 30
        results = search_category(slug, max_res)
        # Output JSON for API consumption
        if len(results) == 1:
            slug_out = list(results.keys())[0]
            print(json.dumps(results[slug_out], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0)

    print("Usage:")
    print("  python3 categories.py --list")
    print("  python3 categories.py --search audio")
    print("  python3 categories.py --search all")
