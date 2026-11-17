function demo_gallery(outputDir)
% Six reusable chart structures. ALL DATA ARE SYNTHETIC DEMONSTRATIONS.
if nargin==0, outputDir=fullfile(pwd,'demo_figures'); end
if ~isfolder(outputDir), mkdir(outputDir); end
c=paper_palette();
x=linspace(0,24,97)'; a=55+12*sin((x-6)*pi/12); b=a+4*cos(x*pi/8);

f=newfig(); ax=axes(f); hold(ax,'on');
h1=plot(ax,x,a,'-','Color',c(1,:),'LineWidth',1.6);
h2=plot(ax,x,b,'--','Color',c(2,:),'LineWidth',1.6);
s=paper_axes(ax); xlabel(ax,'时间 (h)'); ylabel(ax,'负荷 (kW)');
title(ax,'两组趋势对比 · 合成演示数据');
legend(ax,[h1 h2],{'方案 A','方案 B'},'FontName',s.cnFont,'Box','off','Location','northwest');
paper_export(f,fullfile(outputDir,'01_comparison')); close(f);

f=newfig(); ax=axes(f); hold(ax,'on');
w=3+0.12*x; band=paper_band(ax,x,a-w,a+w,c(1,:),'示例范围');
h=plot(ax,x,a,'Color',c(1,:),'LineWidth',1.6);
s=paper_axes(ax); xlabel(ax,'时间 (h)'); ylabel(ax,'负荷 (kW)');
title(ax,'中心曲线与给定上下界 · 合成演示数据');
legend(ax,[h band(1)],{'中心曲线','人为给定范围（非统计区间）'}, ...
    'FontName',s.cnFont,'Box','off','Location','northwest');
paper_export(f,fullfile(outputDir,'02_interval')); close(f);

f=newfig(); ax=axes(f); hold(ax,'on');
errorbar(ax,1:4,[8 6.5 5.8 6.1],[.8 .5 .35 .6],'o', ...
    'Color',c(1,:),'LineWidth',1.4,'MarkerFaceColor','w','MarkerSize',5,'CapSize',9);
s=paper_axes(ax); xticks(ax,1:4); xticklabels(ax,{'A','B','C','D'}); xlim(ax,[.5 4.5]);
xlabel(ax,'方案'); ylabel(ax,'运行时间 (s)'); title(ax,'离散结果与示例误差长度 · 合成数据');
paper_export(f,fullfile(outputDir,'03_errorbar')); close(f);

f=newfig(); ax=axes(f); hold(ax,'on');
p=(0:.1:2)'; cost=10+5*(p-.8).^2; [best,k]=min(cost);
plot(ax,p,cost,'o-','Color',c(3,:),'LineWidth',1.6,'MarkerSize',4);
xline(ax,p(k),'--','Color',[.4 .4 .4],'LineWidth',.9);
plot(ax,p(k),best,'o','Color',c(2,:),'MarkerFaceColor',c(2,:),'MarkerSize',7);
s=paper_axes(ax); xlabel(ax,'参数 λ'); ylabel(ax,'成本 (元)');
title(ax,'参数敏感性 · 合成演示数据');
text(ax,p(k)+.08,best+.5,sprintf('网格最小值：%.2f',p(k)),'FontName',s.cnFont,'FontSize',10);
paper_export(f,fullfile(outputDir,'04_sensitivity')); close(f);

f=newfig(); set(f,'Position',[2 2 16 14]); tl=tiledlayout(f,2,1,'TileSpacing','compact','Padding','compact');
t=(0:2:24)'; observed=4+1.5*t+.8*sin(t); coeff=polyfit(t,observed,1); fitted=polyval(coeff,t);
ax=nexttile(tl); hold(ax,'on');
h1=scatter(ax,t,observed,20,c(1,:),'filled');
h2=plot(ax,t,fitted,'-','Color',c(2,:),'LineWidth',1.6);
s=paper_axes(ax); ylabel(ax,'响应值'); title(ax,'拟合与残差诊断 · 合成演示数据');
legend(ax,[h1 h2],{'示例观测','线性拟合'},'FontName',s.cnFont,'Box','off','Location','northwest');
ax=nexttile(tl); scatter(ax,t,observed-fitted,20,c(1,:),'filled');
yline(ax,0,'--','Color',[.4 .4 .4]); paper_axes(ax); xlabel(ax,'时间 (h)'); ylabel(ax,'残差');
paper_export(f,fullfile(outputDir,'05_diagnostics')); close(f);

f=newfig(); ax=axes(f); [u,v]=meshgrid(linspace(0,1,50)); z=(u-.3).^2+2*(v-.6).^2;
contourf(ax,u,v,z,12,'LineColor','none'); colormap(ax,parula(128));
s=paper_axes(ax); grid(ax,'off'); cb=colorbar(ax); cb.Label.String='响应值（无量纲）';
cb.Label.FontName=s.cnFont; xlabel(ax,'参数 A'); ylabel(ax,'参数 B');
title(ax,'双参数响应面（等高线）· 合成数据');
paper_export(f,fullfile(outputDir,'06_response')); close(f);
end

function f=newfig()
f=figure('Visible','off','Color','w','Units','centimeters','Position',[2 2 16 11]);
end
