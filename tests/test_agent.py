import time
import unittest
from unittest.mock import Mock
import numpy as np
from escapists_agent.demo import scene
from escapists_agent.perception import TemplatePerception
from escapists_agent.planning import WaypointPolicy
from escapists_agent.model import Action, Observation
from escapists_agent.windows import InputController, INPUT
import ctypes


class PerceptionTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(7)
        self.player=rng.integers(40,240,(16,12,3),dtype=np.uint8)
        self.hud=rng.integers(0,255,(12,24,3),dtype=np.uint8)
        self.profile={'shape':[180,300],'hud_box':[8,8,24,12],'search_box':[0,35,300,145],
                      'player_threshold':0.94,'hud_threshold':0.98,'ambiguity_margin':0.03}
        self.detector=TemplatePerception(self.profile,self.player,self.hud)
        self.frame=scene(self.player,self.hud,[80,90])

    def test_find_player(self):
        result=self.detector.observe(self.frame,0)
        self.assertEqual(result.player,(80,90))
        self.assertEqual(result.state,'gameplay')

    def test_identical_npc_rejected(self):
        self.frame[92:108,144:156]=self.player
        self.assertEqual(self.detector.observe(self.frame,0).state,'unknown')

    def test_menu_rejected(self):
        self.frame[8:20,8:32]=0
        self.assertEqual(self.detector.observe(self.frame,0).state,'unknown')

    def test_missing_player_rejected(self):
        self.frame[82:98,74:86]=55
        self.assertEqual(self.detector.observe(self.frame,0).state,'unknown')

    def test_resize_rejected(self):
        self.assertEqual(self.detector.observe(self.frame[:100],0).state,'unknown')


class PlanningTests(unittest.TestCase):
    def test_obstacle_stops(self):
        policy=WaypointPolicy([(100,100)])
        obs=Observation(0,(20,20),1,'gameplay','')
        for _ in range(6): action=policy.decide(obs)
        self.assertIsNone(action.key)
        self.assertIn('No visible progress',action.reason)

    def test_unknown_stops(self):
        action=WaypointPolicy([(100,100)]).decide(Observation(0,None,0,'unknown','menu'))
        self.assertIsNone(action.key)

    def test_route_completes(self):
        policy=WaypointPolicy([(20,20)])
        self.assertIsNone(policy.decide(Observation(0,(20,20),1,'gameplay','')).key)
        self.assertEqual(policy.index,1)


class InputTests(unittest.TestCase):
    def setUp(self):
        self.windows=Mock()
        self.windows.ready.return_value=True
        self.windows.stop_pressed.return_value=False
        self.controller=InputController(self.windows,1,True)
        self.controller.send=Mock()

    def test_dry_run_never_sends(self):
        self.controller.armed=False
        self.controller.perform(Action('w',0.01,''),time.monotonic())
        self.controller.send.assert_not_called()

    def test_stale_never_sends(self):
        with self.assertRaises(RuntimeError): self.controller.perform(Action('w',0.01,''),time.monotonic()-2)
        self.controller.send.assert_not_called()

    def test_focus_loss_releases_key(self):
        self.windows.ready.side_effect=[True,False]
        with self.assertRaises(RuntimeError): self.controller.perform(Action('w',0.1,''),time.monotonic())
        self.assertEqual(self.controller.send.call_args_list,[(('w',False),),(('w',True),)])
        self.assertFalse(self.controller.held)

    def test_f8_never_sends(self):
        self.windows.stop_pressed.return_value=True
        with self.assertRaises(RuntimeError): self.controller.perform(Action('w',0.01,''),time.monotonic())
        self.controller.send.assert_not_called()

    def test_long_hold_rejected(self):
        with self.assertRaises(RuntimeError): self.controller.perform(Action('w',1,''),time.monotonic())
        self.controller.send.assert_not_called()

    def test_non_movement_key_rejected(self):
        with self.assertRaises(RuntimeError): self.controller.perform(Action('enter',0.01,''),time.monotonic())
        self.controller.send.assert_not_called()

    def test_windows_input_size(self):
        self.assertEqual(ctypes.sizeof(INPUT),40 if ctypes.sizeof(ctypes.c_void_p)==8 else 28)


if __name__=='__main__': unittest.main()
