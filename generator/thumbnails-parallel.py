import os, shutil
from tqdm import tqdm
import subprocess



def thumbnails_create(src_dir, dst_dir, check_exists = False):
    '''
    create thumbnails for tree
    '''

    accepted_exts = ['.jpg','.jpeg','.tif','.tiff']
    assert os.path.isdir(src_dir)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

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
            if file.lower().endswith(tuple(accepted_exts)) == False: continue
            src =  os.path.join(dirpath,file)
            dst = os.path.join(dirpath.replace(src_dir,dst_dir),file)

            convert_tuples.append({'src':src,'dst':dst})



    arguments_list_text = ''
    for photo in convert_tuples:
        arguments_list_text += '''{src} ; {dst}\n'''.format(src=photo['src'],dst=photo['dst'])
        #arguments_list_text += '''"{src}";"{dst}"\n'''.format(src=photo['src'][-30:],dst=photo['dst'][-30:])

    with open("parallel.list", "w") as text_file:
        text_file.write(arguments_list_text)

    cmd = '''parallel --eta --bar  --colsep ';' python3 '''+os.path.join(os.path.dirname(os.path.realpath(__file__)),'thumbnail-one.py')+ ''' {1} {2} --no-overwrite :::: < parallel.list'''

    os.system(cmd)
    '''




    '''



#thumbnails_create('/opt/images_origins','/opt/storage',check_exists = True)
#thumbnails_create('/home/trolleway/VirtualBoxShared/website-expose-transfer','/media/trolleway/UBUNTU 22_0/thumbnails',check_exists = True)
thumbnails_create('/opt/images_origins','/opt/storage',check_exists = True)
