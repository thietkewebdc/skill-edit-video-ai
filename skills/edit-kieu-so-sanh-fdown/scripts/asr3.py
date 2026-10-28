import sys, json, subprocess, numpy as np, time, re
from faster_whisper import WhisperModel
wav, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg","-v","error","-i",wav,"-af","highpass=f=80,dynaudnorm=f=150:g=15","-f","f32le","-ac","1","-ar","16000","-"],capture_output=True).stdout
a = np.frombuffer(raw, np.float32); SR=16000
raw0 = subprocess.run(["ffmpeg","-v","error","-i",wav,"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True).stdout
a0 = np.frombuffer(raw0, np.float32)
hop=320; n=len(a0)//hop
env=np.sqrt((a0[:n*hop].reshape(n,hop)**2).mean(1)+1e-12)
db=20*np.log10(env+1e-9)
thr=np.percentile(db,10)+(np.percentile(db,90)-np.percentile(db,10))*0.30
quiet=db<thr
cuts=[];i=0
while i<n:
    if quiet[i]:
        j=i
        while j<n and quiet[j]: j+=1
        if (j-i)*0.02>=0.25: cuts.append(((i+j)/2)*0.02)
        i=j
    else: i+=1
total=len(a)/SR
blocks=[];start=0.0;last=0.0
for c in cuts+[total]:
    if c-start>12 and last>start:
        blocks.append((start,last)); start=last
    last=c
blocks.append((start,total))
BAD=re.compile(r"subscribe|đăng ký kênh|ghiền mì|ủng hộ kênh|hẹn gặp lại|cảm ơn các bạn đã", re.I)
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
words=[]; t0=time.time()
for bi,(s,e) in enumerate(blocks):
    s2=max(0,s-0.2); e2=min(total,e+0.2)
    seg=a[int(s2*SR):int(e2*SR)]
    if len(seg)<SR*0.5: continue
    segs,_=m.transcribe(seg,language="vi",vad_filter=False,beam_size=5,condition_on_previous_text=False,
        temperature=[0.0,0.2,0.4],compression_ratio_threshold=2.0,no_speech_threshold=0.6,log_prob_threshold=-1.0,word_timestamps=True)
    for sg in segs:
        if BAD.search(sg.text) and sg.no_speech_prob>0.2: continue
        if sg.no_speech_prob>0.8: continue
        for w in sg.words:
            words.append({"w":w.word.strip(),"s":round(s2+w.start,2),"e":round(s2+w.end,2)})
    print(f"khối {bi+1}/{len(blocks)} {s:.1f}-{e:.1f}s",flush=True)
json.dump({"words":words,"blocks":blocks},open(out,"w"),ensure_ascii=False)
print(wav,"xong",len(words),"từ",round(time.time()-t0),"s")
