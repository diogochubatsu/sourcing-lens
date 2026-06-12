"""Insert ML fashion products from browser extraction."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute_returning

def classify_fashion(title):
    t = title.lower()
    if any(w in t for w in ['meia calca', 'meias', 'meia termica']):
        return 'Meias'
    if any(w in t for w in ['cueca', 'boxer', 'calcinha', 'suti', 'moda intima', 'lingerie']):
        return 'Moda Intima'
    if any(w in t for w in ['mochila']):
        return 'Mochilas'
    if any(w in t for w in ['bolsa', 'mala']):
        return 'Bolsas'
    if any(w in t for w in ['pijama', 'camisa', 'camiseta', 'blusa', 'calc', 'jaqueta', 'tenis', 'chinelo', 'havaiana', 'legging', 'vestido', 'short', 'bermuda', 'casaco']):
        return 'Moda'
    return 'Moda'

products = [
    ('MLB4004879205', 'Meia Calca De La Termica Translucida Pelucia Forrada Pelinho', 29.09, 100000, 'https://http2.mlstatic.com/D_Q_NP_2X_807585-MLB86376377902_062025-AB-meia-calca-de-l-termica-translucida-pelucia-forrada-pelinho.webp'),
    ('MLB3239976866', 'Kit 6 Pares Meias Puma Cano Medio Alto Atoalhada Original', 69.99, 250000, 'https://http2.mlstatic.com/D_Q_NP_2X_617361-MLB54128842596_032023-AB-kit-6-pares-meias-puma-cano-medio-alto-atoalhada-original.webp'),
    ('MLB2070063236', 'Calca Jeans Masculina Original Elastano Lycra', 44.90, 250000, 'https://http2.mlstatic.com/D_Q_NP_2X_736480-MLB110617161021_042026-AB-calca-jeans-masculina-original-elastano-lycra.webp'),
    ('MLB4182420507', 'Calca Legging Leg Flare Zero Transparencia Academia', 34.90, 50000, 'https://http2.mlstatic.com/D_Q_NP_2X_658388-MLB90869609638_082025-AB-calca-legging-leg-flare-zero-transparncia-grossa-academia.webp'),
    ('MLB4348056327', 'Kit 10 Cueca Boxer Masculina Microfibra Premium', 44.99, 50000, 'https://http2.mlstatic.com/D_Q_NP_2X_655135-MLB100011715022_122025-AB-kit-10-cueca-boxer-masculina-microfibra-adulto-premium.webp'),
    ('MLB3833090845', 'Camisa Social Feminina Classica Listrada', 37.99, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_824323-MLB111193232159_052026-AB-camisa-social-feminina-classica-listrada-c-botoes-tendncia.webp'),
    ('MLB4456307736', 'Blusa De Frio Moletom Estilo Canguru Com Capuz', 53.99, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_682101-MLB104849231103_012026-AB-blusa-de-frio-moletom-estilo-canguru-com-capuz-bolso-macio.webp'),
    ('MLB4048023292', 'Calca Jeans Plus Size Cintura Alta Elastano Lycra', 61.90, 100000, 'https://http2.mlstatic.com/D_Q_NP_2X_793061-MLB104104764674_012026-AB-calca-jeans-plus-size-cintura-alta-elastano-lycra-modeladora.webp'),
    ('MLB4155061189', 'Jaqueta Bobojaco Feminina Puffer Impermeavel', 92.06, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_676587-MLB111990325425_052026-AB-jaqueta-bobojaco-feminina-puffer-impermeavel-capuz-removivel.webp'),
    ('MLB3746504707', 'Chinelo Havaianas Masculino Top Max Comfort', 49.99, 100000, 'https://http2.mlstatic.com/D_Q_NP_2X_888688-MLB85934048501_062025-AB-chinelo-havaianas-masculino-top-max-comfort-anatmica-macia.webp'),
    ('MLB4359093019', 'Tenis Masculino Casual Aramis Daily Slip', 15.80, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_839947-MLB107523923436_032026-AB-tnis-masculino-casual-aramis-daily-slip-confortavel-moderno.webp'),
    ('MLB3477729725', 'Pijama Macacao Kigurumi Stitch Feminino', 99.90, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_846918-MLB111418650757_052026-AB-pijama-macaco-kigurumi-stitch-feminino-adulto-plush-ziper.webp'),
    ('MLB4330911507', 'Mochila Viagem Executiva Grande Notebook', 116.39, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_880773-MLB99691301191_112025-AB-mochila-viagem-executiva-grande-notebook-masculina-feminina.webp'),
    ('MLB3482047960', 'Jaqueta De Couro Masculino Slim Resistente', 153.60, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_881631-MLB109190399926_042026-AB-jaqueta-de-couro-masculino-slim-resistente.webp'),
    ('MLB5369247714', 'Jaqueta Infantil Juvenil Forrada Puffer', 102.52, 10000, 'https://http2.mlstatic.com/D_Q_NP_2X_768716-MLB83940856540_042025-AB-jaqueta-infantil-juvenil-forrada-puffer-menina-menino-teen.webp'),
]

inserted = 0
skipped = 0
for pid, title, price, sales, img_url in products:
    existing = query("SELECT id FROM products WHERE platform='ml' AND platform_id=%s", (pid,))
    if existing:
        skipped += 1
        continue
    cat = classify_fashion(title)
    try:
        execute_returning(
            """INSERT INTO products (platform,platform_id,title,price,image_urls,sales_30d,category_l1,category_l2,category_l3,url,is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true) RETURNING id""",
            ('ml', pid, title[:200], price, [img_url] if img_url else [], sales,
             cat, cat, cat, 'https://www.mercadolivre.com.br/p/' + pid)
        )
        inserted += 1
    except Exception as e:
        print(f'  Error {pid}: {e}')

print(f'Inserted: {inserted}, Skipped: {skipped}')

# Summary
from scripts.db import query as q
r = q("SELECT category_l1, platform, COUNT(*) as cnt FROM products WHERE is_active=true AND category_l1 IN ('Meias','Moda Intima','Mochilas','Bolsas','Moda') GROUP BY category_l1, platform ORDER BY category_l1")
print('\nFashion categories final:')
for row in r:
    print(f'  {row["category_l1"]:15s} {row["platform"]:10s} {row["cnt"]}')
