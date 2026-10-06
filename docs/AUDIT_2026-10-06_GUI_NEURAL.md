# G.A.I. Implementation Audit — GUI, Persistent Vision & Neural Fabric

Date: 2026-10-06
Status: implemented and smoke-tested
Scope: visual organs, phenotype GUI, persistent tools, display behaviour, affective mouth/audio, first neural fabric layer.

## 1. Visual architecture

G.A.I. no longer depends on repeated screenshot captures for its primary visual experience.

A persistent low-resolution desktop stream is maintained by the Screen Stream organ. A persistent camera stream is maintained by the Camera organ. The Senses layer selects one visual source at a time through the shared Sight Focus state:

- IN: desktop/screen stream
- OUT: physical camera/world stream

The selected stream is analysed directly from the latest rolling frame.

The desktop stream is downsampled to 640x360 at 2 FPS. The camera maintains a rolling latest-frame buffer and a low-frequency persistent preview file.

## 2. Invisible focus organ

A separate focus-bubble process provides the gaze target.

The focus organ is invisible, transparent to mouse input, non-activating, separate from the visible G.A.I. body, and controlled by the normal motor/gaze path.

The visible eye reads the same focus state. The pupil grows as the focus target approaches the body and contracts as the target becomes more distant.

OUT/camera attention produces a small lens indicator in the phenotype.

## 3. Visible phenotype

The G.A.I. body is now a single clean circular phenotype with no diagnostic HUD.

Appearance responds to current affect and attention/action state.

Mouth rules:
- no mouth animation during ordinary thought/action
- vocalisation produces mouth movement
- happiness curves the mouth upward
- sadness curves the mouth downward

The speaker organ has no speech-synthesis path and produces affective non-verbal tones only.

## 4. Persistent toy organs

View, State/Thought, Text and Pixels are consolidated into one persistent external Toy Organ application.

The toys are capabilities rather than competing visible identities.

Normal desktop windows are allowed to behave normally. They are not forced above the desktop. The G.A.I. body itself is kept above ordinary windows.

A small non-cognitive watchdog on the motor/maintenance path can recreate a failed toy process without making Central Consciousness manage process supervision directly.

Legacy competing GUI implementations were moved into agent/gui/archive/legacy/.

## 5. Display persistence

A display_guard organ was added.

It maintains:
- idle delay = 0
- screen lock disabled
- display sleep disabled
- automatic suspend disabled
- X screen blanking disabled

The guard runs with the active user session D-Bus environment so Cinnamon settings are committed and maintained.

Post-fix verification returned:
- idle-delay: 0
- lock-enabled: false
- sleep-display-ac: 0
- sleep-inactive-ac-timeout: 0
- sleep-inactive-ac-type: nothing

## 6. Neural fabric — first layer

agent/core/neural_fabric.py is now part of the kernel.

The current substrate is deliberately sparse rather than a large neural network.

Routes are keyed by:

    attended sensory target -> chosen action

Each route stores an adaptive weight, visits, accumulated reward, prediction error, and recency.

Awake plasticity is conservative. Pre-sleep and dream plasticity are larger, allowing structural adaptation to happen primarily during offline phases.

Dream replay reads recent V1 traces and replays attended stimulus/action/consequence relationships into the neural fabric. Maintenance can weaken unused routes and prune the substrate.

The Neural Fabric is not directly commanded by Central Consciousness. It changes from experience, consequences, and lifecycle phase.

Live runtime after implementation showed learned auditory-to-action and visual-to-action routes.

A direct substrate smoke test confirmed awake plasticity of 0.015 and dream plasticity of 0.12, with a substantially larger route change during dream-phase learning.

## 7. Runtime verification

The live organism returned to:
- phase: awake
- normal V1 action selection
- focus mode: OUT/camera
- persistent camera stream active
- persistent desktop stream active
- invisible focus organ active
- single visible G.A.I. bubble
- persistent toy application active
- affective speaker active
- neural fabric active

The visible bubble was checked through the window manager and reported _NET_WM_STATE_ABOVE.

## 8. Tests

The non-camera regression suite completed successfully:

    65 passed

A previous known hardware limitation remains: the standalone pytest camera probe may fail to open /dev/video0 even though the live Camera organ captures successfully in the actual organism runtime.

A temporary Senses regression caused by the new stream contract was found during this pass, corrected, and the full non-camera suite was rerun successfully.

## 9. Design decisions recorded

Persistent streams were chosen over a virtual desktop environment because a virtual environment would add another rendering and IPC layer on this low-resource machine.

The visual architecture is therefore:

    physical stream -> persistent latest frame -> sight focus -> sensory compression -> shared salience -> CNS/CC

rather than a repeated screenshot -> disk -> reload -> process cycle.

The next neural work should extend the sparse adaptive substrate, not replace the current closed loop.