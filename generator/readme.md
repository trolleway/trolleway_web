
# Generator

simple python generator of static web photo gallery


```
docker build -f Dockerfile -t trolleway_website:dev .
cd ..
docker run --rm -it -v ${PWD}:/opt/website -v c:\trolleway\website-storage\storage\:/opt/storage -v c:\trolleway\website-storage\master\:/opt/images_origins  trolleway_website:dev  /bin/bash
docker run --rm -it -v c:\trolleway\trolleway_web\trolleway_web\:/opt/website -v c:\trolleway\trolleway_web\storage\:/opt/storage -v c:\trolleway\trolleway_web\storage\origins\:/opt/images_origins  trolleway_website:dev  /bin/bash
```
Add photos to database:
```
time python3 generator/thumbnails-parallel.py
python3 generator/dir2db.py
run sql in sqlite 
```

Generate html:
```
time python3 generator/model.py && time python3 generator/controller.py
```

## Handle tiff and webp sources

Convert any uncompressed file to loseless webp + metadata files
```
SRC=/opt/images_origins/2022/2022-08-20_vvo_silbera50_src
DST=/opt/images_origins/2022/2022-08-20_vvo_silbera50
mkdir $DST
mogrify -format webp -define webp:lossless=true -path $DST $SRC/*.tif 


parallel "exiftool -charset utf8 -json -all:all -X {} >  {.}.json" ::: $SRC/*.tif
mv $SRC/*.xml $DST


```

### controller.py

* read json files from generator/content/
* generate index.htm for each gallery
* generate html pages
* generate sitemap files

### json 

* if text_html key is exists in json, text for index page will be taken from htm file with same name as json