#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import Model

if __name__ == "__main__":
    #processor = Website_generator()
    #processor.json_from_dir('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')
    model = Model()
    model.dir2db('/opt/storage/2019/2019-04_vladivostok','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2018/2018-07_vladivostok','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2010/2010-10_ramenskoe','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2013/2013-08_shelkovo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2021/2021-10_konobeevo','https://trolleway.com/storage')
    #model.dir2db('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')