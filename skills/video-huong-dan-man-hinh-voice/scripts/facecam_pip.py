"""Vòng tròn mặt viền vàng góc dưới phải, chạy song song video màn hình.
  python3 facecam_pip.py sheet  mat.mp4 sheet.png            # sheet mỗi 4s có mốc giờ -> XEM, chọn đoạn anh ngồi ngay ngắn (gõ phím/rê chuột/nhìn màn hình), bỏ đoạn vung tay
  python3 facecam_pip.py suggest mat.mp4                      # gợi ý tự động (KHÔNG chắc, phải xem sheet kiểm lại)
  python3 facecam_pip.py render --main co_sub.mp4 --face mat.mp4 --windows "4-26,38-62,76-84,88-113" --out ra.mp4 [--crop 340:340:262:0]
Face cam không đủ dài -> tự lặp các đoạn theo thứ tự, nối chuyển mờ 0.4s. Tiếng mặt bị tắt, giữ tiếng video chính."""
import sys, subprocess, argparse, numpy as np
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
cmd=sys.argv[1]
if cmd=="sheet":
    subprocess.run(["ffmpeg","-v","error","-y","-i",sys.argv[2],"-vf","fps=1/4,scale=300:-1,drawtext=text='%{pts\\:hms}':x=6:y=6:fontcolor=yellow:fontsize=22:box=1:boxcolor=black@0.6,tile=7x5","-frames:v","1",sys.argv[3]]); print("xem",sys.argv[3])
elif cmd=="suggest":
    W,H=212,116; raw=subprocess.check_output(["ffmpeg","-v","error","-i",sys.argv[2],"-vf",f"fps=2,scale={W}:{H},format=gray","-f","rawvideo","-"])
    f=np.frombuffer(raw,np.uint8).reshape(-1,H,W).astype(float); b=f[:,int(.5*H):int(.8*H),int(.22*W):int(.78*W)]
    d=np.abs(b-np.median(b,axis=0)).mean(axis=(1,2)); m=np.r_[0,np.abs(np.diff(b,axis=0)).mean(axis=(1,2))]
    k=np.ones(5)/5; ds=np.convolve(d,k,"same"); ms=np.convolve(m,k,"same"); ok=(ds<np.percentile(ds,50))&(ms<np.percentile(ms,60)); i=0; out=[]
    while i<len(ok):
        if ok[i]:
            j=i
            while j<len(ok) and ok[j]: j+=1
            if (j-i)/2>=7: out.append(f"{i/2:.0f}-{j/2:.0f}")
            i=j
        else: i+=1
    print(",".join(out)); print("(gợi ý thôi — kiểm lại bằng sheet)")
else:
    ap=argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--main",required=True); ap.add_argument("--face",required=True)
    ap.add_argument("--windows",required=True); ap.add_argument("--out",required=True); ap.add_argument("--crop",default="340:340:262:0")
    ap.add_argument("--size",type=int,default=300); ap.add_argument("--ring",type=int,default=8); ap.add_argument("--x",type=int,default=-1); ap.add_argument("--y",type=int,default=-1)
    ap.add_argument("--color",default="0xF4C80F"); a=ap.parse_args()
    wins=[tuple(map(float,w.split("-"))) for w in a.windows.split(",")]; D=dur(a.main); XF=0.4; S=a.size; R=S+2*a.ring
    while sum(e-s for s,e in wins)-XF*(len(wins)-1)<D: wins=wins+wins        # lặp lại cho đủ dài
    fc=""
    for i,(s,e) in enumerate(wins): fc+=f"[1:v]trim={s}:{e},setpts=PTS-STARTPTS,crop={a.crop},scale={S}:{S}:flags=lanczos,fps=30,format=yuv420p[c{i}];"
    cur="c0"; acc=wins[0][1]-wins[0][0]
    for i in range(1,len(wins)):
        off=acc-XF; fc+=f"[{cur}][c{i}]xfade=transition=fade:duration={XF}:offset={off:.2f}[x{i}];"; cur=f"x{i}"; acc=off+XF+(wins[i][1]-wins[i][0])
    X=a.x if a.x>=0 else 1920-R-26; Y=a.y if a.y>=0 else 622
    fc+=(f"[{cur}]trim=0:{D},setpts=PTS-STARTPTS,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lt(hypot(X-{S/2},Y-{S/2}),{S/2}),255,0)'[face];"
         f"color=c={a.color}:s={R}x{R},format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lt(hypot(X-{R/2},Y-{R/2}),{R/2}),255,0)'[ring];"
         f"[0:v][ring]overlay={X}:{Y}[a];[a][face]overlay={X+a.ring}:{Y+a.ring}:eof_action=pass[v]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",a.main,"-i",a.face,"-filter_complex",fc,"-map","[v]","-map","0:a","-t",str(D),"-c:v","libx264","-crf","20","-preset","fast","-c:a","copy",a.out],check=True); print("ok",a.out)
