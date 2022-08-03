import os
from tqdm import tqdm
import subprocess



def thumbnails_create(src_dir, dst_dir, check_exists = False):
    '''
    create thumbnails for tree
    '''
    assert os.path.isdir(src_dir)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    '''
    dst_path = os.path.dirname(os.path.abspath(dst_dir))
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    '''
    #create dirs
    paths = []
    for dirpath, dnames, fnames in os.walk(src_dir):
        for dir in dnames:
            paths.append(os.path.join(dirpath, dir))
    for path in paths:
        newpath = path.replace(src_dir,dst_dir) #potential fail place
        if not os.path.isdir(newpath):
            os.makedirs(newpath)

    convert_tuples = []
    for dirpath, dnames, fnames in os.walk(src_dir):
        for file in fnames:
            src =  os.path.join(dirpath,file)
            dst = os.path.join(dirpath.replace(src_dir,dst_dir),file)

            convert_tuples.append({'src':src,'dst':dst})


    pbar = tqdm(total=len(convert_tuples))

    for photo in convert_tuples:
        tqdm.write("Generate thumbnail for %s" % photo['src'])
        photo_thumbnail(photo['src'],photo['dst'],check_exists )

        pbar.update(1)
    pbar.close()

def photo_thumbnail(src,dst,check_exists = False):

    '''
     "-define jpeg:size=" for the image being read in.
     This is passed to the JPEG library, which will return an image somewhere
     between this size and double this size (if possible), rather that the whole
     very large original image. Basically don't overflow the computers memory
     with an huge image when it isn't needed.
    '''
    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.jpg')
    if ( os.path.isfile(path_resized) == False or check_exists == False ):

        cmd = ['convert' ,  src , '-auto-orient' , '-compress', 'JPEG', '-quality', '80', path_resized]
        subprocess.run(cmd)
        filesize = os.path.getsize(path_resized)
        if filesize/(1024*1024) > 3:
            print(path_resized,filesize)
        
    
    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.webp')
    if ( os.path.isfile(path_resized) == False or check_exists == False ):
        cmd = ['convert' ,  src , '-auto-orient' ,
        '-define', 'webp:image-hint=photo',
        '-define', 'webp:near-loseless=90',
        '-define', 'webp:method=5',
        '-define', 'webp:thread-level=1',
        path_resized]
        subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.jpg')
    if ( os.path.isfile(path_resized) == False or check_exists == False ):
        cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'40' , src , '-auto-orient',
              '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
        subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.webp')
    if ( os.path.isfile(path_resized) == False or check_exists == False ):
        cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'60' , src , '-auto-orient',
              '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
        subprocess.run(cmd)



thumbnails_create('/opt/images_origins','/opt/storage',check_exists = True)
