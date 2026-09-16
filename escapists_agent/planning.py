from .model import Action


class WaypointPolicy:
    """Local screen-coordinate navigation. No inferred obstacle or world map."""
    def __init__(self, waypoints, tolerance=8):
        self.waypoints = [tuple(p) for p in waypoints]
        self.index = 0
        self.tolerance = tolerance
        self.last_position = None
        self.stalled = 0
        self.reason = ''

    def decide(self, observation):
        if observation.state != 'gameplay' or observation.player is None:
            return Action(None, 0, observation.reason)
        if self.index >= len(self.waypoints):
            return Action(None, 0, 'Route complete')
        x,y = observation.player
        if self.last_position is not None:
            distance = abs(x-self.last_position[0])+abs(y-self.last_position[1])
            self.stalled = self.stalled+1 if distance < 2 else 0
        self.last_position = (x,y)
        if self.stalled >= 5:
            return Action(None, 0, 'No visible progress; stop and inspect collision/camera')
        tx,ty = self.waypoints[self.index]
        dx,dy = tx-x,ty-y
        if abs(dx)<=self.tolerance and abs(dy)<=self.tolerance:
            self.index += 1
            return Action(None, 0, 'Waypoint reached')
        key = ('d' if dx>0 else 'a') if abs(dx)>abs(dy) else ('s' if dy>0 else 'w')
        return Action(key, 0.08, 'Move toward local waypoint')
