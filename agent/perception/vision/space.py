from __future__ import annotations

def spatial_summary(objects):
    out=[]
    for o in objects:
        x=o['center']['x']; y=o['center']['y']
        horizontal='left' if x < .33 else 'right' if x > .66 else 'center'
        vertical='top' if y < .33 else 'bottom' if y > .66 else 'middle'
        size='large' if o['area_ratio']>.12 else 'medium' if o['area_ratio']>.04 else 'small'
        out.append({**o,'position':f'{vertical}-{horizontal}','size':size})
    return out
