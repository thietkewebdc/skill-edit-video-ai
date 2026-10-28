#!/usr/bin/env python3
"""TEMPLATE (framed/premium look) — COMPOSE step. Run in rembg venv (PIL+numpy).
Reads matted frames (frames_out from bokeh.py) → composes dark bg + rounded glow card +
person-shrink + graphic PANEL reveals → frames_fr. EDIT: IN glob, FPS, panels p_*(),
reveal windows R=[(start,end,kind)], BIG_W/SMALL_W. Then run framed_final.py."""
import glob, time, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S="/private/tmp/claude-501/-Users-cesc-Documents-Video-M-i/d6e1c67f-08c7-4935-8ecb-733feac1b6c8/scratchpad"
W,H,FPS=1080,1920,25
FONT=f"{S}/Montserrat.ttf"
def F(s): return ImageFont.truetype(FONT,s)
IN=sorted(glob.glob(f"{S}/frames_out2/*.jpg"))
ORANGE=(255,150,20)

# background
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
d=np.sqrt((xx-W*0.5)**2+(yy-H*0.30)**2)/(W*0.9); glow=np.clip(1-d,0,1)**2
bg=np.zeros((H,W,3),np.float32); bg[:]=np.array([12,12,22])
bg[:,:,0]+=glow*70; bg[:,:,1]+=glow*40; bg[:,:,2]+=glow*8
gg=np.zeros((H,W),np.float32); gg[::48,::48]=1; bg+=gg[:,:,None]*np.array([15,15,22])
BG=Image.fromarray(np.clip(bg,0,255).astype(np.uint8),"RGB")

def rmask(w,h,r):
    m=Image.new("L",(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],radius=r,fill=255); return m
def gborder(dr,box,r,col):
    for wdt,al in [(16,70),(10,140),(5,255)]:
        dr.rounded_rectangle(box,radius=r,outline=(col[0],col[1],col[2],al),width=wdt)

def base_panel(h=600,accent=ORANGE):
    pw=980; im=Image.new("RGBA",(pw,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,pw-1,h-1],radius=40,fill=(16,16,30,238)); gborder(d,[0,0,pw-1,h-1],40,accent)
    return im,d,pw
def p_cost():
    im,d,pw=base_panel(560,(230,90,70))
    d.text((pw/2,66),"CHI PHÍ VIẾT BÀI (CŨ)",font=F(44),fill=(230,150,150,255),anchor="mm")
    d.text((pw/2,215),"10 TRIỆU / THÁNG",font=F(96),fill=(255,90,90,255),anchor="mm")
    d.text((pw/2,340),"=  120 TRIỆU / NĂM",font=F(78),fill=(255,140,140,255),anchor="mm")
    d.text((pw/2,470),"chỉ để thuê nhân viên viết bài",font=F(40),fill=(200,200,210,255),anchor="mm")
    return im
def p_save():
    im,d,pw=base_panel(540,(70,210,120))
    d.text((pw/2,70),"CHỈ CẦN CẮT 3 NHÂN SỰ",font=F(48),fill=(160,230,180,255),anchor="mm")
    d.text((pw/2,210),"TIẾT KIỆM",font=F(70),fill=(210,255,220,255),anchor="mm")
    d.rounded_rectangle([70,300,pw-70,450],radius=28,fill=(20,95,48,255))
    d.text((pw/2,375),"VÀI TRĂM TRIỆU / NĂM",font=F(74),fill=(230,255,235,255),anchor="mm")
    return im
def p_proc(n):
    im,d,pw=base_panel(620,ORANGE)
    d.text((pw/2,66),"QUY TRÌNH NỘI DUNG BẰNG AI",font=F(44),fill=(255,200,120,255),anchor="mm")
    steps=["Lên kế hoạch bài viết","Kiểm duyệt đúng chuẩn","Tự động đăng theo cấu trúc"]
    for i,st in enumerate(steps):
        y=180+i*130; on=i<n
        cc=(255,150,20,255) if on else (70,70,90,255)
        tc=(255,255,255,255) if on else (120,120,140,255)
        d.ellipse([70,y-42,154,y+42],outline=cc,width=6)
        d.text((112,y),str(i+1),font=F(52),fill=cc,anchor="mm")
        d.text((185,y),st,font=F(50),fill=tc,anchor="lm")
    return im
def p_auto():
    im,d,pw=base_panel(520,(120,120,255))
    d.text((pw/2,72),"TỰ ĐỘNG HÓA",font=F(56),fill=(180,180,255,255),anchor="mm")
    d.text((pw/2,240),"Chạy nội dung",font=F(78),fill=(255,255,255,255),anchor="mm")
    d.text((pw/2,330),"HÀNG THÁNG",font=F(96),fill=(150,170,255,255),anchor="mm")
    d.text((pw/2,450),"theo đúng ngày & giờ đã đặt",font=F(40),fill=(200,200,220,255),anchor="mm")
    return im
COST,SAVE,AUTO=p_cost(),p_save(),p_auto()
PROC=[p_proc(1),p_proc(2),p_proc(3)]

def smooth(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def uwin(t,a,b,r=0.4):
    if t<a-r or t>b+r: return 0.0
    if t<a: return smooth((t-(a-r))/r)
    if t<=b: return 1.0
    return 1-smooth((t-b)/r)
R=[(9.4,20.5,'cost'),(20.85,26.5,'save'),(39.8,61.8,'proc'),(70.8,82.9,'auto')]
def panel_at(t):
    for a,b,k in R:
        u=uwin(t,a,b)
        if u>0:
            if k=='cost': return COST,u
            if k=='save': return SAVE,u
            if k=='auto': return AUTO,u
            n=1 if t<50 else (2 if t<57 else 3); return PROC[n-1],u
    return None,0.0

BIG_W,SMALL_W=940,520
os.makedirs(f"{S}/frames_fr2",exist_ok=True)
t0=time.time()
for i in range(len(IN)):
    t=i/FPS; pnl,u=panel_at(t)
    cw=int(round(BIG_W-(BIG_W-SMALL_W)*u)); ch=int(round(cw*H/W)); cx=(W-cw)//2
    big_y=(H-int(BIG_W*H/W))//2; cy=int(round(big_y-(big_y-96)*u))
    canvas=BG.copy()
    person=Image.open(IN[i]).convert("RGB").resize((cw,ch),Image.LANCZOS)
    canvas.paste(person,(cx,cy),rmask(cw,ch,44))
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    gborder(d,[cx,cy,cx+cw-1,cy+ch-1],44,ORANGE)
    if u>0.02 and pnl is not None:
        pw,ph=pnl.size; px=(W-pw)//2; py=int(round(1770-ph-30*u))
        a=int(255*smooth(u)); pn=pnl.copy(); pn.putalpha(pn.split()[3].point(lambda v:int(v*a/255)))
        ov.alpha_composite(pn,(px,py))
    canvas=Image.alpha_composite(canvas.convert("RGBA"),ov).convert("RGB")
    canvas.save(f"{S}/frames_fr2/{i+1:05d}.jpg",quality=92)
    if i%300==0: print(i,len(IN),round(time.time()-t0),"s",flush=True)
print("FRAMED2 DONE",len(IN),round(time.time()-t0),"s")
