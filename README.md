# Automating ArcGIS Enterprise Administration tasks via Python API for ArcGIS

A bunch of python scripts that I use to help me automate ArcGIS Enterprise Admin Tasks such as adding users, adding groups, changing settings
Have used this as part of a complete hands off deployment using Azure RM + Powershell DSC.

## Running the scripts

python.exe PortalAdmin.py --config PortalConfigSettings.py --url "WebContextURL" --user "siteadmin" --password "PASSWORD"

## Files

**PortalAdmin.py**
This is the main file that is run and contains the code to create users, create groups, create roles, assign users to roles and groups as well as update Portal configuration settings

**PortalConfigSettings.py**
This is the main configuration file with configureable settings, majority of the configuration settings normally carried out via Portal Administration is now controlled by this file

**portaladmin_cleanup.py**
This file removes all users (apart from siteadmin and admin -- configureable), customised roles, customised groups and deleted users' content

e.g. syntax:
python.exe portaladmin_cleanup.py <https://skanska.azure.esriuk.com/arcgis> --user "siteadmin" --password "kkfkjd88jd"

**publish_content.py**
This file reads the users_trek.csv or users_large_trek.csv to attach content to each user

e.g. syntax:
python.exe publish_content.py <https://skanska.azure.esriuk.com/arcgis> --user "siteadmin" --password "kkfkjd88jd"

**users_trek.csv**
Contains a list of Star Trek Captains and characters. Used as basis for the creation of new Portal users.

**groups_trek.csv**
Contains a list of groups that users are assigned to.

## Folders

==Icons==

A folder of icons used for groups, users and some content.

==Logs==

A folder that contains the log files created by the localLogger.py module and can be deleted.

==Utils==

A folder that contains the localLogger module and supporting files. Please do not edit unless you know what you are doing.

==User_content==

A folder for user's content.

==_pycache_==

Folder used by localLogger.py