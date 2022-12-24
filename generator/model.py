#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import os, subprocess
import sqlite3

from shapely import wkt
from shapely.geometry import Point

from iptcinfo3 import IPTCInfo
from exif import Image
from datetime import datetime
from dateutil import parser
from tqdm import tqdm
import copy
import shutil
import pprint



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
        
        self.exiftool_path = '/opt/exiftool/exiftool'

    def dms_to_dd(self,d, m, s):
        dd = d + float(m)/60 + float(s)/3600
        return dd


    def image2datetime(self,path):
        with open(path, 'rb') as image_file:
            try:
                image_exif = Image(image_file)
            
                dt_str = image_exif.get('datetime_original',None)
                dt_obj = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            except:
                dt_obj = None
                cmd = [self.exiftool_path,path,'-datetimeoriginal','-csv']
                exiftool_text_result =  subprocess.check_output(cmd)
                tmp = exiftool_text_result.splitlines()[1].split(b',')
                if len(tmp)>1:
                    dt_str = tmp[1]
                    dt_obj = datetime.strptime(dt_str.decode('UTF-8'), '%Y:%m:%d %H:%M:%S')
                
            

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
        
                direction = None
                if 'gps_img_direction' in image_exif.list_all():
                    try:
                        direction=round(float(image_exif.gps_img_direction))
                    except:
                        direction = None

                return  round(float(lat), 5), round(float(lon), 5), direction

        except:

            photo_coord='0,0'
            lat='0'
            lon='0'
            return None, None, None
  
    def locations2dict(self):
        cur = self.con.cursor()

        sql = "SELECT name_ru, name_int FROM locations  ;"
        names = dict()
        for row in cur.execute(sql):
            names[row['name_int']]=row['name_ru']
        
        return names
    
    def dir2db(self,path,base_url=''):
        #read directory with images. Generate SQL file for manual check and append to database.

        #compress images begin
        today = datetime.today()
        cmd = ['python3', 'generator/thumbnails-parallel.py','--path',path.replace('/storage/','/images_origins/')]
        subprocess.run(cmd)

        assert os.path.isdir(path)

        for (root,dirs,files) in os.walk(path):
            images = list()
            for filename in files:
                if not filename.lower().endswith('.jpg'): continue
                if filename.lower().endswith('.t.jpg'): continue
                if 'ar169' in filename: continue
                if 'arvert' in filename: continue
                filepath = os.path.join(root,filename)
                
                self.logger.debug(filepath)
                temp_path = os.path.normpath(path)
                path_as_list = temp_path.split(os.sep)

                url = base_url + '/' + os.path.join(path_as_list[-2],path_as_list[-1]) + '/' + filename

                info = IPTCInfo(os.path.join(root,filename), force=True)
                city = None
                sublocation = None
                objectname = None

                if info['city'] is not None:
                    city = info['city'].decode('UTF-8')
                if info['sub-location'] is not None:
                    sublocation = info['sub-location'].decode('UTF-8')
                if info['object name'] is not None:
                    try:
                        objectname = info['object name'].decode('UTF-8')
                    except:
                        objectname = info['object name'].decode('CP1251')
                caption = info['caption/abstract']
                if caption is not None:
                    try:
                        caption = caption.decode('UTF-8')
                    except:
                        caption = caption.decode('CP1251')
                else:
                    caption = ''
                image = {'caption':caption,'url_hotlink':url}
                if city is not None: image['city']=city
                if sublocation is not None: image['sublocation']=sublocation

                lat,lon,direction=self.image2latlon(os.path.join(root,filename))
                photo_datetime = self.image2datetime(os.path.join(root,filename))
                

                image['wkt_geometry']=wkt.dumps(Point(lon or 0,lat or 0),rounding_precision=5)
                image['direction'] = direction or 'Null'
                image['datetime']=photo_datetime
                if objectname is not None:  image['objectname']=objectname
                
                if os.path.exists(filepath.replace('.jpg','_ar169.webp')):
                    image['has_ar169']=1
                else:
                    image['has_ar169']=0
                if os.path.exists(filepath.replace('.jpg','_arvert.webp')):
                    image['has_arvert']=1
                else:
                    image['has_arvert']=0               


                images.append(image)

        #end compress images
        
        #for append photos in gallery: filter images already exists in database
        new_images = list()
        some_images_exists = False
        for image in images:
            sql = "SELECT Count() FROM photos WHERE hotlink = '{hotlink}' ".format(hotlink=image['url_hotlink'])
            cur_photos = self.con.cursor()
            cur_photos.execute(sql)
            count = cur_photos.fetchone()[0]
            print(count)
            if count == 0:
                new_images.append(image)
            else:
                some_images_exists = True
        images = new_images
        
        
        #begin make sql code
        #sql="BEGIN TRANSACTION; \n"
        sql = ""
        sql_custom = ""
        values = list()
        page_url = os.path.basename(root)

        for image in images:
            values.append([image['url_hotlink'],image.get('caption',''),image.get('city','')])
            
            tmpstr = '''INSERT INTO photos (hotlink,caption,city,sublocation, objectname, inserting_id, wkt_geometry, direction, datetime, date_append, pages, has_ar169, has_arvert)
            VALUES ( "{hotlink}" , "{caption}", "{city}", "{sublocation}", "{objectname}", "{inserting_id}", "{wkt_geometry}",  {direction},"{datetime}", "{date_append}", "{pages}", {has_ar169} , {has_arvert} );\n  '''
            tmpstr = tmpstr.format(hotlink=image['url_hotlink'],
                inserting_id = today.strftime('%Y-%m-%d-%H%M%S'),
                date_append = today.strftime('%Y-%m-%d'),
                caption = image['caption'].replace('"','""'),
                datetime = image['datetime'].isoformat() if image['datetime'] is not None else '',
                wkt_geometry = image['wkt_geometry'],
                pages = page_url,
                city = image.get('city',''),
                sublocation = image.get('sublocation',''),
                has_ar169 = image.get('has_ar169'),
                has_arvert = image.get('has_arvert'),
                direction = image.get('direction'),
                objectname = image.get('objectname','').replace('"','""')
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

        
        if not(some_images_exists):
            sql+='''INSERT INTO pages(uri, title, ha, date_mod, inserting_id,  "source", "order"  ) VALUES ("{page_url}", "{page_url}", "{page_url}", "{date}", '{inserting_id}', 'photos','dates' );\n '''.format(
            page_url=page_url,
            inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),
            date=today.strftime('%Y-%m-%d'))
        #sql += '''/* INSERT INTO photos_pages (photoid, pageuri, pageid, inserting_id) SELECT photoid, "{page_url}",0, "{inserting_id}"
        #FROM photos
        #WHERE photos.inserting_id='{inserting_id}'
        #ORDER BY photos.hotlink;\n */ '''.format(inserting_id=today.strftime('%Y-%m-%d-%H%M%S'),page_url=page_url,)
        #sql += '''-- UPDATE photos_pages SET pageid = (SELECT pageid FROM pages WHERE uri='{page_url}') WHERE pageuri='{page_url}';\n   '''.format(page_url=page_url)
        #sql += '''-- UPDATE photos_pages SET pageuri = '';\n   '''

        #sql+="COMMIT;"

        sql_file = "tmp_add_page.sql"
        with open(sql_file, "w") as caption_file:
            caption_file.write(sql)
        self.logger.info('sql saved to '+sql_file)
        
        #sql_file = "tmp_custom.sql"
        #with open(sql_file, "w") as caption_file:
        #    caption_file.write(sql_custom)
        #self.logger.info('sql saved to '+sql_file)

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
    
    def id2uri(self,inp):
        return 'I'+str(int(inp)).zfill(5)
        
    def pages_index_jsons(self,path=os.path.join(os.path.dirname(os.path.realpath(__file__ )),'content')):
        cur_pages = self.con.cursor()
        cur_groups = self.con.cursor()
        
        pages_data = dict()
        pages_data['groups']=list()
        
        sql = '''
        SELECT 
        pages_groups.id,
        pages_groups.name,
        pages_groups.name_en
        FROM
        pages_groups
        ORDER BY "order";
        
        '''
        for row in cur_groups.execute(sql):
            group_data = dict()
            group_data['name'] = row['name']
            group_data['name_en'] = row['name_en']
            group_data['pages']=list()
            sql = '''
            SELECT
            pages.pageid,
            pages.uri,
            pages.title,
            pages.text_en AS title_en
            FROM pages
            WHERE hidden=0 AND
            page_group = {page_group}
            ORDER BY date_sort;
            '''.format(page_group=row['id'])
            for page in cur_pages.execute(sql):
                page_data = dict()
                page_data['uri'] = page['uri']
                page_data['title'] = page['title']
                page_data['title_en'] = page['title_en']
                group_data['pages'].append(page_data)
            pages_data['groups'].append(group_data)
        
        json_path = os.path.join(path,'_pages_index')+'.json'
        with open(json_path, "wb") as outfile:
            json_str = json.dumps(pages_data, ensure_ascii=False,indent = 1).encode('utf8')
            outfile.write(json_str)
        
    def make_location_string(self,db_photo):
        
        if db_photo['city'] is None and db_photo['sublocation'] is None: return None
        if db_photo['sublocation'] is not None:
            out = db_photo['sublocation']
            
    def direction2text(self,direction,mode='reverse'):
        name=None
        direction = int(direction)
        if mode=='reverse':
            direction = direction-180
            if direction<0: direction=direction+360
        if direction > (45*1-(45/2)) and direction < (45*1+(45/2)): name = 'северо-восток'
        if direction > (45*2-(45/2)) and direction < (45*2+(45/2)): name = 'восток'
        if direction > (45*3-(45/2)) and direction < (45*3+(45/2)): name = 'юго-восток'
        if direction > (45*4-(45/2)) and direction < (45*4+(45/2)): name = 'юг'
        if direction > (45*5-(45/2)) and direction < (45*5+(45/2)): name = 'юго-запад'
        if direction > (45*6-(45/2)) and direction < (45*6+(45/2)): name = 'запад'
        if direction > (45*7-(45/2)) and direction < (45*7+(45/2)): name = 'северо-запад'
        if direction > (45*7+(45/2)) or direction < (45*1-(45/2)): name = 'север'
        
        if mode=='reverse':
            name = name+'а'
        
        return name
        
        
    def db2gallery_jsons(self,path=os.path.join(os.path.dirname(os.path.realpath(__file__ )),'content'), process_recently_updated = False, recently_days = 2):
        cur_pages = self.con.cursor()
        cur_photos = self.con.cursor()

        locations = self.locations2dict()
        
        if os.path.isdir(path): shutil.rmtree(path)
        os.makedirs(path)

        sql = '''
        -- clean zero geometry
UPDATE photos
SET wkt_geometry = NULL
WHERE wkt_geometry LIKE '%(0.0%';

DROP VIEW IF EXISTS view_canonical_urls;
CREATE VIEW view_canonical_urls AS  
SELECT DISTINCT photoid, uri|| '/' || 'I'|| printf('%05d',photoid) || '.htm' AS canonical_url, wkt_geometry, direction, datetime FROM(
SELECT photos.photoid,
pages.uri,
pages.page_group ,
photos.wkt_geometry,
photos.direction,
photos.datetime 
FROM photos JOIN pages ON photos.pages = pages.uri AND pages.source='photos' AND pages.hidden=0

UNION 
SELECT photos.photoid,
pages.uri,
pages.page_group ,
photos.wkt_geometry,
photos.direction,
photos.datetime 
FROM photos JOIN pages ON photos.tags = pages.uri AND pages.source='tags' AND pages.hidden=0

UNION 
SELECT photos.photoid,
pages.uri,
pages.page_group ,
photos.wkt_geometry,
photos.direction,
photos.datetime 
FROM photos JOIN pages JOIN photos_pages
WHERE photos.photoid = photos_pages.photoid AND photos_pages.pageid = pages.pageid  AND pages.source='photos_pages' AND pages.hidden=0
ORDER BY photoid, page_group ASC
)
GROUP BY photoid;

DROP VIEW IF EXISTS view_photos_geodata;
CREATE VIEW view_photos_geodata AS  
SELECT photoid, 'https://trolleway.com/reports/' || replace(replace(replace(canonical_url,
    " ", "%20"),
    "(", "%28"),
    ")", "%29")  AS canonical_url, wkt_geometry, direction, datetime FROM view_canonical_urls
WHERE wkt_geometry IS NOT NULL;


        DROP VIEW  IF EXISTS view_photos;
        CREATE VIEW view_photos AS SELECT 
photos.photoid ,
photos.hotlink ,
NULLIF(photos.caption,'') AS caption ,
NULLIF(photos.objectname,'') AS objectname ,
COALESCE(locations_city.name_ru, photos.city) AS city ,
COALESCE(locations_sublocation.name_ru, photos.sublocation) AS sublocation ,
photos.city AS city_int,
photos.sublocation AS sublocation_int,
photos.inserting_id ,
photos.wkt_geometry ,
NULLIF(photos.direction,'') AS direction,
NULLIF(photos.direction_inout,0) AS direction_inout,
NULLIF(photos.print_direction,0) AS print_direction,
photos.datetime ,
case when COALESCE(substr(photos.update_timestamp,0,11),substr(photos.date_append,0,11),NULL) > '2022-11-10' THEN COALESCE(substr(photos.update_timestamp,0,11),substr(photos.date_append,0,11),NULL) ELSE NULL END AS sitemap_lastmod,
NULLIF(photos.tags,'') AS tags ,
NULLIF(photos.pages,'') AS pages ,
photos.date_append,
photos.caption_en,
photos.has_ar169,
photos.has_arvert,
photos.fit_contain,
photos.lens,
photos.medium,
photos.film,
licenses.code AS license_code,
view_canonical_urls.canonical_url AS canonical_url
FROM photos 
LEFT OUTER JOIN locations locations_city ON locations_city.name_int = photos.city 
LEFT OUTER JOIN locations locations_sublocation ON locations_sublocation.name_int = photos.sublocation
LEFT JOIN licenses ON licenses.id = photos.license
LEFT OUTER JOIN view_canonical_urls ON photos.photoid = view_canonical_urls.photoid ;
        '''
        cur_photos.executescript(sql)
        
        cmd = '''
        ogr2ogr \
  -f "GPKG" -overwrite -progress html/temp_photos.gpkg \
  generator/web.sqlite \
  -sql \
  "SELECT
     *,
     ST_GeomFromText(wkt_geometry, 4326) AS geometry
   FROM
     view_photos_geodata" \
  -nln "photos" -s_srs EPSG:4326 -t_srs EPSG:4326
        '''
        os.system(cmd)
        
        

        select_only_recently_updated = '''
        
        SELECT DISTINCT pages.* FROM photos JOIN pages ON photos.pages = pages.uri AND pages.source='photos' AND pages.hidden=0 WHERE (date(photos.date_append) > date('now','-{recently_days} day') or date(photos.update_timestamp) > date('now','-{recently_days} day') or date(pages.date_mod) > date('now','-{recently_days} day'))
        UNION
        SELECT DISTINCT pages.* FROM photos JOIN pages ON photos.tags = pages.uri AND pages.source='tags' AND pages.hidden=0 WHERE (date(photos.date_append) > date('now','-{recently_days} day') or date(photos.update_timestamp) > date('now','-{recently_days} day') or date(pages.date_mod) > date('now','-{recently_days} day'))
        UNION
        SELECT DISTINCT pages.* FROM photos JOIN pages JOIN photos_pages  WHERE photos.photoid = photos_pages.photoid AND photos_pages.pageid = pages.pageid  AND pages.source='photos_pages' AND pages.hidden=0 AND (date(photos.date_append) > date('now','-{recently_days} day') or date(photos.update_timestamp) > date('now','-{recently_days} day') or date(pages.date_mod) > date('now','-{recently_days} day'))
        
        '''
        select_only_recently_updated = select_only_recently_updated.format(recently_days=recently_days)


        sql_all_pages = 'SELECT * FROM pages WHERE hidden=0 ;'
        if process_recently_updated:
            sql = select_only_recently_updated
        else:
            sql = sql_all_pages
        
        cur_pages.execute(sql)
        pages = cur_pages.fetchall()
       
        count = len(pages)
        
        pbar = tqdm(total=count)
        

        for row in pages:
            
            
            db_page = dict(row)
            json_path = os.path.join(path,db_page['uri'])+'.json'

            json_content={
            "title": db_page['title'],
 "h1": db_page['ha'] or '',
 "text": db_page['text'] or '',
 "text_en": db_page['text_en'] or '',
 "map_center": db_page['map_center_str'] or '',
 "map_zoom": "12",
 "date_mod": db_page['date_mod'] or ''}
            images = list()

            if db_page.get('source','') in ('','photos_pages'):
                sql = '''SELECT photos.*
                FROM view_photos photos
                JOIN photos_pages ON photos.photoid=photos_pages.photoid
                JOIN pages ON pages.pageid=photos_pages.pageid
                WHERE photos_pages.pageid={pageid}
                ORDER BY photos_pages.'order' ;
                '''.format(pageid=int(db_page['pageid']))
            elif  db_page.get('source','') == 'photos':
                sql = '''SELECT photos.*
                FROM view_photos photos   WHERE photos.pages LIKE "%{uri}%"'''
                
                if db_page.get('order','')=='dates':
                    sql += 'ORDER BY photos.datetime'
                elif db_page.get('order','')=='uri':
                    sql += 'ORDER BY photos.hotlink'
                           
                sql = sql.format(uri=db_page['uri'])
            elif  db_page.get('source','') == 'tags':
                sql = '''SELECT photos.*
                FROM view_photos photos   WHERE photos.tags LIKE "%{uri}%"'''
                
                if db_page.get('order','')=='dates':
                    sql += 'ORDER BY photos.datetime'
                elif db_page.get('order','')=='uri':
                    sql += 'ORDER BY photos.hotlink'
                           
                sql = sql.format(uri=db_page['uri'])
                
            #list of urls for prev/next links    
            uris = list()
            for row2 in cur_photos.execute(sql):
                db_photo = dict(row2)
                uris.append(self.id2uri(db_photo['photoid']))
                
            #make unique html title in python
            title_calc_list = list()
            new_titles_dict = dict()
            for row2 in cur_photos.execute(sql):
                db_photo = dict(row2)
                
                title = db_photo['objectname'] or db_photo['caption'] or ''
                if '.' in title:
                    title = title.split('.')[0]
                
                if db_photo['sublocation'] is not None:
                    if db_photo['sublocation'] not in title:
                        if title != '':
                            title += ', '+db_photo['sublocation']
                        else:
                            title = db_photo['sublocation']  
                            
                if db_photo['city'] is not None:
                    if db_photo['city'] not in title:
                        if title != '':
                            title += ', '+db_photo['city']
                        else:
                            title = db_photo['city']   
                title += ', фото '+db_photo['datetime'][0:4]+' года'

                title = title.replace('.,','.')
                title_calc_dict =  copy.deepcopy(db_photo)
                title_calc_dict['title']=title
                title_calc_list.append(title_calc_dict)
                new_titles_dict[db_photo['photoid']]=title
            #detect same titles and upgrade it to unique for SEO experiment
            photos = list()
            for row2 in cur_photos.execute(sql):
                photos.append(dict(row2))
                
            
            dublicated_titles_clusters = dict()
            for photoid in new_titles_dict:
                if new_titles_dict[photoid] not in dublicated_titles_clusters:
                    dublicated_titles_clusters[new_titles_dict[photoid]]=[photoid]
                else:
                    dublicated_titles_clusters[new_titles_dict[photoid]].append(photoid)


            for key in dublicated_titles_clusters:
                if len(dublicated_titles_clusters[key]) == 1:
                    continue
                
                #add direction text if exist
                for photoid in dublicated_titles_clusters[key]:
                    for db_photo in photos:
                        if db_photo['photoid']==photoid:
                            if db_photo['direction'] is not None:
                                if db_photo['direction_inout'] == 1:
                                    new_title = key + ', вид на '+self.direction2text(int(db_photo['direction']),mode='to')
                                else:
                                    new_title = key + ', вид c '+self.direction2text(int(db_photo['direction']),mode='reverse')
                                new_titles_dict[photoid]=new_title

              

            #add <s>frist</s> <s>last</s> frist diffirencing part of filename
            dublicated_titles_clusters = dict()
            for photoid in new_titles_dict:
                if new_titles_dict[photoid] not in dublicated_titles_clusters:
                    dublicated_titles_clusters[new_titles_dict[photoid]]=[photoid]
                else:
                    dublicated_titles_clusters[new_titles_dict[photoid]].append(photoid)
            
            new_suffixes=dict()
            for key in dublicated_titles_clusters:
                if len(dublicated_titles_clusters[key]) == 1:
                    continue

                cleaned_filenames = list()
                for photoid in dublicated_titles_clusters[key]:
                    for db_photo in photos:
                        if db_photo['photoid']==photoid:
                            uri=db_photo['hotlink']
                            filename=uri.replace('_','-').replace('-ORIGINALFILE','').replace('-ar169','').replace('-arvert','').split('/')[-1].split('.')[0]
                            filename=filename.strip('-')

                            cleaned_filenames.append(filename)
                counter = 0
                for photoid in dublicated_titles_clusters[key]:
                    filename_current = cleaned_filenames[counter]
                    if counter<len(cleaned_filenames)-1:
                        filename_other = cleaned_filenames[counter+1]
                    else:
                        filename_other = cleaned_filenames[counter-1]
                    fla=filename_current.split('-')
                    flb=filename_other.split('-')

                    for partnum in range(len(fla)):
                        if (partnum <  len(flb)-1) and (fla[partnum]==flb[partnum]):
                            continue
                        else:
                            unique_filename_part = fla[partnum]
                    new_suffixes[photoid]=unique_filename_part
                        
                    
                    counter=counter+1
                    new_titles_dict[photoid]+=' '+unique_filename_part
 


            
            counter = 0
            for row2 in cur_photos.execute(sql):
                db_photo = dict(row2)
                assert 'city_int' in db_photo
                
                image={  "url_hotlink": db_photo['hotlink']
                }
                image['uri']=uris[counter]
                image['title']=new_titles_dict[db_photo['photoid']]
                if db_photo['tags'] is not None:
                    image['title'] += ': '+db_page['title']
                if counter > 0:
                    image['uri_prev']=uris[counter-1]
                if counter < len(uris)-1:
                    image['uri_next']=uris[counter+1]
                
                if db_photo.get('caption'): image['caption'] = db_photo.get('caption')
                if db_photo.get('canonical_url') is not None  and db_page['uri'] not in db_photo.get('canonical_url',''):
                    image['canonical_url'] = 'https://trolleway.com/reports/'+db_photo.get('canonical_url')
                
                    
                city = db_photo.get('city','')
                if city != '' and city is not None:
                    if city in locations:
                        city = locations[city]                
                    image['city']=city
                    
                sublocation = db_photo.get('sublocation','')
                if sublocation != '' and sublocation is not None:
                    if sublocation in locations:
                        sublocation = locations[sublocation]                
                    image['sublocation']=sublocation
                    
                objectname = db_photo.get('objectname')
                if objectname != '' and objectname is not None:
                    if objectname in locations:
                        objectname = locations[objectname]                
                    image['objectname']=objectname
                
                if db_photo.get('print_direction')==1:
                    if db_photo['direction'] is not None:
                        if db_photo['direction_inout'] == 1:
                            append =  ', вид на '+self.direction2text(int(db_photo['direction']),mode='to')
                        else:
                            append =  ', вид c '+self.direction2text(int(db_photo['direction']),mode='reverse')
                        if db_photo.get('caption'): 
                            image['caption'] += append
                        elif 'objectname' in image and image['objectname'] is not None:
                            image['objectname'] += append
                if db_photo.get('date_append') is not None:
                    image['date_append'] = db_photo.get('date_append')
                    
                if db_photo.get('wkt_geometry') is not None:
                    image['wkt_geometry'] = db_photo.get('wkt_geometry')
                    
                if db_photo.get('license_code') != 'cc-by':
                    image['license'] = db_photo.get('license_code')  
                    
                if db_photo.get('caption_en') is not None:
                    image['caption_en'] = (db_photo.get('caption_en') or '') + ' '+(db_photo.get('city_int') or '') + ' '+(db_photo.get('sublocation_int') or '')

                    

                if db_photo.get('lens') is not None:
                    image['lens'] = db_photo.get('lens')
                if db_photo.get('film') is not None:
                    image['film'] = db_photo.get('film')
                if db_photo.get('camera') is not None:
                    image['camera'] = db_photo.get('camera')
                if db_photo.get('datetime') is not None:
                    image['datetime'] = db_photo.get('datetime')
                if db_photo.get('has_ar169',0) is not None and db_photo.get('has_ar169',0)>0 :
                    image['ar169'] = True
                if db_photo.get('has_arvert',0)  is not None and db_photo.get('has_arvert',0)>0 :
                    image['arvert'] = True
                if db_photo.get('fit_contain',0)  is not None and db_photo.get('fit_contain',0)>0 :
                    image['fit_contain'] = True
                if db_photo.get('sitemap_lastmod') is not None:
                    image['sitemap_lastmod'] = db_photo.get('sitemap_lastmod')                    
                    
               
                images.append(image)
                counter = counter + 1
            json_content['images']=images

            with open(json_path, "wb") as outfile:
                json_str = json.dumps(json_content, ensure_ascii=False,indent = 1).encode('utf8')
                outfile.write(json_str)
                
            pbar.update(1)
        pbar.close()


if __name__ == "__main__":
    '''
    model = Model()
    model.db2gallery_jsons()
    model.pages_index_jsons()
    '''
    print('call db2json.py instead')