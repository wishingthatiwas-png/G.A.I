from __future__ import annotations

def concepts(vision, temporal):
    result=[]
    for obj in vision.get('objects', []):
        result.extend([
            f"colour:{obj['colour']}",
            f"shape:{obj['shape']}",
            f"size:{obj['size']}",
            f"position:{obj['position']}",
        ])
    if temporal.get('changed'):
        result.append('motion:present')
    else:
        result.append('motion:absent')
    return list(dict.fromkeys(result))
