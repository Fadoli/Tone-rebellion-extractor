#!/usr/bin/env python
import os
import sys
import png
import struct


def get_pal(filename):
    if len(sys.argv) < 2:
        print("No SHP file specified.")
        sys.exit(-1)
    palette = None

    palfile = filename.replace(".SHP",".PAL")
    if len(sys.argv) == 3:
        palfile = sys.argv[2]

    #If we do not have any pal, just try the general one
    if not os.path.isfile(palfile):
        palfile = "GAME.PAL"
        
    #Load the PAL :D
    if os.path.isfile(palfile):
        palfile = open(palfile, 'rb')
        palette = read_palette(palfile)
        palfile.close()

    return palette


def extract_shapes(filename, pal0):
        handle = open(filename, 'rb')
        magic = struct.unpack('<I', handle.read(4))[0]
        if magic != 0x30312E31:
            raise Exception("Invalid SHP file (bad signature).")
        image_count = struct.unpack('<I', handle.read(4))[0]
        startname = os.path.basename(filename).replace(".SHP", "") + "_"
        if image_count == 1:
            dir, file_ = os.path.split(os.path.abspath(filename))
            dir = os.path.abspath(dir+'..')
        else:
            dir, file_ = os.path.split(os.path.abspath(filename))
            dir = os.path.join(dir, filename.replace(".shp", ""))
            dir = os.path.join(dir, filename.replace(".SHP", ""))
            if not os.path.isdir(dir):
                os.makedirs(dir)
        for i in range(image_count):
            off_dat = struct.unpack('<I', handle.read(4))[0]
            off_pal = struct.unpack('<I', handle.read(4))[0]
            off_restore = handle.tell()

            palette = pal0
            if off_pal != 0:
                handle.seek(off_pal)
                print("Skipping ",filename," custom pal not supported !")
                #palette = read_palette()
                return
            elif pal0 is None:
                print("Default palette required for {}/{}; skipping...".format(i+1, image_count))
                continue

            handle.seek(off_dat)
            shp_to_png(startname, dir, palette, handle, i+1, image_count)
            handle.seek(off_restore)


def read_palette(handle, size=256):
    entries = []
    for index in range(size):
        rgb = handle.read(3)
        entries.append([rgb[0] << 2, rgb[1] << 2, rgb[2] << 2, 0xFF])
    return entries


def shp_to_png(startname, dir, palette, handle, entry, total):
    __, parent = os.path.split(dir)
    idxlen = len("{}".format(total))
    pngstr = startname + "{}".format(entry).rjust(idxlen, '0')
    pngstr = "".join([pngstr, '.png'])
    filename = os.path.join(dir, pngstr)
    testname = os.path.join(parent, pngstr)


    height = 1 + struct.unpack('<H', handle.read(2))[0]
    width = 1 + struct.unpack('<H', handle.read(2))[0]


    y_center = struct.unpack('<H', handle.read(2))[0]
    x_center = struct.unpack('<H', handle.read(2))[0]
    
    x_start  = struct.unpack('<i', handle.read(4))[0]
    y_start  = struct.unpack('<i', handle.read(4))[0]
    x_end    = struct.unpack('<i', handle.read(4))[0]
    y_end    = struct.unpack('<i', handle.read(4))[0]

    #print("X [",x_start,";",x_end,"] , center at " , x_center , " size : " , width )
    #print("Y [",y_start,";",y_end,"] , center at " , y_center , " size : " , height )

    x_RealStart = x_start + x_center;
    
    if (x_start > (width-1)) or (y_start > (height-1)):
        #print("Unable to create {} (w:{}, h:{}, x:{}, y:{}).".format(testname, width, height, x_start, y_start))
        return

    if ( x_RealStart < 0 ):
        print("Warning using dirty workaround for ", entry)
        x_center -= x_RealStart

    top = y_start + y_center
    bottom = y_end + y_center
    left = x_start + x_center
    right = x_end + x_center

    background = [0, 0, 0, 0]
    backgroundSkipped = [0, 128, 0, 0]
    pad_row = backgroundSkipped * width
    pad_left = backgroundSkipped * left

    y = 0
    row = []
    pixels = []

    # this doesn't seem right... but works
    plane_width = width << 2
    read_width = (right) << 2
    if plane_width > read_width:
        read_width = plane_width

    while y < top:
            pixels.append(pad_row)
            y+=1
    while y < bottom:

        if len(row) == 0:
            row += pad_left
        try:
            b = handle.read(1)[0]
        except Exception as e:
            print("Unable to create {} (hit EOF at {},{} of {},{}).".format(testname, len(row) >> 2, y, width, height))
            return
        
        #End of line, fill with empty and go to next line !
        if b == 0:
            #Small Workaround to avoid overflow
            if (read_width - len(row)) < plane_width:
                row += backgroundSkipped * ((read_width - len(row))>>2)
            row = row[:plane_width]
            pixels.append(row)
            row = []
            y += 1
        elif b == 1:
            px = handle.read(1)[0]
            row += background * px
        elif (b & 1) == 0:
            clr = palette[handle.read(1)[0]]
            for i in range(b >> 1):
                row += clr
        else:
            for i in range(b >> 1):
                clr = palette[handle.read(1)[0]]
                row += clr

    while ( y < height ):
            pixels.append(pad_row)
            y+=1
            
    fout = open(filename, 'wb')
    w = png.Writer(width=width, height=height, bitdepth=8, alpha=True)
    w.write(fout, pixels)
    fout.close()


def main():
    filename = sys.argv[1]
    current_dir, useless = os.path.split(os.path.abspath(filename))
    if os.path.basename(filename)[0] == '*':
        for file in os.listdir(current_dir):
            if file.endswith(".SHP"):
                filename = os.path.abspath(file)
                palette = get_pal(filename)
                extract_shapes(filename, palette)
    else:
        print("One file !")
        filename = os.path.abspath(filename)
        palette = get_pal(filename)
        extract_shapes(filename, palette)

main()
