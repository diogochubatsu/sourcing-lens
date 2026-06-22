#!/usr/bin/env python3
"""
ArbitLens Taxonomy — 3-level category hierarchy.

L1 = top-level (19 categories)
L2 = mid-level grouping
L3 = specific product type

This is the SINGLE SOURCE OF TRUTH for product categorization.
Apply to products table via scripts/categorize_products.py.
"""

# Format: L1 -> { L2 -> [L3, L3, ...] }
TAXONOMY = {
    "Acessórios Mobile": {
        "Suportes": ["Mesa", "Carro", "Magnético", "Bike", "Selfie Stick"],
        "Cabos & Carregadores": ["Cabo USB", "Cabo Lightning", "Carregador", "Power Bank", "Adaptador"],
        "Memória": ["Cartão SD", "Cartão MicroSD", "Pen Drive"],
        "Capas & Proteção": ["Capa Celular", "Película", "Capa Tablet"],
    },
    "Audio": {
        "Fones": ["Fone Bluetooth", "Fone com Fio", "Fone Gamer", "Headset"],
        "Caixas de Som": ["Portátil", "Smart Speaker", "Home Theater", "Soundbar"],
        "Microfones": ["Lapela Sem Fio", "Condensador", "Dinâmico", "Podcast/Streaming", "Acessório Microfone"],
        "Players": ["DVD/Blu-ray", "MP3 Player", "Toca-Disco"],
    },
    "Bebê": {
        "Fraldas & Lenços": ["Fralda Descartável", "Fralda de Pano", "Lenço Umedecido"],
        "Roupas": ["Body", "Conjunto", "Pijama", "Macacão"],
        "Brinquedos": ["Mordedor", "Chocalho", "Estimulação"],
        "Alimentação": ["Mamadeira", "Copo com Bico", "Prato"],
        "Higiene": ["Shampoo", "Sabonete", "Pomada"],
        "Mobilidade": ["Carrinho", "Bebê Conforto", "Cadeirinha"],
    },
    "Beleza": {
        "Skincare": ["Hidratante Facial", "Hidratante Corporal", "Protetor Solar", "Limpeza Facial", "Sérum", "Antienvelhecimento"],
        "Maquiagem": ["Base", "Batom", "Máscara de Cílios", "Sombra", "Pó", "Corretivo"],
        "Cabelo": ["Shampoo", "Condicionador", "Máscara Capilar", "Óleo Capilar", "Leave-in", "Finalizador"],
        "Higiene": ["Sabonete", "Desodorante", "Banho", "Higiene Íntima"],
        "Barbear": ["Aparador", "Barbeador", "Espuma", "Pós-barba"],
        "Corpo & Banho": ["Esfoliante", "Loção Corporal", "Óleo Corporal", "Reparador"],
    },
    "Bolsas": {
        "Feminina": ["Tote", "Transversal", "Festa", "Ombro", "Sacola", "Mochila Feminina"],
        "Viagem": ["Mala Bordo", "Mala Grande", "Necessaire", "Organizador de Mala", "Acessórios de Viagem"],
        "Acessórios": ["Carteira", "Porta-Cartões", "Kit Bolsas", "Bolsa Térmica"],
    },
    "Brinquedos": {
        "Educativo": ["Quebra-cabeça", "Blocos de Montar", "Jogo Educativo"],
        "Pelúcia": ["Personagem", "Animal"],
        "Bonecos": ["Action Figure", "Boneca", "Carrinho"],
        "Jogos": ["Tabuleiro", "Cartas", "Fantasias"],
        "Bebê": ["Mordedor", "Chocalho", "Piscina Inflável"],
        "Eletrônicos": ["Robô", "Drone Brinquedo", "Controle Remoto"],
    },
    "Casa": {
        "Cozinha": ["Pote Hermético", "Garrafa Térmica", "Copo", "Utensílio"],
        "Banho": ["Tapete de Banho", "Toalha", "Cortina"],
        "Organização": ["Cabide", "Cesto", "Organizador", "Sapateira"],
        "Decoração": ["Quadro", "Vaso", "Almofada", "Tapete Decorativo"],
        "Lavanderia": ["Varal", "Cesto de Roupa"],
    },
    "Cozinha": {
        "Utensílios": ["Pote", "Garrafa", "Copo", "Talher", "Tábua", "Forma"],
        "Eletrodomésticos": ["Airfryer", "Cafeteira", "Liquidificador", "Sanduicheira", "Forno Elétrico"],
        "Acessórios": ["Porta-Tempero", "Escorredor", "Peneira", "Abridor"],
    },
    "Esportes": {
        "Localizadores": ["Smart Tag", "GPS Tracker", "Acessório Rastreador"],
        "Suplementos": ["Creatina", "Whey", "BCAA", "Pré-treino"],
        "Fitness": ["Halter", "Elástico", "Tapete Yoga", "Roda Abdominal"],
        "Acessórios": ["Garrafa Esportiva", "Mochila Esportiva", "Bolsa Térmica"],
    },
    "Ferramentas": {
        "Elétricas": ["Furadeira", "Parafusadeira", "Serra", "Lixadeira", "Esmerilhadeira", "Lavadora"],
        "Manuais": ["Chave", "Soquete", "Martelo", "Alicate", "Jogo de Ferramentas"],
        "Jardim": ["Pá", "Regador", "Tesoura de Poda", "Mangueira"],
        "Acessórios": ["Disco", "Broca", "Extensão", "Bateria"],
    },
    "Fotografia": {
        "Tripés": ["Profissional", "Selfie", "Monopé", "Mesa"],
        "Iluminação Foto": ["Ring Light Foto", "Softbox", "Flash"],
        "Acessórios": ["Suporte Câmera", "Filtro", "Bateria", "Cartão"],
        "Lentes & Adapters": ["Lente", "Adapter", "Teleconverter"],
    },
    "Iluminação": {
        "Ring Light": ["Pequeno", "Médio", "Grande", "Kit Completo"],
        "Bastão LED": ["RGB", "Branco", "Bicolor"],
        "Painel LED": ["Estúdio", "Mesa", "Profissional"],
        "Lâmpadas": ["Smart", "LED", "Decorativa"],
        "Acessórios": ["Tripé Iluminação", "Suporte", "Filtro"],
    },
    "Meias": {
        "Feminina": ["Cano Alto", "Cano Médio", "Cano Curto", "Meia-calça"],
        "Masculina": ["Cano Alto", "Cano Médio", "Esportiva", "Kit"],
        "Infantil": ["Cano Alto", "Cano Médio"],
    },
    "Mochilas": {
        "Trabalho": ["Notebook", "Casual", "Executiva"],
        "Escola": ["Infantil", "Adolescente", "Júnior"],
        "Viagem": ["Expansível", "Esportiva 50L+", "Trekking"],
        "Moda": ["Feminina", "Masculina", "Unissex"],
    },
    "Moda": {
        "Roupas": ["Camisa", "Calça", "Jaqueta", "Blusa", "Saia", "Vestido", "Short", "Moletom"],
        "Acessórios": ["Chapéu", "Boné", "Cinto", "Lenço", "Gravata", "Cachecol"],
        "Calçados": ["Chinelo", "Tênis", "Sapato", "Sandália"],
        "Banho": ["Toalha", "Roupão", "Touca"],
        "Outros": ["Espelho", "Chaveiro", "Máscara", "Pijama", "Guarda-Chuva", "Boina"],
    },
    "Moda Intima": {
        "Cuecas": ["Boxer", "Slip", "Samba-Canção"],
        "Sutiãs": ["Push-up", "Tradicional", "Esportivo"],
        "Conjuntos": ["Lingerie", "Pijama"],
    },
    "Pet Shop": {
        "Cães": ["Ração", "Petisco", "Tapete Higiênico", "Brinquedo", "Caminha"],
        "Gatos": ["Ração", "Areia Sanitária", "Brinquedo", "Arranhador"],
        "Acessórios": ["Coleira", "Guia", "Bebedouro", "Comedouro"],
    },
    "Praia": {
        "Mobiliário": ["Cadeira de Praia", "Guarda-Sol", "Mesa"],
        "Têxtil": ["Toalha de Praia", "Canga", "Saída de Praia"],
        "Acessórios": ["Clips", "Bolsa Térmica", "Cooler", "Esteira"],
    },
    "Wearables": {
        "Smartwatch": ["Amazfit", "Apple Watch", "Samsung", "Xiaomi", "Outros"],
        "Pulseira Fitness": ["Mi Band", "Honor", "Outros"],
        "Acessórios": ["Pulseira", "Carregador", "Película"],
    },
}


def total_count():
    """Total number of (L1, L2, L3) tuples."""
    return sum(len(l3s) for cats in TAXONOMY.values() for l3s in cats.values())


if __name__ == "__main__":
    print(f"Taxonomy: {len(TAXONOMY)} L1 categories")
    for l1, l2_dict in TAXONOMY.items():
        n_l2 = len(l2_dict)
        n_l3 = sum(len(l3s) for l3s in l2_dict.values())
        print(f"  {l1}: {n_l2} L2, {n_l3} L3")
    print(f"\nTotal L3 entries: {total_count()}")
