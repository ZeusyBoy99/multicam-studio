#!/usr/bin/env python3
"""Draw the application mark using macOS's vector drawing API."""
from pathlib import Path
import subprocess
import tempfile
from AppKit import NSImage, NSBezierPath, NSColor, NSBitmapImageRep, NSPNGFileType
from Foundation import NSMakeRect

DESTINATION = Path(__file__).resolve().parent / 'MulticamStudio.icns'

def color(hexcode):
    value = hexcode.lstrip('#')
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(int(value[:2],16)/255,int(value[2:4],16)/255,int(value[4:],16)/255,1)

def rect(x,y,w,h,r,fill):
    color(fill).setFill()
    NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(x,y,w,h),r,r).fill()

def main():
    image=NSImage.alloc().initWithSize_((1024,1024))
    image.lockFocus()
    rect(32,32,960,960,218,'142221')
    rect(108,108,808,808,150,'1D3330')
    rect(174,279,676,464,84,'9BE3BA')
    rect(210,315,604,392,56,'142221')
    rect(263,369,169,284,31,'9BE3BA')
    rect(585,369,169,284,31,'73A9BD')
    color('F0B56D').setStroke()
    slash=NSBezierPath.bezierPath()
    slash.moveToPoint_((456,316));slash.lineToPoint_((570,708))
    slash.setLineWidth_(35);slash.setLineCapStyle_(1);slash.stroke()
    rect(263,592,169,61,20,'C5F4D9')
    rect(585,592,169,61,20,'A6D5E3')
    image.unlockFocus()
    representation=NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
    with tempfile.TemporaryDirectory(prefix='multicam-icon-') as folder:
        folder=Path(folder);source=folder/'source.png';icons=folder/'Studio.iconset';icons.mkdir()
        representation.representationUsingType_properties_(NSPNGFileType,{}).writeToFile_atomically_(str(source),True)
        for size in (16,32,128,256,512):
            for scale in (1,2):
                name=f'icon_{size}x{size}'+('@2x' if scale==2 else '')+'.png'
                subprocess.run(['/usr/bin/sips','-z',str(size*scale),str(size*scale),str(source),'--out',str(icons/name)],stdout=subprocess.DEVNULL,check=True)
        subprocess.run(['/usr/bin/iconutil','-c','icns',str(icons),'-o',str(DESTINATION)],check=True)
    print(DESTINATION)

if __name__=='__main__':main()
