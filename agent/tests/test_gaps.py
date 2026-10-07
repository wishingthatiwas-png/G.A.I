import json
import time
import json
from pathlib import Path

from cognition.v1 import SharedAttention
from core.lifecycle import Lifecycle, Phase
from perception.senses import Senses


def test_audio_senses_consumes_audio_organ_state(tmp_path):
    state = Path("/mnt/gai/state/audio_input.json")
    old = state.read_text() if state.exists() else None
    try:
        state.write_text(json.dumps({
            "timestamp": time.time(),
            "available": True,
            "rms": 0.02,
            "peak": 0.04,
            "signal": 0.4,
            "auditory": {"available": True, "focus": "sound"},
        }))
        senses = Senses()
        try:
            audio = senses._audio_from_organ()
            assert audio["available"] is True
            assert audio["fresh"] is True
            assert audio["signal"] == 0.4
        finally:
            senses.close()
    finally:
        if old is None:
            state.unlink(missing_ok=True)
        else:
            state.write_text(old)


def test_shared_attention_fuses_modalities(tmp_path):
    attention = SharedAttention(tmp_path / "attention.json")
    result = attention.select(
        {
            "vision": {"temporal": {"structure_change": 0.2}, "concepts": ["object"]},
            "audio": {"fresh": True, "signal": 0.9},
        },
        {"object": {"id": "curiosity_object", "state": "quiet"}},
        {"curiosity": 0.8},
    )
    assert result["selected"]["modality"] == "audio"
    assert any(x["modality"] == "vision" for x in result["candidates"])
    assert any(x["modality"] == "world" for x in result["candidates"])
    assert json.loads((tmp_path / "attention.json").read_text())["selected"]["target"] == "sound"


def test_v1_lifecycle_can_sleep_from_critical_memory_pressure():
    life = Lifecycle()
    life.update_power(1.0, True, energy=0.55, fatigue=0.4, memory_pressure=0.99, v1_mode=True)
    assert life.state.phase == Phase.PRE_SLEEP


def test_v1_lifecycle_still_respects_real_low_battery():
    life = Lifecycle()
    life.update_power(0.05, True, energy=0.1, fatigue=0.9, memory_pressure=0.1, v1_mode=True)
    assert life.state.phase == Phase.PRE_SLEEP


def test_shared_compute_scale_has_one_clock():
    from core.scaling import effective_tick_fps, effective_metabolic_hz
    cfg={"compute_scale":1.0}
    assert effective_tick_fps(cfg, 1.0) == 20.0
    assert effective_metabolic_hz(cfg, 1.0) == 2.0
    assert effective_tick_fps(cfg, 10.0) == 200.0
    assert effective_metabolic_hz(cfg, 10.0) == 20.0


def test_storage_pressure_is_sleep_analogue():
    from core.homeostasis import CoreNeeds
    needs=CoreNeeds()
    original=needs.storage_pressure
    assert 0.0 <= original <= 1.0
    assert hasattr(needs, "storage_sleep_need")


def test_battery_maps_directly_to_hunger():
    from core.motivation import InstinctLayer
    class N: energy=1.0; power=0.2; social=0.0; rest=0.0; processing=0.0; temperature=0.0
    low=InstinctLayer().evaluate(N(), {"system":{}}, 0.0)
    N.power=1.0
    high=InstinctLayer().evaluate(N(), {"system":{}}, 0.0)
    assert low.hunger > high.hunger


def test_rest_debt_can_be_discharged_by_rest():
    from core.homeostasis import CoreNeeds
    needs = CoreNeeds(rest=0.8)
    needs.register_rest(1.0)
    assert needs.rest < 0.8
