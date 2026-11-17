function paper_export(fig,stem)
% stem includes output directory, without extension. Requires exportgraphics.
folder=fileparts(stem); if ~isempty(folder)&&~isfolder(folder), mkdir(folder); end
set(fig,'Color','w'); drawnow;
savefig(fig,[stem '.fig']);
exportgraphics(fig,[stem '.png'],'Resolution',300,'BackgroundColor','white');
exportgraphics(fig,[stem '.pdf'],'ContentType','vector','BackgroundColor','white');
end
