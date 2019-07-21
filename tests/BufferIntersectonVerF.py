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

#Remove layers not required
def cleanUpLayers():

    #Clean up - Turn on/off and delete layers
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
    
    for lyr in arcpy.mapping.ListLayers(mxd):
         if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dbV" and lyr.name != "Contour_75dbV" and lyr.name != "Contour_80dbV" and lyr.name != "Contour_85dbV":# Layers to display
             arcpy.mapping.RemoveLayer(df, lyr)
         else:
             lyr.visible = True
    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()    

    #Zoom Extents
    df.zoomToSelectedFeatures()
    arcpy.RefreshActiveView()


#Noise contour generation
def createNoiseContour(ProjectedFeat,SoundCat,ClipLimit):
    
    #---Left Analysis
    AnalysisSide = "LEFT"
    DistField = "D"+SoundCat #First letter determines right or left side to analyis (Assumption D is always left U is always right)
    ClipLimitSide = "D"+ClipLimit
               
    ActualNoiseSeg = AnalysisSide+SoundCat+ "ActSegBuffer"
    ActualNoiseBuffer = AnalysisSide+SoundCat+ "ActBuffer"

    MaxNoiseSeg = AnalysisSide+SoundCat+ "MaxSegBuffer"
    MaxNoiseBuffer = AnalysisSide+SoundCat+ "MaxBuffer" 

    SideType = "FULL"
    EndType = "ROUND"
    DisType = "NONE"

    out_feature_class = AnalysisSide
    xy_tolerance = ""

    #Actual NoiseReadings
    for featureClass in ProjectedFeat:
        arcpy.Buffer_analysis(ProjectedFeat, ActualNoiseSeg ,DistField, SideType, EndType, DisType, )
    #Dissolve
    arcpy.Dissolve_management(ActualNoiseSeg, ActualNoiseBuffer,"", "", "", "")    

    #Max NoiseBuffer
    for featureClass in ClipLimit:
        arcpy.Buffer_analysis(ProjectedFeat, MaxNoiseSeg ,ClipLimitSide, AnalysisSide, EndType, DisType,) 
    #Dissolve
    arcpy.Dissolve_management(MaxNoiseSeg, MaxNoiseBuffer,"", "", "", "")    

    #Clip Max vs Actual
    arcpy.Clip_analysis(ActualNoiseBuffer, MaxNoiseBuffer, AnalysisSide, xy_tolerance)


    #---Right Analysis
    AnalysisSide = "RIGHT"
    DistField = "U"+SoundCat #First letter determines right or left side to analyis (Assumption D is always left U is always right)
    ClipLimitSide= "U"+ClipLimit
    
    ActualNoiseSeg = AnalysisSide+SoundCat+ "ActSegBuffer"
    ActualNoiseBuffer = AnalysisSide+SoundCat+ "ActBuffer"

    MaxNoiseSeg = AnalysisSide+SoundCat+ "MaxSegBuffer"
    MaxNoiseBuffer = AnalysisSide+SoundCat+ "MaxBuffer" 

    #Actual NoiseReadings
    for featureClass in ProjectedFeat:
        arcpy.Buffer_analysis(ProjectedFeat, ActualNoiseSeg ,DistField, SideType, EndType, DisType, )
    #Dissolve
    arcpy.Dissolve_management(ActualNoiseSeg, ActualNoiseBuffer,"", "", "", "")    

    #Max NoiseBuffer
    for featureClass in ClipLimit:
        arcpy.Buffer_analysis(ProjectedFeat, MaxNoiseSeg ,ClipLimitSide, AnalysisSide, EndType, DisType,) 
    #Dissolve
    arcpy.Dissolve_management(MaxNoiseSeg, MaxNoiseBuffer,"", "", "", "")    

    #Clip Max vs Actual
    arcpy.Clip_analysis(ActualNoiseBuffer, MaxNoiseBuffer, AnalysisSide, xy_tolerance)

    #Merge and Disolve Final Sound Buffer
    arcpy.Merge_management(["LEFT", "RIGHT"], "MERGE")
    arcpy.Dissolve_management("MERGE", "Contour_"+SoundCat,"", "", "", "")
    
    return "Contour_"+SoundCat



#Segmentation Centre Line----------------------------------------------------------
#Set local variables
rt = "tempLine"          # the 'hwy' feature class is in the 'roads' feature dataset
rid = "Prefix" 
tbl = "Shorncliffe_SF_GIS$"
props = "Prefix LINE LNRStartValue LNREndValue"
lyr = "Seg_events"
SaveLoc = "G:/Geospatial/GIS/JohnW/QRN/CaseStudy1/QLD_Development_Code_Noise_Contours/JW_Workings/20130304/"

arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
ProjectedFeat = "SegGrid"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(lyr, ProjectedFeat, out_coordinate_system)

#Sort/Delete by column and save output
arcpy.DeleteField_management(ProjectedFeat, ["F2","F4","F6","F13","F20","LOC_ERROR","U85dbV","U80dbV","U75dbV","U70dbV","U150mV"]) 'Delete all other fields 
arcpy.CopyFeatures_management(ProjectedFeat,SaveLoc+tbl.strip("$")+"_SegmentedLine.shp")


["F2","F4","F6","F13","F20","LOC_ERROR","U85dbV","U80dbV","U75dbV","U70dbV","U150mV","U250mV","D85dbF","D80dbF","D75dbF","D70dbF","D85dbV","D80dbV","D75dbV","D70dbV","D150mV","D250mV"]

#"U85dbV","U80dbV","U75dbV","U70dbV","U150mV","U250mV","D85dbF","D80dbF","D75dbF","D70dbF","D85dbV","D80dbV","D75dbV","D70dbV","D150mV","D250mV"
#["F2","F4","F6","F13","F20","LOC_ERROR", "U85dbV",]



sys.exit(3)
                              
#----------------------------------------------------------

#Parse Varaiables (Segmented line,Sound category)
SoundCat1 = "70dbV"
SoundCat2 = "75dbV"
SoundCat3 = "80dbV"
SoundCat4 = "85dbV"
ClipLimit = "150mV" #Either 150mV or 250mV

#Generate Contour,Save and Clean
LayerName = createNoiseContour(ProjectedFeat,SoundCat1,ClipLimit)
arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl.strip("$")+"_Contour"+SoundCat1+".shp")
cleanUpLayers()

LayerName = createNoiseContour(ProjectedFeat,SoundCat2,ClipLimit)
arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl.strip("$")+"_Contour"+SoundCat2+".shp")
cleanUpLayers()
                                 
LayerName = createNoiseContour(ProjectedFeat,SoundCat3,ClipLimit)
arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl.strip("$")+"_Contour"+SoundCat3+".shp")
cleanUpLayers()
                                 
LayerName = createNoiseContour(ProjectedFeat,SoundCat4,ClipLimit)
arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl.strip("$")+"_Contour"+SoundCat4+".shp")
cleanUpLayers()



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




#MAIN FOR LOOP
metrageRoutes = "MetrageRoads_Base"
tempLine = "queryLines"
railPrefix = 'BN'

#Select Line for Segementation
SelectedFeature = arcpy.SelectLayerByAttribute_management (metrageRoutes,"NEW_SELECTION", "PREFIX = '%s' "%railPrefix)
arcpy.CopyFeatures_management(SelectedFeature,tempLine)

relatedID = "Prefix"
tempLine = "Export_Output"
tbl = "Gold_Coast$"
props = "Prefix LINE LNRStartV LNREndV"
lyr = "Seg_events"
arcpy.MakeRouteEventLayer_lr (tempLine, relatedID, tbl, props, lyr, "#",  "ERROR_FIELD")


sys.exit(3)


#Run through all open excel spreadsheets 
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd) [0]

for lyr in arcpy.mapping.ListTableViews(mxd):
     print lyr.name

#Sort/Delete by column and save output
     


#Create route event from return
        
