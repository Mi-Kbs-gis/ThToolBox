# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 TLUBN_Utils
 TLUBN Algorithms
                              -------------------
        begin                : 2019-01-31
        copyright            : (C) 2019 by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
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
__date__ = '2019-01-31'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

from qgis.core import *
from qgis.PyQt.QtCore import QObject
import math

class LayerUtils(QObject):
    
    def __init__(self, crs, feedback):
        self.feedback=feedback
        self.crs=crs
    
    #returns a list of sub features
    def multiPartToSinglePartFeature(self, feat):
        featureList=[]
        #explode Multipart features
        #self.feedback.pushInfo( "multiPartToSinglePartFeature geom: " + str( feat.geometry().asWkt()) +" type: "+ str(feat.geometry().type()) +" wkbtype: "+ str(feat.geometry().wkbType()) + " isMultipart: " + str(feat.geometry().isMultipart()) )

        if feat.geometry().isMultipart():
            #ToDo Explode MultiPartGeometries
            subGeoms=self.multiPartToSinglePartGeom( feat.geometry() )
            #split feature in sub features
            for gSub in subGeoms:
                subFeat=QgsFeature( feat)
                subFeat.setGeometry( gSub )
                subFeat.setAttributes( feat.attributes() )
                featureList.append(subFeat)
        else:
            featureList.append( feat )
        
        return featureList
    
    #returns a list of sub geometries
    def multiPartToSinglePartGeom(self, geom):
        #self.feedback.pushInfo( "geom: " + str( geom.asWkt()) +" type: "+ str(geom.type()) +" wkbtype: "+ str(geom.wkbType()) )

        if geom.isMultipart():
            subGeoms = None #[QgsGeometry, QgsGeometry,..]
            if geom.type() == 2: #Polygon
                subGeoms = self.multiPolygonToSinglePolygons(geom) 
            elif geom.type() == 1: #Line
                subGeoms = self.multiLineToSingleLines(geom) 
            elif geom.type() == 0: #Point
                subGeoms = self.multiLineToSingleLines(geom) 
            return subGeoms
        else:
            return [geom] # Is still a single geometry in a Array
            

    def multiPolygonToSinglePolygons(self, geom):
        multiGeom = geom.asMultiPolygon()
        singleGeoms=[]
        #Schleife zum Auflösen des Multiparts
        for polygon in multiGeom:
            polyPoints=[]
            iRing=0
            for ring in polygon:
                points=[]
                for pxy in ring:
                   #self.feedback.pushInfo(str(iMulti)+" "+str(iRing)+" "+str(pxy) + " " + str(type(pxy)))
                   points.append(QgsPointXY(pxy.x(), pxy.y()))
                #singleLineRing=QgsGeometry().fromPolyline(points)
                polyPoints.append(points)
            singlePolygon=QgsGeometry().fromPolygonXY( polyPoints )          
            singleGeoms.append( singlePolygon )
            iRing=iRing+1
        return singleGeoms

    def multiLineToSingleLines(self, geom):
        multiGeom = geom.asMultiPolyline()
        #self.feedback.pushInfo( "multiGeom: " + str( multiGeom) )
        singleGeoms=[]
        #Schleife zum Auflösen des Multiparts
        for line in multiGeom:
            points=[]
            for pxy in line:
               points.append(QgsPoint(pxy.x(), pxy.y()))
            singleLine=QgsGeometry().fromPolyline(points)
            singleGeoms.append( singleLine )

        return singleGeoms

    def multipointToSinglePoint(self, geom):
        multiGeom = geom.asMultiPolygon()
        singleGeoms=[]
        #Schleife zum Auflösen des Multiparts
        points=[]

        for point in multiGeom:
            pxy=QgsGeometry().fromPointXY(QgsPoint(point.x(), point.y()))
            singleGeoms.append( pxy )

        return singleGeoms