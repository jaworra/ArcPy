

print('''Programmer:
  John Worrall

Version:
  1.0

Last Update:
   18/04/2013
       
  Batch spliting polylines enter interval
  
  NOTE:.
  
''')

# if digitising error occurs, ensure min distance apxp 50m
#Create point of line

import sys, arcgisscripting, string, os
arcpy.env.overwriteOutput = True

gp = arcgisscripting.create(9.3)
gp.Workspace = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb"
gp.OverWriteOutput = 1


print "Setting Parameters"
# set parameters
#inputFC = "StateWide_MetrageRoads_MGA56"
inputFC = "SAMPLE_StateWide_MetrageRoads_MGA56"
outputFC = "EventTableFC"
outputTable = "EventTable"
FC_View = "FCView"

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
gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length] /100) - 0.5) + 1")
gp.CalculateField_management (outputFC, "STATION", "[Shape_Length] - 1")

#gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length] * 100000 /100) - 0.5) + 1")
#gp.CalculateField_management (outputFC, "STATION", "[Shape_Length] * 100000- 1")

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
    #projID = rowID.ProjectID
    projID = rowID.PREFIX
    print numStations
    print projID
    print "a"
    x = 0
    while x+1 < numStations: # insert a row for each station until X = NumStations.  populate with station location along line.
        print "B"
        row = rows.NewRow()
        print "b"
        #row.STATION = x * 100 #for intervals of 10 = change 100 to 10
        row.STATION = x * 100 + 70 # 101 intervals
        print "CC"
        #row.ProjectID = projID
        row.PREFIX = projID
        print "DD"
        rows.InsertRow(row)
        x = x + 1
        print "c"
    rowID = curID.Next() # when x = numStations, go to top of loop and start for next ProjectID.


print "create points throgh linear M" 
rt = outputFC
rid = "Prefix" 
tbl = outputTable
props = "PREFIX POINT STATION"
lyr = "SegPointEvents"
arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")



#HERE - >NEED TO SAVE MAKEROUTE LAYER TO HARD DRIVE AND OPEN
##
##  Error change route points created to shp/lyr file with actual spatial
##  geometry values. 
##
##  ->

## ++++++++++++REMOVE+++++++++++++++++++++++++++++++++++++++++
import math

#midpoint of two coordinates
def midPoint(pt1, pt2):
    x = (pt1[1]+pt2[1])/2
    y = (pt1[2]+pt2[2])/2
    return [1,x,y]

#distance between points on horizontal plane
def ptDist(pt1, pt2):
    return math.sqrt(pow(float(pt2[1])-float(pt1[1]),2) + pow(float(pt2[2])-float(pt1[2]),2))

#gradient of two points - > m
def gradent(pt1, pt2):
    m = float((pt2[2]-pt1[2])/(pt2[1]-pt1[1]))
    if m == 0:
        m = 0.999999
    return m
                        
def perpid(gradentV):
    return float(-1 /gradentV)

def findC(pt1,m):
    return float(pt1[2]-(m*pt1[1]))

def intersect(c1,c2,m1,m2):
    #x = (c2 - c1) / (m1 - m2)
    #y = m1 * x + c1
    return [1,float((c2-c1)/(m1-m2)),float(m1*(float((c2-c1)/(m1-m2))) + c1)]

## ++++++++++++REMOVE+++++++++++++++++++++++++++++++++++++++++

sortTbl = "YYdelete"
sortCol = "STATION"
#Sort rows
lyr = "Export_Output_4"
arcpy.Sort_management(lyr, sortTbl, [[sortCol, "ASCENDING"]])

infc = sortTbl
points = []
pointNo = 0

# Create the geoprocessor object
gp = arcgisscripting.create(9.3)

# Identify the geometry field
desc = gp.Describe(infc)
shapefieldname = desc.ShapeFieldName

# Create search cursor
rows = gp.SearchCursor(infc)
row = rows.Next()

# radius set as a global varaible or parsed
raidusLimit = 500
raidusTight = 300
# Enter while loop for each feature/row
while row:
    # Create the geometry object 'feat'
    feat = row.GetValue(shapefieldname)
    pnt = feat.GetPart() 
    
    # Print x,y coordinates of current point
    IDXY = [row.getValue("STATION"),pnt.x, pnt.y ]

    points.append(IDXY)
    row = rows.Next()

#Output list.......  
stepList = 3
couterList = 1
for p in range(0,len(points)):
    if p*stepList +3 <= len(points):
        couterList = p*stepList
        midpoint1 = midPoint(points[couterList], points[couterList+1])
        midpoint2 = midPoint(points[couterList+2], points[couterList+3])
        m1 = perpid(gradent(points[couterList], points[couterList+1]))
        m2 = perpid(gradent(points[couterList+2], points[couterList+3]))       
        c1 = findC(midpoint1,m1)
        c2 = findC(midpoint2,m2)
        
        #Assiging geometry
        if((ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusTight)): #Radius: 0 - 300
            points[couterList][3:5] = ["Curve",300] 
            points[couterList+1][3:5] = ["Curve",300] 
            points[couterList+2][3:5] = ["Curve",300] 
            points[couterList+3][3:5] = ["Curve",300] 
            
        elif(ptDist(intersect(c1,c2,m1,m2), points[couterList]) > raidusTight and ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusLimit ): #Radius: 301 - 500
            if ((points[couterList][3:4] == ["straight"]) or (points[couterList][3:4] == [])): # assign variable only if
                points[couterList][3:5] = ["Curve",500]
            points[couterList+1][3:5] = ["Curve",500]
            points[couterList+2][3:5] = ["Curve",500]
            points[couterList+3][3:5] = ["Curve",500]
        else: #Straight
            if ((points[couterList][3:4] == []) or (points[couterList][3:4] == ["straight"])):
                points[couterList][3:5] = ["straight",0]
            points[couterList+1][3:5] = ["straight",0]
            points[couterList+2][3:5] = ["straight",0]
            points[couterList+3][3:5] = ["straight",0]
        print points[couterList]#[3:5]
        print points[couterList+1]#[3:5]
        print points[couterList+2]#[3:5]
        print points[couterList+3]#[3:5]    
    else:
        break



# Required to set list for points
[station, x, y, curve/straight, radius]
# Split line by points
##        print points[couterList]
##        print points[couterList+1]
##        print points[couterList+2]
##        print points[couterList+3]
##        print "------------------"
##        print ptDist(points[couterList], points[couterList+1])
##        print midPoint(points[couterList], points[couterList+1]) 
##        print gradent(points[couterList], points[couterList+1])
##        print perpid(gradent(points[couterList], points[couterList+1]))
##        print "------------------"
##        #Perpendicular slope
##        #oringal slope
##        #m1 = gradent(points[couterList], points[couterList+1])
##        #m2 = gradent(points[couterList+2], points[couterList+3])
##        #y intercept      
##        c1 = findC(points[couterList],m1)
##        c2 = findC(points[couterList+2],m1)
##        #Debug
##        print "m1: "+str(m1)+"    m2: "+str(m2)+"    c1: "+str(c1)+"    c2: "+str(c2)
##        print "------------------"
##        print str(intersect(c1,c2,m1,m2)) + " - intersection of two perpindicular lines"
##        print str(ptDist(intersect(c1,c2,m1,m2), points[couterList]))+ " - distance between two points (RADIUS)"
##        print "------------------"
##            print str(ptDist(intersect(c1,c2,m1,m2), points[couterList]))+","+str(intersect(c1,c2,m1,m2))           
##            print "------------------"
##            print str(ptDist(intersect(c1,c2,m1,m2), points[couterList]))+ " Curve"

##            print "------------------"           
##        
        #function of a line y = mx + b OR y = m(x-px)+py
        
       


#calculate
#b = y - mx
#y = mx + b
    
-14512.376699999906 x
7790715.9472000003 y
-1.3804412689 m

y = 20033.4837065026648685207234 + c
c = 7790715.9472000003 - 20033.4837065026648685207234
c = 7770682.4634934976351314792766

y = -1.3804412689x + 7770682.4634934976351314792766 #equation of line



#=============================================================================================================================================================
print "Success!!"
#=============================================================================================================================================================

print "feature to point - for geometry extract"
sortCol = "STATION"
#tblsOrg = "SegPointEvents"
finalTbl = "XXdelete"
sortTbl = "YYdelete"
featurePoint = "FeatPoint"
arcpy.FeatureToPoint_management(lyr,featurePoint,"INSIDE")

print "skip feature to point"
# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "SegPointEvents"
orgTblRows = int(arcpy.GetCount_management(lyr).getOutput(0)) #total rows or table halfed -> Point M to geometry?
print orgTblRows
expressionDel = ' "ORIG_FID" < '+ str(orgTblRows)
arcpy.FeatureToPoint_management(lyr,finalTbl ,"CENTROID")


# Execute SelectLayerByAttribute to determine which rows to delete
arcpy.SelectLayerByAttribute_management(finalTbl, "NEW_SELECTION", expressionDel)

# Execute GetCount and if some features have been selected, then execute
#  DeleteRows to remove the selected rows.
if int(arcpy.GetCount_management(finalTbl).getOutput(0)) > 0:
    arcpy.DeleteRows_management(finalTbl)
   
#Sort rows
arcpy.Sort_management(finalTbl, sortTbl, [[sortCol, "ASCENDING"]])

points = []
pointNo = 0

# Create the geoprocessor object
gp = arcgisscripting.create(9.3)
infc = sortTbl

# Identify the geometry field
desc = gp.Describe(infc)
shapefieldname = desc.ShapeFieldName

# Create search cursor
rows = gp.SearchCursor(infc)
row = rows.Next()

# Enter while loop for each feature/row
while row:
    # Create the geometry object 'feat'
    feat = row.GetValue(shapefieldname)
    pnt = feat.GetPart()
    
    # Print x,y coordinates of current point
    IDXY = [row.getValue("STATION"),pnt.x, pnt.y ]

    points.append(IDXY)
    row = rows.Next()

for p in points:
    print p
    

#=============================================================================================================================================================
print "Success!!"
#=============================================================================================================================================================


arcpy.SaveToLayerFile_management("SegPointEvents", "C:/temp/delte.lyr")

#===============================================================#
#+++++++++++++++++++ERROR IN BELOW CODE+++++++++++++++++++++++++#
#===============================================================#
#Could be a projection issue - not getting even intervals and
#start point at 0 or 1 give no object.
#Also export shapefile/event produces dataset where you are not able
#to report back on object coordiates?? 

print "create points" 
arcpy.MakeRouteEventLayer_lr (rt, rid, tbl, props, lyr, "#",  "ERROR_FIELD")
#arcpy.MakeRouteEventLayer_lr ("EventTableFC","PREFIX","EventTable","PREFIX POINT STATION","SegPointEvents", "#",  "ERROR_FIELD")

#Deep copy - Send out feature layer to class on disk
lyr = "SegPointEvents"
lyrCoords = "Testing3"

#arcpy.CopyFeatures_management(lyr,lyrCoords)
#arcpy.CopyFeatures_management(lyr, lyrCoords)
#arcpy.FeatureClassToFeatureClass_conversion(lyr,"C:\Documents and Settings\jaworra\My Documents\ArcGIS","DeleteSS.shp")
arcpy.CreateFeatureclass_management("C:\TEMP", "TESTING11", "POINT", "", "DISABLED", "DISABLED",)
print "finish Success"

#Write out coordinates!
#lyrCoords = "SAMPLE_StateWide_MetrageRoads_MGA56"
#lyrCoords = "Testing"
lyrCoords = "TESTING11"
print "set array variables"
print "number of records: " + str(arcpy.GetCount_management(lyrCoords))
rows = arcpy.UpdateCursor(lyrCoords)
for row in rows:
    print "a"
    print row.getValue("STATION")
    feat = row.shape
    pnt = feat.getpart()
    print pnt.X, pnt.Y  
    
    feat = row.getValue(lyrCoords) #cannot acces get value
    print "b"
    pnt = feat.getPart()
    print pnt.X, pnt.Y

#===============================================================#
#++++++++++++++++++++++ERROR IN ABOVE CODE++++++++++++++++++++++#
#===============================================================#

lyrCoords = "PointInterval"

lyrCoords = "SegPointEvents"
shapeName = arcpy.Describe(lyrCoords.shapeFieldName)

rows = arcpy.UpdateCursor(lyrCoords)
for row in rows:
    print "1"
    feat = row.getValue(shapeName)                    
    print "a"
    print row.getValue("STATION")
    
    feat = row.shape
    pnt = feat.getpart()
    print pnt.X, pnt.Y


#lyrCoords  = lyrCoords.strip(".shp")
#ERROR HERE ->>> CANT access 

arcpy.CopyFeatures_management("DELETE_ME22", "topo_lines")


arcpy.CopyFeatures_management("SegPointEvents", "XXtopo_lines")

######HERE#########
new_row.shape = newgeo
new_rows.UpdateRow(new_row)
new_row = new_rows.next()
######HERE#########


import arcpy
#lyrCoords = "SAMPLE_StateWide_MetrageRoads_MGA56"
#lyrCoords = "Testing"
lyrCoords = "deletez"

lyrCoords = "PointInterval"
arcpy.RepairGeometry_management (lyrCoords)
print "set array variables"
print "number of records: " + str(arcpy.GetCount_management(lyrCoords))
rows = arcpy.SearchCursor(lyrCoords)
for row in rows:
    print "a"
    print row.getValue("STATION")
    feat = row.shape
    print "c"
    pnt = feat.getpart()
    print pnt.X, pnt.Y  




# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "PointInterval"
arcpy.FeatureToPoint_management("PointInterval","C:/Documents and Settings/jaworra/My Documents/ArcGIS/Default.gdb/deletez","INSIDE")


###
#Split line at point 
#arcpy.SplitLineAtPoint_management("streets.shp","events.shp","splitline_out.shp","20 Meters")

#FUTURE WORKS -
# investigate DELTE FROM GDB tables before starting? how to remove lock...
#Send coordinates to array


import arcpy
import math
from arcpy import env

infc = "Export_Output"
rows = arcpy.UpdateCursor(infc) #this is my feature layer
for row in rows:
    print "a"
    print (row.getValue("STATION"))
    #feat = row.getValue("Export_Output")
    #feat = row.getValue(infc) #cannot acces get value
    #print "b"
    #pnt = feat.getPart()
    #print pnt.X, pnt.Y


mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd, "Layers") 
for lyr in arcpy.mapping.ListLayers(mxd):
    print lyr.name


infc = "SegPointEvents_FeatureToPoin"
infc = "SegPointEvents"
infc = "SegPointEvents_FeatureToPoin"
rows = arcpy.SearchCursor(infc)
for row in rows:
    print "b"
    print (row.getValue("STATION"))
    feat = row.shape
    pnt = feat.getpart()




import arcgisscripting

sortCol = "STATION"
tblsOrg = "SegPointEvents"
finalTbl = "XXdelete"
sortTbl = "YYdelete"

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "SegPointEvents"
orgTblRows = int(arcpy.GetCount_management(tblsOrg).getOutput(0))/2 #total rows or table halfed -> Point M to geometry?

expressionDel = ' "ORIG_FID" < '+ str(orgTblRows)
arcpy.FeatureToPoint_management(tblsOrg,finalTbl ,"CENTROID")


# Execute SelectLayerByAttribute to determine which rows to delete
arcpy.SelectLayerByAttribute_management(finalTbl, "NEW_SELECTION", expressionDel)

# Execute GetCount and if some features have been selected, then execute
#  DeleteRows to remove the selected rows.
if int(arcpy.GetCount_management(finalTbl).getOutput(0)) > 0:
    arcpy.DeleteRows_management(finalTbl)
   
#Sort rows
arcpy.Sort_management(finalTbl, sortTbl, [[sortCol, "ASCENDING"]])

points = []
pointNo = 0

# Create the geoprocessor object
gp = arcgisscripting.create(9.3)
infc = sortTbl

# Identify the geometry field
desc = gp.Describe(infc)
shapefieldname = desc.ShapeFieldName

# Create search cursor
rows = gp.SearchCursor(infc)
row = rows.Next()

# Enter while loop for each feature/row
while row:
    # Create the geometry object 'feat'
    feat = row.GetValue(shapefieldname)
    pnt = feat.GetPart()
    
    # Print x,y coordinates of current point
    IDXY = [row.getValue("STATION"),pnt.x, pnt.y ]

    points.append(IDXY)
    row = rows.Next()

for p in points:
    print p

print "Success!!"

        

#TRIG FORMULA HERE!!!
