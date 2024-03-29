#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse, os
from model import Model



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Import directory with images, create thumbnails and make sql')

    #parser.add_argument('--squash', required=False,  action='store_true')
    #parser.add_argument('--no-squash', dest='squash', required=False,  action='store_false')
    parser.add_argument('path',   help='path')


    args = parser.parse_args()
    
    args.path = args.path.replace('images_origins','storage')

    if not os.path.isdir(args.path):
        raise FileNotFoundError(args.path)


    #processor = Website_generator()
    #processor.json_from_dir('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')
    model = Model()
    
    model.dir2db(args.path,'https://trolleway.com/storage')
    
    #model.dir2db('/opt/storage/2014/2014-02-peshelan-railway','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2014/2014-02-kerzenets-railway','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-11-vereya','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2010/2010-04-polotsk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-sakhalin2','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-11-winzavod','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2020/2020-06-film','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2015/2015-12-lipetsk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2009/2009-07-lomography-fisheye','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-11-voskresensk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-23-vladivostok','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-14-habarovsk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-11-sakhalin','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2006/2006-04-ikarus-280','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2003/2003-03-tatrat7','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2003/2003-01-moscow-tmrp2','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2013/2013-05_visokovsk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2018/2018-12_novosibirsk','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2003/2003-08-svarz-ikarus2','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2003/2003-11-tula-trolleybus','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2003/2003-11-tula-tram','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2014/2014-08-zil','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2012/2012-03-polymus','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2015/2015-10-semigorodnaya','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-10-kizhi','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2012/2012-07-liaz677m','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-10-sakhalin','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-07-sakhalin','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2014/2014-05-alapaevsk-railway','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2014/2014-05-alapaevsk-city','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2019/2019-11-stupino','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2019/2019-11-mihnevo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-15_vvo_silbera50_nikon_coolscan','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-20_vvo_silbera50','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-08-sakhalin','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2021/2021-11-khrapunovo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2020/2020-07-01_film','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/rail/RZD ChS2','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2019/2019-04_vladivostok','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2018/2018-07_vladivostok','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2010/2010-10_ramenskoe','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2013/2013-08_shelkovo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2021/2021-10_konobeevo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')
    
    
