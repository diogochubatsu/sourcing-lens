"""Insert Amazon BR fashion products, classified into proper categories."""
import sys, re
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute_returning

def classify_fashion(title):
    t = title.lower()
    if any(w in t for w in ['meia', 'meias', 'meia calc', 'soquete']):
        return 'Meias'
    if any(w in t for w in ['cueca', 'calcinha', 'suti', 'boxer', 'body', 'moda intima']):
        return 'Moda Intima'
    if any(w in t for w in ['mochila', 'backpack']):
        return 'Mochilas'
    if any(w in t for w in ['bolsa', 'sacola', 'tiracolo', 'shoulder bag', 'handbag']):
        return 'Bolsas'
    if any(w in t for w in ['pulseira', 'relogio', 'watch']):
        return 'Moda'
    if any(w in t for w in ['camiseta', 'camisa', 'blusa', 'calc', 'tenis', 'chinelo', 'havaiana']):
        return 'Moda'
    return 'Moda'

products = [
    ('B0755PWFSN', 'Bateria de Litio CR2032 Cartela 5 unidades Elgin', 9.48, 'https://images-na.ssl-images-amazon.com/images/I/61V3OakYmRL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B07RML3H5T', 'Kit 6 Pares Meias Lupo Cano Medio Algodao', 59.99, 'https://images-na.ssl-images-amazon.com/images/I/713Ija9xF3L._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0GXTY8SMX', 'Romantic Crown Mochila de Viagem Expansivel', 119.99, 'https://images-na.ssl-images-amazon.com/images/I/61ov9flqL+L._AC_UL600_SR600,400_.jpg', 'Mochilas'),
    ('B000YKMHP2', 'Chinelo Havaianas Top adulto-unissex', 29.40, 'https://images-na.ssl-images-amazon.com/images/I/514+LgOiqQL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0F448CZQY', 'Blusa Termica Manga Longa Feminina Peluciada', 29.90, 'https://images-na.ssl-images-amazon.com/images/I/41-4eWsaA8L._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0BVG5XL4N', 'Kit 6 Pares Meia Cano Medio Atoalhada Puma', 75.40, 'https://images-na.ssl-images-amazon.com/images/I/81dGC-9Qk0L._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0G16ZFTV2', 'Kit 3 Pares Meia Termica Flanelada Fleece', 29.90, 'https://images-na.ssl-images-amazon.com/images/I/71q9WMCX0HL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0BX4M1B9W', 'Kit 3 Meia Termica Grossa Flanelada Fleece', 19.00, 'https://images-na.ssl-images-amazon.com/images/I/419p2SbNHJL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0GWVTZ6ZC', 'Meia Calca Termica Veludo Preta Translucida', 29.90, 'https://images-na.ssl-images-amazon.com/images/I/51yoalZR-PL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B01M2CO8RA', 'Body Pacote 5 bodies manga longa Simple Joys', 154.76, 'https://images-na.ssl-images-amazon.com/images/I/91Ua53sAhnL._AC_UL600_SR600,400_.jpg', 'Moda Intima'),
    ('B0D34P8KXM', 'Kit 9 Pares Meia Puma Invisivel Soquete', 69.99, 'https://images-na.ssl-images-amazon.com/images/I/71-+1GnxaUL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B081FW5STV', 'Kit 10 Pares Meia Soquete Invisivel Algodao', 54.99, 'https://images-na.ssl-images-amazon.com/images/I/71VY1EA4JeL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0GSLD9QZ8', 'Meia Calca Termica Feminina Translucida', 29.49, 'https://images-na.ssl-images-amazon.com/images/I/51VBpIG0WIL._AC_UL600_SR600,400_.jpg', 'Meias'),
    ('B0CW246HNL', 'Kit 12 Cuecas Boxer Reebok Masculinas', 119.99, 'https://images-na.ssl-images-amazon.com/images/I/61vNRjm1dHL._AC_UL600_SR600,400_.jpg', 'Moda Intima'),
    ('B000RMC2J8', 'Chinelo Havaianas Brasil', 44.90, 'https://images-na.ssl-images-amazon.com/images/I/61udmUeNlrL._AC_UL300_SR300,200_.jpg', 'Moda'),
    ('B0BL8R7H32', 'Macacao dormir bebes Pijama algodao Carter', 216.74, 'https://images-na.ssl-images-amazon.com/images/I/91qg13wQRgL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0G44Y87DB', 'Camiseta Infantil Juvenil Unissex Algodao', 49.90, 'https://images-na.ssl-images-amazon.com/images/I/71vxNM1wV+L._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B00YTY4ABI', 'Timex Relogio Easy Reader pulseira couro', 654.72, 'https://images-na.ssl-images-amazon.com/images/I/71mCiiNRwPL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0CL8H7GJL', 'Kit 10 Cuecas Boxer Sandrini Masculinas', 69.99, 'https://images-na.ssl-images-amazon.com/images/I/41YTv9vLp6L._AC_UL600_SR600,400_.jpg', 'Moda Intima'),
    ('B0FFTQ4K1Y', 'Tenis Mizuno City Wall', 199.99, 'https://images-na.ssl-images-amazon.com/images/I/61Nhgc1qyoL._AC_UL300_SR300,200_.jpg', 'Moda'),
    ('B0H2R73LWF', 'Calc Moletom Flanelado Jogger Skinny', 54.90, 'https://images-na.ssl-images-amazon.com/images/I/61Qd5RgSYjL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0D2RKV4JL', 'Camiseta Puma Essentials Masculina', 119.90, 'https://images-na.ssl-images-amazon.com/images/I/515WuKHnXdL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0DLNWN9HP', 'Romantic Crown Bolsa Ombro Pequena Feminina', 69.99, 'https://images-na.ssl-images-amazon.com/images/I/41-rbz1Aj0L._AC_UL600_SR600,400_.jpg', 'Bolsas'),
    ('B0CQDGFNBP', 'Calcinha Absorvente Menstrual Pantys Xodo', 39.90, 'https://images-na.ssl-images-amazon.com/images/I/51DGhK2g8qL._AC_UL600_SR600,400_.jpg', 'Moda Intima'),
    ('B0BHMHWW2K', 'Daily T-shirt Masculino', 149.00, 'https://images-na.ssl-images-amazon.com/images/I/51TL7HhfN4L._AC_UL300_SR300,200_.jpg', 'Moda'),
    ('B0DPLFCTW7', 'Camiseta Palmeiras Home II Masculina', 79.90, 'https://images-na.ssl-images-amazon.com/images/I/610fxs-OuKL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B07ZPQBNS6', 'Macacao dormir bebes Cotton Sleep Play', 141.99, 'https://images-na.ssl-images-amazon.com/images/I/81akbZpB4SL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0GYZL5VCY', 'Camiseta Dry Feminina Brasil Selecao', 79.90, 'https://images-na.ssl-images-amazon.com/images/I/61BYoIrAIbL._AC_UL600_SR600,400_.jpg', 'Moda'),
    ('B0FC858CXJ', 'Kit 6 Cuecas Boxer Lupo Microfibra', 159.99, 'https://images-na.ssl-images-amazon.com/images/I/518ZupQVi7L._AC_UL600_SR600,400_.jpg', 'Moda Intima'),
    ('B0CL9QM731', 'Pulseiras esportivas silicone Apple Watch', 23.97, 'https://images-na.ssl-images-amazon.com/images/I/61eFVWSBhxL._AC_UL600_SR600,400_.jpg', 'Moda'),
]

inserted = 0
skipped = 0
for asin, title, price, img_url, cat in products:
    existing = query("SELECT id FROM products WHERE platform='amazon_br' AND platform_id=%s", (asin,))
    if existing:
        skipped += 1
        continue
    try:
        execute_returning(
            """INSERT INTO products (platform, platform_id, title, price, image_urls, sales_30d, category_l1, category_l2, category_l3, url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""",
            ('amazon_br', asin, title[:200], price, [img_url] if img_url else [], None,
             cat, cat, cat, 'https://www.amazon.com.br/dp/' + asin)
        )
        inserted += 1
    except Exception as e:
        print(f'  Error {asin}: {e}')

print(f'Inserted: {inserted}, Skipped: {skipped}')

# Show breakdown
r = query("SELECT category_l1, COUNT(*) as cnt FROM products WHERE platform='amazon_br' AND category_l1 IN ('Meias','Moda Intima','Mochilas','Bolsas','Moda') AND is_active=true GROUP BY category_l1 ORDER BY category_l1")
print('\nNew Amazon BR categories:')
for row in r:
    print(f'  {row["category_l1"]:20s} {row["cnt"]}')
