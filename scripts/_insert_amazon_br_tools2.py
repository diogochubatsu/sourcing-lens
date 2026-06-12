"""Insert batch 2 of Amazon BR tools products."""
import json, sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute_returning

products = [
  {"asin": "B09V1SM8QB", "title": "WAP Parafusadeira e Furadeira a Bateria 12V BPF-12K3", "price": "R$ 205,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/81hJD-odFeL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0GMYQN74L", "title": "Furadeira e Parafusadeira de Impacto Sem Fio com LED", "price": "R$ 111,36", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61FT94WfQeL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0F2JMYPQ9", "title": "WAP Parafusadeira Furadeira de Impacto a Bateria 3/8 12V WF 12K4.2", "price": "R$ 129,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71Bnm202WgL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076N2S8FV", "title": "Sparta Maleta de ferramentas kit com 129 pecas", "price": "R$ 91,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61ZmjmMLsRL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07CV2JXNH", "title": "WD-40 Formula Original - Produto Multiusos Aerossol 300ml", "price": "R$ 38,23", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/41QHjZtHueL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0FP9FF295", "title": "Calibrador Compressor Bomba De Ar Portatil Digital Mini", "price": "R$ 79,90", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51RHJAuAPmL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B08XQWLDKP", "title": "Bosch Furadeira Parafusadeira GSR 1000 Smart 12V", "price": "R$ 313,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61nXSgxFHeL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0778XFVHN", "title": "Vonder Trena Curta De Aco 5 M X 19 Mm", "price": "R$ 14,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71Y14RKTJBL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DXRY7HDS", "title": "Calibrador Portatil Compressor Bomba De Ar Digital", "price": "R$ 69,90", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51GVX-wEbrL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076BB1XPG", "title": "Electrolux Aspirador agua po compacto 1400W 12L", "price": "R$ 231,45", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61X0GXT93RL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0GRP4X66Z", "title": "Multimetro Digital Profissional Auto Range", "price": "R$ 28,99", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61BP6Tl1JDL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B092SPZFYT", "title": "Conjunto de chaves de fenda de precisao 115 em 1", "price": "R$ 26,29", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/713vuYqQbsS._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07CTN73L1", "title": "Bosch Kit de pontas e brocas V-Line 41 pecas", "price": "R$ 115,81", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61tv+b6beQL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07CTM3VSN", "title": "Bosch Kit de pontas para parafusar Mini X-Line 25 pecas", "price": "R$ 48,78", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71ZiGA-2v4L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076ZRKZK1", "title": "Nivel Plastico Com Base Magnetica 9 Vonder", "price": "R$ 14,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61R3IbQOPIL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07BJDL3K1", "title": "Trena Aco P 5M X 19 Mm Auto Trava Vonder", "price": "R$ 22,50", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51pb4EIXIbL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0CBGGBJJ2", "title": "Kit 46 Chave Catraca Jogo De Soquetes Allen Torx", "price": "R$ 22,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71IaidXhgEL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0DB61V6L6", "title": "WAP Parafusadeira e Furadeira a Bateria Li-Ion 12V BPF 12K3 BLACK", "price": "R$ 143,90", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/71xBTN94fpL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0GYSZ97Q8", "title": "Compressor de Ar Portatil Premium Mini Calibrador", "price": "", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61Tmq6FwkzL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076XQLJNL", "title": "Vonder Rebitador Manual Tipo Alicate Rm 244", "price": "R$ 22,30", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/41gPd+MmvJL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0778TV2PQ", "title": "Tramontina Broca para Aco 1/16X43Mm", "price": "R$ 3,52", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/31nuzJdhNwL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B077VW15YL", "title": "Furadeira e Parafusadeira a Bateria Mondial 12V FPF-06M", "price": "R$ 138,90", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/81f0lP0WdIL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0778YTF29", "title": "MTX Alicate Bico Meia Cana 6 Pol 160 mm", "price": "R$ 14,80", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/612JNRbsHoL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B07QZSKWR4", "title": "EDA Chave De Fenda Jogo Com 5 Pecas Excellent", "price": "R$ 10,76", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/716RfX5g+5L._AC_UL600_SR600,400_.jpg"},
  {"asin": "B09QRQQY4S", "title": "Bosch Esmerilhadeira GWS 700 710W 220V", "price": "R$ 285,96", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51AqxXxZ6XL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B0779GTMTB", "title": "MTX Martelo de Unha Magnetico 450 g", "price": "R$ 28,10", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51daMYctfuL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076KP7X7F", "title": "Tramontina Alicate Universal 8 Isolado", "price": "R$ 33,79", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/51MGPcAcbUL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B076YK72YJ", "title": "Caixa Para Ferramentas Plastica 34x34x13 Vonder", "price": "R$ 23,60", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/61AQALBtTCL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B09ML23TTF", "title": "Saint Chave Multifuncional Instalador Hidraulico", "price": "R$ 17,00", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/6111QOW+MCL._AC_UL600_SR600,400_.jpg"},
  {"asin": "B08YRLZCPJ", "title": "Conjunto com 46 chaves catraca Egofine", "price": "R$ 26,49", "imgUrl": "https://images-na.ssl-images-amazon.com/images/I/81vDzUYxbyL._AC_UL600_SR600,400_.jpg"},
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
    existing = query("SELECT id FROM products WHERE platform=%s AND platform_id=%s", ('amazon_br', p['asin']))
    if existing:
        skipped += 1
        continue
    price = parse_price(p['price'])
    img_urls = [p['imgUrl']] if p['imgUrl'] else []
    full_url = 'https://www.amazon.com.br/dp/' + p['asin']
    try:
        execute_returning(
            """INSERT INTO products (platform, platform_id, title, price, image_urls, sales_30d, category_l1, category_l2, category_l3, url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""",
            ('amazon_br', p['asin'], p['title'][:200], price, img_urls, None,
             'Ferramentas', 'Ferramentas', 'Ferramentas', full_url)
        )
        inserted += 1
    except Exception as e:
        print(f'  Error {p["asin"]}: {e}')

print(f'Inserted: {inserted}, Skipped: {skipped}')
