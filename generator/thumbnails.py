import os
from tqdm import tqdm
import subprocess



def thumbnails_create(src_dir, dst_dir):
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
        photo_thumbnail(photo['src'],photo['dst'])

        pbar.update(1)
    pbar.close()

def photo_thumbnail(src,dst):

    '''
     "-define jpeg:size=" for the image being read in.
     This is passed to the JPEG library, which will return an image somewhere
     between this size and double this size (if possible), rather that the whole
     very large original image. Basically don't overflow the computers memory
     with an huge image when it isn't needed.
    '''
    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.jpg')
    cmd = ['convert' ,  src , '-auto-orient' , path_resized]
    subprocess.run(cmd)
    
    if (check_exists == False and os.path.isfile(os.path.basename(os.path.splitext(dst)[0])+'.webp') == False):

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.webp')
    cmd = ['convert' ,  src , '-auto-orient' ,
    '-define', 'webp:image-hint=photo',
    '-define', 'webp:near-loseless=90',
    '-define', 'webp:method=5',
    '-define', 'webp:thread-level=1',
    path_resized]
    subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.jpg')
    cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'50' , src , '-auto-orient',
          '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
    subprocess.run(cmd)

    path_resized = os.path.join(os.path.dirname(dst) , os.path.basename(os.path.splitext(dst)[0])+'.t.webp')
    cmd = ['convert' , '-define', 'jpeg:size=800x800' , '-quality' ,'50' , src , '-auto-orient',
          '-thumbnail', '500x500' ,  '-unsharp', '0x.5' , path_resized]
    subprocess.run(cmd)



thumbnails_create('/opt/images_origins','/opt/storage')
