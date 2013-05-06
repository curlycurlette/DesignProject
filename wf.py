# -*- coding: cp1252 -*-
# Design project 2013
# Guillaume Jornod guillaume.jornod@epfl.ch
# Mikaël Vaivre mikael.vaivre@epfl.ch


import arcpy, arcgisscripting, os, stat, commands
from arcpy import env
from arcpy.sa import *
from datetime import datetime
import winsound, sys

# Import extensions
arcpy.SetProduct('ArcView')
arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension("3D")
#arcpy.CheckOutExtension('Network')

# # Changing windows permissions
target = r"C:/arcout"
# myFile = target
# if not os.path.exists(myFile):
#     os.makedirs(myFile)
# fileAtt = os.stat(myFile)[0]
# if (not fileAtt & stat.S_IWRITE):
#    # File is read-only, so make it writeable
#    os.chmod(myFile, stat.S_IWRITE)

# Set global variables
env.workspace = target
arcpy.overwriteoutput = True
arcpy.env.overwriteOutput = True
recomp = False # Do not recompute all preprocessing steps
multi = False # Fixed decision parameters
gp = arcgisscripting.create()
gp.overwriteoutput = True

# Output time function
def pprint(out):
    FORMAT = '%Y-%m-%d %H:%M:%S'
    print datetime.now().strftime(FORMAT) + ': ' + out
pprint('Start')

try:
    ref = arcpy.SpatialReference("../shp/Routes_w.prj")
    pprint('Spatial refereces defined')
except Exception as e:
    winsound.Beep(2000, 1000)
    print e.message
    sys.exit()

# Create GDB
if (not arcpy.Exists('gruyere.gdb')):
    pprint('GDB creation')
    arcpy.CreateFileGDB_management(target, "gruyere.gdb")
    pprint('Feature dataset creation')
    arcpy.CreateFeatureDataset_management(target + "/gruyere.gdb", "roadFeatDat", ref)
else:
    pprint('GDB already created')

# Dev
if (not arcpy.Exists(target + "/roads.shp")):
    xmin = 780000
    ymin = 5000000
    xmax = 800000
    ymax = 5900000
#     xmin = 756793
#     ymin = 831872
#     xmax = 5828371
#     ymax = 5889175
    strcoo = str(xmin) + ' ' + str(ymin) + ' ' + str(xmax) + ' ' + str(ymax)
    pprint('Clipping MNT')
    arcpy.Clip_management("../shp/DHM25MM_Clip_WGS.tif", strcoo, target + "/DEM.tif", "#", "#", "NONE")
    pprint('Rectangle creation')
    coordList = [[[xmin,ymax], [xmax,ymax], [xmax,ymin], [xmin, ymin]]]
    point = arcpy.Point()
    array = arcpy.Array()
    featureList = []
    for feature in coordList:
        for coordPair in feature:
            point.X = coordPair[0]
            point.Y = coordPair[1]
            array.add(point)
        array.add(array.getObject(0))
        polygon = arcpy.Polygon(array, ref)
        array.removeAll()
        featureList.append(polygon)
    arcpy.CopyFeatures_management(featureList, target + "/rect.shp")
    pprint('Clipping roads')
    arcpy.Clip_analysis("../shp/Routes_w.shp", target+"/rect.shp", target + "/roads.shp")
    pprint('Clipping points')
    arcpy.Clip_analysis("../shp/points.shp", target+"/rect.shp", target + "/points.shp")
else:
    pprint('Data already clipped')
    
    
# # Slope calculation
# if (not arcpy.Exists(target + '/gruyere.gdb/roadFeatDat/outSlopePoly.shp ') or recomp):
#     pprint ('Slope computation')
#     outSlope = Slope(target + "/hillShade.tif", "DEGREE", 1)
#     outSlope = Int(outSlope)
#     pprint('Slope raster to polygon')
#     try:
#         outSlopePoly = arcpy.RasterToPolygon_conversion(outSlope, "outSlopePoly.shp", "SIMPLIFY", "VALUE")
#     except Exception as e:
#         print e.message
#         arcpy.AddError(e.message)
#         winsound.Beep(1000,1000)
#         sys.exit()
#     pprint("Copy to gdb")
#     try:
#         arcpy.FeatureClassToGeodatabase_conversion(outSlopePoly, target + "/gruyere.gdb/roadFeatDat")
#     except Exception as e:
#         print e.message
#         arcpy.AddError(e.message)
#         winsound.Beep(2500,1000)
#         sys.exit()
#     from datetime import datetime
#     pprint('Raster to polygon ended')
# else:
#     pprint('Slope already computed')
# arcpy.env.workspace = target + "/gruyere.gdb/roadFeatDat/"


# Create new layer
# if (not arcpy.Exists('roads.shp') or recomp):
#    pprint('Copying road shpfile in workspace')
#    arcpy.CopyFeatures_management("shp/Routes.shp", "roads.shp")
if (not arcpy.Exists(target + "gruyere.gdb/DEM") and not arcpy.Exists(target + "gruyere.gdb/DEM.tif")):
    try:
        pprint('Copying DEM into gdb')
        arcpy.RasterToGeodatabase_conversion(target + "/DEM.tif", target + "/gruyere.gdb/")
    except Exception as e:
        print e.message
        arcpy.AddError(e.message)
        winsound.Beep(2500,1000)
        sys.exit()
else:
    pprint('DEM already in GDB')
 
from datetime import datetime
arcpy.env.workspace = target + "/gruyere.gdb/"
# Determine which features to delete
pprint('Road selection')
try:
    if (not arcpy.Exists("roadFeatDat/roadSel")):
        arcpy.Select_analysis("C:/arcout/roads.shp", "roadFeatDat/roadSel", "(OBJECTVAL = '1_Klass' OR OBJECTVAL = '2_Klass' OR OBJECTVAL = '3_Klass' OR OBJECTVAL = '4_Klass')")
except Exception as e:
    print e.message
    arcpy.AddError(e.message)
    winsound.Beep(3500,500)
    sys.exit()
    
 
    
# Slopes
if (not arcpy.Exists(target + '/gruyere.gdb/roadFeatDat/roadSlope.shp ') or recomp):
    pprint('Adding vertical information data')
    try:
        arcpy.AddSurfaceInformation_3d("roadFeatDat/roadSel", target+ "/DEM.tif", "Z_MIN; Z_MAX; Z_MEAN; SURFACE_LENGTH; MIN_SLOPE; MAX_SLOPE; AVG_SLOPE", "LINEAR")
    except Exception as e:
        print e.message
        winsound.Beep(1000,1000)
        sys.exit()
    
         
# # Transfer slope attribute to road
# if (not arcpy.Exists('roadSlope') or recomp):
#     pprint('Transfering slopes')
#     try:
#         arcpy.SpatialJoin_analysis("roadSel", "outSlopePoly", "roadSlope", "JOIN_ONE_TO_MANY", "KEEP_ALL")
#     except Exception as e:
#         print e.message
#         arcpy.AddError(e.message)
#         winsound.Beep(1000,500)
#         sys.exit()
# else:
#     pprint('Slopes already transferred')
#  
# winsound.Beep(2500,1000)
 
# Create Network
if (not arcpy.Exists("roadNetwork") or recomp or multi):
#     if arcpy.Exists("roadNetwork_Junctions"):
#         try:
#             arcpy.DeleteFeatures_management("roadFeatDat/roadNetwork_Junctions")
#         except Exception as e:
#             print e.message
#             arcpy.AddError(e.message)
#             winsound.Beep(1000,5000)
#             sys.exit()
#     if arcpy.Exists("roadFeatDat/roadNetwork"):
#         try:
#             arcpy.DeleteFeatures_management("roadFeatDat/roadNetwork")
#         except Exception as e:
#             print e.message
#             arcpy.AddError(e.message)
#             winsound.Beep(1000,5000)
#             sys.exit()
    pprint('Creating Road Network')
    try:
        arcpy.CreateGeometricNetwork_management ("C:/arcout/gruyere.gdb/roadFeatDat", "roadNetwork", "roadSel SIMPLE_EDGE NO", "1.2")#, {weights}, {weight_associations}, {z_snap_tolerance}, {preserve_enabled_values})
    except Exception as e:
        print e.message
        arcpy.AddError(e.message)
        winsound.Beep(1000,500)
        sys.exit()
else:
    pprint('Network already exists')
    
# Snap POI to roads
if (not arcpy.Exists("points")):
    try:
        pprint("Snapping points")
        arcpy.Snap_edit("C:/arcout/points.shp","C:/arcout/gruyere.gdb/roadFeatDat/roadSel EDGE '10'")
    except Exception as e:
        print e.message
        winsound.Beep(150, 500)
        sys.exit()
else:
    pprint("Points already snapped")
 
# Find loops

try:
    pprint('Tracing loops')
    arcpy.TraceGeometricNetwork_management("roadFeatDat/roadNetwork","net","C:/arcout/points.shp","FIND_CONNECTED","","","","","","NO_TRACE_ENDS","NO_TRACE_INDETERMINATE_FLOW","","","AS_IS","","","","AS_IS")
except Exception as e:
    print e.message
    winsound.Beep(1000,500)
    sys.exit()
pprint('Done, exiting')
winsound.Beep(1000,100)
winsound.Beep(1500,100)
winsound.Beep(2000,100)
winsound.Beep(2500,100)


# TODO
# Choisir les classes de routes roulables (genre pas autobahnen) et la limite de pente admissible (il y aquand même du 80%"""
# Eliminer les classes indésirées
# Eliminer les routes qui contiennent une pente au dessus de la limite (peut être repasser à la couche Route en utilisant l'attribut)
# Vérifier que les routes restantent sont bien connectées (idem)
# Checker network analyst pour tsp.
