# 合成公式组排版示例

以下库存递推仅用于展示排版，是自包含的抽象示例，不是任何参赛题的答案。假设示例源文已定义：离散时刻 $k=0,\ldots,K$ 的库存 $x_k$，阶段补给 $u_k$，已知需求 $d_k\ge0$，补给上限 $U\ge0$ 与已知初值 $x_{\mathrm{init}}\ge0$。这些量采用相同的数量单位，且不允许缺货。

用户实际稿件应从其源文提取关系和说明，不能自动采用本例的初值、约束或符号。

```latex
% Requires amsmath and a document setup supporting the caption language.
% Example source: inventory balance, initial state, supply and stock bounds.
\begin{equation}
  \begin{cases}
    \displaystyle x_{k+1}=x_k+u_k-d_k,
      & \text{库存平衡，} k=0,\ldots,K-1, \\[6pt]
    \displaystyle x_0=x_{\mathrm{init}},
      & \text{初始库存}, \\[6pt]
    \displaystyle 0\le u_k\le U,
      & \text{补给范围，} k=0,\ldots,K-1, \\[6pt]
    \displaystyle x_k\ge0,
      & \text{禁止缺货，} k=0,\ldots,K.
  \end{cases}
  \label{eq:inventory-summary}
\end{equation}
```

合适的参数说明可以是：需求序列 $d_k$、上限 $U$、初值 $x_{\mathrm{init}}$ 和阶段数 $K$ 为输入；补给 $u_k$ 为决策；库存 $x_k$ 为状态。这个汇总没有给定优化目标，因此不能将其描述为完整的最优补给模型。

在正式项目中，注释应指向实际原公式或段落。新增编号后检查后文交叉引用；若源文的符号定义或约束范围与本例不同，完全以实际来源为准。
