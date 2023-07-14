FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update 
RUN apt-get install --no-install-recommends -y python3-pip time imagemagick parallel gdal-bin git

ARG uid=1000
ARG gid=1000
RUN groupadd -g $gid trolleway && useradd --home /home/trolleway -u $uid -g $gid trolleway  \
  && mkdir -p /home/trolleway && chown -R trolleway:trolleway /home/trolleway
RUN echo 'trolleway:user' | chpasswd

RUN pip3 install exif iptcinfo3 requests shapely python-dateutil tqdm GDAL
RUN pip3 install --upgrade --force-reinstall git+https://github.com/nextgis/pyngw.git

#RUN apt-get install -y exiftool
#install latest exiftool for webp write from https://exiftool.org/forum/index.php?topic=11619.0 https://github.com/marco-schmidt/am/blob/c5b7904cdd1629f08caac09e90f0f53a2393ca1b/Dockerfile#L30
RUN set -ex; \
  export DEBIAN_FRONTEND=noninteractive; \
  apt-get install -y  curl; \
  curl --version; \
  perl -v ;\
  mkdir -p /opt/exiftool ;\
  cd /opt/exiftool ;\
  EXIFTOOL_VERSION=`curl -s https://exiftool.org/ver.txt` ;\
  EXIFTOOL_ARCHIVE=Image-ExifTool-${EXIFTOOL_VERSION}.tar.gz ;\
  curl -s -O https://exiftool.org/$EXIFTOOL_ARCHIVE ;\
  CHECKSUM=`curl -s https://exiftool.org/checksums.txt | grep SHA1\(${EXIFTOOL_ARCHIVE} | awk -F'= ' '{print $2}'` ;\
  echo "${CHECKSUM}  ${EXIFTOOL_ARCHIVE}" | /usr/bin/sha1sum -c  - ;\
  tar xzf $EXIFTOOL_ARCHIVE --strip-components=1 ;\
  rm -f $EXIFTOOL_ARCHIVE ;\
  ./exiftool -ver && cd /

RUN apt-get install -y  dialog whiptail

#add to sudoers
RUN apt-get install -y apt-utils
RUN apt-get install -y sudo
RUN adduser trolleway sudo
RUN usermod -aG sudo trolleway

ADD https://api.github.com/repos/trolleway/trolleway.github.io/git/refs/heads/master   ver.json
#The API call will return different results when the head changes, invalidating the docker cache

RUN mkdir /opt/website

RUN pip3 install --upgrade numpy

RUN chmod  --recursive 777 /opt/website

WORKDIR /opt/website
ENTRYPOINT ["/opt/website/interface.sh"] 
