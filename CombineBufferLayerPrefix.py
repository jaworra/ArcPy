##ARCHIVE FUNCTION - Combine Layers with the same prefix e.g SP_1 and SP_2
###Combined layers with the same first 3 letters  
##

import math
import arcgisscripting

#Scratch workspace assign to GDB values instead of tempdrive
import sys, arcgisscripting, string, os
arcpy.env.overwriteOutput = True

mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd,"Layers") [0]
layerName=[]

for lyr in arcpy.mapping.ListLayers(mxd):
    try:
        layerName.append(lyr.name)
    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)
j=0
i =0
for p in layerName:
    j += 1
    pLayerName = p[0:3]
    i =0
    for q in layerName[j:]:
        i +=1
        if q[0:3] == pLayerName: # Matching Layers prefix
            if i == 1: #First Combine
                arcpy.Merge_management([p, q], "B")
                arcpy.Dissolve_management("B", "C","CATEGORY", "", "", "")
                arcpy.Sort_management( "C",pLayerName+"NoiseBuffer", [["CATEGORY", "DESCENDING"]])
            else: #Multiple Combines
                arcpy.Merge_management([pLayerName+"NoiseBuffer", q], "B")
                arcpy.Dissolve_management("B", "C","CATEGORY", "", "", "")
                arcpy.Sort_management("C",pLayerName+"NoiseBuffer", [["CATEGORY", "DESCENDING"]])
            layerName.remove(q)
        else: #Rename unprocess layer
            arcpy.CopyFeatures_management(p,pLayerName+"NoiseBuffer")

            
            

