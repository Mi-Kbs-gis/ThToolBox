# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 TerrainModel
 TLUG Algorithms
                              -------------------
        begin                : 2018-08-27
        copyright            : (C) 2017 by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
        email                : Michael.Kuerbs@tlubn.thueringen.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Michael Kürbs'
__date__ = '2022-04-20'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'


import sys
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorDataProvider
from qgis.core import QgsProcessingException
from qgis.core import QgsCoordinateTransform
from qgis.core import QgsProject
from qgis.core import QgsPoint
from qgis.core import QgsFeature
from qgis.core import QgsGeometry
from qgis.core import QgsError
from qgis.core import QgsField
#from qgis.core import QgsWKBTypes
from qgis.core import QgsRaster
from qgis.core import * #QGis
from qgis.PyQt.QtCore import QObject
import math

import datetime
import struct
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from .RasterInterpolator import RasterInterpolator
    
class TerrainModel(QObject):
    
    def __init__(self, rasterLayer, feedback): 
        self.feedback=feedback
        self.rasterLayer=rasterLayer
        self.dataProv = rasterLayer.dataProvider()
        self.exportNodata=-9999  
        self.srcNodata=None
        if self.dataProv.sourceHasNoDataValue==True:
            self.srcNodata=self.dataProv.sourceNoDataValue
        self.myExtent = self.dataProv.extent()
        self.theWidth = self.rasterLayer.width()
        self.theHeight = self.rasterLayer.height()
        self.pixelSizeX=self.rasterLayer.rasterUnitsPerPixelX()
        self.pixelSizeY=self.rasterLayer.rasterUnitsPerPixelY()
        #mittler Rasterweite aus xSize und ySize
        self.rasterWidth=(self.pixelSizeX + self.pixelSizeY) / 2 
        
        dataset = gdal.Open(self.rasterLayer.source(), GA_ReadOnly)
        try:
            geotransform = dataset.GetGeoTransform()
        except Exception as err:
            msg='Digital elevation raster layer <' +  self.rasterLayer.name()+ '> is not valid! Georeference not found! '+ str(err.args) 
            #feedback.reportError( msg )
            raise QgsProcessingException( msg )
        bandNo=1
        band = dataset.GetRasterBand(bandNo)
        self.nodata=band.GetNoDataValue()
        feedback.pushInfo("TerrainModel.NoData:" + str(self.nodata))
        bandtype = gdal.GetDataTypeName(band.DataType)
        interpolMethod=1 #0=nearestNeighbor, 1=linear 2x2 Pixel, 2=bicubic 4x4 Pixel
        self.interpolator=RasterInterpolator(rasterLayer, interpolMethod, bandNo, dataset, self.feedback)
        #print("width",self.rasterLayer.dataProvider().width())
        
    def addZtoPointFeatures(self, inputPoints, inputCrs, fieldIdWithZVals=-1, override=True):
        #pointsListZ=[] #list of QgsFeature()
        featuresWithZ=[]
        try:
            
            #check if pointsLayer is emty
            #if inputPoints.featureCount!=0:
            for feat in inputPoints:
                #if geom.hasZ==False or geom.hasZ==True and override==True:
                # get Raster Values for each point feature
                featZ=QgsFeature(feat.fields()) #Copy of the Feature
                geom=feat.geometry()
                #create a copy of the geometry for temporary transform to the project.crs()
                wkb=feat.geometry().asWkb()
                #self.feedback.pushInfo("addZtoPointFeatures1 " + geom.asWkt())
                geom2CRS=QgsGeometry()
                geom2CRS.fromWkb(wkb)
                #transform geom to rasterLayer.crs() if crs a different
                if not inputCrs.authid()==self.rasterLayer.crs().authid():
                    trafo=QgsCoordinateTransform(inputCrs, self.rasterLayer.crs(), QgsProject.instance())
                    #transform clip Geom to SrcLayer.crs Reverse
                    geom2CRS.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)

                pinPoint=None
                if geom.isMultipart():
                    pinPoint=geom.vertexAt(0) #nimm den ersten Punkt, wenn es ein MultiPoint ist
                    pin2Crs=geom2CRS.vertexAt(0)

                else:
                    pinPoint=geom.asPoint()
                    pin2Crs=geom2CRS.asPoint()

                rastVal=None
                if fieldIdWithZVals > -1:
                    rastVal=feat[fieldIdWithZVals]
                    if rastVal is None or str(rastVal) =='NULL':
                        felder = feat.fields()
                        feld = felder.field(fieldIdWithZVals)
                        self.feedback.reportError('Error on Feature ' + str(feat.id()))
                        self.feedback.reportError('Feature Attributes :' + str(feat.attributes()))
                        raise QgsProcessingException('Z value on field   '  + feld.name() + ' is empty!')
                else: #hole Z-Wert von DGM
                    rastVal = self.interpolator.linear(pin2Crs)            #QgsPointXY(4459566.0, 5613959.0))
                #self.feedback.pushInfo("addZtoPointFeatures2 " + geom.asWkt() + " 2Crs: " + geom2CRS.asWkt())
                #self.feedback.pushInfo("rastVal " + str(pinPoint)+ " = in RasterCrs:"+ str(pin2Crs)+ " = "+ str(rastVal))
                #rastSample = rasterLayer.dataProvider().identify(pin2Crs, QgsRaster.IdentifyFormatValue).results()
                if not rastVal is None and str(rastVal) !='NULL' and self.srcNodata!=rastVal and self.exportNodata!=rastVal: # ToDo der Leerwert muss noch beruecksichtigt werden
                    wkt="PointZ(" + str( pinPoint.x() ) + " " + str(pinPoint.y()) + " " + str(rastVal) + ")"
                    #self.feedback.reportError(wkt)
                    
                    #construct new Feature in source Crs
                    #ptZ=QgsPoint( pinPoint.x(), pinPoint.y() )
                    #ptZ.addZValue( rastVal )
                    geomZ=QgsGeometry.fromWkt( wkt )
                    featZ.setGeometry( geomZ )
                    featZ.setAttributes( feat.attributes() )
                    featuresWithZ.append( featZ )
                else:
                    #construct new Feature in source Crs with Raster value -9999
                    wkt="PointZ(" + str( pinPoint.x() ) + " " + str(pinPoint.y()) + " " + str(self.exportNodata) + ")"

                    geomZ=QgsGeometry.fromWkt( wkt )
                    featZ.setGeometry( geomZ )
                    featZ.setAttributes( feat.attributes() )
                    featuresWithZ.append( featZ )
                    
                    #self.feedback.reportError('Point Feature: ' + feat.id() + '  ' + wkt + ' ' + feat.attributes() )
                    #raise QgsProcessingException("No valid RasterValue for this position: " + str(round(pinPoint.x(),1)) + " " + str(round(pinPoint.y(),1) ) + ' raster value: ' + str(rastVal))
                    
            #self.feedback.pushInfo("addZtoPointFeatures " + str(len(featuresWithZ))+ " Objekte")
        except Exception as err:
            msg = "Error: add Z to Point Features {0} \n {1}".format(err.args, repr(err))
            self.feedback.reportError(msg)
            featuresWithZ=[]
            raise QgsProcessingException(msg)
            #print("Error addZtoPointFeatures")#,str(err.args) + ";" + str(repr(err)))
            #raise QgsProcessingException("Error addZtoPointFeatures " + str(err.args))# + ";" + str(repr(err)))
        return featuresWithZ

    def addZtoPoints(self, inputPoints, inputCrs, fieldIdWithZVals=-1, override=True):
        pointsListZ=[] #list of QgsPoint()
        #featuresWithZ=[]

        #try:
        #self.feedback.pushInfo("ProjektCrs: " + str(inputCrs.authid()) +" <> RasterCrs"+ str(self.rasterLayer.crs().authid()))
            
        for point in inputPoints:
            #if geom.hasZ==False or geom.hasZ==True and override==True:
            # get Raster Values for each point

            rastVal=None
            if fieldIdWithZVals > -1:
                rastVal=feat[fieldIdWithZVals]
            else: #hole Z-Wert von DGM
                #create a copy of the geometry for temporary transform to the project.crs()
                tempGeom = QgsGeometry.fromPointXY( QgsPointXY(point.x(), point.y()))
                tempPoint=QgsPointXY(point.x(), point.y())
               
                #transform input to rasterLayer.crs() if crs a different
                if not inputCrs.authid()==self.rasterLayer.crs().authid():
                    trafo=QgsCoordinateTransform(inputCrs, self.rasterLayer.crs(), QgsProject.instance())
                    #transform clip Geom to SrcLayer.crs Reverse
                    tempGeom.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)
                    tempPoint=tempGeom.asPoint()
                #self.feedback.pushInfo("addZtoPoints: " + str(point) +" <> "+ str(tempPoint))
                rastVal = self.interpolator.linear(tempPoint)            #QgsPointXY(4459566.0, 5613959.0))
            #rastSample = rasterLayer.dataProvider().identify(pinPoint, QgsRaster.IdentifyFormatValue).results()
            #for rastVal in rastSample:
            #rastVal=rastSample[1]
            #ptZ=QgsPoint(point.x(), point.y(), rastVal)
            #wkt="PointZ(" + str(point.x()) + " " + str(point.y()) + " " + str(rastVal) + ")"
            #geomZ=QgsGeometry.fromWkt(wkt)
            #print(point.asWkt(), "Z:", rastVal, geomZ)
            #print(geomZ.asWkt())
            if not rastVal is None:
                pointsListZ.append(QgsPoint(point.x(), point.y(), rastVal))
            else: # if nodata 
                pointsListZ.append(QgsPoint(point.x(), point.y(), 0 ) )#self.nodata

        #else:
        #    raise Exception(self.tr('source layer is emty'))
        
        #Look if new features are there

                
        #except Exception as e:
        #    print("Fehler addZtoPoints")#e.errno, e.strerror)

        
        return pointsListZ