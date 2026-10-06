from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

from cognition.core import Intention
from core.motor_center import MotorActionCentre
from core.nervous import Event, NervousSystem

ROOT = Path('/mnt/gai')


class FakeKernel:
    _lock_file = None
    cfg = {'v1_mode': True}
    latest_reward = 0.0
    latest_prediction_error = 0.0
    last_action = {}

    def __init__(self):
        self.nervous = NervousSystem()
        self.state = SimpleNamespace(mode='awake', happiness=0.5, curiosity=0.6,
                                     fatigue=0.1, boredom=0.1)
        self.motivation = SimpleNamespace(emotions=SimpleNamespace(
            fear=0.0, stress=0.0, happiness=0.0, curiosity=0.5,
            fatigue=0.0, boredom=0.0))
        self.core_needs = SimpleNamespace(register_rest=lambda value: None,
                                          register_social=lambda value: None)
        self.v1_brain = SimpleNamespace(world=None, record_outcome=lambda result: None)


def make_event(kind, payload, correlation_id='gate2-test'):
    return Event(kind, 'test', payload, time.time(), 'gate2-event', correlation_id=correlation_id)


def main():
    assert Intention('move', priority=4).validate().priority == 1.0
    assert Intention('not-real').validate().type == 'none'

    k = FakeKernel()
    m = MotorActionCentre(k)

    move = m.execute_primitive('move', {'dx': 800, 'dy': -800, 'duration': 9}, reason='gate2')
    motor = json.loads((ROOT / 'state/motor_output.json').read_text())
    assert move['success'] is True and abs(motor['dx']) <= 500 and abs(motor['dy']) <= 300 and motor['duration'] <= 4

    output = m.execute_primitive('display', {'window': 'thought', 'visible': True, 'x': 44, 'y': 55}, reason='gate2')
    windows = json.loads((ROOT / 'state/output_windows.json').read_text())
    assert output['success'] is True and windows['thought']['visible'] is True

    artifact = m.execute_primitive('create_text', {'title': 'gate2_output_test', 'text': 'G.A.I. output boundary test'}, reason='gate2')
    assert artifact['success'] is True and Path(artifact['path']).exists()

    unknown = make_event('cognition.intention', {'intention': {'type': 'not-real'}, 'thought': 'reject'})
    m.receive_intention(unknown)
    assert k.last_action['type'] == 'not-real' and k.last_action['executed'] is False

    speech = m.execute_primitive('vocalize', {'emotion': 'curiosity', 'text': 'G A I output organ test.'}, reason='gate2')
    request = json.loads((ROOT / 'state/speaker_request.json').read_text())
    status = json.loads((ROOT / 'state/speaker_organ.json').read_text())
    assert speech['success'] is True and speech['submitted'] is True and request['mode'] == 'speech'
    assert request['correlation_id'] == 'gate2-test'
    assert status.get('mode') in {'speech', 'affective_tone'}
    print('OUTPUT_GATE_2_PASS')
    print(json.dumps({'move': move, 'display': output, 'artifact': artifact, 'speech': speech, 'speaker_status': status}, indent=2, default=str))


if __name__ == '__main__':
    main()
