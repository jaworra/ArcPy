##ARCHIVE FUNCTION - Lines to points
## *** Requirement: Shapefile with attribute station 
##Returns: Shape file of points set interval

import math
import arcgisscripting

#returns midpoint coordinate from two points
def midPoint(pt1, pt2):
    return [1,float((pt1[1]+pt2[1])/2),float((pt1[2]+pt2[2])/2)]

#distance between points
def ptDist(pt1, pt2):    return math.sqrt(pow(float(pt2[1])-float(pt1[1]),2) + pow(float(pt2[2])-float(pt1[2]),2))

#returns gradient
def gradent(pt1, pt2):
    m = float((pt2[2]-pt1[2])/(pt2[1]-pt1[1]))
    if m == 0:
        m = 0.9999999
    return m

#returns perpindicular slope                        
def perpid(gradentV):
    return float(-1 /gradentV)

#returns y intercept
def findC(pt1,m):
    return float(pt1[2]-(m*pt1[1]))

#caluculate intesect using slope and y intercept (mx+c=mx+c ==  x =(c2-c1)/(m1-m2) & y = m1*x+c1], returns a coordinate)
def intersect(c1,c2,m1,m2):
    if m1 == m2:
        m1 = m1+0.0000001
    return [1,float((c2-c1)/(m1-m2)),float(m1*(float((c2-c1)/(m1-m2))) + c1)]

#Clear up Memory from CalcGeometryFunction
def cleanUpLayersGeometrySeg():
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]

    for lyr in arcpy.mapping.ListLayers(mxd):
         try:
             if lyr.name == "GEO_AssignRow" or lyr.name == "GEO_SplitPoint" or lyr.name == "GEO_splitline" or lyr.name == "GEO_EventTableFC" or lyr.name == "GEO_LinesToPoint" or lyr.name == "GEO_EventTable" or lyr.name == "GEO_FCView":# Layers to display
                 print lyr.name
                 gp.Delete_management(lyr)
                 gp.Delete_management(gp.Workspace+"\""+lyr.name)
             else:
                 lyr.visible = True
         except arcpy.ExecuteError:
                 print arcpy.GetMessages(2)
    #Delete Tbls
    arcpy.Delete_management(gp.Workspace+"\GEO_EventTable")
    arcpy.Delete_management(gp.Workspace+"\GEO_FCView")
    #Zoom to extents
    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()    
    df.zoomToSelectedFeatures()
    arcpy.RefreshActiveView()
    
def CalcGeometryFunction(InputFeatClass, OuputFeatClass):
    print "Setting Parameters"
    #Set parameters
    inputFC = InputFeatClass 
    outputFC = "GEO_EventTableFC"
    outputTable = "GEO_EventTable"
    FC_View = "GEO_FCView"

    # Fetch each feature from the cursor and examine the extent properties
    print arcpy.Describe(InputFeatClass).MExtent
    MExtent = arcpy.Describe(InputFeatClass).MExtent
    MExtent.split( );
    SpacePos = MExtent.index(" ")
    LengStr = len(MExtent)


    print MExtent[0:SpacePos-1]
    print MExtent[SpacePos+1:LengStr]
    
    #MinM = int(float(MExtent[0:SpacePos-1]))+1
    MinM = int(float(MExtent[0:SpacePos]))+1
    MaxM = int(float(MExtent[SpacePos+1:LengStr]))-1
    print MinM
    
    if MinM == "":
        print "Enters"
        MinM = 1
         
    print MinM
    print MaxM

    print "Creating FCs"
    # create FCs as neccessary
    if not gp.Exists(outputFC):
        gp.FeatureclassToFeatureclass_conversion (inputFC, gp.Workspace, outputFC) 
    if not gp.Exists(outputTable):
        gp.CreateTable (gp.Workspace, outputTable)
    print "adding fields"

    # add fields as neccessary
    gp.AddField_management (outputFC, "NMBR_STATIONS", "LONG")
    gp.AddField_management (outputFC, "STATION", "LONG")

    print "caculating number of stations"
    # calculate the number of stations needed and the position of the last station
    #gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length]/100) - 0.5) + 1")
    #gp.CalculateField_management (outputFC, "STATION", "[Shape_Length] - 1")
    gp.CalculateField_management (outputFC, "NMBR_STATIONS", (int(MaxM-MinM)/100))
    gp.CalculateField_management (outputFC, "STATION", (MaxM-MinM))
    
    print "add more fields"
    # add more fields to the event table...
    gp.AddField_management (outputTable, "STATION", "LONG")
    gp.AddField_management (outputTable, "PREFIX", "Text")
    #gp.AddField_management (outputTable, "ProjectID", "Text")

    print "Make a table of FC"
    # make a table of the FC that contains the position of the last station (STATION) that can later be appended...
    if not gp.Exists(FC_View):
        gp.TableToTable_conversion(outputFC, gp.Workspace, FC_View)

    # start with the cursors...
    # search cursor gets the number of stations needed for each ProjectID (NMBR_STATIONS)
    # insert cursor is for adding new rows to Event Table
    curID = gp.SearchCursor(outputFC)
    rowID = curID.Next()
    rows = gp.InsertCursor(outputTable)

    print "Enter Station"
    while rowID:
        numStations = rowID.NMBR_STATIONS
        projID = rowID.PREFIX
        x = 0
        while x < numStations: # insert a row for each station until X = NumStations.  populate with station location along line.
            row = rows.NewRow()
            row.STATION = x * 100 + MinM #plus 70 here to as the start point 0, gives error.
            row.PREFIX = projID
            rows.InsertRow(row)
            x = x + 1
        rowID = curID.Next() # when x = numStations, go to top of loop and start for next ProjectID.

    print "create points throgh linear M" 
    #rt = outputFC
    rid = "PREFIX"
    tbl = outputTable
    props = "PREFIX POINT STATION"
    lyr = "GEO_LinesToPoint"

    print 'make layer'
    gp.MakeRouteEventLayer_lr(inputFC, rid, tbl, props, lyr, "#",  "ERROR_FIELD")
    inputPts = lyr
    rows = arcpy.SearchCursor(inputPts, '', '', '', 'Station A')

    words = []
    points = []            
    for row in rows:
         #print row.Shape.getPart()
         #write a skip value in here!!
         if row.LOC_ERROR != "ROUTE MEASURE NOT FOUND":
             words = str(row.Shape.getPart()).split()
             #IDXY = map(int,words[3:4])+map(float,words[0:1])+map(float,words[1:2])
             IDXY = map(float,words[3:4])+map(float,words[0:1])+map(float,words[1:2])
             print IDXY
             print "reasigned IDXY"
             IDXY2 = words[3],words[0],words[1]
             print IDXY2
             #Assign values base on list memebers e.g words[3]
             points.append(IDXY)
         else:
             print "Error Found!!"
             
    ################################################################################################
    #Straights Curve Cacls
    ################################################################################################START HERE!!!!!!!!!!
    #Output list.......
    #Update Moving window from step 3 to step 1
    print "Straights and Curves Calcuation"
    stepList = 3
    couterList = 1
    raidusTight = 300
    raidusLimit = 500
    print points
    try:        
        for p in range(0,len(points)):
            print "s"
            print p
            print len(points)
            print p*stepList
            if p*stepList +3 < len(points):
                print "Set Geo"
                couterList = p*stepList
                midpoint1 = midPoint(points[couterList], points[couterList+1])
                midpoint2 = midPoint(points[couterList+2], points[couterList+3])
                m1 = perpid(gradent(points[couterList], points[couterList+1]))
                m2 = perpid(gradent(points[couterList+2], points[couterList+3]))       
                c1 = findC(midpoint1,m1)
                c2 = findC(midpoint2,m2)
                
                #Assiging geometry
                if((ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusTight)): #Radius: 0 to raidusTight(i.e 0-300)
                    print "1"
                    points[couterList][3:5] = ["Curve",300] 
                    points[couterList+1][3:5] = ["Curve",300] 
                    points[couterList+2][3:5] = ["Curve",300] 
                    points[couterList+3][3:5] = ["Curve",300] 
                    
                elif(ptDist(intersect(c1,c2,m1,m2), points[couterList]) > raidusTight and ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusLimit ): #Radius: raidusTight to raidusLimit (i.e 300-500)
                    print "2"
                    if ((points[couterList][3:4] == ["Straight"]) or (points[couterList][3:4] == [])): # assign variable only if
                        print "2A"
                        points[couterList][3:5] = ["Curve",500]
                    print "2B"
                    points[couterList+1][3:5] = ["Curve",500]
                    points[couterList+2][3:5] = ["Curve",500]
                    points[couterList+3][3:5] = ["Curve",500]
                    
                else: #Straight
                    print "3"
                    if ((points[couterList][3:4] == []) or (points[couterList][3:4] == ["Straight"])):
                        points[couterList][3:5] = ["Straight",0]
                        print "3A"
                    points[couterList+1][3:5] = ["Straight",0]
                    print "3B"
                    points[couterList+2][3:5] = ["Straight",0]
                    points[couterList+3][3:5] = ["Straight",0]
            else:
                print "break"
                break
        
    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)
        cleanUpLayersGeometrySeg()    

    CutPoint = []
    AttributeAssign = []
    #Output only start/end points list
    Sortedpoints = []
    couterList = 0
    print "Sp Points"
    for Sp in points:
        print Sp
        print len(points)
        if couterList == 0:
            prevPoint = Sp
            couterList = 1
            print "a"
            
        else:
            #if Sp[3:5] != "":
            #if prevPoint[3:5] != Sp[3:5] and Sp[3:5] != "" and prevPoint[3:5] != "" and Sp[3:5] != "":
            if prevPoint[3:5] != Sp[3:5] and len(Sp) > 3:
                print "assign"
                print len(Sp)
                print "length"
                CutPoint.append(Sp)
                AttributeAssign.append(prevPoint)#Create a list of points always before the intersection points
                prevPoint = Sp
            else:
                prevPoint = Sp
                print "assing2"
                
    AttributeAssign.append(points[-3]) #Third last point #Second Last point #Last point # HERE PROBLEM ** TAKE OUT THOSU.
    #Delete last point in cutPoints if coordinates are the same
    print "CHECK NOW"
    #print CutPoint[-1]
    #print points[-1]
    
##    if CutPoint[-1] == points[-1]:
##        del CutPoint[-1] #make sure the last cut point isn't the same as last line to points
##    print CutPoint[-1]
##
##    #Debug
##    if CutPoint[-2] == points[-2]:
##        del CutPoint[-2] #make sure the last cut point isn't the same as last line to points


    #print "Last Point"
    #print AttributeAssign
                
    print "Cut Points"
    print "cut points length"
    print len(CutPoint)
    #Only apply if there are more than one Cutpoints saved
    if len(CutPoint) > 0:
        point = arcpy.Point() # Create an empty Point object
        pointGeometryList = [] # A list to hold the PointGeometry objects

        for Xp in CutPoint: #Put a range statement in here!! -3???
            print "cutpoint1"
            point.X = Xp[1]
            point.Y = Xp[2]
            pointGeometry = arcpy.PointGeometry(point)
            pointGeometryList.append(pointGeometry)
            
        print 'Get here'
        SplitPoint = "GEO_SplitPoint"    
        #Create points for split line    
        arcpy.CopyFeatures_management(pointGeometryList,SplitPoint)

        SplitLine="GEO_splitline"
        searchRadius= "20 Meters"
        arcpy.SplitLineAtPoint_management(inputFC, SplitPoint, SplitLine, searchRadius)
    else:#No cut points 
        SplitLine="GEO_splitline"
        arcpy.CopyFeatures_management(inputFC,SplitLine)
        #arcpy.AddField_management(SplitLine, "Geometry", "Text")
        #arcpy.AddField_management(SplitLine, "Radius", "LONG")

    print "Assigned Points"
    point2 = arcpy.Point() # Create an empty Point object
    pointGeometryList2 = [] # A list to hold the PointGeometry objects

    for FP in AttributeAssign: 
        point2.X = FP[1]
        point2.Y = FP[2]
        pointGeometry2 = arcpy.PointGeometry(point2)
        pointGeometryList2.append(pointGeometry2)

    print "Saved Assigned Points"
    AssingRow= "GEO_AssignRow"    
    #Create points for split line    
    arcpy.CopyFeatures_management(pointGeometryList2, "C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb/"+AssingRow)
    arcpy.AddField_management(AssingRow, "Geometry", "Text")
    arcpy.AddField_management(AssingRow, "Radius", "LONG")

    #Points Assigne attributes
    ListCounter = 0 
    Rows = arcpy.UpdateCursor(AssingRow) 
    for row in Rows:
        row.Geometry = AttributeAssign[ListCounter][3]
        row.Radius = AttributeAssign[ListCounter][4]
        Rows.updateRow(row)
        ListCounter += 1
        
    print "update attributes on splitline"
    #New Shapefile Created with Geomtery Attributes
    gp.SpatialJoin("GEO_splitline","GEO_AssignRow", OuputFeatClass, "#", "#","#","INTERSECT")
    print "Assign Attributes"

def createNoiseContour(SegmenetedLine, NoiseBuffer): #Future reference parse categories Straight, curve etch



    #SegmenetedLine ="SegmentedGeoLine"
    #Straights
    where_clause = '"Geometry" = '+"'Straight'"
    arcpy.Select_analysis(SegmenetedLine , "STRAIGHTS", where_clause)

    #Curves 500
    where_clause = '"Geometry" = '+"'Curve'"+' AND "Radius" = 500'
    arcpy.Select_analysis(SegmenetedLine , "CURVE500", where_clause)

    #Curves 300
    where_clause = '"Geometry" = '+"'Curve'"+' AND "Radius" = 300'
    arcpy.Select_analysis(SegmenetedLine , "CURVE300", where_clause)

    #Straight
    arcpy.Buffer_analysis("STRAIGHTS", "Str85",42,"", "", "",)
    arcpy.Buffer_analysis("STRAIGHTS", "Str80",77,"", "", "",)
    arcpy.Buffer_analysis("STRAIGHTS", "Str75",219,"", "", "",)
    arcpy.Buffer_analysis("STRAIGHTS", "Str70",547,"", "", "",)

    #Curve 300-500
    arcpy.Buffer_analysis("CURVE500", "Cur585",50,"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur580",77,"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur575",210,"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur570",547,"", "", "",)

    #Curve 0-300
    arcpy.Buffer_analysis("CURVE300", "Cur385",146,"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur380",388,"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur375",871,"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur370",1708,"", "", "",)

    #Dissolve and merge
    arcpy.Merge_management(["Str85", "Cur585","Cur385"], "MERGE85")
    arcpy.Dissolve_management("MERGE85","X85","", "", "", "")
    arcpy.Merge_management(["Str80", "Cur580","Cur380"], "MERGE80")
    arcpy.Dissolve_management("MERGE80","X80","", "", "", "")
    arcpy.Merge_management(["Str75", "Cur575","Cur375"], "MERGE75")
    arcpy.Dissolve_management("MERGE75","X75","", "", "", "")
    arcpy.Merge_management(["Str70", "Cur570","Cur370"], "MERGE70")
    arcpy.Dissolve_management("MERGE70","X70","", "", "", "")

    #Clip Limti to put in here!!!
    #arcpy.Clip_analysis(ActualNoiseBuffer, MaxNoiseBuffer, AnalysisSide, xy_tolerance)
    
    #Append
    arcpy.Merge_management(["X85", "X80","X75","X70"], NoiseBuffer)

    SegmenetedLine = "SegmentedGeoLine"
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
    
    print "Clearing Memory....."
    for lyr in arcpy.mapping.ListLayers(mxd):
         try:
             #if lyr.name != NoiseBuffer and lyr.name != "X85" and lyr.name != "X80" and lyr.name != "X75" and lyr.name != "X70" and lyr.name != SegmenetedLine:# Layers to display
             if lyr.name != NoiseBuffer and lyr.name != SegmenetedLine:# Layers to display
                 print lyr.name
                 gp.Delete_management(lyr)
                 gp.Delete_management(gp.Workspace+"\""+lyr.name)
             else:
                 lyr.visible = True
         except arcpy.ExecuteError:
                 print arcpy.GetMessages(2)

    #Zoom to extents
    arcpy.RefreshTOC()
    arcpy.RefreshActiveView()    
    df.zoomToSelectedFeatures()
    arcpy.RefreshActiveView()

    

print('''Programmer:
  John Worrall

Version:
  1.0

Last Update:
   18/04/2013
       
  Batch spliting polylines enter interval
  
  NOTE:.
  
''')

# if digitising error occurs, ensure min distance appx 50m
#Create point of line

import sys, arcgisscripting, string, os
arcpy.env.overwriteOutput = True

gp = arcgisscripting.create(9.3)
gp.Workspace = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb" # remove this gdb
gp.OverWriteOutput = 1

#RailDataset = "3SAMPLE_StateWide_MetrageRoads_MGA56" #SUCCESS ML LINE
RailDataset = "SEQ"#"3SAMPLE_StateWide_MetrageRoads_MGA56" #"SAMPLE_StateWide_MetrageRoads_MGA56"#"SEQ"#"StateWide_MetrageRoads_MGA56"

OuputFeatClass = "ProcessedLine"

searchCursor = arcpy.SearchCursor(RailDataset)
row = searchCursor.next()

ProcessedTbl = 0
#SegTbl = .shp"
#SegTbl = OuputFeatClass

for i in range(int(arcpy.GetCount_management(RailDataset).getOutput(0))):    
    RailLine = row.PREFIX
    out_feature_class = os.path.join(gp.Workspace, RailLine)
    where_clause = '"FID"='+str(i)#where_clause = '"OBJECTID"='+str(i+1)
    arcpy.Select_analysis(RailDataset , out_feature_class, where_clause)
    row = searchCursor.next()

    OuputFeatClass = "C:\SegmentedGeoLine_"+RailLine+".shp"

    try:
        CalcGeometryFunction(RailLine,OuputFeatClass)
        cleanUpLayersGeometrySeg()
        arcpy.Delete_management(RailLine)
        arcpy.Delete_management(gp.Workspace+"\""+RailLine)

    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)


    
    #Calls #sys.exit(0) # Bug fix saving layer empty 
    try:
        CalcGeometryFunction(RailLine,OuputFeatClass)
        #cleanUpLayersGeometrySeg()
        ProcessedTbl += 1
        print "Entry"
    
        #Add process table to final
        if ProcessedTbl == 1:
            arcpy.CopyFeatures_management(OuputFeatClass,SegTbl)
            #LEAVE THIS???? #arcpy.Delete_management(OuputFeatClass)
            #arcpy.Delete_management(gp.Workspace+"\""+OuputFeatClass)
            
            print "First"
        else:
            arcpy.Append_management(OuputFeatClass,SegTbl, "TEST","","")
            print "Second"
        
    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)
        #cleanUpLayersGeometrySeg()
        
    #arcpy.Delete_management(RailLine)
    #arcpy.Delete_management(gp.Workspace+"\""+RailLine)

    #================================================
    #Buffer Function
    BufTbl = RailLine+"_NoiseBuffer"#"ML_NoiseBuffer"
    createNoiseContour(SegTbl,BufTbl)
    #================================================

 
#Send data table for buffer per attribute
#    sys.exit(0)
#=============================================================================================================================================================
print "Successfully Completed!!"
#=============================================================================================================================================================
#BUG FIXES 24/05/2013
# *Change assigne float to int for list points 
# *List Limit found where last point split and assignm values.


