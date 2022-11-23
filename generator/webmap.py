import pyngw
#import config ещё не написал

ngwapi = pyngw.Pyngw(ngw_url = 'https://trolleway.nextgis.com', login = '', password = '')
ngwapi.replace_vector_layer(group_id=5035,old_display_name='photos',filepath='/opt/website/html/temp_photos.gpkg')
