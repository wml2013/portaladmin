# Usage: Prints out current Index Status
# Replaces the 'output' block
# Using the getpass module to better handle passwords and remove the need to hardcode them

from arcgis.gis import GIS
import getpass

# Ask for admin/publisher user name and password and site url
username = input("Enter user name: ")
password = getpass.getpass("Enter password: ")
portalURL = input("Enter the URL of portal:")

gis = GIS(portalURL, username, password)
sysmgr = gis.admin.system
idx_status = sysmgr.index_status

import json
print(json.dumps(idx_status, indent=4))

# Output
{
  "indexes": [
    {
      "name": "users",
      "databaseCount": 51,
      "indexCount": 51
    },
    {
      "name": "groups",
      "databaseCount": 325,
      "indexCount": 325
    },
    {
      "name": "search",
      "databaseCount": 8761,
      "indexCount": 8761
    }
  ]
}