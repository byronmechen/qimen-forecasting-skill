# forecasting — 道家阴盘奇门排盘与解盘 Skill

一个 [Claude Code](https://claude.com/claude-code) skill：结构化访谈 → 脚本完成排盘固定计算 → 按参考文档解读并展示九宫格盘面。默认规则集为道家阴盘奇门（`daoist-yinpan`）。

## 功能

**排盘（脚本固定计算，`scripts/qimen_cli.py`）**

- **时盘（测事盘）**：数字公式定局（年支序+农历月+农历日+时支序，%9），冬至/夏至分阳阴遁；地盘、天盘（值符随时干转，坤宫双干）、九星、八门（值使飞宫后顺时针布）、八神、**隐干（暗干）**、空亡宫、马星；暗干伏吟时另出"求变入中"盘。
- **刻盘（刻家）**：`pan_type: "ke"`。一时辰十二刻、每刻 10 分钟，刻柱五鼠遁起子刻；旬首、旬空、值符值使、马星均按刻柱，六亲移位（月作年、日作月、时作日、刻作时）；刻盘暗干伏吟按"跳三宫"取隐干。适合同一时辰内多次占测。
- **终身盘（奇门命理盘）**：`chart_scope: "life"`。按出生时刻起盘，输出四柱每柱入盘干及落宫、**四害**（门迫＞击刑＞入墓＞空亡，逐宫带干与天/地盘层）、月令旺衰、流年太岁落宫；提供性别则排**大运**（八字式：阳男阴女顺、阴男阳女逆，3 日折 1 年，含干支十神）。
- **历法处理**：公历/农历输入、闰月、早晚子时提示、中国夏令时（1986–1991）自动折算、时区（含"北京"别名）、立春/正月初一换年边界 warning。

**解读（skill 文档驱动，`SKILL.md` + `references/`）**

- 排盘前结构化访谈（`references/interview.md`）；解盘方法与取用神（`yinpan-jiepan.md`）；意象辞典（`yinpan-yixiang.md`）；断病参考（`yinpan-duanbing.md`，仅传统术数视角、必附就医提示）；奇门风水与调理（`yinpan-fengshui.md`）；择时选日与应期（`yinpan-zeri.md`）；终身盘解读（`yinpan-zhongshen.md`）。
- 盘面以九宫格 markdown 展示：上方四柱，宫内神/星/门/天地盘干/隐干，空亡宫标 ◎，四害用彩色圆点行（🔴门迫 🟡入墓 🟣击刑 🔵刑墓），终身盘下方附大运表。

## 安装

```bash
git clone https://github.com/ssyan3868-bot/qimen-forecasting-skill.git ~/.claude/skills/forecasting
```

依赖已 vendor 进 `scripts/vendor/`（无需 pip install 即可运行）；也可 `pip install -r scripts/requirements.txt` 使用系统安装版。

## 使用说明

### 方式一：作为 Claude Code skill（推荐）

安装后在 Claude Code 里直接说"帮我测一下……"、"奇门排盘"、"用奇门看看某事"、"排个终身盘"即可触发。流程：Claude 先做简短访谈（问事、时间、城市、想判断什么），再调脚本排盘，最后展示九宫格并解读。

### 方式二：单独调用排盘脚本

输入输出均为 JSON 文件：

```bash
python3 scripts/qimen_cli.py --input in.json --output out.json
```

`in.json` 示例（时盘）：

```json
{
  "question_type": "事业",
  "question_goal": "项目能否谈成",
  "time_input": "2026-07-12 15:30",
  "calendar_type": "solar",
  "location": {"country": "中国", "city": "北京", "timezone": "Asia/Shanghai"},
  "ruleset": "daoist-yinpan",
  "pan_type": "shi"
}
```

常用输入字段：

| 字段 | 说明 |
|------|------|
| `time_input` | `YYYY-MM-DD HH:MM`，占测时间或出生时间 |
| `calendar_type` | `solar` 公历 / `lunar` 农历 |
| `pan_type` | `shi` 时盘（默认）/ `ke` 刻盘 |
| `chart_scope` | 填 `life` 排终身盘（仅时盘） |
| `gender` | `male`/`female`，终身盘排大运用，缺省不排 |
| `liunian_years` | 数组，终身盘要看的流年年份 |
| `location.timezone` | IANA 时区；留空按国家/城市推断，支持"北京"别名 |

输出要点（`out.json`）：

| 字段 | 含义 |
|------|------|
| `ganzhi` | 四柱干支 |
| `chart.dun_type` / `ju_number` / `ju_formula` | 阴阳遁、局数、定局公式分量 |
| `chart.palaces[]` | 逐宫：神、星、门、天盘干（`sky_stems`）、地盘干、隐干（`hidden_stems`）、空亡/马星标记、四害（`sihai`） |
| `chart.zhifu` / `zhishi` | 值符星、值使门及落宫 |
| `chart.kongwang_palaces` / `horse_palace` | 空亡宫、马星落宫 |
| `chart.zhuan_gong` | 空亡转宫表 |
| `chart.fuyin_hidden` / `hidden_qiubian` | 暗干伏吟标记、求变入中盘 |
| `chart.ke` | 刻盘：刻柱、第几刻、刻旬首、刻旬空、原时柱 |
| `chart.life` | 终身盘：四柱落宫、四害、旺衰、大运（`dayun`）、流年（`liunian`） |
| `warnings` | 闰月、晚子时、夏令时折算、换年边界等提示 |

### 验证

```bash
python3 scripts/test_yinpan.py
```

回归测试对排盘做全宫位断言（定局、星门神布局、隐干、伏吟、刻盘、终身盘大运各分支）；测试用生日均为合成数据。

## 免责声明

- 本项目内容属传统术数文化研究与技术实现，不构成任何医疗、法律、投资或其他专业建议。
- 涉及健康的解读仅为传统术数视角的参考性观察，请以医院检查和医生意见为准。
- 排盘规则整理自公开流传的传统奇门遁甲体系知识，文字为本仓库独立撰写。

## 第三方代码

`scripts/vendor/lunar_python/` 来自 [6tail/lunar-python](https://github.com/6tail/lunar-python)（MIT License，版权归原作者），许可证见该目录下 LICENSE。

## License

MIT（见 [LICENSE](LICENSE)）。
