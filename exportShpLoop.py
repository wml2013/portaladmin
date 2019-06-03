# This will take the first shape in the dataframe and make Layers (temporary) and save them as shapefiles with different names like you wanted. Use the code in the Python window.

import arcpy, os
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd, "")[0]
lyr = arcpy.mapping.ListLayers(mxd, "", df)[0]

desc = arcpy.Describe(lyr)
for i in range(0,49):
    out = arcpy.MakeFeatureLayer_management(lyr, desc.basename+str(i)+"temp.shp",""""FID" = """ + str(i))
    arcpy.CopyFeatures_management(out, desc.path+os.sep +desc.basename+str(i)+".shp")