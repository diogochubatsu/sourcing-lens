"""Insert batch 3 of Amazon BR tools products."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute_returning

products = [
  ('B0GKH4DGBV', 'Lanterna 928 LED Dispositivo de Seguranca', 64.25, 'https://images-na.ssl-images-amazon.com/images/I/616WhfkATRL._AC_UL600_SR600,400_.jpg'),
  ('B08LP3JV5J', 'MTX Alicate de Pressao 10 Mordente Curvo', 19.60, 'https://images-na.ssl-images-amazon.com/images/I/61urx5dpVmL._AC_UL600_SR600,400_.jpg'),
  ('B076MJZF3S', 'Tramontina Jogo de Chaves de Fenda 6 Pecas', 25.90, 'https://images-na.ssl-images-amazon.com/images/I/81qOUCSi6-L._AC_UL600_SR600,400_.jpg'),
  ('B0FCZNHXXZ', 'Kit Churrasco Premium 8 Pecas', 78.90, 'https://images-na.ssl-images-amazon.com/images/I/71YFz0929XL._AC_UL600_SR600,400_.jpg'),
  ('B0GZ2LVQJC', 'Lanterna 928 LED Auto Defesa Pessoal', 64.90, 'https://images-na.ssl-images-amazon.com/images/I/71tMv3iOL6L._AC_UL600_SR600,400_.jpg'),
  ('B0GWJBSF8X', 'Estecas ceramica fria Kit Ferramentas 30 Pecas', 59.00, 'https://images-na.ssl-images-amazon.com/images/I/61oQAPTLEwL._AC_UL600_SR600,400_.jpg'),
  ('B07791B3XM', 'MTX Jogo de Chave Allen Longa 9 Pecas', 13.90, 'https://images-na.ssl-images-amazon.com/images/I/51FXg3vivuL._AC_UL600_SR600,400_.jpg'),
  ('B077QGCJZP', 'Alicate Vazador Furador Com 6 Bicos', 27.89, 'https://images-na.ssl-images-amazon.com/images/I/41EuCUMc98L._AC_UL600_SR600,400_.jpg'),
  ('B0FNDGG5G9', 'Lanterna LED UV Luz Negra Ultravioleta', 28.90, 'https://images-na.ssl-images-amazon.com/images/I/51kmFH2shTL._AC_UL600_SR600,400_.jpg'),
  ('B0777PD18N', 'EDA Chaves Torx Tipo L Longas 7 Pecas', 15.00, 'https://images-na.ssl-images-amazon.com/images/I/81mJUZX7c1L._AC_UL600_SR600,400_.jpg'),
  ('B0777RQWYG', 'Vonder Raspador Plano Rp 011', 19.60, 'https://images-na.ssl-images-amazon.com/images/I/6168JnogutL._AC_UL600_SR600,400_.jpg'),
  ('B07VF3XT7P', 'Sparta Pistola Para Silicone Semi-Aberta', 13.22, 'https://images-na.ssl-images-amazon.com/images/I/71qJZ5tM2lL._AC_UL600_SR600,400_.jpg'),
  ('B077VNK4CN', 'Sfor Abracadeira de Nylon 100 Pecas', 6.37, 'https://images-na.ssl-images-amazon.com/images/I/61-2G+yrTmL._AC_UL600_SR600,400_.jpg'),
  ('B09NQ913HH', 'EDA Chave Combinada Avulsa Medida 10 Mm', 5.37, 'https://images-na.ssl-images-amazon.com/images/I/71xPj8Il-lL._AC_UL600_SR600,400_.jpg'),
  ('B0GKPXXP8S', 'Jogo de Soquetes e Chaves 58 Pecas', 118.90, 'https://images-na.ssl-images-amazon.com/images/I/71tkWcwQq5L._AC_UL600_SR600,400_.jpg'),
  ('B0C9TZPX5J', 'Jogo De Ferramentas 163 Pecas Vonder', 360.77, 'https://images-na.ssl-images-amazon.com/images/I/81NzamswRGL._AC_UL600_SR600,400_.jpg'),
  ('B0DLBWNF84', 'Alicate Desencapador Automatico 3 em 1', 35.90, 'https://images-na.ssl-images-amazon.com/images/I/61pWN+TWSPL._AC_UL600_SR600,400_.jpg'),
  ('B0GMTWQ6JZ', 'Lanterna T9 Tattica LED Recarregavel', None, 'https://images-na.ssl-images-amazon.com/images/I/71lRNMhlKLL._AC_UL600_SR600,400_.jpg'),
  ('B0GV1KD2X7', 'Lanterna 928 LED Auto Defesa Premium', 66.74, 'https://images-na.ssl-images-amazon.com/images/I/51TWj-Sas8L._AC_UL600_SR600,400_.jpg'),
  ('B0DB8BR668', 'Lanterna Led Recarregavel 10000 Lumens', 116.84, 'https://images-na.ssl-images-amazon.com/images/I/81hOGs57oeL._AC_UL600_SR600,400_.jpg'),
]

inserted = 0
skipped = 0
for asin, title, price, img_url in products:
    existing = query("SELECT id FROM products WHERE platform='amazon_br' AND platform_id=%s", (asin,))
    if existing:
        skipped += 1
        continue
    try:
        execute_returning(
            """INSERT INTO products (platform, platform_id, title, price, image_urls, sales_30d, category_l1, category_l2, category_l3, url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""",
            ('amazon_br', asin, title[:200], price, [img_url] if img_url else [], None,
             'Ferramentas', 'Ferramentas', 'Ferramentas', 'https://www.amazon.com.br/dp/' + asin)
        )
        inserted += 1
    except Exception as e:
        print(f'Error {asin}: {e}')
print(f'Inserted: {inserted}, Skipped: {skipped}')
