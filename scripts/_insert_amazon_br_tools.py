"""Insert scraped Amazon BR products for Ferramentas."""
import json, re, os, sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning

# Products from Amazon BR best sellers: Ferramentas Manuais Automotivas (19702105011)
products = [
  {"asin": "B0DMNSJQ6D", "title": "CENFORGE Bomba extratora de óleo a vácuo pneumática/manual de 6,5L", "price": "R$ 655,90", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/8187QEc9OML._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DV71D4FQ", "title": "CHAVE SACA FILTRO CINTA REGULAVEL DE 60MM A 120MM UNIVERSAL", "price": "R$ 27,81", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/41YKDYf-WjL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B00NFAOCVU", "title": "POWERTEC Rolo J de cabo longo de 30,5 cm", "price": "R$ 135,10", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51yB3wOZquL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0FX3CR53M", "title": "Suporte Organizador de Pistola de Funilaria e Pintura Automotiva HLVP", "price": "R$ 19,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/41Nq7vhOfvL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0FT9S8JWC", "title": "Saca Filtro de Óleo Tipo Cinta Ajustável 25 a 160mm", "price": "R$ 32,99", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61SgjEvgYxL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DHGYVF1M", "title": "etoolab Chave de torque de 3/20.3 cm", "price": "R$ 212,18", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61LIXWJkkVL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07W9BTN6G", "title": "LUMITECO Rolamentos equipados com rolo de roda", "price": "R$ 94,59", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61gDtUKMdkL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0B8QWZ9J5", "title": "XINMEIWEN 2 pecas de rolo de amortecimento de som", "price": "R$ 92,79", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/41UR6ejuYrL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B08828FMSJ", "title": "KingTony BR Chave De Apoio 6 (150Mm) Encaixe 1/4", "price": "R$ 13,87", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/21-NbWonI1L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07RFPMTM5", "title": "Alavanca Para Mecanico, Vonder", "price": "R$ 87,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/31BEXOT3voL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076QDN7VS", "title": "Chave Estriada 22 Mm Aberta para Sonda Lambda, Raven", "price": "R$ 89,16", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71T1rZdk21L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0779MRYJZ", "title": "KingTony BR Soquete Estriado 5/8-1/2", "price": "R$ 18,78", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51GYdMj9olL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07791G9Q3", "title": "KingTony BR Soquete Estriado 7/16-1/2", "price": "", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61A7IeJvJ4L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07KKDQ5HW", "title": "Soquete Estriado 3/8 - 1/2, Kingtony Br", "price": "R$ 19,89", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61A7IeJvJ4L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0FTXK6LKW", "title": "Saca Filtro de Oleo Universal Tipo Aranha 3 Garras", "price": "R$ 55,99", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61a-Z0qoxxL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07HCY9NGH", "title": "Vonder, Tasso Para Chapeador, Modelo Cunha", "price": "R$ 58,49", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51C6+S4J0GL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B008N7WGMC", "title": "Chave de Vela 14 x 1/2, RAVEN", "price": "R$ 87,10", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51+cIjzuQvL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0FHFVH9L1", "title": "DANGKIY Chave de torque de 1/10.2 cm", "price": "R$ 169,04", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71LwjDAZviL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0GT9NH838", "title": "Chave Saca Braco Axial Caixa de Direcao 27 a 42mm", "price": "", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61kpLu4ykmL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DD5SRQLN", "title": "Mandril de Aco Aperto Rapido Metalico 0.8mm a 10mm", "price": "", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71C9nDTmwGL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DGB4V2SR", "title": "Capri Tools Adaptador de torque de 19 mm", "price": "R$ 130,47", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51LLdU582IL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0G5Q2RH7T", "title": "JBL Power Sport Speaker Stadium Rallybar XL BR", "price": "R$ 5499,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/519mSyT39TL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B01M1D17AW", "title": "EPAuto Chave de torque de 1/5.1 cm", "price": "R$ 352,35", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/81aHYhNRfAL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07BDPLHD9", "title": "Ferramenta para Sincronismo Ford Ka, Raven", "price": "R$ 191,91", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/612tBnmf5wL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0F38BR1X7", "title": "Rolo de pressao de papel de parede com costura", "price": "R$ 14,93", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/514OUtKM5rL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07BNKVHXW", "title": "Vonder, Chave De Corrente, Uso Leve", "price": "R$ 51,45", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51ZX6yokYTL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DGGQ8914", "title": "Kolvoii Kit restaurador de rosca de 61 pecas", "price": "R$ 687,87", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71NuUPZquhL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B00INXZI0S", "title": "Chave L para Soltar Bojao de Oleo 8 X 10Mm, Kingtony", "price": "R$ 55,31", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/418sHaKmZhL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DCGM9VRN", "title": "2 Rolos de Filme Multiuso Com Manopla Embalagem Volante", "price": "R$ 42,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51boHUeNYoL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07BDNS4V7", "title": "Ferramenta com Duas Garras de 75 Mm para Rolamento", "price": "R$ 143,15", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/617B2RiVakL._AC_UL600_SR600,400_.jpg"},
]

def parse_price(s):
    if not s:
        return None
    s = s.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(s)
    except:
        return None

inserted = 0
skipped = 0
for p in products:
    # Check if already exists
    existing = query("SELECT id FROM products WHERE platform=%s AND platform_id=%s",
                     ('amazon_br', p['asin']))
    if existing:
        skipped += 1
        continue
    
    price = parse_price(p['price'])
    img_urls = [p['imgUrl']] if p['imgUrl'] else []
    full_url = f'https://www.amazon.com.br/dp/{p["asin"]}'
    
    try:
        execute_returning(
            """INSERT INTO products 
            (platform, platform_id, title, price, image_urls, sales_30d, 
             category_l1, category_l2, category_l3, url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            RETURNING id""",
            ('amazon_br', p['asin'], p['title'][:200], price, img_urls, None,
             'Ferramentas', 'Ferramentas', 'Ferramentas', full_url)
        )
        inserted += 1
    except Exception as e:
        print(f'  Error {p["asin"]}: {e}')

print(f'Inserted: {inserted}, Skipped: {skipped}')
