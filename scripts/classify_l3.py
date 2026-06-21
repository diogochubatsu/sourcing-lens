"""Auto-classify L3 for flat categories (Bolsas, Moda) using keyword rules."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# Rules: (category_l1, current_l2, current_l3, new_l2, new_l3) based on title keywords
BOLSAS_RULES = {
    'mala': ('Mala', 'Viagem'),
    'bordo': ('Mala', 'Bordo'),
    'necessaire': ('Necessaire', 'Viagem'),
    'isotermica': ('Necessaire', 'Térmica'),
    'mochila': ('Mochila', 'Feminina'),
    'bolsa feminina': ('Bolsa', 'Feminina'),
    'bolsa de ombro': ('Bolsa', 'Ombro'),
    'bolsa transversal': ('Bolsa', 'Transversal'),
    'tote': ('Bolsa', 'Tote'),
    'clutch': ('Bolsa', 'Festa'),
    'sacola': ('Bolsa', 'Sacola'),
    'kit bolsa': ('Bolsa', 'Kit'),
    'balanca': ('Acessório', 'Balança'),
    'cadeado': ('Acessório', 'Cadeado'),
}

MODA_RULES = {
    # Vestuário
    'blusa': ('Vestuário', 'Blusa'),
    'calca': ('Vestuário', 'Calça'),
    'calça': ('Vestuário', 'Calça'),
    'camisa': ('Vestuário', 'Camisa'),
    'jaqueta': ('Vestuário', 'Jaqueta'),
    'pijama': ('Vestuário', 'Pijama'),
    'kigurumi': ('Vestuário', 'Pijama'),
    'macacao': ('Vestuário', 'Pijama'),
    'macacão': ('Vestuário', 'Pijama'),
    'tenis': ('Calçado', 'Tênis'),
    'tênis': ('Calçado', 'Tênis'),
    'chinelo': ('Calçado', 'Chinelo'),
    'havaianas': ('Calçado', 'Chinelo'),
    # Acessórios
    'bone': ('Acessório', 'Boné'),
    'boné': ('Acessório', 'Boné'),
    'chapeu': ('Acessório', 'Chapéu'),
    'chapéu': ('Acessório', 'Chapéu'),
    'cinto': ('Acessório', 'Cinto'),
    'chaveiro': ('Acessório', 'Chaveiro'),
    'lenço': ('Acessório', 'Lenço'),
    'lenco': ('Acessório', 'Lenço'),
    'gravata': ('Acessório', 'Gravata'),
    'mascara': ('Acessório', 'Máscara'),
    'máscara': ('Acessório', 'Máscara'),
    'carteira': ('Carteira', 'Masculina'),
    # Casa
    'toalha': ('Casa', 'Banho'),
    'espelho': ('Casa', 'Espelho'),
    'guarda chuva': ('Casa', 'Guarda-Chuva'),
    'guarda-chuva': ('Casa', 'Guarda-Chuva'),
}

def classify(title, rules):
    """Find first matching rule for title."""
    t = title.lower()
    for kw, (l2, l3) in rules.items():
        if kw in t:
            return l2, l3
    return None, None

def main():
    stats = {'bolsas': {'updated': 0, 'unchanged': 0}, 'moda': {'updated': 0, 'unchanged': 0}}

    # Bolsas
    rows = query("SELECT id, title, category_l1, category_l2, category_l3 FROM products WHERE is_active=true AND category_l1='Bolsas'")
    for r in rows:
        l2, l3 = classify(r['title'], BOLSAS_RULES)
        if l2 and l3:
            execute("UPDATE products SET category_l2=%s, category_l3=%s WHERE id=%s", (l2, l3, r['id']))
            stats['bolsas']['updated'] += 1
        else:
            stats['bolsas']['unchanged'] += 1
    print(f"Bolsas: {stats['bolsas']}")

    # Moda
    rows = query("SELECT id, title FROM products WHERE is_active=true AND category_l1='Moda'")
    for r in rows:
        l2, l3 = classify(r['title'], MODA_RULES)
        if l2 and l3:
            execute("UPDATE products SET category_l2=%s, category_l3=%s WHERE id=%s", (l2, l3, r['id']))
            stats['moda']['updated'] += 1
        else:
            stats['moda']['unchanged'] += 1
    print(f"Moda: {stats['moda']}")

if __name__ == '__main__':
    main()