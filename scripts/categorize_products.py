#!/usr/bin/env python3
"""
Classify products into L1/L2/L3 based on taxonomy.

Strategy:
1. First, check if existing category_l1 is in taxonomy
2. If L3 is "Geral" or L3 == L1, try to find better L3 using title keywords
3. Set category_l2 from taxonomy mapping
4. Use existing L3 if it matches a known L3 in the taxonomy

NO SCRAPING. Just DB updates based on existing data + title analysis.

Usage:
    python3 scripts/categorize_products.py --dry-run    # preview only
    python3 scripts/categorize_products.py              # apply changes
    python3 scripts/categorize_products.py --category Beleza  # only Beleza
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import TAXONOMY

import psycopg2
import psycopg2.extras

# Use .pgpass
os.environ['PGPASSFILE'] = '/tmp/.pgpass'

# ── Title keyword → L3 mapping ──────────────────────────────────
# Order matters: more specific patterns first
KEYWORD_RULES = {
    # Beleza (EN + PT)
    ("Beleza", "Skincare"): [
        # English
        (r"\btoner\b|\btonic\b|t[ôo]nico|toner\s+pads?|exfoliating\s+toner", "Limpeza Facial"),
        (r"\bcleanser\b|\bcleansing\b|oil\s+cleansing|micellar|mise[èe]la", "Limpeza Facial"),
        (r"\bpatch\b|pimple\s+patch|acne\s+patch|hydrocolloid", "Limpeza Facial"),
        (r"\bóleo\s+de\s+(?:banho|limpeza)|\bbath\s+oil\b", "Reparador"),
        (r"\bmáscara\s+de\s+tratamento\b|hair\s+mask|deep\s+mask|collagen\s+mask|bio-?collagen", "Reparador"),
        # Original
        (r"\b(?:hydrating|moisturizing|moisturizer|moisture)\s+(?:cream|lotion|gel)|facial\s+moisturizer|face\s+cream", "Hidratante Facial"),
        (r"body\s+(?:lotion|moisturizer|cream)|body\s+butter", "Hidratante Corporal"),
        (r"\b(?:sunscreen|spf\s*\d+)|sun\s+protection|uv\s+protection", "Protetor Solar"),
        (r"\bcleanser|face\s+wash|cleansing\s+(?:gel|foam)|facial\s+cleanse", "Limpeza Facial"),
        (r"\bserum\b", "Sérum"),
        (r"\banti-?aging|retinol|wrinkle", "Antienvelhecimento"),
        (r"\bhealing\s+ointment|skin\s+protectant|repair\s+cream|ointment", "Reparador"),
        # Portuguese
        (r"hidratante\s+facial|hidrata[çc][ãa]o\s+facial|cr[ée]me\s+(?:facial|hidratante)", "Hidratante Facial"),
        (r"hidratante\s+corporal|lo[çc][ãa]o\s+hidratante|lo[çc][ãa]o\s+corporal", "Hidratante Corporal"),
        (r"protetor\s+solar|fps\s*\d+|sun\s*screen|sunscreen", "Protetor Solar"),
        (r"limpeza\s+facial|sabonete\s+facial|gel\s+de\s+limpeza|demaquilante", "Limpeza Facial"),
        (r"s[ée]rum", "Sérum"),
        (r"antienvelhecimento|anti-idade|retinol|anti\s*idade", "Antienvelhecimento"),
    ],
    ("Beleza", "Cabelo"): [
        # English
        (r"\bshampoo\b|\bshamp[^o]?", "Shampoo"),
        (r"\bconditioner\b", "Condicionador"),
        (r"\bhair\s+mask\b|deep\s+conditioner", "Máscara Capilar"),
        (r"\b(?:hair|argan)\s+oil\b", "Óleo Capilar"),
        (r"\bleave-?in\b|\bhair\s+spray\b|heat\s+protectant", "Leave-in"),
        (r"\bhair\s+serum\b|hair\s+styling", "Finalizador"),
        (r"\b(?:hair\s+)?dryer\b|\bblow\s+dryer\b|\bsecador\b", "Secador"),
        (r"\bflat\s+iron\b|\bprancha\b|\bchapinha\b|\bhair\s+straightener\b|\bplaca\s+de\s+cabelo\b", "Prancha"),
        (r"\b(?:hair\s+)?brush\b|\bescova\s+(?:rotativa|secadora|modeladora)\b", "Escova"),
        (r"\b(?:hair\s+)?clipper\b|\bmaquina\s+de\s+cortar\s+cabelo\b|\baparador\b", "Aparador"),
        # Portuguese
        (r"shampoo|champ[ãu]", "Shampoo"),
        (r"condicionador", "Condicionador"),
        (r"m[áa]scara\s+(?:capilar|tratamento|hidrata)", "Máscara Capilar"),
        (r"[óo]leo\s+(?:capilar|reparador|reparador)", "Óleo Capilar"),
        (r"leave-?in|spray\s+(?:capilar|finalizador)", "Leave-in"),
        (r"finalizador|s[ée]rum\s+capilar", "Finalizador"),
        (r"secador\s+de\s+cabelo|prancha\s+(?:de\s+cabelo|profissional|lizze)|chapinha|escova\s+(?:rotativa|secadora|modeladora)", "Secador/Prancha"),
    ],
    ("Beleza", "Maquiagem"): [
        (r"\bmascara\b|\bm[aá]scara\s+de\s+c[ií]lios|\blash\s+sensational", "Máscara de Cílios"),
        (r"\b(?:eye|eye-)?liner\b|\b(?:eye-)?l[eé]is\b|\blapis\b", "Lápis/Liner"),
        (r"\bbrow\s+pencil\b|\bbrow\s+gel\b|\b(?:lapis|gel)\s+de\s+sobrancelha\b", "Sobrancelha"),
        (r"\b(?:lip|batom|gloss)\b|\bbatom\b|\blip\s+gloss\b|\bgloss\s+labial\b", "Batom/Gloss"),
        (r"\b(?:foundation|base\b|concealer|primer|contorno|p[oó]\b|blush|bronzer|iluminador|highlighter)", "Base"),
        (r"\bnail\s+polish\b|\besmalte\b", "Esmalte"),
    ],
    ("Beleza", "Banho e Corpo"): [
        (r"\bsabonete\b|\bsoap\b|\bbarra\s+de\s+sabonete\b", "Sabonete"),
        (r"\bbody\s+(?:wash|lotion|cream|spray|butter|scrub|oil|gel|mist|sponge|loofah|loofa|brush|brushes)\b|\bhidratante\s+corporal\b|\blo[cçc][ãa]o\s+(?:corporal|hidratante)\b|\bgel\s+de\s+banho\b|\b[sáa]b[eê]on\b", "Higiene Corporal"),
    ],
    ("Beleza", "Maquiagem"): [
        (r"batom|gloss|labial", "Batom"),
        (r"m[áa]scara\s+de\s+c[íi]lios|rimel|colossal", "Máscara de Cílios"),
        (r"\bmascara\b|\bmakeup\b|\blash\s+sensational\b|\blash\s+princess\b|\bfalse\s+lash\b|\bsky\s+high\b", "Máscara de Cílios"),
        (r"base\s+(?:l[íi]quida|matte)", "Base"),
        (r"corretivo|concealer", "Corretivo"),
        (r"p[óo]\s+(?:compacto|transl[úu]cido)", "Pó"),
        (r"\b(?:eye|eye-)?liner\b|\b(?:eye-)?l[eé]is\b|\blapis\b|\bcolorstay\b|\bwaterproof\b", "Lápis/Liner"),
        (r"\bbrow\s+pencil\b|\bbrow\s+gel\b|\binstant\s+lift\b|\b(?:lapis|gel)\s+de\s+sobrancelha\b", "Sobrancelha"),
    ],
    ("Beleza", "Higiene"): [
        # English
        (r"\bbar\s+soap\b|\bhand\s+soap\b|\bbody\s+wash\b|\bsoap\s+bar\b", "Sabonete"),
        (r"\bdeodorant\b|antiperspirant", "Desodorante"),
        (r"\bintimate\s+(?:wash|soap)\b|feminine\s+wash", "Higiene Íntima"),
        # Portuguese
        (r"sabonete\s+em\s+barra|sabonete\s+l[íi]quido", "Sabonete"),
        (r"desodorante|antitranspirante|roll\s*on", "Desodorante"),
        (r"higiene\s+[íi]ntima|[íi]ntimo\s+feminino", "Higiene Íntima"),
    ],
    ("Beleza", "Barbear"): [
        (r"aparador\s+de\s+pelos|aparador\s+barbeador|trimmer", "Aparador"),
        (r"barbeador|l[âa]mina\s+de\s+barbear", "Barbeador"),
        (r"espuma\s+de\s+barbear|gel\s+de\s+barbear", "Espuma"),
    ],
    ("Beleza", "Corpo & Banho"): [
        # English
        (r"\b(?:exfoli?ator|scrub)\b", "Esfoliante"),
        (r"\bbody\s+oil\b|\bbath\s+oil\b", "Óleo Corporal"),
        (r"\b(?:healing|repair)\s+(?:ointment|cream)|ointment\s+for", "Reparador"),
        (r"\bcotton\s+swabs?\b|\bcotton\s+rounds?\b|\bepsom\s+salt\b", "Reparador"),
        # Portuguese
        (r"esfoliante|scrub", "Esfoliante"),
        (r"[óo]leo\s+(?:corporal|bronzeador|para\s+o\s+corpo)", "Óleo Corporal"),
        (r"reparador\s+(?:capilar|para\s+o\s+rosto|labial)", "Reparador"),
    ],
    # Bebê
    ("Bebê", "Fraldas & Lenços"): [
        (r"fralda|pampers|huggies", "Fralda Descartável"),
        (r"len[çc]o\s+umedecido|len[çc]os\s+umedecidos", "Lenço Umedecido"),
    ],
    ("Bebê", "Roupas"): [
        (r"body\s+(?:longo|curto|para\s+beb[êe])|bodies", "Body"),
        (r"conjunto\s+(?:de\s+)?roupa|kit\s+roupa", "Conjunto"),
        (r"pijama\s+(?:beb[êe]|infantil)", "Pijama"),
        (r"macac[ãa]o", "Macacão"),
    ],
    ("Bebê", "Brinquedos"): [
        (r"mordedor|mordedores", "Mordedor"),
        (r"chocalho|chocalhos", "Chocalho"),
        (r"estimula[çc][ãa]o\s+visual|estimula[çc][ãa]o\s+precoce", "Estimulação"),
    ],
    ("Bebê", "Alimentação"): [
        (r"mamadeira|mamaderas|baby\s+bottle|bottle\s+nipple", "Mamadeira"),
        (r"copo\s+(?:com\s+bico|treinamento)|sippy\s+cup|straw\s+cup|training\s+cup", "Copo com Bico"),
        (r"prato\s+(?:de\s+beb[êe]|infantil)|pratinho|baby\s+plate", "Prato"),
    ],
    ("Bebê", "Higiene"): [
        (r"shampoo\s+(?:beb[êe]|infantil|baby|shamppoo\s+bebe)", "Shampoo"),
        (r"\b2.?in.?1.*(?:baby\s+)?shampoo\b|\bbody\s+wash.*(?:tear.?free|hypoallergenic)\b|\b(?:honest|cetaphil)\b", "Shampoo"),
        (r"sabonete\s+(?:beb[êe]|infantil|baby\s+wash)", "Sabonete"),
        (r"pomada\s+(?:anti-?assadura|para\s+assadura)|diaper\s+rash", "Pomada"),
        (r"\bbaby\s+wipes\b|wipes|len[çc]o\s+umedecido|water\s*wipes", "Sabonete"),
        (r"\bgas\s+relief\b|infant\s+drops|mylicon", "Shampoo"),
    ],
    ("Bebê", "Quarto"): [
        (r"swaddle|sleep\s+sack|saco\s+de\s+dormir", "Swaddle"),
        (r"\btoalha.*beb[eê]\b|\bbaby\s+towel\b|\bhooded\s+towel\b", "Toalha"),
    ],
    ("Bebê", "Mobilidade"): [
        (r"canguru|baby\s+carrier|ergon[ôo]mico.*beb[eê]|carrier\s+for", "Canguru"),
        (r"cadeira\s+(?:para\s+)?alimenta[çc][ãa]o|high\s+chair", "Cadeira Alimentação"),
    ],
    ("Bebê", "Alimentação"): [
        (r"\b(?:orgain|pediasure|Ensure|kids)\b.*\bdrink|\bkids.*protein.*shake\b|\bnutritional.*shake\b", "Bebida"),
        (r"\b(?:kit|prato)\s+(?:refei[çc][ãa]o|babador|copo|talher)|\bbabador\b|\bbaby\s+bib\b|\bbibs\b", "Refeição"),
    ],
    ("Bebê", "Mobilidade"): [
        (r"carrinho\s+(?:de\s+beb[êe]|para\s+beb[êe])|baby\s+stroller|stroller", "Carrinho"),
        (r"beb[êe]\s+conforto|ber[çc]o\s+auto|car\s+seat", "Bebê Conforto"),
        (r"cadeirinha\s+(?:para\s+carro|auto)|high\s+chair|cadeira\s+alimenta[çc][ãa]o", "Cadeirinha"),
        (r"bicicleta\s+(?:de\s+equil[íi]brio|infantil|beb[êe])|balance\s+bike", "Carrinho"),  # baby balance bikes
    ],
    ("Bebê", "Fraldas & Lenços"): [
        (r"\bdiapers?\b|\bfralda\b", "Fralda Descartável"),
        (r"potty\s+training|pull-?ups|treinamento\s+penico|penico", "Fralda Descartável"),
    ],
    # Wearables
    ("Wearables", "Smartwatch"): [
        (r"amazfit", "Amazfit"),
        (r"apple\s*watch", "Apple Watch"),
        (r"galaxy\s*watch|samsung\s*(?:watch|galaxy)", "Samsung"),
        (r"mi\s*watch|xiaomi|redmi", "Xiaomi"),
        (r"smartwatch|smart\s*watch|relogio\s+inteligente|rel[óo]gio\s+inteligente", "Outros"),
    ],
    ("Wearables", "Pulseira Fitness"): [
        (r"mi\s*band|xiaomi\s+band|smart\s*band", "Mi Band"),
        (r"honor\s*band|huawei", "Honor"),
        (r"pulseira\s+(?:inteligente|fitness|smart|fitness)", "Outros"),
    ],
    # Brinquedos
    ("Brinquedos", "Educativo"): [
        (r"quebra-?cabe[çc]a|puzzle", "Quebra-cabeça"),
        (r"bloco\s+de\s+montar|lego|blocos", "Blocos de Montar"),
        (r"jogo\s+(?:educativo|pedag[óo]gico)", "Jogo Educativo"),
    ],
    ("Brinquedos", "Pelúcia"): [
        (r"pel[úu]cia|peluche", "Personagem"),
        (r"urso\s+de\s+pel[úu]cia|ursinho", "Animal"),
    ],
    ("Brinquedos", "Bonecos"): [
        (r"action\s*figure|figura\s+de\s+a[çc][ãa]o|buzz\s+lightyear", "Action Figure"),
        (r"boneca|barbie", "Boneca"),
        (r"carrinho\s+de\s+brinquedo|hot\s*wheels", "Carrinho"),
    ],
    ("Brinquedos", "Jogos"): [
        (r"jogo\s+de\s+tabuleiro|boardgame|caiu\s+perdeu", "Tabuleiro"),
        (r"jogo\s+de\s+cartas|baralho|playing\s+cards|poker\s+cards|\b54\s+cartas\b|cartas\b|\bsleeves\b|card\s+sleeves|tcg|flip\s*7", "Cartas"),
        (r"\bpokemon\s+(?:cards?|cards|booster|collection|ex|gx|tcg)|pok[ée]mon", "Cartas"),
        (r"fantasia|disfarce", "Fantasias"),
    ],
    ("Brinquedos", "Pelúcia"): [
        (r"\bsquishy\b|squishies|slow\s+rising|mochi", "Personagem"),
        (r"\bslime\b|\bslimy\b", "Personagem"),
    ],
    ("Brinquedos", "Educativo"): [
        (r"\blápis\s+de\s+cor|lápis|coloring|\bcrayon\b|caneta|\bpencil\b", "Blocos de Montar"),
        (r"\bballoon\b|bal[ãa]o|bal[õo]es|latex\s+balloon|foil\s+balloon|number\s+balloon|party\s+favors", "Blocos de Montar"),  # group as party/decoration
    ],
    ("Brinquedos", "Bonecos"): [
        (r"\bbicicleta\s+(?:de\s+equil[íi]brio|infantil)|balance\s+bike|\bbike\b", "Carrinho"),
    ],
    ("Brinquedos", "Bonecos"): [
        (r"\bbicicleta\s+(?:de\s+equil[íi]brio|infantil)|balance\s+bike", "Carrinho"),
    ],
    ("Brinquedos", "Eletrônicos"): [
        (r"\bballoon\b|bal[ãa]o|bal[õo]es|latex\s+balloon|foil\s+balloon|number\s+balloon", "Robô"),  # Wrong L3, will fallback
    ],
    ("Brinquedos", "Massinha"): [
        (r"massinha|massa\s+(?:de|para)\s+modelar|play\.?doh|modelar\b|guache\b|tempera\s+guache|tinta\s+guache", "Massinha"),
    ],
    ("Brinquedos", "Livros"): [
        (r"livr[ãa]o|livro.*colorir|coloring\s+book|primeiras\s+palavras|mang[áa]|jujutsu|naruto|black\s+clover|haiyku|demons\s+slayer|chainsaw\s+man|attack\s+on\s+titan|tower\s+of\s+god", "Livro"),
    ],
    ("Brinquedos", "Festa"): [
        (r"balloon|balloons|garland|party\s+supplies|party\s+favors|bal[ãa]o|bal[õo]es|latex\s+balloon|foil\s+balloon|number\s+balloon", "Balão"),
    ],
    ("Brinquedos", "Coleção"): [
        (r"figurinha|sticker|stickers|album.*figurinha|[áa]lbum.*figurinha|cromos|panini|copa\s+do?\s+mundo|fifa\s*2026|world\s*cup\s*2026", "Figurinhas"),
    ],
    ("Brinquedos", "Veículos"): [
        (r"caminh[ãa]o|caminhonete|carrinho|carrinhos|ve[ií]culo|hot\s+wheels|truck\b|truck\s+toy", "Carrinho"),
    ],
    ("Brinquedos", "Sensory"): [
        (r"squeeze|squishy|slow\s+rising|mochi|neon\s+doh|fidget", "Sensory"),
    ],
    ("Brinquedos", "Bebê"): [
        (r"chocalho|mordedor|argola|wrist\s+rattle|foot\s+finder|pir[âa]mide\s+de\s+argolas|brinquedo.*beb[eê]\b|beb[eê]\s*brinquedo", "Bebê"),
    ],
    ("Brinquedos", "Cubo Mágico"): [
        (r"cubo\s+m[áa]gico|rubik|pega\s+varetas", "Cubo Mágico"),
    ],
    ("Brinquedos", "Outros"): [
        (r"apito|chocalho|cofre\s+infantil|berimbau|viol[ãa]o\s+infantil|teclado\s+infantil|leapfrog|learning\s+friends|date\s+night\s+dice", "Outros"),
    ],
    # Moda
    ("Moda", "Roupas"): [
        (r"\bjaqueta\b|jacket", "Jaqueta"),
        (r"\bcal[çc]a\b|legging|jeans", "Calça"),
        (r"\bblusa\b|camisa\s+social", "Blusa"),
        (r"\bcamisa\b|polo", "Camisa"),
        (r"\bsaia\b", "Saia"),
        (r"\bvestido\b", "Vestido"),
        (r"\bshort\b|bermuda", "Short"),
        (r"moletom|canguru|sweatshirt", "Moletom"),
    ],
    ("Moda", "Acessórios"): [
        (r"bon[ée]|chapeu|chapéu", "Chapéu"),
        (r"\bbelt\b|cinto|faixa", "Cinto"),
        (r"len[çc]o\s+(?:feminino|de\s+cabelo)|bandana", "Lenço"),
        (r"gravata|gravata\s+tradicional", "Gravata"),
        (r"cachecol|pashmina", "Cachecol"),
    ],
    ("Moda", "Calçados"): [
        (r"chinelo|rasteirinha|slide", "Chinelo"),
        (r"t[êe]nis|sapatilha|esportivo", "Tênis"),
        (r"sapato\s+(?:social|masculino|feminino)", "Sapato"),
        (r"sand[áa]lia", "Sandália"),
    ],
    ("Moda", "Banho"): [
        (r"toalha\s+de\s+banho|toalha\s+de\s+rosto|jogo\s+de\s+toalha", "Toalha"),
        (r"roup[ãa]o\s+de\s+banho|roup[ãa]o", "Roupão"),
        (r"touca\s+de\s+banho|touca\s+(?:de\s+)?nata[çc][ãa]o", "Touca"),
    ],
    # Audio
    ("Audio", "Fones"): [
        (r"fone\s+bluetooth|fone\s+sem\s+fio|fone\s+tws|earbuds", "Fone Bluetooth"),
        (r"fone\s+(?:de\s+ouvido\s+)?(?:com\s+fio|cabe[çc]o|fio)|headphone\s+com\s+fio", "Fone com Fio"),
        (r"fone\s+gamer|headset\s+gamer|headphone\s+gamer", "Fone Gamer"),
        (r"headset|fone\s+de\s+ouvido", "Headset"),
    ],
    ("Audio", "Caixas de Som"): [
        (r"caixa\s+de\s+som\s+(?:port[áa]til|bluetooth|wireless)|jbl\s+(?:clip|flip|charge|go|xtreme|boombox)", "Portátil"),
        (r"echo\s+dot|alexa|google\s+home|smart\s*speaker", "Smart Speaker"),
        (r"soundbar|home\s*theater|home\s*theatre", "Home Theater"),
    ],
    ("Audio", "Microfones"): [
        (r"microfone\s+(?:de\s+)?lapela|lavalier|lapela", "Lapela Sem Fio"),
        (r"microfone\s+(?:condensador|profissional|usb)", "Condensador"),
        (r"microfone\s+din[âa]mico|sm58|sm7b|handheld", "Dinâmico"),
        (r"microfone\s+(?:para\s+)?podcast|streaming|transmiss[ãa]o|rode\s+(?:videomic|nt-)", "Podcast/Streaming"),
    ],
    ("Audio", "Players"): [
        (r"dvd|blu-?ray", "DVD/Blu-ray"),
        (r"mp[3-5]\s+player|ipod", "MP3 Player"),
        (r"toca-?disco|vitrola", "Toca-Disco"),
    ],
    # Bolsas
    ("Bolsas", "Feminina"): [
        (r"bolsa\s+(?:feminina|festa|transversal|tote|sacola|ombro)", "Tote"),  # Will refine
        (r"clutch|bolsa\s+de\s+festa|bolsa\s+de\s+casamento", "Festa"),
    ],
    ("Bolsas", "Viagem"): [
        (r"mala\s+(?:de\s+viagem|bordo|grande|pequena)", "Mala Bordo"),
        (r"necessaire|necessaire\s+de\s+viagem", "Necessaire"),
        (r"organizador\s+de\s+mala|cubo\s+organizador", "Organizador de Mala"),
    ],
    ("Bolsas", "Acessórios"): [
        (r"carteira\s+(?:masculina|feminina)", "Carteira"),
        (r"porta-?cart[õo]es|card\s*holder", "Porta-Cartões"),
        (r"kit\s+bolsas|kit\s+bolsa", "Kit Bolsas"),
    ],
    # Casa
    ("Casa", "Cozinha"): [
        (r"pote\s+herm[ée]tico|pote\s+de\s+vidro|pote\s+pl[áa]stico|potes\s+herm[ée]ticos|kit\s+pot[ei]s|vidro\s+herm[ée]tico|porta\s+mantimento|porta\s+tempero", "Pote Hermético"),
        (r"garrafa\s+t[ée]rmica|garrafa\s+stanley|copo\s+t[ée]rmico|modus", "Garrafa Térmica"),
        (r"copo\s+de\s+(?:cerveja|vidro|pl[áa]stico)|caneca", "Copo"),
        (r"bolsa\s+t[ée]rmica|lancheira|bolsa\s+marmita|cooler\s+bag|cooler|cooler\s+para", "Bolsa Térmica"),
    ],
    ("Casa", "Lavanderia"): [
        (r"cesto\s+de\s+bambu|cesto\s+de\s+roupa|cesto\s+para\s+lavanderia|cesto\s+suju|hamper", "Cesto"),
        (r"tapete\s+(?:de\s+entrada|para\s+entrada|door\s+mat|entryway|entrada|porta)", "Tapete de Entrada"),
    ],
    ("Casa", "Banho"): [
        (r"tapete\s+de\s+banho|tapete\s+para\s+banheiro|tapete\s+de\s+banheiro|bath\s+mat|bath\s+rug|bathroom\s+rug|bath\s+mats?|bath\s+rugs?", "Tapete de Banho"),
        (r"toalha\s+de\s+banho|toalha\s+de\s+rosto|toalha\s+de\s+m[ãa]o|bath\s+towel", "Toalha"),
        (r"box\s+para\s+banheiro|box\s+de\s+banheiro|chuveiro|shower\s+curtain", "Chuveiro"),
    ],
    ("Casa", "Móveis"): [
        (r"\bm[óo]vel\b|\bmesa\s+de\s+centro\b|\bprateleira\b|\bestante\b|\barm[áa]rio\b|\bcama\s+(?:box|infantil|queen|casal|solteiro)\b|\bsof[áa]\b|\bcadeira\s+de\s+escrit[óo]rio\b|\bcadeira\b|\bpoltrona\b|\bguarda.?roupa\b|\bc[ôo]moda\b|\bbalc[ãa]o\b", "Móvel"),
    ],
    ("Casa", "Lavanderia"): [
        (r"\bvaral\s+(?:de\s+ch[ãa]o|port[áa]til|retr[áa]til)\b|\bclothing\s+rack\b|\bdrying\s+rack\b|\bchap[ãa]\s+de\s+passar\b|\bferro\s+de\s+passar\b|\bclothesline\b", "Varal"),
    ],
    ("Casa", "Cama"): [
        (r"\btravesseiro\b|\bpillow\b|\bfronha\b|\bedredom\b|\bsheet\s+set\b|\bbed\s+sheet\b|\bled\s+(?:light|comforter|blanket|cover)\b|\bcobertor\b|\bcolcha\b|\bcobertor\b|\bcapa\s+de\+edredom\b", "Cama"),
    ],
    ("Casa", "Organização"): [
        (r"cabide|cabides|hangers", "Cabide"),
        (r"cesto\s+de\s+roupa|cesto\s+para\s+lavanderia|hamper", "Cesto"),
        (r"organizador|sapateira|shoe\s+rack|storage", "Organizador"),
        (r"lixeira|trash\s+can|garbage", "Lixeira"),
    ],
    ("Casa", "Decoração"): [
        (r"tapete\s+(?:decorativo|para\s+sala|persa|oriental)", "Tapete Decorativo"),
        (r"vaso\s+de\s+planta|vaso\s+decorativo", "Vaso"),
        (r"almofada|almofadas", "Almofada"),
    ],
    ("Casa", "Lavanderia"): [
        (r"varal\s+(?:de\s+ch[ãa]o|port[áa]til|retr[áa]til)", "Varal"),
    ],
    # Cozinha
    ("Cozinha", "Utensílios"): [
        (r"pote\s+herm[ée]tico|pote\s+de\s+pl[áa]stico|porta\s+(?:mantimento|cereal)|pote\s+de\s+vidro", "Pote"),
        (r"garrafa\s+t[ée]rmica|copo\s+t[ée]rmico", "Garrafa"),
        (r"talher|garfo|faca\s+de\s+cozinha|colher|faqueiro", "Talher"),
        (r"pipoqueira", "Pipoqueira"),
        (r"forma\s+de\s+(?:gelo|bolo)|assadeira", "Forma"),
        (r"utens[ií]lios?\s+de\s+cozinha|concha|pegador|escumadeira|amassador|abridor", "Utensílios"),
        (r"bowls?|tigelas?", "Bowl"),
        (r"c[aá]psula\s+(?:caf[eé]|nescaf[eé])|dolce\s+gusto", "Cápsula"),
    ],
    ("Cozinha", "Eletrodomésticos"): [
        (r"air\s*fryer|fritadeira\s+el[ée]trica", "Airfryer"),
        (r"cafeteira|cafeteira\s+el[ée]trica|cappuccino", "Cafeteira"),
        (r"liquidificador|processador|triturador", "Liquidificador"),
        (r"mixer\b|batedeira\b", "Mixer"),
        (r"sanduicheira|grill\s+el[ée]trico", "Sanduicheira"),
        (r"forno\s+el[ée]trico|forno\s+de\s+banco", "Forno Elétrico"),
        (r"chaleira\b", "Chaleira"),
        (r"moedor\s+de\s+caf[ée]|moinho\s+de\s+caf[ée]", "Moedor de Café"),
    ],
    # Iluminação
    ("Iluminação", "Ring Light"): [
        (r"ring\s*light|anel\s+de\s+luz", "Médio"),  # Default to medium
    ],
    ("Iluminação", "Bastão LED"): [
        (r"bast[ãa]o\s+de\s+led|bast[ãa]o\s+led|luz\s+rgb|luz\s+de\s+preenchimento", "RGB"),
    ],
    ("Iluminação", "Painel LED"): [
        (r"painel\s+led|softbox|luz\s+de\s+est[úu]dio", "Estúdio"),
    ],
    # Fotografia
    ("Fotografia", "Tripés"): [
        (r"trip[ée]\s+(?:profissional|universal|para\s+c[âa]mera|para\s+celular)|tripod", "Profissional"),
        (r"monop[ée]|monopode", "Monopé"),
    ],
    # Ferramentas
    ("Ferramentas", "Elétricas"): [
        (r"furadeira|parafusadeira", "Furadeira"),
        (r"serra\s+(?:circular|tico-?tico|el[ée]trica)|serra\s+m[áa]rmore", "Serra"),
        (r"lixadeira|esmerilhadeira", "Lixadeira"),
        (r"lavadora\s+de\s+alta\s+press[ãa]o|wap", "Lavadora"),
    ],
    ("Ferramentas", "Manuais"): [
        (r"jogo\s+de\s+(?:soquetes|chaves|ferramentas)|maleta\s+de\s+ferramentas", "Jogo de Ferramentas"),
        (r"martelo|marreta", "Martelo"),
        (r"alicate", "Alicate"),
        (r"chave\s+(?:inglesa|philips|allen|fenda|combinada)", "Chave"),
    ],
    # Esportes
    ("Esportes", "Localizadores"): [
        (r"smart\s*tag|gps\s*tracker|localizador|rastreador|air\s*tag|tile", "Smart Tag"),
    ],
    ("Esportes", "Suplementos"): [
        (r"creatina|whey\s+protein|whey|albumina|protein", "Creatina"),
        (r"bcaa|glutamina", "BCAA"),
        (r"pr[ée]-?treino|pr[ée]\s*treino|pre-workout", "Pré-treino"),
    ],
    # Praia
    ("Praia", "Mobiliário"): [
        (r"cadeira\s+de\s+praia|cadeira\s+articul", "Cadeira de Praia"),
        (r"guarda-?sol|sombrinha\s+de\s+praia", "Guarda-Sol"),
    ],
    ("Praia", "Têxtil"): [
        (r"toalha\s+de\s+praia|canga", "Toalha de Praia"),
    ],
    ("Praia", "Acessórios"): [
        (r"clips?\s+(?:de\s+praia|para\s+toalha|grande)|prendedor\s+de\s+toalha", "Clips"),
        (r"bolsa\s+t[ée]rmica|cooler\s+de\s+praia", "Bolsa Térmica"),
    ],    ("Pet Shop", "Higiene"): [
        (r"\btapete\s+higi[eê]nico\b|pet\s+pad|puppy\s+pad|fralda\s+para\s+cachorro|manta\s+fralda", "Tapete Higiênico"),
    ],
    ("Pet Shop", "Alimentação"): [
        (r"\bra[cç][ãa]o\b|\bpet\s+food\b|\b(?:dog|cat)\s+food\b|\bgolden\b|\bquatree\b|\bsupreme\b", "Ração"),
    ],
    ("Pet Shop", "Saúde"): [
        (r"\bantipulgas\b|\bsimparic\b|\bnexgard\b|\bbravecto\b|\b(?:pulgas|carrapatos)\b|\bverm[ií]fugo\b|\bvacina\b", "Antipulgas"),
    ],
    ("Pet Shop", "Brinquedos"): [
        (r"\barranhador\b|\bbrinquedo.*(?:gato|cachorro|pet)|\binterativo.*pet", "Brinquedo Pet"),
    ],
    ("Pet Shop", "Sanitário"): [
        (r"\bareia\s+sanit[áa]ria\b|\bcaixa\s+de\s+areia\b|\blitter\b", "Areia Sanitária"),
    ],
    ("Pet Shop", "Acessórios"): [
        (r"\bcama\s+(?:de\s+)?(?:gato|cachorro|pet)|\bcomedouro\b|\bbebedouro\b|\bcoleira\b|\bpeitoral\b|\broupa.*(?:cachorro|pet)|\broupinha.*pet|\broupinha\b", "Acessório Pet"),
    ],
    ("Mochilas", "Mochilas"): [
        (r"\bmochila\b.*(?:notebook|executiva|viagem|trilha|escolar|feminina|masculina|grande|refor[çc]ada|usb|couro|resistente|preto|imperme[áa]vel)", "Mochila"),
        (r"\bmochila\b", "Mochila"),
        (r"\bcapa\s+para\s+mochila\b|\bcapa\s+mochila\b", "Capa"),
    ],
    ("Moda", "Acessórios"): [
        (r"\bboina\b|\bgorro\b|\bchapéu\b|\bbon[ée]\b|\btouca\b", "Chapéu/Boné"),
        (r"\bpulseira\b|\bbracelete\b|\bcollar\b", "Pulseira"),
    ],
    ("Bolsas", "Carteira"): [
        (r"\bcarteira\b.*(?:masculina|feminina|rfid|couro)|\bcarteira\s+masculina\b|\bcarteira\s+feminina\b|\bwallet\b", "Carteira"),
        (r"\bcarteira\b", "Carteira"),
    ],
    ("Audio", "Som Automotivo"): [
        (r"\bprocessador\s+de\s+[áa]udio\b|\bcrossover\b|\bequalizador\b|\bstetsom\b", "Processador"),
        (r"\bcaixa\s+amplificada\b|\bcaixa\s+de\s+som\s+amplificada\b|\bconnect\s+lights\b", "Caixa Amplificada"),
        (r"\bboombox\b|\bbs-?01\b|\baiwa\b", "Boombox"),
    ],
    ("Bebê", "Alimentação"): [
        (r"\bcadeira\s+para\s+alimenta[çc][ãa]o\b|\bcadeira\s+de\s+alimenta[çc][ãa]o\b|\bcadeira\s+poke\b", "Cadeira"),
        (r"\bcanguru\b.*beb[eê]|\bcanguru\s+baby\b|baby\s+bear", "Canguru"),
        (r"\borgain\b.*kids|\bkids.*shake\b|\bnutritional\s+drink\b", "Bebida"),
        (r"\bforma\s+de\s+gelo\b.*papinha|\bforma.*beb[eê].*drinks|\bforma\s+de\s+gelo\b.*sil", "Forma"),
    ],
    ("Beleza", "Skincare"): [
        (r"\bcicaplast\b|\bbepantol\b|\bla\s+roche.?posay\b", "Reparador"),
        (r"\bovomaltine\b|\bcreme\s+crocante\b", "Outros"),
        (r"\bmorte\s+s[uú]bita\b|\bhidratante.*lola\b|\bm[áa]scara\s+super\s+hidratante\b", "Máscara Capilar"),
    ],
    ("Casa", "Limpeza"): [
        (r"\bsab[ãa]o\s+em\s+barra\b|\bsabonete\s+em\s+barra\b|\bsab[ãa]o\s+dove\b", "Sabão"),
        (r"\bpercarbonato\b|\btira\s+manchas\b|\balvejante\b|\bdesinfetante\b", "Limpeza"),
        (r"\bpapel\s+higi[eê]nico\b|\btoilet\s+paper\b|\bpersonal\s+vip\b", "Papel Higiênico"),
        (r"\bcesto\s+de\s+bambu\b|\bhamper\b", "Cesto"),
    ],
    ("Casa", "Banho"): [
        (r"\bdoor\s+mat\b|\bentryway\s+rug\b|\bsuper\s+absorbent\s+door\s+mat\b|\bentryway\b", "Tapete de Entrada"),
    ],
    ("Ferramentas", "Soquetes"): [
        (r"\bsoquete\b|\bjogo\s+soquetes\b|\bcatraca\b|\bsoquetes?\s+estriado\b", "Soquete"),
    ],
    ("Meias", "Meia Calça"): [
        (r"\bmeia\s+cal[cç]a\b", "Meia Calça"),
        (r"\bmeia\s+cano\s+(?:m[eé]dio|alto|baixo)\b|\bat...[oó]alhada\b|\batoalhada\b", "Cano Médio/Alto"),
    ],
    ("Bolsas", "Carteira"): [
        (r"\bcarteira\b", "Carteira"),
        (r"\bwallet\b|\brfid\b|\bporta\s+cart[ãa]o\b", "Carteira"),
    ],
    ("Moda Intima", "Cueca"): [
        (r"\bkit\s+(?:\d+\s+)?cueca\b|\bboxer\s+masculin[oa]\b|\bsandrini\b", "Cueca"),
    ],
    ("Auto", "Acessórios Auto"): [
        (r"\bautom[óo]vel\b|\bcarro\b|\bauto\b.*\bdescanso\b|\bapoio\s+para\s+a\s+cabe[çc]a\b|\benxovais\b", "Acessório Auto"),
    ],
    ("Brinquedos", "Splash/Água"): [
        (r"\bsplash\s+pond\b|\bwater\s+table\b|\bsplash\s+ez\b|\bsplash\s+pad\b|\bsplashes\b|\binfl[aá]vel\s+pool\b|\bpool\s+float\b|\bfloating\s+chair\b", "Piscina/Água"),
        (r"\bwater\s+blaster\b|\bwater\s+gun\b|\bmax\s+liquidator\b", "Pistola Água"),
        (r"\bbubbles\b|\bfubbles\b|\bbubble\s+solu[cç][ãa]o\b|\bbolha\s+de\s+sab[ãa]o\b", "Bolhas"),
        (r"\bfisher.?price\b.*procurar|\bprocurar\s+e\s+encontrar\b", "Educativo"),
    ],
    ("Brinquedos", "Presentes"): [
        (r"\bgifts?\s+for\s+(?:dad|fath)|\bgifts?\s+from\s+(?:daught|son)|\bstocking\s+stuffers?\b|\bwhite\s+elephant\b", "Presente"),
    ],
    ("Bolsas", "Necessaire"): [
        (r"\bgummy\s+rosa\b|\bfliptop\b", "Necessaire"),
    ],
    ("Brinquedos", "Artesanato"): [
        (r"\bpins\s+e\s+bottons\b|\bbuttons?\b|\bbutton\s+machine\b|\bmecolour\b", "Artesanato"),
    ],
    ("Moda", "Carteira"): [
        (r"\bcarteira\b", "Carteira"),
        (r"\bwallet\b|\brfid\b|\bporta\s+cart[ãa]o\b", "Carteira"),
    ],
    ("Moda", "Artesanato"): [
        (r"\bpins?\s+e\s+bottons?\b|\bbuttons?\b|\bbutton\s+machine\b|\bmecolour\b", "Artesanato"),
    ],
    ("Casa", "Pote"): [
        (r"\bpot[ei]s?\s+herm[ée]tic[oi]s?\b|\bkit\s+pot[ei]s\b|\bpote\s+de\s+vidro\b|\bkit\s+\d+\s+potes\b|\bvidro\s+borossilicato\b", "Pote"),
    ],
    ("Casa", "Outros"): [
        (r"\bgummy\s+rosa\b|\bfliptop\b", "Outros"),
    ],
    ("Bebê", "Industrial"): [
        (r"\bluvas?\s+nitr[ií]licas?\b", "Luvas"),
        (r"\bport[ãa]o\s+pet\b|\ba[çc]omix\b", "Outros"),
        (r"\bsab[ãa]o\s+em\s+barra\b|\bsab[ãa]o\s+dove\b", "Sabão"),
    ],
    ("Beleza", "Industrial"): [
        (r"\bpercarbonato\b|\btira\s+manchas\b|\balvejante\b", "Limpeza"),
        (r"\bpapel\s+higi[eê]nico\b|\btoilet\s+paper\b", "Higiene"),
    ],
    ("Bolsas", "Auto"): [
        (r"\bautom[óo]vel\b|\benxovais\b|\bapoio\s+para\s+(?:a\s+)?cabe[çc]a\b", "Acessório Auto"),
    ],
    ("Brinquedos", "Utensílios"): [
        (r"\butens[ií]lios\s+de\s+cozinha\b|\bkit\s+utens[ií]lios\b|\bkit\s+\d+\s+utens[ií]lios\b", "Utensílios"),
    ],

}


def detect_l1_from_title(title):
    """Detect L1 category from title using broad keyword patterns.

    Returns L1 string or None.
    """
    if not title:
        return None
    title_lower = title.lower()

    # Order matters: most specific first
    rules = [
        ('Acessórios Mobile', r'celular|smartphone|capa celular|carregador|cabo usb|pen drive|cart[aã]o sd|suporte celular|carro.*celular'),
        ('Audio', r'fone\b|headphone|headset|caixa de som|caixa ac[uú]stica|amplificada|microfone|soundbar|mp3|aparelho de som'),
        ('Bebê', r'beb[eê]|fralda|mamadeira|carrinho beb[eê]|chupeta|body beb[eê]|berço'),
        ('Beleza', r'shampoo|condicionador|hidratante|protetor solar|batom|base\b|m[aá]scara de c[ií]lios|creme dental|maquiagem|perfume|skincare|barbeador|aparador'),
        ('Bolsas', r'mochila de m[ãa]o|bolsa f[eê]mea|bolsa feminina|bolsa transversal|bolsa t[eê]xtil|bolsa de praia|carteira\b|bolsa de couro|mochila escolar|necessaire|clutch'),
        ('Brinquedos', r'brinquedo|jogo\b|boneca|boneco|pel[uú]cia|quebra.cabe[cç]a|puzzle|action figure|slime|hot wheels|pista|bola\b|carrinho de brinquedo|quebra.cabe[cç]a|massinha|play.doh|cubo m[aá]gico|tris\b|pega varetas'),
        ('Casa', r'tapete|toalha de banho|cesto|varal|cabide|organizador|p[oó]t[ae]|vaso\b|garrafa t[eé]rmica|copo\b|prateleira|arm[aá]rio|cama\b|sof[aá]|mesinha'),
        ('Cozinha', r'panela|frigideira|garrafa t[eé]rmica|pote|afryer|airfryer|cafeteira|espremedor|coador|forma de gelo|ta[cç]a|jogo de jantar|faqueiro|concha|pegador|escumadeira|amassador|abridor|mixer\b|chaleira|bowls?|tigelas?|pipoqueira|mochaccino|c[aá]psula caf[eé]|porta.temperos|cuscuzeira|assadeira|forma de bolo|kit utens[ií]lios de cozinha|kit\s+\d+\s+utens[ií]lios\s+de\s+cozinha|lunch box|water bottle|tumbler|thermos|toaster|blender|food scale|kitchen|cookware|grill\b|sandwich|grinder|spatula|shears|sponge|olive oil sprayer|can opener|food storage|cheesecloth|tablecloth|parchment paper|paper liners|meat thermometer|coffee|mug\b|trash can|frying pan|saucepan|cutting board|colander|rolling pin'),
        ('Esportes', r'tapete yoga|halter|haltere|peso\b|smart tag|localizador|rastreador|suplemento|creatina|whey|faixa el[aá]stica|skate|patins|bicicleta|patinete'),
        ('Ferramentas', r'furadeira|parafusadeira|chave\b|soquete|jogo de chave|alic[ae]|martelo|ferramenta|multimetro|paquímetro|n[íi]vel|lixadeira|esmeril|serra\s*m[aá]quina'),
        ('Fotografia', r'tr[ií]p[eê]|monop[eé]|suporte c[âa]mera|gimbal|estabilizador|anel adaptador|filtro\s*uv|flash\b|cart[aã]o mem[oó]ria'),
        ('Iluminação', r'ring light|luz led|bast[ãa]o led|painel led|softbox|ilumina[cç][ãa]o|lanterna|abajur|lumin[áa]ria'),
        ('Meias', r'^meia(s)?\b|\bmeia(s)?\s+cano|\bmeia(s)?\s+masculin|\bmeia(s)?\s+feminin|kit\s+meia'),
        ('Mochilas', r'\bmochila(s)?\b|mochila escolar|mochila de trilha|mochila de notebook|mochila executiva'),
        ('Moda', r'camiseta|camisa\b|cal[cç]a|short|vestido|saia|blusa|jaqueta|moletom|agasalho|bon[eé]|chapéu|gravata|cinto|len[cç]o|carteira\b|pulseira|rel[óo]gio de pulso|sunglasses|[oó]culos de sol|chinelo|t[eê]nis\b|sapatilha|cueca|suti[ãa]|lingerie|calcinha|meia\b'),
        ('Auto', r'\bautom[óo]vel\b|\bcarro\b|\bauto\b.*\bdescanso\b'),
        ('Moda Intima', r'cueca|suti[ãa]|calcinha|lingerie|top\b|body modelador'),
    ]
    for l1, pattern in rules:
        if re.search(pattern, title_lower, re.IGNORECASE):
            return l1
    return None


def classify_l3(category_l1, title):
    """Classify a product into L2 + L3 based on title keywords.

    Returns (l2, l3) tuple, or (None, None) if can't classify.
    """
    if not title:
        return None, None
    if not any(l1 == category_l1 for (l1, _l2) in KEYWORD_RULES):
        return None, None

    title_lower = title.lower()
    for (l1, l2), rules in KEYWORD_RULES.items():
        if l1 != category_l1:
            continue
        for pattern, l3 in rules:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return l2, l3
    return None, None


def get_l2_from_l3(category_l1, l3):
    """Look up L2 for a given L3 in the taxonomy."""
    if category_l1 not in TAXONOMY:
        return None
    for l2, l3_list in TAXONOMY[category_l1].items():
        if l3 in l3_list:
            return l2
    return None


def get_all_l3_for_l1(category_l1):
    """Return set of all valid L3 values for an L1 category."""
    if category_l1 not in TAXONOMY:
        return set()
    result = set()
    for l3s in TAXONOMY[category_l1].values():
        result.update(l3s)
    return result


def get_all_l2_for_l1(category_l1):
    """Return list of L2 values for an L1."""
    if category_l1 not in TAXONOMY:
        return []
    return list(TAXONOMY[category_l1].keys())


def main():
    parser = argparse.ArgumentParser(description="Categorize products into L1/L2/L3")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no DB writes")
    parser.add_argument("--category", default=None, help="Only process this L1 category")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host="localhost", database="arbtbr", user="hermes1688",
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    where = "WHERE is_active=true"
    if args.category:
        where += f" AND category_l1 = '{args.category}'"
    cur.execute(f"""
        SELECT id, platform, platform_id, title, category_l1, category_l2, category_l3
        FROM products {where}
        ORDER BY category_l1, category_l3, title
    """)
    products = cur.fetchall()
    print(f"Loaded {len(products)} products")

    updates = []  # List of (id, l2, l3, reason)
    unchanged = 0

    for p in products:
        l1 = p['category_l1']
        old_l2 = p['category_l2']
        old_l3 = p['category_l3']
        title = p['title']

        if not l1 or l1 not in TAXONOMY:
            # Try to detect L1 from title
            detected_l1 = detect_l1_from_title(title)
            if detected_l1:
                l1 = detected_l1
                cur.execute("UPDATE products SET category_l1=%s WHERE id=%s", (l1, p['id']))
            else:
                continue

        new_l2 = None
        new_l3 = None
        reason = None

        # 1. If L3 is in taxonomy, derive L2 from it
        if old_l3 and old_l3 in get_all_l3_for_l1(l1):
            new_l2 = get_l2_from_l3(l1, old_l3)
            new_l3 = old_l3
            reason = "l3 in taxonomy"
        # 2. If L3 is "Geral" or L3 == L1, try keyword classification
        elif old_l3 in ("Geral", l1) or not old_l3:
            new_l2, new_l3 = classify_l3(l1, title)
            reason = "keyword classify"
        # 3. L3 not in taxonomy but exists — try to find best match
        else:
            # Keep L3 as-is (existing valid subcategory), just set L2
            new_l2 = get_l2_from_l3(l1, old_l3)
            new_l3 = old_l3
            if not new_l2:
                # Try keyword classification
                new_l2, new_l3 = classify_l3(l1, title)
                if new_l2:
                    reason = "keyword override"
                else:
                    reason = "unknown l3 (keep as-is)"
            else:
                reason = "l2 derived from existing l3"

        # Only update if changed (keep old if new is None)
        final_l2 = new_l2 if new_l2 is not None else old_l2
        final_l3 = new_l3 if new_l3 is not None else old_l3

        if (final_l2 != old_l2) or (final_l3 != old_l3):
            updates.append({
                'id': p['id'],
                'platform': p['platform'],
                'platform_id': p['platform_id'],
                'title': title[:60],
                'old_l1': l1, 'old_l2': old_l2, 'old_l3': old_l3,
                'new_l2': final_l2, 'new_l3': final_l3,
                'reason': reason,
            })
        else:
            unchanged += 1

    print(f"\n=== Preview ===")
    print(f"Will update: {len(updates)}")
    print(f"Unchanged: {unchanged}")

    if updates:
        # Show breakdown by L1
        from collections import Counter
        by_l1 = Counter(u['old_l1'] for u in updates)
        print(f"\nBy L1:")
        for l1, n in by_l1.most_common():
            print(f"  {l1}: {n} updates")

        # Show sample (first 15)
        print(f"\n=== Sample updates (first 15) ===")
        for u in updates[:15]:
            print(f"  [{u['old_l1']}] {u['platform']}/{u['platform_id']}")
            print(f"    title: {u['title']}")
            print(f"    OLD: l2={u['old_l2']!r} l3={u['old_l3']!r}")
            print(f"    NEW: l2={u['new_l2']!r} l3={u['new_l3']!r} ({u['reason']})")
            print()

    if args.dry_run:
        print("\n[DRY RUN] No changes made")
        return

    if not updates:
        print("\nNo updates needed")
        return

    # Apply
    print(f"\nApplying {len(updates)} updates...")
    for u in updates:
        cur.execute("""
            UPDATE products
            SET category_l2 = %s, category_l3 = %s
            WHERE id = %s
        """, (u['new_l2'], u['new_l3'], u['id']))
    conn.commit()
    print(f"✓ Updated {len(updates)} products")

    # Show new state
    if args.category:
        where2 = f"WHERE is_active=true AND category_l1 = '{args.category}'"
    else:
        where2 = "WHERE is_active=true"
    cur.execute(f"""
        SELECT category_l1, category_l2, category_l3, COUNT(*) as n
        FROM products {where2}
        GROUP BY category_l1, category_l2, category_l3
        ORDER BY category_l1, category_l2, category_l3
    """)
    print(f"\n=== New state ===")
    for r in cur.fetchall():
        print(f"  {r['category_l1']} / {r['category_l2']} / {r['category_l3']}: {r['n']}")


if __name__ == "__main__":
    main()
