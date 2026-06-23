#!/usr/bin/env python3
"""
Batch embedding — carrega CLIP uma vez, embedda N queries.
Otimizacao: modelo persistente entre queries.

Usage:
  python3 embed_batch.py
"""
import sys, warnings, urllib3, time, json
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, '/mnt/ssd/1688-intel/scripts/arbitlens')

from embed import cmd_search_and_embed, init_db, _get_db
import sqlite3

# ── All queries for 2000+ products ──
# Multi-language queries for maximum coverage
# Format: (query_pt, need) — search.py uses PT but also translates
ALL_QUERIES = [
    # ── Audio ──
    ("microfone", 40), ("wireless microphone", 30), ("fone bluetooth", 40),
    ("bluetooth earphone", 30), ("caixa de som portatil", 30), ("bluetooth speaker", 25),
    ("headphone", 25), ("fone ouvido", 30),
    # ── Wearables ──
    ("smartwatch", 40), ("smart watch", 30), ("relogio masculino", 35),
    ("pulseira fitness", 25), ("fitness tracker", 20), ("relogio digital", 25),
    # ── Eletronicos ──
    ("power bank", 40), ("powerbank 10000mah", 30), ("cabo usb", 40),
    ("usb cable type c", 30), ("carregador", 40), ("carregador sem fio", 25),
    ("wireless charger", 20), ("mouse sem fio", 25), ("webcam", 25),
    ("adaptador tomada", 20), ("usb hub", 15),
    # ── Camera ──
    ("camera seguranca", 35), ("security camera wifi", 25), ("camera ip", 25),
    ("webcam hd", 20), ("campainha camera", 15),
    # ── Iluminacao ──
    ("lampada led", 30), ("led light bulb", 20), ("fita led", 20), ("led strip", 15),
    ("luz noturna", 20), ("night light", 15),
    # ── Ferramentas ──
    ("kit ferramentas", 35), ("tool set", 20), ("chave inglesa", 30),
    ("wrench set", 15), ("alicate", 30), ("plier", 15),
    ("furadeira", 25), ("drill", 15), ("martelo", 25), ("serra", 20),
    # ── Cozinha ──
    ("utensilios cozinha", 35), ("kitchen utensils", 20), ("faca chef", 30),
    ("chef knife", 20), ("panela", 35), ("cooking pan", 15),
    ("jogo talheres", 25), ("cutlery set", 15), ("frigideira", 25),
    ("tabua corte", 20), ("cutting board", 15), ("espatula silicone", 20),
    # ── Brinquedos ──
    ("brinquedo educativo", 30), ("educational toy", 15), ("boneca", 25),
    ("doll", 15), ("pelucia", 25), ("stuffed toy", 15),
    ("carrinho brinquedo", 25), ("toy car", 15), ("jogo tabuleiro", 20),
    ("board game", 15),
    # ── Esportes ──
    ("tapete yoga", 25), ("yoga mat", 15), ("garrafa agua academia", 25),
    ("sports water bottle", 15), ("mochila", 30), ("backpack", 20),
    ("oculos natacao", 20), ("swimming goggles", 15), ("corda pular", 15),
    # ── Pets ──
    ("coleira cachorro", 25), ("dog collar", 15), ("cama pet", 20),
    ("pet bed", 15), ("arranhador gato", 15), ("cat scratcher", 10),
    ("pote racao", 20), ("pet bowl", 15),
    # ── Casa ──
    ("almofada decorativa", 25), ("decorative pillow", 15), ("vaso", 20),
    ("flower pot", 15), ("toalha banho", 25), ("bath towel", 15),
    ("cortina", 20), ("curtain", 15), ("tapete", 20), ("rug", 15),
    # ── Beleza ──
    ("pincel maquiagem", 25), ("makeup brush", 15), ("escova cabelo", 20),
    ("hair brush", 15), ("batom", 20), ("lipstick", 15),
    ("creme hidratante", 20), ("moisturizer", 15),
    # ── Saude ──
    ("termometro digital", 20), ("digital thermometer", 15),
    ("massageador", 20), ("massager", 15), ("vitamina", 20),
    ("vitamin supplement", 15),
    # ── Jardim ──
    ("vaso planta", 20), ("flower pot", 15), ("ferramentas jardim", 20),
    ("garden tools", 15), ("regador", 15), ("watering can", 10),
    ("sementes", 15),
    # ── Automotivo ──
    ("acessorio carro", 20), ("car accessory", 15), ("adesivo carro", 15),
    ("car sticker", 10), ("cabo chupeta", 15), ("jump cable", 10),
    ("calibrador pneu", 15), ("tire gauge", 10),
    # ── Papelaria ──
    ("caneta", 25), ("pen", 15), ("caderno", 25), ("notebook", 15),
    ("agenda", 20), ("planner", 10), ("marca texto", 15), ("highlighter", 10),
    ("lapis", 20), ("pencil", 10),
    # ── Infantis ──
    ("mamadeira", 20), ("baby bottle", 10), ("body bebe", 20),
    ("baby bodysuit", 10), ("brinquedo infantil", 30), ("baby toy", 15),
    ("fralda", 15), ("carrinho bebe", 15),
    # ── Calcados ──
    ("tenis", 30), ("sneakers", 20), ("sapato", 25), ("shoe", 15),
    ("chinelo", 20), ("slippers", 15), ("bota", 15), ("boots", 10),
    # ── Moveis ──
    ("mesa", 20), ("table", 10), ("cadeira", 20), ("chair", 10),
    ("estante", 15), ("shelf", 10), ("guarda roupa", 10),
    # ── Camping ──
    ("barraca", 20), ("tent", 10), ("saco dormir", 15), ("sleeping bag", 10),
    ("lanterna", 20), ("flashlight", 15), ("bussola", 10),
    # ── Pesca ──
    ("vara pesca", 15), ("fishing rod", 10), ("anzol", 15), ("fish hook", 10),
    ("carretilha", 10),
    # ── Bicicleta ──
    ("acessorio bicicleta", 15), ("bike accessory", 10),
    ("capacete bicicleta", 15), ("bike helmet", 10),
    ("luz bicicleta", 10), ("bike light", 10),
]

def main():
    print(f"Batch embedding: {len(ALL_QUERIES)} queries", flush=True)
    start_total = time.time()
    
    init_db()
    
    processed = 0
    for i, (q, need) in enumerate(ALL_QUERIES):
        t0 = time.time()
        try:
            cmd_search_and_embed(q, need)
        except Exception as e:
            print(f"  FAIL [{i+1}/{len(ALL_QUERIES)}] {q}: {e}", flush=True)
            continue
        
        elapsed = time.time() - t0
        processed += 1
        
        # Check count every 5 queries
        if (i + 1) % 5 == 0:
            conn = _get_db()
            count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
            conn.close()
            eta = (time.time() - start_total) / (i + 1) * (len(ALL_QUERIES) - i - 1)
            print(f"  [{i+1}/{len(ALL_QUERIES)}] {q} ({need}) em {elapsed:.0f}s | Total: {count} | ETA: {eta:.0f}s", flush=True)
    
    # Final stats
    conn = _get_db()
    total = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f"\n{'='*50}", flush=True)
    print(f"FINAL: {total} products in {time.time()-start_total:.0f}s", flush=True)
    for row in conn.execute('SELECT category_n1, COUNT(*) FROM products GROUP BY category_n1 ORDER BY COUNT(*) DESC'):
        print(f"  {row[0]}: {row[1]}", flush=True)
    conn.close()

if __name__ == '__main__':
    main()
