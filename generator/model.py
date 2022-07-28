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
            dt=image_exif.get('datetime_original',None)
            if dt is None:
                return None
            return parser.parse(dt)

    
            
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
                        
                        
    def dir2db(self,path,base_url=''):
    
        today = datetime.today()
        assert os.path.isdir(path)
        
        for (root,dirs,files) in os.walk(path):
            images = list()
            for filename in files:
                if not filename.lower().endswith('.jpg'): continue
                temp_path = os.path.normpath(path)
                path_as_list = temp_path.split(os.sep)
                
                url = base_url + '/' + os.path.join(path_as_list[-2],path_as_list[-1]) + '/' + filename
                
                info = IPTCInfo(os.path.join(root,filename), force=True)
                city = None

                if info['city'] is not None:
                    city = info['city'].decode('UTF-8')
                caption = info['caption/abstract']
                if caption is not None:
                    caption = caption.decode('UTF-8')
                else:
                    caption = ''
                image = {'text':caption,'url_hotlink':url}
                if city is not None: image['city']=city
                
                lat,lon=self.image2latlon(os.path.join(root,filename))
                photo_datetime = self.image2datetime(os.path.join(root,filename))

                image['wkt_geometry']=wkt.dumps(Point(lat or 0,lon or 0))
                
                images.append(image)
                
        #sql="BEGIN TRANSACTION; \n"
        sql=""
        values = list()
        for image in images:
            values.append([image['url_hotlink'],image['text'],image['city']])
            
            tmpstr = '''INSERT INTO photos (hotlink,text,city,inserting_id, wkt_geometry, datetime) VALUES ( "{hotlink}" , "{text}", "{city}", "{inserting_id}", "{wkt_geometry}", "{datetime}" );\n  '''
            tmpstr = tmpstr.format(hotlink=image['url_hotlink'],
                inserting_id = today.strftime('%Y-%m-%d-%H%M%S'),
                text = image['text'],
                datetime = photo_datetime.isoformat(),
                wkt_geometry = image['wkt_geometry'],
                city = image['city'])
            sql += tmpstr
        
        page_url = os.path.basename(root)
        sql+='''INSERT INTO pages(uri,title, date_mod, inserting_id  ) VALUES ("{page_url}", "{date}", "{date}", '{inserting_id}' );\n '''.format(
        page_url=page_url,
        inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),
        date=today.strftime('%Y-%m-%d'))
        sql += ''' INSERT INTO photos_pages (photoid, pageuri, pageid, inserting_id) SELECT photoid, "{page_url}",0, "{inserting_id}"
        FROM photos 
        WHERE photos.inserting_id='{inserting_id}'
        ORDER BY photos.hotlink;\n  '''.format(inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),page_url=page_url,)
        sql += ''' UPDATE photos_pages SET pageid = (SELECT pageid FROM pages WHERE uri='{page_url}') WHERE pageuri='{page_url}';\n   '''.format(page_url=page_url)
        sql += ''' UPDATE photos_pages SET pageuri = '';\n   '''
    
        #sql+="COMMIT;"
        
        print(sql)
        sql_file = "tmp_add_page.sql"
        with open(sql_file, "w") as text_file:
            text_file.write(sql)
        self.logger.info('sql saved to '+sql_file)
        sql='''INSERT INTO photos (hotlink,text,city) VALUES ( "?" , "?", "?" );'''
        return
        
        sql='INSERT INTO photos (hotlink,text,city) VALUES ( ? , ?, ? );'
        cur = self.con.cursor()
        cur.executemany(sql,values)
        self.con.commit()

    '''
    CREATE VIEW photos_pages_view AS SELECT photos_pages."order", photos."text", pages.uri 
FROM photos_pages JOIN photos ON photos_pages.photoid=photos.photoid 
JOIN pages ON photos_pages.pageid = pages.pageid
ORDER BY pages.uri, photos_pages."order";
    '''
    
    def db2gallery_jsons(self,path=os.path.join(os.path.dirname(os.path.realpath(__file__ )),'content2')):
        sql = 'SELECT * FROM pages where hidden=0;'
        cur_pages = self.con.cursor()
        cur_photos = self.con.cursor()
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
            
            sql = '''SELECT photos.* 
            FROM photos 
            JOIN photos_pages ON photos.photoid=photos_pages.photoid
            JOIN pages ON pages.pageid=photos_pages.pageid
            WHERE photos_pages.pageid=?
            ORDER BY photos_pages.'order' ;
            '''
            for row2 in cur_photos.execute(sql,str(db_page['pageid'])):
                db_photo = dict(row2)
                
                images.append({   "text": db_photo['text'],
               "url_hotlink": db_photo['hotlink'],
               "city":  db_photo['city']})
            json_content['images']=images
            
            with open(json_path, "wb") as outfile:
                json_str = json.dumps(json_content, ensure_ascii=False,indent = 1).encode('utf8')
                outfile.write(json_str)






if __name__ == "__main__":
    model = Model()
    model.db2gallery_jsons()
