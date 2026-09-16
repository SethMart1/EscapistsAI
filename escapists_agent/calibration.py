import json
from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk


def calibrate(image_path, destination):
    image = Image.open(image_path).convert('RGB')
    root = tk.Tk()
    root.title('Escapists calibration — drag rectangles, then click waypoints')
    scale = min(1, 1100/image.width, 700/image.height)
    preview = ImageTk.PhotoImage(image.resize((int(image.width*scale),int(image.height*scale))))
    label = tk.Label(root, text='', font=('Arial',12))
    label.pack()
    canvas = tk.Canvas(root,width=preview.width(),height=preview.height())
    canvas.pack()
    canvas.create_image(0,0,anchor='nw',image=preview)
    prompts = ['Drag tightly around YOUR player (exclude name text).',
               'Drag a distinctive, static gameplay HUD icon (avoid changing numbers).',
               'Drag the playable area to search for the player (exclude HUD).',
               'Click nearby clear-ground waypoints. Click Save when finished.']
    boxes, points = [], []
    start = [0,0]
    def prompt(): label.config(text=prompts[min(len(boxes),3)])
    def down(event): start[:] = [event.x,event.y]
    def up(event):
        if len(boxes)<3:
            x1,x2=sorted((start[0],event.x)); y1,y2=sorted((start[1],event.y))
            x,y=int(x1/scale),int(y1/scale)
            w,h=int((x2-x1)/scale),int((y2-y1)/scale)
            if min(w,h)<3 or x<0 or y<0 or x+w>image.width or y+h>image.height:
                return
            boxes.append([x,y,w,h])
            canvas.create_rectangle(x1,y1,x2,y2,outline='lime',width=2)
        else:
            x,y=int(event.x/scale),int(event.y/scale)
            sx,sy,sw,sh=boxes[2]
            if not (sx<=x<sx+sw and sy<=y<sy+sh): return
            points.append([x,y])
            canvas.create_oval(event.x-4,event.y-4,event.x+4,event.y+4,fill='cyan')
        prompt()
    def save():
        if len(boxes)!=3 or not points:
            label.config(text='Select all three rectangles and at least one waypoint first.'); return
        out=Path(destination); out.mkdir(parents=True,exist_ok=True)
        for name,box in zip(('player','hud'),boxes):
            x,y,w,h=box; image.crop((x,y,x+w,y+h)).save(out/f'{name}.png')
        profile={'shape':[image.height,image.width], 'hud_box':boxes[1],
                 'search_box':boxes[2], 'waypoints':points, 'player_threshold':0.94,
                 'hud_threshold':0.98, 'ambiguity_margin':0.03}
        (out/'profile.json').write_text(json.dumps(profile,indent=2))
        root.destroy()
    canvas.bind('<ButtonPress-1>',down); canvas.bind('<ButtonRelease-1>',up)
    tk.Button(root,text='Save profile',command=save).pack()
    prompt(); root.mainloop()
