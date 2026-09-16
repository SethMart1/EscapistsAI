import numpy as np
from .perception import TemplatePerception
from .planning import WaypointPolicy
from .telemetry import Recorder


def scene(player, hud, position):
    image=np.full((180,300,3),(55,72,55),dtype=np.uint8)
    image[8:20,8:32]=hud
    x,y=position
    image[y-8:y+8,x-6:x+6]=player
    return image


def run(directory):
    rng=np.random.default_rng(7)
    player=rng.integers(40,240,(16,12,3),dtype=np.uint8)
    hud=rng.integers(0,255,(12,24,3),dtype=np.uint8)
    profile={'shape':[180,300],'hud_box':[8,8,24,12],'search_box':[0,35,300,145],
             'player_threshold':0.94,'hud_threshold':0.98,'ambiguity_margin':0.03}
    detector=TemplatePerception(profile,player,hud)
    policy=WaypointPolicy([(160,90),(160,140)])
    position=[80,90]; log=Recorder(directory)
    try:
        for i in range(100):
            frame=scene(player,hud,position)
            obs=detector.observe(frame,float(i))
            action=policy.decide(obs)
            log.record(frame,obs,action,'simulation')
            if policy.index==len(policy.waypoints): break
            if action.key:
                dx,dy={'w':(0,-4),'s':(0,4),'a':(-4,0),'d':(4,0)}[action.key]
                position[0]+=dx; position[1]+=dy
        if policy.index!=2: raise RuntimeError('Demo did not reach both waypoints')
        log.event({'result':'success','waypoints_reached':2})
    finally: log.close()
    return log.path
