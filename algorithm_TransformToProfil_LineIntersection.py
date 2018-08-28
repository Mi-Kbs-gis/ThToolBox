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
__date__ = '2018-08-08'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProject,
                       QgsFeature,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsProcessingException)
from .tlug_utils.TerrainModel import TerrainModel
from .tlug_utils.LaengsProfil import LaengsProfil
#from .tlug_utils.LayerSwitcher import LayerSwitcher

class TransformToProfil_LineIntersection(QgsProcessingAlgorithm):
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
    INPUTINTERSECTIONLAYER='INPUTINTERSECTIONLAYER'

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
                self.INPUTINTERSECTIONLAYER,
                self.tr('Intersection Line Layer'),
                [QgsProcessing.TypeVectorLine]
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
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                optional=False,
                minValue=0,
                maxValue=100
                
            )
        )
        


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Profil_Line Intersection Points')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        lineLayer =  self.parameterAsVectorLayer(parameters, self.INPUTINTERSECTIONLAYER, context)
        baseLine=None
        #Basline Layer must have only 1 Feature
        if baseLineLayer.featureCount()==1:
        #baseLine must be the first feature
            baseLine=baseLineLayer.getFeature(0).geometry()       
        elif len(baseLineLayer.selectedFeatures())==1:
            selection=baseLineLayer.selectedFeatures()
            #baseLine must be the first feature
            baseLine=selection[0].geometry() 
        else:
            msg = self.tr("Error: BaseLine layer needs exactly one line feature! ", baseLineLayer.featureCount(), "Just select one feature!")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        #take CRS from Rasterlayer 
        crsProject=rasterLayer.crs()    
        #check if layers have the same crs
        if not baseLineLayer.crs().authid()==crsProject.authid():
            # if not, transform to raster crs()
            trafo1=QgsCoordinateTransform(baseLineLayer.crs(),crsProject,QgsProject.instance())
            #transform BaseLine
            opResult1=baseLine.transform(trafo1,QgsCoordinateTransform.ForwardTransform, False)
        # if not lineLayer.crs().authid()==crsProject.authid():
            # # if not, transform to raster crs()
            # trafo2=QgsCoordinateTransform(lineLayer.crs(),crsProject,QgsProject.instance())
            # #transform BaseLine
            # opResult2=baseLine.transform(trafo2,QgsCoordinateTransform.ForwardTransform, False)

        layerZFieldId=-1
        #init Terrain
        tm = TerrainModel(rasterLayer, feedback)
        #init LaengsProfil
        lp = LaengsProfil(baseLine, tm, crsProject, feedback)
        
        try:
            total = 100.0 / len(lp.linearRef.lineSegments)
        except:
            msg = self.tr("Keine Basislinie")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        bufferWidth=10 #10 m, we make an area to intersect
        #get candidates featuresOnLine=[]
        featuresOnLine=lp.linearRef.getFeaturesOnBaseLine(lineLayer, bufferWidth)
        #Falls Linien, dann ermittle Schnittpunkte mit Laengsprofil
        schnittpunkte=[] #Liste von Features
        if self.isLineType(lineLayer):
            #get intersection point features
            schnittpunkte=self.getSchnittpunkteAusLinien(featuresOnLine, lineLayer.crs(), lp, feedback) #Um Attribute der geschnittenen Objekte zu uebernehmen, muss hier mehr uebergeben werden
            
            
            #calculate Z-Values
            featuresWithZ=tm.addZtoPointFeatures(schnittpunkte, crsProject, layerZFieldId)
            #config Output
            newFields=featuresWithZ[0].fields()
            wkbTyp=featuresWithZ[0].geometry().wkbType()
            (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
            context, newFields, wkbTyp, crsProject)

            #create geometries as profil coordinates
            profilFeatures=[]
            iFeat=0
            for current, srcFeat in enumerate(featuresWithZ):
                # Stop the algorithm if cancel button has been clicked
                if feedback.isCanceled():
                    break
                srcGeom=srcFeat.geometry()
                profilGeometries=lp.extractProfilGeom(srcGeom, ueberhoehung, lp.srcProfilLine)
                #feedback.pushInfo("b " + str(srcFeat.attributes())+ ""+ str(profilGeometries))
                for profilGeom in profilGeometries:
                    # build a Feature
                    profilFeat = QgsFeature(newFields)   
                    profilFeat.setGeometry(profilGeom)#QgsGeometry.fromPointXY(QgsPointXY(profilGeom.x(),profilGeom.y())))
                    profilFeat.setAttributes(srcFeat.attributes())
                    # Add a feature in the sink
                    sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)
                    iFeat=iFeat+1
                    feedback.pushInfo(str(profilFeat.attributes()))
                # Update the progress bar
                feedback.setProgress(int(current * total))

            msgInfo=self.tr("{0} intersections where transformed to profile coordinates:").format(iFeat)
            feedback.pushInfo(msgInfo)
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
        return 'Line - Baseline Intersections'

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
        return TransformToProfil_LineIntersection()

    def isLineType(self, vectorLayer):
        if vectorLayer.wkbType()==2 or vectorLayer.wkbType()==1002 or vectorLayer.wkbType()==2002 or vectorLayer.wkbType()==3002 or vectorLayer.wkbType()==5 or vectorLayer.wkbType()==1005 or vectorLayer.wkbType()==2005 or vectorLayer.wkbType()==3005:
            return True
        else:
            return False

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
        return points       
    
    # this function create a list of point features with intersection Points and manage the geomety type Single or Multi
    def getSchnittpunkteAusLinien(self, overlapFeats, featureCrs, laengsProfil, feedback):
        schnittpunktFeatures=[]
        ioFeat=0
        countPoints=0
        try:
            for feat in overlapFeats:
                #Feature bekommt neues Attribut Station
                if ioFeat==0:
                    fields=feat.fields()
                    fields.append(QgsField("station", QVariant.Double))
                
                schnittpunktFeaturesOfThisLine=[]
                #check if Multipolygon
                iMulti=0
                tempGeom=QgsGeometry()
                tempGeom.fromWkb(feat.geometry().asWkb())
                #transform geom to Project.crs() if crs a different
                if not featureCrs.authid()==QgsProject.instance().crs().authid():
                    trafo=QgsCoordinateTransform(featureCrs, QgsProject.instance().crs(), QgsProject.instance())
                    #transform Geom to Project.crs()
                    tempGeom.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)

                if tempGeom.isMultipart:
                    #feedback.pushInfo(str(iMulti) + str(type(feat.geometry())))
                    multiGeom = tempGeom.asMultiPolyline()
                    for singleLineVertices in multiGeom:  ############## Achtung normalerweise wird diese Schleife zum Auflösen des Multiparts benoetigt
                        points=[]
                        for pxy in singleLineVertices:
                            points.append(QgsPoint(pxy.x(), pxy.y()))
                        singleLine=QgsGeometry().fromPolyline(points)
                        
                        #feedback.pushInfo(str(iMulti) + str(type(singleLine)) + str(singleLineVertices))
                        
                        schnittpunktFeaturesOfThisLine = self.makeIntersectionFeatures(feat, singleLine, laengsProfil, fields, feedback)
                        iMulti=iMulti+1

                
                else: # single Geometry
                    schnittpunktFeaturesOfThisLine = self.makeIntersectionFeatures(feat, tempGeom, laengsProfil, fields, feedback)
                
                #add to list
                for schnittFeat in schnittpunktFeaturesOfThisLine: #Intersection Feature in project.crs()
                    schnittpunktFeatures.append(schnittFeat)
                    #feedback.pushInfo(str(schnittFeat.attributes()))
                ioFeat=ioFeat+1
                #count Intersections
                countPoints=countPoints+len(schnittpunktFeaturesOfThisLine)

        except:
            msg = self.tr("Error: Creating Intesections Geometry {0} Feature {1}").format(str(type(feat.geometry())), str(feat.attributes()))
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        msgInfo=self.tr("Intersected Lines: {0} Intersections: {1}").format(ioFeat, countPoints)
        feedback.pushInfo(msgInfo)
        return schnittpunktFeatures

    # this function create a list of point features with intersection Points
    def makeIntersectionFeatures(self, feat, geom,  laengsProfil, newfields,  feedback):
        schnittpunktFeatures=[]
        countPoints=0
        #explode polyline, get each line segment as LineString in a list
        try:

            linesOfPolyLine = self.extractLineSegments(geom)
        except:
            msg = self.tr("Error: Explode Line Segments for Geometry {0} Feature {1}").format(geom.asWkt(), feat.attributes())
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        for lineP in linesOfPolyLine:
            #get all Intersection Points
            intersectionPoints, stations=laengsProfil.linearRef.getIntersectionPointofPolyLine(lineP)
            if not intersectionPoints is None:
                for i in range(len(intersectionPoints)):
                    try:
                        pt=intersectionPoints[i].asPoint()
                        
                        schnittPunktFeat=QgsFeature(newfields) #Feature with extra attribut
                        schnittPunktFeat.setGeometry(intersectionPoints[i])
                        attrs=feat.attributes()
                        attrs.append(stations[i]) # station is saved in extra Attribute
                        #set new attributes with station
                        schnittPunktFeat.setAttributes(attrs)                               
                        schnittpunktFeatures.append(schnittPunktFeat)
                        #feedback.pushInfo(str(attrs))

                    except:
                        msg = self.tr("Error: Creating Intesections Geometry {0} Feature {1}").format(str(type(intersectionPoints[i].geometry())), str(intersectionPoints[i].attributes()))
                        feedback.reportError(msg)
                        raise QgsProcessingException(msg)
            
        return schnittpunktFeatures
