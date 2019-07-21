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
# Excel Spreadsheet Noise Buffer format - Prefix,LNRStartValue,LNREndValue,D85dbV,D80dbV,D75dbV,D70dbV,D150mV,D250mV,U85dbV,U80dbV,U75dbV,U70dbV,U150mV,U250mV,BRIDGE_CURVE_TYPE,X85,X80,X75,X70,DATE_STAMP
# Datasets MetrageRoads format - Prefix
# Datasets LGA - LGA Code, LGA Name

#Import arcpy modules
import arcpy, sys, os, re,glob
from arcpy import env

#Remove layers not required
def cleanUpLayers():

    #Clean up - Turn on/off and delete layers
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
    
    for lyr in arcpy.mapping.ListLayers(mxd):
         if lyr.name != "StateWide_MetrageRoads" and lyr.name != "Local_Government_Boundaries_region" and lyr.name != "Contour_70dbV" and lyr.name != "Contour_75dbV" and lyr.name != "Contour_80dbV" and lyr.name != "Contour_85dbV":# Layers to display
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

    #Merge,disolve and remove dougnuts for final sound buffer
    arcpy.Merge_management(["LEFT", "RIGHT"], "MERGE")
    arcpy.Dissolve_management("MERGE","DISSOLVE","", "", "", "")
    arcpy.EliminatePolygonPart_management("DISSOLVE", "Contour_"+SoundCat, "PERCENT", "","90","ANY")
    
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
    SaveLoc = "G:/Geospatial/GIS/JohnW/QRN/CaseStudy1/QLD_Development_Code_Noise_Contours/JW_Workings/20130311/Deliverables/"

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
    arcpy.AddField_management(SaveLoc+tbl+"_SegmentedLine.shp", "LGA_Code", "SHORT",11, "", "", "", "NULLABLE", "REQUIRED")
    arcpy.AddField_management(SaveLoc+tbl+"_SegmentedLine.shp", "LGA_NAME", "TEXT","", "", "60")

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

    #Segment line based on laga  
    tblLGA = "Local_Government_Boundaries_region"
    rows = arcpy.UpdateCursor(tblLGA)

    matchcount = 0
    found  = 0
    for row in rows:
        feat = row.Shape
        #SQL
        arcpy.SelectLayerByLocation_management(inputFC,'INTERSECT',feat)
        #Count
        matchcount = int(arcpy.GetCount_management(inputFC).getOutput(0))
        print matchcount
        if matchcount != 0:
            found += 1  
            print('FOUND!')
            if found == 1:
                arcpy.Clip_analysis(inputFC, feat, 'MergeResultsSegLGA' , '')
            else:
                arcpy.Clip_analysis(inputFC, feat, 'clipToAppend' , '')
                arcpy.Append_management('clipToAppend','MergeResultsSegLGA', "","","")

    #Assign LGA attributes
    arcpy.SpatialJoin_analysis('MergeResultsSegLGA', tblLGA, "MergeResultsSegLGA_Attribute", "#", "#", "#","WITHIN")   
    arcpy.DeleteField_management("MergeResultsSegLGA_Attribute",["NAME","NUMBER0","REGIONNAME","REGIONCODE","REGION_"])
    arcpy.CopyFeatures_management("MergeResultsSegLGA_Attribute",SaveLoc+tbl+"_SegmentedLineLGA.shp") 
            
    #Parse Varaiables (Segmented line,Sound category)-----------------------------------
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
    arcpy.CopyFeatures_management("Contour_85dbV",tbl+"_Contour_MergeResult")
    arcpy.Append_management(["Contour_80dbV","Contour_75dbV","Contour_70dbV"],tbl+"_Contour_MergeResult", "","","")

    #Segment Noise buffer with LGA
    arcpy.MakeFeatureLayer_management(tbl+"_Contour_MergeResult","lyrContour")
    rows = arcpy.SearchCursor('Local_Government_Boundaries_region')  #variable needs to be parsed
    found = 0
    for row in rows:
        feat = row.Shape
        #SQL
        arcpy.SelectLayerByLocation_management("lyrContour",'INTERSECT',feat)
        #Count
        matchcount = int(arcpy.GetCount_management("lyrContour").getOutput(0))
        if matchcount != 0:
            found += 1  
            if found == 1:
                arcpy.Clip_analysis("lyrContour", feat, "MergeResultsSegLGA" , "")
            else:
                arcpy.Clip_analysis("lyrContour", feat, "clipToAppend", "")
                arcpy.Append_management("clipToAppend","MergeResultsSegLGA", "","","")
    
    arcpy.CopyFeatures_management("MergeResultsSegLGA",SaveLoc+tbl+"_MergeResults.shp")

print "-------------------------------------------------------------------------------------------"
print "Succusfully Completed"
print "-------------------------------------------------------------------------------------------"














##-------------------------------------------------------------------------------------------
#Adjust side of to buffer on tracks OR
#Determine the outmost track in both directions and apply buffer accordingly.
##-------------------------------------------------------------------------------------------

#Segment segment line with LGA include attributes 

#*SAMPLE********
    arcpy.Intersect_analysis(["line_offset_split_buf" ], "line_offset_split_buf_intersect" , "")
    arcpy.SpatialJoin_analysis("line_offset_split_buf_intersect"  , "line_offset_points" , "line_offset_split_buf_intersect_sj","JOIN_ONE_TO_ONE" , "KEEP_COMMON" , "" , "INTERSECT")##
    rows = arcpy.UpdateCursor("line_offset_split_buf_intersect_sj")
    for row in rows :
        x = row.getValue("X")
        y = row.getValue("Y")
        polyOuter = arcpy.Array()
        feat = row.Shape
        part = feat.getPart(0)
        for pt in iter(lambda:part.next(),None) : # iter stops on null pt
            polyOuter.append(arcpy.Point( 2*x - pt.X ,2*y - pt.Y) )
        row.setValue("Shape"  , arcpy.Polygon(polyOuter))
        rows.updateRow (row)

    arcpy.Append_management("line_offset_split_buf_intersect_sj","line_offset_split_buf","NO_TEST")
    arcpy.Dissolve_management("line_offset_split_buf", "line_offset_split_buf_disolv", "ID" , "", "SINGLE_PART")## the field is set to not dissolve all polygons
    arcpy.Generalize_edit("line_offset_split_buf_disolv", "0.001")
    arcpy.Select_analysis("line_offset_split_buf_disolv" , layer_out)
#*SAMPLE********

#add column to table
Table2Add = "Copy4"
arcpy.CopyFeatures_management("Main_Line_ML_GIS_SegmentedLine",Table2Add)
arcpy.AddField_management(Table2Add, "LGA_Code", "SHORT",11, "", "", "", "NULLABLE", "REQUIRED")
arcpy.AddField_management(Table2Add, "LGA_NAME", "TEXT","", "", "60")

#Segment line
inputFC = Table2Add   
colCat1 = "LGA_Code"
colCat2 = "LGA_NAME"
rows = arcpy.UpdateCursor('Local_Government_Boundaries_region')

matchcount = 0
found  = 0
for row in rows:
    feat = row.Shape
    #SQL
    arcpy.SelectLayerByLocation_management(Table2Add,'INTERSECT',feat)
    #Count
    matchcount = int(arcpy.GetCount_management(Table2Add).getOutput(0))
    print matchcount
    if matchcount != 0:
        found += 1  
        print('FOUND!')
        if found == 1:
            arcpy.Clip_analysis(Table2Add, feat, 'MergeResultsSegLGA' , '')
            #lgaCode = row.getValue(colCat1)
            #lgaName = row.getValue(colCat2)
            #Object within Polygon join

        else:
            arcpy.Clip_analysis(Table2Add, feat, 'clipToAppend' , '')
            #lgaCode = row.getValue(colCat1)
            #lgaName = row.getValue(colCat2) 
            #Object within Polygon join
            arcpy.Append_management('clipToAppend','MergeResultsSegLGA', "","","")

#Segment Noise buffer with LGA
arcpy.MakeFeatureLayer_management('Main_Line_ML_GIS_MergeResults', 'lyrCleveland_CD_GIS_MergeResults')
rows = arcpy.SearchCursor('Local_Government_Boundaries_region')
found = 0
for row in rows:
    feat = row.Shape
    #SQL
    arcpy.SelectLayerByLocation_management('lyrCleveland_CD_GIS_MergeResults','INTERSECT',feat)
    #Count
    matchcount = int(arcpy.GetCount_management('lyrCleveland_CD_GIS_MergeResults').getOutput(0))
    print matchcount
    if matchcount != 0:
        found += 1  
        print('FOUND!')
        if found == 1:
            arcpy.Clip_analysis('lyrCleveland_CD_GIS_MergeResults', feat, 'MergeResultsSegLGA' , '')
        else:
            arcpy.Clip_analysis('lyrCleveland_CD_GIS_MergeResults', feat, 'clipToAppend' , '')
            arcpy.Append_management('clipToAppend','MergeResultsSegLGA', "","","")
            
    
#Write out error messages
    # start try block
    try:

    # If an error occurs when running a tool, print the tool messages
    except arcpy.ExecuteError:
            print arcpy.GetMessages(2)

    #Any other error
    except Exception as e:
        print e.message

        


#Segment line based on lga  ---> This process is not elegant
colCat1 = "LGA_Code"
colCat2 = "LGA_NAME"
inputFC = "BN_GC_GIS_SegmentedLine"
rows = arcpy.UpdateCursor('Local_Government_Boundaries_region')

matchcount = 0
found  = 0

for row in rows:
    feat = row.Shape
    #SQL
    arcpy.SelectLayerByLocation_management(inputFC,'INTERSECT',feat)
    #Count
    matchcount = int(arcpy.GetCount_management(inputFC).getOutput(0))
    print matchcount
    if matchcount != 0:
        found += 1  
        print('FOUND!')
        if found == 1:
            arcpy.Clip_analysis(inputFC, feat, 'MergeResultsSegLGA' , '')
            #lgaCode = row.getValue(colCat1)
            #lgaName = row.getValue(colCat2)
            #Object within Polygon join
        else:
            arcpy.Clip_analysis(inputFC, feat, 'clipToAppend' , '')
            #lgaCode = row.getValue(colCat1)
            #lgaName = row.getValue(colCat2) 
            #Object within Polygon join
            arcpy.Append_management('clipToAppend','MergeResultsSegLGA', "","","")

#Assign attributes with a join 
target_features = "MergeResultsSegLGA"
join_features = "Local_Government_Boundaries_region"
out_feature_class = "MergeResultsSegLGA_Attribute4"

arcpy.SpatialJoin_analysis(target_features, join_features, out_feature_class, "#", "#", "#","WITHIN")
arcpy.DeleteField_management(out_feature_class,["NAME","NUMBER0","REGIONNAME","REGIONCODE","REGION_"])

