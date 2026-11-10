import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
def tech(text):
    # Angular stencil numerals and variant letters, matching the reference hierarchy.
    w,h,t,gap=86,120,19,7
    out=Image.new('L',(len(text)*(w+gap),h+10));d=ImageDraw.Draw(out)
    bars={
      'a':[(t,0),(w-t,0),(w-3,t),(3,t)],
      'b':[(w-t,7),(w,0),(w,53),(w-t,62)],
      'c':[(w-t,62),(w,54),(w,h),(w-t,h-8)],
      'd':[(3,h-t),(w-3,h-t),(w-t,h),(t,h)],
      'e':[(0,62),(t,55),(t,h-8),(0,h)],
      'f':[(0,0),(t,7),(t,61),(0,54)],
      'g':[(t,51),(w-t,51),(w-3,60),(w-t,69),(t,69),(3,60)],
    }
    codes={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','S':'afgcd','5':'afgcd','6':'afgecd','9':'afbgcd'}
    for i,c in enumerate(text):
        x=i*(w+gap)
        if c in codes:
            for b in codes[c]:d.polygon([(u+x,v+5) for u,v in bars[b]],fill=255)
        elif c=='M':
            d.polygon([(x,5),(x+t,5),(x+w//2,52),(x+w-t,5),(x+w,5),(x+w,125),(x+w-t,125),(x+w-t,43),(x+w//2,85),(x+t,43),(x+t,125),(x,125)],fill=255)
        else:d.text((x,0),c,font=ImageFont.truetype('C:/Windows/Fonts/ARIALNB.TTF',120),fill=255)
        if c=='0':d.line([(x+17,113),(x+w-17,15)],fill=255,width=10)
    return out

def text_mask(text,w,h,angle,style,hatched):
    if style=='tech':im=tech(text)
    else:
        font=ImageFont.truetype('C:/Windows/Fonts/ARIALNB.TTF',150)
        temp=ImageDraw.Draw(Image.new('L',(1,1)));b=temp.multiline_textbbox((0,0),text,font=font,spacing=1,align='center')
        im=Image.new('L',(int(np.ceil(b[2]-b[0]+8)),int(np.ceil(b[3]-b[1]+8))))
        ImageDraw.Draw(im).multiline_text((4-b[0],4-b[1]),text,font=font,fill=255,spacing=1,align='center')
    # Reference lettering is condensed and gently slanted, rather than plain upright text.
    a=np.array(im);shear=.10 if style=='tech' else .055
    im=Image.fromarray(cv2.warpAffine(a,np.array([[1,-shear,shear*a.shape[0]],[0,1,0]],np.float32),(int(a.shape[1]+shear*a.shape[0]),a.shape[0]),flags=cv2.INTER_CUBIC))
    im=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    if style=='tech':im=im.resize((max(1,w-4),max(1,h-4)),Image.Resampling.LANCZOS)
    else:im.thumbnail((max(1,w-4),max(1,h-4)),Image.Resampling.LANCZOS)
    out=np.zeros((h,w),np.uint8);px=(w-im.width)//2;py=(h-im.height)//2;out[py:py+im.height,px:px+im.width]=im
    if hatched:
        yy,xx=np.indices(out.shape)
        period=4 if hatched=='vertical' else 6
        out[((xx if hatched=='vertical' else xx+yy)%period)>=2]=0
    return out

