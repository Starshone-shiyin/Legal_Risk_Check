"""Reusable commodity futures catalog and text/link resolution helpers.

The catalog is intentionally industry-agnostic. A debug scenario can add
``commodity_links`` or node-level ``commodity_symbols`` without changing
service code, while RSS text can still resolve an explicitly mentioned
instrument.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CommodityFuture:
    symbol: str
    name: str
    aliases: tuple[str, ...]
    chain_tags: tuple[str, ...]
    exchange: str

    @property
    def display_name(self) -> str:
        """Return a user-facing name that disambiguates similarly named contracts."""
        venue = EXCHANGE_DISPLAY_NAMES.get(self.exchange, self.exchange)
        return f"{self.name}（{venue}）" if venue else self.name


EXCHANGE_DISPLAY_NAMES = {
    "LME": "LME",
    "COMEX": "COMEX",
    "NYMEX": "NYMEX",
    "CBOT": "CBOT",
    "INE": "上期能源",
    "SHFE": "上期所",
    "DCE": "大商所",
    "CZCE": "郑商所",
    "CFFEX": "中金所",
    "GFEX": "广期所",
}


COMMODITY_FUTURES: tuple[CommodityFuture, ...] = (
    CommodityFuture("hf_CAD", "伦铜", ("铜", "copper"), ("metal", "pcb", "power"), "LME"),
    CommodityFuture("hf_AHD", "伦铝", ("铝", "aluminum"), ("metal", "power", "thermal"), "LME"),
    CommodityFuture("hf_SND", "伦锡", ("锡", "tin"), ("metal", "solder", "packaging"), "LME"),
    CommodityFuture("hf_NID", "伦镍", ("镍", "nickel"), ("metal", "battery"), "LME"),
    CommodityFuture("hf_ZSD", "伦锌", ("锌", "zinc"), ("metal", "coating"), "LME"),
    CommodityFuture("hf_PBD", "伦铅", ("铅", "lead"), ("metal", "battery"), "LME"),
    CommodityFuture("hf_GC", "纽约黄金", ("黄金", "gold"), ("precious_metal", "safe_haven"), "COMEX"),
    CommodityFuture("hf_SI", "纽约白银", ("白银", "silver"), ("precious_metal", "electronics"), "COMEX"),
    CommodityFuture("hf_XPD", "钯金", ("钯", "钯金", "palladium"), ("precious_metal", "catalyst"), "NYMEX"),
    CommodityFuture("hf_XPT", "铂金", ("铂", "铂金", "platinum"), ("precious_metal", "catalyst"), "NYMEX"),
    CommodityFuture("hf_NG", "天然气", ("天然气", "natural gas"), ("energy", "chemical"), "NYMEX"),
    CommodityFuture("hf_CL", "原油", ("原油", "石油", "油轮", "crude", "oil", "tanker"), ("energy", "chemical", "logistics"), "NYMEX"),
    CommodityFuture("hf_C", "CBOT玉米", ("玉米", "corn"), ("agriculture", "feed"), "CBOT"),
    CommodityFuture("hf_S", "CBOT大豆", ("大豆", "soybean"), ("agriculture", "feed"), "CBOT"),
    CommodityFuture("hf_W", "CBOT小麦", ("小麦", "wheat"), ("agriculture", "food"), "CBOT"),
    CommodityFuture("if_EC0", "欧线集运主连", ("海运", "航运", "运价", "集运", "freight", "shipping"), ("logistics", "cross_border"), "INE"),
    CommodityFuture("if_SC0", "原油主连", ("原油主连", "上海原油"), ("energy", "chemical", "logistics"), "INE"),
    CommodityFuture("if_SI0", "工业硅主连", ("工业硅", "工业硅期货", "硅系原料", "silicon"), ("silicon", "semiconductor_materials", "solar"), "GFEX"),
    CommodityFuture("if_AU0", "沪金主连", ("沪金", "黄金主连"), ("precious_metal", "safe_haven"), "SHFE"),
    CommodityFuture("if_AG0", "沪银主连", ("沪银", "白银主连"), ("precious_metal", "electronics"), "SHFE"),
    CommodityFuture("if_CU0", "沪铜主连", ("沪铜", "铜主连"), ("metal", "pcb", "power"), "SHFE"),
    CommodityFuture("if_AL0", "沪铝主连", ("沪铝", "铝主连"), ("metal", "power", "thermal"), "SHFE"),
    CommodityFuture("if_ZN0", "沪锌主连", ("沪锌", "锌主连"), ("metal", "coating"), "SHFE"),
    CommodityFuture("if_NI0", "沪镍主连", ("沪镍", "镍主连"), ("metal", "battery"), "SHFE"),
    CommodityFuture("if_SN0", "沪锡主连", ("沪锡", "锡主连"), ("metal", "solder", "packaging"), "SHFE"),
    CommodityFuture("if_RB0", "螺纹钢主连", ("螺纹钢", "钢材"), ("steel", "infrastructure"), "SHFE"),
    CommodityFuture("if_HC0", "热卷主连", ("热卷", "热轧卷板"), ("steel", "manufacturing"), "SHFE"),
    CommodityFuture("if_I0", "铁矿石主连", ("铁矿石", "矿石"), ("steel", "infrastructure"), "DCE"),
    CommodityFuture("if_J0", "焦炭主连", ("焦炭",), ("steel", "energy"), "DCE"),
    CommodityFuture("if_JM0", "焦煤主连", ("焦煤",), ("steel", "energy"), "DCE"),
    CommodityFuture("if_BU0", "沥青主连", ("沥青",), ("energy", "logistics", "infrastructure"), "SHFE"),
    CommodityFuture("if_FU0", "燃料油主连", ("燃料油",), ("energy", "shipping"), "SHFE"),
    CommodityFuture("if_LU0", "低硫燃料油主连", ("低硫燃料油",), ("energy", "shipping"), "INE"),
    CommodityFuture("if_RU0", "橡胶主连", ("橡胶", "天然橡胶"), ("chemical", "automotive"), "SHFE"),
    CommodityFuture("if_SP0", "纸浆主连", ("纸浆",), ("packaging", "industrial_material"), "SHFE"),
    CommodityFuture("if_SA0", "纯碱主连", ("纯碱", "soda ash"), ("chemical", "glass", "substrate"), "CZCE"),
    # Chemical futures used as cost proxies for electronic materials,
    # packaging, display glass, solvents and industrial chemical inputs.
    CommodityFuture("if_EG0", "乙二醇主连", ("乙二醇", "ethylene glycol", "eg"), ("chemical", "electronic_chemical", "polyester"), "DCE"),
    CommodityFuture("if_PP0", "聚丙烯主连", ("聚丙烯", "polypropylene", "pp", "塑料", "塑封"), ("chemical", "packaging", "polymer"), "DCE"),
    CommodityFuture("if_L0", "聚乙烯主连", ("聚乙烯", "polyethylene", "pe"), ("chemical", "packaging", "polymer"), "DCE"),
    CommodityFuture("if_V0", "PVC主连", ("pvc", "聚氯乙烯"), ("chemical", "polymer", "industrial_material"), "DCE"),
    CommodityFuture("if_MA0", "甲醇主连", ("甲醇", "methanol", "溶剂"), ("chemical", "solvent", "electronic_chemical"), "CZCE"),
    CommodityFuture("if_TA0", "PTA主连", ("pta", "精对苯二甲酸", "聚酯", "薄膜"), ("chemical", "polyester", "film"), "CZCE"),
    CommodityFuture("if_SH0", "烧碱主连", ("烧碱", "氢氧化钠", "caustic soda"), ("chemical", "electronic_chemical", "semiconductor_materials"), "SHFE"),
    CommodityFuture("if_FG0", "玻璃主连", ("玻璃", "glass", "基板"), ("glass", "substrate", "display"), "CZCE"),
    CommodityFuture("if_UR0", "尿素主连", ("尿素", "urea"), ("chemical", "industrial_material"), "CZCE"),
    CommodityFuture("if_EB0", "苯乙烯主连", ("苯乙烯", "styrene"), ("chemical", "polymer", "packaging"), "DCE"),
    CommodityFuture("if_PX0", "对二甲苯主连", ("对二甲苯", "px", "paraxylene"), ("chemical", "polyester", "solvent"), "CZCE"),
    CommodityFuture("if_PF0", "短纤主连", ("短纤", "聚酯短纤", "polyester fiber"), ("chemical", "polyester", "industrial_material"), "CZCE"),
    CommodityFuture("if_PG0", "液化石油气主连", ("液化石油气", "lpg"), ("chemical", "energy", "logistics"), "DCE"),
    CommodityFuture("if_P0", "棕榈油主连", ("棕榈油",), ("agriculture", "food"), "DCE"),
    CommodityFuture("if_Y0", "豆油主连", ("豆油",), ("agriculture", "food"), "DCE"),
    CommodityFuture("if_M0", "豆粕主连", ("豆粕",), ("agriculture", "feed"), "DCE"),
    CommodityFuture("if_A0", "豆一主连", ("豆一",), ("agriculture", "food"), "DCE"),
    CommodityFuture("if_RM0", "菜粕主连", ("菜粕",), ("agriculture", "feed"), "CZCE"),
    CommodityFuture("if_OI0", "菜油主连", ("菜油",), ("agriculture", "food"), "CZCE"),
    CommodityFuture("if_SR0", "白糖主连", ("白糖",), ("agriculture", "food"), "CZCE"),
    CommodityFuture("if_CF0", "棉花主连", ("棉花",), ("agriculture", "textile"), "CZCE"),
    CommodityFuture("if_LH0", "生猪主连", ("生猪",), ("agriculture", "food"), "DCE"),
    CommodityFuture("if_JD0", "鸡蛋主连", ("鸡蛋",), ("agriculture", "food"), "DCE"),
    CommodityFuture("if_IF0", "沪深300主连", ("沪深300期货",), ("financial", "risk_appetite"), "CFFEX"),
    CommodityFuture("if_IH0", "上证50主连", ("上证50期货",), ("financial", "risk_appetite"), "CFFEX"),
    CommodityFuture("if_IC0", "中证500主连", ("中证500期货",), ("financial", "risk_appetite"), "CFFEX"),
    CommodityFuture("if_IM0", "中证1000主连", ("中证1000期货",), ("financial", "risk_appetite"), "CFFEX"),
    CommodityFuture("if_T0", "十年期国债主连", ("十年期国债期货", "国债期货"), ("financial", "rates"), "CFFEX"),
    CommodityFuture("if_TF0", "五年期国债主连", ("五年期国债期货",), ("financial", "rates"), "CFFEX"),
    CommodityFuture("if_TS0", "二年期国债主连", ("二年期国债期货",), ("financial", "rates"), "CFFEX"),
)


CATALOG_BY_SYMBOL = {item.symbol: item for item in COMMODITY_FUTURES}


def symbols_from_text(text: str) -> list[str]:
    """Return catalog symbols explicitly referenced by text."""
    normalized = str(text or "").casefold()
    return [item.symbol for item in COMMODITY_FUTURES if any(alias_in_text(alias, normalized) for alias in item.aliases)]


def alias_in_text(alias: str, normalized_text: str) -> bool:
    candidate = str(alias or "").casefold().strip()
    if not candidate:
        return False
    if re.fullmatch(r"[a-z0-9]{1,3}", candidate):
        return re.search(rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])", normalized_text) is not None
    return candidate in normalized_text


def normalize_symbol(value: object) -> str | None:
    candidate = re.sub(r"\s+", "", str(value or ""))
    return candidate if candidate in CATALOG_BY_SYMBOL else None


def catalog_names() -> dict[str, str]:
    return {item.symbol: item.name for item in COMMODITY_FUTURES}


def catalog_display_name(symbol: str) -> str | None:
    """Resolve a catalog symbol to its stable, disambiguated display name."""
    contract = CATALOG_BY_SYMBOL.get(str(symbol or "").strip())
    return contract.display_name if contract else None
