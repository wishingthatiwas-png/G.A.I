from __future__ import annotations
from pathlib import Path
import json, time

ROOT = Path('/mnt/gai')

class SafeActions:
    """Non-destructive actions available to the autonomous loop."""
    def log(self, action, **details):
        p = ROOT / 'data/actions.jsonl'
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a') as f:
            f.write(json.dumps({'ts': time.time(), 'action': action, 'details': details}) + '\n')

    def save_observation(self, observation):
        p = ROOT / 'data/observations/latest.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(observation, indent=2, default=str))
        self.log('save_observation')

    def create_text(self, title, text):
        """Create a bounded text artifact in G.A.I.'s creative sandbox."""
        safe = ''.join(c for c in str(title) if c.isalnum() or c in '-_ ')[:80].strip() or 'thought'
        p = ROOT / 'creative' / 'text' / f'{safe}.txt'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(text)[:12000], encoding='utf-8')
        self.log('create_text', path=str(p))
        return str(p)

    def create_image(self, title, text='', width=640, height=480):
        """Create a simple self-contained SVG image; no external tools or network."""
        import html
        safe = ''.join(c for c in str(title) if c.isalnum() or c in '-_ ')[:80].strip() or 'image'
        p = ROOT / 'creative' / 'images' / f'{safe}.svg'
        p.parent.mkdir(parents=True, exist_ok=True)
        words = html.escape(str(text)[:500]).replace('\n', ' ')
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#111827"/>
<circle cx="{width*0.72:.0f}" cy="{height*0.35:.0f}" r="90" fill="#334155"/>
<path d="M60 {height-90} Q {width/2:.0f} {height-240} {width-60} {height-90}" fill="none" stroke="#93c5fd" stroke-width="8"/>
<text x="40" y="70" fill="#f8fafc" font-family="sans-serif" font-size="28">{words}</text>
</svg>'''
        p.write_text(svg, encoding='utf-8')
        self.log('create_image', path=str(p))
        return str(p)

    def paint(self, title, strokes):
        """Create a bounded SVG canvas from safe line strokes."""
        import html
        safe = ''.join(c for c in str(title) if c.isalnum() or c in '-_ ')[:80].strip() or 'painting'
        p = ROOT / 'creative' / 'paint' / f'{safe}.svg'
        p.parent.mkdir(parents=True, exist_ok=True)
        lines=[]
        for stroke in list(strokes or [])[:64]:
            try:
                pts=list(stroke)[:64]
                if len(pts)<2: continue
                d=' '.join(f'{float(x):.1f},{float(y):.1f}' for x,y in pts)
                lines.append(f'<polyline points="{html.escape(d)}" fill="none" stroke="#93c5fd" stroke-width="6" stroke-linecap="round"/>')
            except Exception: continue
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="100%" height="100%" fill="#0f172a"/>'+''.join(lines)+'</svg>'
        p.write_text(svg, encoding='utf-8')
        self.log('paint', path=str(p), strokes=len(lines))
        return str(p)
