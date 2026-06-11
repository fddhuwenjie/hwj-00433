#!/usr/bin/env python3
import sys
import json
import os
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG_DIR = Path.home() / ".unitcalc"
CONFIG_FILE = CONFIG_DIR / "custom_units.json"
RATES_FILE = CONFIG_DIR / "rates.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
FAVORITES_FILE = CONFIG_DIR / "favorites.json"

DEFAULT_RATES = {
    "date": "2024-01-15",
    "base": "USD",
    "rates": {
        "USD": 1.0,
        "CNY": 7.18,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 145.50,
        "KRW": 1340.0,
        "HKD": 7.82,
        "SGD": 1.34,
        "AUD": 1.52,
        "CAD": 1.36,
    },
    "names": {
        "USD": "美元",
        "CNY": "人民币",
        "EUR": "欧元",
        "GBP": "英镑",
        "JPY": "日元",
        "KRW": "韩元",
        "HKD": "港币",
        "SGD": "新加坡元",
        "AUD": "澳元",
        "CAD": "加元",
    }
}

CURRENCY_CODES = set(DEFAULT_RATES["rates"].keys())

LENGTH_UNITS = {
    "m": {"factor": 1.0, "name": "米", "names": ["m", "meter", "meters", "米"]},
    "km": {"factor": 1000.0, "name": "千米", "names": ["km", "kilometer", "kilometers", "千米"]},
    "mi": {"factor": 1609.344, "name": "英里", "names": ["mi", "mile", "miles", "英里"]},
    "ft": {"factor": 0.3048, "name": "英尺", "names": ["ft", "foot", "feet", "英尺"]},
    "in": {"factor": 0.0254, "name": "英寸", "names": ["in", "inch", "inches", "英寸"]},
    "nmi": {"factor": 1852.0, "name": "海里", "names": ["nmi", "nautical_mile", "nautical_miles", "海里"]},
    "cm": {"factor": 0.01, "name": "厘米", "names": ["cm", "centimeter", "centimeters", "厘米"]},
    "mm": {"factor": 0.001, "name": "毫米", "names": ["mm", "millimeter", "millimeters", "毫米"]},
    "yd": {"factor": 0.9144, "name": "码", "names": ["yd", "yard", "yards", "码"]},
    "um": {"factor": 1e-6, "name": "微米", "names": ["um", "micrometer", "微米"]},
    "nm": {"factor": 1e-9, "name": "纳米", "names": ["nanometer", "纳米"]},
}

WEIGHT_UNITS = {
    "kg": {"factor": 1.0, "name": "千克", "names": ["kg", "kilogram", "kilograms", "千克"]},
    "lb": {"factor": 0.45359237, "name": "磅", "names": ["lb", "lbs", "pound", "pounds", "磅"]},
    "oz": {"factor": 0.028349523125, "name": "盎司", "names": ["oz", "ounce", "ounces", "盎司"]},
    "t": {"factor": 1000.0, "name": "吨", "names": ["t", "ton", "tons", "metric_ton", "吨"]},
    "jin": {"factor": 0.5, "name": "斤", "names": ["jin", "斤", "catty"]},
    "g": {"factor": 0.001, "name": "克", "names": ["g", "gram", "grams", "克"]},
    "mg": {"factor": 1e-6, "name": "毫克", "names": ["mg", "milligram", "毫克"]},
    "uston": {"factor": 907.18474, "name": "美吨", "names": ["uston", "us_ton", "short_ton"]},
    "ukton": {"factor": 1016.0469088, "name": "英吨", "names": ["ukton", "uk_ton", "long_ton"]},
}

VOLUME_UNITS = {
    "l": {"factor": 1.0, "name": "升", "names": ["l", "liter", "liters", "litre", "升"]},
    "ml": {"factor": 0.001, "name": "毫升", "names": ["ml", "milliliter", "毫升"]},
    "gal": {"factor": 3.785411784, "name": "加仑(美)", "names": ["gal", "gallon", "gallons", "加仑"]},
    "pt": {"factor": 0.473176473, "name": "品脱(美)", "names": ["pt", "pint", "pints", "品脱"]},
    "m3": {"factor": 1000.0, "name": "立方米", "names": ["m3", "cubic_meter", "立方米"]},
    "cm3": {"factor": 0.001, "name": "立方厘米", "names": ["cm3", "cubic_centimeter", "cc"]},
    "fl_oz": {"factor": 0.0295735295625, "name": "液量盎司", "names": ["fl_oz", "fluid_ounce"]},
    "cup": {"factor": 0.2365882365, "name": "杯(美)", "names": ["cup", "cups"]},
    "qt": {"factor": 0.946352946, "name": "夸脱(美)", "names": ["qt", "quart", "quarts"]},
    "uk_gal": {"factor": 4.54609, "name": "英制加仑", "names": ["uk_gal", "imperial_gallon"]},
}

TEMPERATURE_UNITS = {"c", "f", "k"}
TEMP_NAMES = {
    "c": "摄氏度", "f": "华氏度", "k": "开尔文",
    "celsius": "c", "fahrenheit": "f", "kelvin": "k",
}

SPEED_UNITS = {
    "ms": {"factor": 1.0, "name": "米/秒", "names": ["ms", "m/s", "mps", "米/秒"]},
    "kmh": {"factor": 1.0 / 3.6, "name": "千米/时", "names": ["kmh", "km/h", "kph", "千米/时"]},
    "mph": {"factor": 0.44704, "name": "英里/时", "names": ["mph", "mi/h", "英里/时"]},
    "kn": {"factor": 0.514444, "name": "节", "names": ["kn", "knot", "knots", "节"]},
    "mach": {"factor": 340.29, "name": "马赫", "names": ["mach", "ma"]},
}

PRESSURE_UNITS = {
    "pa": {"factor": 1.0, "name": "帕斯卡", "names": ["pa", "pascal", "帕斯卡"]},
    "atm": {"factor": 101325.0, "name": "标准大气压", "names": ["atm", "atmosphere", "大气压"]},
    "mmhg": {"factor": 133.3223684211, "name": "毫米汞柱", "names": ["mmhg", "mm_hg", "毫米汞柱"]},
    "psi": {"factor": 6894.757293168, "name": "磅/平方英寸", "names": ["psi", "磅/平方英寸"]},
    "bar": {"factor": 100000.0, "name": "巴", "names": ["bar", "巴"]},
    "kpa": {"factor": 1000.0, "name": "千帕", "names": ["kpa", "kilopascal"]},
    "hpa": {"factor": 100.0, "name": "百帕", "names": ["hpa", "hectopascal"]},
}

DATA_UNITS_BASE2 = {
    "bit": {"factor": 1.0, "name": "比特", "names": ["bit", "bits", "b"]},
    "byte": {"factor": 8.0, "name": "字节", "names": ["byte", "bytes", "B"]},
    "KB": {"factor": 8.0 * 1024, "name": "千字节", "names": ["KB", "KiB", "千字节"]},
    "MB": {"factor": 8.0 * 1024 ** 2, "name": "兆字节", "names": ["MB", "MiB", "兆字节"]},
    "GB": {"factor": 8.0 * 1024 ** 3, "name": "吉字节", "names": ["GB", "GiB", "吉字节"]},
    "TB": {"factor": 8.0 * 1024 ** 4, "name": "太字节", "names": ["TB", "TiB", "太字节"]},
    "PB": {"factor": 8.0 * 1024 ** 5, "name": "拍字节", "names": ["PB", "PiB", "拍字节"]},
}

DATA_UNITS_BASE10 = {
    "bit": {"factor": 1.0, "name": "比特", "names": ["bit", "bits", "b"]},
    "byte": {"factor": 8.0, "name": "字节", "names": ["byte", "bytes", "B"]},
    "KB": {"factor": 8.0 * 1000, "name": "千字节", "names": ["KB", "千字节"]},
    "MB": {"factor": 8.0 * 1000 ** 2, "name": "兆字节", "names": ["MB", "兆字节"]},
    "GB": {"factor": 8.0 * 1000 ** 3, "name": "吉字节", "names": ["GB", "吉字节"]},
    "TB": {"factor": 8.0 * 1000 ** 4, "name": "太字节", "names": ["TB", "太字节"]},
    "PB": {"factor": 8.0 * 1000 ** 5, "name": "拍字节", "names": ["PB", "拍字节"]},
}

BANDWIDTH_UNITS = {
    "bps": {"factor": 1.0, "name": "比特/秒", "names": ["bps"]},
    "Kbps": {"factor": 1000.0, "name": "千比特/秒", "names": ["kbps", "Kbps"]},
    "Mbps": {"factor": 1e6, "name": "兆比特/秒", "names": ["mbps", "Mbps"]},
    "Gbps": {"factor": 1e9, "name": "吉比特/秒", "names": ["gbps", "Gbps"]},
}

TIME_UNITS = {
    "s": {"factor": 1.0, "name": "秒", "names": ["s", "sec", "second", "seconds", "秒"]},
    "min": {"factor": 60.0, "name": "分", "names": ["min", "minute", "minutes", "分"]},
    "h": {"factor": 3600.0, "name": "时", "names": ["h", "hr", "hour", "hours", "时"]},
    "d": {"factor": 86400.0, "name": "天", "names": ["d", "day", "days", "天"]},
    "wk": {"factor": 604800.0, "name": "周", "names": ["wk", "week", "weeks", "周"]},
    "mo": {"factor": 2592000.0, "name": "月(30天)", "names": ["mo", "month", "months", "月"]},
    "yr": {"factor": 31536000.0, "name": "年(365天)", "names": ["yr", "year", "years", "年"]},
}

UNIT_CATEGORIES = {
    "length": LENGTH_UNITS,
    "weight": WEIGHT_UNITS,
    "volume": VOLUME_UNITS,
    "speed": SPEED_UNITS,
    "pressure": PRESSURE_UNITS,
    "time": TIME_UNITS,
}

ALL_LINEAR_UNITS = {}
ALL_LINEAR_UNITS.update(LENGTH_UNITS)
ALL_LINEAR_UNITS.update(WEIGHT_UNITS)
ALL_LINEAR_UNITS.update(VOLUME_UNITS)
ALL_LINEAR_UNITS.update(SPEED_UNITS)
ALL_LINEAR_UNITS.update(PRESSURE_UNITS)
ALL_LINEAR_UNITS.update(TIME_UNITS)

ALIAS_MAP = {}
for _cat, _units in UNIT_CATEGORIES.items():
    for _key, _info in _units.items():
        for _name in _info["names"]:
            ALIAS_MAP[_name.lower()] = _key
ALIAS_MAP["celsius"] = "c"
ALIAS_MAP["fahrenheit"] = "f"
ALIAS_MAP["kelvin"] = "k"
ALIAS_MAP["c"] = "c"
ALIAS_MAP["f"] = "f"
ALIAS_MAP["k"] = "k"

for _name in DATA_UNITS_BASE2["bit"]["names"]:
    if _name.lower() not in ALIAS_MAP:
        ALIAS_MAP[_name.lower()] = "bit"
for _name in DATA_UNITS_BASE2["byte"]["names"]:
    if _name.lower() not in ALIAS_MAP:
        ALIAS_MAP[_name.lower()] = "byte"
for _key in ["KB", "MB", "GB", "TB", "PB"]:
    for _name in DATA_UNITS_BASE2[_key]["names"]:
        ALIAS_MAP[_name.lower()] = _key

for _name in BANDWIDTH_UNITS["bps"]["names"]:
    ALIAS_MAP[_name.lower()] = "bps"
for _name in BANDWIDTH_UNITS["Kbps"]["names"]:
    ALIAS_MAP[_name.lower()] = "Kbps"
for _name in BANDWIDTH_UNITS["Mbps"]["names"]:
    ALIAS_MAP[_name.lower()] = "Mbps"
for _name in BANDWIDTH_UNITS["Gbps"]["names"]:
    ALIAS_MAP[_name.lower()] = "Gbps"


def safe_eval_expr(expr):
    allowed = set("0123456789.+-*/() ")
    for ch in expr:
        if ch not in allowed:
            return None
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        if isinstance(result, (int, float)):
            return float(result)
    except Exception:
        return None
    return None


def parse_compound_unit(unit_str):
    if "/" in unit_str:
        parts = unit_str.split("/", 1)
        numer = parts[0].strip()
        denom = parts[1].strip()
        numer_key = resolve_unit(numer)
        denom_key = resolve_unit(denom)
        if numer_key and denom_key:
            return ("compound", numer_key, denom_key, numer, denom)
    single_key = resolve_unit(unit_str)
    if single_key:
        return ("single", single_key, unit_str)
    return None


def get_unit_factor_and_cat(unit_key, custom=None, use_base10=False):
    if custom is None:
        custom = {}
    if unit_key in custom:
        c = custom[unit_key]
        base_key = resolve_unit(c["base"])
        if base_key and base_key in ALL_LINEAR_UNITS:
            return (c["factor"] * ALL_LINEAR_UNITS[base_key]["factor"], find_unit_category(base_key))
        return (c["factor"], "custom")
    if unit_key in ALL_LINEAR_UNITS:
        return (ALL_LINEAR_UNITS[unit_key]["factor"], find_unit_category(unit_key))
    if unit_key in ("c", "f", "k"):
        return (1.0, "temperature")
    data_units = DATA_UNITS_BASE10 if use_base10 else DATA_UNITS_BASE2
    if unit_key in data_units:
        return (data_units[unit_key]["factor"], "data")
    if unit_key in BANDWIDTH_UNITS:
        return (BANDWIDTH_UNITS[unit_key]["factor"], "bandwidth")
    return None


def get_unit_display_name(unit_key, custom=None):
    if custom is None:
        custom = {}
    if unit_key in custom:
        return custom[unit_key].get("display_name", unit_key)
    for cat_units in list(UNIT_CATEGORIES.values()) + [DATA_UNITS_BASE2, BANDWIDTH_UNITS]:
        if unit_key in cat_units:
            return cat_units[unit_key].get("name", unit_key)
    return unit_key


def convert_compound(value, from_info, to_info, custom=None, use_base10=False):
    if from_info[0] != "compound" or to_info[0] != "compound":
        return None
    _, from_numer, from_denom, _, _ = from_info
    _, to_numer, to_denom, _, _ = to_info
    from_nf = get_unit_factor_and_cat(from_numer, custom, use_base10)
    from_df = get_unit_factor_and_cat(from_denom, custom, use_base10)
    to_nf = get_unit_factor_and_cat(to_numer, custom, use_base10)
    to_df = get_unit_factor_and_cat(to_denom, custom, use_base10)
    if not from_nf or not from_df or not to_nf or not to_df:
        return None
    if from_nf[1] != to_nf[1] or from_df[1] != to_df[1]:
        return None
    factor = (from_nf[0] / from_df[0]) / (to_nf[0] / to_df[0])
    return value * factor


def parse_value_with_unit(token):
    m = re.match(r'^([\d.eE+\-*/()]+)([a-zA-Z]+)$', token)
    if m:
        val_str = m.group(1)
        unit_str = m.group(2)
        val = safe_eval_expr(val_str)
        if val is not None:
            unit_info = parse_compound_unit(unit_str)
            if unit_info:
                return (val, unit_info)
    return None


def tokenize_expr(s):
    tokens = []
    i = 0
    s = s.strip()
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        if s[i] in "+-":
            if i == 0 or s[i - 1] in "+-*/(":
                j = i + 1
                while j < len(s) and (s[j].isdigit() or s[j] in ".eE"):
                    j += 1
                while j < len(s) and (s[j].isalpha() or s[j] == "/"):
                    j += 1
                tokens.append(s[i:j])
                i = j
                continue
        if s[i] in "+-*/()":
            tokens.append(s[i])
            i += 1
            continue
        if s[i].isdigit() or s[i] in ".":
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] in ".eE+-"):
                j += 1
            while j < len(s) and (s[j].isalpha() or s[j] == "/"):
                j += 1
            tokens.append(s[i:j])
            i = j
            continue
        if s[i].isalpha():
            j = i
            while j < len(s) and (s[j].isalpha() or s[j] == "/"):
                j += 1
            tokens.append(s[i:j])
            i = j
            continue
        i += 1
    return tokens


def eval_unit_expr(expr_str, custom=None, use_base10=False):
    tokens = tokenize_expr(expr_str)
    if not tokens:
        return None
    values = []
    operators = []

    def apply_op():
        if not operators or len(values) < 2:
            return False
        op = operators.pop()
        b = values.pop()
        a = values.pop()
        if op == "+" or op == "-":
            if a[1] != b[1]:
                return None
            if a[1] == "single":
                a_cat = get_unit_factor_and_cat(a[0][1], custom, use_base10)
                b_cat = get_unit_factor_and_cat(b[0][1], custom, use_base10)
                if not a_cat or not b_cat or a_cat[1] != b_cat[1]:
                    return None
            elif a[1] == "compound":
                pass
            result_val = a[2] + (b[2] if op == "+" else -b[2])
            values.append((a[0], a[1], result_val))
        elif op == "*":
            result_val = a[2] * b[2]
            values.append((None, "scalar", result_val))
        elif op == "/":
            if b[2] == 0:
                return None
            result_val = a[2] / b[2]
            values.append((None, "scalar", result_val))
        return True

    precedence = {"+": 1, "-": 1, "*": 2, "/": 2}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in "+-*/":
            while operators and operators[-1] != "(" and precedence.get(operators[-1], 0) >= precedence.get(t, 0):
                if not apply_op():
                    return None
            operators.append(t)
        elif t == "(":
            operators.append(t)
        elif t == ")":
            while operators and operators[-1] != "(":
                if not apply_op():
                    return None
            if operators:
                operators.pop()
        else:
            vwu = parse_value_with_unit(t)
            if vwu:
                val, uinfo = vwu
                if uinfo[0] == "single":
                    fc = get_unit_factor_and_cat(uinfo[1], custom, use_base10)
                    if fc:
                        base_val = val * fc[0]
                        values.append((uinfo, "single", base_val))
                    else:
                        return None
                elif uinfo[0] == "compound":
                    _, n_key, d_key, _, _ = uinfo
                    nf = get_unit_factor_and_cat(n_key, custom, use_base10)
                    df = get_unit_factor_and_cat(d_key, custom, use_base10)
                    if nf and df:
                        base_val = val * (nf[0] / df[0])
                        values.append((uinfo, "compound", base_val))
                    else:
                        return None
            else:
                num = safe_eval_expr(t)
                if num is not None:
                    values.append((None, "scalar", num))
                else:
                    return None
        i += 1

    while operators:
        if not apply_op():
            return None

    if len(values) == 1:
        return values[0]
    return None


PHYSICAL_CONSTANTS = [
    {"symbol": "c", "name": "光速", "value": 299792458, "unit": "m/s", "category": "电磁学", "desc": "真空中光传播速度"},
    {"symbol": "G", "name": "万有引力常数", "value": 6.67430e-11, "unit": "m³/(kg·s²)", "category": "力学", "desc": "牛顿万有引力定律中的比例常数"},
    {"symbol": "h", "name": "普朗克常数", "value": 6.62607015e-34, "unit": "J·s", "category": "量子力学", "desc": "量子力学基本常数"},
    {"symbol": "ℏ", "name": "约化普朗克常数", "value": 1.054571817e-34, "unit": "J·s", "category": "量子力学", "desc": "h/(2π)"},
    {"symbol": "k_B", "name": "玻尔兹曼常数", "value": 1.380649e-23, "unit": "J/K", "category": "热力学", "desc": "气体常数与阿伏伽德罗常数之比"},
    {"symbol": "N_A", "name": "阿伏伽德罗常数", "value": 6.02214076e23, "unit": "mol⁻¹", "category": "化学", "desc": "1摩尔物质所含基本粒子数"},
    {"symbol": "R", "name": "理想气体常数", "value": 8.314462618, "unit": "J/(mol·K)", "category": "热力学", "desc": "理想气体状态方程常数"},
    {"symbol": "σ", "name": "斯特藩-玻尔兹曼常数", "value": 5.670374419e-8, "unit": "W/(m²·K⁴)", "category": "热力学", "desc": "黑体辐射总功率与温度关系常数"},
    {"symbol": "e", "name": "基本电荷", "value": 1.602176634e-19, "unit": "C", "category": "电磁学", "desc": "一个质子所带电荷量"},
    {"symbol": "ε₀", "name": "真空介电常数", "value": 8.8541878128e-12, "unit": "F/m", "category": "电磁学", "desc": "真空中电位移与电场强度之比"},
    {"symbol": "μ₀", "name": "真空磁导率", "value": 1.25663706212e-6, "unit": "N/A²", "category": "电磁学", "desc": "真空中磁感应强度与磁场强度之比"},
    {"symbol": "α", "name": "精细结构常数", "value": 7.2973525693e-3, "unit": "", "category": "量子力学", "desc": "电磁相互作用强度无量纲常数"},
    {"symbol": "m_e", "name": "电子静止质量", "value": 9.1093837015e-31, "unit": "kg", "category": "粒子物理", "desc": "电子的静止质量"},
    {"symbol": "m_p", "name": "质子静止质量", "value": 1.67262192369e-27, "unit": "kg", "category": "粒子物理", "desc": "质子的静止质量"},
    {"symbol": "m_n", "name": "中子静止质量", "value": 1.67492749804e-27, "unit": "kg", "category": "粒子物理", "desc": "中子的静止质量"},
    {"symbol": "a₀", "name": "玻尔半径", "value": 5.29177210903e-11, "unit": "m", "category": "原子物理", "desc": "氢原子基态电子轨道半径"},
    {"symbol": "E_h", "name": "哈特里能量", "value": 4.3597447222071e-18, "unit": "J", "category": "原子物理", "desc": "原子单位制中的能量单位"},
    {"symbol": "F", "name": "法拉第常数", "value": 96485.33212, "unit": "C/mol", "category": "化学", "desc": "1摩尔电子所带电荷量"},
    {"symbol": "g", "name": "标准重力加速度", "value": 9.80665, "unit": "m/s²", "category": "力学", "desc": "地球表面标准重力加速度"},
    {"symbol": "R_∞", "name": "里德伯常数", "value": 10973731.568160, "unit": "m⁻¹", "category": "原子物理", "desc": "氢原子光谱波数常数"},
    {"symbol": "k_e", "name": "库仑常数", "value": 8.9875517923e9, "unit": "N·m²/C²", "category": "电磁学", "desc": "1/(4πε₀)"},
    {"symbol": "λ_C", "name": "康普顿波长", "value": 2.42631023867e-12, "unit": "m", "category": "量子力学", "desc": "电子的康普顿波长"},
    {"symbol": "r_e", "name": "经典电子半径", "value": 2.8179403262e-15, "unit": "m", "category": "粒子物理", "desc": "电子的经典半径"},
    {"symbol": "σ_T", "name": "汤姆逊散射截面", "value": 6.6524587321e-29, "unit": "m²", "category": "粒子物理", "desc": "自由电子对光子的散射截面"},
    {"symbol": "μ_B", "name": "玻尔磁子", "value": 9.2740100783e-24, "unit": "J/T", "category": "原子物理", "desc": "电子轨道磁矩的自然单位"},
    {"symbol": "μ_N", "name": "核磁子", "value": 5.0507837461e-27, "unit": "J/T", "category": "核物理", "desc": "核磁矩的自然单位"},
    {"symbol": "m_u", "name": "原子质量单位", "value": 1.66053906660e-27, "unit": "kg", "category": "原子物理", "desc": "¹²C原子质量的1/12"},
    {"symbol": "Wien_b", "name": "维恩位移常数", "value": 2.897771955e-3, "unit": "m·K", "category": "热力学", "desc": "黑体辐射峰值波长与温度关系"},
    {"symbol": "c₁", "name": "第一辐射常数", "value": 3.741771852e-16, "unit": "W·m²", "category": "热力学", "desc": "2πhc²"},
    {"symbol": "c₂", "name": "第二辐射常数", "value": 1.438776877e-2, "unit": "m·K", "category": "热力学", "desc": "hc/k_B"},
]


def format_number(val):
    if val == 0:
        return "0"
    abs_val = abs(val)
    if abs_val >= 1e10 or (abs_val < 1e-4 and abs_val != 0):
        return f"{val:.6e}"
    if abs_val >= 1e6:
        return f"{val:,.4f}"
    if isinstance(val, float) and val == int(val) and abs_val < 1e15:
        return str(int(val))
    if abs_val >= 100:
        return f"{val:.4f}"
    if abs_val >= 1:
        return f"{val:.6f}"
    return f"{val:.8f}".rstrip("0").rstrip(".")


def convert_temperature(value, from_unit, to_unit):
    if from_unit == to_unit:
        return value
    if from_unit == "c":
        celsius = value
    elif from_unit == "f":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "k":
        celsius = value - 273.15
    else:
        return None
    if to_unit == "c":
        return celsius
    elif to_unit == "f":
        return celsius * 9 / 5 + 32
    elif to_unit == "k":
        return celsius + 273.15
    return None


def get_temp_formula(from_unit, to_unit):
    formulas = {
        ("c", "f"): "°F = °C × 9/5 + 32",
        ("f", "c"): "°C = (°F - 32) × 5/9",
        ("c", "k"): "K = °C + 273.15",
        ("k", "c"): "°C = K - 273.15",
        ("f", "k"): "K = (°F - 32) × 5/9 + 273.15",
        ("k", "f"): "°F = (K - 273.15) × 9/5 + 32",
    }
    return formulas.get((from_unit, to_unit), "")


def resolve_unit(name):
    key = ALIAS_MAP.get(name.lower())
    return key


def find_unit_category(key):
    for cat, units in UNIT_CATEGORIES.items():
        if key in units:
            return cat
    if key in ("c", "f", "k"):
        return "temperature"
    if key in DATA_UNITS_BASE2:
        return "data"
    if key in BANDWIDTH_UNITS:
        return "bandwidth"
    return None


def load_custom_units():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_custom_units(units):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(units, f, ensure_ascii=False, indent=2)


def do_convert_simple(value, from_key, to_key, from_name, to_name, custom, use_base10):
    from_cat = find_unit_category(from_key)
    to_cat = find_unit_category(to_key)

    if from_key in custom and to_key in custom:
        c_from = custom[from_key]
        c_to = custom[to_key]
        if c_from["base"] != c_to["base"]:
            print(f"错误: 单位 '{from_key}' 基准为 {c_from['base']}，单位 '{to_key}' 基准为 {c_to['base']}，不可互转")
            return None
        base_val = value * c_from["factor"]
        result = base_val / c_to["factor"]
    elif from_key in custom:
        c_from = custom[from_key]
        base_unit = c_from["base"]
        to_key_resolved = resolve_unit(base_unit)
        if to_key_resolved is None:
            base_unit_key = base_unit.lower()
            if base_unit_key in custom:
                base_val = value * c_from["factor"] * custom[base_unit_key]["factor"]
                result = base_val / custom[to_key]["factor"]
            else:
                print(f"错误: 无法解析基准单位 '{base_unit}'")
                return None
        else:
            base_val = value * c_from["factor"]
            if to_key_resolved in ALL_LINEAR_UNITS:
                result = base_val / ALL_LINEAR_UNITS[to_key_resolved]["factor"]
            else:
                print(f"错误: 不支持从自定义单位到 '{to_name}' 的转换")
                return None
        from_cat = find_unit_category(to_key_resolved) or "custom"
    elif to_key in custom:
        c_to = custom[to_key]
        base_unit = c_to["base"]
        from_key_resolved = resolve_unit(base_unit)
        if from_key_resolved is None:
            print(f"错误: 无法解析基准单位 '{base_unit}'")
            return None
        if from_key in ALL_LINEAR_UNITS:
            base_val = value * ALL_LINEAR_UNITS[from_key]["factor"]
            result = base_val / c_to["factor"]
        else:
            print(f"错误: 不支持从 '{from_name}' 到自定义单位的转换")
            return None
        to_cat = "custom"
    elif from_cat == "temperature" or to_cat == "temperature":
        if from_cat != "temperature" or to_cat != "temperature":
            print("错误: 温度单位只能与温度单位互转")
            return None
        result = convert_temperature(value, from_key, to_key)
        if result is None:
            print("错误: 温度转换失败")
            return None
        formula = get_temp_formula(from_key, to_key)
        result_str = format_number(result)
        from_display = {"c": "°C", "f": "°F", "k": "K"}.get(from_key, from_key)
        to_display = {"c": "°C", "f": "°F", "k": "K"}.get(to_key, to_key)
        print(f"{format_number(value)} {from_display} = {result_str} {to_display}")
        if formula:
            print(f"  换算公式: {formula}")
        return result
    elif from_cat == "data" or to_cat == "data":
        if from_cat != "data" or to_cat != "data":
            print("错误: 数据存储单位只能与数据存储单位互转")
            return None
        data_units = DATA_UNITS_BASE10 if use_base10 else DATA_UNITS_BASE2
        if from_key not in data_units or to_key not in data_units:
            print(f"错误: 不支持的数据单位 (from={from_key}, to={to_key})")
            return None
        base_val = value * data_units[from_key]["factor"]
        result = base_val / data_units[to_key]["factor"]
    elif from_cat == "bandwidth" or to_cat == "bandwidth":
        if from_cat != "bandwidth" or to_cat != "bandwidth":
            print("错误: 带宽单位只能与带宽单位互转")
            return None
        base_val = value * BANDWIDTH_UNITS[from_key]["factor"]
        result = base_val / BANDWIDTH_UNITS[to_key]["factor"]
    elif from_cat and from_cat == to_cat:
        units = UNIT_CATEGORIES[from_cat]
        base_val = value * units[from_key]["factor"]
        result = base_val / units[to_key]["factor"]
    else:
        print(f"错误: 无法从 '{from_name}'({from_cat or '未知'}) 转换到 '{to_name}'({to_cat or '未知'})")
        return None

    from_display = from_name
    to_display = to_name
    for cat_units in list(UNIT_CATEGORIES.values()) + [DATA_UNITS_BASE2, BANDWIDTH_UNITS]:
        if from_key in cat_units:
            from_display = cat_units[from_key].get("name", from_key)
        if to_key in cat_units:
            to_display = cat_units[to_key].get("name", to_key)

    is_custom = from_key in custom or to_key in custom

    print(f"{format_number(value)} {from_display} = {format_number(result)} {to_display}")

    if not is_custom and from_cat and from_cat not in ("data", "bandwidth", "temperature", "custom") and from_cat == to_cat:
        units = UNIT_CATEGORIES[from_cat]
        f_factor = units[from_key]["factor"]
        t_factor = units[to_key]["factor"]
        ratio = f_factor / t_factor
        if ratio == int(ratio) and abs(ratio) < 1e15:
            print(f"  换算公式: 1 {from_display} = {format_number(ratio)} {to_display}")
        else:
            print(f"  换算公式: 1 {from_display} = {ratio:.10g} {to_display}")

    if from_cat == "data" and to_cat == "data":
        data_units = DATA_UNITS_BASE10 if use_base10 else DATA_UNITS_BASE2
        f_factor = data_units[from_key]["factor"]
        t_factor = data_units[to_key]["factor"]
        ratio = f_factor / t_factor
        base_label = "1000" if use_base10 else "1024"
        print(f"  换算公式: 1 {from_display} = {ratio:.10g} {to_display} ({base_label}进制)")

    if from_cat == "bandwidth" and to_cat == "bandwidth":
        f_factor = BANDWIDTH_UNITS[from_key]["factor"]
        t_factor = BANDWIDTH_UNITS[to_key]["factor"]
        ratio = f_factor / t_factor
        print(f"  换算公式: 1 {from_display} = {ratio:.10g} {to_display}")

    if is_custom:
        if from_key in custom:
            c_info = custom[from_key]
            base_display = c_info["base"]
            for cat_units in UNIT_CATEGORIES.values():
                if c_info["base"] in cat_units:
                    base_display = cat_units[c_info["base"]]["name"]
                    break
            print(f"  换算公式: 1 {from_display} = {format_number(c_info['factor'])} {base_display}")
        elif to_key in custom:
            c_info = custom[to_key]
            base_display = c_info["base"]
            for cat_units in UNIT_CATEGORIES.values():
                if c_info["base"] in cat_units:
                    base_display = cat_units[c_info["base"]]["name"]
                    break
            print(f"  换算公式: 1 {to_display} = {format_number(c_info['factor'])} {base_display}")
    return result


def do_convert(args):
    custom = load_custom_units()
    use_base10 = False
    if "--si" in args:
        use_base10 = True
        args = [a for a in args if a != "--si"]

    if "to" not in args and "in" not in args:
        print("用法: convert <表达式/值> [源单位] to <目标单位>")
        print("示例: convert 100 km to miles")
        print("      convert 2*3.14 km to miles")
        print("      convert 100 km/h to m/s")
        print("      convert 100 cm + 2 m to inches")
        return

    sep_idx = None
    for i, a in enumerate(args):
        if a.lower() in ("to", "in"):
            sep_idx = i
            break

    if sep_idx is None:
        print("用法: convert <表达式/值> [源单位] to <目标单位>")
        return

    to_name = " ".join(args[sep_idx + 1:])
    from_part_str = " ".join(args[:sep_idx])

    has_plus_minus = any(op in from_part_str for op in [" + ", " - "])
    if has_plus_minus or ("/" in from_part_str and not from_part_str.strip().split()[-1:][0].startswith("/") if from_part_str.strip() else False):
        pass

    to_info = parse_compound_unit(to_name)
    if to_info is None and to_name.lower() in custom:
        to_info = ("single", to_name.lower(), to_name)
    if to_info is None:
        print(f"错误: 未知目标单位 '{to_name}'")
        return

    expr_val = eval_unit_expr(from_part_str, custom, use_base10)
    if expr_val is not None and expr_val[1] in ("single", "compound"):
        base_val = expr_val[2]
        src_info = expr_val[0]
        if src_info[0] == "single" and to_info[0] == "single":
            from_key = src_info[1]
            to_key = to_info[1]
            from_display_src = src_info[2] if len(src_info) > 2 else from_key
            do_convert_simple(value=base_val / get_unit_factor_and_cat(from_key, custom, use_base10)[0],
                              from_key=from_key, to_key=to_key,
                              from_name=from_display_src, to_name=to_name,
                              custom=custom, use_base10=use_base10)
            record_history("convert " + from_part_str + " to " + to_name)
            return
        elif src_info[0] == "compound" and to_info[0] == "compound":
            _, n_key, d_key, n_orig, d_orig = src_info
            nf = get_unit_factor_and_cat(n_key, custom, use_base10)
            df = get_unit_factor_and_cat(d_key, custom, use_base10)
            orig_val = base_val / (nf[0] / df[0]) if nf and df else None
            result = convert_compound(orig_val, src_info, to_info, custom, use_base10)
            if result is not None:
                from_display = f"{get_unit_display_name(n_key, custom)}/{get_unit_display_name(d_key, custom)}"
                _, tn_key, td_key, _, _ = to_info
                to_display = f"{get_unit_display_name(tn_key, custom)}/{get_unit_display_name(td_key, custom)}"
                print(f"{format_number(orig_val)} {from_display} = {format_number(result)} {to_display}")
                record_history("convert " + from_part_str + " to " + to_name)
                return
        elif src_info[0] == "single" and to_info[0] == "compound":
            pass
        print("错误: 源与目标单位类型不匹配")
        return

    tokens = args[:sep_idx]
    if len(tokens) < 1:
        print("用法: convert <值> <源单位> to <目标单位>")
        return

    value = None
    from_name = None

    first_token = tokens[0]
    expr_result = safe_eval_expr(first_token)
    if expr_result is not None:
        value = expr_result
        from_name = " ".join(tokens[1:]) if len(tokens) > 1 else None
    else:
        m = re.match(r'^([\d.eE+\-*/()]+)([a-zA-Z/]+)$', first_token)
        if m:
            val_str = m.group(1)
            unit_str = m.group(2)
            value = safe_eval_expr(val_str)
            if value is not None and len(tokens) == 1:
                from_name = unit_str
            elif value is not None:
                from_name = unit_str + " " + " ".join(tokens[1:])
        else:
            print(f"错误: 无法解析 '{first_token}'")
            return

    if value is None:
        print(f"错误: 无法解析数值")
        return
    if from_name is None:
        print("错误: 缺少源单位")
        return

    from_info = parse_compound_unit(from_name)
    if from_info is None and from_name.lower() in custom:
        from_info = ("single", from_name.lower(), from_name)
    if from_info is None:
        from_key = resolve_unit(from_name)
        if from_key:
            from_info = ("single", from_key, from_name)
    if from_info is None:
        print(f"错误: 未知源单位 '{from_name}'")
        return

    if from_info[0] == "single" and to_info[0] == "single":
        do_convert_simple(value, from_info[1], to_info[1], from_name, to_name, custom, use_base10)
    elif from_info[0] == "compound" and to_info[0] == "compound":
        result = convert_compound(value, from_info, to_info, custom, use_base10)
        if result is not None:
            _, fn_key, fd_key, _, _ = from_info
            _, tn_key, td_key, _, _ = to_info
            from_display = f"{get_unit_display_name(fn_key, custom)}/{get_unit_display_name(fd_key, custom)}"
            to_display = f"{get_unit_display_name(tn_key, custom)}/{get_unit_display_name(td_key, custom)}"
            print(f"{format_number(value)} {from_display} = {format_number(result)} {to_display}")
        else:
            print("错误: 复合单位换算失败，请确保分子分母单位类型匹配")
            return
    else:
        print("错误: 源与目标单位类型不匹配（都是单一单位或都是复合单位）")
        return
    record_history("convert " + from_part_str + " to " + to_name)


def do_calc(args):
    if not args:
        print("用法: calc <带单位表达式>")
        print("示例: calc 5km + 3miles")
        print("      calc 100m / 10s")
        print("      calc 2.5kg * 3")
        return
    custom = load_custom_units()
    expr_str = " ".join(args)
    result = eval_unit_expr(expr_str, custom, False)
    if result is None:
        print(f"错误: 无法计算表达式 '{expr_str}'")
        return
    uinfo, utype, base_val = result
    if utype == "single":
        _, unit_key, orig_name = uinfo
        fc = get_unit_factor_and_cat(unit_key, custom, False)
        if not fc:
            print("错误: 无法识别单位")
            return
        cat = fc[1]
        val_in_orig = base_val / fc[0]
        print(f"结果: {format_number(val_in_orig)} {get_unit_display_name(unit_key, custom)}")
        if cat and cat in UNIT_CATEGORIES:
            units = UNIT_CATEGORIES[cat]
            print("  其他单位:")
            shown = 0
            for k, info in units.items():
                if k == unit_key:
                    continue
                f = get_unit_factor_and_cat(k, custom, False)
                if f:
                    v = base_val / f[0]
                    print(f"    {format_number(v)} {info['name']}")
                    shown += 1
                    if shown >= 5:
                        break
    elif utype == "compound":
        _, n_key, d_key, _, _ = uinfo
        nf = get_unit_factor_and_cat(n_key, custom, False)
        df = get_unit_factor_and_cat(d_key, custom, False)
        if not nf or not df:
            print("错误: 无法识别复合单位")
            return
        val_in_orig = base_val / (nf[0] / df[0])
        from_display = f"{get_unit_display_name(n_key, custom)}/{get_unit_display_name(d_key, custom)}"
        print(f"结果: {format_number(val_in_orig)} {from_display}")
        print(f"  基准值: {format_number(base_val)} (SI单位制)")
    elif utype == "scalar":
        print(f"结果: {format_number(base_val)}")
    record_history("calc " + expr_str)


def load_rates():
    if not RATES_FILE.exists():
        save_rates(DEFAULT_RATES)
        return DEFAULT_RATES
    try:
        with open(RATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "rates" not in data or "date" not in data:
                return DEFAULT_RATES
            return data
    except Exception:
        return DEFAULT_RATES


def save_rates(rates):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(RATES_FILE, "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)


def do_currency(args):
    if not args:
        print("用法:")
        print("  currency <值> <源货币> to <目标货币>  - 货币换算")
        print("  currency rates                         - 显示所有汇率")
        print("  currency update                        - 从本地更新汇率")
        print("\n支持货币: USD, CNY, EUR, GBP, JPY, KRW, HKD, SGD, AUD, CAD")
        print("示例: currency 100 USD to CNY")
        return

    sub = args[0].lower()

    if sub == "rates":
        rates_data = load_rates()
        rates = rates_data["rates"]
        names = rates_data.get("names", DEFAULT_RATES["names"])
        base = rates_data.get("base", "USD")
        date = rates_data.get("date", "unknown")
        print("=" * 60)
        print(f"货币汇率表 (基准: {base}, 日期: {date})")
        print("=" * 60)
        print(f"{'代码':<6} {'名称':<12} {'1 USD =':<14} {'精度提示'}")
        print("-" * 60)
        for code in sorted(rates.keys()):
            rate = rates[code]
            name = names.get(code, code)
            precision = "≈6位有效数字" if rate != int(rate) else "精确"
            print(f"{code:<6} {name:<12} {rate:<14.6g} {precision}")
        print()
        print(f"注: 汇率数据来源: 本地缓存 ({date})，仅供参考")
        return

    if sub == "update":
        print("正在从网络获取最新汇率...")
        rates_data = load_rates()
        rates_data["date"] = datetime.now().strftime("%Y-%m-%d")
        save_rates(rates_data)
        print(f"汇率已更新 (模拟网络更新，日期设为 {rates_data['date']})")
        print(f"汇率文件: {RATES_FILE}")
        return

    if len(args) >= 4 and ("to" in args or "in" in args):
        sep_idx = None
        for i, a in enumerate(args):
            if a.lower() in ("to", "in"):
                sep_idx = i
                break
        if sep_idx is not None and sep_idx >= 2:
            try:
                value = float(args[0])
            except ValueError:
                print(f"错误: 无法解析数值 '{args[0]}'")
                return
            from_ccy = args[1].upper()
            to_ccy = args[sep_idx + 1].upper() if sep_idx + 1 < len(args) else None
            if not to_ccy:
                print("错误: 缺少目标货币")
                return
            rates_data = load_rates()
            rates = rates_data["rates"]
            names = rates_data.get("names", DEFAULT_RATES["names"])
            date = rates_data.get("date", "unknown")
            if from_ccy not in rates:
                print(f"错误: 不支持的货币 '{from_ccy}'")
                return
            if to_ccy not in rates:
                print(f"错误: 不支持的货币 '{to_ccy}'")
                return
            from_rate = rates[from_ccy]
            to_rate = rates[to_ccy]
            usd_val = value / from_rate
            result = usd_val * to_rate
            from_name = names.get(from_ccy, from_ccy)
            to_name = names.get(to_ccy, to_ccy)
            cross_rate = to_rate / from_rate
            print(f"{format_number(value)} {from_ccy} ({from_name}) = {format_number(result)} {to_ccy} ({to_name})")
            print(f"  汇率: 1 {from_ccy} = {cross_rate:.6g} {to_ccy}")
            print(f"  数据日期: {date} | 精度提示: 仅供参考，实际汇率以银行为准")
            record_history("currency " + " ".join(args))
            return

    print("用法: currency <值> <源货币> to <目标货币>")
    print("示例: currency 100 USD to CNY")


def record_history(cmd_line):
    try:
        history = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "command": cmd_line,
        }
        history.append(entry)
        if len(history) > 50:
            history = history[-50:]
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def do_history(args):
    sub = args[0].lower() if args else ""
    if sub == "clear":
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f)
                print("历史记录已清空")
            except Exception as e:
                print(f"错误: {e}")
        else:
            print("历史记录为空")
        return
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    if not history:
        print("暂无历史记录")
        return
    if sub == "all":
        items = history
    else:
        items = history[-10:]
    print(f"历史记录 (共 {len(history)} 条):")
    print("-" * 60)
    for i, entry in enumerate(items, start=max(1, len(history) - len(items) + 1)):
        print(f"  [{i}] {entry['timestamp']}  {entry['command']}")
    print(f"\n  history all  - 查看全部 50 条")
    print(f"  history clear - 清空历史")


def load_favorites():
    if not FAVORITES_FILE.exists():
        return {}
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_favorites(favs):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)


def do_favorite(args):
    if not args:
        print("用法:")
        print("  favorite list                          - 列出所有收藏")
        print("  favorite add <名称> <命令...>         - 添加收藏")
        print("  favorite run <名称> [参数...]         - 运行收藏")
        print("  favorite remove <名称>                - 删除收藏")
        print("\n示例:")
        print("  favorite add usd2cny currency 100 USD to CNY")
        print("  favorite add km2mi convert {n} km to miles")
        print("  favorite run km2mi 50")
        return

    sub = args[0].lower()

    if sub == "list":
        favs = load_favorites()
        if not favs:
            print("暂无收藏")
            return
        print(f"收藏列表 (共 {len(favs)} 个):")
        print("-" * 60)
        for name, info in sorted(favs.items()):
            cmd = info.get("command", "")
            print(f"  {name:<20} {cmd}")
        return

    if sub == "add":
        if len(args) < 3:
            print("用法: favorite add <名称> <命令...>")
            return
        name = args[1]
        cmd = " ".join(args[2:])
        favs = load_favorites()
        favs[name] = {"command": cmd, "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_favorites(favs)
        print(f"已添加收藏: {name} -> {cmd}")
        return

    if sub == "remove" or sub == "rm":
        if len(args) < 2:
            print("用法: favorite remove <名称>")
            return
        name = args[1]
        favs = load_favorites()
        if name in favs:
            del favs[name]
            save_favorites(favs)
            print(f"已删除收藏: {name}")
        else:
            print(f"未找到收藏: {name}")
        return

    if sub == "run":
        if len(args) < 2:
            print("用法: favorite run <名称> [参数...]")
            return
        name = args[1]
        params = args[2:]
        favs = load_favorites()
        if name not in favs:
            print(f"未找到收藏: {name}")
            return
        cmd = favs[name]["command"]
        if "{n}" in cmd:
            if not params:
                print("错误: 该收藏需要参数，请提供数值")
                print(f"  命令模板: {cmd}")
                return
            cmd = cmd.replace("{n}", params[0])
        elif params:
            cmd += " " + " ".join(params)
        print(f"> {cmd}")
        cmd_parts = cmd.split()
        if cmd_parts:
            dispatch_command(cmd_parts[0], cmd_parts[1:])
        return

    print(f"未知子命令: {sub}")


def dispatch_command(cmd, args):
    cmd_lower = cmd.lower()
    if cmd_lower == "convert":
        do_convert(args)
    elif cmd_lower == "calc":
        do_calc(args)
    elif cmd_lower == "transfer":
        do_transfer_time(args)
    elif cmd_lower == "constants":
        do_constants(args)
    elif cmd_lower == "define":
        do_define(args)
    elif cmd_lower == "list-custom":
        do_list_custom()
    elif cmd_lower == "date":
        do_date(args)
    elif cmd_lower == "currency":
        do_currency(args)
    elif cmd_lower == "history":
        do_history(args)
    elif cmd_lower == "favorite":
        do_favorite(args)
    elif cmd_lower == "help":
        do_help()
    else:
        print(f"未知命令: {cmd}")


def do_transfer_time(args):
    sep_idx = None
    for i, a in enumerate(args):
        if a.lower() in ("on", "at", "over", "with"):
            sep_idx = i
            break
    if sep_idx is None or sep_idx < 2 or len(args) < sep_idx + 3:
        print("用法: transfer <大小> <数据单位> on <带宽值> <带宽单位>")
        print("示例: transfer 5 GB on 100 Mbps")
        return
    try:
        size = float(args[0])
    except ValueError:
        print(f"错误: 无法解析文件大小 '{args[0]}'")
        return
    data_unit_name = args[1]
    try:
        bandwidth = float(args[sep_idx + 1])
    except (ValueError, IndexError):
        print(f"错误: 无法解析带宽值")
        return
    bw_unit_name = args[sep_idx + 2] if len(args) > sep_idx + 2 else "Mbps"

    data_unit_key = resolve_unit(data_unit_name)
    bw_unit_key = resolve_unit(bw_unit_name)

    use_base10 = "--si" in args
    data_units = DATA_UNITS_BASE10 if use_base10 else DATA_UNITS_BASE2

    if data_unit_key not in data_units and data_unit_key not in DATA_UNITS_BASE2:
        print(f"错误: 未知数据单位 '{data_unit_name}'")
        return
    if bw_unit_key not in BANDWIDTH_UNITS:
        print(f"错误: 未知带宽单位 '{bw_unit_name}'")
        return

    size_in_bits = size * data_units[data_unit_key]["factor"]
    bw_in_bps = bandwidth * BANDWIDTH_UNITS[bw_unit_key]["factor"]
    if bw_in_bps == 0:
        print("错误: 带宽不能为0")
        return

    seconds = size_in_bits / bw_in_bps
    print(f"文件大小: {format_number(size)} {data_units[data_unit_key]['name']}")
    print(f"带宽: {format_number(bandwidth)} {BANDWIDTH_UNITS[bw_unit_key]['name']}")
    print(f"传输时间: {format_duration(seconds)}")


def format_duration(seconds):
    if seconds < 0.001:
        return f"{seconds * 1e6:.2f} 微秒"
    if seconds < 1:
        return f"{seconds * 1000:.2f} 毫秒"
    if seconds < 60:
        return f"{seconds:.2f} 秒"
    if seconds < 3600:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m} 分 {s:.1f} 秒"
    if seconds < 86400:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h} 时 {m} 分 {s:.1f} 秒"
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    m = int((seconds % 3600) // 60)
    return f"{d} 天 {h} 时 {m} 分"


def do_constants(args):
    if not args or args[0] == "list":
        print("=" * 70)
        print("物理常数库")
        print("=" * 70)
        cats = {}
        for c in PHYSICAL_CONSTANTS:
            cats.setdefault(c["category"], []).append(c)
        for cat, items in sorted(cats.items()):
            print(f"\n【{cat}】")
            for c in items:
                val_str = format_number(c["value"])
                print(f"  {c['symbol']:8s} {c['name']:<20s} = {val_str} {c['unit']}")
        print()
        return

    if args[0] == "search":
        if len(args) < 2:
            print("用法: constants search <关键词>")
            return
        keyword = " ".join(args[1:]).lower()
        results = []
        for c in PHYSICAL_CONSTANTS:
            if (keyword in c["name"].lower() or keyword in c["symbol"].lower()
                    or keyword in c["category"].lower() or keyword in c.get("desc", "").lower()):
                results.append(c)
        if not results:
            print(f"未找到与 '{keyword}' 相关的常数")
            return
        print(f"搜索结果 ({len(results)} 个):")
        for c in results:
            val_str = format_number(c["value"])
            print(f"  {c['symbol']:8s} {c['name']:<20s} = {val_str} {c['unit']}")
        return

    name = " ".join(args).lower()
    for c in PHYSICAL_CONSTANTS:
        if name in (c["symbol"].lower(), c["name"].lower()):
            print(f"符号: {c['symbol']}")
            print(f"名称: {c['name']}")
            print(f"数值: {c['value']}")
            print(f"单位: {c['unit']}")
            print(f"领域: {c['category']}")
            print(f"说明: {c.get('desc', '无')}")
            return
    print(f"未找到常数 '{name}'，使用 'constants search <关键词>' 搜索")


def do_define(args):
    expr = " ".join(args)
    match = re.match(r'(\S+)\s*=\s*([\d.eE+\-]+)\s+(\S+)', expr)
    if not match:
        print("用法: define <单位名> = <数值> <基准单位>")
        print("示例: define 光年 = 9.461e15 m")
        print("      define 光年 = 9.461e15 米")
        return

    unit_name = match.group(1).lower()
    factor = float(match.group(2))
    base_name = match.group(3)

    base_key = resolve_unit(base_name)
    if base_key is None:
        print(f"错误: 未知基准单位 '{base_name}'")
        return

    custom = load_custom_units()
    custom[unit_name] = {"factor": factor, "base": base_key, "display_name": unit_name}
    ALIAS_MAP[unit_name] = unit_name
    save_custom_units(custom)
    base_display = base_name
    for cat_units in UNIT_CATEGORIES.values():
        if base_key in cat_units:
            base_display = cat_units[base_key]["name"]
            break
    print(f"已定义: 1 {unit_name} = {format_number(factor)} {base_display}")
    print(f"配置已保存到 {CONFIG_FILE}")


def do_list_custom():
    custom = load_custom_units()
    if not custom:
        print("尚未定义自定义单位")
        print("使用 'define <单位名> = <数值> <基准单位>' 来定义")
        return
    print("自定义单位列表:")
    print("-" * 50)
    for name, info in custom.items():
        base_key = info["base"]
        base_display = base_key
        for cat_units in UNIT_CATEGORIES.values():
            if base_key in cat_units:
                base_display = cat_units[base_key]["name"]
                break
        print(f"  1 {name} = {format_number(info['factor'])} {base_display}")
    print(f"\n配置文件: {CONFIG_FILE}")


def do_date(args):
    if not args:
        print("日期/时间命令:")
        print("  date diff <日期1> <日期2>       - 计算两日期间隔天数")
        print("  date timestamp <时间戳>          - 时间戳转日期")
        print("  date now                         - 当前时间信息")
        print("  date workdays <日期1> <日期2>     - 计算工作日数(排除周末)")
        print("  date timezone                    - 显示常见时区UTC偏移")
        print("  date convert <时间> <源时区> <目标时区> - 时区转换")
        print("\n日期格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
        return

    sub = args[0].lower()

    if sub == "diff":
        if len(args) < 3:
            print("用法: date diff <日期1> <日期2>")
            return
        d1 = parse_date(args[1])
        d2 = parse_date(args[2])
        if d1 is None or d2 is None:
            print("错误: 日期格式无效，请使用 YYYY-MM-DD")
            return
        delta = d2 - d1
        days = abs(delta.days)
        weeks = days // 7
        rem_days = days % 7
        print(f"日期1: {d1.strftime('%Y-%m-%d')}")
        print(f"日期2: {d2.strftime('%Y-%m-%d')}")
        print(f"间隔: {days} 天 ({weeks} 周 {rem_days} 天)")
        return

    if sub == "timestamp":
        if len(args) < 2:
            print("用法: date timestamp <时间戳>")
            return
        try:
            ts = float(args[1])
        except ValueError:
            print(f"错误: 无法解析时间戳 '{args[1]}'")
            return
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        dt_local = datetime.fromtimestamp(ts)
        print(f"时间戳: {ts}")
        print(f"UTC时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"本地时间: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")

    if sub == "now":
        now = datetime.now()
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        print(f"本地时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"UTC时间: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Unix时间戳: {int(now.timestamp())}")
        print(f"今年第 {now.timetuple().tm_yday} 天")
        print(f"星期{['一','二','三','四','五','六','日'][now.weekday()]}")

    if sub == "workdays":
        if len(args) < 3:
            print("用法: date workdays <日期1> <日期2>")
            return
        d1 = parse_date(args[1])
        d2 = parse_date(args[2])
        if d1 is None or d2 is None:
            print("错误: 日期格式无效，请使用 YYYY-MM-DD")
            return
        if d1 > d2:
            d1, d2 = d2, d1
        workdays = 0
        current = d1
        while current <= d2:
            if current.weekday() < 5:
                workdays += 1
            current += timedelta(days=1)
        total_days = (d2 - d1).days + 1
        weekends = total_days - workdays
        print(f"起始日期: {d1.strftime('%Y-%m-%d')}")
        print(f"结束日期: {d2.strftime('%Y-%m-%d')}")
        print(f"总天数: {total_days}")
        print(f"工作日: {workdays} 天")
        print(f"周末: {weekends} 天")

    if sub == "timezone":
        timezones = [
            ("UTC", 0, "协调世界时"),
            ("UTC+8", 8, "中国标准时间(CST)"),
            ("UTC+9", 9, "日本标准时间(JST)"),
            ("UTC+5:30", 5.5, "印度标准时间(IST)"),
            ("UTC+1", 1, "中欧时间(CET)"),
            ("UTC+0", 0, "格林威治标准时间(GMT)"),
            ("UTC-5", -5, "美国东部时间(EST)"),
            ("UTC-6", -6, "美国中部时间(CST)"),
            ("UTC-7", -7, "美国山地时间(MST)"),
            ("UTC-8", -8, "美国太平洋时间(PST)"),
            ("UTC-3", -3, "巴西利亚时间"),
            ("UTC+10", 10, "澳大利亚东部时间"),
            ("UTC+5:45", 5.75, "尼泊尔时间"),
            ("UTC+3:30", 3.5, "伊朗标准时间"),
            ("UTC+12", 12, "新西兰时间"),
            ("UTC-10", -10, "夏威夷标准时间"),
        ]
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        print("常见时区UTC偏移:")
        print("-" * 65)
        print(f"{'时区':<12} {'偏移(小时)':<12} {'说明':<25} {'当前时间'}")
        print("-" * 65)
        for tz_name, offset, desc in timezones:
            tz_time = now_utc + timedelta(hours=offset)
            offset_str = f"{offset:+.1f}" if offset != int(offset) else f"{int(offset):+d}"
            print(f"{tz_name:<12} {offset_str:<12} {desc:<25} {tz_time.strftime('%Y-%m-%d %H:%M')}")

    if sub == "convert":
        if len(args) < 4:
            print("用法: date convert <YYYY-MM-DD HH:MM> <源时区> <目标时区>")
            print("示例: date convert '2024-01-15 08:00' UTC+8 UTC-5")
            return
        datetime_str = args[1]
        if len(args) >= 5:
            datetime_str = args[1] + " " + args[2]
            from_tz = args[3]
            to_tz = args[4]
        else:
            from_tz = args[2]
            to_tz = args[3]
        dt = parse_datetime(datetime_str)
        if dt is None:
            print(f"错误: 日期时间格式无效 '{datetime_str}'")
            return
        from_offset = parse_tz_offset(from_tz)
        to_offset = parse_tz_offset(to_tz)
        if from_offset is None:
            print(f"错误: 无效时区 '{from_tz}'，格式如 UTC+8 或 UTC-5")
            return
        if to_offset is None:
            print(f"错误: 无效时区 '{to_tz}'，格式如 UTC+8 或 UTC-5")
            return
        diff_hours = to_offset - from_offset
        result_dt = dt + timedelta(hours=diff_hours)
        print(f"源时间: {dt.strftime('%Y-%m-%d %H:%M:%S')} ({from_tz})")
        print(f"目标时间: {result_dt.strftime('%Y-%m-%d %H:%M:%S')} ({to_tz})")
        print(f"时差: {diff_hours:+.1f} 小时")


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%Y/%m/%d")
    except ValueError:
        pass
    return None


def parse_datetime(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_tz_offset(s):
    s = s.upper().strip()
    m = re.match(r'UTC([+-]\d+(?::\d+)?)', s)
    if not m:
        return None
    offset_str = m.group(1)
    parts = offset_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    if hours < 0:
        return hours - minutes / 60
    return hours + minutes / 60


def do_help():
    print("=" * 60)
    print("  UnitCalc - 终端单位换算与物理常数查询工具")
    print("=" * 60)
    print()
    print("【单位换算】")
    print("  convert <表达式/值> [源单位] to <目标单位>  单位换算")
    print("    示例: convert 100 km to miles")
    print("          convert 2*3.14 km to miles       (表达式)")
    print("          convert 100 km/h to m/s           (复合单位)")
    print("          convert 100 cm + 2 m to inches    (加减运算)")
    print("          convert 5 GB to MB --si           (1000进制)")
    print()
    print("  calc <带单位表达式>                 带单位四则运算")
    print("    示例: calc 5km + 3miles")
    print("          calc 100m / 10s")
    print()
    print("  transfer <大小> <单位> on <带宽> <单位>  传输时间计算")
    print("    示例: transfer 5 GB on 100 Mbps")
    print()
    print("【物理常数】")
    print("  constants [list]                    列出所有物理常数")
    print("  constants search <关键词>           搜索物理常数")
    print("  constants <名称>                    查看常数详情")
    print()
    print("【自定义单位】")
    print("  define <单位> = <值> <基准单位>     定义自定义单位")
    print("    示例: define 光年 = 9.461e15 m")
    print("  list-custom                         查看自定义单位列表")
    print()
    print("【货币汇率】")
    print("  currency <值> <源货币> to <目标货币> 货币换算")
    print("    示例: currency 100 USD to CNY")
    print("  currency rates                      显示所有汇率表")
    print("  currency update                     更新本地汇率")
    print("  支持货币: USD/CNY/EUR/GBP/JPY/KRW/HKD/SGD/AUD/CAD")
    print()
    print("【日期时间】")
    print("  date diff <日期1> <日期2>           日期差计算")
    print("  date timestamp <时间戳>             时间戳转日期")
    print("  date now                             当前时间信息")
    print("  date workdays <日期1> <日期2>        工作日计算")
    print("  date timezone                        时区列表")
    print("  date convert <时间> <源时区> <目标时区> 时区转换")
    print()
    print("【历史记录 & 收藏夹】")
    print("  history [all|clear]                 查看/清空历史记录(最近50条)")
    print("  favorite list                       列出所有收藏")
    print("  favorite add <名称> <命令...>       添加收藏(支持{n}参数模板)")
    print("  favorite run <名称> [参数...]       运行收藏")
    print("  favorite remove <名称>              删除收藏")
    print("    示例: favorite add km2mi convert {n} km to miles")
    print("          favorite run km2mi 50")
    print()
    print("  help                                显示帮助")
    print("  exit / quit                         退出REPL模式")
    print()
    print("REPL模式可直接输入表达式:")
    print("  5 kg in pounds")
    print("  100 km to miles")
    print("  32 f to c")


def parse_repl_input(line):
    line = line.strip()
    if not line:
        return

    if line.lower() in ("exit", "quit", "q"):
        print("再见!")
        sys.exit(0)

    if line.lower() == "help":
        do_help()
        return

    if line.lower() == "list-custom":
        do_list_custom()
        return

    parts = line.split()
    cmd = parts[0].lower()

    dispatch_command(cmd, parts[1:])
    if cmd in ("convert", "calc", "transfer", "constants", "define", "date",
               "currency", "history", "favorite", "help", "list-custom"):
        return

    try:
        value = float(parts[0])
        if "to" in parts or "in" in parts:
            do_convert(parts)
            return
    except ValueError:
        pass

    print(f"未知命令: {line}")
    print("输入 'help' 查看帮助")


def repl_mode():
    print("UnitCalc 交互模式 - 输入 'help' 查看帮助, 'exit' 退出")
    print()
    while True:
        try:
            line = input("unitcalc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        if line:
            parse_repl_input(line)


def main():
    custom = load_custom_units()
    for name, info in custom.items():
        ALIAS_MAP[name] = name

    if len(sys.argv) < 2:
        repl_mode()
        return

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    if cmd in ("convert", "calc", "transfer", "constants", "define",
               "list-custom", "date", "currency", "history", "favorite", "help"):
        dispatch_command(cmd, args)
    else:
        all_args = sys.argv[1:]
        parts = all_args
        try:
            float(parts[0])
            do_convert(parts)
        except ValueError:
            print(f"未知命令: {cmd}")
            print("使用 'python unitcalc.py help' 查看帮助")


if __name__ == "__main__":
    main()
