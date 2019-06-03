# Python to remove the default world geocoder from Portal
#
# Connecting to my ArcGIS Enterprise
### I have a dodgy SSL certificate (self-signed) so need to ignore the error

from arcgis.gis import GIS
gis = GIS("https://test0205.local.net/arcgis/home","siteadmin",verify_cert=False)

# Let's make sure that I am getting the right server
gis

# This is the default Esri Geocode Service:
upd = {'geocodeService': [{
    "url": "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer",
    "northLat": "Ymax",
    "southLat": "Ymin",
    "eastLon": "Xmax",
    "westLon": "Xmin",
    "name": "Esri World Geocoder",
    "batch": "false",
    "placefinding": "true",
    "suggest": "true"},
]}

gis.update_properties(upd)


# Usage Example: Update the geocode service and call it 'AtlantaLocator'
upd = {'geocodeService': [{
  "singleLineFieldName": "Single Line Input",
  "name": "AtlantaLocator",
  "url": "https://some.server.com/server/rest/services/GeoAnalytics/AtlantaLocator/GeocodeServer",
  "itemId": "abc6e1fc691542938917893c8944606d",
  "placeholder": "",
  "placefinding": "true",
  "batch": "true",
  "zoomScale": 10000},
]}

gis.update_properties(upd)

# Usage Example: Deleting all geocode services in a rather brutal way
upd = {'geocodeService': []}
gis.update_properties(upd)