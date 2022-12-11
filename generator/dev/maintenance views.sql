-- этот не работает на запись в dbeaver
DROP VIEW IF EXISTS photos_input;
CREATE view photos_input 
AS
SELECT
photos.hotlink,
photos.objectname,
photos.caption,
photos.caption_en,
photos.sublocation,
photos.wkt_geometry,
photos.update_timestamp,
photos.direction_inout ,
photos.print_direction,
photos.photoid 
FROM photos
ORDER BY photoid DESC;

-- clean zero geometry
UPDATE photos
SET wkt_geometry = NULL
WHERE wkt_geometry LIKE '%(0.0%';

-- canonical URLs and geodata
SELECT DISTINCT photoid, uri|| '/' || printf('%05d',photoid) || '.htm' AS url, wkt_geometry, direction, datetime FROM(
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
GROUP BY photoid