#!/bin/sh

#------------------------
generate_html() {
time python3 generator/model.py && time python3 generator/controller.py
}

#------------------------
rebuild_thumbnails() {
python3 generator/thumbnails-parallel.py

}

#------------------------
webmap_update() {
python3 generator/webmap_password.py

}
#------------------------
exif2sidecar() {

EXIFTOOL=/opt/exiftool/exiftool

HOME=/opt/images_origins
FILE=$(dialog --stdout --title "Choose any file in folder with JPG " --fselect $HOME/ 14 48)


if   [ -d "${FILE}" ]
then echo 'dir';
elif [ -f "${FILE}" ]
then FILE=$(dirname $FILE);
else 
	echo "${FILE} is not valid";
	whiptail --title "Test Message Box" --msgbox "${FILE} is not valid" 10 60
	return 0
     
fi

if (whiptail --title  "Yes/No Box" --yesno "Generate sidecar wxif files for directory ${FILE}" 10 60)  then
	 whiptail --title "Test Message Box" --msgbox "exiftool -ext JPG -o %d%f.xmp -r ${FILE}" 10 60
	 
	 $EXIFTOOL -ext JPG -o %d%f.xmp -r ${FILE}
	 $EXIFTOOL -ext jpg -o %d%f.xmp -r ${FILE}
	 $EXIFTOOL -ext TIF -o %d%f.xmp -r ${FILE}
	 $EXIFTOOL -ext tif -o %d%f.xmp -r ${FILE}
else
     return 0
fi




read -n 1 -s -r -p "Press any key to continue"
}

#------------------------

import_dir() {

HOME=/opt/images_origins
FILE=$(dialog --stdout --title "Choose any file in folder with JPG " --fselect $HOME/ 14 48)


if   [ -d "${FILE}" ]
then echo 'dir';
elif [ -f "${FILE}" ]
then FILE=$(dirname $FILE);
else 
	echo "${FILE} is not valid";
	whiptail --title "Test Message Box" --msgbox "${FILE} is not valid" 10 60
	return 0
     
fi


python3 generator/thumbnails-parallel.py --path ${FILE}

python3 generator/dir2db.py ${FILE}

}

#------------------------


while true
do
DIALOG=${DIALOG=dialog}
tempfile=`mktemp 2>/dev/null` || tempfile=/tmp/test$$
trap "rm -f $tempfile" 0 1 2 5 15

$DIALOG --clear --title "Select operation" \
        --menu "Select operation:" 20 81 8 \
        "generate_html"  "Generate HTML" \
        "rebuild_thumbnails"  "Rebuild thumbnails" \
        "import_dir"  "import/append photos from directory" \
        "webmap_update"  "webmap_update" \
        "exif2sidecar"  "exif2sidecar" \
        "exit"  "Exit" 2> $tempfile

retval=$?

choice=`cat $tempfile`



case $retval in
  0)

    case $choice in
        generate_html) generate_html;;
        rebuild_thumbnails) rebuild_thumbnails;;
        import_dir) import_dir;;
        webmap_update) webmap_update;;
        exif2sidecar) exif2sidecar;;
        mp4_merge) mp4_merge;;
        exit) exit;;
    esac;;
  1)
    echo "Отказ от ввода."
    exit;;
  255)
    echo "Нажата клавиша ESC."
    exit;;
esac
done
