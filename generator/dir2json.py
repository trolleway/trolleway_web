#!/usr/bin/python
# -*- coding: utf-8 -*-

from model import Model

if __name__ == "__main__":
    #processor = Website_generator()
    #processor.json_from_dir('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')
    model = Model()
    #model.dir2db('/opt/storage/2022/2022-07_moscow','https://trolleway.com/storage')
    model.dir2db('/opt/storage/2022/2022-07_retroreis','https://trolleway.com/storage')