"""Sub kiểu thanh xanh gọn ở đáy (chữ trắng, rộng 80% khung, cao 92px, viền xanh sáng mép trên).
  python3 make_sub.py --scenes scenes.json --wav wav --work work --in ghep.mp4 --out co_sub.mp4
Chia cụm theo dấu câu, thời gian chia theo số ký tự trong cửa sổ voice của từng cảnh (lệch nhẹ vài phần mười giây)."""
import json, re, subprocess, argparse
ap=argparse.ArgumentParser(); ap.add_argument("--scenes",default="scenes.json"); ap.add_argument("--wav",default="wav"); ap.add_argument("--work",default="work")
ap.add_argument("--in",dest="inp",required=True); ap.add_argument("--out",required=True); ap.add_argument("--lead",type=float,default=0.25)
ap.add_argument("--font",default="Be Vietnam Pro"); ap.add_argument("--size",type=int,default=44); ap.add_argument("--color",default="0x0B4C73"); a=ap.parse_args()
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
def chunks(t,mx=58):
    parts=[p.strip() for p in re.findall(r"[^,.:;!?]+[,.:;!?]?",t) if p.strip()]; out=[]
    for p in parts:
        while len(p)>mx: w=p.split(); k=len(w)//2; out.append(" ".join(w[:k])); p=" ".join(w[k:])
        if out and len(out[-1])+len(p)<=mx*0.55: out[-1]+=" "+p
        else: out.append(p)
    return out
def ts(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
ev=[]; off=0
for s in json.load(open(a.scenes)):
    d=dur(f"{a.wav}/s{s['id']}.wav"); cs=chunks(s["text"]); tot=sum(len(c) for c in cs); t=off+a.lead
    for c in cs: w=d*len(c)/tot; ev.append(f"Dialogue: 0,{ts(t)},{ts(t+w)},Sub,,0,0,0,,{c}"); t+=w
    off+=dur(f"{a.work}/p{s['id']}.mp4")
hdr=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,{a.font},{a.size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,260,260,36,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
ass=f"{a.work}/sub.ass"; open(ass,"w").write(hdr+"\n".join(ev)+"\n")
vf=(f"drawbox=x=192:y=962:w=1536:h=92:color={a.color}@0.93:t=fill,drawbox=x=192:y=962:w=1536:h=3:color=0x2FA4E8@1:t=fill,ass={ass}")
subprocess.run(["ffmpeg","-v","error","-y","-i",a.inp,"-vf",vf,"-c:v","libx264","-crf","19","-preset","fast","-c:a","copy",a.out],check=True); print(len(ev),"dòng sub ->",a.out)
