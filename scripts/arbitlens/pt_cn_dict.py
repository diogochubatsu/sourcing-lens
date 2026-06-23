"""
PT→CN Keyword Dictionary for arbitlens search.
Portuguese terms → Chinese terms for better results on Chinese marketplaces.
"""
PT_CN_MAP = {
    # Praia / Banho
    "toalha praia": "沙滩巾",
    "toalha de praia": "沙滩巾",
    "toalha": "毛巾",
    "roupa de banho": "浴巾",
    "biquini": "比基尼",
    "maiô": "连体泳衣",
    "chinelo": "拖鞋",
    "garrafa térmica": "保温杯",
    "bolsa praia": "沙滩包",

    # Eletrônicos
    "fone bluetooth": "蓝牙耳机",
    "fone de ouvido": "耳机",
    "carregador iphone": "苹果充电器",
    "carregador": "充电器",
    "cabo usb": "数据线",
    "cabo carregador": "充电线",
    "pelicula": "手机膜",
    "capa celular": "手机壳",
    "caixa som": "蓝牙音箱",
    "smartwatch": "智能手表",
    "relogio inteligente": "智能手表",
    "webcam": "摄像头",
    "mouse": "鼠标",
    "teclado": "键盘",
    "fone com fio": "有线耳机",
    "fone iphone": "苹果耳机",
    "cabo lightning": "苹果数据线",
    "hd externo": "移动硬盘",
    "pendrive": "U盘",
    "cabo hdmi": "HDMI线",
    "carregador wireless": "无线充电器",
    "suporte celular": "手机支架",
    "mousepad": "鼠标垫",
    "microfone": "麦克风",
    "fone gamer": "游戏耳机",
    "teclado mecanico": "机械键盘",

    # Casa / Cozinha
    "caneca personalizada": "定制杯子",
    "caneca": "杯子",
    "copo": "杯子",
    "vaso": "花瓶",
    "tapete": "地毯",
    "almofada": "抱枕",
    "cortina": "窗帘",
    "toalha mesa": "桌布",
    "utensilio cozinha": "厨房用具",
    "faqueiro": "餐具",
    "pote plastico": "塑料盒",
    "organizador": "收纳盒",
    "lixeira": "垃圾桶",
    "cesto": "篮子",
    "porta treco": "收纳盒",
    "necessaire": "化妆包",
    "espelho": "镜子",
    "cabide": "衣架",

    # Moda / Acessorios
    "relogio feminino": "女表",
    "relogio masculino": "男表",
    "corrente": "项链",
    "colar": "项链",
    "brinco": "耳环",
    "anel": "戒指",
    "pulseira": "手链",
    "oculos sol": "太阳镜",
    "oculos": "眼镜",
    "bolsa": "包包",
    "mochila": "背包",
    "carteira": "钱包",
    "cinto": "腰带",
    "bone": "帽子",
    "gorro": "帽子",
    "chaveiro": "钥匙扣",

    # Fitness / Esportes
    "legging": "紧身裤",
    "tenis": "运动鞋",
    "meia": "袜子",
    "tapete yoga": "瑜伽垫",
    "corda pular": "跳绳",
    "barraca": "帐篷",
    "cadeira praia": "沙滩椅",
    "guarda sol": "遮阳伞",
    "cooler": "保温箱",
    "churrasqueira": "烧烤架",
    "boia piscina": "游泳圈",
    "luva": "手套",
    "capa chuva": "雨衣",
    "guarda chuva": "雨伞",

    # Beleza / Cosmeticos
    "maquiagem": "化妆品",
    "batom": "口红",
    "delineador": "眼线笔",
    "sombra": "眼影",
    "rimel": "睫毛膏",
    "esmalte": "指甲油",
    "unha postica": "假指甲",
    "cilios posticos": "假睫毛",
    "peruca": "假发",
    "kit maquiagem": "化妆品套装",

    # Papelaria / Escritorio
    "caderno": "笔记本",
    "caneta": "笔",
    "lapis": "铅笔",
    "adesivo": "贴纸",
    "kit escolar": "文具套装",
    "estojo": "铅笔盒",
    "mochila escolar": "书包",
    "tesoura": "剪刀",
    "fita adesiva": "胶带",
    "cola": "胶水",

    # Automotivo / Ferramentas
    "lanterna": "手电筒",
    "pilha": "电池",
    "carregador portatil": "充电宝",
    "adaptador tomada": "转换插头",
    "chave fenda": "螺丝刀",
    "alicate": "钳子",
    "cadeado": "挂锁",

    # Jardim / Pet
    "vaso flor": "花盆",
    "luz solar": "太阳能灯",
    "semente": "种子",
    "ferramenta jardim": "园艺工具",
    "mangueira": "水管",

    # Bebe
    "fralda": "尿不湿",
    "chupeta": "奶嘴",
    "mamadeira": "奶瓶",
    "carrinho bebe": "婴儿车",
    "brinquedo bebe": "婴儿玩具",
    "roupa bebe": "婴儿服装",
    "babador": "围嘴",
    "lenco umido": "湿巾",

    # Cozinha (extra)
    "forma bolo": "蛋糕模具",
    "assadeira": "烤盘",
    "frigideira": "煎锅",
    "panela": "锅",
    "chaleira": "水壶",
    "kit tempero": "调料瓶",
    "pote vidro": "玻璃罐",
}

def pt_to_cn(portuguese_query: str) -> str | None:
    """Convert Portuguese search term to Chinese. Returns None if no match."""
    q = portuguese_query.lower().strip()
    # Direct match
    if q in PT_CN_MAP:
        return PT_CN_MAP[q]
    # Partial match - check if any key is contained in the query
    for pt, cn in PT_CN_MAP.items():
        if pt in q:
            return cn
    return None

def build_queries(portuguese_query: str) -> list[str]:
    """Return list of queries to try: [portuguese, chinese_if_available]"""
    queries = [portuguese_query]
    cn = pt_to_cn(portuguese_query)
    if cn:
        queries.append(cn)
    return queries
