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
         if lyr.name != "StateWide_MetrageRoads" and lyr.name != "Contour_70dbV" and lyr.name != "Contour_75dbV" and lyr.name != "Contour_80dbV" and lyr.name != "Contour_85dbV":# Layers to display
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
#Set overwrite on
arcpy.env.overwriteOutput = True

#Run through all open excel spreadsheets 
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd) [0]

for lyr in arcpy.mapping.ListTableViews(mxd):
    print lyr.name

    #Set local variables
    rt = "StateWide_MetrageRoads"
    rid = "Prefix" 
    tbl = lyr.name.strip("$")
    props = "Prefix LINE LNRStartValue LNREndValue"
    lyr = "Seg_events"
    SaveLoc = "G:/Geospatial/GIS/JohnW/QRN/CaseStudy1/QLD_Development_Code_Noise_Contours/JW_Workings/20130305/Deliverables/"

    arcpy.MakeRouteEventLayer_lr (rt, rid, tbl+"$", props, lyr, "#",  "ERROR_FIELD")

    #Export to shp
    #Set projection to MGA94 Z56, assumes Brisbane
    ProjectedFeat = "SegGrid"
    install_dir = arcpy.GetInstallInfo()['InstallDir']
    out_coordinate_system = os.path.join(install_dir, r"Coordinate Systems/Projected Coordinate Systems/National Grids/Australia/GDA 1994 MGA Zone 56.prj")

    #Saves line for buffer analysis
    arcpy.Project_management(lyr, ProjectedFeat, out_coordinate_system)

    #Save shapefile and delete by columns
    arcpy.CopyFeatures_management(ProjectedFeat,SaveLoc+tbl+"_SegmentedLine.shp") 
    arcpy.DeleteField_management(SaveLoc+tbl+"_SegmentedLine.shp",["F2","F4","F6","F13","F20","LOC_ERROR", "U85dbV","U80dbV","U75dbV","U70dbV","U150mV","U250mV","D85dbV","D80dbV","D75dbV","D70dbV","D150mV","D250mV",])

    #Rewrite any records > 250 to 250
    inputFC = tbl+"_SegmentedLine"   
    colCat1 = "X85"     
    colCat2 = "X80"
    colCat3 = "X75"
    colCat4 = "X70"

    rows = arcpy.UpdateCursor(inputFC)
    for row in rows:
       
        if (row.getValue(colCat1) > 250):
            print row.getValue(colCat1)
            row.setValue(colCat1,250)
            rows.updateRow(row)

        if (row.getValue(colCat2) > 250):
            print row.getValue(colCat2)
            row.setValue(colCat2,250)
            rows.updateRow(row)
            
        if (row.getValue(colCat3) > 250):
            print row.getValue(colCat3)
            row.setValue(colCat3,250)
            rows.updateRow(row)
            
        if (row.getValue(colCat4) > 250):
            print row.getValue(colCat4)
            row.setValue(colCat4,250)
            rows.updateRow(row)

    #Parse Varaiables (Segmented line,Sound category)
    SoundCat1 = "70dbV"
    SoundCat2 = "75dbV"
    SoundCat3 = "80dbV"
    SoundCat4 = "85dbV"
    ClipLimit = "250mV" #Maximum Buffer setting 

    #Generate Contour,Save and Clean
    LayerName = createNoiseContour(ProjectedFeat,SoundCat1,ClipLimit)
    arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl+"_Contour"+SoundCat1+".shp")
    cleanUpLayers()

    LayerName = createNoiseContour(ProjectedFeat,SoundCat2,ClipLimit)
    arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl+"_Contour"+SoundCat2+".shp")
    cleanUpLayers()
                                     
    LayerName = createNoiseContour(ProjectedFeat,SoundCat3,ClipLimit)
    arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl+"_Contour"+SoundCat3+".shp")
    cleanUpLayers()
                                     
    LayerName = createNoiseContour(ProjectedFeat,SoundCat4,ClipLimit)
    arcpy.CopyFeatures_management(LayerName,SaveLoc+tbl+"_Contour"+SoundCat4+".shp")
    cleanUpLayers()
    
    #Copy and Append 
    arcpy.CopyFeatures_management("Contour_70dbV",tbl+"_Contour_MergeResult")
    arcpy.Append_management(["Contour_75dbV","Contour_80dbV","Contour_85dbV"],tbl+"_Contour_MergeResult", "","","")
    arcpy.CopyFeatures_management(tbl+"_Contour_MergeResult",SaveLoc+tbl+"_MergeResults.shp") # ERROR DOEST NOT REWRITE??

print "-------------------------------------------------------------------------------------------"
print "Succusfully Completed"
print "-------------------------------------------------------------------------------------------"
##-------------------------------------------------------------------------------------------
#Adjust side of to buffer on tracks OR
#Determine the outmost track in both directions and apply buffer accordingly.
##-------------------------------------------------------------------------------------------


#LGA Segmentation
#Use the Clip or Intersect analysis process
#






#Write out error messages
    # start try block
    try:

    # If an error occurs when running a tool, print the tool messages
    except arcpy.ExecuteError:
            print arcpy.GetMessages(2)

    #Any other error
    except Exception as e:
        print e.message






       
