# forecasting — 道家阴盘奇门排盘与解盘 Skill

一个 [Claude Code](https://claude.com/claude-code) skill：结构化访谈 → 脚本完成排盘固定计算 → 按参考文档解读并展示九宫格盘面。默认规则集为道家阴盘奇门（`daoist-yinpan`），支持时盘、刻盘（`pan_type: "ke"`）与终身盘（`chart_scope: "life"`，含大运、流年、四害）。

## 安装

```bash
git clone https://github.com/ssyan3868-bot/qimen-forecasting-skill.git ~/.claude/skills/forecasting
```

依赖已 vendor 进 `scripts/vendor/`（无需 pip install 即可运行）；也可 `pip install -r scripts/requirements.txt` 使用系统安装版。

## 结构

- `SKILL.md`：技能主文档（访谈流程、脚本调用、盘面展示与解读规范）
- `references/`：规则集、解盘方法、意象、断病参考、风水、择时、终身盘、访谈问题库
- `scripts/qimen_cli.py`：排盘计算脚本（输入/输出均为 JSON）
- `scripts/test_yinpan.py`：回归测试（排盘全宫位断言，测试用生日均为合成数据）

## 验证

```bash
python3 scripts/test_yinpan.py
```

## 免责声明

- 本项目内容属传统术数文化研究与技术实现，不构成任何医疗、法律、投资或其他专业建议。
- 涉及健康的解读仅为传统术数视角的参考性观察，请以医院检查和医生意见为准。
- 排盘规则整理自公开流传的传统奇门遁甲体系知识，文字为本仓库独立撰写。

## 第三方代码

`scripts/vendor/lunar_python/` 来自 [6tail/lunar-python](https://github.com/6tail/lunar-python)（MIT License，版权归原作者），许可证见该目录下 LICENSE。

## License

MIT（见 [LICENSE](LICENSE)）。
