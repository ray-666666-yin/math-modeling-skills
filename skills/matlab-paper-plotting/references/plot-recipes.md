# 图型与误差表达

| 目的 | 图型 | 需要的依据 |
|---|---|---|
| 连续趋势比较 | plot，颜色与线型 | 同一轴含义和单位 |
| 连续区间 | paper_band加中心曲线 | 每个采样点的上下界及其定义 |
| 离散估计 | errorbar加marker | 每个估计量与误差长度的来源 |
| 参数敏感性 | 参数-响应曲线 | 实际扰动配置与输出 |
| 拟合诊断 | 观测/拟合、残差上下分面 | 同一组输入的拟合值与残差 |
| 双参数响应 | contourf或surf | 两个连续自变量及相应响应网格 |

```matlab
c=paper_palette();
f=figure('Color','w','Units','centimeters','Position',[2 2 16 11]);
ax=axes(f); hold(ax,'on');
band=paper_band(ax,x,lowerBound,upperBound,c(1,:),'给定区间');
curve=plot(ax,x,prediction,'Color',c(1,:),'LineWidth',1.6);
s=paper_axes(ax);
xlabel(ax,'时间 (h)'); ylabel(ax,'功率 (kW)');
if isempty(band)
    legend(ax,curve,{'预测值'},'FontName',s.cnFont,'Box','off');
else
    legend(ax,[curve band(1)],{'预测值','给定区间'},'FontName',s.cnFont,'Box','off');
end
paper_export(f,fullfile('figures','prediction'));
```

只有实际区间定义支持时，才把“给定区间”改为“95%预测区间”等具体名字。缺测不跨越；乱序或重复横轴先按业务含义处理，不在绘图函数中自动平均。

柱形图一般从零起，局部曲线放大需显示尺度。可以减少marker的显示频率，但完整曲线数据仍保留。额外工具箱函数需单独声明，不能因基础辅助函数可运行就认为整个任务无工具箱依赖。

