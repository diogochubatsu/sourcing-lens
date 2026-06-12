"""Drill into ML best sellers hub to find subcategory IDs."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# Categories we care about
targets = ['Audio', 'Casa', 'Fotografia', 'Iluminacao', 'Praia', 'Wearables',
           'Acessorios Moveis', 'Moda Intima', 'Mochilas', 'Bolsas', 'Meias',
           'Fones de Ouvido', 'Microfone', 'Tripé', 'Smartwatch', 'Organizacao']

# Try subcategory best sellers by drilling into top cats
top_cats = {
    '1000': 'Eletrônicos, Áudio e Vídeo',
    '5726': 'Eletrodomésticos',
    '1430': 'Calçados, Roupas e Bolsas',
    '1051': 'Celulares e Telefones',
    '5672': 'Acessórios para Veículos',
    '1276': 'Esportes e Fitness',
    '263532': 'Ferramentas',
    '1246': 'Beleza e Cuidado Pessoal',
}

def find_bs_links(content, name):
    """Find all /mais-vendidos/MLB links in content."""
    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/mais-vendidos/MLB'))
    results = []
    for a in links:
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if isinstance(href, str) and isinstance(text, str):
            m = re.search(r'MLB(\d+)', href)
            if m:
                results.append((m.group(1), text.replace('Ver mais', '').strip()))
    return results

print('=== DRILLING INTO TOP CATEGORIES ===\n')
all_subcats = {}

for cat_id, cat_name in top_cats.items():
    url = f'https://www.mercadolivre.com.br/mais-vendidos/MLB{cat_id}'
    try:
        resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
            'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
        }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=90)
        content = resp.json()['results'][0]['content']
        
        subcats = find_bs_links(content, cat_name)
        print(f'{cat_name} (MLB{cat_id}): {len(subcats)} subcategorias')
        for sub_id, sub_name in subcats[:15]:
            all_subcats.setdefault(cat_name, []).append((sub_id, sub_name))
            print(f'  MLB{sub_id:>8s} — {sub_name}')
        print()
    except Exception as e:
        print(f'{cat_name}: ERRO {e}\n')

# Now search for our target keywords
print('\n=== TARGET CATEGORY SEARCH ===')
for parent, subcats in all_subcats.items():
    for sub_id, sub_name in subcats:
        sub_lower = sub_name.lower()
        for target in targets:
            if target.lower() in sub_lower:
                print(f'  ✅ {target:20s} → MLB{sub_id} ({sub_name}) [em {parent}]')
