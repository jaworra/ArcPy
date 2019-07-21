#---------------------------------------------------------------
print ("CHECK GEOMETRY") 
#---------------------------------------------------------------
# Import modules
import arcpy
import os

# The workspace in which the feature classes will be checked
outTable = "C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb\checkGeometryResult"
arcpy.env.workspace = "C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb"
 
# A variable that will hold the list of all the feature classes 
# inside the geodatabase
fcs = []
 
# List all feature classes in feature datasets
for fds in arcpy.ListDatasets("","featuredataset"):
    fcs += arcpy.ListFeatureClasses("*","",fds)
          
# List all standalone feature classes
fcs = arcpy.ListFeatureClasses()
     
print "Running the check geometry tool on %i feature classes" % len(fcs)
arcpy.CheckGeometry_management(fcs, outTable)
print (str(arcpy.GetCount_management(outTable)) + " geometry problems were found.")

#---------------------------------------------------------------
print ("REPAIR GEOMETRY")
#---------------------------------------------------------------

# Table that was produced by Check Geometry tool
table = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb\checkGeometryResult"
 
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
    arcpy.RepairGeometry_management(lyr

#---------------------------------------------------------------
print ("Clip Feature")
#---------------------------------------------------------------

rows = arcpy.SearchCursor('key250k_GDA94_polygon_region')
for row in rows:
    feat = row.Shape
    arcpy.Clip_analysis('bop_v3_trig', feat, 'bop_v3_trig_' + str(row.getValue('FID')), '')
print "Successful Completed!!"