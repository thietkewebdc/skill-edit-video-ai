#!/usr/bin/env python3
"""TEMPLATE (framed/premium look) — FINAL step. Captions(ASS)+hook+CTA+whoosh+music+loudnorm+encode.
EDIT: paths, P[] captions (output timeline), pills/hook/cta, WHOOSH_AT, END. tpad freeze BEFORE subtitles."""
import subprocess, wave
from pathlib import Path
import numpy as np
S=Path("/private/tmp/claude-501/-Users-cesc-Documents-Video-M-i/d6e1c67f-08c7-4935-8ecb-733feac1b6c8/scratchpad")
PROJ=Path.home()/"Videos"
FONT=S/"Montserrat.ttf"; RES=PROJ/"Visa5s - Bộ dựng CapCut"/"Tài nguyên"
OUT=PROJ/"DJI - Reel tiết kiệm 100 triệu (TikTok).mp4"
W,H,END,sr=1080,1920,99.6,48000
def run(c):
    p=subprocess.run(c,capture_output=True,text=True)
    if p.returncode!=0: print("ERR",p.stderr[-1800:]); raise SystemExit(1)
def tt(s):
    cs=int(round(s*100));return f"{cs//360000}:{(cs//6000)%60:02d}:{(cs//100)%60:02d}.{cs%100:02d}"

# audio: base + whoosh
def pcm(p,dur=None):
    a=["ffmpeg","-v","error","-i",str(p)]+(["-t",str(dur)] if dur else [])+["-ar",str(sr),"-ac","2","-f","f32le","-"]
    return np.frombuffer(subprocess.check_output(a),np.float32).reshape(-1,2).copy()
base=pcm(S/"base2_audio.wav"); N=int(END*sr); mix=np.zeros((N,2),np.float32)
k=min(len(base),N); mix[:k]=base[:k]
wh=pcm(RES/"Whoosh.mp3",dur=1.4); wh*=0.20/max(1e-9,np.max(np.abs(wh)))
for t in [9.2,20.6,26.6,39.6,61.9,70.6,83.0,97.2]:
    s=int(t*sr); e=min(len(wh),N-s)
    if 0<=s<N: mix[s:s+e]+=wh[:e]
mix*=min(1,10**(-1.0/20)/max(1e-9,np.max(np.abs(mix))))
with wave.open(str(S/"mix2.wav"),"wb") as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-1,1)*32767).astype("<i2").tobytes())

P=[(0.00,2.30,"Nếu bạn đang mất hàng giờ","W",0),(2.30,4.10,"chỉ để làm những việc này","W",0),
(4.10,6.00,"thì phải THAY ĐỔI NGAY","Y",1),(9.16,12.20,"Tiết kiệm ~100 TRIỆU tiền viết bài","Y",0),
(13.32,15.00,"Thuê nhân viên viết bài","W",0),(15.06,18.60,"10 TRIỆU mỗi tháng","Y",1),
(18.74,20.72,"= 120 TRIỆU / năm","Y",1),(20.88,23.00,"Chỉ cần cắt 3 nhân sự","W",0),
(23.00,26.46,"là bớt được VÀI TRĂM TRIỆU","Y",1),(26.92,30.72,"Video này hướng dẫn cụ thể","W",0),
(30.72,34.50,"cách ứng dụng vào công việc","W",0),(35.16,38.86,"Xem hết & bình luận nhé!","Y",0),
(39.52,42.54,"Đầu tiên, lên kế hoạch chi tiết","W",0),(42.74,46.76,"mỗi tháng viết bao nhiêu bài","W",0),
(46.92,50.92,"cấu trúc & nội dung ra sao","W",0),(50.92,53.36,"Nội dung phải được kiểm duyệt","W",0),
(53.46,56.76,"đọc kỹ, đúng chuẩn phong cách","W",0),(56.76,61.86,"không phải viết rồi đăng đại","Y",0),
(62.62,66.06,"Đây là bộ kế hoạch chuyên sâu","W",0),(66.34,70.60,"bạn cứ dựa theo mà làm","W",0),
(70.64,73.68,"Lên bộ kế hoạch nội dung","W",0),(73.78,77.55,"rồi nạp nội dung vào","W",0),
(77.60,82.88,"hệ thống TỰ ĐỘNG chạy hàng tháng","Y",0),(83.06,86.68,"Chi tiết hơn ở khóa chuyên sâu","W",0),
(86.82,91.60,"để bạn tự vận hành doanh nghiệp","W",0),(92.16,94.76,"trọn bộ nội dung & viết bài","W",0),
(95.46,97.30,"Hẹn gặp lại nhé!","Y",0)]
head=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Montserrat,70,&H00FFFFFF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,72,1
Style: Y,Montserrat,70,&H0000D4FF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,72,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ls=[]
for s,e,txt,st,big in P:
    fx="{\\fad(100,70)\\fscx88\\fscy88\\t(0,120,\\fscx100\\fscy100)}" if not big else "{\\fad(100,70)\\fs92\\fscx86\\fscy86\\t(0,130,\\fscx104\\fscy104)}"
    ls.append(f"Dialogue: 0,{tt(s)},{tt(e)},{st},,0,0,0,,{fx}{txt}")
(S/"cap4.ass").write_text(head+"\n".join(ls)+"\n",encoding="utf-8")

def dtxt(txt,t0,t1,box,fg,x,y,fs):
    tf=S/f"d4_{abs(hash(txt))%99999}.txt";tf.write_text(txt,encoding="utf-8")
    a=f"if(lt(t,{t0}+0.2),(t-{t0})/0.2,if(gt(t,{t1}-0.3),({t1}-t)/0.3,1))"
    return (f"drawtext=fontfile='{FONT}':textfile='{tf}':x={x}:y={y}:fontsize={fs}:fontcolor={fg}:"
            f"box=1:boxcolor={box}:boxborderw=24:alpha='{a}':enable='between(t,{t0},{t1})'")
hook=dtxt("MẤT 100 TRIỆU/NĂM VÌ VIỆC NÀY?",0,6.0,"0xFFD400@0.96","0x1E1746","(w-tw)/2",48,50)
cta=dtxt("BÌNH LUẬN: QUAN TÂM",94.0,END,"0x5946CE@0.96","white","(w-tw)/2",1650,58)

vf=(f"tpad=stop_mode=clone:stop_duration=1.5,subtitles='{S}/cap4.ass':fontsdir='{S}',{hook},{cta}")
run(["ffmpeg","-v","error","-y","-framerate","25","-i",f"{S}/frames_fr2/%05d.jpg","-i",str(S/"mix2.wav"),
     "-vf",vf,"-af","loudnorm=I=-14:TP=-1:LRA=11","-t",str(END),
     "-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-r","30",
     "-c:a","aac","-b:a","192k","-movflags","+faststart",str(OUT)])
print("DONE",OUT)
