#!/usr/bin/env python3
"""
taxonomy_setup.py — Create and populate the 4-level taxonomy in PostgreSQL.

Usage:
  python3 taxonomy_setup.py --create    # Create tables
  python3 taxonomy_setup.py --populate  # Insert taxonomy data
  python3 taxonomy_setup.py --backfill  # Backfill products
  python3 taxonomy_setup.py --all       # All steps
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

# ═══════════════════════════════════════════════════════════
# TAXONOMY DATA — 4-level hierarchy
# ═══════════════════════════════════════════════════════════

TAXONOMY = [
    # N1: audio
    ("audio", 1, None, "Áudio & Microfones", "Audio & Microphones", "🎙️",
     ["microfone", "fone", "headphone", "caixa de som", "speaker", "lapela"]),
    ("audio.microfones", 2, "audio", "Microfones", "Microphones", "🎤",
     ["microfone", "lapela", "condensador", "shotgun"]),
    ("audio.microfones.lapela_fio", 3, "audio.microfones", "Lavalier com Fio", "Wired Lavalier", "📎",
     ["lapela com fio", "lavalier wired", "microfone lapela"]),
    ("audio.microfones.lapela_fio.lapela_universal", 4, "audio.microfones.lapela_fio", "Universal", "Universal", "📎",
     ["universal", "generic", "3.5mm"]),
    ("audio.microfones.lapela_fio.lapela_profissional", 4, "audio.microfones.lapela_fio", "Profissional", "Professional", "📎",
     ["profissional", "xlr", "condensador"]),
    ("audio.microfones.lapela_fio.lapela_kit", 4, "audio.microfones.lapela_fio", "Kit 2+ unidades", "Kit 2+ units", "📎",
     ["kit", "2 microfone", "dual"]),
    ("audio.microfones.lapela_sem_fio", 3, "audio.microfones", "Lavalier Sem Fio", "Wireless Lavalier", "📡",
     ["lapela sem fio", "wireless lavalier", "k9", "k15"]),
    ("audio.microfones.lapela_sem_fio.lapela_24ghz", 4, "audio.microfones.lapela_sem_fio", "2.4GHz", "2.4GHz", "📡",
     ["2.4ghz", "2.4g"]),
    ("audio.microfones.lapela_sem_fio.lapela_bluetooth", 4, "audio.microfones.lapela_sem_fio", "Bluetooth", "Bluetooth", "📡",
     ["bluetooth", "bt"]),
    ("audio.microfones.lapela_sem_fio.lapela_uhf", 4, "audio.microfones.lapela_sem_fio", "UHF", "UHF", "📡",
     ["uhf", "vhf"]),
    ("audio.microfones.condensador", 3, "audio.microfones", "Condensador", "Condenser", "🎚️",
     ["condensador", "condenser", "cardioide"]),
    ("audio.microfones.condensador.condensador_usb", 4, "audio.microfones.condensador", "USB", "USB", "🎚️",
     ["usb", "plug and play"]),
    ("audio.microfones.condensador.condensador_xlr", 4, "audio.microfones.condensador", "XLR", "XLR", "🎚️",
     ["xlr", "phantom"]),
    ("audio.microfones.shotgun", 3, "audio.microfones", "Shotgun", "Shotgun", "🎬",
     ["shotgun", "boom", "câmera mic"]),
    ("audio.microfones.headset_mic", 3, "audio.microfones", "Headset com Microfone", "Headset with Mic", "🎧",
     ["headset", "headphone com microfone"]),
    ("audio.microfones.headset_mic.headset_gamer", 4, "audio.microfones.headset_mic", "Gamer", "Gaming", "🎧",
     ["gamer", "gaming", "rgb"]),
    ("audio.microfones.headset_mic.headset_callcenter", 4, "audio.microfones.headset_mic", "Call Center", "Call Center", "🎧",
     ["call center", "office", "mono"]),

    ("audio.fones", 2, "audio", "Fones de Ouvido", "Headphones & Earbuds", "🎧",
     ["fone", "headphone", "earbuds", "airpods", "tws"]),
    ("audio.fones.tws", 3, "audio.fones", "True Wireless (TWS)", "True Wireless (TWS)", "🎵",
     ["tws", "true wireless", "airpods"]),
    ("audio.fones.tws.tws_base", 4, "audio.fones.tws", "Com Caixa de Carregamento", "With Charging Case", "🎵",
     ["caixa", "carregamento", "charging case"]),
    ("audio.fones.tws.tws_airpods", 4, "audio.fones.tws", "Estilo AirPods", "AirPods Style", "🎵",
     ["airpods", "apple style", "pro"]),
    ("audio.fones.tws.tws_sport", 4, "audio.fones.tws", "Esportivo", "Sport", "🎵",
     ["esportivo", "sport", "resistente agua", "ipx"]),
    ("audio.fones.over_ear", 3, "audio.fones", "Over-Ear", "Over-Ear", "🎧",
     ["over-ear", "circumaural"]),
    ("audio.fones.over_ear.over_ear_anc", 4, "audio.fones.over_ear", "Cancelamento de Ruído (ANC)", "Noise Cancelling (ANC)", "🎧",
     ["anc", "noise cancel"]),
    ("audio.fones.over_ear.over_ear_gamer", 4, "audio.fones.over_ear", "Gamer", "Gaming", "🎧",
     ["gamer", "gaming", "7.1"]),
    ("audio.fones.on_ear", 3, "audio.fones", "On-Ear", "On-Ear", "🎧",
     ["on-ear", "supraaural"]),
    ("audio.fones.in_ear", 3, "audio.fones", "In-Ear com Fio", "Wired In-Ear", "🎧",
     ["in-ear", "com fio", "wired", "3.5mm"]),
    ("audio.fones.bluetooth_neckband", 3, "audio.fones", "Bluetooth Pescoço", "Bluetooth Neckband", "🎧",
     ["neckband", "pescoço"]),

    ("audio.caixas_som", 2, "audio", "Caixas de Som", "Speakers", "🔊",
     ["caixa de som", "speaker", "bluetooth speaker"]),
    ("audio.caixas_som.bt_portatil", 3, "audio.caixas_som", "Bluetooth Portátil", "Portable Bluetooth", "🔊",
     ["portatil", "portable", "bluetooth"]),
    ("audio.caixas_som.bt_portatil.bt_mini", 4, "audio.caixas_som.bt_portatil", "Mini", "Mini", "🔊",
     ["mini", "compact"]),
    ("audio.caixas_som.bt_portatil.bt_medio", 4, "audio.caixas_som.bt_portatil", "Média", "Medium", "🔊",
     ["media", "medio"]),
    ("audio.caixas_som.bt_portatil.bt_grande", 4, "audio.caixas_som.bt_portatil", "Grande/Party", "Large/Party", "🔊",
     ["grande", "party", "bass"]),
    ("audio.caixas_som.smart_speaker", 3, "audio.caixas_som", "Smart Speaker", "Smart Speaker", "🔊",
     ["smart speaker", "alexa", "google home"]),
    ("audio.caixas_som.soundbar", 3, "audio.caixas_som", "Barra de Som", "Soundbar", "🔊",
     ["soundbar", "barra de som", "home theater"]),

    ("audio.acessorios_audio", 2, "audio", "Acessórios de Áudio", "Audio Accessories", "🔌",
     ["suporte microfone", "pop filter", "interface audio"]),
    ("audio.acessorios_audio.suporte_microfone", 3, "audio.acessorios_audio", "Suporte/Arco", "Mount/Boom Arm", "🔌",
     ["suporte", "arco", "boom arm"]),
    ("audio.acessorios_audio.pop_filter", 3, "audio.acessorios_audio", "Pop Filter", "Pop Filter", "🔌",
     ["pop filter", "pop shield"]),
    ("audio.acessorios_audio.interface_audio", 3, "audio.acessorios_audio", "Interface de Áudio USB", "USB Audio Interface", "🔌",
     ["interface", "audio usb"]),

    # N1: eletronicos
    ("eletronicos", 1, None, "Eletrônicos & Acessórios", "Electronics & Accessories", "📱",
     ["celular", "carregador", "cabo", "mouse", "teclado", "power bank"]),
    ("eletronicos.carregadores", 2, "eletronicos", "Carregadores", "Chargers", "🔋",
     ["carregador", "charger", "power bank"]),
    ("eletronicos.carregadores.power_bank", 3, "eletronicos.carregadores", "Power Bank", "Power Bank", "🔋",
     ["power bank", "bateria externa"]),
    ("eletronicos.carregadores.power_bank.pb_10000", 4, "eletronicos.carregadores.power_bank", "10.000mAh", "10,000mAh", "🔋",
     ["10000", "10k"]),
    ("eletronicos.carregadores.power_bank.pb_20000", 4, "eletronicos.carregadores.power_bank", "20.000mAh", "20,000mAh", "🔋",
     ["20000", "20k"]),
    ("eletronicos.carregadores.power_bank.pb_magSafe", 4, "eletronicos.carregadores.power_bank", "MagSafe", "MagSafe", "🔋",
     ["magsafe", "magnetico"]),
    ("eletronicos.carregadores.carregador_parede", 3, "eletronicos.carregadores", "Parede", "Wall Charger", "🔋",
     ["parede", "wall", "tomada"]),
    ("eletronicos.carregadores.carregador_parede.cp_20w", 4, "eletronicos.carregadores.carregador_parede", "20W", "20W", "🔋",
     ["20w"]),
    ("eletronicos.carregadores.carregador_parede.cp_65w", 4, "eletronicos.carregadores.carregador_parede", "65W GaN", "65W GaN", "🔋",
     ["65w", "gan"]),
    ("eletronicos.carregadores.carregador_veicular", 3, "eletronicos.carregadores", "Veicular", "Car Charger", "🔋",
     ["veicular", "carro", "car charger"]),
    ("eletronicos.carregadores.carregador_sem_fio", 3, "eletronicos.carregadores", "Sem Fio", "Wireless Charger", "🔋",
     ["sem fio", "wireless"]),

    ("eletronicos.cabos", 2, "eletronicos", "Cabos & Adaptadores", "Cables & Adapters", "🔌",
     ["cabo", "cable", "usb", "type c", "hdmi"]),
    ("eletronicos.cabos.usb_c", 3, "eletronicos.cabos", "USB-C", "USB-C", "🔌",
     ["usb-c", "type-c"]),
    ("eletronicos.cabos.usb_c.usbc_curto", 4, "eletronicos.cabos.usb_c", "Curto (<1m)", "Short (<1m)", "🔌",
     ["curto", "short", "0.5m"]),
    ("eletronicos.cabos.usb_c.usbc_longo", 4, "eletronicos.cabos.usb_c", "Longo (2m+)", "Long (2m+)", "🔌",
     ["longo", "long", "2m"]),
    ("eletronicos.cabos.usb_c.usbc_65w", 4, "eletronicos.cabos.usb_c", "65W PD", "65W PD", "🔌",
     ["65w", "pd", "power delivery"]),
    ("eletronicos.cabos.hdmi", 3, "eletronicos.cabos", "HDMI", "HDMI", "🔌",
     ["hdmi", "4k"]),
    ("eletronicos.cabos.adaptadores_cabo", 3, "eletronicos.cabos", "Adaptadores", "Adapters", "🔌",
     ["adaptador", "adapter", "hub"]),
    ("eletronicos.cabos.adaptadores_cabo.usbc_hub", 4, "eletronicos.cabos.adaptadores_cabo", "Hub USB-C", "USB-C Hub", "🔌",
     ["hub", "dock"]),

    ("eletronicos.acessorios_celular", 2, "eletronicos", "Acessórios de Celular", "Phone Accessories", "📱",
     ["capa celular", "pelicula", "suporte celular"]),
    ("eletronicos.acessorios_celular.suporte_celular", 3, "eletronicos.acessorios_celular", "Suporte", "Phone Stand", "📱",
     ["suporte", "stand", "holder"]),
    ("eletronicos.acessorios_celular.capa_celular", 3, "eletronicos.acessorios_celular", "Capa", "Phone Case", "📱",
     ["capa", "case"]),
    ("eletronicos.acessorios_celular.pelicula", 3, "eletronicos.acessorios_celular", "Película", "Screen Protector", "📱",
     ["película", "temperado", "screen protector"]),

    ("eletronicos.memorias", 2, "eletronicos", "Memórias", "Storage", "💾",
     ["pendrive", "cartão sd", "ssd"]),
    ("eletronicos.memorias.pendrive", 3, "eletronicos.memorias", "Pendrive USB", "USB Flash Drive", "💾",
     ["pendrive", "flash drive"]),
    ("eletronicos.memorias.sd_card", 3, "eletronicos.memorias", "Cartão SD", "SD Card", "💾",
     ["sd card", "micro sd"]),
    ("eletronicos.memorias.ssd_portatil", 3, "eletronicos.memorias", "SSD Portátil", "Portable SSD", "💾",
     ["ssd", "portatil", "externo"]),

    # N1: wearables
    ("wearables", 1, None, "Wearables & Smartwatches", "Wearables & Smartwatches", "⌚",
     ["smartwatch", "pulseira", "relógio inteligente"]),
    ("wearables.relogios", 2, "wearables", "Relógios", "Watches", "⌚",
     ["relógio", "watch", "smartwatch"]),
    ("wearables.relogios.smartwatch", 3, "wearables.relogios", "Smartwatch", "Smartwatch", "⌚",
     ["smartwatch", "relógio inteligente"]),
    ("wearables.relogios.smartwatch.sw_kids", 4, "wearables.relogios.smartwatch", "Infantil", "Kids", "⌚",
     ["infantil", "kids", "criança"]),
    ("wearables.relogios.smartwatch.sw_sport", 4, "wearables.relogios.smartwatch", "Esportivo", "Sport", "⌚",
     ["esportivo", "sport", "gps"]),
    ("wearables.relogios.smartwatch.sw_premium", 4, "wearables.relogios.smartwatch", "Premium/GPS", "Premium/GPS", "⌚",
     ["premium", "luxo", "apple watch"]),
    ("wearables.pulseiras", 2, "wearables", "Pulseiras Inteligentes", "Smart Bands", "📿",
     ["pulseira", "smart band", "fitness tracker"]),
    ("wearables.pulseiras.fitness_tracker", 3, "wearables.pulseiras", "Fitness", "Fitness", "📿",
     ["fitness", "exercício"]),
    ("wearables.pulseiras.smart_band", 3, "wearables.pulseiras", "Smart Band", "Smart Band", "📿",
     ["smart band", "mi band"]),
    ("wearables.audio_wearable", 2, "wearables", "Áudio Vestível", "Wearable Audio", "🦻",
     ["condução óssea", "bone conduction", "earclip"]),
    ("wearables.audio_wearable.bone_conduction", 3, "wearables.audio_wearable", "Condução Óssea", "Bone Conduction", "🦻",
     ["condução óssea", "bone conduction"]),

    # N1: eletronicos (cont.)
    # N1: camera
    ("camera", 1, None, "Câmeras & Segurança", "Cameras & Security", "📷",
     ["câmera", "webcam", "action cam", "drone", "segurança"]),
    ("camera.seguranca", 2, "camera", "Câmeras de Segurança", "Security Cameras", "🛡️",
     ["segurança", "cftv", "ip camera"]),
    ("camera.seguranca.camera_wifi", 3, "camera.seguranca", "Wi-Fi", "Wi-Fi", "🛡️",
     ["wifi", "sem fio"]),
    ("camera.seguranca.camera_wifi.cam_wifi_mini", 4, "camera.seguranca.camera_wifi", "Mini", "Mini", "🛡️",
     ["mini", "compact", "espiã"]),
    ("camera.seguranca.camera_wifi.cam_wifi_pan", 4, "camera.seguranca.camera_wifi", "Pan/Tilt", "Pan/Tilt", "🛡️",
     ["pan", "tilt", "360"]),
    ("camera.seguranca.camera_ip", 3, "camera.seguranca", "IP (Fio)", "IP (Wired)", "🛡️",
     ["ip", "poe", "fio"]),
    ("camera.seguranca.campainha", 3, "camera.seguranca", "Campainha", "Doorbell", "🛡️",
     ["campainha", "doorbell"]),
    ("camera.webcam", 2, "camera", "Webcam", "Webcam", "💻",
     ["webcam", "câmera notebook"]),
    ("camera.webcam.webcam_hd", 3, "camera.webcam", "HD 1080p", "HD 1080p", "💻",
     ["1080p", "hd"]),
    ("camera.webcam.webcam_4k", 3, "camera.webcam", "4K", "4K", "💻",
     ["4k", "ultra hd"]),
    ("camera.action_cam", 2, "camera", "Action Camera", "Action Camera", "🎬",
     ["action cam", "gopro"]),
    ("camera.drones", 2, "camera", "Drones", "Drones", "🚁",
     ["drone", "fpv"]),
    ("camera.drones.drone_mini", 3, "camera.drones", "Mini (<250g)", "Mini (<250g)", "🚁",
     ["mini", "leve"]),
    ("camera.drones.drone_gps", 3, "camera.drones", "GPS", "GPS", "🚁",
     ["gps", "return home"]),
    ("camera.estabilizadores", 2, "camera", "Estabilizadores", "Gimbals", "🎥",
     ["gimbal", "estabilizador"]),
    ("camera.acc_camera", 2, "camera", "Acessórios de Câmera", "Camera Accessories", "📎",
     ["tripé", "ring light", "lente"]),
    ("camera.acc_camera.tripod", 3, "camera.acc_camera", "Tripé", "Tripod", "📎",
     ["tripé", "tripod"]),
    ("camera.acc_camera.ring_light", 3, "camera.acc_camera", "Ring Light", "Ring Light", "📎",
     ["ring light", "anel de luz"]),

    # N1: beleza
    ("beleza", 1, None, "Beleza & Cuidados", "Beauty & Personal Care", "💄",
     ["maquiagem", "cabelo", "barba", "unha", "skincare"]),
    ("beleza.maquiagem", 2, "beleza", "Maquiagem", "Makeup", "💄",
     ["maquiagem", "makeup", "cosmético"]),
    ("beleza.maquiagem.batom", 3, "beleza.maquiagem", "Batom", "Lipstick", "💄",
     ["batom", "lipstick", "lip gloss"]),
    ("beleza.maquiagem.base_maquiagem", 3, "beleza.maquiagem", "Base", "Foundation", "💄",
     ["base", "foundation", "concealer"]),
    ("beleza.maquiagem.paleta", 3, "beleza.maquiagem", "Paleta", "Palette", "💄",
     ["paleta", "palette", "sombra"]),
    ("beleza.maquiagem.kit_maquiagem", 3, "beleza.maquiagem", "Kit", "Kit", "💄",
     ["kit", "conjunto"]),
    ("beleza.cabelo", 2, "beleza", "Cabelo", "Hair", "💇",
     ["cabelo", "hair", "secador", "alisador"]),
    ("beleza.cabelo.secador", 3, "beleza.cabelo", "Secador", "Hair Dryer", "💇",
     ["secador", "dryer"]),
    ("beleza.cabelo.alisador", 3, "beleza.cabelo", "Alisador", "Straightener", "💇",
     ["alisador", "straightener", "chapinha"]),
    ("beleza.barba", 2, "beleza", "Barba", "Beard", "🧔",
     ["barba", "beard", "máquina"]),
    ("beleza.barba.maquina_barba", 3, "beleza.barba", "Máquina", "Trimmer", "🧔",
     ["máquina", "trimmer", "aparador"]),
    ("beleza.unha", 2, "beleza", "Unha", "Nails", "💅",
     ["unha", "nail", "esmalte"]),
    ("beleza.skincare", 2, "beleza", "Skincare", "Skincare", "🧴",
     ["skincare", "hidratante", "protetor solar"]),

    # N1: pets
    ("pets", 1, None, "Pet Shop", "Pet Shop", "🐾",
     ["pet", "cachorro", "gato", "coleira"]),
    ("pets.caes", 2, "pets", "Cães", "Dogs", "🐾",
     ["cachorro", "cães", "dog"]),
    ("pets.caes.brinquedo_caes", 3, "pets.caes", "Brinquedos", "Toys", "🐾",
     ["brinquedo", "toy", "osso"]),
    ("pets.caes.coleira", 3, "pets.caes", "Coleiras", "Collars", "🐾",
     ["coleira", "collar", "peitoral"]),
    ("pets.caes.cama_caes", 3, "pets.caes", "Camas", "Beds", "🐾",
     ["cama", "bed", "colchonete"]),
    ("pets.gatos", 2, "pets", "Gatos", "Cats", "🐱",
     ["gato", "cats", "felino"]),
    ("pets.gatos.arranhador", 3, "pets.gatos", "Arranhadores", "Scratchers", "🐱",
     ["arranhador", "scratcher"]),
    ("pets.gatos.brinquedo_gatos", 3, "pets.gatos", "Brinquedos", "Toys", "🐱",
     ["brinquedo", "toy", "bolinha"]),

    # N1: infantis
    ("infantis", 1, None, "Infantil & Brinquedos", "Kids & Toys", "🧸",
     ["brinquedo", "infantil", "criança", "kids", "toy"]),
    ("infantis.bonecos", 2, "infantis", "Bonecos & Action Figures", "Action Figures", "🧸",
     ["boneco", "action figure"]),
    ("infantis.lego", 2, "infantis", "Blocos & Montar", "Building Blocks", "🧱",
     ["lego", "bloco", "montar"]),
    ("infantis.puzzles", 2, "infantis", "Quebra-Cabeça", "Puzzles", "🧩",
     ["quebra-cabeça", "puzzle"]),
    ("infantis.carrinho_controle", 2, "infantis", "Controle Remoto", "Remote Control", "🏎️",
     ["controle remoto", "remote control", "rc"]),
    ("infantis.educativos", 2, "infantis", "Educativos", "Educational", "📚",
     ["educativo", "educational"]),

    # N1: esportes
    ("esportes", 1, None, "Esportes & Lazer", "Sports & Leisure", "🏋️",
     ["esporte", "academia", "yoga", "fitness"]),
    ("esportes.academia", 2, "esportes", "Academia & Fitness", "Gym & Fitness", "🏋️",
     ["academia", "gym", "fitness"]),
    ("esportes.academia.yoga_mat", 3, "esportes.academia", "Tapete Yoga", "Yoga Mat", "🧘",
     ["yoga", "mat", "tapete", "pilates"]),
    ("esportes.academia.halteres", 3, "esportes.academia", "Halteres", "Dumbbells", "🏋️",
     ["halteres", "dumbbells", "peso"]),
    ("esportes.academia.corda_pular", 3, "esportes.academia", "Corda Pular", "Jump Rope", "🏃",
     ["corda", "jump rope"]),
    ("esportes.ciclismo", 2, "esportes", "Ciclismo", "Cycling", "🚴",
     ["bicicleta", "bike", "ciclismo"]),
    ("esportes.ciclismo.capacete_bike", 3, "esportes.ciclismo", "Capacete", "Helmet", "⛑️",
     ["capacete", "helmet"]),
    ("esportes.camping", 2, "esportes", "Camping", "Camping", "⛺",
     ["camping", "barraca"]),
    ("esportes.camping.barraca", 3, "esportes.camping", "Barraca", "Tent", "⛺",
     ["barraca", "tent"]),
    ("esportes.camping.sleeping_bag", 3, "esportes.camping", "Saco Dormir", "Sleeping Bag", "🛏️",
     ["saco", "sleeping bag"]),
    ("esportes.praia", 2, "esportes", "Praia", "Beach", "🏖️",
     ["praia", "beach"]),
    ("esportes.aventura", 2, "esportes", "Aventura", "Adventure", "🏔️",
     ["aventura", "adventure", "trekking"]),

    # N1: casa
    ("casa", 1, None, "Casa & Decoração", "Home & Decor", "🏠",
     ["casa", "decoração", "organizador", "cortina"]),
    ("casa.organizacao", 2, "casa", "Organização", "Organization", "📦",
     ["organizador", "organização", "storage"]),
    ("casa.banheiro", 2, "casa", "Banheiro", "Bathroom", "🚿",
     ["banheiro", "bathroom", "toalha"]),
    ("casa.quarto", 2, "casa", "Quarto", "Bedroom", "🛏️",
     ["quarto", "bedroom", "cortina"]),
    ("casa.limpeza", 2, "casa", "Limpeza", "Cleaning", "🧹",
     ["limpeza", "cleaning", "aspirador"]),
    ("casa.limpeza.aspirador", 3, "casa.limpeza", "Aspirador", "Vacuum", "🧹",
     ["aspirador", "vacuum"]),
    ("casa.limpeza.aspirador_robo", 3, "casa.limpeza", "Aspirador Robô", "Robot Vacuum", "🤖",
     ["robô", "robot"]),

    # N1: ferramentas
    ("ferramentas", 1, None, "Ferramentas", "Tools", "🔧",
     ["ferramenta", "furadeira", "parafusadeira", "alicate"]),
    ("ferramentas.manuais", 2, "ferramentas", "Manuais", "Hand Tools", "🔧",
     ["manual", "chave", "alicate"]),
    ("ferramentas.manuais.chave_fenda", 3, "ferramentas.manuais", "Chave Fenda", "Screwdriver", "🪛",
     ["fenda", "phillips"]),
    ("ferramentas.manuais.alicate", 3, "ferramentas.manuais", "Alicate", "Pliers", "🔧",
     ["alicate", "pliers"]),
    ("ferramentas.eletricas", 2, "ferramentas", "Elétricas", "Power Tools", "⚡",
     ["elétrica", "furadeira", "parafusadeira"]),
    ("ferramentas.eletricas.furadeira", 3, "ferramentas.eletricas", "Furadeira", "Drill", "🔧",
     ["furadeira", "drill"]),
    ("ferramentas.eletricas.parafusadeira", 3, "ferramentas.eletricas", "Parafusadeira", "Screwdriver", "🔧",
     ["parafusadeira", "impact driver"]),
    ("ferramentas.medicao", 2, "ferramentas", "Medição", "Measuring", "📏",
     ["medição", "trena", "nível"]),
    ("ferramentas.kits_ferramentas", 2, "ferramentas", "Kits & Conjuntos", "Kits & Sets", "🧰",
     ["kit", "conjunto"]),

    # N1: cozinha
    ("cozinha", 1, None, "Cozinha & Utensílios", "Kitchen & Utensils", "🍳",
     ["cozinha", "kitchen", "panela", "faqueiro"]),
    ("cozinha.panelas", 2, "cozinha", "Panelas", "Pots & Pans", "🍳",
     ["panela", "pot", "frigideira"]),
    ("cozinha.facas", 2, "cozinha", "Facas", "Knives", "🔪",
     ["faca", "knife"]),
    ("cozinha.utensilios", 2, "cozinha", "Utensílios", "Utensils", "🥄",
     ["utensílio", "utensil", "espátula"]),
    ("cozinha.copos", 2, "cozinha", "Copos & Canecas", "Cups & Mugs", "☕",
     ["copo", "caneca", "garrafa"]),

    # N1: iluminacao
    ("iluminacao", 1, None, "Iluminação", "Lighting", "💡",
     ["lâmpada", "led", "fita led", "luz"]),
    ("iluminacao.lampadas", 2, "iluminacao", "Lâmpadas", "Bulbs", "💡",
     ["lâmpada", "bulb", "led"]),
    ("iluminacao.lampadas.led_smart", 3, "iluminacao.lampadas", "Smart Bulb", "Smart Bulb", "💡",
     ["smart", "wifi", "alexa"]),
    ("iluminacao.lampadas.led_rgb", 3, "iluminacao.lampadas", "RGB", "RGB", "🌈",
     ["rgb", "color"]),
    ("iluminacao.fitas_led", 2, "iluminacao", "Fitas LED", "LED Strips", "✨",
     ["fita led", "led strip"]),
    ("iluminacao.luminarias", 2, "iluminacao", "Luminárias", "Lamps", "🪔",
     ["luminária", "abajur"]),
    ("iluminacao.luz_noturna", 2, "iluminacao", "Luz Noturna", "Night Light", "🌙",
     ["luz noturna", "night light"]),
    ("iluminacao.iluminacao_exterior", 2, "iluminacao", "Exterior", "Outdoor", "🌳",
     ["exterior", "outdoor", "lanterna"]),

    # N1: saude
    ("saude", 1, None, "Saúde & Bem-Estar", "Health & Wellness", "🏥",
     ["saúde", "health", "massagem", "termômetro"]),
    ("saude.massagem", 2, "saude", "Massagem", "Massage", "💆",
     ["massagem", "massage", "massagador"]),
    ("saude.massagem.pistola_massagem", 3, "saude.massagem", "Pistola", "Massage Gun", "🔫",
     ["pistola", "gun", "percussão"]),
    ("saude.massagem.massager_cervical", 3, "saude.massagem", "Cervical", "Cervical", "💆",
     ["cervical", "pescoço"]),
    ("saude.monitoramento", 2, "saude", "Monitoramento", "Monitoring", "📊",
     ["monitoramento", "monitor", "medição"]),
    ("saude.monitoramento.termometro", 3, "saude.monitoramento", "Termômetro", "Thermometer", "🌡️",
     ["termômetro", "thermometer"]),
    ("saude.monitoramento.oximetro", 3, "saude.monitoramento", "Oxímetro", "Pulse Oximeter", "🫁",
     ["oxímetro", "oximeter"]),
    ("saude.ortopedia", 2, "saude", "Ortopedia", "Orthopedics", "🦴",
     ["ortopedia", "orthopedic", "cinta"]),

    # N1: automotivo
    ("automotivo", 1, None, "Automotivo", "Automotive", "🚗",
     ["carro", "automotivo", "car", "veículo"]),
    ("automotivo.interior", 2, "automotivo", "Interior", "Interior", "🚗",
     ["interior", "dentro do carro"]),
    ("automotivo.interior.suporte_celular_car", 3, "automotivo.interior", "Suporte Celular", "Phone Mount", "📱",
     ["suporte", "phone mount", "ventosa"]),
    ("automotivo.exterior_car", 2, "automotivo", "Exterior", "Exterior", "🚙",
     ["exterior", "fora do carro"]),
    ("automotivo.exterior_car.camera_re", 3, "automotivo.exterior_car", "Câmera Ré", "Reverse Camera", "📷",
     ["câmera ré", "reverse"]),
    ("automotivo.eletrica_car", 2, "automotivo", "Elétrica", "Electrical", "⚡",
     ["elétrica", "bateria", "compressor"]),
    ("automotivo.eletrica_car.compressor", 3, "automotivo.eletrica_car", "Compressor", "Compressor", "💨",
     ["compressor", "pneu", "inflador"]),

    # N1: moda
    ("moda", 1, None, "Moda & Acessórios", "Fashion & Accessories", "👗",
     ["bolsa", "óculos", "cinto", "chapéu", "mochila"]),
    ("moda.bolsas", 2, "moda", "Bolsas", "Bags", "👜",
     ["bolsa", "bag", "mochila"]),
    ("moda.bolsas.bolsa_mao", 3, "moda.bolsas", "Mão", "Handbag", "👜",
     ["mão", "handbag"]),
    ("moda.bolsas.bolsa_costas", 3, "moda.bolsas", "Costas/Mochila", "Backpack", "🎒",
     ["costas", "backpack", "mochila"]),
    ("moda.oculos", 2, "moda", "Óculos", "Glasses", "🕶️",
     ["óculos", "glasses"]),
    ("moda.oculos.oculos_sol", 3, "moda.oculos", "Sol", "Sunglasses", "🕶️",
     ["sol", "sunglasses", "uv"]),
    ("moda.oculos.oculos_blue", 3, "moda.oculos", "Blue Light", "Blue Light", "💻",
     ["blue light", "luz azul"]),
    ("moda.chapeus", 2, "moda", "Chapéus", "Hats", "🎩",
     ["chapéu", "hat", "boné"]),

    # N1: papelaria
    ("papelaria", 1, None, "Papelaria & Escritório", "Stationery & Office", "📝",
     ["papelaria", "escritório", "caneta", "caderno"]),
    ("papelaria.canetas", 2, "papelaria", "Canetas", "Pens", "🖊️",
     ["caneta", "pen", "gel"]),
    ("papelaria.cadernos", 2, "papelaria", "Cadernos", "Notebooks", "📓",
     ["caderno", "notebook", "bloco"]),
    ("papelaria.organizacao_escrit", 2, "papelaria", "Organização", "Organization", "🗂️",
     ["organizador", "prancheta"]),

    # N1: jardim
    ("jardim", 1, None, "Jardim & Plantio", "Garden & Planting", "🌱",
     ["jardim", "garden", "planta", "vaso"]),
    ("jardim.regador", 2, "jardim", "Regador/Aspersor", "Watering", "💧",
     ["regador", "aspersor"]),
    ("jardim.ferramentas_jardim", 2, "jardim", "Ferramentas", "Tools", "🌱",
     ["ferramenta", "tool", "pá"]),
    ("jardim.iluminacao_jardim", 2, "jardim", "Iluminação", "Lighting", "☀️",
     ["iluminação", "solar"]),
    ("jardim.vasos", 2, "jardim", "Vasos", "Pots", "🪴",
     ["vaso", "pot"]),
    ("jardim.horta_hidroponia", 2, "jardim", "Hidroponia", "Hydroponics", "🌿",
     ["hidroponia", "hydroponic"]),

    # N1: calcados
    ("calcados", 1, None, "Calçados", "Footwear", "👟",
     ["sapato", "tênis", "chinelo", "sandália"]),
    ("calcados.tenis", 2, "calcados", "Tênis", "Sneakers", "👟",
     ["tênis", "sneaker"]),
    ("calcados.chinelo", 2, "calcados", "Chinelo", "Slippers", "🩴",
     ["chinelo", "slipper"]),
    ("calcados.sandalia", 2, "calcados", "Sandália", "Sandals", "👡",
     ["sandália", "sandal"]),
    ("calcados.botina", 2, "calcados", "Botina", "Boots", "🥾",
     ["botina", "boot"]),

    # N1: moveis
    ("moveis", 1, None, "Móveis & Organização", "Furniture & Organization", "🪑",
     ["móvel", "furniture", "cadeira", "mesa"]),
    ("moveis.cadeiras", 2, "moveis", "Cadeiras", "Chairs", "🪑",
     ["cadeira", "chair"]),
    ("moveis.mesas", 2, "moveis", "Mesas", "Tables", "🪵",
     ["mesa", "table"]),
    ("moveis.prateleiras", 2, "moveis", "Prateleiras", "Shelves", "📚",
     ["prateleira", "shelf", "estante"]),
]

def create_tables():
    """Create taxonomy table and add columns to arbitlens_products."""
    conn = get_pg_conn()
    cursor = conn.cursor()

    # Create taxonomy table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taxonomy (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(200) UNIQUE NOT NULL,
            level INTEGER NOT NULL,
            parent_slug VARCHAR(200),
            name_pt VARCHAR(200) NOT NULL,
            name_en VARCHAR(200),
            icon VARCHAR(10),
            keywords TEXT[],
            product_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Add category columns to arbitlens_products if not exists
    for col in ['category_n2', 'category_n3', 'category_n4', 'category_path']:
        try:
            cursor.execute(f"ALTER TABLE arbitlens_products ADD COLUMN {col} VARCHAR(200)")
        except Exception:
            pass  # Column already exists

    # Create indexes
    for idx, col in [
        ('idx_products_cat2', 'category_n2'),
        ('idx_products_cat3', 'category_n3'),
        ('idx_products_cat4', 'category_n4'),
        ('idx_products_path', 'category_path'),
        ('idx_taxonomy_level', 'level'),
        ('idx_taxonomy_parent', 'parent_slug'),
    ]:
        try:
            table = 'taxonomy' if 'taxonomy' in idx else 'arbitlens_products'
            cursor.execute(f"CREATE INDEX {idx} ON {table}({col})")
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("✅ Tables created")

def populate_taxonomy():
    """Insert taxonomy data."""
    conn = get_pg_conn()
    cursor = conn.cursor()

    inserted = 0
    for slug, level, parent, name_pt, name_en, icon, keywords in TAXONOMY:
        try:
            cursor.execute("""
                INSERT INTO taxonomy (slug, level, parent_slug, name_pt, name_en, icon, keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET
                    name_pt = EXCLUDED.name_pt,
                    name_en = EXCLUDED.name_en,
                    icon = EXCLUDED.icon,
                    keywords = EXCLUDED.keywords
            """, (slug, level, parent, name_pt, name_en, icon, keywords))
            inserted += 1
        except Exception as e:
            print(f"  Error inserting {slug}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Taxonomy populated: {inserted} categories")

def backfill_products():
    """Backfill category columns from existing category data."""
    conn = get_pg_conn()
    cursor = conn.cursor()

    # Get all products with their category
    cursor.execute("""
        SELECT id, category FROM arbitlens_products
        WHERE category IS NOT NULL AND category != ''
    """)
    products = cursor.fetchall()
    print(f"  Products to backfill: {len(products)}")

    updated = 0
    for prod_id, category in products:
        # Find matching taxonomy entries
        cursor.execute("SELECT slug, level FROM taxonomy WHERE slug = %s OR slug LIKE %s ORDER BY level",
                       (category, f"{category}.%"))
        tax_entries = cursor.fetchall()

        cat_n2 = None
        cat_n3 = None
        cat_n4 = None

        for slug, level in tax_entries:
            if level == 2:
                cat_n2 = slug.split('.')[-1]
            elif level == 3:
                cat_n3 = slug.split('.')[-1]
            elif level == 4:
                cat_n4 = slug.split('.')[-1]

        # Build path
        parts = [category]
        if cat_n2:
            parts.append(cat_n2)
        if cat_n3:
            parts.append(cat_n3)
        if cat_n4:
            parts.append(cat_n4)
        path = '.'.join(parts)

        cursor.execute("""
            UPDATE arbitlens_products
            SET category_n2 = %s, category_n3 = %s, category_n4 = %s, category_path = %s
            WHERE id = %s
        """, (cat_n2, cat_n3, cat_n4, path, prod_id))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ Products backfilled: {updated}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Setup taxonomy')
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--populate', action='store_true')
    parser.add_argument('--backfill', action='store_true')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    if args.all or args.create:
        create_tables()
    if args.all or args.populate:
        populate_taxonomy()
    if args.all or args.backfill:
        backfill_products()

if __name__ == '__main__':
    main()
