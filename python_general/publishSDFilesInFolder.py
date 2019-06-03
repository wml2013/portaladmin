from IPython.display import display
from arcgis.gis import GIS
import os
username = "siteadmin"
password = "*****"
gis = GIS("https://sdmsdev1w004.ordsvy.gov.uk/portal/home/", username, password)

# In order to have the codes below run smoothly, use the pre-requisite cells as in cell[2] to delete existing .zip, .sd, or services from the gis content, and in cell [3] to delete existing folder.
def delete_existing_items(item_types, name_list):
    for current_item_type in item_types:
        for file_name in name_list:    
            search_result = gis.content.search(query=file_name, item_type=current_item_type)
            if len(search_result) > 0:
                for item in search_result:
                    item.delete()
                    print("Deleted existing " + current_item_type + ": ", item)
                    
item_types = ["Service Definition", "Feature Layer Collection", "Map Service"]
name_list = ["Nursing_home_locations", "NewPy_WTL_test_SingleLayerBuildCache"]
delete_existing_items(item_types, name_list)

item_types = ["Shapefile", "Feature Layer Collection"]
name_list = ["power_pedestals_2012"]
delete_existing_items(item_types, name_list)

item_types = ["CSV", "Feature Layer Collection"]
name_list = ["Chennai_precipitation"]
delete_existing_items(item_types, name_list)

def delete_existing_folder(folder_name):
    try:
        return gis.content.delete_folder(folder=folder_name)
    except:
        return False

my_folder_name = "Rainfall Data"
delete_existing_folder(my_folder_name) # returns True if folder exists, or False if non-exist

# Publish all the service definition files in a folder
# The sample below lists all the service definition (.sd) files in a data directory and publishes them as web layers. To publish a service definition file, we first add the .sd file to the Portal, and then call the publish() method:

# path relative to this notebook
data_dir = "data/"

#Get list of all files
file_list = os.listdir(data_dir)

#Filter and get only .sd files
sd_file_list = [x for x in file_list if x.endswith(".sd")]
print("Number of .sd files found: " + str(len(sd_file_list)))

# Loop through each file and publish it as a service
for current_sd_file in sd_file_list:
    item = gis.content.add({}, data_dir + current_sd_file)   # .sd file is uploaded and a .sd file item is created
    if "BuildCache" not in current_sd_file:
        published_item = item.publish()                      # .sd file item is published and a web layer item is created
    else:
        published_item = item.publish(build_initial_cache=True)  # publish as hosted tile layer with "build cache" enabled
    display(published_item)