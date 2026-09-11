"""Original local garment illustrations. No downloaded or branded assets."""
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

COLORS = {'Black': '#30312e', 'White': '#eeede7', 'Charcoal': '#53534e', 'Cream': '#dcd6c6', 'Beige': '#c2b29a', 'Gray': '#9c9e95', 'Dark Gray': '#5c6058', 'Olive': '#757965', 'Natural': '#d1c1a3'}


def garment(category, color, index=0):
    scale = 2
    size = (600 * scale, 750 * scale)
    mask = Image.new('L', size)
    draw = ImageDraw.Draw(mask)
    def poly(points):
        draw.polygon([(int(x * scale), int(y * scale)) for x, y in points], fill=255)
    if category == 'T-Shirts':
        poly([(207,174),(162,184),(65,257),(118,354),(185,318),(190,594),(410,594),(415,318),(482,354),(535,257),(438,184),(393,174),(356,196),(244,196)])
    elif category in ['Shirts', 'Jackets', 'Hoodies']:
        poly([(213,169),(166,191),(131,254),(66,524),(135,544),(190,355),(191,594),(409,594),(410,355),(465,544),(534,524),(469,254),(434,191),(387,169),(347,187),(253,187)])
        if category == 'Hoodies':
            draw.rounded_rectangle((204*scale,116*scale,396*scale,273*scale), radius=80*scale, fill=255)
    elif category in ['Pants','Shorts']:
        bottom = 615 if category == 'Pants' else 488
        poly([(174,143),(426,143),(437,272),(430,bottom),(318,bottom),(300,340),(282,bottom),(170,bottom),(163,272)])
    elif category == 'Dresses':
        poly([(225,138),(266,145),(272,184),(328,184),(334,145),(375,138),(379,240),(355,316),(437,622),(163,622),(245,316),(221,240)])
    elif index == 19:
        draw.rounded_rectangle((165*scale,284*scale,435*scale,573*scale), radius=13*scale, fill=255)
        draw.arc((225*scale,172*scale,375*scale,416*scale),180,360,fill=255,width=19*scale)
    else:
        draw.pieslice((144*scale,237*scale,451*scale,529*scale),180,360,fill=255)
        draw.ellipse((172*scale,340*scale,480*scale,462*scale),fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(.7))
    base = Image.new('RGB', size, COLORS[color])
    pixels = base.load()
    rgb = pixels[0,0]
    # Gentle cloth texture and directional light; deterministic across seeding.
    rng = random.Random(index)
    noise = Image.new('L', (600,750))
    noise.putdata([int(128 + rng.gauss(0,5)) for _ in range(600*750)])
    noise = noise.resize(size)
    texture = Image.merge('RGB',(noise,noise,noise))
    base = ImageChops.add(base, texture, scale=1, offset=-128)
    details = Image.new('RGBA',size)
    d = ImageDraw.Draw(details)
    light = tuple(min(255,c+24) for c in rgb)+(115,)
    dark = tuple(max(0,c-33) for c in rgb)+(150,)
    def line(points,fill=dark,width=2):
        d.line([(int(x*scale),int(y*scale)) for x,y in points],fill=fill,width=max(1,width*scale),joint='curve')
    def arc(box,start,end,fill=dark,width=3):
        d.arc(tuple(int(v*scale) for v in box),start,end,fill=fill,width=width*scale)
    def rect(box,fill=None,outline=dark,width=2):
        d.rectangle(tuple(int(v*scale) for v in box),fill=fill,outline=outline,width=width*scale)
    if category == 'T-Shirts':
        arc((238,146,362,228),0,180,dark,13)
        arc((239,151,361,229),0,180,light,3)
        line([(190,574),(410,574)],dark,2)
        line([(81,277),(129,342)],light,2)
        line([(471,342),(519,277)],light,2)
        line([(190,318),(197,551)],light,2)
        line([(410,318),(403,551)],dark,2)
    elif category in ['Shirts','Jackets']:
        d.polygon([(x*scale,y*scale) for x,y in [(213,169),(268,147),(301,188),(261,238)]],fill=dark)
        d.polygon([(x*scale,y*scale) for x,y in [(387,169),(332,147),(301,188),(339,238)]],fill=light)
        line([(300,188),(300,591)],dark,4)
        line([(309,223),(309,590)],light,1)
        for y in range(255,565,55):
            d.ellipse(((297)*scale,(y-3)*scale,303*scale,(y+3)*scale),fill=dark)
        rect((333,273,388,329),outline=dark,width=2)
        if category == 'Jackets':
            rect((205,427,271,508),outline=light)
            rect((329,427,395,508),outline=light)
        line([(190,575),(410,575)],dark,2)
    elif category == 'Hoodies':
        arc((233,136,366,273),185,355,dark,10)
        line([(279,239),(274,345)],light,3)
        line([(320,239),(326,345)],light,3)
        line([(230,428),(370,428),(392,507),(210,507),(230,428)],dark,2)
        line([(193,570),(407,570)],dark,7)
        if index == 10:
            line([(300,240),(300,590)],light,3)
    elif category in ['Pants','Shorts']:
        line([(174,169),(426,169)],dark,5)
        line([(300,168),(300,290),(285,310)],dark,2)
        line([(192,169),(198,193)],dark,5)
        line([(408,169),(402,193)],dark,5)
        line([(180,185),(217,192),(194,264),(168,280)],dark,2)
        line([(420,185),(383,192),(406,264),(432,280)],dark,2)
        bottom=615 if category == 'Pants' else 488
        line([(171,bottom-18),(282,bottom-18)],dark,2)
        line([(318,bottom-18),(430,bottom-18)],dark,2)
        if index == 15:
            rect((174,326,252,414),outline=dark)
            rect((348,326,426,414),outline=dark)
            line([(174,343),(252,343)],dark,4)
            line([(348,343),(426,343)],dark,4)
    elif category == 'Dresses':
        arc((263,132,337,208),0,180,dark,3)
        line([(245,316),(355,316)],dark,2)
        for x in [240,275,325,360]:
            line([(300+(x-300)*.6,322),(x,597)],light,2)
        line([(170,603),(430,603)],dark,2)
    elif index == 19:
        rect((180,298,420,558),outline=dark,width=1)
        line([(240,286),(240,322)],dark,2)
        line([(360,286),(360,322)],dark,2)
    else:
        arc((174,254,420,468),185,290,light,2)
        line([(298,242),(310,382)],light,2)
        arc((198,351,461,447),0,170,light,2)
        d.ellipse((291*scale,231*scale,310*scale,244*scale),fill=dark)
    base = Image.alpha_composite(base.convert('RGBA'), details)
    base.putalpha(mask)
    return base.resize((600,750),Image.Resampling.LANCZOS)


def product_image(path, category, color, index):
    path.parent.mkdir(parents=True,exist_ok=True)
    canvas=Image.new('RGBA',(600,750),'#eeece5')
    cloth=garment(category,color,index)
    shadow=Image.new('RGBA',canvas.size,'#645c4c')
    shadow.putalpha(cloth.getchannel('A').filter(ImageFilter.GaussianBlur(13)).point(lambda p:int(p*.19)))
    canvas.alpha_composite(shadow,(7,15))
    canvas.alpha_composite(cloth)
    canvas.convert('RGB').save(path,quality=91,optimize=True)


def hero_image(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    canvas=Image.new('RGBA',(1000,1100),'#d4d1c6')
    # A flat-lay capsule wardrobe, using the same local illustrations as the catalog.
    looks=[('Pants','Black',13,(390,180),-12,1.30),('Shirts','Beige',7,(-30,-125),14,1.15),('T-Shirts','White',2,(-50,345),-8,1.0),('Accessories','Natural',19,(430,640),12,.7)]
    for category,color,index,pos,scale_angle,ratio in looks:
        cloth=garment(category,color,index)
        cloth=cloth.resize((int(600*ratio),int(750*ratio)),Image.Resampling.LANCZOS).rotate(scale_angle,resample=Image.Resampling.BICUBIC,expand=True)
        shadow=Image.new('RGBA',cloth.size,'#645c4c')
        shadow.putalpha(cloth.getchannel('A').filter(ImageFilter.GaussianBlur(17)).point(lambda p:int(p*.28)))
        canvas.alpha_composite(shadow,(pos[0]+14,pos[1]+18))
        canvas.alpha_composite(cloth,pos)
    canvas.convert('RGB').save(path,quality=92,optimize=True)

