# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 LaengsProfil
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
__date__ = '2018-08-08'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

from qgis.PyQt.QtCore import QObject
from qgis.core import *
from qgis.core import QgsGeometry, QgsFeature,QgsPoint, QgsPointXY
import math
from .LinearReferencingMaschine import LinearReferencingMaschine


class LaengsProfil(QObject):
    
    def __init__(self, srcProfilLine, terrainModel, crsProject, feedback):
        self.feedback=feedback
        self.srcProfilLine=srcProfilLine
        isMulti=self.srcProfilLine.isMultipart
        self.terrainModel=terrainModel
        self.crsProject=crsProject #Projekt.crsProject == srcProfilLine.crsProject!
        #init Linear Referencing
        self.linearRef=LinearReferencingMaschine(srcProfilLine, crsProject, self.feedback)
        self.detailedProfilLine=None
        self.profilLine3d=None
    #Erstellt eine Polyline mit Z-Werten in Rasterauflösung
    def calc3DProfile(self):

        #insert new vertices on raster cells
        self.detailedProfilLine=self.linearRef.verdichtePunkte(self.terrainModel.rasterWidth)
        #sample values from Rasters
        points3D = self.terrainModel.addZtoPoints(self.detailedProfilLine.vertices(), self.crsProject)
        #Create Geometry
        profilLine3d=QgsGeometry.fromPolyline(points3D)
        #self.feedback.pushInfo( profilLine3d.asWkt() )
        self.profilLine3d = profilLine3d
        return profilLine3d

        
    #Diese Funktion uebersetzt eine Geometrie in eine ProfilGeometrie, an Hand von Z-Koorinaten und eine Basislinie(X-Achse)
    def extractProfilGeom(self, geom, zFactor, baseLine):
        #print("extractProfilGeom for", geom.asWkt())
        multiGeom = QgsGeometry()
        geometries = []
        wkb=geom.asWkb() 
        #Umwandeln in OGR-Geometry um auf Z.Kooridnate zuzugreifen
        #geom_ogr = ogr.CreateGeometryFromWkb(wkb)
        #print(geom.type(),geom.wkbType())#, str(ogr.GetGeometryType()))
        if "Point" in geom.asWkt(): #geom.type()==1: #Point
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        #print("alt", pxy.x(), pxy.y(), pxy.z())
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                        if not station is None and not abstand is None:
                            ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                            #print("Profil", ptProfil.x(), ptProfil.y())
                            points.append(ptProfil)
                    geometries.append(QgsGeometry().fromPointXY(points))
            else:
                pxy=geom.vertexAt(0)
                #print(geom.wkbType(),"alt",geom.asWkt())
                station, abstand=self.linearRef.transformToLineCoords(pxy)
                if not station is None and not abstand is None:
                    ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                    #print("Profil", ptProfil.x(), ptProfil.y())
                    geometries.append(QgsGeometry().fromPointXY(ptProfil))
        elif "Line" in geom.asWkt(): #geom.type()==2: # Line
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    points=[]
                    for elem in i:
                        pxy=elem.asPoint()
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                        if not station is None and not abstand is None:
                            ptProfil=QgsPoint(station, pxy.z() * zFactor)
                            #print(pxy,"-m->", ptProfil.asWkt())
                            points.append(ptProfil)
                    prLine=QgsGeometry().fromPolyline(points)
                    geometries.append(prLine)
                    #print("profilGeom", prLine.asWkt())   
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.linearRef.transformToLineCoords(pxy)
                    if not station is None and not abstand is None:
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        #print(pxy,"-s->", ptProfil.asWkt())
                        points.append(ptProfil)
                    else:
                        self.feedback.reportError( "Point " + str( pxy ) + " Profile Coords invalid: " + str(station) +", " +str(abstand) )
                prLine=QgsGeometry().fromPolyline(points)
                geometries.append(prLine)
                #print("profilGeom", prLine.asWkt())
    
        elif "Polygon" in geom.asWkt(): # geom.type()==3: # Polygon
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        station, abstand=self.linearRef.transformToLineCoords(pxy)
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPolygon([points]))
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.linearRef.transformToLineCoords(pxy)
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    points.append(QgsPoint(pxy.x(), pxy.y()))
                geometries.append(QgsGeometry().fromPolygon([points]))
        else:
            print("def extractProfilGeom: Geometrietyp", geom.type(),geom.wkbType(),geom.asWkt(), "nicht zugeordnet")
        #print("Single:", len(geometries), "Geometrien")
        
        return geometries

    #entfernt Bereiche einer Profilline, die keine validen Werte enthält        
    def getCleanGradient(self, baseLineFeature, zFactor, noDataValue, use_nodata, use_zerodata, use_negativeData): 
    
        cleanLines=[]
        #Erzeuge LinienGeometry des Laengsprofils
        i=0
        profilLinePoints=[]
        curStation=0
        lastStation=0
        prePointIndex=0
        curPointIndex=0
        lastPoint=self.profilLine3d.vertexAt(0)
        lastPointValid=True
        curPointValid=True
        for pointGeom in self.profilLine3d.vertices():
           
            #Station des Punktes im Profil wir berechnet
            iStation=round( self.linearRef.punktEntfernung2D(pointGeom, lastPoint), 3)
            curStation=curStation + iStation

            zY = round(pointGeom.z(),2) * zFactor

            # check if z value is a NULL-Value           
            if use_zerodata == False and pointGeom.z()==0 or use_nodata == False and pointGeom.z()==noDataValue or use_negativeData==False and pointGeom.z()<0:
                #lastPointValid=False
                curPointValid=False
                # check if the point list has valid points
                if lastPointValid==True: 
                    if len(profilLinePoints) == 1:
                        #we need 2 Points to creat a line, now we make a pseudo point
                        lastStation
                        avgX=(lastStation+curStation)/2
                        lastZ=round(lastPoint.z(),2) * zFactor
                        self.feedback.pushInfo('Just one Point on this line part:' + str(lastStation) + ' ' + str(lastZ))
                        self.feedback.pushInfo('additional point created:' + str(avgX) + ' ' + str(lastZ))
                        profilLinePoints.append(QgsPointXY(avgX, lastZ))
                
                    if len(profilLinePoints) > 1: # Must be more than one point to make a valid line
                        #Create Feature for separate line part
                        profilFeat = QgsFeature(baseLineFeature.fields())   
                        profilFeat.setGeometry(QgsGeometry.fromPolylineXY( profilLinePoints ))
                        profilFeat.setAttributes( baseLineFeature.attributes() )
                        # Add a feature in the list
                        cleanLines.append(profilFeat)
                    profilLinePoints.clear()
                    
            
            else:  #add new vertex in Profil coordinates
                curPointValid=True
                profilLinePoints.append(QgsPointXY(curStation, zY ))

            lastPoint=pointGeom
            lastStation=curStation
            i=i+1
            lastPointValid=curPointValid

                   
        if len(profilLinePoints) > 1: # Must be more than one point to make a valid line
            #Create Feature
            profilFeat = QgsFeature(baseLineFeature.fields())   
            profilFeat.setGeometry(QgsGeometry.fromPolylineXY(profilLinePoints))
            profilFeat.setAttributes(baseLineFeature.attributes())
            # Add a feature in the list
            cleanLines.append(profilFeat)
    
        return cleanLines
    
    # Calucates the normal vectors of the profile baslines vertikal planes
    def get3DPlanesNormales(self):
        lastPoint=self.profilLine3d.vertexAt(0)
        planesNormals = [] #  [[x0,y0,z0], [x1,y1,z1],[..., ..., ...] ]
        for i,pointGeom in enumerate(self.profilLine3d.vertices()):
            if i>0:
                x0i = lastPoint.x()
                x1i = pointGeom.x()
                y0i = lastPoint.y()
                y1i = pointGeom.y()
                
                deltaX = x1i-x0i
                deltaY = y1i-y0i
                
                #create a rectangular vektor 
                #swap x/y of the base vector and multiply one of them with -1
                normalX = deltaY
                normalY = -deltaX
                normalZ = 0 # the Z-direction of the normal is always horizontal
                normal = [normalX, normalY, normalZ]
                planes.append( normal )
            
        return planesNormals
        
