docker build -f Dockerfile -t trolleway_website:dev .
docker run --rm -it -v ${PWD}:/opt/website -v c:\trolleway\website-storage\storage\:/opt/storage -v c:\trolleway\website-storage\master\:/opt/images_origins  trolleway_website:dev  /bin/bash

pause