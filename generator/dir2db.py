#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse, os
from model import Model



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Import directory with images, create thumbnails and make sql')

    parser.add_argument('path',   help='path')


    args = parser.parse_args()
    
    args.path = args.path.replace('images_origins','storage')

    if not os.path.isdir(args.path):
        raise FileNotFoundError(args.path)


    model = Model()
    
    model.dir2db(args.path,'https://trolleway.com/storage')
    

    
