#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import requests

from exif import Image
import shutil,logging

import pathlib
from datetime import datetime
from iptcinfo3 import IPTCInfo

from shapely import wkt
from shapely.geometry import Point
from datetime import datetime
from tqdm import tqdm


class Website_generator():


    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    sitemap_base_url = ''
    
    
    def __init__(self, sitemap_base_url = 'https://trolleway.com/reports/'):
        self.sitemap_base_url = sitemap_base_url
        self.basedir = (os.path.dirname(os.path.realpath(__file__)))
        self.json_dir = os.path.join(self.basedir,'content')
        self.texts_dir = os.path.join(self.basedir,'texts')

    def numfill(self,value):
        return str(value).zfill(2)

    def dms_to_dd(self,d, m, s):
        dd = d + float(m)/60 + float(s)/3600
        return dd

    def  template_remove_map(self,template):
        txt = '''<!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- mapnik -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js" integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==" crossorigin=""></script>
    <!-- fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Prosto+One&display=swap" rel="stylesheet">
    <link href="../newsincerity.css" rel="stylesheet">
    <style>
    .bgimg-1 {bgimg}
    </style>
    </head>
    <body>
    <div class="bgimg-1">
    <div id="backwardlink"><a href="{url_left}" rel="{rel_left}" ><img src="../transparent.gif"></a></div>
    <div id="forwardlink"><a href="{url_right}" rel="{rel_right}" ><img src="../transparent.gif">{right_frist_image}</a></div>
      <div class="caption">
        <span class="border">
        {caption}
        </span><br>
      </div>
    </div>
    <footer>
    <div id="map" style="width: 100%; height: 400px;"></div>
    <div id="copyright">
           <a rel="cc:attributionURL" property="dc:title">Photo</a> by
           <a rel="dc:creator" href=""
           property="cc:attributionName">Artem Svetlov</a> is licensed to the public under
           the <a rel="license"
           href="https://creativecommons.org/licenses/by/4.0/">Creative
           Commons Attribution 4.0 License</a>.
    </div>
    <script>
    {map_js}
    </script>
    {google_counter}
    {yandex_counter}
    </footer>
    </body>
    </html>
        '''
        return txt

    def get_body_from_html(self,html_text_filename):
        assert os.path.exists(html_text_filename) , 'not found '+html_text_filename
        with open(html_text_filename, encoding='utf-8') as text_file:
            text = text_file.read()

        text = text[text.find('<body>')+6:text.find('</body>')].strip()
        return text


    def coords_list_average(self,coords):
        return None



    def generate_pages_list_content(self):

        json_filename = os.path.join(self.json_dir,'_pages_index.json')
        assert os.path.isfile(json_filename),'must exists file "'+json_filename+'"'
        try:
            with open(json_filename, encoding='utf-8') as json_file:
                data = json.load(json_file)

        except Exception as e:

            print('error open json '+os.path.join(self.json_dir,json_filename))
            print(e)

        assert data is not None
        
        table = '<table id="pages">'
        for group in data['groups']:
            table += '<tr><td colspan="2">'+"\n"
            table += '<p lang="ru">'+group['name']+'</p>'
            table += '<p lang="en">'+group['name_en']+'</p>'
            table += '</td></tr>'+"\n"
            for page in group['pages']:
                table += '<tr>'+"\n"
                table += '<td><a lang="ru" href="{uri}/index.htm">{text_ru}</a></td>'.format(uri=page['uri'],text_ru=page['title'])+"\n"
                table += '<td><span lang="en">{text_en}</a></td>'.format(uri=page['uri'],text_en=page['title_en'])+"\n"
                table += '</tr>'+"\n"
        
        table += '</table>'
        
        return table

    def generate_pages_list(self):
        content = self.generate_pages_list_content()
        
        template_filepath = os.path.join(self.basedir, 'gallery.list.template.htm')
        assert os.path.exists(template_filepath), 'must exist file '+template_filepath
        with open(template_filepath, encoding='utf-8') as template_file:
            template = template_file.read()
            
        html = template.replace('{content}', content)
        
        output_directory = os.path.join(self.basedir,'..','html','reports')
        filename = os.path.join(output_directory,'index.htm')
        with open(filename, "w", encoding='utf-8') as text_file:
            text_file.write(html)
            
        
    def drop_html_tags(self,raw_html):
        import re
        # as per recommendation from @freylis, compile once only
        CLEANR = re.compile('<.*?>') 

        cleantext = re.sub(CLEANR, '', raw_html)
        return cleantext
    def process_datetime_trolleway(self,textdate):
        if textdate == '': return ''
        textdate = textdate[0:10]
        photodateobj = datetime.strptime(textdate, '%Y-%m-%d')
        today = datetime.today()
        delta  = today-photodateobj
        if delta.days > (365*9):
            return textdate
        else:
            return ''

    def generate(self):




        #---- set output directory for files
        output_directory = os.path.join(self.basedir,'..','html','reports')
        if not os.path.isdir(output_directory): os.makedirs(output_directory)

        sitemap_path_manual = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sitemap_manual.xml') #, ".."+os.sep
        sitemap_path = os.path.join(self.basedir,'..','html','sitemap.xml')
        assert os.path.isfile(sitemap_path_manual),'not found file '+sitemap_path_manual
        pages2sitemap=[]

        #---- copy static files
        src = os.path.join(self.basedir,'static')
        src_files = os.listdir(src)
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, output_directory)


        assert os.path.isdir(self.json_dir),'must exists directory "'+self.json_dir+'"'

        json_files = [f for f in os.listdir(self.json_dir) if os.path.isfile(os.path.join(self.json_dir, f)) and f.lower().endswith('.json') and not f.startswith('_')]
        assert len(json_files)>0,'must be find some .json files in '+self.json_dir

        #generate article for each json
        for json_filename in json_files:
            with open(os.path.join(self.json_dir,json_filename), encoding='utf-8') as json_file:
                self.logger.debug(json_filename)
                try:
                    data = json.load(json_file)
                except Exception as e:

                    print('error open json '+os.path.join(self.json_dir,json_filename))
                    print(e)
                    print()
                    continue
            assert data is not None
            if 'date_mod' in data:
                GALLERY_DATE_MOD = data['date_mod']
            else:
                GALLERY_DATE_MOD = datetime.today().strftime('%Y-%m-%d')

            # target directory calc
            if 'uri' in data:
                output_directory_name = data['uri']
                directory_level=data['uri'].count('/')
                html_basedir='../'
                for i in range(0,directory_level):
                    html_basedir+='../'
                self.logger.debug(html_basedir)
                
            else:
                output_directory_name = os.path.splitext(json_filename)[0]
                directory_level = 0
                html_basedir='../'

            output_directory_path = os.path.join(output_directory,output_directory_name)

            if not os.path.isdir(output_directory_path):
                self.logger.debug('create '+output_directory_path)
                os.makedirs(output_directory_path)

            assert os.path.isdir(output_directory_path), 'must exist directory '+output_directory_path

            template_filepath = os.path.join(self.basedir, 'gallery.template.htm')
            assert os.path.exists(template_filepath), 'must exist file '+template_filepath
            with open(template_filepath, encoding='utf-8') as template_file:
                template = template_file.read()
            assert '{image_url}' in template

            template_index_filepath = os.path.join(self.basedir, 'gallery.index.template.htm')
            assert os.path.exists(template_index_filepath), 'must exist file '+template_index_filepath

            count_images = len(data['images'])
            current_image = 0

            #calculate filenames for prev/next link

            coords_list = list()
            photos4template = list()
            leaflet_geojson_features = list()
            for image in tqdm(data['images']):
                schema_org_sameas=list()
                current_image += 1

                if current_image < count_images:
                    url_right = image.get('uri_next')+'.htm'
                    rel_right = 'next'
                else:
                    url_right = 'index.htm'
                    rel_right = 'up'
                if current_image > 1:
                    url_left = image.get('uri_prev')+'.htm'
                    rel_left = 'prev'
                else:
                    url_left = 'index.htm'
                    rel_left = 'up'

                if current_image == 1:
                    right_link_image = '''<img class="left_arrow"   alt="Go to next page" src="{html_basedir}Controls_chapter_next.svg">'''.format(html_basedir=html_basedir)
                elif current_image == len(data['images']):
                    right_link_image = '''<img class="right_arrow"   alt="Go to index page" src="{html_basedir}Controls_eject.svg">'''.format(html_basedir=html_basedir)
                else:
                    right_link_image = '''<img class="right_arrow"   alt="Go to next page" src="{html_basedir}Controls_chapter_next.svg">'''.format(html_basedir=html_basedir)

                if current_image == 1:
                    left_link_image = '''<img class="left_arrow"  alt="Go to index page" src="{html_basedir}Controls_eject.svg">'''.format(html_basedir=html_basedir)
                else:
                    left_link_image = '''<img class="right_arrow"   alt="Go to previous page" src="{html_basedir}Controls_chapter_previous.svg">'''.format(html_basedir=html_basedir)



                # get photo coordinates from json if exists

                photo_coord = None
                wkt_geometry = image.get('wkt_geometry') or None
                lat = None
                lon = None

                if wkt_geometry is not None:
                    shapely_point = wkt.loads(wkt_geometry)
                    lat = shapely_point.y
                    lon = shapely_point.x
                    photo_coord = str(lat)+','+str(lon)

                # get coordinates from exif



                # print map


                map_center = image.get('center_map',photo_coord)
                if str(image.get('center_map'))=='1':
                    map_center = photo_coord
                if wkt_geometry is  None:
                    map_js = ''
                else:
                    map_js = '''
                var photo_coord = ['''+photo_coord+''']
                var map = L.map('map').setView(['''+map_center+'''], '''+data['map_zoom']+''');
                var OpenStreetMap_DE = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
                    maxZoom: 18,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                });
                var tiles = OpenStreetMap_DE.addTo(map);
                var circle = L.circle(photo_coord, {
                    color: 'red',
                    fillColor: '#f03',
                    fillOpacity: 0.5,
                    radius: 200
                }).addTo(map).bindPopup('Гиперссылка на картографический сервис');
                    '''
                google_counter_trolleway_github = """<!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-119801939-1"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'UA-119801939-1');
        </script>"""
                google_counter = '''<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3J5MD6L525"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-3J5MD6L525');
</script>'''
                yandex_counter_trolleway_github_io = '''<!-- Yandex.Metrika counter -->
        <script type="text/javascript" >
           (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
           m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
           (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
           ym(87742115, "init", {
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true
           });
        </script>
        <noscript><div><img src="https://mc.yandex.ru/watch/87742115" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
        <!-- /Yandex.Metrika counter -->'''

                yandex_counter = '''
                <!-- Yandex.Metrika counter -->
<script type="text/javascript" >
   (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
   m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
   ym(55429573, "init", {
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true
   });
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/55429573" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
                '''
                


                image['url'] = image['url_hotlink']

                caption = image.get('caption','')
                caption = caption or ''
                caption = caption.strip()
                if caption.endswith('.'): caption=caption[0:-1]

                caption_location = caption
                
                if 'objectname' in image:
                    if image['objectname'] is not None and image['objectname'] not in caption_location:
                        if caption_location != '':
                            caption_location = caption_location + ', ' + image['objectname']
                        else:
                            caption_location = image['objectname']

                    
                if 'sublocation' in image and image['sublocation'] is not None:
                    if image['sublocation'].upper() not in caption_location.upper():
                        if caption_location != '':
                            caption_location = caption_location + ', ' + image['sublocation']
                        else:
                            caption_location = image['sublocation']
                            
                if 'city' in image:
                    if image['city'].upper() not in caption_location.upper():
                        if caption_location != '':
                            caption_location = caption_location + ', ' + image['city']
                        else:
                            caption_location = image['city']
                            
                caption_location = caption_location.replace('.,','.')
                
                if 'film' in image:
                    film = '<span>Taken on film '+image.get('film')+'</span> '
                else:
                    film = ''                
                if 'lens' in image:
                    lens = '<span>Lens '+image.get('lens')+'</span> '
                else:
                    lens = ''
                if 'camera' in image:
                    camera = image.get('camera')
                else:
                    camera = ''
                if 'ORIGINALFILE' in image['url']:
                    film += '<span>Original file from digital camera</span> '
                    
                #dirty generation of caption, but quick to implement
                tech_info = ''
                tech_info = ' '.join([film, camera, lens])
                tech_info = tech_info.replace(' ,',',')
                tech_info = tech_info.strip()
                if tech_info.endswith(','): tech_info = tech_info[0:-1]
                if tech_info == ', ': tech_info = ''
                
                commons_link = image.get('hotlink_commons','')
                if commons_link != '': commons_link = '<div lang="en"><a href="{url}" rel="external">Uncompressed source image page on Wikimedia Commons</a></div>'.format(url=image.get('hotlink_commons',''))
                if commons_link != '': schema_org_sameas.append(image.get('hotlink_commons',''))
                                
                flickr_link = image.get('url_flickr','')
                if flickr_link != '': flickr_link = '<div lang="en"><a href="{url}" rel="external">Uncompressed source image page on flickr</a></div>'.format(url=image.get('url_flickr',''))
                if flickr_link != '': schema_org_sameas.append(image.get('url_flickr',''))
                                                
                shutterstock_link = image.get('url_shutterstock','')
                if shutterstock_link != '': shutterstock_link = '<div lang="en"><a href="{url}" rel="external">Royalty free license this image for use in media</a></div>'.format(url=image.get('url_shutterstock',''))
                if shutterstock_link != '': schema_org_sameas.append(image.get('url_shutterstock',''))
                
                licenses_footer = dict()
                licenses_footer['cc-by']='''       <a rel="cc:attributionURL" property="dc:title">Photo</a> by
       <a rel="dc:creator" href=""
       property="cc:attributionName">Artem Svetlov</a> is licensed to the public under 
       the <a rel="license"
       href="https://creativecommons.org/licenses/by/4.0/">Creative
       Commons Attribution 4.0 License</a>. '''
                licenses_footer['unknown author'] = '''author unknown'''
                
                html = str()
                #template = self.template_remove_map(template)
                photo4template=dict()
                photo4template['page_file_local']=os.path.join(output_directory_path,image['uri'])
                photo4template['page_url_absolute']=self.sitemap_base_url+output_directory_name+'/'+image['uri']+'.htm'
                photo4template['uri']=image['uri']
                photo4template['image_url']=image['url']
                photo4template['image_url_base']=image['url'].replace('.jpg','')
                photo4template['thumbnail']=photo4template['image_url_base']+'.t.webp'
                photo4template['thumbnail_jpg']=photo4template['image_url_base']+'.t.jpg'
                photo4template['caption']=caption_location
                photo4template['caption_en']=image.get('caption_en','')
                photo4template['title']=image.get('title') or caption_location
                photo4template['url_left']=url_left
                photo4template['url_right']=url_right
                photo4template['rel_left']=rel_left
                photo4template['rel_right']=rel_right
                photo4template['map_js']=map_js
                photo4template['city']=image.get('city','')
                photo4template['datetime']=self.process_datetime_trolleway(image.get('datetime',''))
                photo4template['sublocation']=image.get('sublocation','')
                photo4template['tech_info']=tech_info
                photo4template['alt']=image.get('objectname','')
                photo4template['lat']=lat
                photo4template['lon']=lon
                photo4template['right_link_image']=right_link_image
                photo4template['left_link_image']=left_link_image
                photo4template['google_counter']=google_counter
                photo4template['yandex_counter']=yandex_counter
                photo4template['license_footer']=licenses_footer[image.get('license','cc-by')]
                photo4template['license']=image.get('license') #for index
                photo4template['source_srcset']=''
                photo4template['html_basedir']=html_basedir
                photo4template['optional_commons_link']=commons_link
                photo4template['optional_flickr_link']=flickr_link
                photo4template['optional_shutterstock_link']=shutterstock_link
                photo4template['prerender']='''{ "prerender":[{"urls":["'''+photo4template['url_right']+'''"]}]}'''
                
                if image.get('ar169'):
                    photo4template['source_srcset']+='<source srcset="{image_url_base}_ar169.webp" media="(min-aspect-ratio: 16/9)" type="image/webp">'.format(image_url_base=photo4template['image_url_base'])+"\n"
                if image.get('arvert'):
                    photo4template['source_srcset']+='<source srcset="{image_url_base}_arvert.webp" media="(max-aspect-ratio: 1/1)" type="image/webp">'.format(image_url_base=photo4template['image_url_base'])+"\n"
                if image.get('fit_contain'):
                    photo4template['image_css_class']='stack__element_forced_contain'
                else:
                    photo4template['image_css_class']='stack__element'
                    
                if 'ORIGINALFILE' not in image['url']:
                    photo4template['source_srcset']+='<source srcset="{image_url_base}.webp"  media="(min-aspect-ratio: 1/1)" type="image/webp">'.format(image_url_base=photo4template['image_url_base']) +"\n"
                else:
                    photo4template['source_srcset']=''
                    
                if image.get('canonical_url'):
                     photo4template['canonical_url']='<link rel="canonical" href="{canonical_url}" />'.format(canonical_url=image.get('canonical_url'))
                else:
                    photo4template['canonical_url']=''
                
                if photo4template['city'] != '': photo4template['city']+='.'
                assert photo4template['sublocation'] is not None, photo4template
                if photo4template['sublocation'] != '': photo4template['sublocation']+='.'
                
                sameas =schema_org_sameas
                if len(schema_org_sameas)==0:
                    sameastext = ''
                elif len(schema_org_sameas)==1:
                    sameastext = '"sameAs":"'+schema_org_sameas[0]+'",'
                elif len(schema_org_sameas)>1:
                    sameastext = '"sameAs": [' + ','.join(f'"{item}"' for item in schema_org_sameas) + '],'
                schema_org_js = '''<script type="application/ld+json">{"@context":"https:\/\/schema.org","@type":"ImageObject","contentUrl":"{contentUrl}","license":"https:\/\/creativecommons.org\/licenses\/by\/4.0","acquireLicensePage":"{page_url}", 
                {sameastext}
                "creator": {"@type": "Person","name": "Artem Svetlov"},
                "contentLocation": {"@type": "Place", "geo": {    "@type": "GeoCoordinates",    "latitude": "{lat}",    "longitude": "{lon}" }}}"}</script>'''
                schema_org_js=schema_org_js.replace('{contentUrl}',photo4template['image_url'])
                schema_org_js=schema_org_js.replace('{lat}',str(lat or ''))
                schema_org_js=schema_org_js.replace('{lon}',str(lon or ''))
                schema_org_js=schema_org_js.replace('{sameastext}',sameastext)
                schema_org_js=schema_org_js.replace('{page_url}',photo4template['page_url_absolute'].replace('/','\/'))
                photo4template['schema_org_js'] = schema_org_js
                
                photos4template.append(photo4template)
                #----------- end of photo page content


                with open(template_filepath, encoding='utf-8') as template_file:
                    template = template_file.read()
                html = template.format_map(photo4template)

                filename = photo4template['page_file_local'] +'.htm'
                with open(filename, "w", encoding='utf-8') as text_file:
                    text_file.write(html)

                if not data.get('hide'):
                    sitemap_page_record={'loc':photo4template['page_url_absolute']+'', 'image_url':photo4template['image_url']+''} #'priority':'0.4',
                    if image.get('sitemap_lastmod'):
                        sitemap_page_record['lastmod']=image.get('sitemap_lastmod')
                    
                    #sitemap_page_record['lastmod']=data.get('date_append')
                    pages2sitemap.append(sitemap_page_record)
                    

                popup_content = '<a href="{href}"><img src="{thumbnail}"><p>{title}</a>'.format(
                href=photo4template['uri']+'.htm',
                thumbnail=photo4template['image_url_base']+'.t.webp',
                title=photo4template['title']
                )
                leaflet_geojson_part = {
                "type": "Feature",
                "properties": {"popupContent":popup_content},
                "geometry": { "type": "Point", "coordinates": [photo4template['lon'], photo4template['lat']]}
                }
                if photo4template['lon'] != 0 and photo4template['lon'] is not None and photo4template['lon'] != 'null':
                    leaflet_geojson_features.append(leaflet_geojson_part)
                
            
            if not data.get('hide'):
                sitemap_page_record={'loc':self.sitemap_base_url+output_directory_name+'/'+'index.htm','priority':'0.6'}
                sitemap_page_record['lastmod']=GALLERY_DATE_MOD
                pages2sitemap.append(sitemap_page_record)
                
            


            # ----------- photos index page

            with open(template_index_filepath, encoding='utf-8') as template_file:
                template = template_file.read()

            if 'text_en' in data:
                content_en = '<div>'+data['text_en']+'</div>'+"\n"
            else:
                content_en = "\n"

            #html_text_filename = os.path.join(self.texts_dir,json_filename).replace('.json','.htm')
            #if os.path.exists(html_text_filename):
            #    text = self.get_body_from_html(html_text_filename)
            #else:
            #    text = data.get('text','')
                
            html_text_filename = os.path.join(self.texts_dir,json_filename.replace('.json',''),'HEADER.htm')
            print('search for '+html_text_filename)
            if os.path.exists(html_text_filename):
                text = data.get('text','') + "<p>\n" + self.get_body_from_html(html_text_filename)
            else:
                text = data.get('text','')
            #---------- copy images for header
            src = os.path.join(self.texts_dir,json_filename.replace('.json',''))
            if os.path.isdir(src):    
                dst = output_directory_path
                files=os.listdir(src)
                for fname in files:
                    if fname=='HEADER.htm':
                        continue
                    shutil.copy2(os.path.join(src,fname), dst)
            # if exists poster image for index.htm
            index_meta_og_image = ''

            if os.path.isfile(os.path.join(output_directory_path,'poster.jpg')):

                index_meta_og_image = '''<meta property="og:image" content="{url}" /> <meta name="twitter:image" content="{url}" />'''.format(url='https://trolleway.com/reports/'+os.path.split(output_directory_path)[-1]+'/poster.jpg')
                
                
            
                
            #---------- map on index page

            leaflet_geojson = {
    "type": "FeatureCollection",
    "features":leaflet_geojson_features
    }
            leaflet_geojson_text = 'var photos = '+json.dumps(leaflet_geojson, indent=None, sort_keys=True)+';'
            
            map_js = '''
            
  // initialize the map
  var map = L.map('map').setView([37.35, 55.08], 3);
var OpenStreetMap_DE = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
	maxZoom: 18,
	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});
var trolleway_tramlines = L.tileLayer('https://trolleway.nextgis.com/api/component/render/tile?resource=5101&x={x}&y={y}&z={z}', {
	maxZoom: 18,
	attribution: '&copy; Artem Svetlov'
});
var tiles = OpenStreetMap_DE.addTo(map);
var tiles = trolleway_tramlines.addTo(map);
'''
            map_js += leaflet_geojson_text
            map_js += '''
            
function onEachFeature(feature, layer) {
var popupContent = '' ; // make string from variables 
if (feature.properties && feature.properties.popupContent) {
    popupContent += feature.properties.popupContent;
}
layer.bindPopup(popupContent,{maxWidth : 800});
}
var geojsonMarkerOptions = {
	radius: 8,
	fillColor: "#ff7800",
	color: "#000",
	weight: 1,
	opacity: 1,
	fillOpacity: 0.8
};
var layer_photos = L.geoJSON(photos, {
    onEachFeature: onEachFeature,
	pointToLayer: function (feature, latlng) {
		return L.circleMarker(latlng, geojsonMarkerOptions);
	}
})
layer_photos.addTo(map);
map.fitBounds(layer_photos.getBounds());
            '''





            thumbnails_body = ''
            current_image = 0
            
            licenses_footer = dict()
            licenses_footer['cc-by']='''       <a rel="cc:attributionURL" property="dc:title">Page and images</a> by
       <a rel="dc:creator" href=""
       property="cc:attributionName">Artem Svetlov</a> is licensed to the public under
       the <a rel="license"
       href="https://creativecommons.org/licenses/by/4.0/">Creative
       Commons Attribution 4.0 License</a>.'''
            licenses_footer['mixed'] = ''' ''' 

            gallery_start_uri = photos4template[0]['uri']+'.htm'
            
            is_all_licenses_same = True
            for photo in photos4template:
                photo_html = '<p class="photo"><figure><a href="{photo_page_url}"><picture><source srcset="{url_thumbnail_webp}" type="image/webp"><img src="{url_thumbnail_jpg}"></picture></a><figcaption><span lang="ru" class="photo_index_caption_ru">{caption}</span>'
                if photo.get('caption_en'): photo_html += '<span lang="en" class="photo_index_caption_en">{caption_en}</span>'
                photo_html+="</figcaption></figure></p>"
                photo_html = photo_html.format(
                photo_page_url=photo['uri']+'.htm',
                url_thumbnail_jpg=os.path.join(os.path.dirname(photo['image_url']) , os.path.basename(os.path.splitext(photo['image_url'])[0])+'.t.jpg'),
                url_thumbnail_webp=os.path.join(os.path.dirname(photo['image_url']) , os.path.basename(os.path.splitext(photo['image_url'])[0])+'.t.webp'),
                caption=photo['caption'],
                caption_en=photo.get('caption_en'),
                )
                thumbnails_body += photo_html+"\n"
                
                if photo['license'] is not None: 
                    is_all_licenses_same = False
            datetime = data.get('datetime','')
            datetime = datetime[0:10]

            if is_all_licenses_same:
                license_footer = licenses_footer['cc-by']
            else:
                license_footer = licenses_footer['mixed']
            html = template.format(
                title = data['title'],
                text = text,
                content_en = content_en,
                h1 = data['h1'],
                city = data.get('city',''),
                datetime = datetime,
                google_counter=google_counter,
                yandex_counter=yandex_counter,
                thumbnails_body = thumbnails_body,
                map_js = map_js,
                gallery_start_uri=gallery_start_uri,
                license_footer = license_footer,
                description=self.drop_html_tags(text.split('\n')[0]+' Фото в высоком разрешении.'),
                meta_og_image=index_meta_og_image,
                html_basedir=html_basedir,
                )

            html = html.replace('<!--google_counter-->',google_counter)
            html = html.replace('<!--yandex_counter-->',yandex_counter)
            filename = os.path.join(output_directory_path,'index.htm')

            with open(filename, "w", encoding='utf-8') as text_file:
                text_file.write(html)

        #sitemap
        
        #index page last update for sitemap
        dates_galleries_create=list()
        for json_filename in json_files:
            with open(os.path.join(self.json_dir,json_filename), encoding='utf-8') as json_file:
                try:
                    data = json.load(json_file)
                except Exception as e:
                    print('error open json '+os.path.join(self.json_dir,json_filename))
                    print(e)
                    print()
                    continue
            assert data is not None
            if 'date_mod' in data:
                dates_galleries_create.append(data['date_mod'])

        latest_page_update = sorted(dates_galleries_create)[-1]
        sitemap_page_record={'loc':self.sitemap_base_url+''+'index.htm','priority':'0.6'}
        sitemap_page_record['lastmod']=latest_page_update
        pages2sitemap.insert(0,sitemap_page_record)
        sitemap_page_record={'loc':'https://trolleway.com/index.htm','priority':'0.2'}
        pages2sitemap.insert(0,sitemap_page_record)
                
        
        out = ''
        with open(sitemap_path_manual, encoding='utf-8') as sitemap_manual:
                sitemap_template = sitemap_manual.read()

        #regular photo pages to sitemap
        with open(sitemap_path, "w", encoding='utf-8') as text_file:
            
            for page in pages2sitemap:
                if 'image_url' in page:
                    imgurl='<image:image><image:loc>{url_image}</image:loc></image:image>'.format(url_image=page['image_url'])
                    if '.jpg.jpg' in page['image_url']: print('invalid image hotlink: ',page['image_url'])
                else:
                    imgurl = ''
                out += "<url><loc>{url}</loc>{imgurl}<lastmod>{lastmod}</lastmod></url>\n".format(
                url=page['loc'],imgurl=imgurl,lastmod=page.get('lastmod',''))

            out = out.replace('<lastmod></lastmod>','')
            text_file.write(sitemap_template.replace('<!--GENERATED SITEMAP CONTENT FROM PYTHON-->',out))

if __name__ == "__main__":
    processor = Website_generator(sitemap_base_url = 'https://trolleway.com/reports/')
    processor.generate_pages_list()
    processor.generate()