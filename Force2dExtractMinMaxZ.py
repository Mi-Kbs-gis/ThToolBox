# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 Force 2D Extract Min/Max Z-Values
 TLUG Algorithms
                              -------------------
        begin                : 2017-12-19
        copyright            : (C) 2017 by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)
        email                : Michael.Kuerbs@tlug.thueringen.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Michael Kürbs'
__date__ = '2017-12-19'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'


import sys
from PyQt4.QtCore import QSettings, QVariant
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorDataProvider
from qgis.core import QgsPoint
from qgis.core import QgsFeature
from qgis.core import QgsGeometry
from qgis.core import QgsError
from qgis.core import QGis, QgsField, QgsWKBTypes

import datetime
import struct
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector, OutputFile
from processing.tools import dataobjects, vector


import struct
import datetime
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from PyQt4 import QtSql


from osgeo import ogr


class Force2dExtractMinMaxZ(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_LAYER = 'INPUT_LAYER'
    OUTPUT = 'OUTPUT'
    USE_NULL = 'USE_NULL'
    
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name, self.i18n_name = self.trAlgorithm('Force2D & Extract Min/Max Z-Values')

        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('3D Tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterVector(self.INPUT_LAYER, self.tr('Input 3D Vectorlayer'),[ParameterVector.VECTOR_TYPE_ANY]))


        # We add a Vectorlayer as Output
        self.addOutput(OutputVector(self.OUTPUT, self.tr('2D layer with Min/Max Z-Values')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        outputFileName = self.getOutputValue(self.OUTPUT)

        #------ hole Layer -------
        startTime= datetime.datetime.now()
        print "Start", startTime

        vectorLayer = dataobjects.getObjectFromUri(inputFilename)

        if vectorLayer.wkbType()==ogr.wkbMultiPoint25D or vectorLayer.wkbType()==ogr.wkbLineString25D or vectorLayer.wkbType()==ogr.wkbMultiLineString25D or vectorLayer.wkbType()==ogr.wkbPolygon25D or vectorLayer.wkbType()==ogr.wkbMultiPolygon25D:
            pass #ok
        else: #ogr.wkbGeometryCollection25D is not implemented yet
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
                                       self.tr('Vector format not supported: ' + geom_ogr.GetGeometryType()))
                                       
            raise GeoAlgorithmExecutionException('Vector format not supported: ' + geom_ogr.GetGeometryType()+ " Supported are MultiPoint25D, LineString25D, MultiLineString25D, Polygon25D, MultiPolygon25D")

        isGeomunique, geomTypes = self.checkForUniqueGeometryType(vectorLayer)
        print "Geometrietypen:", geomTypes #"Layerobjekte haben evtl. unterschiedliche Geometrytypen"
        if isGeomunique==False:
            raise GeoAlgorithmExecutionException('Layer object have several geometry types', geomTypes)
        
        fields = vectorLayer.pendingFields()
        fields.append(QgsField("z_min", QVariant.Double))
        fields.append(QgsField("z_max", QVariant.Double))
        
        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields,
            QgsWKBTypes.multiType(QGis.fromOldWkbType(self.getCorresponding2dWkbType(vectorLayer.wkbType()))),
            vectorLayer.crs())
        

        #Iterating over Vector Layer
        iter = vectorLayer.getFeatures()
        i=0
        for feature in iter:
            attrs=feature.attributes()
            geom = feature.geometry()
            geom2d, zmin, zmax=self.computeGeometrieValuesZ(geom)
            attrs.append(zmin)
            attrs.append(zmax)
            try:
                out_feat = QgsFeature()
                out_feat.setGeometry(geom2d)
                out_feat.setAttributes(attrs)
                writer.addFeature(out_feat)
            except:
                ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
                                       self.tr('Feature geometry error: One or more '
                                               'output features ignored due to '
                                               'invalid geometry.'))
                continue
            progress.setPercentage(100.0 * i / vectorLayer.featureCount())
            i=i+1
        
        del writer

        endTime= datetime.datetime.now()
        print "Ende", endTime
        self.printTimeDiff(startTime, endTime)
        
    #gets the List of all Points from a MultiPolygonZ as OGR-Geometry
    def getPointsFromMultiPolygonZ(self, ogrGeom):
        pointList=[]
        for polygon in ogrGeom:
            for linRing in polygon:
                for i in range(linRing.GetPointCount()-1): #Last coordinate in a LinearRing is a duplicate of the first point
                    point=linRing.GetPoint(i)
                    pointList.append(point)
        return pointList

    #gets the List of all Points from a PolygonZ as OGR-Geometry
    def getPointsFromPolygonZ(self, ogrGeom):
        pointList=[]
        for linRing in ogrGeom:
            for i in range(linRing.GetPointCount()-1): #Last coordinate in a LinearRing is a duplicate of the first point
                point=linRing.GetPoint(i)
                pointList.append(point)
        return pointList

    #gets the List of all Points from a PolygonZ as OGR-Geometry
    def getPointsFromMultiLineStingZ(self, ogrGeom):
        pointList=[]
        for line in ogrGeom:
            for i in range(line.GetPointCount()-1): #Last coordinate in a LinearRing is a duplicate of the first point
                point=line.GetPoint(i)
                pointList.append(point)
        return pointList
        
    #gets the List of all Points from a LineStringZ as OGR-Geometry
    def getPointsFromLineStingZ(self, ogrGeom):
        pointList=[]
        for i in range(ogrGeom.GetPointCount()):
            point=ogrGeom.GetPoint(i)
            pointList.append(point)
        return pointList

    #gets the List of all Points from a LineStringZ as OGR-Geometry
    def getPointsFromMultiPointZ(self, ogrGeom):
        pointList=[]
        for i in range(ogrGeom.GetPointCount()):
            point=ogrGeom.GetPoint(i)
            pointList.append(point)
        return pointList
    
    #gets 2D Geometry from a MultiPolygonZ by Union
    def get2dGeometrieFromMultiPolygonZ(self, geom):
        polygonList=geom.asMultiPolygon() 
        i=0
        unionGeom=None
        for polygon in polygonList:
            pGeom=QgsGeometry.fromPolygon(polygon)
            if unionGeom==None and pGeom.area()>0.01: #i==0: Wenn das Erste Objekt keine Fläche hat funktioniert union nicht
                unionGeom=pGeom

            elif unionGeom!=None and pGeom.area()>0.01:
                tempGeom=unionGeom.combine(pGeom)
                if tempGeom.area()>0.01:
                    unionGeom=tempGeom
                                
            #print i, unionGeom.exportToWkt(), pGeom.exportToWkt()
            i=i+1
        return unionGeom #Kann ein Multipolgon sein, insofern sich die Elemente nicht überlagern
        
    #gets 2D Geometry from a PolygonZ
    def get2dGeometrieFromPolygonZ(self, geom):
        ptList2d=geom.asPolygon()
        geom2d=QgsGeometry.fromPolygon(ptList2d)
        return geom2d

    #gets 2D Geometry from a MultiLineStringZ
    def get2dGeometrieFromMultiLineStringZ(self, geom):
        ptList2d=geom.asMultiPolyline()
        geom2d=QgsGeometry.fromMultiPolyline(ptList2d)
        return geom2d
        
    #gets 2D Geometry from a LineStringZ
    def get2dGeometrieFromLineStringZ(self, geom):
        ptList2d=geom.asPolyline()
        geom2d=QgsGeometry.fromPolyline(ptList2d)
        return geom2d
        
    #gets 2D Geometry from a MultiPointZ
    def get2dGeometrieFromMultiPointZ(self, geom):
        ptList2d=geom.asMultiPoint()
        geom2d=QgsGeometry.fromMultiPoint(ptList2d)
        return geom2d

    #gets 2D Geometry from a PointZ
    def get2dGeometrieFromPointZ(self, geom):
        ptList2d=geom.asPoint()
        geom2d=QgsGeometry.fromPoint(ptList2d)
        return geom2d
        

    #analyze the Z-Values of each vertex from a MultipolygonZ or PolygonZ as QgsGeometry
    def computeGeometrieValuesZ(self, geom):
        ipoint=0
        zmax=0
        zmin=0
        wkb=geom.asWkb()
        #convert to a OGR.Geometry, because in QgsGeometry is no access to Z-values yet (QGIS 2.18)
        geom_ogr = ogr.CreateGeometryFromWkb(wkb)
        
        #compute the Minimum and Maximum Z-Value of the ggeometry
        points=[]
        geom2d=None
        #print geom_ogr.GetGeometryType(), geom_ogr.GetGeometryCount(), geom_ogr.GetPointCount(), geom_ogr.ExportToWkt()
        if geom_ogr.GetGeometryType()==ogr.wkbMultiPolygon25D:
            points=self.getPointsFromMultiPolygonZ(geom_ogr)
            geom2d=self.get2dGeometrieFromMultiPolygonZ(geom) # returns a 2d Geometry, overlapped features were unioned and hand out as a single Geometry
            
        elif geom_ogr.GetGeometryType()==ogr.wkbPolygon25D:
            points=self.getPointsFromPolygonZ(geom_ogr)
            geom2d=self.get2dGeometrieFromPolygonZ(geom)
            
        elif geom_ogr.GetGeometryType()==ogr.wkbMultiLineString25D:
            points=self.getPointsFromMultiLineStingZ(geom_ogr)
            geom2d=self.get2dGeometrieFromMultiLineStringZ(geom)
            
        elif geom_ogr.GetGeometryType()==ogr.wkbLineString25D:
            points=self.getPointsFromLineStingZ(geom_ogr)
            geom2d=self.get2dGeometrieFromLineStringZ(geom)
            
        elif geom_ogr.GetGeometryType()==ogr.wkbMultiPoint25D:
            points=self.getPointsFromMultiPointZ(geom_ogr)
            geom2d=self.get2dGeometrieFromMultiPointZ(geom)
            
        elif geom_ogr.geom_ogr.GetGeometryType()==ogr.wkbPoint25D:
            points=geom.asPoint()
            geom2d=self.get2dGeometrieFromPointZ(geom)
            
        else:
            print "falscher Geometrietyp:", geom_ogr.GetGeometryType()
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
                                       self.tr('Vector format not supported: ' + geom_ogr.GetGeometryType()))
                                       
            raise GeoAlgorithmExecutionException('Vector format not supported: ' + geom_ogr.GetGeometryType())
        for point in points:
            z=point[2]
            #get Minimum and Maximum
            if ipoint==0:
                zmax=z
                zmin=z
            elif z>zmax:
                zmax=z
            elif z<zmin:
                zmin=z
            #print point
            ipoint=ipoint+1
        #print zmin, zmax, geom.exportToWkt()
        return geom2d, zmin, zmax
    
    #testet ob die Objekte eines Layers alle den gleichen Geometrietyp haben
    def checkForUniqueGeometryType(self,layer):
        isUnique=False
        typeList=[]
        #Iterating over Vector Layer
        iter = layer.getFeatures()
        i=0
        for feature in iter:
            attrs=feature.attributes()
            geom = feature.geometry()
            #print str(geom.exportToWkt())[:15]
            wkb=geom.asWkb()
            #convert to a OGR.Geometry, because in QgsGeometry make no Difference between several Types (QGIS 2.18)
            geom_ogr = ogr.CreateGeometryFromWkb(wkb)
            geomType=geom_ogr.GetGeometryType() #geom.wkbType()
            try:
                j=typeList.index(geomType)
                #GeometryType vorhanden
            except ValueError:
                typeList.append(geomType)
        if len(typeList)>1: # Wenn mehr als ein Geometrietyp pro Layer
            isUnique=False
        else:
            isUnique=True
        return isUnique, typeList
        
    def printTimeDiff(self, startTime, endTime):
        timeDelta=endTime-startTime
        totalSeconds=timeDelta.total_seconds()
        print "totalSeconds", totalSeconds
        
        minsDecimal=str(totalSeconds/60)
        splitMins=minsDecimal.split(".")
        mins=int(splitMins[0])
        if len(splitMins)>1:
            seconds=int(float("0."+splitMins[1])*60) #Sekunden abzueglich der vollen Minuten
        hoursDecimal=str(mins/60)
        splitHours=hoursDecimal.split(".")
        hours=int(splitHours[0])
        if len(splitHours)>1:
            mins=int(float("0."+splitHours[1])*60) #mins abzueglich der vollen Stunden
        print "Dauer h:min:sec", hours, ":",mins, ":", seconds

    def getCorresponding2dWkbType(self, wkbType):
        typeMap={}
        typeMap[ogr.wkbPoint25D]=ogr.wkbPoint
        typeMap[ogr.wkbLineString25D]=ogr.wkbLineString
        typeMap[ogr.wkbPolygon25D]=ogr.wkbPolygon
        typeMap[ogr.wkbMultiPoint25D]=ogr.wkbMultiPoint
        typeMap[ogr.wkbMultiLineString25D]=ogr.wkbMultiLineString
        typeMap[ogr.wkbMultiPolygon25D]=ogr.wkbMultiPolygon
        try:
            type=typeMap[wkbType]
            return type
        except KeyError:
            print "Vector format not supported"
            raise GeoAlgorithmExecutionException('Vector format not supported: ' + geom_ogr.GetGeometryType()+ " Supported are MultiPoint25D, LineString25D, MultiLineString25D, Polygon25D, MultiPolygon25D")
        return type