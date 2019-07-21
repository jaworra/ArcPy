#-------------------------------------------------------------------------------
# Name: Mapping Script for QRN
# Purpose: QRN Transport Rail Noise Contours - Setback Distances
# Segment Meterage Road with Kilometre post
#
# Author: John Worrall
# Created: 05/02/2013
#-------------------------------------------------------------------------------
# Remove all local variables

##Requirements:
# Excel Spreadsheet Noise Buffer formatt - Prefix,LNRStartValue,LNREndValue,U85dbV,U80dbV,U75dbV,U70dbV,U150mV,U250mV,D85dbV,D80dbV,D75dbV,D70dbV,D150mV,D250mV
# Excel Spreadsheet Metrage Rail Segment formatt - LineName,Attribute,StartKM,EndKM,KMCentre,Latitude,Longitude,Prefix,KM_Centre,M_Centre,Thru
# Datasets - SF_Metrageroads_CalibratedRoutes,SF_kmPosts


#Import arcpy modules
import arcpy, sys, os, re,glob
from arcpy import env

#Set local variables
InFeature = 'SF_kmPosts'
ChAttr = 'Distance'
NearFeature = 'SF_Metrageroads_CalibratedRoutes'

#Copy input points features to temporary feature class for Km Post and MeterageLine
env.overwriteOutput = True
scratchWorkspace = arcpy.GetParameterAsText(2)
scratchWorkspace = env.scratchWorkspace
TempFC = os.path.join(scratchWorkspace,'tempPoint')
arcpy.CopyFeatures_management(InFeature,TempFC)

#Add XY Coordinates for point features
arcpy.AddXY_management(TempFC)

#Near Analysis - requires 3D analyst
#arcpy.Near_analysis(TempFC,NearFeature,'','LOCATION', 'NO_ANGLE')

#Segment Line with included attributes
#Create TempLine
TempFC = os.path.join(scratchWorkspace,'tempLine')
arcpy.CopyFeatures_management(NearFeature,TempFC)



#Loop through point Km post 
rows = arcpy.SearchCursor(InFeature)
for row in rows:
    EndCh = row.getValue(ChAttr)
    if EndCh != 0: #Skip first point - Where Km post is equal to the start
        POINT_X = row.shape.centroid.X
        POINT_Y = row.shape.centroid.Y      
        print EndCh, POINT_Y,POINT_X


##-------------------------------------------------------------------------------------------
#Segment Line with included attributes
#Create TempLine  #HERE
arcpy.CopyFeatures_management('tempLine', 'MetrageRail_Segmented')







##-------------------------------------------------------------------------------------------
#Segmentation Noise Contours Process
#Set local variables
rt = "tempLine"          # the 'hwy' feature class is in the 'roads' feature dataset
rid = "Prefix" 
tbl = "Shorncliffe$"
props = "Prefix LINE LNRStartValue LNREndValue"
lyr = "pave_events"

arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
input_features = "pave_events"
output_features_class = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\TTSF_LNR.shp"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(input_features, output_features_class, out_coordinate_system)

#Buffer
#Set local variables
OutFileDir = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\Buffer_TTSF_LNR.shp"
DistField = "U70dbV"
SideType = "LEFT"
EndType = "ROUND"
DisType = "NONE"
featureClasses = ['TTSF_LNR']

for featureClass in featureClasses:
    arcpy.Buffer_analysis('TTSF_LNR' , OutFileDir ,DistField, "LEFT", EndType, DisType, )

#Dissolve
arcpy.Dissolve_management('Buffer_TTSF_LNR', 'Buffer_TTSF_LNR',"", "", "", "")    

#Clip Buffer @ 150m
#Create polygon to clip
arcpy.Buffer_analysis('templine' , 'ClipBuffer' ,'150 meter', "LEFT", "ROUND", "NONE",) 

#Set local variables
in_features = "Buffer_TTSF_LNR"
clip_features = "ClipBuffer"
out_feature_class = "Contour_70dBA"
xy_tolerance = ""

# Execute Clip
arcpy.Clip_analysis(in_features, clip_features, out_feature_class, xy_tolerance)

##-------------------------------------------------------------------------------------------
#Cosmetic
#Turn off all other Layers
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]

for lyr in arcpy.mapping.ListLayers(mxd):
     if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dBA":# Layers to display
         lyr.visible = False
     if lyr.name == "Buffer_TTSF_LNR":
         arcpy.mapping.RemoveLayer(df, lyr)
arcpy.RefreshTOC()
arcpy.RefreshActiveView()    

#Zoom Extents
#df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
df.zoomToSelectedFeatures()
arcpy.RefreshActiveView()

##-------------------------------------------------------------------------------------------
#Repeat for Other Noise Section -75DBA
##-------------------------------------------------------------------------------------------

#Segmentation Process
#Set local variables
rt = "tempLine"          # the 'hwy' feature class is in the 'roads' feature dataset
rid = "Prefix" 
tbl = "Shorncliffe$"
props = "Prefix LINE LNRStartValue LNREndValue"
lyr = "pave_events"

arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
input_features = "pave_events"
output_features_class = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\TTSF_LNR.shp"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(input_features, output_features_class, out_coordinate_system)

#Buffer
#Set local variables
OutFileDir = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\Buffer_TTSF_LNR.shp"
DistField = "U75dbV"
SideType = "LEFT"
EndType = "ROUND"
DisType = "NONE"
featureClasses = ['TTSF_LNR']

for featureClass in featureClasses:
    arcpy.Buffer_analysis('TTSF_LNR' , OutFileDir ,DistField, "LEFT", EndType, DisType, )

#Dissolve
arcpy.Dissolve_management('Buffer_TTSF_LNR', 'Buffer_TTSF_LNR',"", "", "", "")    

#Clip Buffer @ 150m
#Create polygon to clip
arcpy.Buffer_analysis('templine' , 'ClipBuffer' ,'150 meter', "LEFT", "ROUND", "NONE",) 

#Set local variables
in_features = "Buffer_TTSF_LNR"
clip_features = "ClipBuffer"
out_feature_class = "Contour_75dBA"
xy_tolerance = ""

# Execute Clip
arcpy.Clip_analysis(in_features, clip_features, out_feature_class, xy_tolerance)


##-------------------------------------------------------------------------------------------
#Cosmetic
#Turn off all other Layers
mxd = arcpy.mapping.MapDocument("CURRENT")
for lyr in arcpy.mapping.ListLayers(mxd):
     if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dBA" and lyr.name != "Contour_75dBA":# Layers to display
         lyr.visible = False
     if lyr.name == "Buffer_TTSF_LNR":
         arcpy.mapping.RemoveLayer(df, lyr)
arcpy.RefreshTOC()
arcpy.RefreshActiveView()    

#Zoom Extents
df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
df.zoomToSelectedFeatures()
arcpy.RefreshActiveView()

##-------------------------------------------------------------------------------------------
#Repeat for Other Noise Section -80DBA
##-------------------------------------------------------------------------------------------

#Segmentation Process
#Set local variables
rt = "tempLine"          # the 'hwy' feature class is in the 'roads' feature dataset
rid = "Prefix" 
tbl = "Shorncliffe$"
props = "Prefix LINE LNRStartValue LNREndValue"
lyr = "pave_events"

arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
input_features = "pave_events"
output_features_class = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\TTSF_LNR.shp"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(input_features, output_features_class, out_coordinate_system)

#Buffer
#Set local variables
OutFileDir = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\Buffer_TTSF_LNR.shp"
DistField = "U80dbV"
SideType = "LEFT"
EndType = "ROUND"
DisType = "NONE"
featureClasses = ['TTSF_LNR']

for featureClass in featureClasses:
    arcpy.Buffer_analysis('TTSF_LNR' , OutFileDir ,DistField, "LEFT", EndType, DisType, )

sys.exit(3)

#Dissolve
arcpy.Dissolve_management('Buffer_TTSF_LNR', 'Buffer_TTSF_LNR',"", "", "", "")    

#Clip Buffer @ 150m
#Create polygon to clip
arcpy.Buffer_analysis('templine' , 'ClipBuffer' ,'150 meter', "LEFT", "ROUND", "NONE",) 

#Set local variables
in_features = "Buffer_TTSF_LNR"
clip_features = "ClipBuffer"
out_feature_class = "Contour_80dBA"
xy_tolerance = ""

# Execute Clip
arcpy.Clip_analysis(in_features, clip_features, out_feature_class, xy_tolerance)

##-------------------------------------------------------------------------------------------
#Cosmetic
#Turn off all other Layers
mxd = arcpy.mapping.MapDocument("CURRENT")
for lyr in arcpy.mapping.ListLayers(mxd):
     if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dBA" and lyr.name != "Contour_75dBA" and lyr.name != "Contour_80dBA":# Layers to display
         lyr.visible = False
     if lyr.name == "Buffer_TTSF_LNR":
         arcpy.mapping.RemoveLayer(df, lyr)
arcpy.RefreshTOC()
arcpy.RefreshActiveView()    

#Zoom Extents
df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
df.zoomToSelectedFeatures()
arcpy.RefreshActiveView()

##-------------------------------------------------------------------------------------------
#Repeat for Other Noise Section -85DBA
##-------------------------------------------------------------------------------------------

#Segmentation Process
#Set local variables
rt = "tempLine"          # the 'hwy' feature class is in the 'roads' feature dataset
rid = "Prefix" 
tbl = "Shorncliffe$"
props = "Prefix LINE LNRStartValue LNREndValue"
lyr = "pave_events"

arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
input_features = "pave_events"
output_features_class = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\TTSF_LNR.shp"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(input_features, output_features_class, out_coordinate_system)

#Buffer
#Set local variables
OutFileDir = "G:\Geospatial\GIS\JohnW\QRN\CaseStudy1\QLD_Development_Code_Noise_Contours\JW_Workings\Buffer_TTSF_LNR.shp"
DistField = "U85dbV"
SideType = "LEFT"
EndType = "ROUND"
DisType = "NONE"
featureClasses = ['TTSF_LNR']

for featureClass in featureClasses:
    arcpy.Buffer_analysis('TTSF_LNR' , OutFileDir ,DistField, "LEFT", EndType, DisType, )

#Dissolve
arcpy.Dissolve_management('Buffer_TTSF_LNR', 'Buffer_TTSF_LNR',"", "", "", "")    

#Clip Buffer @ 150m
#Create polygon to clip
arcpy.Buffer_analysis('templine' , 'ClipBuffer' ,'150 meter', "LEFT", "ROUND", "NONE",) 

#Set local variables
in_features = "Buffer_TTSF_LNR"
clip_features = "ClipBuffer"
out_feature_class = "Contour_85dBA"
xy_tolerance = ""

# Execute Clip
arcpy.Clip_analysis(in_features, clip_features, out_feature_class, xy_tolerance)

##-------------------------------------------------------------------------------------------
#Cosmetic
#Turn off all other Layers
mxd = arcpy.mapping.MapDocument("CURRENT")
for lyr in arcpy.mapping.ListLayers(mxd):
     if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dBA" and lyr.name != "Contour_75dBA" and lyr.name != "Contour_80dBA" and lyr.name != "Contour_85dBA":# Layers to display
         lyr.visible = False
     else:
         lyr.visible = True
     if lyr.name == "Buffer_TTSF_LNR" or lyr.name == "ClipBuffer" or lyr.name == "tempLine" or lyr.name == "tempPoint" or lyr.name == "TTSF_LNR" or lyr.name == "pave_events" or lyr.name == "Buffer_TTSF_LNR_CLIP2":
         arcpy.mapping.RemoveLayer(df, lyr)
arcpy.RefreshTOC()
arcpy.RefreshActiveView()    

#Zoom Extents
df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
df.zoomToSelectedFeatures()
arcpy.RefreshActiveView()

##-------------------------------------------------------------------------------------------
#Copy and Append 
arcpy.CopyFeatures_management("Contour_70dBA", "SF_NoiseContour")
arcpy.Append_management(["Contour_75dBA","Contour_80dBA","Contour_85dBA"], "SF_NoiseContour", "","","")

##-------------------------------------------------------------------------------------------
print "##-------------------------------------------------------------------------------------------"
print "Succusfully Completed"
print "##-------------------------------------------------------------------------------------------"
##-------------------------------------------------------------------------------------------
#Adjust side of to buffer on tracks OR
#Determine the outmost track in both directions and apply buffer accordingly.


##-------------------------------------------------------------------------------------------
##-------------------------------------------------------------------------------------------


        
