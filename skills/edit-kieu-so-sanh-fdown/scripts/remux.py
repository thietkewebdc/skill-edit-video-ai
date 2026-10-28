import sys, json, os
import render
cfg = render._expand(json.load(open(sys.argv[1])))
render.mux(cfg, os.path.join(cfg["work"], cfg["name"]))
