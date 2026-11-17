function h = paper_band(ax,x,lower,upper,color,label)
% Caller defines interval meaning. Preserve missing-data gaps.
if nargin<6, label='Interval'; end
x=x(:); lower=lower(:); upper=upper(:);
assert(numel(x)==numel(lower)&&numel(x)==numel(upper),'Lengths must match.');
valid=isfinite(x)&isfinite(lower)&isfinite(upper);
assert(all(lower(valid)<=upper(valid)),'Lower bound exceeds upper bound.');
assert(all(diff(x(isfinite(x)))>0),'Finite x values must be strictly increasing.');
edges=diff([false;valid;false]); starts=find(edges==1); stops=find(edges==-1)-1;
wasHeld=ishold(ax); hold(ax,'on'); h=gobjects(0);
for k=1:numel(starts)
    idx=starts(k):stops(k); if numel(idx)<2, continue; end
    xx=x(idx); lo=lower(idx); hi=upper(idx);
    p=fill(ax,[xx;flipud(xx)],[lo;flipud(hi)],color, ...
        'FaceAlpha',.15,'EdgeColor','none','DisplayName',label);
    if ~isempty(h), p.HandleVisibility='off'; end
    h(end+1)=p; %#ok<AGROW>
end
if ~wasHeld, hold(ax,'off'); end
end
