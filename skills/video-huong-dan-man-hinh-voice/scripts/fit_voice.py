"""Ghép voice vào màn hình: mỗi cảnh lấy đoạn màn hình [t0,t1], co/giãn cho khớp thời lượng voice.
  python3 fit_voice.py --src man_hinh.mp4 --scenes scenes.json --wav wav --work work --out ghep.mp4
Màn hình dài hơn voice -> tua nhanh (tối đa --max-speed, mặc định 1.3x); voice dài hơn -> làm chậm (tối thiểu 0.85x) rồi đứng hình.
Cảnh còn thừa im lặng > 2s được báo kèm số chữ nên viết thêm."""
import json, subprocess, argparse, os
ap=argparse.ArgumentParser(); ap.add_argument("--src",required=True); ap.add_argument("--scenes",default="scenes.json")
ap.add_argument("--wav",default="wav"); ap.add_argument("--work",default="work"); ap.add_argument("--out",default="ghep.mp4")
ap.add_argument("--max-speed",type=float,default=1.3); ap.add_argument("--min-speed",type=float,default=0.85)
ap.add_argument("--lead",type=float,default=0.25); ap.add_argument("--tail",type=float,default=0.35); ap.add_argument("--fps",type=int,default=30); a=ap.parse_args()
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
os.makedirs(a.work,exist_ok=True); parts=[]; rep=[]
for s in json.load(open(a.scenes)):
    d=dur(f"{a.wav}/s{s['id']}.wav"); need=a.lead+d+a.tail; L=s["t1"]-s["t0"]
    sp=max(a.min_speed,min(L/need,a.max_speed)); vlen=L/sp; pad=max(0,need-vlen); total=max(vlen,need)
    note="khớp" if 0.95<=sp<=1.1 else ("tua %.2fx"%sp if sp>1 else "chậm %.2fx"%sp)
    if pad>0.05: note+=" + đứng hình %.1fs"%pad
    gap=vlen-need
    if gap>2: note+=" | thừa %.1fs im lặng -> viết thêm ~%d chữ"%(gap,round(gap*len(s["text"].split())/d))
    rep.append(f"cảnh {s['id']}: màn hình {L:.1f}s, voice {d:.1f}s -> {note}")
    out=f"{a.work}/p{s['id']}.mp4"; ms=int(a.lead*1000)
    fc=(f"[0:v]trim=start={s['t0']}:end={s['t1']},setpts=(PTS-STARTPTS)/{sp},fps={a.fps},scale=1920:1080,setsar=1,"
        f"tpad=stop_mode=clone:stop_duration={pad+0.05},trim=duration={total}[v];"
        f"[1:a]adelay={ms}|{ms},apad=whole_dur={total},atrim=duration={total}[a]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",a.src,"-i",f"{a.wav}/s{s['id']}.wav","-filter_complex",fc,"-map","[v]","-map","[a]",
        "-c:v","libx264","-crf","20","-preset","fast","-ar","44100","-c:a","aac","-b:a","192k",out],check=True); parts.append(os.path.abspath(out))
lst=f"{a.work}/list.txt"; open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,"-c","copy",a.out],check=True)
open(f"{a.work}/bao_cao.txt","w").write("\n".join(rep)); print("\n".join(rep)); print("tổng %.1fs ->"%dur(a.out),a.out)
