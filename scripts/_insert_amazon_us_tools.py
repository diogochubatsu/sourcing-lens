"""Insert Amazon US tools products."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute_returning

products = [
  ('B08JHCVHTY', 'blink plus plan with monthly auto-renewal', 11.99, 'https://images-na.ssl-images-amazon.com/images/I/31YHGbJsldL._AC_UL600_SR600,400_.png'),
  ('B07G2KT7FN', 'Simply 20x20x1 Air Filter Merv 8 6 Pack', 31.95, 'https://images-na.ssl-images-amazon.com/images/I/711VgI5He3L._AC_UL600_SR600,400_.jpg'),
  ('B0787D4CMM', "Rust-Oleum 331182 Painter's Touch 2X Ultra Cover Spray Paint", 5.99, 'https://images-na.ssl-images-amazon.com/images/I/71W4xyMWJ0L._AC_UL600_SR600,400_.jpg'),
  ('B0B27HX6P7', 'TESSAN European Travel Plug Adapter 2 Pack', 24.99, 'https://images-na.ssl-images-amazon.com/images/I/61cl-IrRJbL._AC_UL600_SR600,400_.jpg'),
  ('B0882ZJ48W', 'GE XWFE Refrigerator Water Filter', 49.98, 'https://images-na.ssl-images-amazon.com/images/I/71Z4DYovOvL._AC_UL600_SR600,400_.jpg'),
  ('B00004SU18', 'Brita Standard Water Filter for Pitchers', 17.98, 'https://images-na.ssl-images-amazon.com/images/I/71Sc1WjCZGL._AC_UL600_SR600,400_.jpg'),
  ('B00UXG4WR8', 'everydrop by Whirlpool Refrigerator Water Filter', 57.00, 'https://images-na.ssl-images-amazon.com/images/I/71wDXhHgWoL._AC_UL600_SR600,400_.jpg'),
  ('B0C3SSXL4K', 'Inspire Black Nitrile Gloves HEAVY DUTY 6 Mil', 14.44, 'https://images-na.ssl-images-amazon.com/images/I/71u2II-WKSL._AC_UL600_SR600,400_.jpg'),
  ('B00CJZ8LAK', 'Filterbuy 20x20x1 Air Filter MERV 8 4-Pack', 29.96, 'https://images-na.ssl-images-amazon.com/images/I/71IWOICrJNL._AC_UL600_SR600,400_.jpg'),
  ('B004Q69HIU', 'Filtrete 20x25x1 AC Furnace Air Filter MERV 11', 28.17, 'https://images-na.ssl-images-amazon.com/images/I/71QxuJbM30L._AC_UL600_SR600,400_.jpg'),
  ('B0DFPQ4VY8', 'SWIFTLITE Black Vinyl Gloves Food Grade', 7.99, 'https://images-na.ssl-images-amazon.com/images/I/71d0n-QszAL._AC_UL600_SR600,400_.jpg'),
  ('B071NFVVNG', 'Samsung HAF-QIN/EXP Genuine Refrigerator Water Filter', 38.49, 'https://images-na.ssl-images-amazon.com/images/I/51FTb50X96L._AC_UL600_SR600,400_.jpg'),
  ('B07FP5X3JH', 'Filtrete 20x30x1 Air Filter MERV 5 6-Pack', 27.96, 'https://images-na.ssl-images-amazon.com/images/I/81FmxwYkANL._AC_UL600_SR600,400_.jpg'),
  ('B0FHJ7TKZM', 'Ring Battery Doorbell newest model', 99.99, 'https://images-na.ssl-images-amazon.com/images/I/616Leg1GwuL._AC_UL600_SR600,400_.jpg'),
  ('B0BDF8CVBN', 'MCGOR 10inch Under Cabinet Lighting 2 Pack', 16.99, 'https://images-na.ssl-images-amazon.com/images/I/61x62WLGvNL._AC_UL600_SR600,400_.jpg'),
  ('B009PCI2JU', 'GE RPWFE Refrigerator Water Filter', 49.98, 'https://images-na.ssl-images-amazon.com/images/I/71dfZ714jtL._AC_UL600_SR600,400_.jpg'),
  ('B01MU7973W', 'Brita Elite Water Filter Replacements', 29.78, 'https://images-na.ssl-images-amazon.com/images/I/71+OP0yDXFL._AC_UL600_SR600,400_.jpg'),
  ('B00C7N7L1E', 'ZeroWater Official Replacement Filter', 40.78, 'https://images-na.ssl-images-amazon.com/images/I/71Ltr3pvOmL._AC_UL600_SR600,400_.jpg'),
  ('B0DJ1BVZGX', 'Skrizcable 16/3 25 FT Outdoor Extension Cord', 11.49, 'https://images-na.ssl-images-amazon.com/images/I/71DU0yh7o4L._AC_UL600_SR600,400_.jpg'),
  ('B0D18VS397', 'Inspire Black Nitrile Disposable Gloves 4.5 Mil', 9.99, 'https://images-na.ssl-images-amazon.com/images/I/61QVSsOP3UL._AC_UL600_SR600,400_.jpg'),
  ('B0CNQPKX9B', 'HANYCONY European Travel Plug Adapter USB C', 9.99, 'https://images-na.ssl-images-amazon.com/images/I/412IcQgyAQL._AC_UL600_SR600,400_.jpg'),
  ('B075BMVZ2N', 'Amazon Basics Extension Cord 10 Ft', 6.99, 'https://images-na.ssl-images-amazon.com/images/I/61giskL9XuL._AC_UL600_SR600,400_.jpg'),
  ('B0FBC8ZWDH', 'Ring Chime Enhanced audio alerts', 34.99, 'https://images-na.ssl-images-amazon.com/images/I/614v5hajZbL._AC_UL600_SR600,400_.jpg'),
  ('B0BZWRLRLK', 'Ring Battery Doorbell Home security', 59.99, 'https://images-na.ssl-images-amazon.com/images/I/51TfEjHNQHL._AC_UL600_SR600,400_.jpg'),
  ('B074HLRXMP', 'LG LT1000P Replacement Refrigerator Water Filter', 47.45, 'https://images-na.ssl-images-amazon.com/images/I/619ejfPUKbL._AC_UL600_SR600,400_.jpg'),
  ('B00VBP8QPO', 'everydrop by Whirlpool Refrigerator Filter 2', 53.99, 'https://images-na.ssl-images-amazon.com/images/I/71XeYFXacFL._AC_UL600_SR600,400_.jpg'),
  ('B01D93Z9ZA', 'Felt Furniture Pads X-PROTECTOR 133 PCS', 9.99, 'https://images-na.ssl-images-amazon.com/images/I/81n7OmTSxXL._AC_UL600_SR600,400_.jpg'),
  ('B07JHQ4L4F', 'Pro Grade Paint Brushes 5-Piece Set', 7.99, 'https://images-na.ssl-images-amazon.com/images/I/61KC7YmX0CL._AC_UL600_SR600,400_.jpg'),
  ('B0BPS5QB4D', '4 Rolls Premium Painters Tape Blue Tape', 5.99, 'https://images-na.ssl-images-amazon.com/images/I/71++hSisgmL._AC_UL600_SR600,400_.jpg'),
  ('B0G4BMR5BJ', 'METAONLY Magnetic Screen Door Mesh', 9.42, 'https://images-na.ssl-images-amazon.com/images/I/81Npzz59MyL._AC_UL600_SR600,400_.jpg'),
]

inserted = 0
skipped = 0
for asin, title, price, img_url in products:
    existing = query("SELECT id FROM products WHERE platform='amazon_us' AND platform_id=%s", (asin,))
    if existing:
        skipped += 1
        continue
    try:
        execute_returning(
            """INSERT INTO products (platform, platform_id, title, price, image_urls, sales_30d, category_l1, category_l2, category_l3, url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""",
            ('amazon_us', asin, title[:200], price, [img_url] if img_url else [], None,
             'Ferramentas', 'Ferramentas', 'Ferramentas', 'https://www.amazon.com/dp/' + asin)
        )
        inserted += 1
    except Exception as e:
        print(f'Error {asin}: {e}')
print(f'Inserted: {inserted}, Skipped: {skipped}')
