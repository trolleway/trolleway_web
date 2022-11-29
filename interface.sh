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

import_dir() {
dialog --title "Choose any file in folder" --fselect ~ 30 60
FILE=$(dialog --stdout --title "Choose any file in folder with JPG and gpx" --fselect $HOME/ 14 48)
echo "${FILE} file chosen."


if   [ -d "${FILE}" ]
then echo 'dir';
elif [ -f "${FILE}" ]
then FILE=$(dirname $FILE);
else echo "${FILE} is not valid";
     
fi



echo ${FILE}
read -n 1 -s -r -p "Press any key to continue"

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
        "import_dir"  "import_dir" \
        "exit"  "Exit" 2> $tempfile

retval=$?

choice=`cat $tempfile`



case $retval in
  0)

    case $choice in
        generate_html) generate_html;;
        rebuild_thumbnails) rebuild_thumbnails;;
        import_dir) import_dir;;
        xiaomi360_logo) xiaomi360_logo;;
        gopro_video) gopro_video;;
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
