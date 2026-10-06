from __future__ import annotations

import json
import math
import os
import random
import signal
import subprocess
import time
from pathlib import Path

from .nervous import Event
from .cell import Cell
from actions.safe import SafeActions
from perception.sight_focus import set_focus
from cognition.v1 import V1World
from .habitat import DigitalHabitat

ROOT = Path('/mnt/gai')
MOTOR = ROOT / 'state/motor_output.json'
PROPRIO = ROOT / 'state/proprioception.json'
OUTPUT_CTRL = ROOT / 'state/output_windows.json'
OUTPUT_PID = ROOT / 'state/output_windows.pid'
TOY_PIDS = ROOT / 'state/toy_pids.json'
INTERACTION = ROOT / 'state/toy_interaction.json'


class MotorActionCentre(Cell):
    """Low-level body/action centre between CC and G.A.I.'s organs.

    CC proposes intentions. This centre converts them into bounded motor/output
    commands. It can also generate ordinary body movement from drives and sensory
    state without language-model involvement.
    """
    def __init__(self, kernel):
        super().__init__('motor_action', kernel.nervous, version='1.0.0',
                         sleep_phases={'awake'}, critical=True)
        self.kernel = kernel
        self.actions = SafeActions()
        self.last_intention = None
        self.last_move = 0.0
        self.phase = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.novelty = 0.0
        self.sound = 0.0
        self.proprio = {}
        self.last_primitive = None
        self.output_started = False
        self.test_mode = self.kernel._lock_file is None
        self._last_toy_check = 0.0
        self.listen('cognition.intention', self.receive_intention, {'awake'})
        self.listen('drive.update', self.receive_drive, {'awake'})
        self.listen('perception.observation', self.receive_perception, {'awake'})
        self.listen('prediction.error', self.receive_prediction, {'awake'})
        self.listen('motor.proprioception', self.receive_proprioception, {'awake'})
        self.nervous.register_component('motor_action', kind='motor', version='1.0.0',
                                        sleep_capable=True, critical=True)
        if not self.test_mode:
            self._ensure_toys(True)
            if not bool(self.kernel.cfg.get('v1_mode', False)):
                self.start_background()

    def start_background(self):
        import threading
        threading.Thread(target=self._body_loop, daemon=True,
                         name='gai-motor-centre').start()

    def _ensure_toys(self, active: bool):
        # V1 phenotype is one bubble. Capability apps are optional external toys,
        # never part of the organism's visible identity.
        if not active:
            self._stop_toys()
            return
        TOY_PIDS.parent.mkdir(parents=True, exist_ok=True)
        pid = None
        try:
            pid = int(OUTPUT_PID.read_text().strip())
            os.kill(pid, 0)
        except Exception:
            pid = None
        if pid is None:
            env = dict(os.environ)
            env.setdefault('DISPLAY', ':0')
            env.setdefault('XAUTHORITY', '/home/null/.Xauthority')
            proc = subprocess.Popen([str(ROOT/'venvs/gai/bin/python'), str(ROOT/'agent/gui/toy_app.py')],
                                    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    start_new_session=True)
            OUTPUT_PID.write_text(str(proc.pid))
        TOY_PIDS.write_text(json.dumps({'suite': int(OUTPUT_PID.read_text().strip())}))
        self.output_started = True

    def _stop_toys(self):
        pids=json.loads(TOY_PIDS.read_text()) if TOY_PIDS.exists() else {}
        for pid in pids.values():
            try: os.kill(int(pid),signal.SIGTERM)
            except Exception: pass
        try: TOY_PIDS.unlink()
        except FileNotFoundError: pass
        try:
            pid=int(OUTPUT_PID.read_text().strip()); os.kill(pid,signal.SIGTERM)
        except Exception: pass
        try: OUTPUT_PID.unlink()
        except FileNotFoundError: pass
        self.output_started=False; self.test_mode=self.kernel._lock_file is None

    def close(self):
        self._stop_toys()
        try:
            self.heartbeat('stopped')
        except Exception:
            pass

    def receive_drive(self, event: Event):
        p = event.payload or {}
        self.novelty = max(0.0, min(1.0, float(p.get('curiosity', 0.0))))
        self.heartbeat({'novelty_pressure': self.novelty})

    def receive_prediction(self, event: Event):
        self.novelty = max(self.novelty, min(1.0, float((event.payload or {}).get('value', 0.0))))

    def receive_perception(self, event: Event):
        if not self.test_mode and time.monotonic() - self._last_toy_check >= 5.0:
            self._last_toy_check = time.monotonic()
            self._ensure_toys(True)
        try:
            senses = ((event.payload or {}).get('perception') or {}).get('senses') or {}
            audio = senses.get('audio') or {}
            self.sound = max(0.0, min(1.0, float(audio.get('rms', 0.0)) * 12.0))
        except Exception:
            self.sound = 0.0
        self.proprio = {}
        self.last_primitive = None

    def receive_proprioception(self, event: Event):
        self.proprio = dict(event.payload or {})
        self.heartbeat({'proprioception': self.proprio})

    def _read_proprioception(self):
        try:
            self.proprio = json.loads(PROPRIO.read_text())
        except Exception:
            pass
        return self.proprio

    def _update_hands(self):
        """Two small contact organs around the body; touch is derived from proximity."""
        try:
            p = self._read_proprioception()
            sw = float(p.get('screen_width', 1920)); sh = float(p.get('screen_height', 1080))
            cx = float(p.get('x', sw / 2)) + float(p.get('width', 260)) / 2
            cy = float(p.get('y', sh / 2)) + float(p.get('height', 250)) / 2
            world = getattr(getattr(self.kernel, 'v1_brain', None), 'world', None) or V1World()
            tx, ty = world.target_px(sw, sh)
            hands = {
                'timestamp': time.time(),
                'left': {'x': cx - 125.0, 'y': cy + 18.0},
                'right': {'x': cx + 125.0, 'y': cy + 18.0},
                'contact': False,
                'target': world.state['object']['id'],
            }
            for hand in ('left', 'right'):
                h = hands[hand]
                h['distance_px'] = round(math.hypot(tx-h['x'], ty-h['y']), 1)
                h['contact'] = h['distance_px'] <= 105.0
                hands['contact'] = hands['contact'] or h['contact']
            (ROOT / 'state/hands.json').write_text(json.dumps(hands, separators=(',', ':')))
            return hands
        except Exception:
            return {}

    def execute_primitive(self, primitive, target=None, reason='primitive'):
        target = target if isinstance(target, dict) else {}
        primitive = str(primitive or '').lower()
        self.last_primitive = primitive
        if primitive in {'move', 'wander'}:
            result = self._command_move(target or {'dx': random.uniform(-80,80), 'dy': random.uniform(-50,50), 'duration': .5}, reason=reason)
            self._update_hands()
            return result
        if primitive in {'orient', 'look_at', 'gaze'}:
            tx=str(target.get('mode',target.get('target','in'))).lower()
            mode='out' if tx in {'out','world','real_world','external','camera'} else 'in'
            x=float(target.get('x',0.5)); y=float(target.get('y',0.18 if mode=='out' else 0.78))
            radius=float(target.get('radius',0.14))
            set_focus(mode=mode,x=x,y=y,radius=radius,target=target.get('target',mode),reason=reason)
            self.nervous.publish('motor.look', {'target': target, 'primitive': primitive, 'reason': reason, 'focus_mode': mode},
                                 source='motor_action', priority='control')
            return True
        if primitive == 'approach':
            p = self._read_proprioception()
            tx, ty = float(target.get('x', p.get('screen_center_x', 960))), float(target.get('y', p.get('screen_center_y', 540)))
            x, y = float(p.get('x', tx)), float(p.get('y', ty))
            return self._command_move({'dx': (tx-x)*.25, 'dy': (ty-y)*.25, 'duration': .5}, reason=reason)
        if primitive == 'retreat':
            p = self._read_proprioception()
            x, y = float(p.get('x', 960)), float(p.get('y', 540))
            return self._command_move({'dx': (x-960)*.2 or random.choice([-80,80]), 'dy': (y-540)*.2 or random.choice([-50,50]), 'duration': .5}, reason=reason)
        if primitive == 'gesture':
            return self._command_move({'dx': random.uniform(-35,35), 'dy': random.uniform(-25,25), 'duration': .3}, reason=reason)
        if primitive == 'interact':
            self._update_hands()
            p = self._read_proprioception()
            sw = float(p.get('screen_width', p.get('screen_center_x', 1920) * 2))
            sh = float(p.get('screen_height', p.get('screen_center_y', 1080) * 2))
            world = getattr(getattr(self.kernel, 'v1_brain', None), 'world', None) or V1World()
            tx, ty = world.target_px(sw, sh)
            x = float(p.get('x', p.get('screen_center_x', sw / 2)))
            y = float(p.get('y', p.get('screen_center_y', sh / 2)))
            distance = math.hypot(tx - x, ty - y)
            habitat = DigitalHabitat()
            object_id = str(target.get('object') or world.state.get('object', {}).get('id', 'curiosity_object'))
            if distance <= 120.0 and object_id != 'curiosity_object':
                result = habitat.interact(object_id)
            else:
                result = world.interact(distance=distance)
                if isinstance(result, dict) and result.get('outcome'):
                    result['habitat_object'] = object_id
            if isinstance(result, dict) and bool(result.get('success') or (result.get('outcome') or {}).get('success')):
                try:
                    self.kernel.core_needs.register_social(1.0)
                except Exception:
                    pass
            self._set_interaction('curiosity_object', action='touch')
            self.nervous.publish(
                'environment.outcome',
                result,
                source='environment',
                priority='control'
            )
            return result
        if primitive == 'wait':
            return True
        if primitive == 'rest':
            self.nervous.publish('motor.posture', {'mode':'rest'}, source='motor_action', priority='control')
            try:
                self.kernel.core_needs.register_rest(1.0)
                self.kernel.state.fatigue = max(0.0, float(self.kernel.state.fatigue) - 0.08)
            except Exception:
                pass
            return True
        if primitive == 'vocalize':
            from perception.output_audio import emit_affect
            emotions = getattr(self.kernel.motivation, 'emotions', None)
            state = self.kernel.state
            if isinstance(target, dict) and target.get('emotion'):
                emotion = str(target.get('emotion'))
            else:
                candidates = {
                    'fear': float(getattr(emotions, 'fear', 0.0) if emotions else 0.0),
                    'stress': float(getattr(emotions, 'stress', 0.0) if emotions else 0.0),
                    'happiness': max(0.0, float(getattr(state, 'happiness', 0.0))),
                    'curiosity': float(getattr(state, 'curiosity', 0.0)),
                    'fatigue': float(getattr(state, 'fatigue', 0.0)),
                    'boredom': float(getattr(state, 'boredom', 0.0)),
                }
                emotion = max(candidates, key=candidates.get)
            speech_text = ''
            organ_result = emit_affect(emotion, 'vocalize', text=speech_text)
            result = {
                'success': True,
                'submitted': True,
                'organ': 'speaker',
                'organ_result': organ_result,
            }
            self.nervous.publish('organ.vocalization', {
                'emotion': emotion, 'result': result, 'timestamp': time.time()
            }, source='motor_action', priority='normal')
            return result
        if primitive == 'display':
            return self._command_output(target, reason=reason)
        if primitive in {'create', 'tool_use'}:
            self._create_artifact(target.get('kind','create_text'), target, target.get('thought',''))
            return True
        return False

    def receive_intention(self, event: Event):
        p = event.payload or {}
        intention = p.get('intention') if isinstance(p.get('intention'), dict) else {}
        kind = str(intention.get('type', 'none'))
        target = intention.get('target') if isinstance(intention.get('target'), dict) else {}
        cycle_id = p.get('cycle_id')
        self.last_intention = {
            'type': kind,
            'target': target,
            'reason': intention.get('reason', ''),
            'cycle_id': cycle_id,
            'thought': str(p.get('thought', '') or ''),
            'timestamp': time.time()
        }

        # Speech is an output stream of the organism, not a separate GUI organ.
        # Keep it independent from ordinary thought so a vocalization remains
        # visible for its short display lifetime instead of being overwritten by
        # the next internal action.
        thought = str(p.get('thought', '') or '')
        result = False
        if kind in {'move','orient','approach','look_at','gaze','gesture','wander','retreat','rest','wait','interact','vocalize','display','create','tool_use'}:
            primitive = kind
            result = self.execute_primitive(primitive, target, reason='cognitive_goal')
        elif kind == 'look':
            result = self.execute_primitive('orient', target, reason='cognitive_goal')
        elif kind == 'output':
            result = self._command_output(target, reason='cognitive_goal')
        elif kind in {'create_text', 'create_image', 'paint'}:
            result = self._create_artifact(kind, target, p.get('thought', ''))
        elif kind == 'maintain':
            self.nervous.publish('motor.posture', {'mode': kind}, source='motor_action', priority='control')
            result = True

        executed = result is not False
        self.kernel.state.mode = kind
        self.kernel.last_action = {
            'type': kind,
            'reason': intention.get('reason', ''),
            'cycle_id': cycle_id,
            'executed': executed,
            'result': result if isinstance(result, dict) else {'success': bool(executed)},
        }
        payload = {
            'cycle_id': cycle_id,
            'action': kind,
            'executed': executed,
            'target': target,
            'result': result if isinstance(result, dict) else {'success': bool(executed)},
            'reason': intention.get('reason', ''),
        }
        self.nervous.publish(
            'action.completed',
            payload,
            source='motor_action',
            priority='normal',
            correlation_id=event.correlation_id
        )
        if bool(self.kernel.cfg.get('v1_mode', False)) and hasattr(self.kernel, 'v1_brain'):
            try:
                self.kernel.v1_brain.record_outcome(payload.get('result', {}))
            except Exception as exc:
                self.nervous.publish('v1.trace.error', {'error': str(exc)}, source='motor_action', priority='background')
            self.nervous.publish('memory.enqueued', {
                'stimuli': ['v1', kind, str((target or {}).get('object', 'curiosity_object'))],
                'reward': self.kernel.latest_reward,
                'prediction_error': self.kernel.latest_prediction_error,
                'action': self.kernel.last_action,
                'context': p.get('context', []),
            }, source='experience', priority='background', correlation_id=event.correlation_id, provenance='experience')
        self.heartbeat({'last_intention': kind, 'executed': executed})
    def _command_move(self, target, reason='motor'):
        try:
            dx = max(-500.0, min(500.0, float(target.get('dx', 0))))
            dy = max(-300.0, min(300.0, float(target.get('dy', 0))))
            duration = max(0.05, min(4.0, float(target.get('duration', 0.5))))
        except (TypeError, ValueError):
            return
        payload = {'timestamp': time.time(), 'action': 'move', 'dx': dx, 'dy': dy,
                   'duration': duration, 'reason': reason, 'source': 'motor_action'}
        MOTOR.parent.mkdir(parents=True, exist_ok=True)
        MOTOR.write_text(json.dumps(payload, separators=(',', ':')))
        self.nervous.publish('motor.command', payload, source='motor_action', priority='control')

    def _set_interaction(self, tool, action='use'):
        payload = {'tool': str(tool), 'action': str(action), 'timestamp': time.time(), 'active': True}
        INTERACTION.parent.mkdir(parents=True, exist_ok=True)
        INTERACTION.write_text(json.dumps(payload, separators=(',', ':')))
        self.nervous.publish('toy.interaction', payload, source='motor_action', priority='normal')

    def _command_output(self, target, reason='motor'):
        allowed = {'view', 'thought', 'text', 'pixels'}
        windows = target.get('windows', []) if isinstance(target, dict) else []
        if isinstance(windows, str):
            windows = [windows]
        windows = [w for w in windows if w in allowed]
        if not windows:
            windows = [str(target.get('window'))] if target.get('window') in allowed else ['thought']
        try:
            current = json.loads(OUTPUT_CTRL.read_text())
        except Exception:
            current = {}
        for w in windows:
            spec = dict(current.get(w, {}))
            for key in ('visible', 'x', 'y', 'font_size'):
                if key in target:
                    spec[key] = target[key]
            current[w] = spec
        OUTPUT_CTRL.write_text(json.dumps(current, indent=2))
        self._set_interaction(windows[0], action='use')
        payload = {'windows': windows, 'target': target, 'reason': reason, 'timestamp': time.time()}
        self.nervous.publish('ui.output', payload, source='motor_action', priority='normal')

    def _create_artifact(self, kind, target, thought):
        toy = 'pixels' if kind == 'paint' else 'text'
        self._set_interaction(toy, action='create')
        try:
            if kind == 'create_text':
                path = self.actions.create_text(target.get('title', 'thought'), target.get('text', thought))
            elif kind == 'create_image':
                path = self.actions.create_image(target.get('title', 'image'), target.get('text', thought))
            else:
                path = self.actions.paint(target.get('title', 'painting'), target.get('strokes', []))
            self.nervous.publish('artifact.created', {'kind': kind, 'path': str(path)},
                                 source='motor_action', priority='normal')
        except Exception as exc:
            self.nervous.publish('motor.action.error', {'kind': kind, 'error': str(exc)},
                                 source='motor_action', priority='background')

    def _body_loop(self):
        """Fast body loop: ordinary movement is generated here, not by CC."""
        while getattr(self.kernel, '_running', True):
            try:
                phase = self.kernel.lifecycle.state.phase.value
                if phase != 'awake':
                    time.sleep(0.25)
                    continue
                now = time.monotonic()
                if now - self.last_move >= 2.2:
                    state = self.kernel.state
                    emotions = self.kernel.motivation.emotions
                    curiosity = max(0.0, min(1.0, float(getattr(state, 'curiosity', 0.0))))
                    stress = max(0.0, min(1.0, float(getattr(state, 'stress', 0.0))))
                    fatigue = max(0.0, min(1.0, float(getattr(state, 'fatigue', 0.0))))
                    # Motor exploration is a small, organic target-selection process.
                    # It is not a sinusoid and does not ask the language model to move.
                    if fatigue > .78 or stress > .9:
                        dx = dy = 0.0
                    else:
                        self.phase += random.uniform(0.55, 1.35) + curiosity * .7
                        magnitude = 18.0 + 75.0 * curiosity + 25.0 * self.sound
                        dx = math.cos(self.phase) * magnitude + random.uniform(-18, 18)
                        dy = math.sin(self.phase * 0.73) * magnitude * .65 + random.uniform(-12, 12)
                        if stress > .65:
                            dx *= .45; dy *= .45
                    self._command_move({'dx': dx, 'dy': dy, 'duration': random.uniform(.25, .8)},
                                       reason='body_exploration')
                    self.last_move = now
                self.heartbeat({'state': 'running', 'autonomous_motor': True})
            except Exception as exc:
                self.nervous.publish('motor.loop.error', {'error': str(exc)}, source='motor_action', priority='background')
            time.sleep(0.2)
