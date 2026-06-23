#!/usr/bin/env python3
"""
arbitlens Embedding Pipeline — CLIP embeddings + SQLite storage.
Part of EPIC X3: Classificação + Embedding Matching.

Usage:
  python3 embed.py --search "microfone k15"       # Search + embed
  python3 embed.py --embed-all                     # Embed all cached products
  python3 embed.py --match "product_id"            # Find similar products
  python3 embed.py --classify "product_id"         # Classify N1/N2/N3
  python3 embed.py --stats                         # Show DB stats
"""
import json
import os
import sqlite3
import struct
import sys
import time
import warnings
from io import BytesIO

import numpy as np
import requests
import urllib3
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Config ──
DB_PATH = os.path.join(os.path.dirname(__file__), 'output', 'embeddings.db')
MODEL_NAME = 'openai/clip-vit-base-patch32'
EMBED_DIM = 512
RAKUMART_URL = 'https://www.rakumart.com.br/'

# Category hierarchy (N1 → N2 → N3)
CATEGORIES = {
    'audio': {
        'name': 'Áudio',
        'sub': {
            'microfones': {'name': 'Microfones', 'sub': ['lapela_fio', 'lapela_sem_fio', 'headset', 'condensador']},
            'fones': {'name': 'Fones', 'sub': ['tws', 'headphone', 'bluetooth']},
            'caixas_som': {'name': 'Caixas de Som', 'sub': ['portatil', 'bluetooth', 'smart_speaker']},
        }
    },
    'eletronicos': {
        'name': 'Eletrônicos',
        'sub': {
            'carregadores': {'name': 'Carregadores', 'sub': ['power_bank', 'carregador_parede', 'carregador_veicular', 'carregador_sem_fio']},
            'cabos': {'name': 'Cabos', 'sub': ['usb_a', 'usb_c', 'lightning', 'hdmi']},
            'acessorios': {'name': 'Acessórios', 'sub': ['suporte_celular', 'capa_celular', 'pelicula', 'mouse']},
        }
    },
    'wearables': {
        'name': 'Wearables',
        'sub': {
            'relogios': {'name': 'Relógios', 'sub': ['smartwatch', 'digital', 'analogico']},
            'pulseiras': {'name': 'Pulseiras', 'sub': ['fitness_tracker', 'smart_band']},
        }
    },
    'camera': {
        'name': 'Câmeras',
        'sub': {
            'seguranca': {'name': 'Segurança', 'sub': ['camera_wifi', 'camera_ip', 'campainha']},
            'webcam': {'name': 'Webcams', 'sub': ['webcam_hd', 'webcam_4k']},
        }
    },
    'iluminacao': {
        'name': 'Iluminação',
        'sub': {'led': {'name': 'LED', 'sub': ['lampada', 'fita_led', 'luz_noturna']}},
    },
    'ferramentas': {
        'name': 'Ferramentas',
        'sub': {
            'manuais': {'name': 'Manuais', 'sub': ['chave', 'alicate', 'martelo', 'chave_fenda']},
            'eletricas': {'name': 'Elétricas', 'sub': ['furadeira', 'parafusadeira', 'serra']},
            'medicao': {'name': 'Medição', 'sub': ['trena', 'nivel', 'paquimetro']},
        }
    },
    'cozinha': {
        'name': 'Cozinha & Utensílios',
        'sub': {
            'panelas': {'name': 'Panelas', 'sub': ['frigideira', 'panela_pressao', 'panela_antiaderente']},
            'facas': {'name': 'Facas', 'sub': ['faca_chef', 'faca_pao', 'descascador']},
            'utensilios': {'name': 'Utensílios', 'sub': ['espátula', 'concha', 'ralador', 'tábua']},
            'talheres': {'name': 'Talheres', 'sub': ['garfo', 'faca_mesa', 'colher', 'jogo_talheres']},
        }
    },
    'brinquedos': {
        'name': 'Brinquedos',
        'sub': {
            'educativos': {'name': 'Educativos', 'sub': ['quebra_cabeca', 'montar', 'ciencia']},
            'bonecos': {'name': 'Bonecos', 'sub': ['action_figure', 'boneca', 'pelucia']},
            'jogos': {'name': 'Jogos', 'sub': ['tabuleiro', 'carta', 'video_game']},
        }
    },
    'esportes': {
        'name': 'Esportes & Lazer',
        'sub': {
            'fitness': {'name': 'Fitness', 'sub': ['peso', 'tapete', 'corda', 'garrafa']},
            'ao_ar_livre': {'name': 'Ao Ar Livre', 'sub': ['barraca', 'mochila', 'bussola']},
            'aquaticos': {'name': 'Aquáticos', 'sub': ['oculos_natacao', 'touca', 'boia']},
        }
    },
    'pets': {
        'name': 'Pets & Animais',
        'sub': {
            'caes': {'name': 'Cães', 'sub': ['coleira', 'guia', 'cama', 'brinquedo_cachorro']},
            'gatos': {'name': 'Gatos', 'sub': ['arranhador', 'caixa_areia', 'cama_gato']},
            'acessorios': {'name': 'Acessórios', 'sub': ['pote', 'fonte', 'transportador']},
        }
    },
    'casa': {
        'name': 'Casa & Decoração',
        'sub': {
            'decoracao': {'name': 'Decoração', 'sub': ['vaso', 'quadro', 'vela', 'almofada']},
            'organizacao': {'name': 'Organização', 'sub': ['cesta', 'prateleira', 'gancho']},
            'banheiro': {'name': 'Banheiro', 'sub': ['toalha', 'cortina', 'tapete_banheiro']},
        }
    },
    'beleza': {
        'name': 'Beleza & Cuidados',
        'sub': {
            'maquiagem': {'name': 'Maquiagem', 'sub': ['batom', 'sombra', 'base', 'pincel']},
            'cabelo': {'name': 'Cabelo', 'sub': ['escova', 'pente', 'secador', 'prancha']},
            'cuidados': {'name': 'Cuidados', 'sub': ['creme', 'protetor', 'hidratante']},
        }
    },
    'saude': {
        'name': 'Saúde & Bem-estar',
        'sub': {
            'equipamentos': {'name': 'Equipamentos', 'sub': ['termometro', 'medidor', 'massageador']},
            'suplementos': {'name': 'Suplementos', 'sub': ['vitamina', 'proteina', 'colageno']},
        }
    },
    'jardim': {
        'name': 'Jardim',
        'sub': {
            'ferramentas_jardim': {'name': 'Ferramentas', 'sub': ['pá', 'tesoura_poda', 'regador']},
            'vasos': {'name': 'Vasos', 'sub': ['vaso', 'cachepot', 'suporte']},
        }
    },
    'automotivo': {
        'name': 'Automotivo',
        'sub': {
            'acessorios': {'name': 'Acessórios', 'sub': ['adesivo', 'nevoeiro', 'antenna']},
            'ferramentas_auto': {'name': 'Ferramentas', 'sub': ['macaco', 'cabo_chupeta', 'calibrador']},
        }
    },
    'papelaria': {
        'name': 'Papelaria',
        'sub': {
            'escrita': {'name': 'Escrita', 'sub': ['caneta', 'lapis', 'marca_texto']},
            'cadernos': {'name': 'Cadernos', 'sub': ['caderno', 'agenda', 'bloco_notas']},
            'organizacao': {'name': 'Organização', 'sub': ['pasta', 'classificador', 'etiqueta']},
        }
    },
    'infantis': {
        'name': 'Infantis',
        'sub': {
            'brinquedos': {'name': 'Brinquedos', 'sub': ['carrinho', 'boneco', 'massinha']},
            'roupas': {'name': 'Roupas', 'sub': ['body', 'macacao', 'vestido_bebe']},
            'alimentacao': {'name': 'Alimentação', 'sub': ['mamadeira', 'prato_bebe', 'copo_transicao']},
        }
    },
    'calcados': {
        'name': 'Calçados',
        'sub': {
            'tenis': {'name': 'Tênis', 'sub': ['tenis_casual', 'tenis_esporte', 'tenis_caminhada']},
            'sapatos': {'name': 'Sapatos', 'sub': ['sapato_social', 'sapato_feminino', 'bota']},
            'sandalia': {'name': 'Sandálias', 'sub': ['chinelo', 'sandalia', 'rasteirinha']},
        }
    },
    'moveis': {
        'name': 'Móveis',
        'sub': {
            'escritorio': {'name': 'Escritório', 'sub': ['mesa', 'cadeira', 'estante']},
            'quarto': {'name': 'Quarto', 'sub': ['criado_mudo', 'escrivaninha', 'cabeceira']},
            'sala': {'name': 'Sala', 'sub': ['rack', 'sofa', 'poltrona']},
        }
    },
    'camping': {
        'name': 'Camping & Aventura',
        'sub': {
            'barracas': {'name': 'Barracas', 'sub': ['barraca', 'lona', 'esteira']},
            'equipamentos': {'name': 'Equipamentos', 'sub': ['saco_dormir', 'fogareiro', 'cantil', 'lanterna']},
        }
    },
    'pesca': {
        'name': 'Pesca',
        'sub': {
            'varas': {'name': 'Varas', 'sub': ['vara_pesca', 'molinete', 'carretilha']},
            'acessorios': {'name': 'Acessórios', 'sub': ['caixa_pesca', 'anzol', 'chumbada', 'isca']},
        }
    },
}


# ── Singleton model ──
_model = None
_processor = None
_session = None


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        try:
            _session.get(RAKUMART_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        except Exception:
            pass
    return _session


def _get_model():
    global _model, _processor
    if _model is None:
        from transformers import CLIPProcessor, CLIPModel
        print(f'  Loading {MODEL_NAME}...', file=sys.stderr)
        t0 = time.time()
        _model = CLIPModel.from_pretrained(MODEL_NAME, use_safetensors=True)
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        print(f'  Model loaded in {time.time()-t0:.1f}s', file=sys.stderr)
    return _model, _processor


# ── Database ──

def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=OFF')
    return conn


def init_db():
    """Create schema if not exists."""
    conn = _get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            source_platform TEXT NOT NULL,
            product_name TEXT,
            category_n1 TEXT,
            category_n2 TEXT,
            category_n3 TEXT,
            embedding BLOB,
            embedding_model TEXT,
            price_brl REAL,
            image_url TEXT,
            metadata TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_n1 ON products(category_n1)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_n2 ON products(category_n2)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_n3 ON products(category_n3)')
    conn.commit()
    conn.close()


def _embedding_to_blob(emb):
    """Serialize numpy array to binary blob."""
    return struct.pack(f'{len(emb)}f', *emb)


def _blob_to_embedding(blob):
    """Deserialize binary blob to numpy array."""
    return np.array(struct.unpack(f'{len(blob)//4}f', blob))


# ── Image download + Embedding ──

def _download_image(url, timeout=30):
    """Download product image, return PIL Image or None."""
    if not url or not url.startswith('http'):
        return None
    sess = _get_session()
    try:
        r = sess.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.rakumart.com.br/',
        }, timeout=timeout, verify=False)
        if r.status_code == 200 and len(r.content) > 1000:
            from PIL import Image
            return Image.open(BytesIO(r.content)).convert('RGB')
    except Exception:
        pass
    return None


def compute_embedding(image_url):
    """Download image + compute CLIP embedding. Returns np.array or None."""
    from PIL import Image
    img = _download_image(image_url)
    if img is None:
        return None
    model, processor = _get_model()
    inputs = processor(images=img, return_tensors='pt')
    outputs = model.get_image_features(**inputs)
    return outputs.detach().numpy()[0]


# ── Zero-shot Classification ──

def classify_n1(product_name, image_url):
    """Classify product into N1 category using TITLE keywords (not image).
    CLIP is unreliable for thumbnail classification. Title-based is more accurate."""
    name = (product_name or '').lower()
    
    # Keyword-based N1 classification
    n1_keywords = {
        'audio': ['microfone', 'fone', 'headphone', 'caixa de som', 'bluetooth speaker', 'ouvido', 'earphone', 'headset', 'mic', 'k15', 'k9', 'q8', 'lapela'],
        'eletronicos': ['carregador', 'power bank', 'cabo usb', 'cabo type', 'adaptador', 'usb', 'type-c', 'lightning', 'hdmi', 'carregamento'],
        'wearables': ['smartwatch', 'relógio', 'pulseira', 'fitness', 'smart band', 'watch', 'wearable'],
        'camera': ['câmera', 'camera', 'webcam', 'segurança', 'security', 'vigilância', 'cctv', 'dvr'],
        'iluminacao': ['lâmpada', 'led', 'luz', 'lamp', 'light', 'iluminação'],
    'ferramentas': ['ferramenta', 'chave', 'alicate', 'martelo', 'furadeira', 'parafusadeira', 'serra', 'trena', 'paquímetro', 'nível', 'kit ferramentas', 'screwdriver', 'wrench', 'pliers'],
    'cozinha': ['cozinha', 'faca', 'panela', 'talher', 'espátula', 'concha', 'ralador', 'tábua', 'frigideira', 'colher', 'garfo', 'utensílio', 'kit cozinha', 'chef'],
    'brinquedos': ['brinquedo', 'boneco', 'boneca', 'pelúcia', 'jogo', 'quebra-cabeça', 'action figure', 'tabuleiro', 'carta', 'educativo', 'montar', 'lego'],
    'esportes': ['esporte', 'fitness', 'academia', 'peso', 'tapete yoga', 'corda', 'garrafa água', 'mochila', 'barraca', 'bússola', 'óculos natação', 'touca', 'boia'],
    'pets': ['pet', 'cachorro', 'gato', 'coleira', 'guia', 'cama pet', 'arranhador', 'caixa areia', 'pote ração', 'fonte água', 'brinquedo cão'],
    'casa': ['casa', 'decoração', 'vaso', 'quadro', 'vela', 'almofada', 'cesta', 'prateleira', 'gancho', 'toalha', 'cortina', 'tapete'],
    'beleza': ['beleza', 'maquiagem', 'batom', 'sombra', 'base', 'pincel', 'escova', 'pente', 'secador', 'prancha', 'creme', 'protetor solar', 'hidratante'],
    'saude': ['saúde', 'termômetro', 'medidor pressão', 'massageador', 'vitamina', 'proteína', 'colágeno', 'suplemento'],
    'jardim': ['jardim', 'planta', 'vaso', 'pá', 'regador', 'tesoura poda', 'cachepot', 'jardinagem'],
    'automotivo': ['automotivo', 'carro', 'acessório carro', 'adesivo', 'macaco', 'cabo chupeta', 'calibrador', 'nevoeiro'],
    'papelaria': ['papelaria', 'caneta', 'lápis', 'caderno', 'agenda', 'marca texto', 'pasta', 'classificador', 'etiqueta', 'bloco'],
    'infantis': ['infantil', 'bebê', 'criança', 'mamadeira', 'carrinho', 'boneco', 'body', 'macacão', 'brinquedo infantil', 'berço'],
    'calcados': ['tênis', 'sapato', 'chinelo', 'bota', 'sandália', 'sapatilha', 'calçado', 'sneaker', 'boots', 'slipper'],
    'moveis': ['móvel', 'mesa', 'cadeira', 'estante', 'rack', 'escrivaninha', 'criado', 'sofá', 'poltrona', 'cabeceira'],
    'camping': ['camping', 'barraca', 'saco dormir', 'lanterna', 'fogareiro', 'cantil', 'tent', 'sleeping bag', 'flashlight'],
    'pesca': ['pesca', 'vara', 'molinete', 'carretilha', 'anzol', 'chumbada', 'isca', 'caixa pesca', 'fishing', 'fish hook'],
    }
    
    scores = {}
    for slug, kws in n1_keywords.items():
        score = sum(1 for kw in kws if kw in name)
        if score > 0:
            scores[slug] = score
    
    if scores:
        best = max(scores, key=scores.get)
        return best, min(1.0, scores[best] / 3)
    # Truncate for CLIP
    product_name = (product_name or '')[:100]
    
    # Fallback: use CLIP zero-shot
    img = _download_image(image_url)
    if img is None:
        return None, 0.0
    model, processor = _get_model()
    labels = [cat['name'] for cat in CATEGORIES.values()]
    inputs = processor(images=img, text=labels, return_tensors='pt', padding=True, truncation=True)
    outputs = model(**inputs)
    logits = outputs.logits_per_image[0].detach().numpy()
    idx = int(np.argmax(logits))
    confidence = float((np.exp(logits[idx]) / np.exp(logits).sum()))
    if confidence < 0.3:
        return None, confidence
    return list(CATEGORIES.keys())[idx], confidence


# N2 keyword map: n1 > {keyword: n2_slug}
N2_KEYWORDS = {
    'audio': {'microfone': 'microfones', 'mic': 'microfones', 'lapela': 'microfones', 'k15': 'microfones', 'fone': 'fones', 'ouvido': 'fones', 'headphone': 'fones', 'earphone': 'fones', 'caixa': 'caixas_som', 'alto-falante': 'caixas_som', 'speaker': 'caixas_som'},
    'eletronicos': {'carregador': 'carregadores', 'power bank': 'carregadores', 'bateria': 'carregadores', 'cabo': 'cabos', 'usb': 'cabos', 'hdmi': 'cabos', 'type-c': 'cabos', 'type c': 'cabos', 'lightning': 'cabos', 'suporte': 'acessorios', 'capa': 'acessorios', 'mouse': 'acessorios'},
    'wearables': {'relógio': 'relogios', 'smartwatch': 'relogios', 'watch': 'relogios', 'pulseira': 'pulseiras', 'fitness': 'pulseiras', 'band': 'pulseiras'},
    'camera': {'câmera': 'seguranca', 'camera': 'seguranca', 'vigilância': 'seguranca', 'cctv': 'seguranca', 'dvr': 'seguranca', 'webcam': 'webcam'},
    'iluminacao': {'lâmpada': 'led', 'lampada': 'led', 'led': 'led', 'luz': 'led', 'light': 'led'},
    'ferramentas': {'chave': 'manuais', 'alicate': 'manuais', 'martelo': 'manuais', 'furadeira': 'eletricas', 'parafusadeira': 'eletricas', 'serra': 'eletricas', 'trena': 'medicao', 'nivel': 'medicao', 'paquimetro': 'medicao'},
    'cozinha': {'panela': 'panelas', 'frigideira': 'panelas', 'faca': 'facas', 'descascador': 'facas', 'espátula': 'utensilios', 'concha': 'utensilios', 'ralador': 'utensilios', 'tábua': 'utensilios', 'talher': 'talheres', 'garfo': 'talheres', 'colher': 'talheres', 'jogo': 'talheres'},
    'brinquedos': {'quebra-cabeça': 'educativos', 'montar': 'educativos', 'ciência': 'educativos', 'action figure': 'bonecos', 'boneca': 'bonecos', 'pelúcia': 'bonecos', 'tabuleiro': 'jogos', 'carta': 'jogos', 'video game': 'jogos'},
    'esportes': {'peso': 'fitness', 'tapete': 'fitness', 'corda': 'fitness', 'garrafa': 'fitness', 'barraca': 'ao_ar_livre', 'mochila': 'ao_ar_livre', 'bússola': 'ao_ar_livre', 'óculos': 'aquaticos', 'touca': 'aquaticos', 'boia': 'aquaticos'},
    'pets': {'coleira': 'caes', 'guia': 'caes', 'cama': 'caes', 'brinquedo': 'caes', 'arranhador': 'gatos', 'areia': 'gatos', 'pote': 'acessorios', 'fonte': 'acessorios', 'transportador': 'acessorios'},
    'casa': {'vaso': 'decoracao', 'quadro': 'decoracao', 'vela': 'decoracao', 'almofada': 'decoracao', 'cesta': 'organizacao', 'prateleira': 'organizacao', 'gancho': 'organizacao', 'toalha': 'banheiro', 'cortina': 'banheiro', 'tapete': 'banheiro'},
    'beleza': {'batom': 'maquiagem', 'sombra': 'maquiagem', 'base': 'maquiagem', 'pincel': 'maquiagem', 'escova': 'cabelo', 'pente': 'cabelo', 'secador': 'cabelo', 'prancha': 'cabelo', 'creme': 'cuidados', 'protetor': 'cuidados', 'hidratante': 'cuidados'},
    'saude': {'termômetro': 'equipamentos', 'medidor': 'equipamentos', 'massageador': 'equipamentos', 'vitamina': 'suplementos', 'proteína': 'suplementos', 'colágeno': 'suplementos', 'suplemento': 'suplementos'},
    'jardim': {'pá': 'ferramentas_jardim', 'tesoura': 'ferramentas_jardim', 'regador': 'ferramentas_jardim', 'vaso': 'vasos', 'cachepot': 'vasos', 'suporte': 'vasos'},
    'automotivo': {'adesivo': 'acessorios', 'nevoeiro': 'acessorios', 'macaco': 'ferramentas_auto', 'cabo': 'ferramentas_auto', 'calibrador': 'ferramentas_auto'},
    'papelaria': {'caneta': 'escrita', 'lápis': 'escrita', 'marca texto': 'escrita', 'caderno': 'cadernos', 'agenda': 'cadernos', 'bloco': 'cadernos', 'pasta': 'organizacao', 'classificador': 'organizacao', 'etiqueta': 'organizacao'},
    'infantis': {'carrinho': 'brinquedos', 'boneco': 'brinquedos', 'massinha': 'brinquedos', 'body': 'roupas', 'macacão': 'roupas', 'vestido': 'roupas', 'mamadeira': 'alimentacao', 'prato': 'alimentacao', 'copo': 'alimentacao'},
    'calcados': {'tênis': 'tenis', 'sapato': 'sapatos', 'bota': 'sapatos', 'chinelo': 'sandalia', 'sandália': 'sandalia', 'sapatilha': 'sandalia'},
    'moveis': {'mesa': 'escritorio', 'cadeira': 'escritorio', 'estante': 'escritorio', 'criado': 'quarto', 'escrivaninha': 'quarto', 'cabeceira': 'quarto', 'rack': 'sala', 'sofá': 'sala', 'poltrona': 'sala'},
    'camping': {'barraca': 'barracas', 'lona': 'barracas', 'saco': 'equipamentos', 'fogareiro': 'equipamentos', 'cantil': 'equipamentos', 'lanterna': 'equipamentos'},
    'pesca': {'vara': 'varas', 'molinete': 'varas', 'carretilha': 'varas', 'anzol': 'acessorios', 'chumbada': 'acessorios', 'isca': 'acessorios', 'caixa': 'acessorios'},
}


def classify_n2(n1_slug, product_name, image_url):
    """Classify into N2 subcategory using title keywords."""
    name = (product_name or '').lower()
    
    n2_map = N2_KEYWORDS.get(n1_slug, {})
    if not n2_map:
        return None, 0.0
    
    scores = {}
    for kw, n2_slug in n2_map.items():
        if kw in name:
            scores[n2_slug] = scores.get(n2_slug, 0) + 1
    
    if scores:
        best = max(scores, key=scores.get)
        return best, min(1.0, scores[best])
    
    return None, 0.0


def classify_n3(n1_slug, n2_slug, product_name, image_url):
    """Classify into N3 microcategory."""
    if n1_slug not in CATEGORIES or n2_slug not in CATEGORIES[n1_slug]['sub']:
        return None, 0.0
    
    n3_list = CATEGORIES[n1_slug]['sub'][n2_slug]['sub']
    if not n3_list:
        return None, 0.0
    
    img = _download_image(image_url)
    if img is None:
        return None, 0.0
    
    model, processor = _get_model()
    texts = [f'{n3.replace("_", " ")}' for n3 in n3_list]
    
    inputs = processor(images=img, text=texts, return_tensors='pt', padding=True)
    outputs = model(**inputs)
    logits = outputs.logits_per_image[0].detach().numpy()
    
    idx = int(np.argmax(logits))
    confidence = float((np.exp(logits[idx]) / np.exp(logits).sum()))
    
    if confidence < 0.2:
        return None, confidence
    
    return n3_list[idx], confidence


def classify_full(product_name, image_url):
    """N1 → N2 → N3 cascade classification."""
    # Truncate long titles (CLIP max 77 tokens)
    product_name = (product_name or '')[:200]
    n1, c1 = classify_n1(product_name, image_url)
    if not n1:
        return {'n1': None, 'n2': None, 'n3': None, 'confidence': 0}
    
    n2, c2 = classify_n2(n1, product_name, image_url)
    if not n2:
        return {'n1': n1, 'n2': None, 'n3': None, 'confidence': c1}
    
    n3, c3 = classify_n3(n1, n2, product_name, image_url)
    
    return {
        'n1': n1, 'n2': n2, 'n3': n3,
        'confidence': min(c1, c2, c3),
        'c_n1': round(c1, 3),
        'c_n2': round(c2, 3),
        'c_n3': round(c3, 3),
    }


# ── Store & Query ──

def store_product(prod_dict, category=None, embedding=None):
    """Store or update a product in the DB."""
    conn = _get_db()
    pid = f"{prod_dict.get('platform', '?')}_{prod_dict.get('product_url', prod_dict.get('product_name', '?'))}"
    
    emb_blob = None
    if embedding is not None:
        emb_blob = _embedding_to_blob(embedding)
    
    category = category or {}
    
    conn.execute('''
        INSERT OR REPLACE INTO products
        (id, source_platform, product_name, category_n1, category_n2, category_n3,
         embedding, embedding_model, price_brl, image_url, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pid,
        prod_dict.get('platform', ''),
        prod_dict.get('product_name', '')[:200],
        category.get('n1'),
        category.get('n2'),
        category.get('n3'),
        emb_blob,
        MODEL_NAME,
        prod_dict.get('price_brl'),
        prod_dict.get('image_url', ''),
        json.dumps(prod_dict, ensure_ascii=False, default=str),
    ))
    conn.commit()
    conn.close()
    return pid


def find_similar(pid, n3_filter=None, limit=10):
    """Find similar products by cosine similarity."""
    conn = _get_db()
    
    # Get source embedding
    row = conn.execute('SELECT embedding, category_n1 FROM products WHERE id = ?', (pid,)).fetchone()
    if not row or not row[0]:
        conn.close()
        return []
    
    source_emb = _blob_to_embedding(row[0])
    source_n1 = row[1]
    
    # Query candidates — prefer same N1, fallback to all
    if source_n1:
        candidates = conn.execute(
            'SELECT id, product_name, price_brl, category_n1, category_n2, category_n3, embedding, image_url FROM products WHERE id != ? AND category_n1 = ?',
            (pid, source_n1)
        ).fetchall()
    else:
        candidates = conn.execute(
            'SELECT id, product_name, price_brl, category_n1, category_n2, category_n3, embedding, image_url FROM products WHERE id != ?',
            (pid,)
        ).fetchall()
    
    # If too few candidates, expand to all
    if len(candidates) < 5:
        candidates = conn.execute(
            'SELECT id, product_name, price_brl, category_n1, category_n2, category_n3, embedding, image_url FROM products WHERE id != ?',
            (pid,)
        ).fetchall()
    
    conn.close()
    
    # Compute cosine similarities
    results = []
    for c in candidates:
        cid, cname, cprice, cn1, cn2, cn3, cemb_blob, cimg = c
        if not cemb_blob:
            continue
        cemb = _blob_to_embedding(cemb_blob)
        sim = float(np.dot(source_emb, cemb) / (np.linalg.norm(source_emb) * np.linalg.norm(cemb)))
        
        # Bonus if same N1 category
        n1_bonus = 0.05 if cn1 == source_n1 and source_n1 else 0
        
        score = (sim + n1_bonus) * 0.7
        
        results.append({
            'id': cid,
            'product_name': cname,
            'price_brl': cprice,
            'category_n1': cn1,
            'category_n2': cn2,
            'category_n3': cn3,
            'image_url': cimg,
            'similarity': round(sim, 4),
            'score': round(score * 100, 1),
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


# ── CLI ──

def cmd_stats():
    conn = _get_db()
    total = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    with_emb = conn.execute('SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL').fetchone()[0]
    with_n1 = conn.execute('SELECT COUNT(*) FROM products WHERE category_n1 IS NOT NULL').fetchone()[0]
    with_n3 = conn.execute('SELECT COUNT(*) FROM products WHERE category_n3 IS NOT NULL').fetchone()[0]
    conn.close()
    
    print(f'\n📊 DB Stats')
    print(f'  Total products: {total}')
    print(f'  With embedding: {with_emb}')
    print(f'  With N1:        {with_n1}')
    print(f'  With N3:        {with_n3}')
    
    # Show categories
    if with_n1 > 0:
        conn = _get_db()
        rows = conn.execute('SELECT category_n1, COUNT(*) FROM products WHERE category_n1 IS NOT NULL GROUP BY category_n1 ORDER BY COUNT(*) DESC').fetchall()
        print(f'\n  Categories:')
        for n1, cnt in rows:
            print(f'    {n1}: {cnt}')
        conn.close()


def cmd_search_and_embed(query, max_results=30):
    """Search products, classify, embed, and store."""
    from search import search_all
    print(f'Searching: {query}', file=sys.stderr)
    t0 = time.time()
    result = search_all(query, max_results_per_platform=max_results // 5)
    products = result.get('products', [])
    print(f'  Found {len(products)} products in {time.time()-t0:.1f}s', file=sys.stderr)
    
    init_db()
    
    stored = 0
    for i, p in enumerate(products):
        url = p.get('image_url', '')
        if not url:
            continue
        
        print(f'  [{i+1}/{len(products)}] {p.get("product_name","")[:40]}...', file=sys.stderr)
        
        # Compute embedding
        emb = compute_embedding(url)
        if emb is None:
            print(f'    No image', file=sys.stderr)
            continue
        
        # Classify
        cat = classify_full(p.get('product_name', ''), url)
        
        # Store
        pid = store_product(p, category=cat, embedding=emb)
        stored += 1
        print(f'    -> {pid[:50]} | N1={cat.get("n1","?")}', file=sys.stderr)
        
        if stored >= max_results:
            break
    
    print(f'\n✅ Stored {stored} products', file=sys.stderr)


def cmd_match(pid, limit=10):
    # Support partial ID search
    conn = _get_db()
    exact = conn.execute('SELECT id FROM products WHERE id = ?', (pid,)).fetchone()
    if not exact:
        # Try partial match
        rows = conn.execute('SELECT id FROM products WHERE id LIKE ? OR product_name LIKE ? LIMIT 1', (f'%{pid}%', f'%{pid}%')).fetchall()
        if rows:
            pid = rows[0][0]
            print(f'  Matched to: {pid[:60]}', file=sys.stderr)
        else:
            print('Product not found.')
            conn.close()
            return
    conn.close()
    results = find_similar(pid, limit=limit)
    if not results:
        print('No similar products found.')
        return
    print(f'\n🔍 Top {len(results)} similar to {pid[:50]}...')
    print(f'{"Score":>6s} | {"Sim":>5s} | {"N3":20s} | Product')
    print('-' * 70)
    for r in results:
        n3 = (r.get('category_n3') or '?')[:20]
        print(f'{r["score"]:>5.1f}% | {r["similarity"]:.3f} | {n3:20s} | {r["product_name"][:40]}')


if __name__ == '__main__':
    if '--search' in sys.argv:
        idx = sys.argv.index('--search')
        query = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else 'microfone'
        max_r = int(sys.argv[idx + 2]) if len(sys.argv) > idx + 2 else 30
        cmd_search_and_embed(query, max_r)
    elif '--match' in sys.argv:
        idx = sys.argv.index('--match')
        pid = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else ''
        limit = int(sys.argv[idx + 2]) if len(sys.argv) > idx + 2 else 10
        cmd_match(pid, limit)
    elif '--stats' in sys.argv:
        cmd_stats()
    elif '--classify' in sys.argv:
        idx = sys.argv.index('--classify')
        pid = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else ''
        conn = _get_db()
        row = conn.execute('SELECT product_name, image_url FROM products WHERE id = ?', (pid,)).fetchone()
        conn.close()
        if row:
            cat = classify_full(row[0], row[1])
            print(json.dumps(cat, indent=2))
        else:
            print(f'Product {pid} not found')
    else:
        print(__doc__)

