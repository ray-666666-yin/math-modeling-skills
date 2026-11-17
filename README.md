# 数学建模 Skills｜国二选手自用

把备赛、比赛和赛后复盘中的工作方法，整理成能跨项目复用的 AI 技能。

从模型选型、创新验证，到 MATLAB 绘图、流程图和论文整理，再到模型交接与结果追溯。本仓库分享个人实践，欢迎参考、反馈和持续改进。获奖经历是项目背景；具体任务仍需要核验假设、计算和论证。

## 技能清单

| 技能 | 适合什么时候用 |
| --- | --- |
| [mcm-model-selection](skills/mcm-model-selection/SKILL.md) | 根据问题结构和数据条件选择模型，比较备选与失效条件 |
| [mcm-model-innovation](skills/mcm-model-innovation/SKILL.md) | 找到瓶颈，设计有依据的改进、基线和消融 |
| [mcm-model-summary](skills/mcm-model-summary/SKILL.md) | 从已有推导提取核心公式，整理模型总结 |
| [matlab-paper-plotting](skills/matlab-paper-plotting/SKILL.md) | 生成论文图表及可编辑文件 |
| [mcm-paper-flowcharts](skills/mcm-paper-flowcharts/SKILL.md) | 整理技术路线，生成可编辑 draw.io 图 |
| [mcm-word-to-latex](skills/mcm-word-to-latex/SKILL.md) | 将队伍 Word 稿转入已有 LaTeX 模板并核对内容 |
| [mcm-model-handoff](skills/mcm-model-handoff/SKILL.md) | 跨队员、跨聊天交接模型版本与变更影响 |
| [mcm-result-lineage](skills/mcm-result-lineage/SKILL.md) | 对齐原始结果、图表、正文和附件 |

前六项整理自备赛与比赛期间的个人技能；后两项是在赛后复盘中补充的协作方法。公开版已重写为通用说明，并配有合成示例。

## 全局安装

需要 Python 3.10+。下载本仓库后，在仓库根目录执行：

```sh
python scripts/install.py --dry-run
python scripts/install.py
```

默认安装到 `CODEX_HOME/skills`（已设置时），否则为 `~/.codex/skills`，供不同项目使用。安装完成后重新打开 Codex 会话以加载技能。

只安装部分技能：

```sh
python scripts/install.py --skill mcm-model-handoff mcm-result-lineage
```

安装器替换同名技能前会备份完整旧目录，其他技能保持原有配置。已有本地修改也会进入备份；具体恢复方法见 [维护说明](CONTRIBUTING.md)。

## 使用示例

在任务中明确调用技能，并提供当前题面、材料和工作范围：

```text
使用 $mcm-model-selection，结合题面和附件，逐问比较首选与备选模型。
使用 $mcm-model-handoff，整理当前采用模型、未决分支和需要同步的产物。
使用 $mcm-result-lineage，核对结果表、正文和附件的数值来源与口径。
```

推荐顺序是：理解问题与选型 → 改进与验证 → 实现与绘图 → 论文整理 → 交接与结果核对。每项也能独立使用，按任务需要选择。

安装与静态检查使用 Python 标准库。MATLAB 绘图需要 MATLAB；LaTeX 编译需要本机相应工具链；draw.io 文件可以在 diagrams.net 中编辑。具体输入、命令和依赖见各项技能。

## 更新与维护

更新本地仓库后，重新运行安装器即可；相同文件会跳过。

```sh
git pull --ff-only
python scripts/check.py
python -m unittest discover -s tests
python scripts/install.py
```

欢迎提交 Issue 或 PR，描述遇到的问题、最小合成示例和预期结果。贡献约定见 [CONTRIBUTING.md](CONTRIBUTING.md)，版本变化见 [CHANGELOG.md](CHANGELOG.md)。

## 来源与许可

本仓库内容采用 [MIT License](LICENSE)。通用建模方法、软件和外部项目的权利归各自权利人所有；来源说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

可搭配 [MathModelAgent](https://github.com/jihe520/MathModelAgent) 的完整工作流使用，请按其自身许可获取。其工作流、素材和模板不包含在本发行包中。

文档组织参考了 [Anthropic Skills](https://github.com/anthropics/skills) 和 [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) 的技能目录、快速开始与维护说明形式。
