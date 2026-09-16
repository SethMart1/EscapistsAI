import argparse
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image
from .perception import TemplatePerception
from .planning import WaypointPolicy
from .telemetry import Recorder


def main():
    parser=argparse.ArgumentParser(description='Screen-only Escapists MVP; observation by default')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('windows',help='List exact visible window titles')
    demo=sub.add_parser('demo',help='Synthetic closed-loop navigation; never sends input')
    demo.add_argument('--output',default='runs/demo')
    capture=sub.add_parser('capture')
    capture.add_argument('--title',default='The Escapists')
    capture.add_argument('--output',default='runs/capture.png')
    capture.add_argument('--delay',type=float,default=5)
    calibration=sub.add_parser('calibrate')
    calibration.add_argument('image'); calibration.add_argument('--profile',default='profiles/local')
    run=sub.add_parser('run')
    run.add_argument('--title',default='The Escapists')
    run.add_argument('--profile',default='profiles/local')
    run.add_argument('--output',default='runs/live')
    run.add_argument('--seconds',type=float,default=20)
    run.add_argument('--delay',type=float,default=5)
    run.add_argument('--arm',action='store_true',help='Enable bounded WASD movement')
    args=parser.parse_args()
    if args.command=='demo':
        from .demo import run as demo_run
        print(demo_run(args.output)); return
    if args.command=='calibrate':
        from .calibration import calibrate
        calibrate(args.image,args.profile); return
    from .windows import Windows, InputController
    windows=Windows()
    if args.command=='windows':
        available=windows.windows()
        for hwnd,title in available: print(f'{hwnd}: {title}')
        if not available:
            print('No desktop windows are accessible. Run Launch.cmd directly on your desktop.')
        return
    if not 0<=args.delay<=60: parser.error('--delay must be between 0 and 60')
    hwnd=windows.find(args.title)
    if args.command=='capture':
        print(f'Focus the game within {args.delay:g} seconds.'); time.sleep(args.delay)
        frame=windows.capture(hwnd)
        path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(frame).save(path); print(path); return
    if not 0<args.seconds<=120: parser.error('--seconds must be between 0 and 120')
    directory=Path(args.profile)
    profile=json.loads((directory/'profile.json').read_text())
    player=np.array(Image.open(directory/'player.png').convert('RGB'))
    hud=np.array(Image.open(directory/'hud.png').convert('RGB'))
    detector=TemplatePerception(profile,player,hud)
    policy=WaypointPolicy(profile['waypoints'])
    log=Recorder(args.output)
    controller=InputController(windows,hwnd,args.arm,Path('STOP'))
    mode='armed' if args.arm else 'observe'
    print(f'{mode}: focus game within {args.delay:g}s. F8 or STOP file stops. Logs: {log.path}')
    try:
        time.sleep(args.delay)
        deadline=time.monotonic()+args.seconds
        while time.monotonic()<deadline:
            if not controller.safe(): raise RuntimeError('Focus lost or emergency stop')
            timestamp=time.monotonic(); frame=windows.capture(hwnd)
            observation=detector.observe(frame,timestamp)
            action=policy.decide(observation)
            log.record(frame,observation,action,mode)
            if args.arm and observation.state!='gameplay':
                raise RuntimeError(observation.reason)
            controller.perform(action,timestamp)
            log.event({'execution':'sent' if args.arm and action.key else 'no_input'})
            if policy.index>=len(policy.waypoints) or policy.stalled>=5: break
            time.sleep(0.1)
        log.event({'result':'stopped','waypoints_reached':policy.index})
    except BaseException as exc:
        log.event({'error':str(exc),'type':type(exc).__name__})
        raise
    finally:
        try: controller.release()
        finally: log.close()


if __name__=='__main__':
    try: main()
    except (RuntimeError,ValueError,FileNotFoundError,KeyError) as exc:
        raise SystemExit(f'Agent stopped: {exc}')
