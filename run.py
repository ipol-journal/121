#!/usr/bin/env python3

import subprocess
import argparse
import PIL.Image
import math
import sys


# parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("scalefactor", type=float)
ap.add_argument("psfsigma", type=float)
ap.add_argument("action", type=str)
args = ap.parse_args()

grid = "centered"

img = PIL.Image.open('input_0.png')
(sizeX, sizeY) = img.size        
p = {}
logfile = open('log.txt', 'w')

if args.action == "Interpolate":
    # In this run mode, the interpolation is performed directly on the
    # selected image, and the estimated contours are also shown.
    
    # If the image dimensions are small, zoom the displayed results.
    # This value is always at least 1.
    displayzoom = int(math.ceil(400.0/(args.scalefactor*max(sizeX, sizeY))))
    # Check that interpolated image dimensions are not too large
    cropsize = (min(sizeX, int(800/args.scalefactor)),
        min(sizeY, int(800/args.scalefactor)))
    
    if (sizeX, sizeY) != cropsize:
        (x0, y0) = (int(math.floor((sizeX - cropsize[0])/2)),
            int(math.floor((sizeY - cropsize[1])/2)))
        imgcrop = img.crop((x0, y0, x0 + cropsize[0], y0 + cropsize[1]))
        imgcrop.save('input_0.png')
    
    p = {
        # Perform the actual contour stencil interpolation
        'interp' : 
            subprocess.run(['sinterp', '-g', grid, '-x', str(args.scalefactor), '-p', str(args.psfsigma), 'input_0.png', 'interpolated.png']),
            
        # For display, create a nearest neighbor zoomed version of the
        # input. nninterp does nearest neighbor interpolation on 
        # precisely the same grid so that displayed images are aligned.
        'inputzoom' : 
            subprocess.run(['nninterp', '-g', grid, '-x', str(args.scalefactor*displayzoom), 'input_0.png', 'input_0_zoom.png']),
            
        # Generate an image showing the estimated contour orientations
        'contour' : 
            subprocess.run(['sinterp', '-s', '-g', grid, '-x', str(args.scalefactor*displayzoom), '-p', str(args.psfsigma), 'input_0.png', 'contour.png']),
            
        # Estimated contour orientations as EPS
        'contour-eps' : 
            subprocess.run(['sinterp', '-s', '-g', grid, '-x', str(args.scalefactor*displayzoom), '-p', str(args.psfsigma), 'input_0.png', 'contour.eps']),
            
        # Estimated contour orientations as SVG
        'contour-svg' : 
            subprocess.run(['sinterp', '-s', 
            '-g', grid,
            '-x', str(args.scalefactor*displayzoom), 
            '-p', str(args.psfsigma),
            'input_0.png', 'contour.svg', 'contour-bg.png'],
            stdout=logfile, stderr=logfile)
        }
    
    if displayzoom > 1:
        p['interpzoom'] = subprocess.run(['nninterp', '-g', 'centered', '-x', str(displayzoom), 'interpolated.png', 'interpolated_zoom.png'])

else:
    #write Coarsen=True in algo_info.txt
    with open('algo_info.txt', 'w') as file:
        file.write("Coarsen=1")

    # In this run mode, the selected image is coarsened, interpolated
    # and compared with the original.
                
    # If the image dimensions are small, zoom the displayed results.
    # This value is always at least 1.
    displayzoom = int(math.ceil(350.0/max(sizeX, sizeY)))
    displaysize = (displayzoom*sizeX, displayzoom*sizeY)
    
    # Coarsen the image
    p['coarsened'] = subprocess.run(['imcoarsen', '-g', grid, '-x', str(args.scalefactor), '-p', str(args.psfsigma), 'input_0.png', 'coarsened.png'])
    
    if displayzoom > 1:
        p['exactzoom'] = subprocess.run(['nninterp', '-g', 'centered', '-x', str(displayzoom), 'input_0.png', 'input_0_zoom.png'])
    
    p = {
        'interpolated' : 
            subprocess.run(['sinterp', '-g', grid, '-x', str(args.scalefactor), '-p', str(args.psfsigma), 'coarsened.png', 'interpolated.png']),
                    
        # Generate an image showing the estimated contour orientations
        'contour' :
            subprocess.run(['sinterp', '-s', '-g', grid, '-x', str(args.scalefactor*displayzoom), '-p', str(args.psfsigma), 'coarsened.png', 'contour.png']),
            
        # Estimated contour orientations as EPS
        'contour-eps' :
            subprocess.run(['sinterp', '-s', '-g', grid, '-x', str(args.scalefactor*displayzoom), '-p', str(args.psfsigma), 'coarsened.png', 'contour.eps']),
            
        # Estimated contour orientations as SVG
        'contour-svg' :
            subprocess.run(['sinterp', '-s', '-g', grid, '-x', str(args.scalefactor*displayzoom), '-p', str(args.psfsigma), 'coarsened.png', 'contour.svg', 'contour-bg.png'])
        }

    # For display, create a nearest neighbor zoomed version of the
    # coarsened image.  nninterp does nearest neighbor interpolation 
    # on precisely the same grid as cwinterp so that displayed images
    # are aligned.
    p['coarsened_zoom'] = subprocess.run(['nninterp', '-g', grid, '-x', str(args.scalefactor*displayzoom), 'coarsened.png', 'coarsened_zoom.png'])
                
    # Because of rounding, the interpolated image dimensions might be 
    # slightly larger than the original image.  For example, if the 
    # input is 100x100 and the scale factor is 3, then the coarsened 
    # image has size 34x34, and the interpolation has size 102x102.
    # The following crops the results if necessary.
    img = PIL.Image.open('coarsened_zoom.png')
    
    if displaysize != img.size:
        img.crop((0, 0, displaysize[0], displaysize[1]))
        img.save('coarsened_zoom.png')
        img = PIL.Image.open('contour.png')
        imgcrop = img.crop((0, 0, displaysize[0], displaysize[1]))
        imgcrop.save('contour.png')
    
    img = PIL.Image.open('interpolated.png')
    
    if (sizeX, sizeY) != img.size:
        imgcrop = img.crop((0, 0, sizeX, sizeY))
        imgcrop.save('interpolated.png')
                
    # Generate difference image
    p['difference'] = subprocess.run(['imdiff', 'input_0.png', 'interpolated.png', 'difference.png'])
    # Compute maximum difference, PSNR, and MSSIM
    p['metrics'] = subprocess.run(['imdiff', 'input_0.png', 'interpolated.png'])
    
    if displayzoom > 1:
        p['interpzoom'] = subprocess.run(['nninterp', '-g', 'centered', '-x', str(displayzoom), 'interpolated.png', 'interpolated_zoom.png'])
        p['differencezoom'] = subprocess.run(['nninterp', '-g', 'centered', '-x', str(displayzoom), 'difference.png', 'difference_zoom.png'])

# Convert EPS to PDF
try:
    subprocess.run(['gs', '-dSAFER', '-q', '-P-', '-dCompatibilityLevel=1.4', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pdfwrite', '-sOutputFile=contour.pdf', '-c', '.setpdfwrite', '-f', 'contour.eps'])
except OSError:
    with open("demo_failure.txt", "w") as file:
        file.write("eps->pdf conversion failed,"
            + " gs is probably missing on this system")
        sys.exit(0)
