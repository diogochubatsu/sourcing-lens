#!/usr/bin/env python3
"""
arbitlens Categories V2 — Expanded product categories for ML sellers.

20 categories with 4-6 queries each (PT/CN/EN), targeting high-demand
products for Brazilian Mercado Livre sellers importing from China.

Usage:
  python3 categories_v2.py --list
  python3 categories_v2.py --search audio
  python3 categories_v2.py --search all --limit 20
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
        "priority": "high",
        "queries": {
            "pt": ["microfone lapela", "microfone sem fio", "caixa de som portátil", "microfone condensador", "mesa de som"],
            "cn": ["领夹麦克风", "无线麦克风", "蓝牙音箱", "电容麦克风", "调音台"],
            "en": ["lapel microphone", "wireless microphone", "portable speaker", "condenser mic", "audio mixer"],
        },
        "exclude": ["meia", "sock", "calça", "camisa", "shoe", "tênis"],
    },
    "wearables": {
        "name": "Wearables & Smartwatches",
        "icon": "⌚",
        "priority": "high",
        "queries": {
            "pt": ["relógio smart", "smartwatch", "pulseira inteligente", "relógio esportivo", "watchband"],
            "cn": ["智能手表", "智能手环", "运动手表", "表带", "儿童电话手表"],
            "en": ["smart watch", "smart band", "fitness tracker", "sport watch", "watch band"],
        },
        "exclude": ["meia", "sock", "calça", "pants", "camisa", "tênis", "sapato"],
    },
    "eletronicos": {
        "name": "Eletrônicos & Acessórios",
        "icon": "📱",
        "priority": "high",
        "queries": {
            "pt": ["capa celular", "pelicula celular", "suporte celular", "mouse sem fio", "teclado bluetooth"],
            "cn": ["手机壳", "手机膜", "手机支架", "无线鼠标", "蓝牙键盘"],
            "en": ["phone case", "screen protector", "phone holder", "wireless mouse", "bluetooth keyboard"],
        },
        "exclude": ["meia", "calça", "camisa"],
    },
    "casa": {
        "name": "Casa & Decoração",
        "icon": "🏠",
        "priority": "medium",
        "queries": {
            "pt": ["organizador", "armário organização", "prateleira", "cortina blackout", "almofada decorativa"],
            "cn": ["收纳盒", "置物架", "隔板", "遮光窗帘", "抱枕"],
            "en": ["storage box", "shelf", "partition", "blackout curtain", "decorative pillow"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "cozinha": {
        "name": "Cozinha & Utensílios",
        "icon": "🍳",
        "priority": "medium",
        "queries": {
            "pt": ["airfryer", "liquidificador portátil", "panela elétrica", "coador café", "faqueiro"],
            "cn": ["空气炸锅", "便携搅拌机", "电煮锅", "咖啡滤网", "餐具套装"],
            "en": ["air fryer", "portable blender", "electric pot", "coffee filter", "cutlery set"],
        },
        "exclude": ["fone", "microfone", "meia", "calça"],
    },
    "beleza": {
        "name": "Beleza & Cuidados",
        "icon": "💄",
        "priority": "high",
        "queries": {
            "pt": ["maquiagem", "kit pincel", "secador portátil", "chapinha", "aparador barba"],
            "cn": ["化妆品套装", "化妆刷套装", "便携吹风机", "直发器", "剃须刀"],
            "en": ["makeup kit", "brush set", "portable dryer", "hair straightener", "beard trimmer"],
        },
        "exclude": ["meia", "calça", "camisa", "sapato"],
    },
    "ferramentas": {
        "name": "Ferramentas & Hardware",
        "icon": "🔧",
        "priority": "medium",
        "queries": {
            "pt": ["ferramenta elétrica", "parafusadeira", "chave inglesa", "nível laser", "kit ferramentas"],
            "cn": ["电动工具", "电钻", "扳手", "激光水平仪", "工具套装"],
            "en": ["power tool", "electric drill", "wrench", "laser level", "tool kit"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "esportes": {
        "name": "Esportes & Fitness",
        "icon": "🏋️",
        "priority": "medium",
        "queries": {
            "pt": ["tapete yoga", "halteres", "bola pilates", "faixa elástica", "corda pular"],
            "cn": ["瑜伽垫", "哑铃", "瑜伽球", "弹力带", "跳绳"],
            "en": ["yoga mat", "dumbbells", "pilates ball", "resistance band", "jump rope"],
        },
        "exclude": ["fone", "microfone", "meia", "calça"],
    },
    "pets": {
        "name": "Pet Shop",
        "icon": "🐾",
        "priority": "high",
        "queries": {
            "pt": ["brinquedo cachorro", "coleira pet", "comedouro automático", "cama pet", "arranhador gato"],
            "cn": ["狗玩具", "宠物项圈", "自动喂食器", "宠物床", "猫抓板"],
            "en": ["dog toy", "pet collar", "automatic feeder", "pet bed", "cat scratcher"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "infantis": {
        "name": "Infantil & Brinquedos",
        "icon": "🧸",
        "priority": "high",
        "queries": {
            "pt": ["brinquedo educativo", "carrinho controle remoto", "boneca", "puzzle 3d", "jogo tabuleiro"],
            "cn": ["益智玩具", "遥控车", "洋娃娃", "3D拼图", "桌游"],
            "en": ["educational toy", "remote control car", "doll", "3d puzzle", "board game"],
        },
        "exclude": ["fone", "microfone", "meia", "calça"],
    },
    "automotivo": {
        "name": "Automotivo",
        "icon": "🚗",
        "priority": "medium",
        "queries": {
            "pt": ["acessório carro", "organizador porta-malas", "suporte celular carro", "câmera ré", "led automotivo"],
            "cn": ["汽车用品", "后备箱收纳", "车载手机支架", "倒车摄像头", "汽车LED灯"],
            "en": ["car accessory", "trunk organizer", "car phone mount", "reverse camera", "car led light"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "iluminacao": {
        "name": "Iluminação LED",
        "icon": "💡",
        "priority": "medium",
        "queries": {
            "pt": ["lâmpada led", "fita led", "luz noturna", "lanterna recarregável", "abajour led"],
            "cn": ["LED灯泡", "LED灯带", "小夜灯", "充电手电筒", "LED台灯"],
            "en": ["led bulb", "led strip", "night light", "rechargeable flashlight", "led lamp"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "jardim": {
        "name": "Jardim & Plantas",
        "icon": "🌱",
        "priority": "low",
        "queries": {
            "pt": ["vaso flor", "regador automático", "ferramenta jardim", "mangueira", "semente"],
            "cn": ["花盆", "自动浇水器", "园艺工具", "水管", "种子"],
            "en": ["flower pot", "auto waterer", "garden tool", "hose", "seeds"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "saude": {
        "name": "Saúde & Bem-estar",
        "icon": "🏥",
        "priority": "medium",
        "queries": {
            "pt": ["termômetro digital", "massagador", "pulso digital", "oxímetro", "faixa compressão"],
            "cn": ["电子体温计", "按摩器", "电子血压计", "血氧仪", "压缩绷带"],
            "en": ["digital thermometer", "massager", "pulse oximeter", "compression bandage"],
        },
        "exclude": ["fone", "microfone", "meia", "calça"],
    },
    "papelaria": {
        "name": "Papelaria & Escritório",
        "icon": "📝",
        "priority": "low",
        "queries": {
            "pt": ["caderno personalizado", "caneta gel", "adesivo", "organizador mesa", "luminária mesa"],
            "cn": ["定制笔记本", "中性笔", "贴纸", "桌面收纳", "台灯"],
            "en": ["custom notebook", "gel pen", "stickers", "desk organizer", "desk lamp"],
        },
        "exclude": ["fone", "microfone", "meia", "calça"],
    },
    "moda": {
        "name": "Moda & Acessórios",
        "icon": "👗",
        "priority": "high",
        "queries": {
            "pt": ["bolsa feminina", "óculos sol", "cinto couro", "chapéu", "mochila"],
            "cn": ["女包", "太阳镜", "皮带", "帽子", "背包"],
            "en": ["women bag", "sunglasses", "leather belt", "hat", "backpack"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "calcados": {
        "name": "Calçados",
        "icon": "👟",
        "priority": "medium",
        "queries": {
            "pt": ["tênis esportivo", "chinelo", "sandália", "botina", "sapato social"],
            "cn": ["运动鞋", "拖鞋", "凉鞋", "工装靴", "皮鞋"],
            "en": ["sports shoe", "slipper", "sandal", "work boot", "dress shoe"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "moveis": {
        "name": "Móveis & Organização",
        "icon": "🪑",
        "priority": "low",
        "queries": {
            "pt": ["estante", "cadeira escritório", "mesa dobrável", "armário", "gaveteiro"],
            "cn": ["书架", "办公椅", "折叠桌", "衣柜", "抽屉柜"],
            "en": ["bookshelf", "office chair", "foldable table", "wardrobe", "drawer unit"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
    "alimentos": {
        "name": "Alimentos & Bebidas",
        "icon": "🍜",
        "priority": "medium",
        "queries": {
            "pt": ["chá em pó", "tempero instantâneo", "lanche chinês", "biscoito importado", "café especial"],
            "cn": ["速溶茶", "即调味料", "中国零食", "进口饼干", "特种咖啡"],
            "en": ["instant tea", "seasoning", "chinese snack", "imported biscuit", "specialty coffee"],
        },
        "exclude": ["fone", "microfone", "meia"],
    },
}


def list_categories():
    """Print all available categories."""
    print(f"\n{'Slug':20s} | {'Name':30s} | {'Priority':10s} | {'Queries':8s}")
    print("-" * 75)
    for slug, cat in sorted(CATEGORIES.items(), key=lambda x: x[1].get('priority', 'low')):
        n_queries = sum(len(qs) for qs in cat["queries"].values())
        print(f"{slug:20s} | {cat['name']:30s} | {cat.get('priority','?'):10s} | {n_queries:8d}")
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

        all_queries = []
        for lang, queries in cat["queries"].items():
            for q in queries:
                all_queries.append(q)

        print(f"  Running {len(all_queries)} queries in parallel...", file=sys.stderr)

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

        merged.sort(key=lambda x: x.get("price_brl") or 0)

        plat_counts = {}
        for s in sources:
            for plat, count in s.get("platforms", {}).items():
                plat_counts[plat] = plat_counts.get(plat, 0) + count

        result = {
            "category": cat_slug,
            "category_name": cat["name"],
            "icon": cat["icon"],
            "priority": cat.get("priority", "medium"),
            "total_products": len(merged),
            "products": merged,
            "platforms": plat_counts,
            "search_time_ms": int((time.time() - start) * 1000),
        }
        all_results[cat_slug] = result

        print(f"\n  Total: {len(merged)} unique products across {len(plat_counts)} platforms", file=sys.stderr)

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
        if len(results) == 1:
            slug_out = list(results.keys())[0]
            print(json.dumps(results[slug_out], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0)

    print("Usage:")
    print("  python3 categories_v2.py --list")
    print("  python3 categories_v2.py --search audio")
    print("  python3 categories_v2.py --search all --limit 20")
