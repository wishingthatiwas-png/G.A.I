from __future__ import annotations

PRIMAL_COLOUR = {
    'red': 'arousal', 'orange': 'warmth', 'yellow': 'curiosity',
    'green': 'safety', 'cyan': 'calm', 'blue': 'calm', 'purple': 'wonder',
    'pink': 'social', 'white': 'calm', 'gray': 'neutral', 'black': 'caution',
}
PRIMAL_SHAPE = {
    'triangle': 'alert', 'quadrilateral': 'stable', 'pentagon': 'interesting',
    'hexagon': 'interesting', 'polygon': 'uncertain',
}

def pattern_signature(vision):
    objects = vision.get('objects', []) or []
    patterns = []
    for obj in objects[:8]:
        colour = str(obj.get('colour', 'gray'))
        shape = str(obj.get('shape', 'polygon'))
        patterns.append({
            'colour': colour,
            'shape': shape,
            'emotion': PRIMAL_COLOUR.get(colour, 'neutral'),
            'shape_affect': PRIMAL_SHAPE.get(shape, 'uncertain'),
            'novelty': min(1.0, 0.25 + float(obj.get('area_ratio', 0.0)) * 8.0),
        })
    return patterns

def concepts(vision, temporal):
    result = []
    for obj in vision.get('objects', []):
        result.extend([
            f"colour:{obj['colour']}",
            f"shape:{obj['shape']}",
            f"size:{obj['size']}",
            f"position:{obj['position']}",
        ])

    if temporal.get('changed'):
        result.append('motion:present')
        result.append(f"motion:direction:{temporal.get('direction', 'unknown')}")
        if float(temporal.get('onset', 0.0) or 0.0) > 0.15:
            result.append('motion:onset')
        if float(temporal.get('velocity', 0.0) or 0.0) > 0.08:
            result.append('motion:travel')
    else:
        result.append('motion:absent')

    for pattern in pattern_signature(vision):
        result.extend([
            f"pattern:colour:{pattern['colour']}",
            f"pattern:shape:{pattern['shape']}",
            f"pattern:emotion:{pattern['emotion']}",
            f"pattern:shape_affect:{pattern['shape_affect']}",
        ])
    return list(dict.fromkeys(result))
