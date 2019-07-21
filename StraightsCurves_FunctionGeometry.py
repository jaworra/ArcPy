##ARCHIVE FUNCTION - Geometry assignment
## *** Requirement: points table created from previous script
##Returns: List file with geometry attributes

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
## ++++++++++++REMOVE+++++++++++++++++++++++++++++++++++++++++

sortTbl = "SortTbl"
sortCol = "STATION"
#Sort rows
lyr = "Export_Output_8"
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


#Output the whole list
for Wl in points:
    print 


exit 


    
#Output only start/end points list
Sortedpoints = []
couterList = 0
for Sp in points:
    if couterList == 0:
        print Sp
        prevPoint = Sp[3:5]
        couterList = 1
        
    else:
        if prevPoint != Sp[3:5]:
            print Sp
            prevPoint = Sp[3:5]          
        

#=============================================================================================================================================================
print "Successfully Completed!!"
#=============================================================================================================================================================
