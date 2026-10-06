from __future__ import annotations

import ctypes
import json
import os
import random
import time
from pathlib import Path

ROOT = Path("/mnt/gai")
PATH = ROOT / "state/neural_population.json"

# G's GTX 950M is an older CUDA device.  Keep the GPU backend optional and
# self-contained so the neural layer can always fall back to CPU operation.
try:
    nvrtc = ROOT / "venvs/gai/lib/python3.12/site-packages/nvidia/cuda_nvrtc/lib/libnvrtc.so.12"
    if nvrtc.exists():
        os.environ.setdefault("CUDA_PATH", str(nvrtc.parent.parent))
        ctypes.CDLL(str(nvrtc))
    import cupy as cp
    GPU_AVAILABLE = cp.cuda.runtime.getDeviceCount() > 0
except Exception:
    cp = None
    GPU_AVAILABLE = False

ROLES = (
    "sensory", "salience", "attention", "routing",
    "association", "prediction", "memory", "motor",
)

_GPU_ACTIVATE = None
_GPU_DECAY = None

if GPU_AVAILABLE:
    try:
        _GPU_ACTIVATE = cp.RawKernel(
            r'''
            extern "C" __global__ void activate(float* a, const int* idx,
                                                int n, float strength) {
                int i = blockDim.x * blockIdx.x + threadIdx.x;
                if (i < n) {
                    int j = idx[i];
                    a[j] = 0.65f * a[j] + 0.35f * strength;
                }
            }
            ''',
            "activate",
            options=("--gpu-architecture=compute_50",),
        )
        _GPU_DECAY = cp.RawKernel(
            r'''
            extern "C" __global__ void decay(float* a, float factor) {
                int i = blockDim.x * blockIdx.x + threadIdx.x;
                a[i] = a[i] * factor;
            }
            ''',
            "decay",
            options=("--gpu-architecture=compute_50",),
        )
    except Exception:
        GPU_AVAILABLE = False


class NeuralPopulation:
    """Lightweight scalable neural-agent population.

    Agents are data objects, not processes.  On G, activation/decay is
    batched on the GTX 950M when CUDA is available; CPU remains the
    orchestration/state layer.
    """

    def __init__(self, target=96, maximum=1024):
        self.target = max(16, int(target))
        self.maximum = max(self.target, int(maximum))
        self.nodes = {}
        self.generation = 0
        self.stats = {"created": 0, "activations": 0, "pruned": 0}
        self.gpu_enabled = bool(GPU_AVAILABLE)
        self._gpu_activations = None
        self.load()
        self.scale_to(self.target)
        self._ensure_gpu_state()

    def _new_node(self, index):
        role = ROLES[index % len(ROLES)]
        return {
            "id": f"n{index:04d}",
            "role": role,
            "activation": 0.0,
            "visits": 0,
            "plasticity": 0.015,
            "last_active": 0.0,
        }

    def load(self):
        try:
            obj = json.loads(PATH.read_text())
            self.nodes = obj.get("nodes", {})
            self.generation = int(obj.get("generation", 0))
            self.stats.update(obj.get("stats", {}))
        except Exception:
            pass

    def _ensure_gpu_state(self):
        if not self.gpu_enabled or cp is None:
            return
        try:
            values = [float(n.get("activation", 0.0)) for n in self.nodes.values()]
            self._gpu_activations = cp.asarray(values, dtype=cp.float32)
            cp.cuda.Stream.null.synchronize()
        except Exception:
            self.gpu_enabled = False
            self._gpu_activations = None

    def _sync_gpu_to_nodes(self):
        if not self.gpu_enabled or self._gpu_activations is None:
            return
        try:
            values = cp.asnumpy(self._gpu_activations)
            for node, value in zip(self.nodes.values(), values):
                node["activation"] = round(float(value), 5)
        except Exception:
            self.gpu_enabled = False

    def save(self):
        self._sync_gpu_to_nodes()
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps({
            "generation": self.generation,
            "nodes": self.nodes,
            "stats": self.stats,
            "backend": "cuda" if self.gpu_enabled else "cpu",
        }, separators=(",", ":")))

    def scale_to(self, count):
        count = max(16, min(self.maximum, int(count)))
        if len(self.nodes) < count:
            existing = {int(k[1:]) for k in self.nodes if k.startswith("n") and k[1:].isdigit()}
            index = 0
            while len(self.nodes) < count:
                while index in existing:
                    index += 1
                node = self._new_node(index)
                self.nodes[node["id"]] = node
                existing.add(index)
                self.stats["created"] += 1
                index += 1
        elif len(self.nodes) > count:
            removable = sorted(
                self.nodes.items(),
                key=lambda kv: (
                    int(kv[1].get("visits", 0)),
                    float(kv[1].get("activation", 0.0)),
                    float(kv[1].get("last_active", 0.0)),
                ),
            )
            for key, node in removable:
                if len(self.nodes) <= count:
                    break
                if int(node.get("visits", 0)) == 0:
                    self.nodes.pop(key, None)
                    self.stats["pruned"] += 1
        if self._gpu_activations is not None:
            self._ensure_gpu_state()
        self.save()
        return len(self.nodes)

    def recruit(self, signal, amount=8):
        signal = dict(signal or {})
        strength = max(0.0, min(1.0, float(
            signal.get("salience", signal.get("strength", 0.5))
        )))
        modality = str(signal.get("modality", "general"))
        candidates = sorted(
            enumerate(self.nodes.values()),
            key=lambda item: (
                0 if item[1].get("role") in {"sensory", "salience", "attention"}
                and modality in {"vision", "audio"} else 1,
                float(item[1].get("activation", 0.0)),
                int(item[1].get("visits", 0)),
            ),
        )
        chosen = candidates[:max(1, min(int(amount), len(candidates)))]
        now = time.time()

        if self.gpu_enabled and self._gpu_activations is not None and _GPU_ACTIVATE is not None:
            try:
                indices = cp.asarray([i for i, _ in chosen], dtype=cp.int32)
                _GPU_ACTIVATE(((max(1, len(chosen)) + 127) // 128,), (128,),
                              (self._gpu_activations, indices, len(chosen), cp.float32(strength)))
                cp.cuda.Stream.null.synchronize()
            except Exception:
                self.gpu_enabled = False

        for _, node in chosen:
            if not self.gpu_enabled:
                node["activation"] = round(min(
                    1.0, 0.65 * float(node.get("activation", 0.0)) + 0.35 * strength
                ), 5)
            node["visits"] = int(node.get("visits", 0)) + 1
            node["last_active"] = now
            self.stats["activations"] += 1
        return [n["id"] for _, n in chosen]

    def decay(self, factor=0.94):
        if self.gpu_enabled and self._gpu_activations is not None and _GPU_DECAY is not None:
            try:
                n = len(self.nodes)
                _GPU_DECAY(((n + 127) // 128,), (128,),
                           (self._gpu_activations, cp.float32(factor)))
                cp.cuda.Stream.null.synchronize()
                return
            except Exception:
                self.gpu_enabled = False
        for node in self.nodes.values():
            node["activation"] = round(
                float(node.get("activation", 0.0)) * float(factor), 5
            )

    def snapshot(self):
        self._sync_gpu_to_nodes()
        active = [
            n for n in self.nodes.values()
            if float(n.get("activation", 0.0)) > 0.05
        ]
        roles = {}
        for node in self.nodes.values():
            roles[node["role"]] = roles.get(node["role"], 0) + 1
        gpu_name = None
        if self.gpu_enabled and cp is not None:
            try:
                gpu_name = cp.cuda.runtime.getDeviceProperties(0)["name"].decode()
            except Exception:
                gpu_name = "CUDA device"
        return {
            "target": self.target,
            "maximum": self.maximum,
            "node_count": len(self.nodes),
            "active_count": len(active),
            "roles": roles,
            "generation": self.generation,
            "stats": dict(self.stats),
            "backend": "cuda" if self.gpu_enabled else "cpu",
            "gpu": gpu_name,
            "active_nodes": sorted(
                [{"id": n["id"], "role": n["role"], "activation": n["activation"]}
                 for n in active],
                key=lambda x: x["activation"], reverse=True
            )[:16],
        }
