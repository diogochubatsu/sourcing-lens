#!/usr/bin/env python3
"""
expand_keywords.py — Expand taxonomy keywords to improve classification accuracy.

This script adds additional keywords to existing taxonomy entries to improve
N2 and N3 classification rates.

Usage:
  python3 expand_keywords.py --dry-run  # Show what would be updated
  python3 expand_keywords.py --apply    # Apply updates to database
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

# Additional keywords to add to existing taxonomy entries
KEYWORD_EXPANSIONS = {
    # N2: audio.microfones - more microphone keywords
    "audio.microfones": [
        "mic", "microfone", "lavalier", "shotgun", "condenser",
        "wireless mic", "bluetooth mic", "usb mic", "xlr mic",
        "podcast", "streaming", "karaoke", "gravador"
    ],
    
    # N2: audio.fones - more headphone keywords
    "audio.fones": [
        "headphone", "earphone", "earbuds", "airpods", "tws",
        "bluetooth headphone", "wired headphone", "noise cancelling",
        "over ear", "in ear", "on ear", "headset"
    ],
    
    # N2: audio.caixas_som - more speaker keywords
    "audio.caixas_som": [
        "speaker", "caixa de som", "bluetooth speaker", "portable speaker",
        "soundbar", "home theater", "subwoofer", "woofer",
        "jbl", "marshall", "bose", "sony speaker"
    ],
    
    # N2: eletronicos.carregadores - more charger keywords
    "eletronicos.carregadores": [
        "charger", "carregador", "power bank", "bateria externa",
        "wireless charger", "fast charger", "quick charge", "pd charger",
        "gan charger", "usb charger", "wall charger", "car charger"
    ],
    
    # N2: eletronicos.cabos - more cable keywords
    "eletronicos.cabos": [
        "cable", "cabo", "usb cable", "type c cable", "lightning",
        "hdmi cable", "adapter", "hub", "dock", "extensor",
        "extensão", "kvm", "switch", "splitter"
    ],
    
    # N2: eletronicos.acessorios_celular - more phone accessory keywords
    "eletronicos.acessorios_celular": [
        "phone case", "capa celular", "phone holder", "phone stand",
        "screen protector", "película", "temperado", "ring holder",
        "pop socket", "grip", "mount", "suporte celular"
    ],
    
    # N2: wearables.relogios - more watch keywords
    "wearables.relogios": [
        "smartwatch", "watch", "relógio", "smart watch",
        "apple watch", "galaxy watch", "xiaomi watch",
        "fitness watch", "sport watch", "gps watch"
    ],
    
    # N2: wearables.pulseiras - more band keywords
    "wearables.pulseiras": [
        "smart band", "fitness band", "pulseira", "mi band",
        "fitness tracker", "activity tracker", "health band",
        "sleep tracker", "heart rate monitor"
    ],
    
    # N2: camera.webcam - more webcam keywords
    "camera.webcam": [
        "webcam", "câmera", "camera", "hd webcam", "4k webcam",
        "streaming camera", "video call", "zoom camera",
        "logitech", "razer camera", "obs camera"
    ],
    
    # N2: camera.seguranca - more security camera keywords
    "camera.seguranca": [
        "security camera", "câmera segurança", "cftv", "ip camera",
        "wifi camera", "outdoor camera", "indoor camera",
        "doorbell camera", "campainha", "video doorbell",
        "night vision", "motion detection"
    ],
    
    # N2: beleza.maquiagem - more makeup keywords
    "beleza.maquiagem": [
        "makeup", "maquiagem", "cosmético", "cosmetics",
        "lipstick", "batom", "foundation", "base",
        "mascara", "rímel", "eyeshadow", "sombra",
        "blush", "contour", "highlighter", "primer"
    ],
    
    # N2: beleza.cabelo - more hair keywords
    "beleza.cabelo": [
        "hair", "cabelo", "hair dryer", "secador",
        "straightener", "alisador", "chapinha",
        "curling iron", "babyliss", "hair clipper",
        "máquina de cabelo", "hair trimmer"
    ],
    
    # N2: esportes.academia - more gym keywords
    "esportes.academia": [
        "gym", "fitness", "academia", "workout",
        "yoga", "pilates", "exercise", "exercício",
        "dumbbell", "halteres", "resistance band",
        "kettlebell", "pull up", "barra"
    ],
    
    # N2: casa.organizacao - more organization keywords
    "casa.organizacao": [
        "organizer", "organizador", "storage", "armazenamento",
        "drawer", "gaveta", "shelf", "prateleira",
        "closet", "wardrobe", "armário", "estante",
        "basket", "cesto", "box", "caixa"
    ],
    
    # N2: ferramentas.eletricas - more power tool keywords
    "ferramentas.eletricas": [
        "drill", "furadeira", "screwdriver", "parafusadeira",
        "saw", "serra", "grinder", "esmerilhadeira",
        "sander", "lixadeira", "jigsaw", "tico tico",
        "rotary tool", "dremel", "multitool"
    ],
    
    # N2: cozinha.panelas - more kitchen keywords
    "cozinha.panelas": [
        "pot", "pan", "panela", "frigideira", "frying pan",
        "pressure cooker", "panela pressão", "air fryer",
        "fryer", "deep fryer", "wok", "leiteira"
    ],
    
    # N2: moda.bolsas - more bag keywords
    "moda.bolsas": [
        "bag", "bolsa", "backpack", "mochila",
        "handbag", "bolsa de mão", "shoulder bag",
        "crossbody", "tote", "clutch", "wallet",
        "carteira", "purse", "briefcase", "malote"
    ],
    
    # N2: moda.oculos - more glasses keywords
    "moda.oculos": [
        "glasses", "óculos", "sunglasses", "óculos de sol",
        "eyeglasses", "óculos grau", "blue light glasses",
        "reading glasses", "óculos leitura", "safety glasses",
        "goggles", "óculos proteção"
    ],
}

def expand_keywords(dry_run=True):
    """Add additional keywords to taxonomy entries."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    updated = 0
    
    for slug, new_keywords in KEYWORD_EXPANSIONS.items():
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
        print(f"\n✅ Updated {updated} taxonomy entries")
    else:
        print(f"\n📝 Dry run: would update {updated} entries")
        print("   Run with --apply to apply changes")
    
    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Expand taxonomy keywords')
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    
    if args.apply:
        expand_keywords(dry_run=False)
    else:
        expand_keywords(dry_run=True)

if __name__ == '__main__':
    main()
