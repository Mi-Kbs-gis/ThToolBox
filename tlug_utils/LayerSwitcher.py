# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 A QGIS plugin
 TLUG Algorithms
                              -------------------
        begin                : 2017-10-25
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
__date__ = '2018-07-31'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtCore import QObject
from osgeo import ogr
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import *


class LayerSwitcher(QObject):
    
    def __init__(self, mapLayers, layerZFields, laengsProfil, terrain, crs): #QgsVectorLayer, QgsLinestringZ
        if len(mapLayers)==len(layerZFields):
            self.mapLayers=mapLayers
            self.profilLayers=[]
            self.baseLineAsProfilLayer=None
            self.laengsProfil=laengsProfil
            self.terrain=terrain #TerrainModel
            self.layerZFieldIds=layerZFields #[]
            self.bohrPunktSetting=None #BohrpunktSettings()
            self.crsProfil=crs
        else:
            print("Layeranzahl und Definition der Z-Felder stimmen nicht ueberein!")
            raise Exception()
            

    def setBohrPunktSetting(self, bohrpunktSetting): #BohrpunktSettings() Objekt
        self.bohrPunktSetting=bohrpunktSetting
    # check if the layer is a line layer
    def isLineType(self, vectorLayer):
        if vectorLayer.wkbType()==2 or vectorLayer.wkbType()==1002 or vectorLayer.wkbType()==2002 or vectorLayer.wkbType()==3002 or vectorLayer.wkbType()==5 or vectorLayer.wkbType()==1005 or vectorLayer.wkbType()==2005 or vectorLayer.wkbType()==3005:
            return True
        else:
            return False
    # check if the layer is a polygon layer
    def isPolygonType(self, vectorLayer):
        if vectorLayer.wkbType()==3 or vectorLayer.wkbType()==1003 or vectorLayer.wkbType()==2003 or vectorLayer.wkbType()==3003 or vectorLayer.wkbType()==6 or vectorLayer.wkbType()==1006 or vectorLayer.wkbType()==2006 or vectorLayer.wkbType()==3006:
            return True
        else:
            return False
        
    
    def getSchnittpunkteAusLinien(self, overlapFeats):
        #linesOfProfil = self.extractLineSegments(self.laengsProfil.srcProfilLine)
        schnittpunktFeatures=[]
        ioFeat=0
        countPoints=0
        for feat in overlapFeats:
            #Feature bekommr neues Attribut Station
            if ioFeat==0:
                fields=feat.fields()
                fields.append(QgsField("station", QVariant.Double))
            
            #check if Multipolygon
            if feat.geometry().isMultipart: #feat.geometry().wkbType()==5 or feat.geometry().wkbType()==1005 or feat.geometry().wkbType()==2005 or feat.geometry().wkbType()==3005:
                #for polygon in feat:  ############## Achtung normalerweise wird diese Schleife zum Auflösen des Multiparts benoetigt
                #    print(type(polygon))
                linesOfPolygon = self.extractLineSegments(feat.geometry())#polygon)
                #print("Polyline", len(linesOfPolygon),"Segments")
                intersections = {}
                
                for lineP in linesOfPolygon:
                    #hole alle Schnittpunkte
                    #print("Test1", self.laengsProfil.linearRef.profilLine3d.asWkt())
                    intersectionPoints, stations=self.laengsProfil.linearRef.getIntersectionPointofPolyLine(lineP)
                    if not intersectionPoints is None:
                        #zaehle Schnittpunkte
                        countPoints=countPoints+len(intersectionPoints)
                        if not intersectionPoints is None:
                            for i in range(len(intersectionPoints)):
                                intersections[stations[i]]=intersectionPoints[i]
                                pt=intersectionPoints[i].asPoint()
                                #print(pt.x(), pt.y())
                                
                                schnittPunktFeat=QgsFeature(feat)#Copy of the Feature
                                schnittPunktFeat.setGeometry(intersectionPoints[i])
                                attrs=feat.attributes()
                                attrs.append(stations[i]) # station wird in Attributen gespeichert
                                schnittPunktFeat.setAttributes(feat.attributes())                               
                                schnittpunktFeatures.append(schnittPunktFeat)
            
            else: # other geometry type
                linesOfPolygon = self.extractLineSegments(feat.geometry())
            ioFeat=ioFeat+1
        print("Schneidende Linien",ioFeat,"Schnittpunkte:", countPoints)
        return schnittpunktFeatures
        
    def getSchnittpunkteAusPolygonen(self, overlapFeats):
        #linesOfProfil = self.extractLineSegments(self.laengsProfil.srcProfilLine)
        #print("getSchnittpunkteAusPolygonen")
        schnittpunktFeatures=[]
        ioFeat=0
        countPoints=0
        fields=None
        for feat in overlapFeats:
            if ioFeat==0:
                fields=feat.fields()
                fields.append(QgsField("station", QVariant.Double))
            #check if Multipolygon
            #if feat.geometry().isMultipart: #feat.geometry().wkbType()==5 or feat.geometry().wkbType()==1005 or feat.geometry().wkbType()==2005 or feat.geometry().wkbType()==3005:
            #for polygon in feat:  ############## Achtung normalerweise wird diese Schleife zum Auflösen des Multiparts benoetigt
            #    print(type(polygon))
            linesOfPolygon = self.extractLineSegments(feat.geometry())#polygon)
            print("Polygon", len(linesOfPolygon),"Segments")
            intersections = {}
            
            for lineP in linesOfPolygon:
                #print("linePolygon",lineP)
                #hole alle Schnittpunkte
                intersectionPoints, stations=self.laengsProfil.linearRef.getIntersectionPointofPolyLine(lineP)
                if not intersectionPoints is None:
                    #zaehle Schnittpunkte
                    countPoints=countPoints+len(intersectionPoints)
                    for i in range(len(intersectionPoints)):
                        intersections[stations[i]]=intersectionPoints[i]
                        #print(intersectionPoints[i].wkbType())
                        #print("Schnittpunkt",i,intersectionPoints[i].asWkt())
                        schnittPunktFeat=QgsFeature(feat)#Copy of the Feature
                        schnittPunktFeat.setGeometry(intersectionPoints[i])
                        attrs=feat.attributes()
                        attrs.append(stations[i]) # station wird in Attributen gespeichert
                        schnittPunktFeat.setAttributes(feat.attributes())
                        schnittpunktFeatures.append(schnittPunktFeat)
            print("Polygon mit ",len(linesOfPolygon), " Segmenten auf Schnittpunkte untersucht")
            #else: # other geometry type
            #    linesOfPolygon = self.extractLineSegments(feat.geometry())
            #print("bevor Break bei Feature",ioFeat, "von"))
            #break
            ioFeat=ioFeat+1
        print("Schneidende Polygone:",ioFeat,"Schnittpunkte:", countPoints)
        return schnittpunktFeatures
        
    def transformBaseLineToProfil(self, zFactor):
            #Erzeuge Profilgeometrien als Linie
            print("Verarbeite BasisLinie")
            # create layer
            profilLayer= QgsVectorLayer("LineString", "Laengsprofil", "memory")
            pr = profilLayer.dataProvider()

            # add fields
            fields=[QgsField("id",  QVariant.Int),QgsField("name", QVariant.String)]
            pr.addAttributes(fields)
                                # ),
                                # QgsField("size", QVariant.Double)])
            profilLayer.updateFields() # tell the vector layer to fetch changes from the provider
            #protokoll=[]
            #Erzeuge LinienGeometry des Laengsprofils
            i=0
            profilLinePoints=[]
            curStation=0
            prePointIndex=0
            curPointIndex=0
            lastPoint=self.laengsProfil.profilLine3d.vertexAt(0)
            for pointGeom in self.laengsProfil.profilLine3d.vertices():
                #curPoint=self.laengsProfil.profilLine3d.vertexAt(curPointIndex)
                #prePoint=self.laengsProfil.profilLine3d.vertexAt(prePointIndex)
                
                #Station des Punktes im Profil wir berechnet
                station=self.laengsProfil.linearRef.punktEntfernung2D(pointGeom, lastPoint)
                curStation=curStation + station
                
                #protokoll.append("cur: "+str(curStation) + " station: " + str(curStation))
                #print(pointGeom.asWkt(), curPoint.asWkt(), prePoint.asWkt(),"-->",curStation, pointGeom.z() * zFactor)
                #profilLinePoints.append(QgsPointXY(curStation, pointGeom.z() * zFactor))
                #print(pointGeom, lastPoint,curStation, pointGeom.z(),pointGeom.asWkt())
                profilLinePoints.append(QgsPointXY(curStation, pointGeom.z() * zFactor))
                #curPointIndex=curPointIndex + 1
                #prePointIndex=curPointIndex - 1
                lastPoint=pointGeom
                i=i+1
            #print(profilLinePoints, type(profilLinePoints))
            #Erzeuge Feature
            profilFeat = QgsFeature()#fields)   
            #profilFeat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(0,90),QgsPointXY(11,135),QgsPointXY(26,50)]))
            profilFeat.setGeometry(QgsGeometry.fromPolylineXY(profilLinePoints))
            profilFeat.setAttributes([0,"BaseLine"])


            
            
            
            pr.addFeatures([profilFeat])

            # update layer's extent when new features have been added
            # because change of extent in provider is not propagated to the layer
            profilLayer.updateExtents()
            #add new Layer to Layerset
            self.baseLineAsProfilLayer=profilLayer
            #for txt in protokoll:
            #    print(txt)
            
    def transformLayerToProfil(self, bufferWidth, zFactor): #zFactor=Ueberhoehung
        i=0
        for srcLayer in self.mapLayers:
            print("Verarbeite Layer", srcLayer.name(), srcLayer.featureCount(), "Objekte")
            #iter = srcLayer.getFeatures()
            
            
            #ermittle Kanditaten featuresOnLine=[]
            featuresOnLine=self.laengsProfil.linearRef.getFeaturesOnBaseLine(srcLayer, bufferWidth) #100 m
            #Falls Linien oder Polygone, dann ermittle Schnittpunkte mit Laengsprofil
            print("Erzeuge Schnittpunkt-Features")
            #Erzeuge Schnittpunkt-Features
            schnittpunkte=[] #Liste von Features
            if self.isLineType(srcLayer):
                print("isLineType")
                schnittpunkte=self.getSchnittpunkteAusLinien(featuresOnLine) #Um Attribute der geschnittenen Objekte zu uebernehmen, muss hier mehr uebergeben werden
            elif self.isPolygonType(srcLayer):
                schnittpunkte=self.getSchnittpunkteAusPolygonen(featuresOnLine)
                print("isPolygonType")
            else:
                schnittpunkte=featuresOnLine
                
            # for feat in schnittpunkte:
                # print(feat.geometry().asWkt())
            
            
            #Berechne Z-Werte
            featuresWithZ=self.terrain.addZtoPointFeatures(schnittpunkte,self.layerZFieldIds[i])
            
            #Erzeuge Profilgeometrien gehr derzeit nur als Punkt
            profilFeatures=[]
            for srcFeat in featuresWithZ:
                srcGeom=srcFeat.geometry()
                #print("pointsWithZ", srcFeat.attributes(), srcGeom.asWkt())
                profilGeometries=self.extractProfilGeom(srcGeom, zFactor, self.laengsProfil.srcProfilLine)
                for profilGeom in profilGeometries:
                    profilFeat = QgsFeature(srcLayer.fields())   
                    #muss fuer jeden Geometrityp gehen
                    profilFeat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(profilGeom.x(),profilGeom.y())))
                    profilFeat.setAttributes(srcFeat.attributes())
                    #print("ProfilFeature",srcFeat.attributes(),profilGeom.asWkt())
                    profilFeatures.append(profilFeat)
            
            print(srcLayer.name()+"_profil",len(profilFeatures), "Objekte in Profil")

            # create layer
            profilLayer= QgsVectorLayer("Point", srcLayer.name()+"_profil", "memory")
            pr = profilLayer.dataProvider()

            # add fields
            pr.addAttributes(srcLayer.fields())
            # pr.addAttributes([QgsField("name", QVariant.String),
                                # QgsField("age",  QVariant.Int),
                                # QgsField("size", QVariant.Double)])
            profilLayer.updateFields() # tell the vector layer to fetch changes from the provider

            pr.addFeatures(profilFeatures)

            # update layer's extent when new features have been added
            # because change of extent in provider is not propagated to the layer
            profilLayer.updateExtents()
            #add new Layer to Layerset
            self.profilLayers.append(profilLayer)
            i=i+1

    def transformBohrpunkteToProfil(self, bufferWidth, zFactor): #zFactor=Ueberhoehung
        i=0
        #self.bohrPunktLayer
        print("Verarbeite Layer", self.bohrPunktSetting.bohrPunktLayer.name(), " als Bohrpunkt-Layer", self.bohrPunktSetting.bohrPunktLayer.featureCount(), "Objekte")
        #iter = srcLayer.getFeatures()
        
        
        #ermittle Kanditaten featuresOnLine=[]
        featuresOnLine=self.laengsProfil.linearRef.getFeaturesOnBaseLine(self.bohrPunktSetting.bohrPunktLayer, bufferWidth) #100 m
        #Falls Linien oder Polygone, dann ermittle Schnittpunkte mit Laengsprofil

        # for feat in schnittpunkte:
            # print(feat.geometry().asWkt())
        
        
        #Berechne Z-Werte
        featuresWithZ=self.terrain.addZtoPointFeatures(featuresOnLine,self.layerZFieldIds[i])
        
        # BohrpunktSettings(QObject):

        # self.bohrPunktSetting
        # self.IndexBohrPunktLayerFieldZ=-1
        # self.indexFieldtiefeOK=-1
        # self.indexFieldtiefeUK=-1
        # self.fieldIndexRichtungHz=-1
        # self.fieldIndexAzimut=-1
        
        print("Z", self.bohrPunktSetting.IndexBohrPunktLayerFieldZ)
        print("tVon", self.bohrPunktSetting.indexFieldtiefeOK)
        print("tBis", self.bohrPunktSetting.indexFieldtiefeUK)
        print("rHz",self.bohrPunktSetting.fieldIndexRichtungHz)
        print("az", self.bohrPunktSetting.fieldIndexAzimut)
        
        #Erzeuge Profilgeometrien fuer Bohrpunkte
        profilFeatures=[]
        for srcFeat in featuresWithZ:
            srcGeom=srcFeat.geometry()
            #berechne 3D Linie fuer einzelne Schicht
            tVon=srcFeat[self.bohrPunktSetting.indexFieldtiefeOK]
            tBis=srcFeat[self.bohrPunktSetting.indexFieldtiefeUK]
            #rHz=0
            #az=0
            if self.bohrPunktSetting.fieldIndexRichtungHz==-1 or self.bohrPunktSetting.fieldIndexAzimut==-1:
                rHz=0
                az=math.pi #Winkel schaut zum Nadir
            else:
                rHz=srcFeat[self.bohrPunktSetting.fieldIndexRichtungHz]
                az=srcFeat[self.bohrPunktSetting.fieldIndexAzimut]
                #if rHz is None
            #erzeuge 3D-Linie fuer den Bohraufschluss
            line3D=self.createBohrungSchichtLineGeometry(srcGeom.vertexAt(0), tVon, tBis, rHz, az)
            
            #print("line3D", line3D.asWkt())#,srcFeat.attributes(),)
            profilGeometries=self.extractProfilGeom(line3D, zFactor, self.laengsProfil.srcProfilLine)
            for profilGeom in profilGeometries:
                profilFeat = QgsFeature(self.bohrPunktSetting.bohrPunktLayer.fields())   
                #muss fuer jeden Geometrityp gehen
                profilFeat.setGeometry(profilGeom)
                profilFeat.setAttributes(srcFeat.attributes())
                #print("ProfilFeature",srcFeat.attributes(),profilGeom.asWkt())
                profilFeatures.append(profilFeat)
        
        print(self.bohrPunktSetting.bohrPunktLayer.name()+"_profil",len(profilFeatures), "Objekte in Profil")

        # create layer
        profilLayer= QgsVectorLayer("LineString?crs=epsg:"+str(self.crsProfil.authid()), self.bohrPunktSetting.bohrPunktLayer.name()+"_profil", "memory")
        pr = profilLayer.dataProvider()

        # add fields
        pr.addAttributes(self.bohrPunktSetting.bohrPunktLayer.fields())
        # pr.addAttributes([QgsField("name", QVariant.String),
                            # QgsField("age",  QVariant.Int),
                            # QgsField("size", QVariant.Double)])
        profilLayer.updateFields() # tell the vector layer to fetch changes from the provider

        pr.addFeatures(profilFeatures)

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        profilLayer.updateExtents()
        #add new Layer to Layerset
        self.profilLayers.append(profilLayer)
        i=i+1

    def createBohrungSchichtLineGeometry(self, position, tiefeVon, tiefeBis, richtungHz, azimut):
        pVon=self.polarerAnhaenger3D(position,  tiefeVon, richtungHz, azimut)
        pBis=self.polarerAnhaenger3D(position,  tiefeBis, richtungHz, azimut)
        lineZ=QgsGeometry.fromPolyline([pVon, pBis])
        return lineZ

    def polarerAnhaenger3D(self, position, schraegStrecke, richtungHz, azimut):
        print(position, schraegStrecke, richtungHz, azimut)
        #richtungRAD=richtungHz * math.pi/180
        #azimutRAD=azimut * math.pi/180
        #print("HZrad", richtungRAD,"azRad", azimutRAD)
        entfernung2D=float(math.sin(azimut)) * float(schraegStrecke) ##?
        deltaZ=float(math.cos(azimut)) * float(schraegStrecke)# *-1
        richtungswinkel2D=richtungHz #??
        deltaX=float(math.sin(richtungswinkel2D)) * entfernung2D
        deltaY=float(math.cos(richtungswinkel2D)) * entfernung2D
        
        xZiel=position.x() + deltaX
        yZiel=position.y() + deltaY
        zZiel=position.z() + deltaZ
        #print("polarerAnhaenger3D", position, schraegStrecke, math.sin(azimut), entfernung2D, richtungHz, azimut, deltaX, deltaY, deltaZ)
        
        return QgsPoint(round(xZiel,2), round(yZiel,2), round(zZiel,2))
    
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
                        station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
                        if not station is None and not abstand is None:
                            ptProfil=QgsPoint(station, pxy.z() * zFactor)
                            #print("Profil", ptProfil.x(), ptProfil.y())
                            points.append(ptProfil)
                    geometries.append(QgsGeometry().fromPoint(points))
            else:
                pxy=geom.vertexAt(0)
                #print(geom.wkbType(),"alt",geom.asWkt())
                station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
                if not station is None and not abstand is None:
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    #print("Profil", ptProfil.x(), ptProfil.y())
                    geometries.append(ptProfil)
        elif "Line" in geom.asWkt(): #geom.type()==2: # Line
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    points=[]
                    for elem in i:
                        pxy=elem.asPoint()
                        station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
                    
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        print(pxy,"-m->", ptProfil.asWkt())
                        points.append(ptProfil)
                    prLine=QgsGeometry().fromPolyline(points)
                    geometries.append(prLine)
                    print("profilGeom", prLine.asWkt())   
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
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
                        station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPolygon(points))
            else:# Single Feature
                points=[]
                for pxy in geom.vertices():
                    station, abstand=self.laengsProfil.linearRef.transformToLineCoords(pxy)
                    ptProfil=QgsPoint(station, pxy.z() * zFactor)
                    points.append(QgsPoint(pxy.x(), pxy.y()))
                geometries.append(QgsGeometry().fromPolygon(points))
        else:
            print("def extractProfilGeom: Geometrietyp", geom.type(),geom.wkbType(),geom.asWkt(), "nicht zugeordnet")
        #print("Single:", len(geometries), "Geometrien")
        
        return geometries

    #extraiere Linienseqmente
    def extractLineSegments(self, geom):
        points=self.getVertices(geom)
        #create the lines
        lines=[]
        i=0 # Line number
        while i < len(points)-1:
            p1=points[i]
            p2=points[i+1]
            lineGeom=QgsGeometry.fromPolyline([p1,p2])
            lines.append(lineGeom)
            i=i+1
        return lines

    #liefert die Stuetzpunkte einer Single-Geometrie
    def getVertices(self, geom):
        v_iter = geom.vertices()
        points=[]

        while v_iter.hasNext():
            pt = v_iter.next()
            points.append(pt)
            #print(pt.x(), pt.y())
        return points       
    
    def extractAsSingle(self, geom):
        multiGeom = QgsGeometry()
        geometries = []
        print(geom.type(),geom.wkbType(), QgsWkbTypes.MultiLineString)
        if geom.wkbType() ==  QgsWkbTypes.MultiPoint :
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPoint(i))
            else:
                geometries.append(geom)
        elif geom.wkbType() == QgsWkbTypes.MultiLineString:
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPolyline(points))
            else:
                geometries.append(geom)
        elif geom.wkbType() == QgsWkbTypes.MultiPolygon :
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    geometries.append(QgsGeometry().fromPolygon(i))
            else:
                geometries.append(geom)
        print("Single:", len(geometries), "Geometrien")
        
        return geometries    