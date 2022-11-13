import os, shutil
from tqdm import tqdm
import subprocess

import argparse



def thumbnails_create(src_dir, dst_dir, check_exists = False, squash=False, path=None):
    '''
    create thumbnails for tree
    '''
    
    if path:
        optional_path = os.path.join(src_dir,path)
        assert os.path.isdir(optional_path),'must exist '+optional_path
    
    accepted_exts = ['.jpg','.jpeg','.tif','.tiff','.webp']
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
    
    source_dir = src_dir
    if path: source_dir = optional_path
    for dirpath, dnames, fnames in os.walk(source_dir):
        for file in fnames:
            if file.lower().endswith(tuple(accepted_exts)) == False: continue
            src =  os.path.join(dirpath,file)
            dst = os.path.join(dirpath.replace(src_dir,dst_dir),file)

            convert_tuples.append({'src':src,'dst':dst})
            
    if squash:
        squash_key = '--squash'
    else:
        squash_key = ''



    arguments_list_text = ''
    for photo in convert_tuples:
        arguments_list_text += '''{src} ; {dst}\n'''.format(src=photo['src'],dst=photo['dst'])
        #arguments_list_text += '''"{src}";"{dst}"\n'''.format(src=photo['src'][-30:],dst=photo['dst'][-30:])

    with open("parallel.list", "w") as text_file:
        text_file.write(arguments_list_text)

    cmd = '''parallel --eta --bar  --colsep ';' python3 '''+os.path.join(os.path.dirname(os.path.realpath(__file__)),'thumbnail-one.py')+ ''' {1} {2} --no-overwrite '''+squash_key+'''  :::: < parallel.list'''

    os.system(cmd)


parser = argparse.ArgumentParser(description='Compress all picture for website')

parser.add_argument('--squash', required=False,  action='store_true')
parser.add_argument('--no-squash', dest='squash', required=False,  action='store_false')
parser.add_argument('--path', dest='path', required=False,  help='subdirectory path for process only one dir')


args = parser.parse_args()

#thumbnails_create('/opt/images_origins','/opt/storage',check_exists = True)
#thumbnails_create('/home/trolleway/VirtualBoxShared/website-expose-transfer','/media/trolleway/UBUNTU 22_0/thumbnails',check_exists = True)
thumbnails_create('/opt/images_origins','/opt/storage',check_exists = True,squash = args.squash, path = args.path )
