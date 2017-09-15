#!/usr/bin/env python
import os
import sys
import png
import struct


def Tone_Hardcode_PAL(filename):
    useless,lclName = os.path.split(filename)
    outFile = lclName.replace("SHP","PAL")
    
    #Islands I00-FEAT[TRIG].SHP -> ISLAND00.PAL
    if ( lclName[0] == 'I' and lclName[1] != 'S' and lclName[1] != 'N' ):
        outFile = outFile.replace("-FEAT","")
        outFile = outFile.replace("-TRIG","")
        outFile = outFile.replace("I","ISLAND")
    outFile = outFile.replace("LILMAP","ISLAND")


    if ( lclName[0] == 'N' and lclName[1] == 'G' ):
        outFile = "NEWGAME.PAL"
        if ( lclName[2] == 'B' ):
            outFile = "MAINMAP.PAL"

    #NEWGAME
    outFile = outFile.replace("BIGFLOAT","NEWGAME")
    outFile = outFile.replace("GLYPHS","NEWGAME")
    outFile = outFile.replace("LEVIDIF","NEWGAME")
    outFile = outFile.replace("NEWBACK","NEWGAME")

    #EXTEND ?
    outFile = outFile.replace("L-CRYTON","NEWGAME")
    outFile = outFile.replace("L-ENRICH","NEWGAME")
    outFile = outFile.replace("L-EXTEND","NEWGAME")

    #MAP related
    outFile = outFile.replace("END.","MAINMAP.")
    outFile = outFile.replace("ENDGLW","MAINMAP")
    outFile = outFile.replace("MAPBACK","MAINMAP")
    outFile = outFile.replace("SMISLE","MAINMAP")

    #END !
    outFile = outFile.replace("ENDTEMP","ENDGAME")
    outFile = outFile.replace("ENDTEM","ENDGAM")


    #caca
    outFile = outFile.replace("SMREALMS","ENDGAME")
    outFile = outFile.replace("LIFE","ENDGAME")
    outFile = outFile.replace("SEEK","ENDGAME")

    return os.path.join(useless,outFile)
        
        
    

def get_pal(filename):
    if len(sys.argv) < 2:
        print("No SHP file specified.")
        sys.exit(-1)
    palette = None

    palfile = Tone_Hardcode_PAL(filename)
    if len(sys.argv) == 3:
        palfile = sys.argv[2]

    #print(palfile)
    #If we do not have any pal, just try the general one
    if not os.path.isfile(palfile):
        #print("Using default PAL")
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
        if image_count == 1 and False:
            dir, file_ = os.path.split(os.path.abspath(filename))
            dir = os.path.abspath(dir+'..')
        else:
            dir, file_ = os.path.split(os.path.abspath(filename))
            dir = os.path.join(dir, filename.replace(".shp", ""))
            dir = os.path.join(dir, filename.replace(".SHP", ""))
            if not os.path.isdir(dir):
                os.makedirs(dir)
        #print("Count : ",image_count)
        IndMax = os.path.getsize(filename)
        for i in range(image_count):
            off_dat = struct.unpack('<I', handle.read(4))[0]
            off_pal = struct.unpack('<I', handle.read(4))[0]
            off_restore = handle.tell()

            palette = pal0
            if off_pal != 0:
                handle.seek(off_pal)
                print("Skipping ",filename," custom pal not supported !")
                #palette = read_palette(handle)
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



    x_RealStart = x_start + x_center;
    
    if (x_start > (width-1)) or (y_start > (height-1)):
        #print("Unable to create {} (w:{}, h:{}, x:{}, y:{}).".format(testname, width, height, x_start, y_start))
        return

    if ( x_RealStart < 0 ):
        print("Warning using dirty workaround for ", entry)
        x_center -= x_RealStart
    
    top = y_start + y_center
    bottom = y_end + y_center + 1
    left = x_start + x_center
    right = x_end + x_center + 1
    
    #print("ENTRY : ", entry)
    #print("X [",left,";",right,"]" )
    #print("Y [",top,";",bottom,"]" )

    background = [255, 0, 0, 0]
    backgroundSkipped = [0, 128, 0, 0]
    pad_row = backgroundSkipped * width
    pad_left = backgroundSkipped * left
    pad_right = backgroundSkipped * (width - right)

    y = 0
    row = []
    pixels = []

    # This is related to the fact that 1 pixel is 4 byte long
    PerLine = (right - left) << 2;
    
    while y < top:
        pixels.append(pad_row)
        y+=1
    row = []
    while y < bottom:

        row = []
        x = 0
        
        while ( True ):
            byte = handle.read(1)[0]
            
            #End of line, fill with empty and go to next line !
            if byte == 0:
                break
            elif byte == 1:
                px = handle.read(1)[0]
                row += background * px
                x += px
            elif (byte & 1) == 0:
                length = byte >> 1
                clr = palette[handle.read(1)[0]]
                row += clr * length
                x += (length)
            else:
                length = byte >> 1
                for i in range(length):
                    row += palette[handle.read(1)[0]]
                x += length
        #On new lines
        #Small Workaround to avoid overflow
        if (PerLine - len(row)) > 0 :
            row += background * (PerLine - len(row)>>2)
        row = row[:PerLine]
        pixels.append(pad_left + row + pad_right)
        y += 1
        
    while ( y < height ):
        pixels.append(pad_row)
        y += 1
            
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
                palette = get_pal(file)
                extract_shapes(filename, palette)
    else:
        print("One file !")
        filename = os.path.abspath(filename)
        palette = get_pal(filename)
        extract_shapes(filename, palette)

main()
