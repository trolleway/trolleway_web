
# Generator

simple python generator of static web photo gallery


```
docker build -f Dockerfile -t trolleway_website:dev .
cd ..
docker run --rm -it -v ${PWD}:/opt/website -v c:\trolleway\website-storage\storage\:/opt/storage trolleway_website:dev  /bin/bash
```
In container run:
```

time python3 generator/run.py
```

## Detailed process

### dir2json.py

* read folder with files
* read each jpg in system alphabet order
* create in this folder .json file with content: URL, IPTC City, IPTC Caption tags

user should manually move .json file to generator/content/

### run.py

* read json files from generator/content/
* generate index.htm for each gallery
* generate html pages
* generate sitemap files

### json 

* if text_html key is exists in json, text for index page will be taken from htm file with same name as json