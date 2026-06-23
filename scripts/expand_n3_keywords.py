#!/usr/bin/env python3
"""
expand_n3_keywords.py — Expand N3 taxonomy keywords to improve classification.

Usage:
  python3 expand_n3_keywords.py --dry-run  # Show what would be updated
  python3 expand_n3_keywords.py --apply    # Apply updates to database
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

# N3 keyword expansions - more specific keywords for subcategories
N3_KEYWORD_EXPANSIONS = {
    # N3: audio.microfones.lapela_fio - wired lavalier
    "audio.microfones.lapela_fio": [
        "wired lavalier", "lapela com fio", "lavalier wired",
        "clip mic", "microfone clipe", "collar mic",
        "3.5mm mic", "trrs mic", "smartphone mic"
    ],
    
    # N3: audio.microfones.lapela_sem_fio - wireless lavalier
    "audio.microfones.lapela_sem_fio": [
        "wireless lavalier", "lapela sem fio", "bluetooth lavalier",
        "2.4ghz lavalier", "uhf lavalier", "digital wireless",
        "compact wireless mic", "mini wireless mic"
    ],
    
    # N3: audio.microfones.condensador - condenser mic
    "audio.microfones.condensador": [
        "condenser mic", "microfone condensador", "cardioid mic",
        "studio mic", "podcast mic", "streaming mic",
        "usb condenser", "xlr condenser", "large diaphragm"
    ],
    
    # N3: audio.microfones.shotgun - shotgun mic
    "audio.microfones.shotgun": [
        "shotgun mic", "boom mic", "camera mic", "video mic",
        "directional mic", "on-camera mic", "interview mic",
        "røde", "deity", "sennheiser"
    ],
    
    # N3: audio.fones.tws - true wireless
    "audio.fones.tws": [
        "tws", "true wireless", "wireless earbuds",
        "bluetooth earbuds", "noise cancelling earbuds",
        "sport earbuds", "gaming earbuds", "stem earbuds"
    ],
    
    # N3: audio.fones.over_ear - over ear headphones
    "audio.fones.over_ear": [
        "over ear", "over-ear", "circumaural", "full size",
        "noise cancelling headphones", "wireless headphones",
        "bluetooth headphones", "studio headphones", "gaming headset"
    ],
    
    # N3: audio.caixas_som.bt_portatil - portable bluetooth speaker
    "audio.caixas_som.bt_portatil": [
        "portable bluetooth", "bluetooth speaker", "wireless speaker",
        "outdoor speaker", "waterproof speaker", "party speaker",
        "mini speaker", "travel speaker", "camping speaker"
    ],
    
    # N3: eletronicos.carregadores.power_bank - power bank
    "eletronicos.carregadores.power_bank": [
        "power bank", "portable charger", "bateria externa",
        "external battery", "fast charge power bank",
        "magsafe power bank", "solar power bank"
    ],
    
    # N3: eletronicos.carregadores.carregador_parede - wall charger
    "eletronicos.carregadores.carregador_parede": [
        "wall charger", "carregador parede", "fast charger",
        "quick charge", "pd charger", "gan charger",
        "multi port charger", "usb charger"
    ],
    
    # N3: eletronicos.cabos.usb_c - usb-c cable
    "eletronicos.cabos.usb_c": [
        "usb-c", "type-c", "usb type c", "usb c cable",
        "fast charging cable", "data cable", "braided cable",
        "right angle usb-c", "retractable usb-c"
    ],
    
    # N3: eletronicos.acessorios_celular.capa_celular - phone case
    "eletronicos.acessorios_celular.capa_celular": [
        "phone case", "capa celular", "silicone case",
        "clear case", "armor case", "wallet case",
        "magsafe case", "shockproof case", "slim case"
    ],
    
    # N3: wearables.relogios.smartwatch - smartwatch
    "wearables.relogios.smartwatch": [
        "smartwatch", "smart watch", "relógio inteligente",
        "fitness watch", "sport watch", "gps watch",
        "health watch", "android watch", "amazfit"
    ],
    
    # N3: wearables.pulseiras.smart_band - smart band
    "wearables.pulseiras.smart_band": [
        "smart band", "fitness band", "mi band",
        "xiaomi band", "activity tracker", "fitness tracker",
        "sleep tracker", "heart rate band"
    ],
    
    # N3: camera.webcam.webcam_hd - hd webcam
    "camera.webcam.webcam_hd": [
        "hd webcam", "1080p webcam", "full hd webcam",
        "streaming webcam", "video call camera",
        "logitech webcam", "autofocus webcam"
    ],
    
    # N3: camera.seguranca.camera_wifi - wifi security camera
    "camera.seguranca.camera_wifi": [
        "wifi camera", "wireless security camera",
        "ip camera wifi", "smart camera", "home camera",
        "indoor camera", "outdoor camera", "ptz camera"
    ],
    
    # N3: beleza.maquiagem.batom - lipstick
    "beleza.maquiagem.batom": [
        "lipstick", "batom", "lip gloss", "lip tint",
        "liquid lipstick", "matte lipstick", "gloss labial"
    ],
    
    # N3: beleza.cabelo.secador - hair dryer
    "beleza.cabelo.secador": [
        "hair dryer", "secador", "blow dryer",
        "ionic dryer", "professional dryer", "travel dryer",
        "conair dryer", "dyson dryer"
    ],
    
    # N3: esportes.academia.yoga_mat - yoga mat
    "esportes.academia.yoga_mat": [
        "yoga mat", "tapete yoga", "exercise mat",
        "fitness mat", "pilates mat", "workout mat",
        "non slip mat", "thick yoga mat"
    ],
    
    # N3: esportes.academia.halteres - dumbbells
    "esportes.academia.halteres": [
        "dumbbells", "halteres", "hand weights",
        "adjustable dumbbells", "neoprene dumbbells",
        "vinyl dumbbells", "chrome dumbbells"
    ],
    
    # N3: casa.organizacao - organization
    "casa.organizacao": [
        "organizer", "organizador", "storage box",
        "drawer organizer", "closet organizer",
        "shelf organizer", "hanging organizer"
    ],
    
    # N3: ferramentas.eletricas.furadeira - drill
    "ferramentas.eletricas.furadeira": [
        "drill", "furadeira", "cordless drill",
        "power drill", "impact drill", "hammer drill",
        "electric drill", "rotary drill"
    ],
    
    # N3: moda.bolsas.bolsa_costas - backpack
    "moda.bolsas.bolsa_costas": [
        "backpack", "mochila", "school bag",
        "laptop backpack", "travel backpack",
        "anti theft backpack", "waterproof backpack"
    ],
    
    # N3: moda.oculos.oculos_sol - sunglasses
    "moda.oculos.oculos_sol": [
        "sunglasses", "óculos de sol", "aviator sunglasses",
        "polarized sunglasses", "uv400 sunglasses",
        "sport sunglasses", "oversized sunglasses"
    ],
}

def expand_n3_keywords(dry_run=True):
    """Add additional keywords to N3 taxonomy entries."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    updated = 0
    
    for slug, new_keywords in N3_KEYWORD_EXPANSIONS.items():
        # Get current keywords
        cursor.execute("SELECT keywords FROM taxonomy WHERE slug = %s", (slug,))
        row = cursor.fetchone()
        if not row:
            print(f"  ⚠️  {slug}: not found in taxonomy")
            continue
        
        current_keywords = row[0] or []
        
        # Add new keywords (avoid duplicates)
        merged = list(set(current_keywords + new_keywords))
        added = len(merged) - len(current_keywords)
        
        if added > 0:
            if dry_run:
                print(f"  📝 {slug}: +{added} keywords")
            else:
                cursor.execute(
                    "UPDATE taxonomy SET keywords = %s WHERE slug = %s",
                    (merged, slug)
                )
                print(f"  ✅ {slug}: +{added} keywords")
            updated += 1
    
    if not dry_run:
        conn.commit()
        print(f"\n✅ Updated {updated} N3 taxonomy entries")
    else:
        print(f"\n📝 Dry run: would update {updated} N3 entries")
        print("   Run with --apply to apply changes")
    
    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Expand N3 taxonomy keywords')
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    
    if args.apply:
        expand_n3_keywords(dry_run=False)
    else:
        expand_n3_keywords(dry_run=True)

if __name__ == '__main__':
    main()
