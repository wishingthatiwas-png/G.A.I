from __future__ import annotations
import cv2
import numpy as np

COLOUR_NAMES = ('red','orange','yellow','green','cyan','blue','purple','pink','white','gray','black')


def _colour_name(h, s, v):
    if v < 45: return 'black'
    if s < 35 and v > 190: return 'white'
    if s < 45: return 'gray'
    if h < 10 or h >= 170: return 'red'
    if h < 22: return 'orange'
    if h < 35: return 'yellow'
    if h < 85: return 'green'
    if h < 100: return 'cyan'
    if h < 135: return 'blue'
    if h < 160: return 'purple'
    return 'pink'


def analyse(frame):
    if frame is None:
        return {'objects': [], 'image': {}}
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(gray, 80, 160)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects=[]
    image_mean = hsv.reshape(-1,3).mean(axis=0)
    for c in contours:
        area=cv2.contourArea(c)
        if area < max(80, w*h*0.002): continue
        x,y,cw,ch=cv2.boundingRect(c)
        aspect=cw/max(1,ch)
        peri=cv2.arcLength(c,True)
        approx=cv2.approxPolyDP(c,0.04*peri,True)
        shape={3:'triangle',4:'quadrilateral',5:'pentagon',6:'hexagon'}.get(len(approx),'polygon')
        cx=(x+cw/2)/w; cy=(y+ch/2)/h
        roi=hsv[y:y+ch,x:x+cw]
        mh,ms,mv=roi.reshape(-1,3).mean(axis=0) if roi.size else (0,0,0)
        objects.append({'shape':shape,'colour':_colour_name(float(mh),float(ms),float(mv)),'area_ratio':area/(w*h),'center':{'x':cx,'y':cy},'aspect':aspect})
    objects.sort(key=lambda o:o['area_ratio'], reverse=True)
    return {'image':{'width':w,'height':h,'mean_hsv':[float(x) for x in image_mean]},'objects':objects[:32]}
