#!/usr/bin/env python3
"""用实盘例题验证 daoist-yinpan 排盘。"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CLI = Path(__file__).resolve().parent / "qimen_cli.py"
TMP = Path(tempfile.mkdtemp())

def run(time_input, pan_type="shi"):
    payload = {
        "question_type": "test", "question_goal": "test",
        "time_input": time_input, "calendar_type": "solar",
        "location": {"country": "中国", "city": "北京", "timezone": "Asia/Shanghai"},
        "ruleset": "daoist-yinpan", "pan_type": pan_type,
    }
    inp, outp = TMP / "in.json", TMP / "out.json"
    inp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(CLI), "--input", str(inp), "--output", str(outp)])
    data = json.loads(outp.read_text(encoding="utf-8"))
    if "error" in data:
        raise RuntimeError(data["error"])
    return data

FAIL = []

def check(label, actual, expected):
    ok = actual == expected
    if not ok:
        FAIL.append(f"{label}: got {actual!r}, want {expected!r}")
    print(("PASS" if ok else "FAIL"), label, "" if ok else f"got={actual!r} want={expected!r}")

def palaces_by_no(data):
    return {p["palace"]: p for p in data["chart"]["palaces"]}

# ---- T1 教科书阳7局：2006-5-23 19:45 ----
d = run("2006-05-23 19:45")
c = d["chart"]
check("T1 dun", c["dun_type"], "阳遁")
check("T1 ju", c["ju_number"], 7)
check("T1 时柱", d["ganzhi"]["time"], "庚戌")
check("T1 旬首", c["xunshou"], "甲辰")
check("T1 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天芮", 9))
check("T1 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("死门", 8))
check("T1 空亡宫", c["kongwang_palaces"], [3, 8])
check("T1 马星", c["horse_palace"], 2)
P = palaces_by_no(d)
exp = {
    4: ("庚", "天英", "开门", "九天"), 9: ("壬丙", "天芮", "休门", "值符"),
    2: ("戊", "天柱", "生门", "螣蛇"), 3: ("丁", "天辅", "惊门", "九地"),
    7: ("乙", "天心", "伤门", "太阴"), 8: ("癸", "天冲", "死门", "玄武"),
    1: ("己", "天任", "景门", "白虎"), 6: ("辛", "天蓬", "杜门", "六合"),
}
for pal, (sky, star, door, god) in exp.items():
    check(f"T1 宫{pal}", ("".join(P[pal]["sky_stems"]), P[pal]["star"], P[pal]["door"], P[pal]["god"]), (sky, star, door, god))

# ---- T2 例题 X先生：2009-4-13 9:39 阳2局 ----
d = run("2009-04-13 09:39")
c = d["chart"]
check("T2 dun/ju", (c["dun_type"], c["ju_number"]), ("阳遁", 2))
check("T2 四柱", (d["ganzhi"]["year"], d["ganzhi"]["month"], d["ganzhi"]["day"], d["ganzhi"]["time"]), ("己丑", "戊辰", "戊子", "丁巳"))
check("T2 旬首", c["xunshou"], "甲寅")
check("T2 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天柱", 8))
check("T2 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("惊门", 1))
check("T2 空亡宫", c["kongwang_palaces"], [1, 8])
check("T2 马星", c["horse_palace"], 6)
P = palaces_by_no(d)
exp_star_door_god = {
    4: ("乙", "天蓬", "生门", "太阴"), 9: ("丁", "天任", "伤门", "六合"),
    2: ("己", "天冲", "杜门", "白虎"), 3: ("壬", "天心", "休门", "螣蛇"),
    7: ("庚", "天辅", "景门", "玄武"), 8: ("癸", "天柱", "开门", "值符"),
    1: ("戊辛", "天芮", "惊门", "九天"), 6: ("丙", "天英", "死门", "九地"),
}
for pal, (sky, star, door, god) in exp_star_door_god.items():
    check(f"T2 宫{pal}", ("".join(P[pal]["sky_stems"]), P[pal]["star"], P[pal]["door"], P[pal]["god"]), (sky, star, door, god))
exp_hidden = {1: "丁", 8: "己", 3: "庚", 4: "丙", 9: "戊辛", 2: "癸", 7: "壬", 6: "乙"}
for pal, hid in exp_hidden.items():
    check(f"T2 隐干宫{pal}", "".join(P[pal]["hidden_stems"]), hid)

# ---- T3 阴五局：2005-12-5 10:59 ----
d = run("2005-12-05 10:59")
c = d["chart"]
check("T3 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 5))
check("T3 旬首", c["xunshou"], "甲寅")
check("T3 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天英", 8))
check("T3 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("景门", 6))

# ---- T4 暗干伏吟：2005-12-5 12:05 阴六局 ----
d = run("2005-12-05 12:05")
c = d["chart"]
check("T4 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 6))
check("T4 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天蓬", 6))
check("T4 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("休门", 6))
check("T4 伏吟", c["fuyin_hidden"], True)
qb = {int(k): "".join(v) for k, v in c["hidden_qiubian"].items()}
check("T4 求变入中", qb, {5: "戊", 9: "己", 8: "庚", 7: "辛", 6: "壬", 4: "癸", 3: "丁", 2: "丙", 1: "乙"})

# ---- T5 2011-5-3 20:05 阳2局（投资局例题）----
d = run("2011-05-03 20:05")
c = d["chart"]
check("T5 dun/ju", (c["dun_type"], c["ju_number"]), ("阳遁", 2))
check("T5 四柱", (d["ganzhi"]["year"], d["ganzhi"]["month"], d["ganzhi"]["day"], d["ganzhi"]["time"]), ("辛卯", "壬辰", "戊午", "壬戌"))
check("T5 值符/值使", (c["zhifu"]["star"], c["zhishi"]["door"]), ("天柱", "惊门"))
check("T5 空亡宫", c["kongwang_palaces"], [1, 8])
P = palaces_by_no(d)
exp_hidden5 = {4: "庚", 9: "丙", 2: "戊辛", 3: "己", 8: "丁", 1: "乙", 7: "癸", 6: "壬"}
for pal, hid in exp_hidden5.items():
    check(f"T5 隐干宫{pal}", "".join(P[pal]["hidden_stems"]), hid)

# ---- T6 阴七局 禽星值符：2005-11-18 9:50 ----
d = run("2005-11-18 09:50")
c = d["chart"]
check("T6 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 7))
check("T6 旬首", c["xunshou"], "甲申")
check("T6 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天禽", 2))
check("T6 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("死门", 5))
check("T6 空亡宫", c["kongwang_palaces"], [2, 9])

# ================= 刻盘 =================

# ---- KA1 校准用app实盘：2026-07-13 19:26 刻盘阴遁1局（全宫位校准）----
d = run("2026-07-13 19:26", pan_type="ke")
c = d["chart"]
check("KA1 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 1))
check("KA1 刻柱", (c["ke"]["ganzhi"], c["ke"]["number"]), ("壬寅", 3))
check("KA1 时柱", c["ke"]["shi_ganzhi"], "壬戌")
check("KA1 旬首", c["xunshou"], "甲午")
check("KA1 空亡宫", c["kongwang_palaces"], [4])
check("KA1 马星", c["horse_palace"], 2)
check("KA1 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天柱", 6))
check("KA1 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("惊门", 8))
P = palaces_by_no(d)
exp_ka1 = {
    4: ("丙", "天冲", "休门", "白虎", "庚"), 9: ("丁", "天辅", "生门", "六合", "丙"),
    2: ("己", "天英", "伤门", "太阴", "丁"), 3: ("庚", "天任", "开门", "玄武", "戊"),
    7: ("乙癸", "天芮", "杜门", "螣蛇", "己"), 6: ("辛", "天柱", "景门", "值符", "乙癸"),
    8: ("戊", "天蓬", "惊门", "九地", "壬"), 1: ("壬", "天心", "死门", "九天", "辛"),
}
for pal, (sky, star, door, god, hid) in exp_ka1.items():
    check(f"KA1 宫{pal}", ("".join(P[pal]["sky_stems"]), P[pal]["star"], P[pal]["door"], P[pal]["god"], "".join(P[pal]["hidden_stems"])), (sky, star, door, god, hid))

# ---- KA2 校准用app实盘：2026-07-14 19:03 刻盘阴遁8局（暗干伏吟，隐干跳三宫）----
d = run("2026-07-14 19:03", pan_type="ke")
c = d["chart"]
check("KA2 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 8))
check("KA2 刻柱", (c["ke"]["ganzhi"], c["ke"]["number"]), ("甲子", 1))
check("KA2 时柱", c["ke"]["shi_ganzhi"], "甲戌")
check("KA2 旬首", c["xunshou"], "甲子")
check("KA2 空亡宫", c["kongwang_palaces"], [6])
check("KA2 马星", c["horse_palace"], 8)
check("KA2 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天任", 8))
check("KA2 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("生门", 8))
check("KA2 伏吟", c["fuyin_hidden"], True)
P = palaces_by_no(d)
exp_ka2 = {
    4: ("壬", "天辅", "杜门", "九地", "己"), 9: ("乙", "天英", "景门", "玄武", "癸"),
    2: ("丁辛", "天芮", "死门", "白虎", "辛戊"), 3: ("癸", "天冲", "伤门", "九天", "庚"),
    7: ("己", "天柱", "惊门", "六合", "丙"), 6: ("庚", "天心", "开门", "太阴", "乙"),
    8: ("戊", "天任", "生门", "值符", "丁"), 1: ("丙", "天蓬", "休门", "螣蛇", "壬"),
}
for pal, (sky, star, door, god, hid) in exp_ka2.items():
    check(f"KA2 宫{pal}", ("".join(P[pal]["sky_stems"]), P[pal]["star"], P[pal]["door"], P[pal]["god"], "".join(P[pal]["hidden_stems"])), (sky, star, door, god, hid))

# ---- KA3 校准用app实盘：2026-07-15 14:45 刻盘阴遁7局（仅暗干伏吟、天盘未伏吟 → 隐干与地盘重合，不跳三宫）----
d = run("2026-07-15 14:45", pan_type="ke")
c = d["chart"]
check("KA3 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 7))
check("KA3 刻柱", (c["ke"]["ganzhi"], c["ke"]["number"]), ("壬戌", 11))
check("KA3 旬首", c["xunshou"], "甲寅")
check("KA3 空亡宫", c["kongwang_palaces"], [1, 8])
check("KA3 马星", c["horse_palace"], 2)
check("KA3 值符", (c["zhifu"]["star"], c["zhifu"]["palace"]), ("天芮", 3))
check("KA3 值使", (c["zhishi"]["door"], c["zhishi"]["palace"]), ("死门", 3))
check("KA3 伏吟", c["fuyin_hidden"], True)
P = palaces_by_no(d)
exp_ka3 = {
    4: ("戊", "天柱", "惊门", "九天", "辛"), 9: ("己", "天心", "开门", "九地", "丙"),
    2: ("丁", "天蓬", "休门", "玄武", "癸庚"), 3: ("癸庚", "天芮", "死门", "值符", "壬"),
    7: ("乙", "天任", "生门", "白虎", "戊"), 6: ("壬", "天冲", "伤门", "六合", "己"),
    8: ("丙", "天英", "景门", "螣蛇", "乙"), 1: ("辛", "天辅", "杜门", "太阴", "丁"),
}
for pal, (sky, star, door, god, hid) in exp_ka3.items():
    check(f"KA3 宫{pal}", ("".join(P[pal]["sky_stems"]), P[pal]["star"], P[pal]["door"], P[pal]["god"], "".join(P[pal]["hidden_stems"])), (sky, star, door, god, hid))

# ---- 刻盘：例题书实盘 6 例（无伏吟例）----
def check_ke(label, time_input, ju, ke_gz, ke_no, xunshou, kong_palaces, zhifu_star, zhishi_door):
    d = run(time_input, pan_type="ke")
    c = d["chart"]
    check(f"{label} dun/ju", (c["dun_type"], c["ju_number"]), ("阳遁", ju))
    check(f"{label} 刻柱", (c["ke"]["ganzhi"], c["ke"]["number"]), (ke_gz, ke_no))
    check(f"{label} 旬首", c["xunshou"], xunshou)
    check(f"{label} 空亡宫", c["kongwang_palaces"], kong_palaces)
    check(f"{label} 值符/值使", (c["zhifu"]["star"], c["zhishi"]["door"]), (zhifu_star, zhishi_door))

check_ke("K1", "2009-04-07 19:43", 6, "庚辰", 5, "甲戌", [2, 7], "天柱", "惊门")
check_ke("K2", "2010-06-05 16:40", 5, "戊戌", 11, "甲午", [4], "天任", "生门")
check_ke("K3", "2009-03-26 11:30", 9, "癸卯", 4, "甲午", [4], "天冲", "伤门")
check_ke("K4", "2009-04-15 09:42", 9, "壬辰", 5, "甲申", [2, 9], "天芮", "死门")
check_ke("K5", "2011-01-04 09:30", 8, "丁卯", 4, "甲子", [6], "天任", "生门")
check_ke("K6", "2009-04-17 10:42", 8, "丙戌", 11, "甲申", [2, 9], "天蓬", "休门")

# ---- L1 终身盘（chart_scope=life）自洽性：1990-08-15 14:30 阴1局 ----
def run_life(time_input, **extra):
    payload = {
        "question_type": "终身盘", "question_goal": "test",
        "time_input": time_input, "calendar_type": "solar",
        "location": {"country": "中国", "city": "北京", "timezone": "Asia/Shanghai"},
        "ruleset": "daoist-yinpan", "pan_type": "shi", "chart_scope": "life",
    }
    payload.update(extra)
    inp, outp = TMP / "in.json", TMP / "out.json"
    inp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    subprocess.run([sys.executable, str(CLI), "--input", str(inp), "--output", str(outp)])
    data = json.loads(outp.read_text(encoding="utf-8"))
    if "error" in data:
        raise RuntimeError(data["error"])
    return data

d = run_life("1990-08-15 14:30", gender="female", liunian_years=[2026, 2027, 2028])
c = d["chart"]
life = c["life"]
check("L1 scope", d["normalized_input"]["chart_scope"], "life")
check("L1 dun/ju", (c["dun_type"], c["ju_number"]), ("阴遁", 1))
check("L1 四柱", tuple(life["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "time")),
      ("庚午", "甲申", "壬子", "丁未"))
check("L1 月干甲遁庚", life["pillars"]["month"]["stem_visible"], "庚")
P = palaces_by_no(d)
for key in ("year", "month", "day", "time"):
    pil = life["pillars"][key]
    ok = all(pil["stem_visible"] in P[n]["sky_stems"] for n in pil["sky_palaces"])
    check(f"L1 {key}干天盘落宫自洽", ok, True)
check("L1 日干天盘落巽", life["pillars"]["day"]["sky_palaces"], [4])
check("L1 巽宫击刑入墓", sorted(h["type"] for h in life["sihai"]["4"]), ["入墓", "击刑"])
check("L1 空亡入四害", all(str(n) in life["sihai"] and any(h["type"] == "空亡" for h in life["sihai"][str(n)])
                          for n in c["kongwang_palaces"]), True)
check("L1 月令", (life["wangshuai"]["season"], life["wangshuai"]["ling_element"]), ("秋", "金"))
check("L1 兑宫金旺", life["wangshuai"]["palace_states"]["7"]["state"], "旺")
check("L1 流年酉年看酉宫", [(x["ganzhi"], x["palace"]) for x in life["liunian"]],
      [("丙午", 9), ("丁未", 2), ("戊申", 2)])

# 测事盘也输出逐宫四害；时区别名"北京"可识别
d = run("2006-05-23 19:45")
P = palaces_by_no(d)
check("S1 测事盘宫有sihai字段", all("sihai" in p for p in d["chart"]["palaces"]), True)
check("S1 chart.sihai与宫内一致", d["chart"]["sihai"], {str(n): p["sihai"] for n, p in P.items() if p["sihai"]})
check("S1 空亡宫入sihai", all(any(h["type"] == "空亡" for h in P[n]["sihai"]) for n in d["chart"]["kongwang_palaces"]), True)

payload_bj = {
    "question_type": "test", "question_goal": "test",
    "time_input": "2006-05-23 19:45", "calendar_type": "solar",
    "location": {"country": "中国", "city": "北京", "timezone": "北京"},
    "ruleset": "daoist-yinpan", "pan_type": "shi",
}
inp, outp = TMP / "in.json", TMP / "out.json"
inp.write_text(json.dumps(payload_bj, ensure_ascii=False), encoding="utf-8")
subprocess.run([sys.executable, str(CLI), "--input", str(inp), "--output", str(outp)])
d = json.loads(outp.read_text(encoding="utf-8"))
check("S2 时区别名北京", (d["normalized_input"]["timezone"], d["chart"]["ju_number"]), ("Asia/Shanghai", 7))

# ---- L2 终身盘四害回归（合成生日）：1993-02-20 16:20 阳遁4局 ----
# 巽4壬刑+墓（天盘）、艮8庚刑+墓（天盘）+空亡、坤2己击刑（地盘）、乾6丙入墓（天盘）
d = run_life("1993-02-20 16:20")
c = d["chart"]
check("L2 dun/ju", (c["dun_type"], c["ju_number"]), ("阳遁", 4))
check("L2 空亡宫", c["kongwang_palaces"], [3, 8])
sh = c["life"]["sihai"]
check("L2 巽4壬刑墓", sorted((h["type"], h.get("stem"), h.get("layer")) for h in sh["4"]),
      [("入墓", "壬", "天盘"), ("击刑", "壬", "天盘")])
check("L2 坤2己击刑", [(h["type"], h.get("stem"), h.get("layer")) for h in sh["2"]],
      [("击刑", "己", "地盘")])
check("L2 艮8庚刑墓空", sorted((h["type"], h.get("stem"), h.get("layer")) for h in sh["8"]),
      [("入墓", "庚", "天盘"), ("击刑", "庚", "天盘"), ("空亡", None, None)])
check("L2 乾6丙入墓", [(h["type"], h.get("stem"), h.get("layer")) for h in sh["6"]],
      [("入墓", "丙", "天盘")])
check("L2 中宫不单列", "5" in sh, False)
check("L2 宫内与chart.sihai一致", c["sihai"], sh)

# 大运：癸酉阴年女顺排、顺数至惊蛰起运4岁
d = run_life("1993-02-20 16:20", gender="female")
dy = d["chart"]["life"]["dayun"]
check("L2 大运方向", (dy["direction"], dy["counted_to_jie"], dy["qiyun_age"]), ("顺排", "惊蛰", 4))
check("L2 大运列表", [(e["start_year"], e["ganzhi"], e["shishen"]) for e in dy["list"]],
      [(1993, "甲寅", "食食"), (1997, "乙卯", "伤伤"), (2007, "丙辰", "才杀"),
       (2017, "丁巳", "财才"), (2027, "戊午", "杀财"), (2037, "己未", "官官"),
       (2047, "庚申", "枭枭"), (2057, "辛酉", "印印"), (2067, "壬戌", "比杀"),
       (2077, "癸亥", "劫比")])
check("L2 无性别不排大运", run_life("1993-02-20 16:20")["chart"]["life"]["dayun"], None)

# ---- V1-V5 终身盘分支回归（合成生日，覆盖大运顺逆/早子时/立春界/夏令时/闰月）----
def check_life(label, time_input, gender, sizhu, dun, ju, xunshou, zhifu_star, zhishi_door,
               kong, horse, dy_dir, dy_head):
    d = run_life(time_input, gender=gender)
    c = d["chart"]
    g = d["ganzhi"]
    check(f"{label} 四柱", (g["year"], g["month"], g["day"], g["time"]), sizhu)
    check(f"{label} dun/ju", (c["dun_type"], c["ju_number"]), (dun, ju))
    check(f"{label} 旬首", c["xunshou"], xunshou)
    check(f"{label} 值符/值使", (c["zhifu"]["star"], c["zhishi"]["door"]), (zhifu_star, zhishi_door))
    check(f"{label} 空亡宫", c["kongwang_palaces"], kong)
    check(f"{label} 马星", c["horse_palace"], horse)
    dy = c["life"]["dayun"]
    check(f"{label} 大运向", dy["direction"], dy_dir)
    check(f"{label} 大运头四段", [(e["start_year"], e["ganzhi"], e["shishen"]) for e in dy["list"][:4]], dy_head)

# V1 早子时+阳年女逆排（兼验甲辰柱遁仪）：1992-04-10 00:30
check_life("V1", "1992-04-10 00:30", "female",
           ("壬申", "甲辰", "丙辰", "戊子"), "阳遁", 3, "甲申", "天禽", "死门", [2, 9], 8, "逆排",
           [(1992, "甲辰", "枭食"), (1993, "癸卯", "官印"), (2003, "壬寅", "杀枭"), (2013, "辛丑", "财伤")])

# V2 立春前出生（年柱归上年甲戌，起运前段年份标签用干支年）：1995-01-25 08:05
check_life("V2", "1995-01-25 08:05", "female",
           ("甲戌", "丁丑", "丙辰", "壬辰"), "阳遁", 8, "甲申", "天蓬", "休门", [2, 9], 8, "逆排",
           [(1994, "丁丑", "劫伤"), (2001, "丙子", "比官"), (2011, "乙亥", "印杀"), (2021, "甲戌", "枭食")])

# V3 夏令时+阳年男顺排：1988-07-15 23:10（墙钟）→ 标准时 22:10 亥时
check_life("V3", "1988-07-15 23:10", "male",
           ("戊辰", "己未", "辛未", "己亥"), "阴遁", 7, "甲午", "天辅", "杜门", [4], 4, "顺排",
           [(1988, "己未", "枭枭"), (1995, "庚申", "劫劫"), (2005, "辛酉", "比比"), (2015, "壬戌", "伤印")])

# V4 阴年女顺排+闰月定局：1993-05-20 02:45（1993 闰三月）
check_life("V4", "1993-05-20 02:45", "female",
           ("癸酉", "丁巳", "辛丑", "己丑"), "阳遁", 8, "甲申", "天蓬", "休门", [2, 9], 6, "顺排",
           [(1993, "丁巳", "杀官"), (1998, "戊午", "印杀"), (2008, "己未", "枭枭"), (2018, "庚申", "劫劫")])

# V5 阴年男逆排：1995-10-08 06:00
check_life("V5", "1995-10-08 06:00", "male",
           ("乙亥", "乙酉", "壬申", "癸卯"), "阴遁", 2, "甲午", "天任", "生门", [4], 4, "逆排",
           [(1995, "乙酉", "伤印"), (2005, "甲申", "食枭"), (2015, "癸未", "劫官"), (2025, "壬午", "比财")])
d = run_life("1995-10-08 06:00", gender="male")
check("V5 大运尾段", [(e["start_year"], e["ganzhi"], e["shishen"]) for e in d["chart"]["life"]["dayun"]["list"][4:]],
      [(2035, "辛巳", "印才"), (2045, "庚辰", "枭杀"), (2055, "己卯", "官伤"),
       (2065, "戊寅", "杀食"), (2075, "丁丑", "财官"), (2085, "丙子", "才劫")])

# life 与刻盘互斥
try:
    run_life("1990-08-15 14:30", pan_type="ke")
    check("L1 life+ke 拒绝", "no error", "error")
except RuntimeError:
    check("L1 life+ke 拒绝", "error", "error")

print()
if FAIL:
    print(f"{len(FAIL)} FAILURES")
    sys.exit(1)
print("ALL PASS")
