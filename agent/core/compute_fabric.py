from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path("/mnt/gai")
PATH = ROOT / "state/compute_fabric.json"


class ComputeGate:
    """Logical sorting gate; never a process and never tied to one device."""

    def __init__(self, name, kind, capacity=1.0):
        self.name = name
        self.kind = kind
        self.capacity = float(capacity)
        self.busy = 0.0
        self.jobs = 0
        self.last_score = 0.0

    def score(self, workload=0.1, urgency=0.5, locality=0.5):
        availability = max(0.0, 1.0 - self.busy)
        score = (
            0.50 * availability
            + 0.20 * float(locality)
            + 0.20 * float(urgency) * availability
            + 0.10 * max(0.0, 1.0 - float(workload))
        )
        self.last_score = score
        return score

    def reserve(self, workload):
        self.busy = min(1.0, self.busy + max(0.0, float(workload)) / max(0.1, self.capacity))
        self.jobs += 1

    def release(self, workload):
        self.busy = max(0.0, self.busy - max(0.0, float(workload)) / max(0.1, self.capacity))


class ComputeFabric:
    """CPU/GPU execution router for the neural layer.

    CPU owns orchestration. GPU owns suitable batched neural math.
    The fabric chooses an execution gate using availability, urgency,
    locality and workload, with safe CPU fallback.
    """

    def __init__(self):
        self.gates = {
            "cpu": ComputeGate("cpu", "cpu", 1.0),
            "gpu0": ComputeGate("gpu0", "cuda", 2.0),
            "igpu0": ComputeGate("igpu0", "intel_gpu", 1.5),
        }
        self.generation = 0
        self.stats = {
            "routes": 0,
            "gpu_routes": 0,
            "cpu_routes": 0,
            "fallbacks": 0,
            "intel_gpu_routes": 0,
            "intel_gpu_fallbacks": 0,
        }
        self.gpu_available = False
        self.gpu_name = None
        self.intel_gpu_available = False
        self.intel_gpu_name = None
        self._cp = None
        self._cl = None
        self._intel_context = None
        self._intel_queue = None
        self._intel_kernel = None
        self._cuda_neural_kernel = None
        self._load_gpu()
        self._detect_intel_gpu()
        self.load()

    def _load_gpu(self):
        try:
            nvrtc = ROOT / "venvs/gai/lib/python3.12/site-packages/nvidia/cuda_nvrtc"
            if nvrtc.exists():
                os.environ.setdefault("CUDA_PATH", str(nvrtc))
                os.environ["LD_LIBRARY_PATH"] = (
                    str(nvrtc / "lib") + ":" + os.environ.get("LD_LIBRARY_PATH", "")
                )
            import cupy as cp
            if cp.cuda.runtime.getDeviceCount() > 0:
                self._cp = cp
                self.gpu_available = True
                try:
                    self._cuda_neural_kernel = cp.RawKernel(r'''
                    extern "C" __global__ void neural_mix(const float* x, float* y, float strength) {
                        int i = blockDim.x * blockIdx.x + threadIdx.x;
                        if (i < 1048576) y[i] = 0.65f * x[i] + 0.35f * strength;
                    }
                    ''', "neural_mix", options=("--gpu-architecture=compute_50",))
                except Exception:
                    self._cuda_neural_kernel = None
                name = cp.cuda.runtime.getDeviceProperties(0)["name"]
                self.gpu_name = name.decode() if isinstance(name, bytes) else str(name)
        except Exception:
            self._cp = None
            self.gpu_available = False

    def _detect_intel_gpu(self):
        # Detect the integrated Intel GPU independently of CUDA.  On this
        # laptop it is Intel HD Graphics 620 (renderD128).  It becomes a
        # compute gate only when a suitable runtime is present; we never
        # claim GPU execution merely because PCI hardware exists.
        try:
            vendor = Path("/sys/class/drm/renderD128/device/vendor").read_text().strip()
            device = Path("/sys/class/drm/renderD128/device/device").read_text().strip()
            if vendor == "0x8086":
                self.intel_gpu_available = False
                self.intel_gpu_name = f"Intel GPU {device}"
                try:
                    import pyopencl as cl
                    devices = [d for p in cl.get_platforms() for d in p.get_devices()
                               if "Intel" in d.vendor or "Intel" in d.name]
                    if devices:
                        device = devices[0]
                        self._cl = cl
                        self._intel_context = cl.Context(devices=[device])
                        self._intel_queue = cl.CommandQueue(self._intel_context)
                        program = cl.Program(self._intel_context, """
                        __kernel void neural_mix(__global const float *x,
                                                  __global float *y,
                                                  const float strength) {
                            size_t i = get_global_id(0);
                            y[i] = 0.65f * x[i] + 0.35f * strength;
                        }
                        """).build()
                        self._intel_kernel = program.neural_mix
                        self.intel_gpu_available = True
                        self.intel_gpu_name = device.name
                except Exception:
                    pass
        except Exception:
            self.intel_gpu_available = False

    def load(self):
        try:
            obj = json.loads(PATH.read_text())
            self.generation = int(obj.get("generation", 0))
            self.stats.update(obj.get("stats", {}))
        except Exception:
            pass

    def save(self):
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps(self.snapshot(), separators=(",", ":")))

    def refresh(self):
        # Cheap host-side load estimate.  We deliberately do not migrate
        # arbitrary application work; only neural workloads use this fabric.
        try:
            load1 = min(1.0, float(os.getloadavg()[0]) / max(1.0, float(os.cpu_count() or 1)))
            self.gates["cpu"].busy = load1
        except Exception:
            pass
        if self.gpu_available and self._cp is not None:
            try:
                free, total = self._cp.cuda.runtime.memGetInfo()
                memory_pressure = 1.0 - (float(free) / float(total))
                # Memory pressure is a conservative proxy; compute utilisation
                # is not reliably exposed by the CUDA runtime.
                self.gates["gpu0"].busy = max(0.0, min(1.0, memory_pressure))
            except Exception:
                pass

    def route(self, workload=0.1, urgency=0.5, modality="general",
              locality="cpu", require_gpu=False):
        self.refresh()
        locality_gpu = 0.9 if locality in {"gpu", "cuda", "neural_gpu"} else 0.35
        locality_cpu = 0.9 if locality == "cpu" else 0.55

        scores = {
            "cpu": self.gates["cpu"].score(workload, urgency, locality_cpu),
            "gpu0": self.gates["gpu0"].score(workload, urgency, locality_gpu)
                     if self.gpu_available else -1.0,
            "igpu0": self.gates["igpu0"].score(workload, urgency, 0.75)
                     if self.intel_gpu_available else -1.0,
        }

        if require_gpu and self.gpu_available:
            selected = "gpu0"
        else:
            selected = max(scores, key=scores.get)

        self.gates[selected].reserve(workload)
        self.stats["routes"] += 1
        if selected == "gpu0":
            self.stats["gpu_routes"] += 1
        elif selected == "igpu0":
            self.stats["intel_gpu_routes"] += 1
        else:
            self.stats["cpu_routes"] += 1

        return {
            "gate": selected,
            "kind": self.gates[selected].kind,
            "score": round(float(scores[selected]), 4),
            "scores": {k: round(float(v), 4) for k, v in scores.items()},
            "gpu": self.gpu_name,
            "modality": modality,
            "urgency": urgency,
        }

    def release(self, route, workload=0.1):
        gate = str((route or {}).get("gate", "cpu"))
        if gate in self.gates:
            self.gates[gate].release(workload)

    def execute_neural(self, activations, strength, urgency=0.5,
                       modality="general", locality="gpu"):
        """Execute one batched neural activation update through a gate."""
        route = self.route(
            workload=min(1.0, max(0.01, len(activations) / 1024.0)),
            urgency=urgency,
            modality=modality,
            locality=locality,
            require_gpu=False,
        )
        try:
            if route["gate"] == "igpu0" and self._intel_kernel is not None:
                cl = self._cl
                import numpy as np
                values = np.asarray(activations, dtype=np.float32)
                out = np.empty_like(values)
                mf = cl.mem_flags
                bx = cl.Buffer(self._intel_context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=values)
                by = cl.Buffer(self._intel_context, mf.WRITE_ONLY, out.nbytes)
                self._intel_kernel(self._intel_queue, values.shape, None, bx, by, np.float32(strength))
                cl.enqueue_copy(self._intel_queue, out, by).wait()
                result = out.tolist()
            elif route["gate"] == "gpu0" and self._cp is not None and self._cuda_neural_kernel is not None:
                cp = self._cp
                values = cp.asarray(activations, dtype=cp.float32)
                out = cp.empty_like(values)
                n = len(activations)
                blocks = (n + 127) // 128
                self._cuda_neural_kernel((blocks,), (128,), (values, out, cp.float32(strength)))
                cp.cuda.Stream.null.synchronize()
                result = cp.asnumpy(out).tolist()
            else:
                result = [
                    0.65 * float(x) + 0.35 * float(strength)
                    for x in activations
                ]
            return result, route
        except Exception:
            self.stats["fallbacks"] += 1
            if route.get("gate") == "igpu0":
                self.stats["intel_gpu_fallbacks"] += 1
            result = [0.65 * float(x) + 0.35 * float(strength) for x in activations]
            route["fallback"] = True
            return result, route
        finally:
            self.release(route, min(1.0, max(0.01, len(activations) / 1024.0)))

    def snapshot(self):
        self.refresh()
        return {
            "generation": self.generation,
            "gpu_available": self.gpu_available,
            "gpu_name": self.gpu_name,
            "intel_gpu_detected": bool(self.intel_gpu_name),
            "intel_gpu_available": self.intel_gpu_available,
            "intel_gpu_name": self.intel_gpu_name,
            "gates": {
                k: {
                    "kind": v.kind,
                    "busy": round(v.busy, 4),
                    "jobs": v.jobs,
                    "last_score": round(v.last_score, 4),
                } for k, v in self.gates.items()
            },
            "stats": dict(self.stats),
        }
