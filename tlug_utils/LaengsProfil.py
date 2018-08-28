# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 LaengsProfil
 TLUG Algorithms
                              -------------------
        begin                : 2018-08-27
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Michael Kürbs'
__date__ = '2018-08-08'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

from qgis.PyQt.QtCore import QObject
from qgis.core import *
from qgis.core import QgsGeometry, QgsFeature,QgsPoint
import math
from .LinearReferencingMaschine import LinearReferencingMaschine


class LaengsProfil(QObject):
    
    def __init__(self, srcProfilLine, terrainModel, crsProject, feedback):
        self.feedback=feedback
        self.srcProfilLine=srcProfilLine
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
        points3D=self.terrainModel.addZtoPoints(self.detailedProfilLine.vertices(), self.crsProject)
        #Create Geometry
        profilLine3d=QgsGeometry.fromPolyline(points3D)
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
                    
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        print(pxy,"-m->", ptProfil.asWkt())
                        points.append(ptProfil)
                    prLine=QgsGeometry().fromPolyline(points)
                    geometries.append(prLine)
                    print("profilGeom", prLine.asWkt())   
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.linearRef.transformToLineCoords(pxy)
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    print(pxy,"-s->", ptProfil.asWkt())
                    points.append(ptProfil)
                prLine=QgsGeometry().fromPolyline(points)
                geometries.append(prLine)
                print("profilGeom", prLine.asWkt())
    
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