import sys
from PIL import Image
FEN="r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2PP1N2/PP3PPP/RNBQ1RK1"
def plateau(dossier, case, clair=(236,237,209), sombre=(120,150,90), tex=None):
    im = Image.new("RGB",(case*8,case*8))
    if tex: im.paste(Image.open(tex).convert("RGB").resize((case*8,case*8)))
    else:
        for r in range(8):
            for f in range(8):
                im.paste(clair if (r+f)%2==0 else sombre,(f*case,r*case,(f+1)*case,(r+1)*case))
    t=int(case*0.88); off=(case-t)//2
    sp={}
    for i,row in enumerate(FEN.split("/")):
        f=0
        for ch in row:
            if ch.isdigit(): f+=int(ch); continue
            nom = ch.lower()+("" if ch.isupper() else "b")
            if nom not in sp: sp[nom]=Image.open(f"{dossier}/{nom}.png").convert("RGBA").resize((t,t),Image.LANCZOS)
            im.paste(sp[nom],(f*case+off,i*case+off),sp[nom]); f+=1
    return im
if __name__=="__main__":
    d=sys.argv[1]; out=sys.argv[2]
    a=plateau(d,80); b=plateau(d,40)
    c=Image.new("RGB",(640+20+320,640),(18,18,20)); c.paste(a,(0,0)); c.paste(b,(660,0)); c.save(out)
