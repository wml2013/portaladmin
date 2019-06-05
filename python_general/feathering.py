# -*- coding: utf-8 -*- 
"""==============================================================================

 Title			:feathering.py
 Description		:Creating feathering for a polygon - shp or feature class
 Author		        :LF Velasquez - MapAction
 Date			:July 05 2019
 Version		:1.0
 Usage			:python feathering.py
 Notes			:If running python 3 the raw_input needs to be changed to input()
 python version	        :2.7.14

=============================================================================="""
# =============================================================================
# Modules - Libraries
# =============================================================================

import arcpy
import os 
import datetime

# =============================================================================
# Setting Global Variables
# =============================================================================
try:
    startTime = datetime.datetime.now()

    ##Set variable
    shp = raw_input('Please enter the shp file path (i.e. C:/folder/fileName.shp or C:/folder/gdb/fileName) : ')
    featherPath = raw_input('Please enter the folder path for the output: ')
    distanceNumber = int(raw_input ('Please enter the number of rings you would like (using between 10 and 20 buffers assures a smooth-looking gradation): '))
    bufferDistance = int(raw_input ('Please enter how wide you would like the rings - this will be done in meters i.e 500: '))
    distancesList = [] 
    
    # =============================================================================
    # Start of Main Process
    # =============================================================================
    
    ##Creating distance list
    distance = bufferDistance
    for i in range(distanceNumber):
        distancesList.append(distance)
        distance += bufferDistance


    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
    print '... creating the buffer'
    
    ##Set feather output name
    nameSplit = shp.split('\\')
    ##Checking if it is shp or feature class
    if nameSplit[-1].split('.')[-1] == 'shp':
        featherName = nameSplit[-1].split('.')[0] + '_feather.shp'
    else:
        featherName = nameSplit[-1] + '_feather'

    ##Set local variables for feathering
    inFeatures = shp
    outFeatureClass = featherPath + '\\' + featherName
    bufferUnit = "meters"
    expression = '((100 * !distance!)/!lg_dist!)'
    
     
    # Execute MultipleRingBuffer
    arcpy.MultipleRingBuffer_analysis(inFeatures, outFeatureClass, distancesList, bufferUnit, "", "ALL", "OUTSIDE_ONLY")

    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
    print '...adding field for symbology'
    arcpy.AddField_management(outFeatureClass, "Xpar", "SHORT", "", "", "", "", "", "NON_REQUIRED", "")
    arcpy.AddField_management(outFeatureClass, "lg_dist", "SHORT", "", "", "", "", "", "NON_REQUIRED", "")
    arcpy.CalculateField_management(outFeatureClass, "lg_dist", distancesList[-1], "PYTHON_9.3")
    arcpy.CalculateField_management(outFeatureClass, "Xpar", expression, "PYTHON_9.3")
    arcpy.DeleteField_management(outFeatureClass, ["lg_dist"])

    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
    print '...creating readme file for feather display in arcmap'
    ##Set output location - add file outside of gdb if neccesary
    nameSplit = featherPath.split('\\')
    check = nameSplit[-1].split('.')
    if check[-1] == 'gdb':
        file_path = '\\'.join(featherPath.split('\\')[:-1])
    else:
        file_path = featherPath
    my_file = os.path.join(file_path, 'feather_readme.txt')
    file = open(my_file, "w") 
    file.write("To symbolize the feather in arcamp: \n"
               "1. On the Symbology tab, show the features using a single symbol with a the desired colour and no outline (set the outline color to No color) \n"
               "2. Click the Advanced button and click Transparency \n"
               "3. Set the field to Xpar and click OK twice to see the results.") 
    file.close()


except Exception:
    e = sys.exc_info()[1]
    print(e.args[0])

print '--------------------------'  
print '--------------------------' 
print '--------------------------'  
print 'Time running the script' + ' ' + str(datetime.datetime.now() - startTime) 
print ' Check files in %s - hit enter to close window' %featherPath