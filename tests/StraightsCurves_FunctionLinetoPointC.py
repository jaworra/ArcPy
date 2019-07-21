##ARCHIVE FUNCTION - Lines to points
## *** Requirement: Shapefile with attribute station 
##Returns: Shape file of points set interval


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

print "Setting Parameters"
# set parameters
inputFC = "SAMPLE_StateWide_MetrageRoads_MGA56" #"SAMPLETEST_StateWide_MetrageRoads_MGA56"
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
gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length]/100) - 0.5) + 1")
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
    projID = rowID.PREFIX
    x = 0
    while x+1 < numStations: # insert a row for each station until X = NumStations.  populate with station location along line.
        row = rows.NewRow()
        row.STATION = x * 100 + 70 #plus 70 here to as the start point 0, gives error.
        row.PREFIX = projID
        rows.InsertRow(row)
        x = x + 1
    rowID = curID.Next() # when x = numStations, go to top of loop and start for next ProjectID.

print "create points throgh linear M" 
#rt = outputFC
rid = "PREFIX"
tbl = outputTable
props = "PREFIX POINT STATION"
lyr = "LinesToPoint"


print 'make layer'
gp.MakeRouteEventLayer_lr(inputFC, rid, tbl, props, lyr, "#",  "ERROR_FIELD")
#Assign points to list
gp.MakeRouteEventLayer_lr("SAMPLE_StateWide_MetrageRoads_MGA56","PREFIX", "EventTable", "PREFIX POINT STATION","LinesToPoint19") # TAKE THIS OUT
#polyArray = arcpy.Array()
inputPts = 'LinesToPoint19'
rows = arcpy.SearchCursor(inputPts, '', '', '', 'Station A')

words = []
points = []            
for row in rows:
     #print row.Shape.getPart()           
     words = str(row.Shape.getPart()).split()
     IDXY = map(int,words[3:4])+map(float,words[0:1])+map(float,words[1:2])
     points.append(IDXY)

################################################################################################
import math
import arcgisscripting
#returns midpoint coordinate from two points
def midPoint(pt1, pt2):
    return [1,float((pt1[1]+pt2[1])/2),float((pt1[2]+pt2[2])/2)]

#distance between points
def ptDist(pt1, pt2):
    return math.sqrt(pow(float(pt2[1])-float(pt1[1]),2) + pow(float(pt2[2])-float(pt1[2]),2))

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

#caluculate intesect using slope and y intercept
#mx+c=mx+c ==  x =(c2-c1)/(m1-m2) & y = m1*x+c1], returns a coordinate
def intersect(c1,c2,m1,m2):
    if m1 == m2:
        m1 = m1+0.0000001
    return [1,float((c2-c1)/(m1-m2)),float(m1*(float((c2-c1)/(m1-m2))) + c1)]
     
#######################################################################################################START HERE!!!!!!!!!!

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
        if((ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusTight)): #Radius: 0 to raidusTight(i.e 0-300)
            points[couterList][3:5] = ["Curve",300] 
            points[couterList+1][3:5] = ["Curve",300] 
            points[couterList+2][3:5] = ["Curve",300] 
            points[couterList+3][3:5] = ["Curve",300] 
            
        elif(ptDist(intersect(c1,c2,m1,m2), points[couterList]) > raidusTight and ptDist(intersect(c1,c2,m1,m2), points[couterList]) <= raidusLimit ): #Radius: raidusTight to raidusLimit (i.e 300-500)
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
    else:
        break

CutPoint = []
AttributeAssign = []
   
#Output only start/end points list
Sortedpoints = []
couterList = 0
for Sp in points:
    if couterList == 0:
        prevPoint = Sp
        couterList = 1
        
    else:
        if prevPoint[3:5] != Sp[3:5]:
            CutPoint.append(Sp)
            AttributeAssign.append(prevPoint)#Create a list of points always before the intersection points
            prevPoint = Sp
        else:
            prevPoint = Sp
AttributeAssign.append(points[-1]) #Last point
            
print "Cut Points"
point = arcpy.Point() # Create an empty Point object
pointGeometryList = [] # A list to hold the PointGeometry objects

for Xp in CutPoint:
    point.X = Xp[1]
    point.Y = Xp[2]

    pointGeometry = arcpy.PointGeometry(point)
    pointGeometryList.append(pointGeometry)

SplitPoint = "SplitPoint"    
#Create points for split line    
arcpy.CopyFeatures_management(pointGeometryList,SplitPoint)

inFeatures="SAMPLE_StateWide_MetrageRoads_MGA56"
SplitLine="splitline"
searchRadius= "20 Meters"
arcpy.SplitLineAtPoint_management(inFeatures, SplitPoint, SplitLine, searchRadius)

#Add Columns
arcpy.AddField_management(SplitLine, "Geometry", "Text")
arcpy.AddField_management(SplitLine, "Radius", "LONG")


print "Assigned Points"
point = arcpy.Point() # Create an empty Point object
pointGeometryList = [] # A list to hold the PointGeometry objects

for Xp in AttributeAssign:
    point.X = Xp[1]
    point.Y = Xp[2]

    pointGeometry = arcpy.PointGeometry(point)
    pointGeometryList.append(pointGeometry)

AssingRow= "AssignRow"    
#Create points for split line    
arcpy.CopyFeatures_management(pointGeometryList, "C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb/"+AssingRow)
arcpy.AddField_management(pointGeometryList, "Geometry", "Text")
arcpy.AddField_management(pointGeometryList, "Radius", "LONG")

#Set attributes to points
ListCounter = 0 
Rows = arcpy.SearchCursor(AssingRow) # loop through attribute table    
for row in Rows:
    #GeometryVar = AttributeAssign[ListCounter][3:4]
    #print GeometryVar
    #RadiusVar = AttributeAssign[ListCounter][4:5]
    #print RadiusVar
    #row.setValue("Geometry", GeometryVar )
    #row.setValue("Geometry", RadiusVar )       
    row.setValue("Geometry", AttributeAssign[ListCounter][3:4])
    row.setValue("Geometry", AttributeAssign[ListCounter][4:5])
    Rows.updateRow(row)
    ListCounter += 1

#=============================================================================================================================================================
print "Successfully Completed!!"
#=============================================================================================================================================================









