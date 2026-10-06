from __future__ import annotations

import numpy as np


class TemporalVision:
    """Low-level temporal salience: change, onset, direction and persistence."""

    def __init__(self):
        self.previous = None
        self.previous_centroid = None
        self.previous_velocity = 0.0
        self.previous_motion_ratio = 0.0

    def compare(self, frame):
        if frame is None:
            return {
                'motion': 0.0,
                'changed': False,
                'motion_ratio': 0.0,
                'onset': 0.0,
                'velocity': 0.0,
                'acceleration': 0.0,
                'direction': 'still',
                'salience': 0.0,
            }

        gray = frame if len(frame.shape) == 2 else frame.mean(axis=2)
        gray = gray.astype(np.float32)
        brightness = float(np.mean(gray) / 255.0)
        previous_brightness = float(np.mean(self.previous) / 255.0) if self.previous is not None else brightness
        brightness_change = abs(brightness - previous_brightness)
        if self.previous is None:
            self.previous = gray
            return {
                'motion': 0.0,
                'changed': False,
                'motion_ratio': 0.0,
                'onset': 0.0,
                'velocity': 0.0,
                'acceleration': 0.0,
                'direction': 'still',
                'salience': 0.0,
            }

        diff = np.abs(gray - self.previous)
        motion = float(np.mean(diff) / 255.0)
        moving = diff > 22.0
        motion_ratio = float(np.mean(moving))

        ys, xs = np.nonzero(moving)
        centroid = None
        if len(xs):
            centroid = (float(xs.mean()) / max(1, gray.shape[1]), float(ys.mean()) / max(1, gray.shape[0]))

        velocity = 0.0
        direction = 'still'
        if centroid is not None and self.previous_centroid is not None:
            dx = centroid[0] - self.previous_centroid[0]
            dy = centroid[1] - self.previous_centroid[1]
            velocity = float(min(1.0, (dx * dx + dy * dy) ** 0.5 * 3.0))
            if velocity > 0.035:
                if abs(dx) >= abs(dy):
                    direction = 'right' if dx > 0 else 'left'
                else:
                    direction = 'down' if dy > 0 else 'up'
        elif motion_ratio > 0.015:
            direction = 'onset'

        onset = max(0.0, min(1.0, (motion_ratio - self.previous_motion_ratio) * 4.0))
        acceleration = max(0.0, min(1.0, abs(velocity - self.previous_velocity) * 2.5))

        # Animal-like bottom-up salience: sudden/large change gets attention;
        # steady repetition decays unless there is new movement.
        motion_term = min(1.0, motion * 9.0)
        area_term = min(1.0, motion_ratio * 3.0)
        brightness_term = min(1.0, brightness_change * 8.0)
        salience = max(
            0.0,
            min(1.0, 0.38 * motion_term + 0.22 * area_term + 0.14 * onset + 0.10 * max(velocity, acceleration) + 0.16 * brightness_term),
        )

        self.previous = gray
        self.previous_centroid = centroid
        self.previous_velocity = velocity
        self.previous_motion_ratio = motion_ratio

        return {
            'motion': motion,
            'brightness': round(brightness, 4),
            'brightness_change': round(brightness_change, 4),
            'brightness_event': brightness_change >= 0.035,
            'changed': motion > 0.015 or motion_ratio > 0.015 or brightness_change >= 0.02,
            'motion_ratio': motion_ratio,
            'onset': onset,
            'velocity': velocity,
            'acceleration': acceleration,
            'direction': direction,
            'centroid': (
                {'x': round(centroid[0], 3), 'y': round(centroid[1], 3)}
                if centroid is not None else None
            ),
            'salience': round(salience, 4),
        }
