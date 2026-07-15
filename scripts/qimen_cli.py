#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from lunar_python import Lunar, Solar
except ImportError:  # 未安装时用随包附带的 vendor 副本（chat/沙箱环境）
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
    from lunar_python import Lunar, Solar

DEFAULT_RULESET = "mainline-cn-v1"
DEFAULT_TIMEZONE = "Asia/Shanghai"
CHINA_NAMES = {"cn", "china", "中国", "中华人民共和国", ""}

JIAZI = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

YANG_TERMS = {
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
}

JU_TABLE = {
    "阳遁": {
        "冬至": {"上元": 1, "中元": 7, "下元": 4},
        "小寒": {"上元": 2, "中元": 8, "下元": 5},
        "大寒": {"上元": 3, "中元": 9, "下元": 6},
        "立春": {"上元": 8, "中元": 5, "下元": 2},
        "雨水": {"上元": 9, "中元": 6, "下元": 3},
        "惊蛰": {"上元": 1, "中元": 7, "下元": 4},
        "春分": {"上元": 3, "中元": 9, "下元": 6},
        "清明": {"上元": 4, "中元": 1, "下元": 7},
        "谷雨": {"上元": 5, "中元": 2, "下元": 8},
        "立夏": {"上元": 4, "中元": 1, "下元": 7},
        "小满": {"上元": 5, "中元": 2, "下元": 8},
        "芒种": {"上元": 6, "中元": 3, "下元": 9},
    },
    "阴遁": {
        "夏至": {"上元": 9, "中元": 3, "下元": 6},
        "小暑": {"上元": 8, "中元": 2, "下元": 5},
        "大暑": {"上元": 7, "中元": 1, "下元": 4},
        "立秋": {"上元": 2, "中元": 5, "下元": 8},
        "处暑": {"上元": 1, "中元": 4, "下元": 7},
        "白露": {"上元": 9, "中元": 3, "下元": 6},
        "秋分": {"上元": 7, "中元": 1, "下元": 4},
        "寒露": {"上元": 6, "中元": 9, "下元": 3},
        "霜降": {"上元": 5, "中元": 8, "下元": 2},
        "立冬": {"上元": 6, "中元": 9, "下元": 3},
        "小雪": {"上元": 5, "中元": 8, "下元": 2},
        "大雪": {"上元": 4, "中元": 7, "下元": 1},
    },
}

EARTH_STEM_ORDER = {
    "阳遁": ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"],
    "阴遁": ["戊", "乙", "丙", "丁", "癸", "壬", "辛", "庚", "己"],
}

ROTATION_RING = [1, 8, 3, 4, 9, 2, 7, 6]
STAR_RING = ["天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"]
DOOR_RING = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
GOD_RING_YANG = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
GOD_RING_YIN = ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "螣蛇"]

XUNSHOU_TO_HIDDEN_YI = {
    "甲子": "戊",
    "甲戌": "己",
    "甲申": "庚",
    "甲午": "辛",
    "甲辰": "壬",
    "甲寅": "癸",
}

BRANCH_TO_PALACE = {
    "子": 1,
    "丑": 8,
    "寅": 8,
    "卯": 3,
    "辰": 4,
    "巳": 4,
    "午": 9,
    "未": 2,
    "申": 2,
    "酉": 7,
    "戌": 6,
    "亥": 6,
}

PALACE_INFO = {
    1: {"name": "坎宫", "direction": "北", "trigram": "坎", "element": "水"},
    2: {"name": "坤宫", "direction": "西南", "trigram": "坤", "element": "土"},
    3: {"name": "震宫", "direction": "东", "trigram": "震", "element": "木"},
    4: {"name": "巽宫", "direction": "东南", "trigram": "巽", "element": "木"},
    5: {"name": "中宫", "direction": "中", "trigram": "中", "element": "土"},
    6: {"name": "乾宫", "direction": "西北", "trigram": "乾", "element": "金"},
    7: {"name": "兑宫", "direction": "西", "trigram": "兑", "element": "金"},
    8: {"name": "艮宫", "direction": "东北", "trigram": "艮", "element": "土"},
    9: {"name": "离宫", "direction": "南", "trigram": "离", "element": "火"},
}

GRID_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6]

# ---------- daoist-yinpan（道家阴盘奇门）专用常量 ----------

YINPAN_RULESET = "daoist-yinpan"
YINPAN_RULESET_ALIASES = {YINPAN_RULESET}

BRANCH_INDEX = {
    "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
    "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12,
}

# 马星：按时支三合取驿马，落宫为四隅宫
HORSE_PALACE = {
    "亥": 4, "卯": 4, "未": 4,   # 亥卯未时 马星在巽
    "申": 8, "子": 8, "辰": 8,   # 申子辰时 马星在艮
    "寅": 2, "午": 2, "戌": 2,   # 寅午戌时 马星在坤
    "巳": 6, "酉": 6, "丑": 6,   # 巳酉丑时 马星在乾
}

# 驿马地支：三合局首字冲位（申子辰马在寅、寅午戌马在申、巳酉丑马在亥、亥卯未马在巳）
HORSE_BRANCH = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

# 空亡转宫表：人在面前（近空/先天断）——落宫空亡转到该宫先天卦的后天位置
ZHUAN_GONG_PRESENT = {1: 2, 8: 3, 3: 9, 4: 7, 9: 6, 2: 4, 7: 1, 6: 8}
# 空亡转宫表：人不在面前（远空/后天断）——飘着转，转到该宫对应的先天卦宫
ZHUAN_GONG_ABSENT = {1: 7, 9: 3, 7: 4, 3: 8, 4: 2, 2: 1, 6: 9, 8: 6}

# 阴盘地盘布干固定顺序（阳局按宫数顺布，阴局按宫数逆布）
YINPAN_STEM_SEQ = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]

# ---------- 终身盘（奇门命理盘）----------
# 用神：年干、日干在天盘的落宫；四害层级：门迫＞击刑＞入墓＞空亡。

DOOR_ELEMENT = {
    "休门": "水", "生门": "土", "伤门": "木", "杜门": "木",
    "景门": "火", "死门": "土", "惊门": "金", "开门": "金",
}
ELEMENT_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
ELEMENT_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 六仪击刑：戊落震（子刑卯）、己落坤（戌刑未）、庚落艮（申刑寅）、
# 辛落离（午自刑）、壬落巽（辰自刑）、癸落巽（寅刑巳）
JIXING_PALACE = {"戊": 3, "己": 2, "庚": 8, "辛": 9, "壬": 4, "癸": 4}

# 十干入墓（按阴阳长生诀）：未墓坤、戌墓乾、丑墓艮、辰墓巽
RUMU_PALACE = {
    "甲": 2, "癸": 2,           # 墓未 → 坤
    "乙": 6, "丙": 6, "戊": 6,  # 墓戌 → 乾
    "丁": 8, "己": 8, "庚": 8,  # 墓丑 → 艮
    "辛": 4, "壬": 4,           # 墓辰 → 巽
}

# ---------- 十二长生（宫位地支上的干支状态，供盘面展示）----------
CHANGSHENG_ABBR = "生沐冠临旺衰病死墓绝胎养"
CHANGSHENG_FULL = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
CHANGSHENG_START = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",  # 阳干顺行
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",  # 阴干逆行
}
BRANCHES_SEQ = "子丑寅卯辰巳午未申酉戌亥"
PALACE_BRANCHES = {
    1: ["子"], 8: ["丑", "寅"], 3: ["卯"], 4: ["辰", "巳"], 9: ["午"],
    2: ["未", "申"], 7: ["酉"], 6: ["戌", "亥"], 5: [],
}

# 月将：换将于中气（雨水后亥将……大寒后子将）
YUEJIANG_BY_QI = {
    "雨水": "亥", "春分": "戌", "谷雨": "酉", "小满": "申", "夏至": "未", "大暑": "午",
    "处暑": "巳", "秋分": "辰", "霜降": "卯", "小雪": "寅", "冬至": "丑", "大寒": "子",
}


def changsheng_index(stem: str, branch: str) -> int:
    """干在支上的十二长生序（0=长生）。阳顺阴逆。"""
    start = BRANCHES_SEQ.index(CHANGSHENG_START[stem])
    step = 1 if STEM_ORDER.index(stem) % 2 == 0 else -1
    return (BRANCHES_SEQ.index(branch) - start) * step % 12


def palace_changsheng(stem: str | None, palace_no: int) -> str | None:
    """干落宫的长生状态标签：单支宫单字（旺/死…），双支宫合并两字（沐冠/死墓…），养+长生记“养生”。"""
    branches = PALACE_BRANCHES.get(palace_no) or []
    if not stem or not branches:
        return None
    idxs = sorted({changsheng_index(stem, b) for b in branches})
    if set(idxs) == {0, 11}:
        return "养生"
    return "".join(CHANGSHENG_ABBR[i] for i in idxs)


def changsheng_entries(stems: list[str] | None, palace_no: int) -> list[dict[str, str]]:
    return [
        {"stem": s, "state": palace_changsheng(s, palace_no)}
        for s in (stems or [])
        if s and palace_changsheng(s, palace_no)
    ]


def jieqi_window(lunar: Any) -> dict[str, Any]:
    """当前所处节气区间（节+气都算）与月将。"""
    prev_jq = lunar.getPrevJieQi(False)
    next_jq = lunar.getNextJieQi(False)
    prev_qi = lunar.getPrevQi(False)
    yuejiang = YUEJIANG_BY_QI.get(prev_qi.getName()) if prev_qi else None
    return {
        "active_jie_started_at": prev_jq.getSolar().toYmdHms() if prev_jq else None,
        "next_jie": next_jq.getName() if next_jq else None,
        "next_jie_at": next_jq.getSolar().toYmdHms() if next_jq else None,
        "yuejiang": yuejiang,
        "yuejiang_qi": prev_qi.getName() if prev_qi else None,
    }


SEASON_BY_MONTH_BRANCH = {
    "寅": "春", "卯": "春", "辰": "四季",
    "巳": "夏", "午": "夏", "未": "四季",
    "申": "秋", "酉": "秋", "戌": "四季",
    "亥": "冬", "子": "冬", "丑": "四季",
}
SEASON_ELEMENT = {"春": "木", "夏": "火", "秋": "金", "冬": "水", "四季": "土"}

DUI_GONG = {1: 9, 9: 1, 2: 8, 8: 2, 3: 7, 7: 3, 4: 6, 6: 4}

PILLAR_ROLES = {
    "year": "祖上/父母/领导；个人根基与天赋",
    "month": "兄弟姐妹/平辈/门户",
    "day": "命主自己",
    "time": "子女/事业平台/晚运",
}


def wuxing_state(element: str, ling: str) -> str:
    """旺相休囚死：当令旺、令生者相、生令者休、克令者囚、令克者死。"""
    if element == ling:
        return "旺"
    if ELEMENT_SHENG[ling] == element:
        return "相"
    if ELEMENT_SHENG[element] == ling:
        return "休"
    if ELEMENT_KE[element] == ling:
        return "囚"
    return "死"


def palace_sihai(n: int, p: dict[str, Any], extra_earth: list[str] | None = None) -> list[dict[str, str]]:
    """单宫四害检测（中5宫无门，门迫不查）。

    干类四害（击刑/入墓）查天盘干与地盘干（含中宫寄坤的地盘干），隐干不查——
    按实盘校准（2026-07-14 终身盘截图：坤2地盘寄癸入墓、艮8地盘庚刑+墓）。
    """
    harms: list[dict[str, str]] = []
    door = p.get("door")
    if door and ELEMENT_KE[DOOR_ELEMENT[door]] == p["element"]:
        harms.append({"type": "门迫", "detail": f"{door}（{DOOR_ELEMENT[door]}）克{p['name']}（{p['element']}）"})
    layers: list[tuple[str, str]] = [("天盘", s) for s in (p.get("sky_stems") or [])]
    layers += [("地盘", s) for s in ([p["earth_stem"]] if p.get("earth_stem") else []) + (extra_earth or [])]
    for layer, stem in layers:
        if JIXING_PALACE.get(stem) == n:
            harms.append({"type": "击刑", "stem": stem, "layer": layer, "detail": f"{layer}{stem}落{p['name']}击刑"})
        if RUMU_PALACE.get(stem) == n:
            harms.append({"type": "入墓", "stem": stem, "layer": layer, "detail": f"{layer}{stem}入墓于{p['name']}"})
    if p.get("is_kongwang"):
        harms.append({"type": "空亡", "detail": f"{p['name']}旬空"})
    return harms


def detect_sihai(palaces_by_no: dict[int, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """全盘四害：仅收有四害的宫。坤2 附带中宫寄坤的地盘干一起查。"""
    center = palaces_by_no.get(5) or {}
    result: dict[str, list[dict[str, str]]] = {}
    for n, p in palaces_by_no.items():
        if n == 5:
            continue  # 中宫寄坤，其地盘干并入坤2检查
        extra = [center["earth_stem"]] if n == 2 and center.get("earth_stem") else None
        if harms := palace_sihai(n, p, extra_earth=extra):
            result[str(n)] = harms
    return result


def pillar_visible_stem(ganzhi: str) -> tuple[str, str | None]:
    """柱干入盘用干：甲按本柱旬首所遁之仪。返回 (入盘干, 备注)。"""
    stem = ganzhi[0]
    if stem != "甲":
        return stem, None
    idx = JIAZI.index(ganzhi)
    xun = JIAZI[idx - idx % 10]
    hidden = XUNSHOU_TO_HIDDEN_YI[xun]
    return hidden, f"{ganzhi}柱干为甲，按旬首{xun}所遁之仪{hidden}取用"


STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
BRANCH_MAIN_STEM = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}


def shishen(day_stem: str, other: str) -> str:
    """十神简称（比劫食伤才财杀官枭印），以日干为我。"""
    de, oe = STEM_ELEMENT[day_stem], STEM_ELEMENT[other]
    same_pol = STEM_ORDER.index(day_stem) % 2 == STEM_ORDER.index(other) % 2
    if oe == de:
        return "比" if same_pol else "劫"
    if ELEMENT_SHENG[de] == oe:
        return "食" if same_pol else "伤"
    if ELEMENT_SHENG[oe] == de:
        return "枭" if same_pol else "印"
    if ELEMENT_KE[de] == oe:
        return "才" if same_pol else "财"
    return "杀" if same_pol else "官"


def pillar_shishen(day_stem: str, ganzhi: str) -> str:
    """干支两字十神：天干十神+地支本气十神（app 同款标签）。"""
    return shishen(day_stem, ganzhi[0]) + shishen(day_stem, BRANCH_MAIN_STEM[ganzhi[1]])


def build_dayun(lunar: Any, gender: str | None, warnings: list[str]) -> dict[str, Any] | None:
    """八字式大运（app 校准）：月柱起排，阳男阴女顺、阴男阳女逆；
    顺数至下一节/逆数至上一节，3 天折 1 岁起运，十年一运。"""
    if gender not in {"male", "female"}:
        warnings.append("未提供性别，无法确定大运顺逆，未排大运。")
        return None
    year_gz = lunar.getYearInGanZhiExact()
    yang_year = STEM_ORDER.index(year_gz[0]) % 2 == 0
    forward = (yang_year and gender == "male") or (not yang_year and gender == "female")

    solar = lunar.getSolar()
    birth_dt = datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                        solar.getHour(), solar.getMinute(), solar.getSecond())
    jie = lunar.getNextJie(False) if forward else lunar.getPrevJie(False)
    jie_dt = datetime.fromisoformat(jie.getSolar().toYmdHms().replace(" ", "T"))
    # 起运（app 五盘校准）：天数舍尾取整，3 日折 1 年、1 日折 4 月；首运年 = 起运日所在公历年
    days = abs((jie_dt - birth_dt).total_seconds()) / 86400
    days_int = int(days)
    qiyun_years, qiyun_months = days_int // 3, days_int % 3 * 4
    total_m = birth_dt.month - 1 + qiyun_months
    qiyun_year = birth_dt.year + qiyun_years + total_m // 12
    qiyun_month = total_m % 12 + 1
    qiyun_date = f"{qiyun_year}-{qiyun_month:02d}-{min(birth_dt.day, 28):02d}"

    day_stem = lunar.getDayInGanZhiExact()[0]
    month_gz = lunar.getMonthInGanZhiExact()
    idx = JIAZI.index(month_gz)
    birth_year = solar.getYear()
    # 起运前月柱段的年份标签用干支年（立春前出生归上一公历年，app 同款）
    ganzhi_year = birth_year if year_ganzhi_of(birth_year) == year_gz else birth_year - 1

    entries = [{
        "start_year": ganzhi_year,
        "ganzhi": month_gz,
        "shishen": pillar_shishen(day_stem, month_gz),
        "pre_dayun": True,
    }]
    for n in range(1, 10):
        gz = JIAZI[(idx + n) % 60] if forward else JIAZI[(idx - n) % 60]
        entries.append({
            "start_year": qiyun_year + 10 * (n - 1),
            "ganzhi": gz,
            "shishen": pillar_shishen(day_stem, gz),
            "pre_dayun": False,
        })
    return {
        "direction": "顺排" if forward else "逆排",
        "counted_to_jie": jie.getName(),
        "qiyun_age": qiyun_years,
        "qiyun_months": qiyun_months,
        "qiyun_date_approx": qiyun_date,
        "list": entries,
        "note": "八字式大运（月柱起、阳男阴女顺/阴男阳女逆；天数舍尾，3日折1年、1日折4月）；首段为起运前的月柱期。",
    }


def year_ganzhi_of(year: int) -> str:
    """公历年份粗取干支（未按立春切分，边界需人工确认）。"""
    return STEM_ORDER[(year - 4) % 10] + "子丑寅卯辰巳午未申酉戌亥"[(year - 4) % 12]


def build_life_block(chart: dict[str, Any], lunar: Any, payload: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    palaces_by_no = {p["palace"]: p for p in chart["palaces"]}

    pillars: dict[str, Any] = {}
    pillar_ganzhi = {
        "year": lunar.getYearInGanZhiExact(),
        "month": lunar.getMonthInGanZhiExact(),
        "day": lunar.getDayInGanZhiExact(),
        "time": lunar.getTimeInGanZhi(),
    }
    for key, ganzhi in pillar_ganzhi.items():
        visible, note = pillar_visible_stem(ganzhi)
        if note:
            warnings.append(note)
        sky_palaces = [n for n, p in palaces_by_no.items() if visible in (p.get("sky_stems") or [])]
        hidden_palaces = [n for n, p in palaces_by_no.items() if visible in (p.get("hidden_stems") or [])]
        earth_palaces = [n for n, p in palaces_by_no.items() if p.get("earth_stem") == visible]
        pillars[key] = {
            "ganzhi": ganzhi,
            "stem": ganzhi[0],
            "stem_visible": visible,
            "note": note,
            "sky_palaces": sorted(sky_palaces),
            "hidden_palaces": sorted(hidden_palaces),
            "earth_palaces": sorted(earth_palaces),
            "role": PILLAR_ROLES[key],
        }

    sihai = detect_sihai(palaces_by_no)

    # 气之旺衰：以出生月支所值之令衡量各宫五行
    month_branch = pillar_ganzhi["month"][1]
    season = SEASON_BY_MONTH_BRANCH[month_branch]
    ling = SEASON_ELEMENT[season]
    palace_states = {
        str(n): {"element": p["element"], "state": wuxing_state(p["element"], ling)}
        for n, p in palaces_by_no.items()
    }

    # 流年：太岁地支落宫（书例：酉年看酉宫）
    liunian_years = payload.get("liunian_years")
    if not liunian_years:
        this_year = datetime.now().year
        liunian_years = list(range(this_year, this_year + 10))
    liunian = []
    for year in liunian_years:
        gz = year_ganzhi_of(int(year))
        liunian.append({
            "year": int(year),
            "ganzhi": gz,
            "branch": gz[1],
            "palace": BRANCH_TO_PALACE[gz[1]],
        })
    warnings.append("流年干支按公历年份粗取，未按立春切分；立春前出生或岁首边界请人工确认。")

    gender_raw = str(payload.get("gender") or "").strip().lower()
    gender = {"male": "male", "男": "male", "m": "male",
              "female": "female", "女": "female", "f": "female"}.get(gender_raw)
    dayun = build_dayun(lunar, gender, warnings)

    return {
        "gender": gender or (gender_raw or None),
        "dayun": dayun,
        "pillars": pillars,
        "sihai": sihai,
        "sihai_order": ["门迫", "击刑", "入墓", "空亡"],
        "wangshuai": {
            "month_branch": month_branch,
            "season": season,
            "ling_element": ling,
            "palace_states": palace_states,
        },
        "mirror": {
            "dui_gong": DUI_GONG,
            "note": "镜像断法：看对宫，以及先后天宫（先后天表沿用 zhuan_gong）。",
        },
        "liunian": liunian,
    }


# ---------- 刻盘（刻家）----------
# 一时辰十二刻，每刻 10 分钟；刻干支从时干按五鼠遁起子刻（甲己起甲子、乙庚起丙子、
# 丙辛起戊子、丁壬起庚子、戊癸起壬子），沿六十甲子顺排。已用实盘校准。
KE_MINUTES = 10
STEM_ORDER = "甲乙丙丁戊己庚辛壬癸"


def ke_anchor_index(time_gan: str) -> int:
    """五鼠遁起子刻：返回该时辰第一刻在六十甲子中的下标。"""
    return (STEM_ORDER.index(time_gan) % 5) * 12


def compute_ke(solar_dt: datetime, time_gan: str) -> dict[str, Any]:
    hour, minute = solar_dt.hour, solar_dt.minute
    start_hour = 23 if hour in (23, 0) else hour - (1 - hour % 2)
    minutes_into = (hour * 60 + minute - start_hour * 60) % (24 * 60)
    ke_index = minutes_into // KE_MINUTES  # 0..11
    idx = (ke_anchor_index(time_gan) + ke_index) % 60
    xun_start = idx - idx % 10
    return {
        "ganzhi": JIAZI[idx],
        "number": ke_index + 1,
        "xun": JIAZI[xun_start],
        "xunkong": JIAZI[(xun_start + 10) % 60][1] + JIAZI[(xun_start + 11) % 60][1],
        "minute_in_ke": minutes_into % KE_MINUTES,
    }


TIMEZONE_ALIASES = {"北京", "北京时间", "beijing", "beijing time", "cst", "中国标准时间"}


def get_timezone(name: str):
    if name.strip().lower() in TIMEZONE_ALIASES:
        name = DEFAULT_TIMEZONE
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=8), name=DEFAULT_TIMEZONE)
        if name.upper() == "UTC":
            return timezone.utc
        raise


@dataclass
class NormalizedInput:
    question_type: str
    question_goal: str
    calendar_type: str
    timezone: str
    country: str
    city: str
    use_now: bool
    leap_month: bool
    solar_dt: datetime
    lunar_input: dict[str, Any] | None
    original_time_input: Any
    warnings: list[str]


def rotate_to_start(seq: list[Any], start: Any) -> list[Any]:
    idx = seq.index(start)
    return seq[idx:] + seq[:idx]


def parse_datetime_string(value: str) -> dict[str, int]:
    normalized = value.strip().replace("T", " ").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", " ")
    normalized = normalized.replace("时", ":").replace("點", ":").replace("点", ":").replace("分", "").replace("秒", "")
    parts = normalized.split()
    if not parts:
        raise ValueError("time_input 不能为空")
    date_part = parts[0]
    date_bits = [int(bit) for bit in date_part.split("-") if bit]
    if len(date_bits) != 3:
        raise ValueError("日期格式需为 YYYY-MM-DD")
    time_bits = [0, 0, 0]
    if len(parts) > 1:
        raw_time = parts[1]
        tmp = [int(bit) for bit in raw_time.split(":") if bit]
        if len(tmp) >= 2:
            time_bits[0] = tmp[0]
            time_bits[1] = tmp[1]
        if len(tmp) >= 3:
            time_bits[2] = tmp[2]
    return {
        "year": date_bits[0],
        "month": date_bits[1],
        "day": date_bits[2],
        "hour": time_bits[0],
        "minute": time_bits[1],
        "second": time_bits[2],
    }


def resolve_timezone(location: dict[str, Any], warnings: list[str]) -> str:
    timezone = (location.get("timezone") or "").strip()
    if timezone.lower() in TIMEZONE_ALIASES:
        return DEFAULT_TIMEZONE
    if timezone:
        return timezone
    country = (location.get("country") or "").strip().lower()
    city = (location.get("city") or "").strip()
    if country in CHINA_NAMES or not country:
        return DEFAULT_TIMEZONE
    warnings.append(f"未提供海外时区，脚本暂按 {DEFAULT_TIMEZONE} 计算，请在访谈中先补齐时区。")
    if city:
        warnings.append(f"已收到海外城市 {city}，但仍缺少明确时区。")
    return DEFAULT_TIMEZONE


def normalize_input(payload: dict[str, Any]) -> NormalizedInput:
    warnings: list[str] = []
    location = payload.get("location") or {}
    timezone = resolve_timezone(location, warnings)
    try:
        tz = get_timezone(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"无法识别时区 {timezone}: {exc}") from exc

    calendar_type = str(payload.get("calendar_type") or "solar").strip().lower()
    original_time_input = payload.get("time_input")
    leap_month = False
    lunar_input: dict[str, Any] | None = None

    if calendar_type == "now":
        solar_dt = datetime.now(tz).replace(microsecond=0)
        use_now = True
    elif calendar_type == "solar":
        use_now = False
        if isinstance(original_time_input, dict):
            raw = {
                "year": int(original_time_input["year"]),
                "month": int(original_time_input["month"]),
                "day": int(original_time_input["day"]),
                "hour": int(original_time_input.get("hour", 0)),
                "minute": int(original_time_input.get("minute", 0)),
                "second": int(original_time_input.get("second", 0)),
            }
        else:
            raw = parse_datetime_string(str(original_time_input))
        solar_dt = datetime(raw["year"], raw["month"], raw["day"], raw["hour"], raw["minute"], raw["second"], tzinfo=tz)
    elif calendar_type == "lunar":
        use_now = False
        if isinstance(original_time_input, dict):
            raw = {
                "year": int(original_time_input["year"]),
                "month": int(original_time_input["month"]),
                "day": int(original_time_input["day"]),
                "hour": int(original_time_input.get("hour", 0)),
                "minute": int(original_time_input.get("minute", 0)),
                "second": int(original_time_input.get("second", 0)),
                "is_leap_month": bool(original_time_input.get("is_leap_month", False)),
            }
        else:
            raw = parse_datetime_string(str(original_time_input))
            raw["is_leap_month"] = bool(payload.get("is_leap_month", False))
        leap_month = bool(raw.get("is_leap_month", False))
        lunar_month = -raw["month"] if leap_month else raw["month"]
        lunar_obj = Lunar.fromYmdHms(raw["year"], lunar_month, raw["day"], raw["hour"], raw["minute"], raw["second"])
        solar_obj = lunar_obj.getSolar()
        solar_dt = datetime(
            solar_obj.getYear(),
            solar_obj.getMonth(),
            solar_obj.getDay(),
            solar_obj.getHour(),
            solar_obj.getMinute(),
            solar_obj.getSecond(),
            tzinfo=tz,
        )
        lunar_input = raw
    else:
        raise ValueError(f"不支持的 calendar_type: {calendar_type}")

    # 夏令时（如中国 1986-1991）：墙上钟时比标准时快，排盘折回标准时（app 同款处理）
    dst = solar_dt.dst()
    if dst:
        solar_dt = solar_dt - dst
        warnings.append(
            f"起局时间处于夏令时区间，已折算为标准时 {solar_dt.strftime('%Y-%m-%d %H:%M')} 排盘。"
        )

    return NormalizedInput(
        question_type=str(payload.get("question_type") or "").strip(),
        question_goal=str(payload.get("question_goal") or "").strip(),
        calendar_type=calendar_type,
        timezone=timezone,
        country=str(location.get("country") or "").strip(),
        city=str(location.get("city") or "").strip(),
        use_now=use_now,
        leap_month=leap_month,
        solar_dt=solar_dt,
        lunar_input=lunar_input,
        original_time_input=original_time_input,
        warnings=warnings,
    )


def build_solar_and_lunar(normalized: NormalizedInput) -> tuple[Solar, Any]:
    solar = Solar.fromYmdHms(
        normalized.solar_dt.year,
        normalized.solar_dt.month,
        normalized.solar_dt.day,
        normalized.solar_dt.hour,
        normalized.solar_dt.minute,
        normalized.solar_dt.second,
    )
    lunar = solar.getLunar()
    return solar, lunar


def active_jie(lunar: Any) -> tuple[str, Any, Any]:
    prev_jie = lunar.getPrevJie(False)
    next_jie = lunar.getNextJie(False)
    if prev_jie is None:
        raise ValueError("无法确定当前节令")
    return prev_jie.getName(), prev_jie, next_jie


def compute_yuan(day_ganzhi: str) -> str:
    idx = JIAZI.index(day_ganzhi)
    return ["上元", "中元", "下元"][(idx // 5) % 3]


def compute_earth_plate(dun_type: str, ju_number: int) -> dict[int, str]:
    palaces = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rotated = rotate_to_start(palaces, ju_number)
    stems = EARTH_STEM_ORDER[dun_type]
    return dict(zip(rotated, stems))


def find_stem_palace(earth_plate: dict[int, str], stem: str) -> int:
    for palace, palace_stem in earth_plate.items():
        if palace_stem == stem:
            return palace
    raise ValueError(f"地盘中未找到天干 {stem}")


def hosted_palace(palace: int) -> int:
    return 2 if palace == 5 else palace


def split_branch_pair(text: str) -> list[str]:
    return [text[i : i + 1] for i in range(0, len(text), 1) if text[i : i + 1]]


def build_chart(normalized: NormalizedInput, solar: Solar, lunar: Any) -> dict[str, Any]:
    warnings = list(normalized.warnings)

    current_jie_name, prev_jie, next_jie = active_jie(lunar)
    dun_type = "阳遁" if current_jie_name in YANG_TERMS else "阴遁"
    day_ganzhi = lunar.getDayInGanZhiExact()
    yuan = compute_yuan(day_ganzhi)
    ju_number = JU_TABLE[dun_type][current_jie_name][yuan]
    earth_plate = compute_earth_plate(dun_type, ju_number)

    time_ganzhi = lunar.getTimeInGanZhi()
    time_gan = lunar.getTimeGan()
    time_xun = lunar.getTimeXun()
    time_xunkong = lunar.getTimeXunKong()
    hidden_yi = XUNSHOU_TO_HIDDEN_YI[time_xun]
    visible_time_gan = hidden_yi if time_gan == "甲" else time_gan
    if time_gan == "甲":
        warnings.append(f"时干为甲，按旬首所遁之仪 {hidden_yi} 入盘。")

    xunshou_raw_palace = find_stem_palace(earth_plate, hidden_yi)
    time_raw_palace = find_stem_palace(earth_plate, visible_time_gan)
    xunshou_palace = hosted_palace(xunshou_raw_palace)
    time_palace = hosted_palace(time_raw_palace)

    if xunshou_raw_palace == 5 or time_raw_palace == 5:
        warnings.append("本规则集中宫相关判断一律寄坤处理。")

    if dun_type == "阳遁":
        palace_order = rotate_to_start(ROTATION_RING, time_palace)
        star_order = rotate_to_start(STAR_RING, STAR_RING[ROTATION_RING.index(xunshou_palace)])
        door_order = rotate_to_start(DOOR_RING, DOOR_RING[ROTATION_RING.index(xunshou_palace)])
        god_order = GOD_RING_YANG
        outer_earth = [earth_plate[palace] for palace in ROTATION_RING]
    else:
        reverse_ring = list(reversed(ROTATION_RING))
        reverse_star_ring = list(reversed(STAR_RING))
        reverse_door_ring = list(reversed(DOOR_RING))
        palace_order = rotate_to_start(reverse_ring, time_palace)
        star_order = rotate_to_start(reverse_star_ring, STAR_RING[ROTATION_RING.index(xunshou_palace)])
        door_order = rotate_to_start(reverse_door_ring, DOOR_RING[ROTATION_RING.index(xunshou_palace)])
        god_order = GOD_RING_YIN
        outer_earth = [earth_plate[palace] for palace in reverse_ring]

    sky_start_stem = hidden_yi if xunshou_raw_palace != 5 else earth_plate[xunshou_palace]
    sky_order = rotate_to_start(outer_earth, sky_start_stem)
    star_map = dict(zip(palace_order, star_order))
    door_map = dict(zip(palace_order, door_order))
    god_map = dict(zip(palace_order, god_order))
    sky_map = dict(zip(palace_order, sky_order))

    zhifu = {"star": star_map[time_palace], "palace": time_palace}
    zhishi = {"door": door_map[time_palace], "palace": time_palace}

    active_jie_dt = datetime.fromisoformat(prev_jie.getSolar().toYmdHms().replace(" ", "T")).replace(tzinfo=normalized.solar_dt.tzinfo)
    next_jie_dt = None
    if next_jie is not None:
        next_jie_dt = datetime.fromisoformat(next_jie.getSolar().toYmdHms().replace(" ", "T")).replace(tzinfo=normalized.solar_dt.tzinfo)
    if abs(normalized.solar_dt - active_jie_dt) <= timedelta(hours=24):
        warnings.append("当前时间距离节令起点较近，属于节气边界附近。")
    if next_jie_dt and abs(next_jie_dt - normalized.solar_dt) <= timedelta(hours=24):
        warnings.append("当前时间距离下一个节令较近，属于节气边界附近。")

    kongwang_branches = split_branch_pair(time_xunkong)
    kongwang_palaces = sorted({BRANCH_TO_PALACE[branch] for branch in kongwang_branches if branch in BRANCH_TO_PALACE})

    palaces: list[dict[str, Any]] = []
    for palace_no in sorted(PALACE_INFO):
        info = PALACE_INFO[palace_no]
        palace_entry = {
            "palace": palace_no,
            "name": info["name"],
            "direction": info["direction"],
            "trigram": info["trigram"],
            "element": info["element"],
            "earth_stem": earth_plate.get(palace_no),
            "sky_stem": sky_map.get(palace_no),
            "star": "天禽" if palace_no == 5 else star_map.get(palace_no),
            "door": None if palace_no == 5 else door_map.get(palace_no),
            "god": None if palace_no == 5 else god_map.get(palace_no),
            "is_center": palace_no == 5,
            "hosts_center": palace_no == 2,
            "hosting_note": "中宫寄坤" if palace_no in {2, 5} else None,
        }
        palaces.append(palace_entry)

    return {
        "dun_type": dun_type,
        "yuan": yuan,
        "ju_number": ju_number,
        "xunshou": time_xun,
        "hidden_yi": hidden_yi,
        "kongwang": kongwang_branches,
        "kongwang_palaces": kongwang_palaces,
        "time_stem_visible": visible_time_gan,
        "zhifu": zhifu,
        "zhishi": zhishi,
        "active_jie": current_jie_name,
        "active_jie_started_at": prev_jie.getSolar().toYmdHms(),
        "next_jie": next_jie.getName() if next_jie else None,
        "next_jie_at": next_jie.getSolar().toYmdHms() if next_jie else None,
        "grid_order": GRID_ORDER,
        "palaces": palaces,
        "warnings": warnings,
    }


def yinpan_active_jieqi(lunar: Any) -> str:
    """取当前所处的节气（节+气都算，用于冬至/夏至分阴阳遁）。"""
    prev_jie = lunar.getPrevJie(False)
    prev_qi = lunar.getPrevQi(False)
    candidates = [item for item in (prev_jie, prev_qi) if item is not None]
    if not candidates:
        raise ValueError("无法确定当前节气")
    latest = max(candidates, key=lambda item: item.getSolar().toYmdHms())
    return latest.getName()


def yinpan_ju(lunar: Any, warnings: list[str], ke_branch: str | None = None) -> tuple[str, int, dict[str, Any]]:
    """阴盘定局：局数 =（年支序 + 农历月 + 农历日 + 时支序 [+ 刻支序]）% 9，余 0 取 9。"""
    year_gz = lunar.getYearInGanZhi()
    year_branch = year_gz[1]
    lunar_month = lunar.getMonth()
    if lunar_month < 0:
        warnings.append("起局时间在闰月内，定局公式按同名月份的月数计算，结果供参考。")
    month_num = abs(lunar_month)
    day_num = lunar.getDay()
    time_branch = lunar.getTimeZhi()
    total = BRANCH_INDEX[year_branch] + month_num + day_num + BRANCH_INDEX[time_branch]
    parts: dict[str, Any] = {
        "year_branch": year_branch,
        "year_branch_index": BRANCH_INDEX[year_branch],
        "lunar_month": month_num,
        "lunar_day": day_num,
        "time_branch": time_branch,
        "time_branch_index": BRANCH_INDEX[time_branch],
    }
    if ke_branch is not None:
        total += BRANCH_INDEX[ke_branch]
        parts["ke_branch"] = ke_branch
        parts["ke_branch_index"] = BRANCH_INDEX[ke_branch]
    parts["sum"] = total
    ju = total % 9 or 9
    term = yinpan_active_jieqi(lunar)
    dun_type = "阳遁" if term in YANG_TERMS else "阴遁"
    return dun_type, ju, parts


def yinpan_zhishi_palace(dun_type: str, xunshou_raw_palace: int, time_ganzhi: str, time_xun: str) -> int:
    """值使门落宫：从旬首宫按宫数阳顺阴逆数到当前时辰（含中5宫）。"""
    offset = (JIAZI.index(time_ganzhi) - JIAZI.index(time_xun)) % 60
    if dun_type == "阳遁":
        palace = (xunshou_raw_palace - 1 + offset) % 9 + 1
    else:
        palace = (xunshou_raw_palace - 1 - offset) % 9 + 1
    return palace


def build_chart_yinpan(normalized: NormalizedInput, solar: Solar, lunar: Any, pan_type: str = "shi") -> dict[str, Any]:
    warnings = list(normalized.warnings)

    if normalized.solar_dt.hour >= 23:
        warnings.append("起局时间在 23 点后（晚子时），农历日按 lunar_python 当日取值，请人工确认日数。")

    ke_info: dict[str, Any] | None = None
    if pan_type == "ke":
        ke_info = compute_ke(normalized.solar_dt, lunar.getTimeGan())
        if ke_info["minute_in_ke"] in (0, KE_MINUTES - 1):
            warnings.append("起局时间距刻界不足 1 分钟，刻柱可能差一刻，请确认精确到分的时间。")
        warnings.append("刻盘六亲移位：原月干作年干、日干作月干、时干作日干、刻干作时干（用神按移位后取）。")

    dun_type, ju_number, ju_parts = yinpan_ju(lunar, warnings, ke_branch=ke_info["ganzhi"][1] if ke_info else None)
    earth_plate = compute_earth_plate(dun_type, ju_number)

    if ke_info:
        # 刻盘：刻柱顶替时柱——旬首、旬空、值符值使、盘面时干、马星均按刻柱
        time_ganzhi = ke_info["ganzhi"]
        time_gan = time_ganzhi[0]
        time_xun = ke_info["xun"]
        time_xunkong = ke_info["xunkong"]
    else:
        time_ganzhi = lunar.getTimeInGanZhi()
        time_gan = lunar.getTimeGan()
        time_xun = lunar.getTimeXun()
        time_xunkong = lunar.getTimeXunKong()
    hidden_yi = XUNSHOU_TO_HIDDEN_YI[time_xun]
    visible_time_gan = hidden_yi if time_gan == "甲" else time_gan
    if time_gan == "甲":
        warnings.append(f"时干为甲，按旬首所遁之仪 {hidden_yi} 入盘。")

    xunshou_raw_palace = find_stem_palace(earth_plate, hidden_yi)
    time_raw_palace = find_stem_palace(earth_plate, visible_time_gan)
    xunshou_palace = hosted_palace(xunshou_raw_palace)
    time_palace = hosted_palace(time_raw_palace)
    if xunshou_raw_palace == 5 or time_raw_palace == 5:
        warnings.append("旬首或时干地盘落中宫，按中宫寄坤处理。")

    # 值符星与值使门：取旬首地盘落宫的原星原门；落中宫取天禽（寄坤按天芮转动）、死门
    if xunshou_raw_palace == 5:
        zhifu_star = "天禽"
        anchor_star = "天芮"
        zhishi_door = "死门"
    else:
        ring_idx = ROTATION_RING.index(xunshou_raw_palace)
        zhifu_star = STAR_RING[ring_idx]
        anchor_star = zhifu_star
        zhishi_door = DOOR_RING[ring_idx]

    # 天盘：星与天盘干随值符转到时干宫；坤宫地盘干与中宫寄干成对随行
    def earth_of(palace: int) -> list[str]:
        stems = [earth_plate[palace]]
        if palace == 2:
            stems.append(earth_plate[5])
        return stems

    outer_earth = [earth_of(p) for p in ROTATION_RING]
    anchor_ring_idx = ROTATION_RING.index(xunshou_palace)
    target_ring_idx = ROTATION_RING.index(time_palace)
    shift = (target_ring_idx - anchor_ring_idx) % 8
    # 星环与天盘干环整体旋转 shift 格
    star_map: dict[int, str] = {}
    sky_map: dict[int, list[str]] = {}
    for i, palace in enumerate(ROTATION_RING):
        src = (i - shift) % 8
        star_map[palace] = STAR_RING[src]
        sky_map[palace] = outer_earth[src]

    # 值使门落宫与八门（八门永远顺时针排布）
    zhishi_raw_palace = yinpan_zhishi_palace(dun_type, xunshou_raw_palace, time_ganzhi, time_xun)
    zhishi_palace = hosted_palace(zhishi_raw_palace)
    if zhishi_raw_palace == 5:
        warnings.append("值使门落中宫，按中宫寄坤处理。")
    door_map: dict[int, str] = {}
    door_start = ROTATION_RING.index(zhishi_palace)
    door_seq = rotate_to_start(DOOR_RING, zhishi_door)
    for i in range(8):
        door_map[ROTATION_RING[(door_start + i) % 8]] = door_seq[i]

    # 八神：值符落时干宫，阳遁顺时针、阴遁逆时针
    god_map: dict[int, str] = {}
    for i in range(8):
        if dun_type == "阳遁":
            palace = ROTATION_RING[(target_ring_idx + i) % 8]
        else:
            palace = ROTATION_RING[(target_ring_idx - i) % 8]
        god_map[palace] = GOD_RING_YANG[i]

    # 隐干（暗干）：地盘盘面沿环从时干宫刚性旋转到值使门宫；旋转量为 0 则为暗干伏吟，改用时干入中排法
    hidden_map: dict[int, list[str]] = {}
    hidden_shift = (ROTATION_RING.index(zhishi_palace) - ROTATION_RING.index(time_palace)) % 8
    fuyin_hidden = hidden_shift == 0
    for i, palace in enumerate(ROTATION_RING):
        src = (i - hidden_shift) % 8
        hidden_map[palace] = earth_of(ROTATION_RING[src])
    hidden_qiubian: dict[int, list[str]] | None = None
    if fuyin_hidden and ke_info and shift == 0:
        # 刻盘全盘伏吟（天盘旋转量也为 0，即刻干宫=旬首宫）：隐干按跳三宫排——
        # 隐干(宫n) = 地盘(宫n+3)，1←4←7、3←6←9、2←5←8（5 寄坤）
        warnings.append("全盘伏吟（刻干宫与旬首宫重合，天地盘相同），刻盘隐干按跳三宫排布（宫n 取宫n+3 地盘干）。")
        jump = lambda p: p + 3 if p + 3 <= 9 else p + 3 - 9
        hidden_map = {p: [earth_plate[jump(p)]] for p in ROTATION_RING}
        hidden_map[2].append(earth_plate[jump(5)])  # 中宫隐干寄坤
    elif fuyin_hidden and ke_info:
        # 仅暗干伏吟（值使门宫=刻干宫，但天盘未伏吟）：隐干与地盘重合，原样保留（实盘校准）
        warnings.append("暗干伏吟（值使门宫与刻干宫重合），隐干与地盘重合。")
    elif fuyin_hidden:
        warnings.append("暗干伏吟（值使门宫与时干宫重合），隐干与地盘重合；另附“求变入中”排法结果 hidden_qiubian。")
        seq = rotate_to_start(YINPAN_STEM_SEQ, visible_time_gan)
        walk = [1, 2, 3, 4, 6, 7, 8, 9] if dun_type == "阳遁" else [9, 8, 7, 6, 4, 3, 2, 1]
        hidden_qiubian = {5: [visible_time_gan]}
        for i, palace in enumerate(walk):
            hidden_qiubian[palace] = [seq[i + 1]]

    kongwang_branches = split_branch_pair(time_xunkong)
    kongwang_palaces = sorted({BRANCH_TO_PALACE[b] for b in kongwang_branches if b in BRANCH_TO_PALACE})
    horse_source_branch = time_ganzhi[1] if ke_info else lunar.getTimeZhi()
    horse_palace = HORSE_PALACE[horse_source_branch]
    horse_branch = HORSE_BRANCH[horse_source_branch]

    palaces: list[dict[str, Any]] = []
    for palace_no in sorted(PALACE_INFO):
        info = PALACE_INFO[palace_no]
        palaces.append({
            "palace": palace_no,
            "name": info["name"],
            "direction": info["direction"],
            "trigram": info["trigram"],
            "element": info["element"],
            "earth_stem": earth_plate.get(palace_no),
            "sky_stems": sky_map.get(palace_no),
            "hidden_stems": hidden_map.get(palace_no),
            "star": "天禽" if palace_no == 5 else star_map.get(palace_no),
            "door": None if palace_no == 5 else door_map.get(palace_no),
            "god": None if palace_no == 5 else god_map.get(palace_no),
            "is_kongwang": palace_no in kongwang_palaces,
            "has_horse": palace_no == horse_palace,
            "is_center": palace_no == 5,
            "hosts_center": palace_no == 2,
            "hosting_note": "中宫寄坤" if palace_no in {2, 5} else None,
            "changsheng": {
                "sky": changsheng_entries(sky_map.get(palace_no), palace_no),
                # 坤2 追加中宫寄坤的地盘干（与四害口径一致）
                "earth": changsheng_entries(
                    ([earth_plate.get(palace_no)] if earth_plate.get(palace_no) else [])
                    + ([earth_plate[5]] if palace_no == 2 and earth_plate.get(5) else []),
                    palace_no,
                ),
                "hidden": changsheng_entries(hidden_map.get(palace_no), palace_no),
            },
        })
    sihai_map = detect_sihai({p["palace"]: p for p in palaces})
    for entry in palaces:
        entry["sihai"] = sihai_map.get(str(entry["palace"]), [])

    return {
        "dun_type": dun_type,
        "yuan": None,
        "ju_number": ju_number,
        "ju_formula": ju_parts,
        "pan_type": pan_type,
        "ke": (
            {
                "ganzhi": ke_info["ganzhi"],
                "number": ke_info["number"],
                "xun": ke_info["xun"],
                "xunkong": ke_info["xunkong"],
                "shi_ganzhi": lunar.getTimeInGanZhi(),
            }
            if ke_info
            else None
        ),
        "xunshou": time_xun,
        "hidden_yi": hidden_yi,
        "kongwang": kongwang_branches,
        "kongwang_palaces": kongwang_palaces,
        "horse_palace": horse_palace,
        "horse_branch": horse_branch,
        "sihai": sihai_map,
        "time_stem_visible": visible_time_gan,
        "zhifu": {"star": zhifu_star, "palace": time_palace, "home_palace": xunshou_raw_palace},
        "zhishi": {"door": zhishi_door, "palace": zhishi_raw_palace, "hosted_palace": zhishi_palace},
        "fuyin_hidden": fuyin_hidden,
        "hidden_qiubian": hidden_qiubian,
        "zhuan_gong": {"present": ZHUAN_GONG_PRESENT, "absent": ZHUAN_GONG_ABSENT},
        "active_jie": yinpan_active_jieqi(lunar),
        **jieqi_window(lunar),
        "grid_order": GRID_ORDER,
        "palaces": palaces,
        "warnings": warnings,
    }


def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_input(payload)
    solar, lunar = build_solar_and_lunar(normalized)
    ruleset_id = str(payload.get("ruleset") or DEFAULT_RULESET)
    if ruleset_id in YINPAN_RULESET_ALIASES:
        ruleset_id = YINPAN_RULESET
    pan_type = str(payload.get("pan_type") or "shi").strip().lower()
    if pan_type not in {"shi", "ke"}:
        raise ValueError(f"不支持的 pan_type: {pan_type}（可选 shi / ke）")
    chart_scope = str(payload.get("chart_scope") or "event").strip().lower()
    if chart_scope not in {"event", "life"}:
        raise ValueError(f"不支持的 chart_scope: {chart_scope}（可选 event / life）")
    if chart_scope == "life":
        if ruleset_id != YINPAN_RULESET:
            raise ValueError("终身盘仅支持 daoist-yinpan 规则集")
        if pan_type != "shi":
            raise ValueError("终身盘按出生时辰起时盘，不支持刻盘")
    if ruleset_id == YINPAN_RULESET:
        chart = build_chart_yinpan(normalized, solar, lunar, pan_type=pan_type)
    else:
        if pan_type == "ke":
            raise ValueError("刻盘仅支持 daoist-yinpan 规则集")
        chart = build_chart(normalized, solar, lunar)
    if chart_scope == "life":
        chart["life"] = build_life_block(chart, lunar, payload, chart["warnings"])

    return {
        "normalized_input": {
            "question_type": normalized.question_type,
            "question_goal": normalized.question_goal,
            "calendar_type": normalized.calendar_type,
            "ruleset": ruleset_id,
            "pan_type": pan_type,
            "chart_scope": chart_scope,
            "timezone": normalized.timezone,
            "country": normalized.country,
            "city": normalized.city,
            "used_now": normalized.use_now,
            "original_time_input": normalized.original_time_input,
        },
        "calendar": {
            "solar": {
                "ymd_hms": solar.toYmdHms(),
                "timezone": normalized.timezone,
            },
            "lunar": {
                "year": lunar.getYear(),
                "month": abs(lunar.getMonth()),
                "day": lunar.getDay(),
                "month_text": lunar.getMonthInChinese(),
                "day_text": lunar.getDayInChinese(),
                "is_leap_month": lunar.getMonth() < 0,
            },
            "jieqi": {
                "active_jie": chart["active_jie"],
                "active_jie_started_at": chart["active_jie_started_at"],
                "next_jie": chart["next_jie"],
                "next_jie_at": chart["next_jie_at"],
                "yuejiang": chart.get("yuejiang"),
                "yuejiang_qi": chart.get("yuejiang_qi"),
            },
        },
        "ganzhi": {
            "year": lunar.getYearInGanZhiExact(),
            "month": lunar.getMonthInGanZhiExact(),
            "day": lunar.getDayInGanZhiExact(),
            "time": lunar.getTimeInGanZhi(),
            "day_xun_exact": lunar.getDayXunExact(),
            "day_xunkong_exact": lunar.getDayXunKongExact(),
            "time_xun": lunar.getTimeXun(),
            "time_xunkong": lunar.getTimeXunKong(),
        },
        "ruleset": (
            {
                "id": ruleset_id,
                "name": "道家阴盘奇门",
                "timezone_default": "北京时间（Asia/Shanghai）",
                "dun_type_rule": "冬至后夏至前为阳遁，夏至后冬至前为阴遁。",
                "ju_rule": (
                    "刻盘局数 =（年支序 + 农历月 + 农历日 + 时支序 + 刻支序）% 9，余 0 取 9。"
                    if pan_type == "ke"
                    else "局数 =（年支序 + 农历月 + 农历日 + 时支序）% 9，余 0 取 9。"
                ),
                "ke_rule": (
                    "一时辰十二刻、每刻 10 分钟；刻干支从时干五鼠遁起子刻，沿六十甲子顺排；"
                    "旬首、旬空、值符值使、马星均按刻柱；暗干伏吟时隐干跳三宫；"
                    "六亲移位：月干作年干、日干作月干、时干作日干、刻干作时干。"
                    if pan_type == "ke"
                    else None
                ),
                "zhishi_rule": "值使门从旬首宫按宫数阳顺阴逆数至当前时辰（含中5宫）。",
                "hidden_stem_rule": "隐干为地盘沿八宫环从时干宫刚性旋转至值使门宫；重合时暗干伏吟，时干入中、阳顺阴逆排。",
                "center_hosting_rule": "中宫相关判断一律寄坤处理。",
            }
            if ruleset_id == YINPAN_RULESET
            else {
                "id": ruleset_id,
                "name": "时家转盘奇门（大陆默认）",
                "timezone_default": "北京时间（Asia/Shanghai）",
                "dun_type_rule": "冬至到芒种用阳遁，夏至到大雪用阴遁，按当前节令判定。",
                "yuan_rule": "按日干支所在六十甲子序列，每 5 日一元，循环上元/中元/下元。",
                "ju_rule": "按当前节令和三元，从固定定局表取局数。",
                "center_hosting_rule": "中宫相关判断一律寄坤处理。",
            }
        ),
        "chart": {
            key: chart[key]
            for key in chart
            if key not in {"active_jie", "active_jie_started_at", "next_jie", "next_jie_at", "yuejiang", "yuejiang_qi", "warnings"}
        },
        "warnings": chart["warnings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a structured qimen dunjia chart payload.")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
        output = build_output(payload)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        error_payload = {"error": str(exc)}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(error_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
