#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import os
import sqlite3

from shapely import wkt
from shapely.geometry import Point

from iptcinfo3 import IPTCInfo
from exif import Image
from datetime import datetime
from dateutil import parser
from tqdm import tqdm

class Model():


    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    def __init__(self):
        dbpath = os.path.join(os.path.dirname(os.path.realpath(__file__ )),'web.sqlite')
        assert os.path.isfile(dbpath)

        self.con = sqlite3.connect(dbpath)
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #for row in cur.execute('SELECT * FROM photos ORDER BY photoid'):
        #    print(dict(row))
        cur.execute("SELECT * FROM photos ORDER BY photoid")
        results = cur.fetchall()
        assert len(results) > 0

    def dms_to_dd(self,d, m, s):
        dd = d + float(m)/60 + float(s)/3600
        return dd


    def image2datetime(self,path):
        with open(path, 'rb') as image_file:
            image_exif = Image(image_file)
            
            try:
                dt_str = image_exif.get('datetime_original',None)
                dt_obj = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            except:
                dt_obj = None
            

            if dt_obj is None:
                return None
            return dt_obj



    def image2latlon(self,path):
        try:
            with open(path, 'rb') as image_file:
                image_exif = Image(image_file)
                lat_dms=image_exif.gps_latitude
                lat=self.dms_to_dd(lat_dms[0],lat_dms[1],lat_dms[2])
                lon_dms=image_exif.gps_longitude
                lon=self.dms_to_dd(lon_dms[0],lon_dms[1],lon_dms[2])

                photo_coord=str(lat)+','+str(lon)


                lat = str(round(float(lat), 5))
                lon = str(round(float(lon), 5))
                coord = list()
                coord.append(round(float(lat), 5))# , round(float(lon), 4))
                coord.append(round(float(lon), 5))# , round(float(lon), 4))


                return  round(float(lat), 5), round(float(lon), 5)

        except:

            photo_coord='0,0'
            lat='0'
            lon='0'
            return None, None
  
    def locations2dict(self):
        cur = self.con.cursor()

        sql = "SELECT name_ru, name_int FROM locations  ;"
        names = dict()
        for row in cur.execute(sql):
            names[row['name_int']]=row['name_ru']
        
        return names
    
    def dir2db(self,path,base_url=''):

        today = datetime.today()
        assert os.path.isdir(path)

        for (root,dirs,files) in os.walk(path):
            images = list()
            for filename in files:
                if not filename.lower().endswith('.jpg'): continue
                if filename.lower().endswith('.t.jpg'): continue
                
                self.logger.debug(filename)
                temp_path = os.path.normpath(path)
                path_as_list = temp_path.split(os.sep)

                url = base_url + '/' + os.path.join(path_as_list[-2],path_as_list[-1]) + '/' + filename

                info = IPTCInfo(os.path.join(root,filename), force=True)
                city = None
                sublocation = None

                if info['city'] is not None:
                    city = info['city'].decode('UTF-8')
                if info['sub-location'] is not None:
                    sublocation = info['sub-location'].decode('UTF-8')
                    
                caption = info['caption/abstract']
                if caption is not None:
                    caption = caption.decode('UTF-8')
                else:
                    caption = ''
                image = {'caption':caption,'url_hotlink':url}
                if city is not None: image['city']=city
                if sublocation is not None: image['sublocation']=sublocation

                lat,lon=self.image2latlon(os.path.join(root,filename))
                photo_datetime = self.image2datetime(os.path.join(root,filename))
                

                image['wkt_geometry']=wkt.dumps(Point(lon or 0,lat or 0),rounding_precision=5)
                image['datetime']=photo_datetime


                images.append(image)

        #sql="BEGIN TRANSACTION; \n"
        sql = ""
        sql_custom = ""
        values = list()
        for image in images:
            values.append([image['url_hotlink'],image.get('caption',''),image.get('city','')])

            tmpstr = '''INSERT INTO photos (hotlink,caption,city,sublocation,inserting_id, wkt_geometry, datetime, date_append)
            VALUES ( "{hotlink}" , "{caption}", "{city}", "{sublocation}", "{inserting_id}", "{wkt_geometry}", "{datetime}", "{date_append}" );\n  '''
            tmpstr = tmpstr.format(hotlink=image['url_hotlink'],
                inserting_id = today.strftime('%Y-%m-%d-%H%M%S'),
                date_append = today.strftime('%Y-%m-%d'),
                caption = image['caption'],
                datetime = image['datetime'].isoformat() if image['datetime'] is not None else '',
                wkt_geometry = image['wkt_geometry'],
                city = image.get('city',''),
                sublocation = image.get('sublocation','')
                )
            sql += tmpstr
            
            sql_custom += '''UPDATE photos SET city="{city}", sublocation="{sublocation}",datetime="{datetime}", wkt_geometry="{wkt_geometry}"
            WHERE hotlink="{hotlink}"  ;\n '''.format(hotlink=image['url_hotlink'],
                inserting_id = today.strftime('%Y-%m-%d-%H%M%S'),
                caption = image['caption'],
                datetime = image['datetime'].isoformat() if image['datetime'] is not None else '',
                wkt_geometry = image['wkt_geometry'],
                city = image.get('city',''),
                sublocation = image.get('sublocation','')
                )

        page_url = os.path.basename(root)
        sql+='''INSERT INTO pages(uri,title, date_mod, inserting_id, source, order  ) VALUES ("{page_url}", "{date}", "{date}", '{inserting_id}', 'photos','dates' );\n '''.format(
        page_url=page_url,
        inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),
        date=today.strftime('%Y-%m-%d'))
        sql += '''/* INSERT INTO photos_pages (photoid, pageuri, pageid, inserting_id) SELECT photoid, "{page_url}",0, "{inserting_id}"
        FROM photos
        WHERE photos.inserting_id='{inserting_id}'
        ORDER BY photos.hotlink;\n */ '''.format(inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),page_url=page_url,)
        sql += '''-- UPDATE photos_pages SET pageid = (SELECT pageid FROM pages WHERE uri='{page_url}') WHERE pageuri='{page_url}';\n   '''.format(page_url=page_url)
        sql += '''-- UPDATE photos_pages SET pageuri = '';\n   '''

        #sql+="COMMIT;"

        print(sql)
        sql_file = "tmp_add_page.sql"
        with open(sql_file, "w") as caption_file:
            caption_file.write(sql)
        self.logger.info('sql saved to '+sql_file)
        
        sql_file = "tmp_custom.sql"
        with open(sql_file, "w") as caption_file:
            caption_file.write(sql_custom)
        self.logger.info('sql saved to '+sql_file)

        return

        sql='INSERT INTO photos (hotlink,caption,city) VALUES ( ? , ?, ? );'
        cur = self.con.cursor()
        cur.executemany(sql,values)
        self.con.commit()

    '''
    CREATE VIEW photos_pages_view AS SELECT photos_pages."order", photos."caption", pages.uri
FROM photos_pages JOIN photos ON photos_pages.photoid=photos.photoid
JOIN pages ON photos_pages.pageid = pages.pageid
ORDER BY pages.uri, photos_pages."order";
    '''

    def db2gallery_jsons(self,path=os.path.join(os.path.dirname(os.path.realpath(__file__ )),'content')):
        cur_pages = self.con.cursor()
        cur_photos = self.con.cursor()

        locations = self.locations2dict()

        sql = "SELECT COUNT(*) as count FROM pages WHERE hidden=0 ;"
        cur_pages.execute(sql)
        row = cur_pages.fetchone()
        count=row['count']
        pbar = tqdm(total=count)
        
        sql = "SELECT * FROM pages WHERE hidden=0 ;"
        for row in cur_pages.execute(sql):
            
            db_page = dict(row)
            json_path = os.path.join(path,db_page['uri'])+'.json'

            json_content={ "title": db_page['title'],
 "h1": db_page['ha'] or '',
 "text": db_page['text'] or '',
 "text_en": db_page['text_en'] or '',
 "map_center": db_page['map_center_str'] or '',
 "map_zoom": "12",
 "date_mod": db_page['date_mod'] or ''}
            images = list()

            if db_page.get('source','') in ('','photos_pages'):
                sql = '''SELECT photos.*
                FROM photos
                JOIN photos_pages ON photos.photoid=photos_pages.photoid
                JOIN pages ON pages.pageid=photos_pages.pageid
                WHERE photos_pages.pageid={pageid}
                ORDER BY photos_pages.'order' ;
                '''.format(pageid=int(db_page['pageid']))
            elif  db_page.get('source','') == 'photos':
                sql = '''SELECT photos.*
                FROM photos   WHERE photos.pages LIKE "%{uri}%"'''
                
                if db_page.get('order','')=='dates':
                    sql += 'ORDER BY photos.datetime'
                elif db_page.get('order','')=='uri':
                    sql += 'ORDER BY photos.hotlink'
                           
                sql = sql.format(uri=db_page['uri'])
            elif  db_page.get('source','') == 'tags':
                sql = '''SELECT photos.*
                FROM photos   WHERE photos.tags LIKE "%{uri}%"'''
                
                if db_page.get('order','')=='dates':
                    sql += 'ORDER BY photos.datetime'
                elif db_page.get('order','')=='uri':
                    sql += 'ORDER BY photos.hotlink'
                           
                sql = sql.format(uri=db_page['uri'])
                
                
            for row2 in cur_photos.execute(sql):
                db_photo = dict(row2)


                image={   "caption": db_photo['caption'],
                "url_hotlink": db_photo['hotlink']
                }
                city = db_photo.get('city')
                if city != '':
                    if city in locations:
                        city = locations[city]                
                    image['city']=city
                    
                sublocation = db_photo.get('sublocation')
                if sublocation != '':
                    if sublocation in locations:
                        sublocation = locations[sublocation]                
                    image['sublocation']=sublocation
                
                if db_photo.get('date_append') is not None:
                    image['date_append'] = db_photo.get('date_append')
                    
                if db_photo.get('wkt_geometry') is not None:
                    image['wkt_geometry'] = db_photo.get('wkt_geometry')
               
                images.append(image)
            json_content['images']=images

            with open(json_path, "wb") as outfile:
                json_str = json.dumps(json_content, ensure_ascii=False,indent = 1).encode('utf8')
                outfile.write(json_str)
                
            pbar.update(1)
        pbar.close()






if __name__ == "__main__":
    model = Model()
    model.db2gallery_jsons()
