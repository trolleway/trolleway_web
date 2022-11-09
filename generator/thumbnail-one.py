import os, shutil
from tqdm import tqdm
import subprocess

import argparse


def photo_thumbnail(src,dst,overwrite = False):

    #print(src+' to '+dst)
    #quit()

    # small photos from old cameras do not recompressed, just copied instead
    is_small_image = False
    keep_original_file = False
    aspect_ratio_version = False
    
    filesize = os.path.getsize(src)
    if filesize/(1024*1024) < 1.5:
        is_small_image = True
        
    if 'ORIGINALFILE' in src:
        keep_original_file = True
    if 'ar169' in src or 'arvert' in src:
        aspect_ratio_version = True


    '''
     "-define jpeg:size=" for the image being read in.
     This is passed to the JPEG library, which will return an image somewhere
     between this size and double this size (if possible), rather that the whole
     very large original image. Basically don't overflow the computers memory
     with an huge image when it isn't needed.
    '''

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.jpg')
    if (is_small_image or keep_original_file) and src.lower().endswith('.jpg'):
        shutil.copyfile(src,path_resized)
    elif aspect_ratio_version:
        pass 
        #not create jpg
    else:
        if ( os.path.isfile(path_resized) == False or overwrite ):
            if not args.squash: 
                cmd = ['convert', src , '-auto-orient' , '-compress', 'JPEG', '-quality', '80', path_resized]
            else:
                cmd = ['convert', src , '-auto-orient' , '-compress', 'JPEG', '-quality', '70', path_resized]
            subprocess.run(cmd)
    #apply exif tags from sidecar file if exist
    src_file_basepart = os.path.splitext(src)[0]
    if os.path.isfile(src_file_basepart + '.xmp'):
        cmd = ['/opt/exiftool/exiftool', '-charset', 'utf8', '-tagsfromfile', src_file_basepart+'.xmp', '-overwrite_original',  path_resized]        #'-all:all' ,
        print(cmd)
        subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.webp')
    if src.lower().endswith('.webp'):
        shutil.copy(src,path_resized)
    elif keep_original_file:
        pass 
        #no create webp
    else:
        if ( os.path.isfile(path_resized) == False or overwrite ):
            if not args.squash: 
                cmd = ['convert' ,  src , '-auto-orient' ,
                '-define', 'webp:image-hint=photo',
                '-define', 'webp:near-loseless=90',
                '-define', 'webp:method=5',
                '-define', 'webp:thread-level=1',
                '-unsharp', '0.5x0.5+0.5+0.008',
                path_resized]
            else:
                cmd = ['convert' ,  src , '-auto-orient' ,
                '-define', 'webp:image-hint=photo',
                '-quality','82',
                #'-define', 'webp:near-loseless=70',
                '-define', 'webp:method=5',
                '-define', 'webp:thread-level=1',
                '-unsharp', '0.5x0.5+0.5+0.008',
                path_resized]
            
            subprocess.run(cmd)
            if os.path.getsize(path_resized)>1024*1024*3:
                cmd = ['convert' ,  src , '-auto-orient' ,
                '-define', 'webp:image-hint=photo',
                '-quality','82',
                '-define', 'webp:method=5',
                '-define', 'webp:thread-level=1',
                '-unsharp', '0.5x0.5+0.5+0.008',
                path_resized]
            
                subprocess.run(cmd) 

        #add metadata to webp. prorably not work due not implementation in exiftool
        if os.path.isfile(src_file_basepart + '.xmp'):
            cmd = ['/opt/exiftool/exiftool', '-charset', 'utf8', '-tagsfromfile', src_file_basepart+'.xmp', '-overwrite_original',  path_resized]        #'-all:all' ,
            print(cmd)
            subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.jpg')
    if not aspect_ratio_version:
        if ( os.path.isfile(path_resized) == False or overwrite ):
            if not args.squash:
                cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'35' , src , '-auto-orient',
                      '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
            else:
                cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'30' , src , '-auto-orient',
                      '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
            subprocess.run(cmd)

        path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.webp')
        if ( os.path.isfile(path_resized) == False or overwrite ):
            if not args.squash:
                cmd = ['convert' , '-quality' ,'70',  src , '-auto-orient', '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
            else:    
                cmd = ['convert' , '-quality' ,'65',  src , '-auto-orient', '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
            subprocess.run(cmd)

#-define', 'webp:near-loseless=60'

parser = argparse.ArgumentParser(description="Compress one picture for website. \n Keys in filenames: \n - ORIGINALFILE: copy jpeg, do not create webp \n - arvert: \n - ar169: ")
parser.add_argument('src')
parser.add_argument('dst')
parser.add_argument('--overwrite', required=False,  action='store_true')
parser.add_argument('--no-overwrite', dest='overwrite', required=False,  action='store_false')
parser.add_argument('--squash', required=False,  action='store_true')
parser.add_argument('--no-squash', dest='squash', required=False,  action='store_false')
parser.set_defaults(overwrite=False)

args = parser.parse_args()
photo_thumbnail(args.src, args.dst, args.overwrite)
