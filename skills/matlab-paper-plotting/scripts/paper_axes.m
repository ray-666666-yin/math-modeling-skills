function s = paper_axes(ax)
% Local axes styling. Call after plotting/hold operations.
if nargin==0, ax=gca; end
s.colors=paper_palette(); fonts=string(listfonts); s.font='Arial';
if any(strcmpi(fonts,'Times New Roman')), s.font='Times New Roman'; end
s.cnFont=s.font;
for candidate=["Microsoft YaHei","SimHei","SimSun","Noto Sans CJK SC"]
    if any(strcmpi(fonts,candidate)), s.cnFont=char(candidate); break; end
end
set(ax,'FontName',s.font,'FontSize',10,'LineWidth',0.8, ...
    'Color','w','Box','on','TickDir','out','XGrid','on','YGrid','on', ...
    'GridColor',[.65 .65 .65],'GridAlpha',.18, ...
    'XMinorGrid','off','YMinorGrid','off','ColorOrder',s.colors);
for t=[ax.XLabel ax.YLabel ax.ZLabel]
    set(t,'FontName',s.cnFont,'FontSize',11,'Interpreter','tex');
end
set(ax.Title,'FontName',s.cnFont,'FontSize',12,'FontWeight','normal','Interpreter','tex');
end
