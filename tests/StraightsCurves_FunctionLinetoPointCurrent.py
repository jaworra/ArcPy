##ARCHIVE FUNCTION - Lines to points
## *** Requirement: Shapefile with attribute station 
##Returns: Shape file of points set interval

import math
import arcgisscripting
import gc

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

#returns y interceptv
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
    inputFC = InputFeatClass 
    outputFC = "GEO_EventTableFC"
    outputTable = "GEO_EventTable"
    FC_View = "GEO_FCView"
    distBetPoints = 100

    # Fetch each feature from the cursor and examine the extent properties
    print arcpy.Describe(InputFeatClass).MExtent
    MExtent = arcpy.Describe(InputFeatClass).MExtent
    print MExtent
    
    for row in arcpy.SearchCursor (InputFeatClass):
        feature = row.shape
        MaxM = int(feature.length)-1
        MinM = 1
        lineLen = int(feature.length)

    #Length of parse line is smaller than 4 points dist
    if (lineLen < 4 * distBetPoints):
        #Copy input to output
        arcpy.CopyFeatures_management(InputFeatClass,OuputFeatClass)
        arcpy.AddField_management(OuputFeatClass, "Geometry", "Text") 
        arcpy.AddField_management(OuputFeatClass, "Radius", "LONG")
        #Update records
        Rows =  arcpy.UpdateCursor(OuputFeatClass) 
        for row in Rows:
            row.setValue("Geometry","Straight")
            row.setValue("Radius",0)
            Rows.updateRow(row) 
        return

    if MExtent.find('QNAN')== -1: #Has MVALUE -ITS A NUMBER!"
        MExtent.split( );
        SpacePos = MExtent.index(" ")
        LengStr = len(MExtent)
        print MExtent[0:SpacePos]
        print MExtent[SpacePos+1:LengStr]

        #MinM = int(float(MExtent[0:SpacePos-1]))+1
        MinM = int(float(MExtent[0:SpacePos]))+1
        MaxM = int(float(MExtent[SpacePos+1:LengStr]))-1
            
        if MinM == "": #Start Value x+1
            MinM = 1
            
        if MaxM < 500:
            print "Less than 500"
            print MaxM 
            return # instea of return here
        else:
            print "greaterthan 500"
            print MaxM    
     
    if MExtent.find('QNAN')!= -1: #No MVALUE - use shape distace"
        print "NOT A NUMBER - No MVALUE"
        # Create Route from polyline
        arcpy.CreateRoutes_lr(InputFeatClass,"OBJECTID",InputFeatClass+"_HasM","LENGTH","#","#","UPPER_LEFT","1","0","IGNORE","INDEX")
        newPrefix = InputFeatClass
        inputFC = InputFeatClass+"_HasM"       
        
        arcpy.AddField_management (inputFC,"PREFIX","Text")       
    ##arcpy.AddField_management (InputFeatClass,"CATEGORY","Text")
        Rows = arcpy.UpdateCursor(inputFC)
        for row in Rows:
            row.PREFIX = newPrefix
            Rows.updateRow(row)
                       
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
    gp.CalculateField_management (outputFC, "NMBR_STATIONS", (int(MaxM-MinM)/distBetPoints))
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
            row.STATION = x * distBetPoints + MinM #plus 70 here to as the start point 0, gives error.
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
             IDXY = map(float,words[3:4])+map(float,words[0:1])+map(float,words[1:2])
             IDXY2 = words[3],words[0],words[1]
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
    try:        
        for p in range(0,len(points)):
            if p*stepList +3 < len(points):
                couterList = p*stepList
                midpoint1 = midPoint(points[couterList], points[couterList+1])
                midpoint2 = midPoint(points[couterList+2], points[couterList+3])
                m1 = perpid(gradent(points[couterList], points[couterList+1]))
                m2 = perpid(gradent(points[couterList+2], points[couterList+3]))       
                c1 = findC(midpoint1,m1)
                c2 = findC(midpoint2,m2)
                
                #Assiging geometry
                if((ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusTight)): #Radius: 0 to raidusTight(i.e 0-300)
                    points[couterList][3:5] = ["Curve",300] 
                    points[couterList+1][3:5] = ["Curve",300] 
                    points[couterList+2][3:5] = ["Curve",300] 
                    points[couterList+3][3:5] = ["Curve",300] 
                    
                elif(ptDist(intersect(c1,c2,m1,m2), points[couterList]) > raidusTight and ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusLimit ): #Radius: raidusTight to raidusLimit (i.e 300-500)
                    if ((points[couterList][3:4] == ["Straight"]) or (points[couterList][3:4] == [])): # assign variable only if
                        points[couterList][3:5] = ["Curve",500]
                    points[couterList+1][3:5] = ["Curve",500]
                    points[couterList+2][3:5] = ["Curve",500]
                    points[couterList+3][3:5] = ["Curve",500]
                    
                else: #Straight
                    if ((points[couterList][3:4] == []) or (points[couterList][3:4] == ["Straight"])):
                        points[couterList][3:5] = ["Straight",0]
                    points[couterList+1][3:5] = ["Straight",0]
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
        if couterList == 0:
            prevPoint = Sp
            couterList = 1
            
        else:
            #if Sp[3:5] != "":
            #if prevPoint[3:5] != Sp[3:5] and Sp[3:5] != "" and prevPoint[3:5] != "" and Sp[3:5] != "":
            if prevPoint[3:5] != Sp[3:5] and len(Sp) > 3:
                CutPoint.append(Sp)
                AttributeAssign.append(prevPoint)#Create a list of points always before the intersection points
                prevPoint = Sp
            else:
                prevPoint = Sp
                
    AttributeAssign.append(points[-3]) #Third last point #Second Last point #Last point # HERE PROBLEM ** TAKE OUT THOSU.
    #Delete last point in cutPoints if coordinates are the same
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
    #Only apply if there are more than one Cutpoints saved
    if len(CutPoint) > 0:
        point = arcpy.Point() # Create an empty Point object
        pointGeometryList = [] # A list to hold the PointGeometry objects

        for Xp in CutPoint: #Put a range statement in here!! -3???
            point.X = Xp[1]
            point.Y = Xp[2]
            pointGeometry = arcpy.PointGeometry(point)
            pointGeometryList.append(pointGeometry)
            
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
    arcpy.AddField_management(AssingRow, "Geometry", "Text") #Take this out.....
    arcpy.AddField_management(AssingRow, "Radius", "LONG") #Take this out.......

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
    #gp.SpatialJoin("GEO_splitline","GEO_AssignRow", OuputFeatClass, "#", "#","#","INTERSECT")
    gp.SpatialJoin("GEO_splitline","GEO_AssignRow",OuputFeatClass, "#", "#","#","CLOSEST")
    print "Assign Attributes"
    
    points[:] = []
    words[:] = []
    AttributeAssign[:] = []
    CutPoint[:] = []
    Sortedpoints[:] = []
    #pointGeometryList[:] = [] 
    #pointGeometryList2[:] = []

def createNoiseContour(SegmenetedLine, NoiseBuffer,RailLine,RailDataset): #Future reference parse categories Straight, curve etch
    test = True
    #Truncation passenger= 150 freight =250
    #Defualt distance 20m on bridges = 10m radius
    #Assign Noise buffer criteria
    if RailLine == 'NC' or RailLine == "HM" or RailLine == "PA" or RailLine == "FS" or RailLine == "ML" or RailLine == "AR" or RailLine == "BN_F" or RailLine == 'CY' or RailLine == "CD_F" or RailLine == "NS" or RailLine == "BF" or RailLine == "IW" or RailLine == "EZ":
        bufferMax = 250 #FREIGHT

        Str85=42
        Str80=77
        Str75=219
        Str70=547

        Cur585=25+Str85
        Cur580=69+Str80
        Cur575=169+Str75
        Cur570=324+Str70
        
        Cur385=121+Str85
        Cur380=311+Str80
        Cur375=652+Str75
        Cur370=1161+Str70
        
        structWood85=52
        structWood80=142 
        structWood75=328
        structWood70=607

        structSteel85=154
        structSteel80=385
        structSteel75=786
        structSteel70=1389

        structConcret85=7
        structConcret80=18
        structConcret75=48
        structConcret70=96

        structLvlX85=52
        structLvlX80=142
        structLvlX75=328
        structLvlX70=607

    elif RailLine == 'AT':
        bufferMax = 150

        Str85=6
        Str80=10
        Str75=17
        Str70=30

        Cur585=6
        Cur580=10
        Cur575=17
        Cur570=30
        
        Cur385=6
        Cur380=10
        Cur375=17
        Cur370=30
        
        structWood85=6
        structWood80=10 
        structWood75=17
        structWood70=30

        structSteel85=6
        structSteel80=10
        structSteel75=17
        structSteel70=30
        
        structConcret85=6
        structConcret80=10
        structConcret75=17
        structConcret70=30

        structLvlX85=6
        structLvlX80=10
        structLvlX75=17
        structLvlX70=30
        
    else: #PASSENGER
        bufferMax = 150
        Str85=30
        Str80=66
        Str75=130
        Str70=236
        
        Cur585=19+Str85
        Cur580=34+Str80
        Cur575=57+Str75
        Cur570=100+Str70
        
        Cur385=70+Str85
        Cur380=120+Str80
        Cur375=207+Str75
        Cur370=364+Str70
        
        structWood85=36
        structWood80=63
        structWood75=107
        structWood70=188
        
        structSteel85=84
        structSteel80=144
        structSteel75=249
        structSteel70=438
        
        structConcret85=6
        structConcret80=10
        structConcret75=17
        structConcret70=30
        
        structLvlX85=36
        structLvlX80=63
        structLvlX75=107
        structLvlX70=188
        
    structTermYard85=308
    structTermYard80=343
    structTermYard75=291
    structTermYard70=278

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
    arcpy.Buffer_analysis("STRAIGHTS", "Str85",min(Str85,bufferMax),"", "", "",) 
    arcpy.Buffer_analysis("STRAIGHTS", "Str80",min(Str80,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("STRAIGHTS", "Str75",min(Str75,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("STRAIGHTS", "Str70",min(Str70,bufferMax),"", "", "",)

    #Curve 300-500
    arcpy.Buffer_analysis("CURVE500", "Cur585",min(Cur585,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur580",min(Cur580,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur575",min(Cur575,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE500", "Cur570",min(Cur570,bufferMax),"", "", "",)
    
    #Curve 300
    arcpy.Buffer_analysis("CURVE300", "Cur385",min(Cur385,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur380",min(Cur380,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur375",min(Cur375,bufferMax),"", "", "",)
    arcpy.Buffer_analysis("CURVE300", "Cur370",min(Cur370,bufferMax),"", "", "",)

    #Dissolve and merge
    arcpy.Merge_management(["Str85", "Cur585","Cur385"], "MERGE85")
    arcpy.Dissolve_management("MERGE85","X85","", "", "", "") 

    arcpy.Merge_management(["Str80", "Cur580","Cur380"], "MERGE80")
    arcpy.Dissolve_management("MERGE80","X80","", "", "", "")
        
    arcpy.Merge_management(["Str75", "Cur575","Cur375"], "MERGE75")
    arcpy.Dissolve_management("MERGE75","X75","", "", "", "")
    
    arcpy.Merge_management(["Str70", "Cur570","Cur370"], "MERGE70")
    arcpy.Dissolve_management("MERGE70","X70","", "", "", "")

    #Append
    arcpy.Merge_management(["X85","X80","X75","X70"], NoiseBuffer)
    arcpy.AddField_management (NoiseBuffer,"PREFIX","Text")
    arcpy.AddField_management (NoiseBuffer,"CATEGORY","Text")

    Rows = arcpy.UpdateCursor(NoiseBuffer)
    rowcount=1
    for row in Rows:
        row.PREFIX = RailLine
        if rowcount ==1:
            row.CATEGORY = "X85"
        if rowcount ==2:
            row.CATEGORY = "X80"
        if rowcount ==3:
            row.CATEGORY = "X75"
        if rowcount ==4:
            row.CATEGORY = "X70"
        Rows.updateRow(row)
        rowcount += 1

    #OuputFeatClass = "C:\SegmentedGeoLine_"+RailLine+str(rowCount)+".shp"
    #Deep Copy final Product
    #OuputFeatClass = "C:\\"+RailLine+str(rowCount)+".shp"
    BufferOutputHD = "C:\\"+NoiseBuffer+".shp"
    #arcpy.CopyFeatures_management(NoiseBuffer,"C:\""+NoiseBuffer)+".shp")
    arcpy.CopyFeatures_management(NoiseBuffer,BufferOutputHD)
    
    #sys.exit(0) #HERE
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
    print "Clearing Memory....."
    
    for lyr in arcpy.mapping.ListLayers(mxd):
         try:
             #if lyr.name != NoiseBuffer and lyr.name != "X85" and lyr.name != "X80" and lyr.name != "X75" and lyr.name != "X70" and lyr.name != SegmenetedLine:# Layers to display
             if lyr.name != NoiseBuffer and lyr.name != SegmenetedLine and lyr.name != RailDataset:# Layers to display
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

#if digitising error occurs, ensure min distance appx 50m
#Create point of line

import sys, arcgisscripting, string, os
arcpy.env.overwriteOutput = True
arcpy.env.scratchWorkspace = "C:/TEMP/scratchoutput.gdb"

gp = arcgisscripting.create(9.3)
gp.Workspace = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb" # remove this gdb
gp.OverWriteOutput = 1

#RailDataset = "SortedByLength_SEQ"
#RailDataset = "StateWide_MetrageRoads_MGA56_SEQ"
RailDataset = "SR_NC"
OuputFeatClass = "ProcessedLine"

searchCursor = arcpy.SearchCursor(RailDataset)
row = searchCursor.next()
ProcessedTbl = 0
rowCount = 1

for i in range(int(arcpy.GetCount_management(RailDataset).getOutput(0))):    
    RailLine = row.PREFIX
    out_feature_class = os.path.join(gp.Workspace, RailLine)
    where_clause = '"FID"='+str(i)
    #where_clause = '"OBJECTID_1"='+str(i+1)
    arcpy.Select_analysis(RailDataset , out_feature_class, where_clause)
    row = searchCursor.next()

    #OuputFeatClass = "C:\SegmentedGeoLine_"+RailLine+str(rowCount)+".shp"
    OuputFeatClass = "C:\\"+RailLine+"_"+str(rowCount)+"_SegmentedGeoLine.shp"
    #BufTbl = RailLine+str(rowCount)+"_NoiseBuffer"
    BufTbl = RailLine+"_"+str(rowCount)+"_NoiseBuffer"
    rowCount += 1
    exit 
    
    try:
        CalcGeometryFunction(RailLine,OuputFeatClass)
        #createNoiseContour(OuputFeatClass,BufTbl,RailLine,RailDataset)
        cleanUpLayersGeometrySeg()
        arcpy.Delete_management(RailLine)
        arcpy.Delete_management(gp.Workspace+"\""+RailLine)
            
    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)

    gc.collect()
#=============================================================================================================================================================
print "Successfully Completed!!"
#=============================================================================================================================================================
#BUG FIXES 24/05/2013

# *Change assigne float to int for list points 
# *List Limit found where last point split and assignm values.

#arcpy.Sort_management("SEQ_RAIL_MAY_2013", "SEQ_RAIL_MAY_2013_DEShpLength", [["SHAPE_len", "DESCENDING"]])
#arcpy.Sort_management("SEQ_RAIL_MAY_2013_DesShpLength", "NEW_SEQ_RAIL", [["Shape_Leng", "DESCENDING"]])

##InputTable = "SEQ_RAIL_MAY_2013"
##OutTable= "SortedByLength_SEQ"
##ColLength = "New_Length"
##
##arcpy.AddField_management(InputTable, "New_Length", "LONG") 

##length = 0
##rows = arcpy.UpdateCursor (InputTable)
##for row in rows:
##    feature = row.shape
##    length = feature.length
##    #print length
##    row.setValue(ColLength, length)
##    rows.updateRow(row)
##    
##arcpy.Sort_management(InputTable, OutTable, [[ColLength, "DESCENDING"]]) 

