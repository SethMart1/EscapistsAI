import json
import time
from pathlib import Path
from dataclasses import asdict
from PIL import Image, ImageDraw


class Recorder:
    def __init__(self, directory):
        self.path = Path(directory)/time.strftime('%Y%m%d-%H%M%S')
        self.path.mkdir(parents=True,exist_ok=False)
        self.file = (self.path/'events.jsonl').open('w',encoding='utf-8')
        self.index=0

    def record(self, frame, observation, action, mode):
        stem=f'{self.index:05d}'
        Image.fromarray(frame).save(self.path/f'{stem}-raw.png')
        image=Image.fromarray(frame); draw=ImageDraw.Draw(image)
        if observation.player:
            x,y=observation.player; draw.ellipse((x-10,y-10,x+10,y+10),outline='lime',width=2)
        draw.rectangle((0,0,image.width,32),fill='black')
        draw.text((4,3),f'{mode} | {observation.state} {observation.confidence:.3f} | {action.key}',fill='white')
        draw.text((4,17),action.reason,fill='white')
        image.save(self.path/f'{stem}-debug.png')
        self.event({'frame':stem,'observation':asdict(observation),'action':asdict(action),'mode':mode})
        self.index+=1

    def event(self, data):
        self.file.write(json.dumps(data)+'\n'); self.file.flush()

    def close(self): self.file.close()
