# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 TransformToProfil_Points
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
__date__ = '2018-10-08'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from PyQt5 import QtGui
from PyQt5.QtCore import QCoreApplication, QVariant#, ZeroDivisionError
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProject,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsWkbTypes,
                       QgsProcessingException)
from .tlug_utils.TerrainModel import TerrainModel
from .tlug_utils.LaengsProfil import LaengsProfil
import math
from .tlug_utils.ProfilItem import ProfilItem

class TransformToProfil_Points(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUTBASELINE = 'INPUTVECTOR'
    INPUTRASTER = 'INPUTRASTER'
    INPUTZFACTOR='INPUTZFACTOR'
    INPUTBUFFER='INPUTBUFFER'
    INPUTPOINTLAYER='INPUTPOINTLAYER'
    INPUTZFIELDSTART='INPUTZFIELDSTART'
    INPUTZFIELDEND='INPUTZFIELDEND'
    INPUTZFIELD='INPUTZFIELD'


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        #print("initAlgorithm")
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTPOINTLAYER,
                self.tr('Point Layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE,
                self.tr('Profil Baseline'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUTBUFFER,
                self.tr('Baseline Buffer(used if no points selection)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=100,
                optional=False,
                minValue=0,
                maxValue=10000
                
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUTRASTER,
                self.tr('Elevation Raster'),
                None, 
                False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUTZFACTOR,
                self.tr('Z-Factor / Ueberhoehung'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10,
                optional=False,
                minValue=0,
                maxValue=100
                
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUTZFIELD,
                self.tr('Z-Value Field'),
                None,
                self.INPUTPOINTLAYER,
                QgsProcessingParameterField.Numeric,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUTZFIELDSTART,
                self.tr('Depth (Start)'),
                None,
                self.INPUTPOINTLAYER,
                QgsProcessingParameterField.Numeric,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUTZFIELDEND,
                self.tr('Depth Field (End)'),
                None,
                self.INPUTPOINTLAYER,
                QgsProcessingParameterField.Numeric,
                optional=True
            )
        )


        #fieldRichtungHz
        #fieldAzimut


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Profil_Points')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsDouble(parameters, self.INPUTZFACTOR, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        pointLayer =  self.parameterAsVectorLayer(parameters, self.INPUTPOINTLAYER, context)
        zFieldName =  self.parameterAsString(parameters, self.INPUTZFIELD, context)
        startZFieldName = self.parameterAsString(parameters, self.INPUTZFIELDSTART, context)
        endZFieldName = self.parameterAsString(parameters, self.INPUTZFIELDEND, context)
        #fieldRichtungHz = self.parameterAsString(parameters, self.INPUTFIELDXXX, context)
        #fieldAzimut = self.parameterAsString(parameters, self.INPUTFIELDXXX, context)
        bufferWidth = self.parameterAsDouble(parameters, self.INPUTBUFFER, context)

        baseLine=None
        #Basline Layer must have only 1 Feature
        if baseLineLayer.featureCount()==1:
        #baseLine must be the first feature
            baseLineFeature=next(baseLineLayer.getFeatures(QgsFeatureRequest().setLimit(1)))
            baseLine=baseLineFeature.geometry()
        elif len(baseLineLayer.selectedFeatures())==1:
            selection=baseLineLayer.selectedFeatures()
            #baseLine must be the first feature
            selFeats=[f for f in selection]
            baseLineFeature=selFeats[0]
            baseLine=baseLineFeature.geometry() 
        else:
            msg = self.tr("Error: BaseLine layer needs exactly one line feature! " + str(baseLineLayer.featureCount()) + " Just select one feature!")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)


        #take CRS from Project

        crsProject=QgsProject.instance().crs()       #rasterLayer.crs()    
        #check if layers have the same crs
        if not baseLineLayer.crs().authid()==crsProject.authid():
            # if not, transform to raster crs()
            trafo1=QgsCoordinateTransform(baseLineLayer.crs(),crsProject,QgsProject.instance())
            #transform BaseLine
            opResult1=baseLine.transform(trafo1,QgsCoordinateTransform.ForwardTransform, False)
        # if not pointLayer.crs().authid()==crsProject.authid():
            # # if not, transform to raster crs()
            # trafo2=QgsCoordinateTransform(pointLayer.crs(), crsProject,QgsProject.instance())
            # #transform BaseLine
            # opResult2=baseLine.transform(trafo2,QgsCoordinateTransform.ForwardTransform, False)

        layerZFieldId=-1
        #init Terrain
        tm = TerrainModel(rasterLayer, feedback)
        #init LaengsProfil
        lp = LaengsProfil(baseLine, tm, crsProject, feedback)
        


#        if self.isPointType(pointLayer):
        #get candidates 
        featuresOnLine=[]       

        #check Selection of Pointlayer
        #if yes, use just the selection
        if len(pointLayer.selectedFeatures()) == 0:
            featuresOnLine=lp.linearRef.getFeaturesOnBaseLine(pointLayer, bufferWidth)
        else:
            featuresOnLine = pointLayer.selectedFeatures() # Buffer would be ignored

        #Handling of the Z-Values of the input points
        featuresWithZ=[]
        modus=-1
        #Field with Z-Values
        fidxZ=-1

        if zFieldName:
            #feedback.pushInfo("1 self.hasZGeometries(pointLayer):"+str(self.hasZGeometries(pointLayer, feedback)))
            if self.hasZGeometries(pointLayer, feedback) == True:
                reply = QMessageBox.question(self.iface.mainWindow(), 'Continue?', 
                                 'Overide Z by field ' + zFieldName, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    modus=1
                else:
                    modus=3
            else:
                modus=1
        else:
            #feedback.pushInfo("2 self.hasZGeometries(pointLayer):"+str(self.hasZGeometries(pointLayer, feedback)))
            if self.hasZGeometries(pointLayer, feedback) == True:
                modus=3
            else:
                modus=2


        if modus==1:
            fidxZ = pointLayer.fields().lookupField(zFieldName)
            featuresWithZ=tm.addZtoPointFeatures(featuresOnLine, pointLayer.crs(), fidxZ)
        elif modus==2:
            fidxZ = -1
            featuresWithZ=tm.addZtoPointFeatures(featuresOnLine, pointLayer.crs(), fidxZ)
        elif modus==3:
            #Conversion from QgsFeatureiterator to a list
            featuresWithZ = [feature for feature in featuresOnLine]

        #Handling of the depth settings, make vertikal lines from depth attributes
        wkbTyp=None #Output Geometry Type
        fidx=[None, None] #Field Indizes for the Z values
        modusDepth=-1
        if endZFieldName=="" and startZFieldName=="": #No Depth
            modusDepth=1
            #keep featuresWithZ 
            wkbTyp=QgsWkbTypes.Point
        else:
            if endZFieldName and startZFieldName:
                idx1 = pointLayer.fields().lookupField(startZFieldName)
                idx2 = pointLayer.fields().lookupField(endZFieldName)
                fidx=[idx1, idx2]
                modusDepth=2
            elif endZFieldName and startZFieldName=="":
                fidx=[-1, idx2]
            elif endZFieldName=="" and startZFieldName:
                fidx=[idx1, -1]

            wkbTyp=QgsWkbTypes.LineString
            #erzeuge 3D-Linien fuer den Bohraufschluss im Project-Crs
            featuresWithZ=self.createBohrungSchichtLineFeatures(featuresWithZ, idx1, idx2, 0, math.pi, feedback)
        

        try:
            if len(featuresWithZ)>0:
                total = 100.0 / len(featuresWithZ)
            else:
                feedback.pushInfo("No features processed. May be change buffer size.")
        except: #ZeroDivisionError or Nonetype
            msg = self.tr("Keine Punkte mit Z-Werten")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        sinkFields=pointLayer.fields()

#        if wkbTyp == QgsWkbTypes.Point:
        sinkFields.append(QgsField("station", QVariant.Double))
        sinkFields.append(QgsField("abstand", QVariant.Double))
        #config Output
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
        context, sinkFields, wkbTyp, crsProject)

        # #create geometries as profil coordinates
        #profilFeatures=[]
        iNewFeatures=0
        for current, srcFeat in enumerate(featuresWithZ):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            wkb=srcFeat.geometry().asWkb()
            srcGeom=srcFeat.geometry()
            srcOrgGeom=QgsGeometry()
            srcOrgGeom.fromWkb(wkb)
            #transform srcGeom to Project.crs() if crs a different
            if not pointLayer.crs().authid()==QgsProject.instance().crs().authid():
                trafo=QgsCoordinateTransform(pointLayer.crs(), QgsProject.instance().crs(), QgsProject.instance())
                #transform clip Geom to SrcLayer.crs Reverse
                status=srcGeom.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)
            #calc profile geometry
            profilItems, isGeomOnLine = self.extractProfilGeom(srcGeom, ueberhoehung, lp, feedback)
            if isGeomOnLine == False:
                feedback.pushInfo("Feature({0}) is not orthogonal to the Base Line: ".format( srcFeat.id() ) + " " + srcGeom.asWkt())
            else:
                for profilItem in profilItems:
                    profilFeat = QgsFeature(srcFeat.fields())   
                    #muss fuer jeden Geometrityp gehen
                    profilFeat.setGeometry(profilItem.profilGeom)
                    attrs=srcFeat.attributes()
                    #add station and abstand
                    attrs.append(profilItem.station)
                    attrs.append(profilItem.abstand)
                    profilFeat.setAttributes(attrs)
                    # Add a feature in the sink
                    sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)
                    iNewFeatures=iNewFeatures+1

            # Update the progress bar
            feedback.setProgress(int(current * total))
        

        feedback.pushInfo(str(iNewFeatures) +" transformed to profile coordinates.")
        # Return the results of the algorithm. In this case our only result is
        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Points (incl. Bore Axis)'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'To Profile Coordinates'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_Points()

    # def isPointType(self, vectorLayer):
        # if vectorLayer.wkbType()==1 or vectorLayer.wkbType()==1001 or vectorLayer.wkbType()==2001 or vectorLayer.wkbType()==3001 or vectorLayer.wkbType()==4 or vectorLayer.wkbType()==1004 or vectorLayer.wkbType()==2004 or vectorLayer.wkbType()==3004:
            # return True
        # else:
            # return False

    def createBohrungSchichtLineFeatures(self, pointfeaturesWithZ, tiefeVonIdx, tiefeBisIdx, richtungHz, azimut, feedback):
        featuresWithZ=[]
        for current, srcFeat in enumerate(pointfeaturesWithZ):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            #create a Line Geometry
            if tiefeVonIdx==-1:
                tiefeVon=srcFeat.geometry().vertexAt(0).z()
            
            else:
                tiefeVon=srcFeat.attribute(tiefeVonIdx)
            if tiefeBisIdx==-1:
                tiefeBis=srcFeat.geometry().vertexAt(0).z()
            
            else:
                tiefeBis=srcFeat.attribute(tiefeVonIdx)         
            
            tiefeBis=srcFeat.attribute(tiefeBisIdx)
            #feedback.pushInfo(str(tiefeVon)+"-->"+ str(tiefeBis) +":"+ str(srcFeat.attributes()))
            inputGeom = srcFeat.geometry().vertexAt(0)
            pVon=self.polarerAnhaenger3D(inputGeom,  tiefeVon, richtungHz, azimut, feedback)
            pBis=self.polarerAnhaenger3D(inputGeom,  tiefeBis, richtungHz, azimut, feedback)
            lineZ=QgsGeometry.fromPolyline([pVon, pBis])
            zFeat=QgsFeature(srcFeat.fields())
            zFeat.setGeometry(lineZ)
            zFeat.setAttributes(srcFeat.attributes())
            featuresWithZ.append(zFeat)
        return featuresWithZ

    def polarerAnhaenger3D(self, position, schraegStrecke, richtungHz, azimut, feedback):
        #feedback.pushInfo(str(position)+" Typ:" + str(type(position)))
        #print(position, schraegStrecke, richtungHz, azimut)
        #richtungRAD=richtungHz * math.pi/180
        #azimutRAD=azimut * math.pi/180
        #print("HZrad", richtungRAD,"azRad", azimutRAD)
        entfernung2D=float(math.sin(azimut)) * float(schraegStrecke) ##?
        deltaZ=float(math.cos(azimut)) * float(schraegStrecke)# *-1
        #feedback.pushInfo(str(position.z())+" + deltaZ: "+str(deltaZ))
        richtungswinkel2D=richtungHz #??
        deltaX=float(math.sin(richtungswinkel2D)) * entfernung2D
        deltaY=float(math.cos(richtungswinkel2D)) * entfernung2D
        xZiel=position.x() + deltaX
        yZiel=position.y() + deltaY
        zZiel=position.z() + deltaZ
        #print("polarerAnhaenger3D", position, schraegStrecke, math.sin(azimut), entfernung2D, richtungHz, azimut, deltaX, deltaY, deltaZ)
        
        return QgsPoint(round(xZiel,2), round(yZiel,2), round(zZiel,2))

    #Diese Funktion uebersetzt eine Geometrie in eine ProfilGeometrie, an Hand von Z-Koorinaten und eine Basislinie(X-Achse)
    def extractProfilGeom(self, geom, zFactor, laengsProfil, feedback):
        #print("extractProfilGeom for", geom.asWkt())
        multiGeom = QgsGeometry()
        geometries = []
        profilItems=[]
        wkb=geom.asWkb() 
        isOnBaseLine=True #is set to false if a geometry is not orthogonal to the bsaeLine
        #Umwandeln in OGR-Geometry um auf Z.Kooridnate zuzugreifen
        #geom_ogr = ogr.CreateGeometryFromWkb(wkb)
        if "Point" in geom.asWkt(): #geom.type()==1: #Point
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for i in multiGeom:
                    points=[]
                    for pxy in i:
                        station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                        if not station is None and not abstand is None:
                            ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                            points.append(ptProfil)
                        else:
                            isOnBaseLine=False
                    if isOnBaseLine==True:
                        geometries.append(QgsGeometry().fromPointXY(points))
                        item=ProfilItem(geom, QgsGeometry().fromPointXY(points), station, abstand, zFactor)
                        profilItems.append(item)
            else:
                pxy=geom.vertexAt(0)
                station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                if not station is None and not abstand is None:
                    ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                    #feedback.pushInfo("Profil_Multi: "+ str(ptProfil.x())+ " " + str(ptProfil.y()))
                    geometries.append(QgsGeometry().fromPointXY(ptProfil))
                    item=ProfilItem(geom, QgsGeometry().fromPointXY(ptProfil), station, abstand, zFactor)
                    profilItems.append(item)
                else:
                    isOnBaseLine=False
        elif "Line" in geom.asWkt(): #geom.type()==2: # Line
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    points=[]
                    isFirst=True
                    firstStation=0
                    firstAbstand=0
                    for elem in i:
                        pxy=elem.asPoint()
                        station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                        if isFirst:
                            firstStation = station
                            firstAbstand = abstand
                            isFirst=False
                        if not station is None and not abstand is None:
                            ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                            points.append(ptProfil)
                        else:
                            isOnBaseLine=False
                    if isOnBaseLine==True:
                        prLine=QgsGeometry().fromPolyline(points)
                        geometries.append(prLine)
                        item=ProfilItem(geom, prLine, firstStation, firstAbstand, zFactor)
                        profilItems.append(item)
            else:# Single Feature
                points=[]
                isFirst=True
                firstStation=0
                firstAbstand=0
                for pxy in geom.vertices():

                    station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                    if not station is None and not abstand is None:

                        if isFirst:
                            firstStation = station
                            firstAbstand = abstand
                            isFirst=False
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        #feedback.pushInfo("station: " +str( station ) + " pxy: " + str(pxy) +"-s->" + ptProfil.asWkt() + " zScale: " + str(zFactor) )
                        points.append(ptProfil)
                    else:
                        isOnBaseLine=False
                if isOnBaseLine==True:
                    prLine=QgsGeometry().fromPolyline(points)
                    geometries.append(prLine)
                    item=ProfilItem(geom, prLine, firstStation, firstAbstand, zFactor)
                    profilItems.append(item)
    
        elif "Polygon" in geom.asWkt(): # geom.type()==3: # Polygon
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for i in multiGeom:
                    isFirst=True
                    firstStation=0
                    firstAbstand=0
                    points=[]
                    for pxy in i:
                        station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                        if isFirst:
                            firstStation = station
                            firstAbstand = abstand
                            isFirst=False
                        if not station is None and not abstand is None:
                            ptProfil=QgsPoint(station, pxy.z() * zFactor)
                            points.append(QgsPoint(pxy.x(), pxy.y()))
                        else:
                            isOnBaseLine=False
                    if isOnBaseLine==True:
                        geometries.append(QgsGeometry().fromPolygon(points))
                        item=ProfilItem(geom, QgsGeometry().fromPolygon(points), firstStation, firstAbstand, zFactor)
                        profilItems.append(item)
            else:# Single Feature
                points=[]
                isFirst=True
                firstStation=0
                firstAbstand=0
                for pxy in geom.vertices():
                    station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                    if isFirst:
                        firstStation = station
                        firstAbstand = abstand
                        isFirst=False
                    if not station is None and not abstand is None:
                        ptProfil=QgsPoint(station, pxy.z() * zFactor)
                        points.append(QgsPoint(pxy.x(), pxy.y()))
                    else:
                        isOnBaseLine=False
                if isOnBaseLine==True:
                    geometries.append(QgsGeometry().fromPolygon(points))
                    item=ProfilItem(geom, QgsGeometry().fromPolygon(points), firstStation, firstAbstand, zFactor)
                    profilItems.append(item)
        else:
            feedback.pushnfo("def extractProfilGeom: Geometrietyp: "+str( geom.type())+str(geom.wkbType())+ geom.asWkt()+ " nicht zugeordnet")
       
        return profilItems, isOnBaseLine

    def hasZGeometries(self, vectorLayer, feedback):
        #feedback.pushInfo("hasZGeometries: ")

        try:
            for feat in vectorLayer.getFeatures():
                if feat.isValid(): # get the first valid Feature
                    vertex=feat.geometry().vertexAt(0) #QgsPoint
                    # if vertex.wkbType == QgsWkbTypes.PointZ or vertex.wkbType == QgsWkbTypes.MultiPointZ:
                        # feedback.pushInfo("hasZGeometries:True " + str(vertex.wkbType))
                        # return True
                    if vertex.z():
                        if math.isnan(vertex.z()):
                            return False
                        else:
                            #feedback.pushInfo("hasZGeometries vertex.z(): True")
                            return True
                    else:
                        return False
        except:
            feedback.pushInfo("hasZGeometries: Fehler")
            return False