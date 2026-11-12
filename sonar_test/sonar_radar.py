import tkinter as tk
import math
import re
import sys
import time

try:
    import serial
except ImportError:
    raise SystemExit('PySerial missing: sudo apt install python3-serial')

PORT = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
BAUD = 115200
WIDTH_IN = 26
LENGTH_IN = 47
COLORS = {'RED':'#e74c3c','ORANGE':'#f39c12','YELLOW':'#f4d03f','GREEN':'#2ecc71','UNKNOWN':'#64748b'}
LABELS = {1:'Front left',2:'Left front',3:'Left rear',4:'Rear left',5:'Front right',6:'Right front',7:'Right rear',8:'Rear right'}

root=tk.Tk()
root.title('CENTAUR | Sonar Radar')
root.geometry('1100x850')
root.minsize(760,620)
root.configure(bg='#0c1420')

header=tk.Frame(root,bg='#0c1420')
header.pack(fill='x',padx=18,pady=(14,5))
tk.Label(header,text='CENTAUR  /  SONAR RADAR',font=('Arial',19,'bold'),fg='white',bg='#0c1420').pack(side='left')
connection=tk.Label(header,text='Connecting...',font=('Arial',11),fg='#f4d03f',bg='#0c1420')
connection.pack(side='right')

main=tk.Frame(root,bg='#0c1420')
main.pack(fill='both',expand=True,padx=12,pady=6)
canvas=tk.Canvas(main,bg='#0c1420',highlightthickness=0)
canvas.pack(side='left',fill='both',expand=True)
side=tk.Frame(main,bg='#152131',width=245)
side.pack(side='right',fill='y',padx=(8,0))
side.pack_propagate(False)
tk.Label(side,text='LIVE SENSOR READINGS',bg='#152131',fg='white',font=('Arial',13,'bold')).pack(pady=(16,12))
rows=[]
for i in range(1,9):
    frame=tk.Frame(side,bg='#152131')
    frame.pack(fill='x',padx=12,pady=5)
    tag=tk.Label(frame,text=f'S{i}',bg='#64748b',fg='white',font=('Arial',11,'bold'),width=3)
    tag.pack(side='left')
    detail=tk.Frame(frame,bg='#152131')
    detail.pack(side='left',fill='x',expand=True,padx=8)
    tk.Label(detail,text=LABELS[i],bg='#152131',fg='#cbd5e1',font=('Arial',10)).pack(anchor='w')
    value=tk.Label(detail,text='NO DATA',bg='#152131',fg='white',font=('Arial',12,'bold'))
    value.pack(anchor='w')
    rows.append((tag,value))

tk.Label(side,text='DISTANCE ZONES',bg='#152131',fg='white',font=('Arial',12,'bold')).pack(pady=(28,10))
for text,color in [('RED     0–6 in',COLORS['RED']),('ORANGE  >6–12 in',COLORS['ORANGE']),('YELLOW  >12–24 in',COLORS['YELLOW']),('GREEN   >24 in',COLORS['GREEN']),('GRAY    No echo',COLORS['UNKNOWN'])]:
    tk.Label(side,text=text,fg=color,bg='#152131',font=('Arial',11,'bold'),anchor='w').pack(fill='x',padx=18,pady=4)

footer=tk.Label(root,text='26 in wide × 47 in long  |  Visual warnings only — not a collision-avoidance controller',bg='#0c1420',fg='#94a3b8',font=('Arial',10))
footer.pack(pady=(0,12))

readings=[None]*8
last_seen=[0.0]*8
ser=None
rx_buffer=bytearray()

def state(distance):
    if distance is None:return 'UNKNOWN'
    if distance<=6:return 'RED'
    if distance<=12:return 'ORANGE'
    if distance<=24:return 'YELLOW'
    return 'GREEN'

def poly(points,**kwargs):
    canvas.create_polygon([coord for p in points for coord in p],**kwargs)

def draw():
    canvas.delete('all')
    w=max(400,canvas.winfo_width())
    h=max(500,canvas.winfo_height())
    cx=w/2;cy=h/2
    # Keep actual 26:47 aspect ratio, and leave room for three finite bands plus green outer zone.
    scale=min((w-110)/(WIDTH_IN+96),(h-110)/(LENGTH_IN+96),4.8)
    hx=WIDTH_IN*scale/2;hy=LENGTH_IN*scale/2
    offsets=[0,6*scale,12*scale,24*scale,48*scale]
    # Divide front/rear into two halves and each long side into two halves.
    # Draw independent bands: colored up to the current reading; outer area remains subdued.
    def bounds(d):return (cx-hx-d,cy-hy-d,cx+hx+d,cy+hy+d)
    def patch(sensor,inner,outer):
        x1,y1,x2,y2=bounds(inner);a1,b1,a2,b2=bounds(outer)
        if sensor==1:return [(x1,y1),(cx,y1),(cx,b1),(a1,b1)]
        if sensor==5:return [(cx,y1),(x2,y1),(a2,b1),(cx,b1)]
        if sensor==4:return [(x1,y2),(cx,y2),(cx,b2),(a1,b2)]
        if sensor==8:return [(cx,y2),(x2,y2),(a2,b2),(cx,b2)]
        if sensor==2:return [(x1,y1),(a1,b1),(a1,cy),(x1,cy)]
        if sensor==3:return [(x1,cy),(a1,cy),(a1,b2),(x1,y2)]
        if sensor==6:return [(x2,y1),(a2,b1),(a2,cy),(x2,cy)]
        return [(x2,cy),(a2,cy),(a2,b2),(x2,y2)]
    for i in range(1,9):
        val=readings[i-1]
        for band in range(4):
            lower=[0,6,12,24][band]
            active=val is not None and val>lower
            # Critical readings also light up the innermost band.
            if band==0 and val is not None:active=True
            color=COLORS[state(val)] if active else '#1d2a3b'
            poly(patch(i,offsets[band],offsets[band+1]),fill=color,outline='#334155',width=2)
    # Body
    x1,y1,x2,y2=bounds(0)
    canvas.create_rectangle(x1,y1,x2,y2,fill='#09121d',outline='white',width=3)
    canvas.create_text(cx,cy-28,text='▲ FRONT',fill='#e2e8f0',font=('Arial',11,'bold'))
    canvas.create_text(cx,cy,text='CENTAUR',fill='white',font=('Arial',16,'bold'))
    canvas.create_text(cx,cy+24,text='26″ × 47″',fill='#cbd5e1',font=('Arial',11))
    canvas.create_text(cx,cy+48,text='▼ REAR',fill='#e2e8f0',font=('Arial',11,'bold'))
    # Labels along the outer edges
    far=offsets[-1]
    for i in range(1,9):
        if i in (1,5):
            x=cx+(-hx/2 if i==1 else hx/2);y=cy-hy-far+14
        elif i in (4,8):
            x=cx+(-hx/2 if i==4 else hx/2);y=cy+hy+far-14
        else:
            x=cx+(-hx-far+27 if i in (2,3) else hx+far-27)
            y=cy+(-hy/2 if i in (2,6) else hy/2)
        val=readings[i-1]
        label=f'S{i}\n'+('NO ECHO' if val is None else f'{val:.1f} in')
        canvas.create_text(x,y,text=label,fill='white',font=('Arial',10,'bold'),justify='center')
    for i,(tag,value) in enumerate(rows):
        val=readings[i]
        tag.configure(bg=COLORS[state(val)])
        value.configure(text='NO ECHO' if val is None else f'{val:.1f} in')

def poll():
    global ser
    if ser is not None:
        try:
            data=ser.read(min(4096,ser.in_waiting or 1))
            rx_buffer.extend(data)
            # Process only complete lines, so partial USB packets are not lost.
            while b'\n' in rx_buffer:
                raw,_,remaining=rx_buffer.partition(b'\n')
                rx_buffer[:]=remaining
                m=re.match(r'\s*Sensor\s+(\d+):\s*(NO ECHO|[-+]?\d+(?:\.\d+)?)',raw.decode(errors='ignore'),re.I)
                if m:
                    n=int(m.group(1))
                    if 1<=n<=8:
                        token=m.group(2)
                        cm=None if token.upper()=='NO ECHO' else float(token)
                        readings[n-1]=None if cm is None or cm<0 else cm/2.54
                        last_seen[n-1]=time.monotonic()
            if len(rx_buffer)>4096:rx_buffer.clear()
            connection.configure(text=f'CONNECTED  {PORT}',fg='#2ecc71')
        except (OSError,serial.SerialException) as exc:
            connection.configure(text=f'DISCONNECTED: {exc}',fg='#e74c3c')
            try:ser.close()
            except Exception:pass
            ser=None
    now=time.monotonic()
    for i in range(8):
        if now-last_seen[i]>4:readings[i]=None
    draw()
    root.after(150,poll)

def shutdown():
    if ser is not None:ser.close()
    root.destroy()

try:
    ser=serial.Serial(PORT,BAUD,timeout=0)
except (OSError,serial.SerialException) as exc:
    connection.configure(text=f'PORT ERROR: {exc}',fg='#e74c3c')

root.protocol('WM_DELETE_WINDOW',shutdown)
canvas.bind('<Configure>',lambda event:draw())
root.after(100,poll)
root.mainloop()

