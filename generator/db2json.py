#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse, os
from model import Model



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Make intermediate JSON from database')
    parser.add_argument('--recent', action='store_true', help='process only recend updated pages, useful for watch changes')
    args = parser.parse_args()
    

  
    model = Model()
    model.db2gallery_jsons(process_recently_updated = args.recent)
    model.pages_index_jsons()
    