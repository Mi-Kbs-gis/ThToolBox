# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 TransformToProfil_PointsDirection
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
__date__ = '2024-12-18'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMessageBox
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
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterEnum,
                       QgsExpression,
                       QgsExpressionContext,
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
from PyQt5.QtGui import QIcon
import os
import numpy as np


class TransformToProfil_PointsDirection(QgsProcessingAlgorithm):
    """
    This function calculates the intersection lines of a series of planes with the vertical cross-section plane.

    For each directed point objekt it will calculate a intersection line on each base line segment. It is conform with calculation of the apparent dip.

    The planes are defined by a reference point with a horizontal direction and a vertical angle.
    The parameter <b>horizonal direction</b> means the directional angle from north, measures clockwise in degrees.(north=0°; east=90°; west=270°)
    The parameter <b>angle of depression</b> (true dip) means the angle between the horizontal an the direction of fall in degrees. (horizontal=0°; nadir=90°)
    
    The parameter <b>Result Line Length</b> regulates the length of the intersection line in the cross section plane.
    
    Kinked base lines are permitted and will be fully processed.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUTBASELINE = 'INPUTBASELINE'
    INPUTRASTER = 'INPUTRASTER'
    INPUTZFACTOR='INPUTZFACTOR'
    INPUTBUFFER='INPUTBUFFER'
    INPUTPOINTLAYER='INPUTPOINTLAYER'
    INPUTZFIELD='INPUTZFIELD'
    AZIMUTH='AZIMUTH'
    HZ_DIRECTION='HZ_DIRECTION'
    LINELENGTHMETHODVALUE='LINELENGTHMETHODVALUE'


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

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
                defaultValue=None,
                parentLayerParameterName=self.INPUTPOINTLAYER,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.HZ_DIRECTION,
                self.tr('horizontal direction in degrees'),
                defaultValue=None,
                parentLayerParameterName=self.INPUTPOINTLAYER,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.AZIMUTH,
                self.tr('angle of depression in degrees'),
                defaultValue=None,
                parentLayerParameterName=self.INPUTPOINTLAYER,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINELENGTHMETHODVALUE,
                self.tr('Result Line Length'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1000,
                optional=True,
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Profil_Plane Intersections')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo("PythonCommand: " + self.asPythonCommand( parameters, context ) )
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsDouble(parameters, self.INPUTZFACTOR, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        pointLayer =  self.parameterAsVectorLayer(parameters, self.INPUTPOINTLAYER, context)
        zFieldName =  self.parameterAsString(parameters, self.INPUTZFIELD, context)
        hz_directionFieldName =  self.parameterAsString(parameters, self.HZ_DIRECTION, context)
        hoehenWinkelFieldName = self.parameterAsString( parameters, self.AZIMUTH, context )
        maxLineLength = self.parameterAsDouble(parameters, self.LINELENGTHMETHODVALUE, context)
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

        crsProject=QgsProject.instance().crs()       
        #check if layers have the same crs
        if not baseLineLayer.crs().authid()==crsProject.authid():
            
            trafo1=QgsCoordinateTransform(baseLineLayer.crs(),crsProject,QgsProject.instance())
            #transform BaseLine
            opResult1=baseLine.transform(trafo1,QgsCoordinateTransform.ForwardTransform, False)

   
    
        layerZFieldId=-1

        #init Terrain
        tm = TerrainModel(rasterLayer, feedback)
        #init LaengsProfil
        lp = LaengsProfil(baseLine, tm, crsProject, feedback)


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
            modus=1 #Height Values from a Field will be used

        else:
            if self.hasZGeometries(pointLayer, feedback) == True:
                modus=3 #Height Values from Geometry will be used
            else:
                modus=2 #Height Values from Raster-DEM will be used


        if modus==1:
            fidxZ = pointLayer.fields().lookupField(zFieldName)
            featuresWithZ=tm.addZtoPointFeatures(featuresOnLine, pointLayer.crs(), fidxZ)
        elif modus==2:
            fidxZ = -1
            featuresWithZ=tm.addZtoPointFeatures(featuresOnLine, pointLayer.crs(), fidxZ)
        elif modus==3:
            #Conversion from QgsFeatureiterator to a list
            featuresWithZ = [feature for feature in featuresOnLine]

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
        
        wkbTyp = QgsWkbTypes.LineString
        sinkFields.append(QgsField("z_reference", QVariant.Double))
        sinkFields.append(QgsField("apparent_dip_angle", QVariant.Double))
        sinkFields.append(QgsField("station", QVariant.Double))
        sinkFields.append(QgsField("offset", QVariant.Double))
        sinkFields.append(QgsField("z_factor", QVariant.Double))

        #config Output
        feedback.pushInfo('parameters: ' + str(parameters))
        feedback.pushInfo('self.OUTPUT: ' + str(self.OUTPUT))
        feedback.pushInfo('context: ' + str(context))
        feedback.pushInfo('sinkFields: ' + str(sinkFields.toList()))
        feedback.pushInfo('wkbTyp: ' + str(wkbTyp))
        feedback.pushInfo('crsProject: ' + str(crsProject.authid()))
        (sink, dest_id) = self.parameterAsSink( parameters, self.OUTPUT, context, sinkFields, wkbTyp, crsProject )

        # #create geometries as profil coordinates
        iNewFeatures=0
        featureError =''
        schnittLinien3D = {}
        for current, srcFeat in enumerate(featuresWithZ):
            featureError='Feature ' + str(current)
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            wkb=srcFeat.geometry().asWkb()
            srcGeom=srcFeat.geometry()
            
            #transform srcGeom to Project.crs() if crs a different
            if not pointLayer.crs().authid()==QgsProject.instance().crs().authid():
                trafo=QgsCoordinateTransform(pointLayer.crs(), QgsProject.instance().crs(), QgsProject.instance())
                #transform clip Geom to SrcLayer.crs Reverse
                status=srcGeom.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)
            
            hoehenWinkelGrad=0 # meint Tiefenwinkel in Grad, means angle of depression in degrees
            try:
                hoehenWinkelGrad=srcFeat[ hoehenWinkelFieldName ]
            except:
                feedback.pushInfo("Parameter azimut is empty: set to 0")
                
            zenitWinkelGrad=hoehenWinkelGrad + 90
            hzDirectionGrad=srcFeat[ hz_directionFieldName ]
            if hoehenWinkelGrad is None or hoehenWinkelGrad >90 or hoehenWinkelGrad<-90:
                zenitWinkelGrad = 90 # Set to Horizonztal
                featureError = featureError + '; field angle of depression is invalid: ' + str(hoehenWinkelGrad) + ' on feature ' + str(srcFeat.id()) 
            if hzDirectionGrad is None:
                hzDirectionGrad=0
                zenitWinkelGrad = 90 # Set to Horizonztal
            
            
            
            #Plane of the directed point
            pointDirectionVector = self.getVectorFromAngles( hzDirectionGrad, zenitWinkelGrad, feedback )

            pointOrthoVector = [pointDirectionVector[1], -pointDirectionVector[0], 0] # Vector regtangular to the pointDirectionVector [deltaY, -deltaX, 0]
            
            pointNormalZenitWinkelGrad=zenitWinkelGrad-90
            pointNormalZenitWinkelRad = pointNormalZenitWinkelGrad * math.pi / 180
            sHzNormal = math.sin( pointNormalZenitWinkelRad ) # *(s=1)

            pRef=srcGeom.vertexAt(0)

            #feedback.pushInfo('reference point: ' + srcGeom.asWkt())
            refPoint=[ pRef.x(), pRef.y(), pRef.z() ] #--> z muss der Geländehöhe entsprechen
             
             
            #Ebene für das Punktobjekt definiert aus Referenzpunkt, dem Richtungsvector und dem Normalenvektor der Basisilinienebene
            #gilt nur wenn ObjektEbene die Basisilinienebene lotrecht schneidet- Sonderfall!!!
            #Der Normalenvektor dieser Ebene ergibt sich aus dem Kreuzprodukt von Richtungsvector und Normalenvektor der Basisilinienebene
            object_planeNormal = np.cross( pointDirectionVector, pointOrthoVector)
            object_plane = self.ebenenGleichung_parameterForm(refPoint, object_planeNormal, feedback)  
            feedback.pushInfo('----------------------------------------'+str(current) +' ID: ' + str(round(srcFeat[ 'PKT_ID' ]))+'-----------------------------------------------')
            feedback.pushInfo('angle of depression(degrees): ' + str(hoehenWinkelGrad) )
            feedback.pushInfo('zenith angle(degrees): ' + str(zenitWinkelGrad) )
            feedback.pushInfo('hzDirection(degrees): ' + str(hzDirectionGrad) )

            feedback.pushInfo('refPoint: ' + str([ round(pRef.x(),2), round(pRef.y(),2), round(pRef.z(),2 )]))
            #feedback.pushInfo('pointDirectionVector: ' + str([ round(pointDirectionVector[0],3), round(pointDirectionVector[1],3), round(pointDirectionVector[2],3)]))
            #feedback.pushInfo('pointOrthoVector: ' + str([ round(pointOrthoVector[0],3), round(pointOrthoVector[1],3), round(pointOrthoVector[2],3)]))
            #feedback.pushInfo('--------- obejct plane ------------------------------')
            #feedback.pushInfo('  object_planeNormal: X:'+ str( round(object_planeNormal[0],2))+' Y:'+ str( round(object_planeNormal[1],2))+ '  Z:'+ str( round(object_planeNormal[2],2)) )
            #feedback.pushInfo('  object_plane: X:'+ str( round(object_plane[0],2))+' Y:'+ str( round(object_plane[1],2))+ '  Z:'+ str( round(object_plane[2],2))+ '  D:'+ str( round(object_plane[3],2)) )

            ptGeom=QgsPoint( round( refPoint[0],2), round( refPoint[1],2) )
            object_station, object_abstand=lp.linearRef.transformToLineCoords( ptGeom ) 
            lotPunkt=lp.linearRef.pointToRealWorld( QgsPoint(object_station, object_abstand), 0, 1) #getLotPunkt(ptGeom, baseLine)
            pLot =self.pointOnPlane_fixXY(object_plane, lotPunkt.x(), lotPunkt.y(), feedback)
            #zLotpunkt=float(round(pLot[2],2))

            #Calculate the intersection line with the plane of each baseline segment
            #Berechne die Schnittlinie mit der Ebene jedes Baselinesegents
            intersectionLinePoints=[]
            intersectionProfileLines=[]
            schnittLinienList3D=[]
            overLenRest = 1 # Wird dynamisch berechnet um bei einer Maximallänge der Ergebnislinie sich zu merken ob beim vorherigen Liniensegment die Maximallänge schon errreichtb wurde
            for i, line in enumerate(lp.linearRef.lineSegments):
                useLineSegment=True
                linePoints=lp.linearRef.getVertices(line)
                if len(linePoints)!=2:
                    useLineSegment=False
                    #Error
                    pass
                else:


                    segmentStat, segmentOffset=lp.linearRef.transformToSegmentCoords( ptGeom , line)

                    #get 3D Point an the object plane for the 2D kinked points of the base line segment
                    #liefert einen 3D-Punkt auf der Objekt-Ebene an dem Knickpunkt der Profilschnittlinie
                    # hole die 3D Punktkoordinaten der Schnittlinien für Anfangs- und Endpunkt des aktuellen Segments der Profilschnittlinine
                    p1 = self.pointOnPlane_fixXY(object_plane, linePoints[0].x(), linePoints[0].y(), feedback)
                    p2 = self.pointOnPlane_fixXY(object_plane, linePoints[1].x(), linePoints[1].y(), feedback)
                    pGeom1 = QgsPoint(p1[0], p1[1], p1[2])
                    pGeom2 = QgsPoint(p2[0], p2[1], p2[2])
                    #feedback.pushInfo('base line ' + str( i) +' intersection p1: '+ str(p1)  )                    
                    #feedback.pushInfo('base line ' + str( i) +' intersection p2: '+ str(p2)  )                    
                    lineLength=lp.linearRef.punktEntfernung2D(pGeom1, pGeom2)

                    if segmentStat: 

                        useLineSegment=True
                    else:
                        useLineSegment=False
                        
                    if useLineSegment == True:
                        feedback.pushInfo('-->' + str(i) + '. base line segment...')
                        lotPunktOnSegment=lp.linearRef.getLotPunkt(ptGeom , line)
                        lotPunktOnSegmentZ =self.pointOnPlane_fixXY(object_plane, lotPunktOnSegment.x(), lotPunktOnSegment.y(), feedback)                    
                        zSegmentLotpunkt=float(round(lotPunktOnSegmentZ[2],2))
                        #feedback.pushInfo('perpendicular foot: '+ str( lotPunkt)) # lotPunkt
                    
                        #p0=[linePoints[0].x(), linePoints[0].y(), pRef.z()]
                        #feedback.pushInfo('p0: '+ str( p0))
                    
                        lineVector=self.getVectorFromLineSegment(linePoints, feedback)
                        deltaX1=lineVector[0]
                        deltaY1=lineVector[1]
                        lineLength2D=math.sqrt( deltaX1 * deltaX1 + deltaY1 * deltaY1 )
                        
                        # create normal vector of the base line segment plane
                        # make a 3D-vector rectangular to 2d baseline direction --> swap x/y and multiply x with -1 right-system/rechtssytem
                        deltaXi = -deltaY1
                        deltaYi = deltaX1
                        deltaZi = 0

                        baseline_planeNormal=[deltaXi/deltaXi, deltaYi/deltaXi, deltaZi/deltaXi ] # Normal of the BaseLine Plane x=1

                        baseline_plane = self.ebenenGleichung_parameterForm( lotPunktOnSegmentZ, baseline_planeNormal, feedback) # hier wird Der Lotpunkt eingesetzt

                        #baseline_plane = self.ebenenGleichung_parameterForm( p0, baseline_planeNormal, feedback) # hier wir die Höhe des Referenz-Punktobjektes genutzt

                        # x1, y1, z1, d1, normal1 = object_plane
                        # x2, y2, z2, d2, normal2 = baseline_plane

                        #feedback.pushInfo('baseline_planeNormal: X:'+ str( round(baseline_planeNormal[0],2))+' Y:'+ str( round(baseline_planeNormal[1],2))+ '  Z:'+ str( round(baseline_planeNormal[2],2)) )
                        #feedback.pushInfo('baseline_plane: '+ str( baseline_plane))
                       

                        
                        # liegt Lotpunkt zwischen p1 und p2
                        # is lotpunkt between p1 and p2
                        stationP1, abstandP1=lp.linearRef.transformToLineCoords( pGeom1 )
                        stationP2, abstandP2=lp.linearRef.transformToLineCoords( pGeom2 )
                    

                        feedback.pushInfo('perpendicular foot point (real elevation): '+ str( lotPunktOnSegmentZ ))
                        intersectionLinePoints = []
                        pBase1=QgsPoint(p1[0], p1[1], p1[2])
                        pBase2=QgsPoint(p2[0], p2[1], p2[2])
                        intersectionLinePoints.append( pBase1 )
                        intersectionLinePoints.append( pBase2 )
                        line3D = QgsGeometry().fromPolyline( intersectionLinePoints )
                        #feedback.pushInfo('line on base line plane ' + str( i) +': '+ line3D.asWkt()  )
                        schnittLinienList3D.append(line3D)
                        
                        profileLinePoints=[]
                        #first Point                       
                        feedback.pushInfo('.. Coordinates in Profile-System: ' )
                        statLot, abstLot=lp.linearRef.transformToLineCoords( lotPunktOnSegment )
                        feedback.pushInfo('p1= ' + str(round(statLot,2))+ ', ' + str(round(zSegmentLotpunkt,2)) + ' (perpendicular foot point)')
                        profileLinePoints.append( QgsPoint(statLot, zSegmentLotpunkt * ueberhoehung) )

                        #second point with limited distance
                        #which point is in the projected direction (Start or End of the baseline segment)
                        if hoehenWinkelGrad>=0 and p2[2]<p1[2]: 
                            secondPxy = QgsPoint(stationP2, p2[2])  
                        else:
                            secondPxy = QgsPoint(stationP1, p1[2])  
                        statP2, zP2, isBetween, overLen = self.pointOnIntersectionLine_planes_fixDistance( QgsPoint(statLot, zSegmentLotpunkt ), secondPxy, maxLineLength, feedback)                       
                        feedback.pushInfo('p2= ' + str(round(statP2,2))+ ', ' + str(round(zP2,2)))# + ' Overlength=' + str(overLen))

                        profileLinePoints.append( QgsPoint(statP2, zP2 * ueberhoehung) )
                        profilLineGeom=QgsGeometry().fromPolyline(profileLinePoints) 
                        #intersectionProfileLines.append( profilLineGeom )
                        #feedback.pushInfo('profile line on base line plane ' + str( i) +': '+ profilLineGeom.asWkt()  )

                        profilFeat = QgsFeature(srcFeat.fields())   
                        #muss fuer jeden Geometrityp gehen
                        profilFeat.setGeometry( profilLineGeom )
                        
                        #berechne Tiefenwinkel scheinbares Fallen beta= arctan(tan alpha * cos roh)
                        #calculate the angle of depression in the profile plane
                        alpha = hoehenWinkelGrad
                        alphaRad = alpha*math.pi/180
                        tObjektRad = hzDirectionGrad*math.pi/180
                        tBaselineRad = lp.linearRef.richtungswinkelRAD(pBase1,pBase2)                       
                        # reduce the angle, if <0 or >360
                        rohRad = tBaselineRad - tObjektRad
                        if rohRad < 0:
                            rohRad = rohRad + 2 * math.pi
                        elif rohRad > (2 * math.pi):
                            rohRad = rohRad - 2 * math.pi
                        betaRad=math.atan( math.tan( alphaRad ) * math.cos(rohRad))
                        beta = round( betaRad*180/math.pi, 3 ) #scheinbares Fallen beta
                        
                        attrs=srcFeat.attributes()
                        #add station and abstand
                        attrs.append( pRef.z() ) #Höhe des Referenzpunktes
                        attrs.append( beta ) # scheinbares Fallen
                        attrs.append( round( statLot,2) ) #station des lotpunktes
                        attrs.append( round( segmentOffset,2) )#abstand zur schnittlinie)
                        attrs.append( ueberhoehung )
                        profilFeat.setAttributes( attrs )
                        # Add a feature in the sink
                        sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)
                        iNewFeatures=iNewFeatures+1
                schnittLinien3D[current]=schnittLinienList3D


            # Update the progress bar
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo('\n----------------- 3D intersection lines -----------------------')
        for objekt_index in schnittLinien3D.keys():
            lineList=schnittLinien3D[objekt_index]
            for geom3D in lineList:
                feedback.pushInfo(str(objekt_index)+': '+geom3D.asWkt())
        feedback.pushInfo('\n' + str(iNewFeatures) +" intersection lines from "+ str(len(schnittLinien3D)) +" transformed to profile coordinates.")
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
        return self.tr('plane_baseline_intersections')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Plane - Baseline Intersections (Directed Points)')

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

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self.__doc__)
   
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_PlaneIntersection_Logo.png'))


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_PointsDirection()


    def getVectorFromLineSegment(self, linePoints, feedback): # linePoints must have len = 2 
        p0=linePoints[0] # Start Point of current baseline Segment
        p1=linePoints[1] # End Point of current baseline Segment

        # first 2D-vector of current baseline Segment(line direction)
        deltaX1 = p1.x() - p0.x()
        deltaY1 = p1.y() - p0.y()
        
        lineVector=[deltaX1, deltaY1]
        return lineVector
    
    # generiert einen Einheitsverktor
    def getVectorFromAngles(self, hzDirectionGrad, zenitWinkelGrad, feedback):
        zenitWinkelRad = zenitWinkelGrad * math.pi / 180
        hzDirectionRad = hzDirectionGrad  * math.pi / 180
        
        #feedback.pushInfo('zenitWinkel(Rad): ' + str(zenitWinkelRad) )
        #feedback.pushInfo('hzDirection(Rad): ' + str(hzDirectionRad) )
        #calc normal_vektor of the intersection plane
        #1. given is a horizontal distance of 1 m
        #wenn s=1 kürzt sich weg
        
        sHz = math.sin( zenitWinkelRad ) # *s
        deltaX = math.sin( hzDirectionRad ) * sHz 
        deltaY = math.cos( hzDirectionRad ) * sHz
        deltaZ = math.cos( zenitWinkelRad ) # *s 
        pointDirectionVector = [deltaX, deltaY, deltaZ]
        pointDirectionVectorOne = pointDirectionVector / np.linalg.norm(pointDirectionVector) 
        return pointDirectionVectorOne

    def polarerAnhaenger3D(self, position, schraegStrecke, richtungHz, azimut, feedback):
        entfernung2D=float(math.sin(azimut)) * float(schraegStrecke) ##?
        deltaZ=float(math.cos(azimut)) * float(schraegStrecke)# *-1

        richtungswinkel2D=richtungHz #??
        deltaX=float(math.sin(richtungswinkel2D)) * entfernung2D
        deltaY=float(math.cos(richtungswinkel2D)) * entfernung2D
        xZiel=position.x() + deltaX
        yZiel=position.y() + deltaY
        zZiel=position.z() + deltaZ

        return QgsPoint(round(xZiel,2), round(yZiel,2), round(zZiel,2))

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
         
    def ebenenGleichung_parameterForm(self, referenzPunkt, normalenvektor, feedback): # referenzpunkt [x,y,z]
        # this function calculates the plan equation in parameters form
        # Ebenengleichung in Normalenform: (P - P0) * N = 0
        # Punkte in Form von (x, y, z)
        P0 = np.array(referenzPunkt)

        # # Berechne die Normalen durch das Kreuzprodukt
        # normalenvektor = np.cross(V1, V2)
        # print('normalenvektor', normalenvektor, 'passt')
        

        # # Normalisiere den Normalenvektor
        # #normalenvektor = normalenvektor / np.linalg.norm(normalenvektor)
        
        # ##print('normalisierter normalenvektor', normalenvektor)

        # # Verwende einen der Punkte als Referenzpunkt P0
        # P0 = P1
        # print('Ebenenstützpunkt', P0, 'passt')
       
        A, B, C = normalenvektor

        #D erhält man in dem man den Referenzpunkt in die Gleichung einsetzt und nach D auflöst
        # D=Ax+By+Cz
        D = A*referenzPunkt[0] + B*referenzPunkt[1] + C*referenzPunkt[2]
        #feedback.pushInfo('Skalarprodukt(normalenvektor * -P0) ' + str(normalenvektor)+' * ' +str(-P0) + ' = ' + str( D)+  ' passt') # könnte auch durch einsetzen der Koordinaten von P1 berechnet werden
        #feedback.pushInfo('Ebenengleichung:'+ str(round(A,3)) + 'X ' + str(round(B,3)) + 'Y ' +str(round(C,3)) +'Z = ' + str(round(D,3)))
        return A, B, C, D, normalenvektor


    #Ergebnis ist ein Array [pX, pY, pZ] mit den Punktkoordinaten 
    def pointOnIntersectionLine_planes_fixZ(self,  ebene1, ebene2, pZ, feedback): # Plane Formula in Parameterform                        
        #this function calculates a point on a plane with a given z value

        x1, y1, z1, d1, normal1 = ebene1
        x2, y2, z2, d2, normal2 = ebene2
        #z wird in Gleichungen eingesetzt und auf die rechte Seite der Gleichung verschoben
        z1z = z1 * pZ
        z2z = z2 * pZ
        left=np.array([ [x1, y1],[x2, y2]]) #rechte Seite das Gleichungssystems
        right=np.array( [d1-z1z,d2-z2z] )   #linke Seite das Gleichungssystems
        # Lösung des linearen Gleichungssystems
        #feedback.pushInfo('Gleichungsssystem mit eingesetzten z-Wert: '+str(left) + ' = ' + str(right) )
        erg=np.linalg.solve(left,right)
        schnittpunkt=[erg[0], erg[1], pZ]
        return schnittpunkt
        
    #Ergebnis ist ein Array [pX, pY, pZ] mit den Punktkoordinaten 
    def pointOnPlane_fixXY(self, ebene1,  pX, pY, feedback): # Plane Formula in Parameterform                        
        #this function calculates a point on an plan with given values for x and y
        x1, y1, z1, d1, normal1 = ebene1

        #z wird in Gleichungen eingesetzt und auf die rechte Seite der Gleichung verschoben
        x1x = x1 * pX
        y1y = y1 * pY
       
        pZ = (d1 -x1x - y1y)/z1
        #feedback.pushInfo('pointOnPlane_fixXY --> Z: ' + str( pZ ))
        #pLot = pLotnp.astype(np.double)
        return [pX, pY, pZ]
        
    #Ergebnis ist ein Array [pNx, pNy, isBetween, overLen] 
    def pointOnIntersectionLine_planes_fixDistance(self,  p0, p1, distance, feedback): # Plane Formula in Parameterform                        
        #this function calculates a point on line with a given distance
        
        dx=p1.x()-p0.x()
        dy=p1.y()-p0.y()
        
        ds= math.sqrt(dx*dx + dy*dy)
        m = distance / ds
        
        pNx= p0.x() + m * dx
        pNy= p0.y() + m * dy
        isBetween = False
        #feedback.pushInfo( 'distance <=ds ?' + str(distance) + '=?' + str(ds) )
        if distance <=ds:
            isBetween=True
        overLen = distance - ds
        
        return pNx, pNy, isBetween, overLen
