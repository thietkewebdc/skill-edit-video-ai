"""Cắt video nói (mở đầu 20s, đoạn người thật) theo CHỮ: bỏ im lặng/vấp/lan man, mối nối vào chỗ lặng, zoom xen kẽ, chuẩn âm -14 LUFS.
  python3 cut_opening.py words  video.mp4 work         # nhận giọng (mlx whisper) -> work/words.txt (chữ@mốc) để chọn đoạn giữ
  python3 cut_opening.py render video.mp4 work ranges.json -o mo-dau.mp4 [--zoom 1.15]
ranges.json: [[bắt đầu, kết thúc], ...] theo mốc chữ (giây). Mép vào/ra tự dời vào khoảng lặng gần nhất. Thêm phần tử thứ 3 "raw" để KHÔNG dời.
Sau khi render: nghe lại bằng `words` trên file ra — số liệu/chữ thừa lọt mối nối thì chỉnh mép (vd chữ kế sát đuôi: lùi mép ra 0.05s)."""
import sys, json, subprocess, argparse, numpy as np
import os
PY=os.environ.get("HMT_ASR_PY") or os.path.expanduser("~/.claude/hmt-asr/venv/bin/python")   # python có mlx_whisper
def run_words(video,work,out_json):
    import os; os.makedirs(work,exist_ok=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-vn","-ac","1","-ar","16000",f"{work}/a.wav"],check=True)
    code=f"""import mlx_whisper,json
r=mlx_whisper.transcribe('{work}/a.wav',path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='vi',word_timestamps=True,condition_on_previous_text=False)
json.dump(r,open('{out_json}','w'),ensure_ascii=False)
open('{work}/words.txt','w').write(' '.join(f"{{w['word'].strip()}}@{{w['start']:.2f}}-{{w['end']:.2f}}" for s in r['segments'] for w in s['words']))
print(open('{work}/words.txt').read())"""
    subprocess.run([PY,"-c",code],check=True)
if sys.argv[1]=="words": run_words(sys.argv[2],sys.argv[3],sys.argv[3]+"/words.json")
else:
    ap=argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("video"); ap.add_argument("work"); ap.add_argument("ranges"); ap.add_argument("-o",required=True)
    ap.add_argument("--zoom",type=float,default=1.15); ap.add_argument("--w",type=int,default=0); ap.add_argument("--h",type=int,default=0); a=ap.parse_args()
    probe=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",a.video]).decode().strip().split(",")
    W,H=int(probe[0]),int(probe[1]); subprocess.run(["ffmpeg","-v","error","-y","-i",a.video,"-vn","-ac","1","-ar","16000",f"{a.work}/a.wav"],check=True)
    x=np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",f"{a.work}/a.wav","-f","s16le","-ac","1","-ar","16000","-"]),dtype=np.int16).astype(float)
    env=np.sqrt(np.convolve(x**2,np.ones(160)/160,"same"))[::160]
    def snap(t,lo,hi): i0=max(0,int((t-lo)*100)); i1=int((t+hi)*100); return (i0+int(np.argmin(env[i0:i1])))/100
    segs=[]
    for r in json.load(open(a.ranges)):
        s,e=r[0],r[1]
        if len(r)<3: s=max(0,snap(s,0.25,0.0)-0.06); e=snap(e,0.0,0.18)+0.06
        segs.append((s,e))
    fc=""
    for i,(s,e) in enumerate(segs):
        z=1.0 if i%2==0 else a.zoom; cw,ch=W/z,H/z; cx=max(0,min(W-cw,W/2-cw/2)); cy=max(0,min(H-ch,H*0.46-ch*0.42))
        fc+=f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,crop={cw:.0f}:{ch:.0f}:{cx:.0f}:{cy:.0f},scale={W}:{H}:flags=lanczos,setsar=1[v{i}];"
        fc+=f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={e-s-0.04:.2f}:d=0.04[a{i}];"
    fc+="".join(f"[v{i}][a{i}]" for i in range(len(segs)))+f"concat=n={len(segs)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg","-v","error","-y","-i",a.video,"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-r","30","-c:a","aac",f"{a.work}/tho.mp4"],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"{a.work}/tho.mp4","-af","loudnorm=I=-14:LRA=7:TP=-1.5","-c:v","copy","-c:a","aac","-b:a","192k",f"{a.work}/n1.mp4"],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"{a.work}/n1.mp4","-af","volume=1.3dB,alimiter=limit=0.9:level=disabled","-c:v","copy","-c:a","aac","-b:a","192k",a.o],check=True)   # loudnorm ra ~-15.4 -> bù +1.3dB về ~-14
    d=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",a.o]).decode().strip(); print("ok",a.o,d+"s")
