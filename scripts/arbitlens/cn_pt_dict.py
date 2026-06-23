"""
CN→PT Keyword Dictionary for arbitlens title translation.
Chinese product titles → Portuguese labels for display.
"""
import re

# Common Chinese product terms → Portuguese
CN_PT_MAP = {
    # Electronics
    "蓝牙耳机": "fone bluetooth",
    "耳机": "fone",
    "有线耳机": "fone com fio",
    "游戏耳机": "fone gamer",
    "苹果耳机": "fone iphone",
    "无线充电器": "carregador wireless",
    "充电器": "carregador",
    "苹果充电器": "carregador iphone",
    "充电宝": "carregador portátil",
    "数据线": "cabo usb",
    "充电线": "cabo carregador",
    "苹果数据线": "cabo lightning",
    "HDMI线": "cabo hdmi",
    "手机壳": "capa celular",
    "手机膜": "pelicula",
    "手机支架": "suporte celular",
    "蓝牙音箱": "caixa de som",
    "智能手表": "smartwatch",
    "智能手环": "pulseira inteligente",
    "摄像头": "webcam",
    "鼠标": "mouse",
    "键盘": "teclado",
    "机械键盘": "teclado mecânico",
    "鼠标垫": "mousepad",
    "麦克风": "microfone",
    "移动硬盘": "hd externo",
    "U盘": "pendrive",
    "转换插头": "adaptador tomada",
    "电池": "pilha",
    "手电筒": "lanterna",
    "LED灯": "lâmpada led",
    "台灯": "lâmpada de mesa",
    "风扇": "ventilador",
    "USB风扇": "ventilador usb",

    # Fashion / Accessories
    "女表": "relógio feminino",
    "男表": "relógio masculino",
    "手表": "relógio",
    "项链": "colar",
    "耳环": "brinco",
    "耳钉": "brinco",
    "戒指": "anel",
    "手链": "pulseira",
    "手镯": "pulseira",
    "太阳镜": "óculos de sol",
    "眼镜": "óculos",
    "包包": "bolsa",
    "背包": "mochila",
    "钱包": "carteira",
    "腰带": "cinto",
    "帽子": "boné",
    "围巾": "cachecol",
    "手套": "luva",
    "袜子": "meia",
    "拖鞋": "chinelo",
    "运动鞋": "tênis",
    "紧身裤": "legging",
    "钥匙扣": "chaveiro",

    # Home / Kitchen
    "杯子": "caneca",
    "花瓶": "vaso",
    "地毯": "tapete",
    "抱枕": "almofada",
    "窗帘": "cortina",
    "桌布": "toalha de mesa",
    "收纳盒": "organizador",
    "垃圾桶": "lixeira",
    "篮子": "cesto",
    "化妆包": "necessaire",
    "镜子": "espelho",
    "衣架": "cabide",
    "毛巾": "toalha",
    "沙滩巾": "toalha de praia",
    "蛋糕模具": "forma de bolo",
    "烤盘": "assadeira",
    "煎锅": "frigideira",
    "锅": "panela",
    "水壶": "chaleira",
    "调料瓶": "kit tempero",
    "玻璃罐": "pote de vidro",
    "塑料盒": "pote plástico",
    "保温杯": "garrafa térmica",

    # Beauty / Cosmetics
    "化妆品": "maquiagem",
    "口红": "batom",
    "眼线笔": "delineador",
    "眼影": "sombra",
    "睫毛膏": "rímel",
    "指甲油": "esmalte",
    "假指甲": "unha postiça",
    "假睫毛": "cílios postiços",
    "假发": "peruca",
    "化妆品套装": "kit de maquiagem",
    "化妆刷": "pincel de maquiagem",
    "粉底": "base",
    "遮瑕": "corretivo",

    # Sports / Outdoor
    "瑜伽垫": "tapete de yoga",
    "跳绳": "corda de pular",
    "帐篷": "barraca",
    "沙滩椅": "cadeira de praia",
    "遮阳伞": "guarda-sol",
    "保温箱": "cooler",
    "烧烤架": "churrasqueira",
    "游泳圈": "boia de piscina",
    "雨衣": "capa de chuva",
    "雨伞": "guarda-chuva",

    # Baby / Kids
    "尿不湿": "fralda",
    "奶嘴": "chupeta",
    "奶瓶": "mamadeira",
    "婴儿车": "carrinho de bebê",
    "婴儿玩具": "brinquedo de bebê",
    "婴儿服装": "roupa de bebê",
    "围嘴": "babador",
    "湿巾": "lenço úmido",

    # Office / Stationery
    "笔记本": "caderno",
    "笔": "caneta",
    "铅笔": "lápis",
    "贴纸": "adesivo",
    "文具套装": "kit escolar",
    "铅笔盒": "estojo",
    "书包": "mochila escolar",
    "剪刀": "tesoura",
    "胶带": "fita adesiva",
    "胶水": "cola",

    # Garden / Pet
    "花盆": "vaso de flor",
    "太阳能灯": "luz solar",
    "种子": "semente",
    "园艺工具": "ferramenta de jardim",
    "水管": "mangueira",

    # Common modifiers
    "新款": "novo",
    "热卖": "mais vendido",
    "爆款": "popular",
    "包邮": "frete grátis",
    "批发": "atacado",
    "厂家": "fábrica",
    "直销": "direto da fábrica",
    "正品": "original",
    "高品质": "alta qualidade",
    "便携": "portátil",
    "迷你": "mini",
    "大号": "grande",
    "小号": "pequeno",
    "中号": "médio",
    "防水": "à prova d'água",
    "可爱": "fofo",
    "时尚": "moderno",
    "潮流": "tendência",
    "韩版": "estilo coreano",
    "日系": "estilo japonês",
    "欧美": "estilo europeu",

    "沙滩": "praia",
    "夹子": "clipe",
    "沙滩夹": "clipe de praia",
    "沙滩巾夹": "clipe toalha praia",
    "沙滩毛巾夹": "prendedor toalha",
    "毛巾夹": "prendedor toalha",
    "塑料夹": "clipe plástico",
    "防风夹": "prendedor",
    "晾晒夹": "prendedor varal",
    "衣夹": "prendedor roupa",
    "帽子夹": "prendedor boné",
    "内裤": "cueca",
    "内衣": "roupa íntima",
    "塑身": "modelador",
    "收腹": "modelador",
    "船袜": "meia invisível",
    "塑身衣": "modelador",
    "收腹裤": "calça modeladora",
    "塑身裤": "calça modeladora",
    "塑身内衣": "modelador",
    "塑形": "modelador",
    "瘦身": "modelador",
    "提臀": "modelador",
    "束腰": "modelador",
    "束腹": "modelador",
    "高腰": "cintura alta",
    "冰丝": "gelo",
    "无痕": "invisível",
    "女内裤": "calcinha",
    "男内裤": "cueca",
    "四角裤": "cueca",
    "平角裤": "cueca",
    "三角裤": "calcinha",
    "收纳": "organizador",
    "置物架": "estante",
    "整理": "organizador",
    "桌面": "mesa",
    "储物": "armazenamento",
    "储物盒": "caixa organizadora",
    "化妆品": "maquiagem",
    "塑料盒": "pote",
    "塑料箱": "caixa plástica",
    "整理盒": "caixa organizadora",
    "收纳箱": "caixa organizadora",
    "置物": "organizador",
    "家居": "casa",
    "家用": "casa",
    "多层": "multinível",
    "抽屉": "gaveta",
    "透明": "transparente",
    "棉袜": "meia algodão",
    "丝袜": "meia seda",
    "短袜": "meia curta",
    "长袜": "meia longa",
    "运动袜": "meia esportiva",
    "船袜女": "meia invisível",
    "袜子": "meia",
    "防滑": "antiderrapante",
    "硅胶": "silicone",
    "电钻": "furadeira",
    "钻头": "broca",
    "充电": "recarregável",
    "锂电池": "lítio",
    "无线": "sem fio",
    "电动螺丝刀": "parafusadeira",
    "电动": "elétrico",
    "冲击钻": "martelete",
    "手枪钻": "furadeira",
    "锂电钻": "furadeira bateria",
    "多功能": "multifuncional",
    "工业": "industrial",}

# Sort by length (longest first) for greedy matching
_SORTED_KEYS = sorted(CN_PT_MAP.keys(), key=len, reverse=True)


def cn_to_pt(title: str) -> str:
    """Translate Chinese product title to Portuguese.
    
    Uses greedy keyword matching — replaces known Chinese terms
    with Portuguese equivalents. Unrecognized parts stay as-is.
    """
    result = title
    for cn in _SORTED_KEYS:
        if cn in result:
            result = result.replace(cn, CN_PT_MAP[cn])
    return result


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def translate_if_chinese(title: str) -> str:
    """Translate title if it contains Chinese, otherwise return as-is."""
    if has_chinese(title):
        return cn_to_pt(title)
    return title
