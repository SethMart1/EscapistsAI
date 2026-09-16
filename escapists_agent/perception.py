"""Conservative appearance matching, with a separate fixed HUD gate.

Scores are pixel similarities, not calibrated probabilities. Identical NPCs
cannot be distinguished from the player; ambiguous scenes fail closed.
"""
import numpy as np
from .model import Observation


def match(frame, template):
    h, w = template.shape[:2]
    H, W = frame.shape[:2]
    if h > H or w > W or min(h, w) < 2:
        return None, 0.0, 0.0
    # Sparse screening followed by exact RGB comparison of the best candidates.
    score = np.zeros((H-h+1, W-w+1), dtype=np.float32)
    for y in np.linspace(0, h-1, min(h, 6), dtype=int):
        for x in np.linspace(0, w-1, min(w, 6), dtype=int):
            score += np.abs(frame[y:y+H-h+1, x:x+W-w+1].astype(np.float32)
                            - template[y, x]).mean(axis=2)
    candidates = []
    for _ in range(8):
        y, x = np.unravel_index(np.argmin(score), score.shape)
        if not np.isfinite(score[y, x]):
            break
        exact = 1 - float(np.abs(frame[y:y+h, x:x+w].astype(float) - template).mean()) / 255
        candidates.append((exact, (int(x+w//2), int(y+h//2))))
        score[max(0,y-h//2):y+h//2+1, max(0,x-w//2):x+w//2+1] = np.inf
    candidates.sort(reverse=True)
    return candidates[0][1], candidates[0][0], candidates[1][0] if len(candidates)>1 else 0


class TemplatePerception:
    def __init__(self, profile, player, hud):
        self.profile, self.player, self.hud = profile, player, hud

    def observe(self, frame, timestamp):
        p = self.profile
        def unknown(reason, confidence=0):
            return Observation(timestamp, None, confidence, 'unknown', reason)
        if list(frame.shape[:2]) != p['shape']:
            return unknown('Window size changed; recalibrate')
        if frame.std() < 3:
            return unknown('Blank or uniform capture')
        x,y,w,h = p['hud_box']
        hud_score = 1-float(np.abs(frame[y:y+h,x:x+w].astype(float)-self.hud).mean())/255
        if hud_score < p['hud_threshold']:
            return unknown('Gameplay HUD not recognized')
        x,y,w,h = p['search_box']
        center, confidence, runner_up = match(frame[y:y+h,x:x+w], self.player)
        if confidence < p['player_threshold']:
            return unknown('Player appearance not recognized', confidence)
        if confidence-runner_up < p['ambiguity_margin']:
            return unknown('Ambiguous player/NPC match', confidence)
        return Observation(timestamp, (center[0]+x,center[1]+y), confidence,
                           'gameplay', 'Player and HUD recognized')
