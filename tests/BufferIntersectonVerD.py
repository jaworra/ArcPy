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
    for lyr in arcpy.mapping.ListLayers(mxd):
         if lyr.name != "SF_Metrageroads_CalibratedRoutes" and lyr.name != "SF_kmPosts" and lyr.name != "Contour_70dBA" and lyr.name != "Contour_75dBA" and lyr.name != "Contour_80dBA" and lyr.name != "Contour_85dBA":# Layers to display
             arcpy.mapping.RemoveLayer(df, lyr)
         else:
             lyr.visible = True
    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()    

    #Zoom Extents
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
    df.zoomToSelectedFeatures()
    arcpy.RefreshActiveView()


#Noise contour generation
def createNoiseContour(ProjectedFeat,SoundCat,ClipLimit):
    
    #---Left Analysis
    AnalysisSide = "LEFT"
    DistField = "D"+SoundCat #First letter determines right or left side to analyis (Assumption D is always left U is always right)
    ClipLimit= "D"+ClipLimit
               
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
        arcpy.Buffer_analysis(ProjectedFeat, MaxNoiseSeg ,ClipLimit, AnalysisSide, EndType, DisType,) 
    #Dissolve
    arcpy.Dissolve_management(MaxNoiseSeg, MaxNoiseBuffer,"", "", "", "")    

    #Clip Max vs Actual
    arcpy.Clip_analysis(ActualNoiseBuffer, MaxNoiseBuffer, AnalysisSide, xy_tolerance)



    #---Right Analysis
    AnalysisSide = "RIGHT"
    DistField = "U"+SoundCat #First letter determines right or left side to analyis (Assumption D is always left U is always right)
    ClipLimit= "U"+ClipLimit
    
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
        arcpy.Buffer_analysis(ProjectedFeat, MaxNoiseSeg ,ClipLimit, AnalysisSide, EndType, DisType,) 
    #Dissolve
    arcpy.Dissolve_management(MaxNoiseSeg, MaxNoiseBuffer,"", "", "", "")    

    #Clip Max vs Actual
    arcpy.Clip_analysis(ActualNoiseBuffer, MaxNoiseBuffer, AnalysisSide, xy_tolerance)

    #Merge and Disolve Final Sound Buffer
    arcpy.Merge_management(["LEFT", "RIGHT"], "MERGE")
    arcpy.Dissolve_management("MERGE", "Contour_"+SoundCat,"", "", "", "")


# MainFunction
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
lyr = "Seg_events"
arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#Export to shp
#Set projection to MGA94 Z56, assumes Brisbane
ProjectedFeat = "SegGrid"
install_dir = arcpy.GetInstallInfo()['InstallDir']
out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

arcpy.Project_management(lyr, ProjectedFeat, out_coordinate_system)

#Parse Varaiables (Segmented line,Sound category)
SoundCat1 = "70dbV"
SoundCat2 = "75dbV"
SoundCat3 = "80dbV"
SoundCat4 = "85dbV"

ClipLimit = "150mV" #Either 150mV or 250mV

createNoiseContour(ProjectedFeat,SoundCat1,ClipLimit) 
createNoiseContour(ProjectedFeat,SoundCat2,ClipLimit) 
createNoiseContour(ProjectedFeat,SoundCat3,ClipLimit) 
createNoiseContour(ProjectedFeat,SoundCat4,ClipLimit) 

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


        
