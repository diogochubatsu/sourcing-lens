"""Image classification using SigLIP zero-shot — verify product categories.

This is a quality check: we already have categories, but we want to verify
that the image actually matches its assigned category. This catches:
- Misclassified products
- Mixed categories
- Image-content/category mismatches
"""
import sys, os
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

# (label_id, descriptive_label) — descriptive labels in English + clean Portuguese
# Using English-heavy labels because SigLIP is trained on English-heavy data
CATEGORIES = [
    ('AUDIO', 'AUDIO speaker headphone earbuds microphone bluetooth portable'),
    ('ACESSORIOS', 'ACESSORIOS phone stand holder support desk car mobile'),
    ('BOLSAS', 'BOLSAS bag purse wallet luggage suitcase travel tote'),
    ('CASA', 'CASA home organization container bottle tumbler thermal cup'),
    ('COZINHA', 'COZINHA kitchen cookware pan pot utensil spatula jar container'),
    ('ESPORTES', 'ESPORTES sports tracker GPS smart tag running fitness'),
    ('FERRAMENTAS', 'FERRAMENTAS tool drill screwdriver wrench hammer socket'),
    ('FOTOGRAFIA', 'FOTOGRAFIA camera tripod stand monopod support photo'),
    ('ILUMINACAO', 'ILUMINACAO ring light LED panel lamp photo video'),
    ('MEIAS', 'MEIAS socks stockings hosiery'),
    ('MOCHILAS', 'MOCHILAS backpack school travel bag laptop'),
    ('MODA', 'MODA clothing apparel shirt pants jacket hat belt'),
    ('MODA_INTIMA', 'MODA INTIMA underwear boxer lingerie intimate'),
    ('PET_SHOP', 'PET SHOP pet dog cat food treat litter animal'),
    ('PRAIA', 'PRAIA beach towel chair clip pin outdoor'),
    ('WEARABLES', 'WEARABLES smartwatch watch wristband fitness tracker'),
]

# Map label_id to actual category_l1 in DB
LABEL_TO_L1 = {
    'AUDIO': 'Audio',
    'ACESSORIOS': 'Acessórios Mobile',
    'BOLSAS': 'Bolsas',
    'CASA': 'Casa',
    'COZINHA': 'Cozinha',
    'ESPORTES': 'Esportes',
    'FERRAMENTAS': 'Ferramentas',
    'FOTOGRAFIA': 'Fotografia',
    'ILUMINACAO': 'Iluminação',
    'MEIAS': 'Meias',
    'MOCHILAS': 'Mochilas',
    'MODA': 'Moda',
    'MODA_INTIMA': 'Moda Intima',
    'PET_SHOP': 'Pet Shop',
    'PRAIA': 'Praia',
    'WEARABLES': 'Wearables',
}


def main():
    import torch
    from PIL import Image
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from io import BytesIO
    import requests

    print("Loading SigLIP...")
    model = SentenceTransformer('google/siglip-base-patch16-224')

    labels = [c[1] for c in CATEGORIES]
    text_embs = model.encode(labels, convert_to_tensor=True)
    print(f"Text embeddings: {text_embs.shape}")

    # Get sample of products to classify
    rows = query("""
        SELECT id, platform, title, category_l1, image_urls[1] as img
        FROM products
        WHERE is_active=true AND image_urls IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 100
    """)
    print(f"Classifying {len(rows)} products...")

    images = []
    valid_ids = []
    valid_titles = []
    valid_l1 = []
    skipped = 0
    for r in rows:
        img = None
        path = r['img']
        if path and path.startswith('/images/'):
            local = '/mnt/ssd/arbitlens/data' + path
            if os.path.exists(local):
                try:
                    img = Image.open(local).convert('RGB')
                except Exception:
                    pass
        elif path and path.startswith('http'):
            try:
                resp = requests.get(path, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content)).convert('RGB')
            except Exception:
                pass
        if img:
            images.append(img)
            valid_ids.append(r['id'])
            valid_titles.append(r['title'])
            valid_l1.append(r['category_l1'])
        else:
            skipped += 1
    print(f"Loaded {len(images)} images, skipped {skipped}")

    if not images:
        return

    img_embs = model.encode(images, convert_to_tensor=True, batch_size=8, show_progress_bar=False)
    sims = (img_embs @ text_embs.T).cpu().numpy()

    correct = 0
    mismatches = []
    for i, (pid, title, actual_l1) in enumerate(zip(valid_ids, valid_titles, valid_l1)):
        top3 = sims[i].argsort()[-3:][::-1]
        predicted_label_id = CATEGORIES[top3[0]][0]
        predicted_l1 = LABEL_TO_L1[predicted_label_id]
        match = predicted_l1 == actual_l1
        if match:
            correct += 1
        else:
            mismatches.append((pid, title[:50], actual_l1, predicted_l1, float(sims[i][top3[0]])))

    acc = 100 * correct / len(valid_ids)
    print(f"\n[OK] Accuracy on sample: {correct}/{len(valid_ids)} = {acc:.0f}%")

    if mismatches:
        print(f"\nTop 10 mismatches:")
        for m in mismatches[:10]:
            print(f"  {m[0]}: actual='{m[2]}' predicted='{m[3]}' (conf={m[4]:.2f}) {m[1]}")

    # Per-category stats
    print(f"\nPer-category accuracy:")
    from collections import defaultdict
    cat_stats = defaultdict(lambda: [0, 0])  # [correct, total]
    for i, l1 in enumerate(valid_l1):
        top3 = sims[i].argsort()[-3:][::-1]
        predicted_l1 = LABEL_TO_L1[CATEGORIES[top3[0]][0]]
        cat_stats[l1][1] += 1
        if predicted_l1 == l1:
            cat_stats[l1][0] += 1
    for cat, (c, t) in sorted(cat_stats.items(), key=lambda x: -x[1][1]):
        print(f"  {cat:25} {c:>3}/{t:>3} = {100*c/t:>3.0f}%")


if __name__ == '__main__':
    main()