# 布局输入与实现

`scripts/render_drawio.py` 仅依赖 Python 3 标准库，接收UTF-8 JSON并输出未压缩draw.io XML。不需要Node包、在线账号或专有运行时。它不是自动排版器；复杂图需根据语义调整坐标，再在绘图软件核查。

```text
python scripts/render_drawio.py assets/example-flow.json work/example.drawio
```

默认拒绝覆盖已有输出；明确要替换时加 `--overwrite`。输入路径和输出路径不能相同。坐标单位是draw.io画布单位。

顶层字段：
- `title`：图页名称；`width`、`height`：正数画布大小。
- `font`：可选字体名，默认 `sans-serif`；使用目标机器实际可用字体。包内不提供字体。
- `nodes`：对象列表；各项必须含 `id`、`label`、`x`、`y`、`width`、`height`。
- 节点可选 `role` 为input/model/compute/decision/output/group，`shape` 为rounded/rect/diamond/ellipse；`fontSize` 为正数。group是视觉分组框，不是嵌套父对象，排在内容节点之前绘制。
- `edges`：各项含 `source`、`target`；可选唯一 `id`、`label`、布尔 `dashed`；`points` 为折线路点，每项含 `x`、`y`。没有路点时由编辑器按正交规则连接。

标签是纯文本，换行用JSON的 `\n`；脚本转义XML和HTML，保留中文与数学Unicode。脚本不解释LaTeX或Markdown。复杂公式可在目标编辑器中另作语义核对和可编辑排版，不把所有标签变成轮廓。

`assets/example-flow.json` 是全新通用结构示例，含并行分支、汇合与带条件的反馈，不来自论文截图。其标签仅为演示，不声明任何真实模型已经验证。

PNG/PDF导出可用已安装的diagrams.net桌面程序或浏览器导出菜单。使用其当前帮助确认命令和可用选项；输出后实际查看，避免把XML检查当成图像检查。PPTX需环境中的独立编辑/导出实现，XML脚本本身不生成PPTX。

