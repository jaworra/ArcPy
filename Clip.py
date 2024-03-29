'----------------------------------------------------------------------------------------------------------
Sets workspace for Clip Function
Creates new layers for each Clip

'----------------------------------------------------------------------------------------------------------

import arcpy

# Set the workspace environment to local file geodatabase
arcpy.env.workspace = r'C:/data/base.gdb'


rows = arcpy.SearchCursor('key250k_GDA94_polygon_region')
for row in rows:
    feat = row.Shape
    arcpy.Clip_analysis('bop_v3_trig', feat, 'bop_v3_trig_' + str(row.getValue('FID')), '')




'----------------------------------------------------------------------------------------------------------



# Description: 
#   Goes through the table generated by the Check Geometry tool and does 
#   the following
#   1) backs-up all features which will be acted upon to a "_bad_geom" feature class
#   2) runs repairGeometry on all feature classes listed in the table 

import arcpy
import os

'----------------------------------------------------------------------------------------------------------

 
# Table that was produced by Check Geometry tool
table = r"c:\temp\f.gdb\cg_sample1"
 
# Create local variables
fcs = []
prevFc = ""
 
# Loop through the table and get the list of fcs
for row in arcpy.SearchCursor(table):
    # Get the class (feature class) for that row
    fc = row.getValue("CLASS")
 
    if fc != prevFc:
        prevFc = fc
        fcs.append(fc)
 
# Now loop through the fcs list, backup the bad geometries into fc + "_bad_geom"
# then repair the fc
print "> Processing %i feature classes" % len(fcs)
for fc in fcs:
    print "Processing " + fc
    lyr = os.path.basename(fc)
    if arcpy.Exists(lyr):
        arcpy.Delete_management(lyr)
    
    tv = "cg_table_view"
    if arcpy.Exists(tv):
        arcpy.Delete_management(tv)

    arcpy.MakeTableView_management(table, tv, ("\"CLASS\" = '%s'" % fc))
    arcpy.MakeFeatureLayer_management(fc, lyr)
    arcpy.AddJoin_management(lyr, arcpy.Describe(lyr).OIDFieldName, tv, "FEATURE_ID")
    arcpy.CopyFeatures_management(lyr, fc + "_bad_geom")
    arcpy.RemoveJoin_management(lyr, os.path.basename(table))
    arcpy.RepairGeometry_management(lyr)
                    
