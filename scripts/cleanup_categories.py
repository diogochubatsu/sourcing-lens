#!/usr/bin/env python3
"""
Clean up old L2/L3 values that don't match the new taxonomy.

For each L1, map old (l2, l3) → new (l2, l3) using a lookup table.
This is a 2nd-pass after categorize_products.py.

Usage:
    python3 scripts/cleanup_categories.py --dry-run   # preview
    python3 scripts/cleanup_categories.py             # apply
"""
import os
import sys
import psycopg2
import psycopg2.extras
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import TAXONOMY

os.environ['PGPASSFILE'] = '/tmp/.pgpass'

# ── Cleanup map: (old_l1, old_l2, old_l3) → (new_l2, new_l3) ──
# Or (old_l1, ANY_L2, old_l3) → (new_l2, new_l3) using None for any
CLEANUP_MAP = {
    # Audio
    ("Audio", "Headphones", "Bluetooth"): ("Fones", "Fone Bluetooth"),
    ("Audio", "Headphones", "Portáteis"): ("Fones", "Headset"),  # not perfect but ok
    ("Audio", "Speakers", "Portáteis"): ("Caixas de Som", "Portátil"),
    ("Audio", "Speakers", "Bluetooth"): ("Caixas de Som", "Portátil"),
    ("Audio", "Speakers", "Geral"): ("Caixas de Som", "Portátil"),
    # Bebê
    ("Bebê", "Bebê", "Geral"): (None, "Geral"),  # Drop old L2
    ("Bebê", None, "Geral"): (None, "Geral"),  # Keep
    # Beleza
    ("Beleza", "Beleza", "Geral"): (None, "Geral"),  # Drop old L2
    # Bolsas
    ("Bolsas", "Bolsas", "Bolsas"): (None, "Geral"),  # Generic
    ("Bolsas", "Bolsas", "Geral"): (None, "Geral"),
    ("Bolsas", "Mala", "Viagem"): ("Viagem", "Mala Bordo"),
    ("Bolsas", "Mochila", "Feminina"): ("Feminina", "Mochila Feminina"),
    # Brinquedos
    ("Brinquedos", "Brinquedos", "Geral"): (None, "Geral"),
    # Casa
    ("Casa", "Organização", "Casa"): (None, "Geral"),
    ("Casa", "Organização", "Organização"): (None, "Geral"),
    ("Casa", "Organização", "Copos Térmicos"): ("Cozinha", "Copo"),
    ("Casa", "Casa", "Casa"): (None, "Geral"),
    # Cozinha
    ("Cozinha", "Cozinha", "Utensílios"): ("Utensílios", "Utensílios"),
    ("Cozinha", "Cozinha", "Geral"): (None, "Geral"),
    # Esportes
    ("Esportes", "Rastreadores", "GPS/Tag"): ("Localizadores", "Smart Tag"),
    # Ferramentas
    ("Ferramentas", "Automotivas", "Manual"): ("Manuais", "Jogo de Ferramentas"),
    ("Ferramentas", "Automotivas", "Geral"): ("Manuais", "Jogo de Ferramentas"),
    ("Ferramentas", "Ferramentas", "Ferramentas"): (None, "Geral"),
    # Iluminação
    ("Iluminação", "LED Panels", "Luz Contínua"): ("Painel LED", "Estúdio"),
    ("Iluminação", "Ring Lights", "Selfie/Stream"): ("Ring Light", "Médio"),
    # Meias, Mochilas
    ("Meias", "Meias", "Meias"): (None, "Geral"),
    ("Mochilas", "Mochilas", "Mochilas"): (None, "Geral"),
    # Moda
    ("Moda", "Carteira", "Masculina"): (None, "Geral"),  # Wallets - skip
    ("Moda", "Moda", "Moda"): (None, "Geral"),
    # Moda Intima
    ("Moda Intima", "Moda Intima", "Moda Intima"): (None, "Geral"),
    # Pet Shop
    ("Pet Shop", "Pet Shop", "Pet Shop"): (None, "Geral"),
    # Praia
    ("Praia", "Prendedores", "Cadeira/Toalha"): ("Acessórios", "Clips"),
    # Wearables
    ("Wearables", "Smartwatches", "Geral"): ("Smartwatch", "Outros"),
}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = psycopg2.connect(host="localhost", database="arbtbr", user="hermes1688")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Find all products with old (l2, l3) that need cleanup
    updates = []
    for (l1, old_l2, old_l3), (new_l2, new_l3) in CLEANUP_MAP.items():
        where = "is_active=true AND category_l1 = %s"
        params = [l1]
        if old_l2 is None:
            where += " AND category_l2 IS NULL"
        else:
            where += " AND category_l2 = %s"
            params.append(old_l2)
        if old_l3 is None:
            where += " AND category_l3 IS NULL"
        else:
            where += " AND category_l3 = %s"
            params.append(old_l3)

        cur.execute(f"SELECT id, title, category_l2 as cur_l2, category_l3 as cur_l3 FROM products WHERE {where}", params)
        rows = cur.fetchall()
        for r in rows:
            updates.append({
                'id': r['id'],
                'title': r['title'][:60] if r['title'] else '',
                'l1': l1, 'old_l2': r['cur_l2'], 'old_l3': r['cur_l3'],
                'new_l2': new_l2, 'new_l3': new_l3,
            })

    print(f"Will clean up {len(updates)} products")

    if updates:
        # Show breakdown
        from collections import Counter
        by_change = Counter((u['l1'], u['old_l2'], u['old_l3'], u['new_l2'], u['new_l3']) for u in updates)
        for (l1, ol2, ol3, nl2, nl3), n in sorted(by_change.items(), key=lambda x: -x[1])[:20]:
            print(f"  {l1} | {ol2!r:>15} | {ol3!r:>20} → {nl2!r:>15} | {nl3!r:>20}  ({n})")

    if args.dry_run:
        print("\n[DRY RUN] No changes")
        return

    if not updates:
        print("Nothing to do")
        return

    # Apply
    for u in updates:
        cur.execute("""
            UPDATE products
            SET category_l2 = %s, category_l3 = %s
            WHERE id = %s
        """, (u['new_l2'], u['new_l3'], u['id']))
    conn.commit()
    print(f"\n✓ Updated {len(updates)} products")


if __name__ == "__main__":
    main()
