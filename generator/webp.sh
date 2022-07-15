
echo "convert jpg to webp"
echo "usage:  ./webp.sh dir"

SRC=$1
DST=$1/webp

mkdir $DST

parallel --bar convert {} -define webp:lossless=false -define webp:auto-filter=true -define webp:image-hint=photo -define webp:method=6 $DST/{/}{/.}.webp :::  $SRC/*.jpg


DST=$1/jpg

mkdir $DST


parallel --bar convert {} - $DST/{/}{/.}.jpg :::  $SRC/*.jpg
