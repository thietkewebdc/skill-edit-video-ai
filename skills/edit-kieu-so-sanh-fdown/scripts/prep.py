import json, sys
def apply(src, dst, drop=(), sub=None, drop_ranges=()):
    ws = json.load(open(src))["words"]
    sub = sub or {}
    dr = set(drop)
    for a, b in drop_ranges: dr.update(range(a, b + 1))
    out = []
    for i, w in enumerate(ws):
        if i in dr: continue
        if i in sub: w = dict(w, w=sub[i])
        out.append(w)
    json.dump(out, open(dst, "w"), ensure_ascii=False)
    return len(out)
