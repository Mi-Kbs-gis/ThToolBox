#from ggis.processing import alg
#@alg(name= profileEachLine, label="Baseline for all Lines of Layer Data driven",groop="To Profile Coordinates"

# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ThToolBox
                                 TransformToProfil_Points
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
__date__ = '2024-10-17'
__copyright__ = '(C) 2024 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
import processing
from .tlug_utils.TerrainModel import TerrainModel
from .tlug_utils.LaengsProfil import LaengsProfil
import math
from .tlug_utils.ProfilItem import ProfilItem
from PyQt5.QtGui import QIcon
import os
from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsFeatureRequest,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsFeature,
                       QgsWkbTypes,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterField,
                       QgsExpression,
                       QgsExpressionContext)

class TransformToProfil_PointsForAllLinesDataDriven(QgsProcessingAlgorithm):
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

    INPUTBASELINE = 'INPUTBASELINE'
    INPUTRASTER = 'INPUTRASTER'
    INPUTZFACTOR = 'INPUTZFACTOR'
    OUTPUT = 'OUTPUT'

    MAPPINGTABLE='MAPPINGTABLE'
    INPUTPOINTLAYER='INPUTPOINTLAYER'
    INPUTZFIELDSTART='INPUTZFIELDSTART'
    INPUTZFIELDEND='INPUTZFIELDEND'
    INPUTZFIELD='INPUTZFIELD'
    SOURCE_BASLINE_ID = 'SOURCE_BASLINE_ID'
    SOURCE_POINT_ID = 'SOURCE_POINT_ID'
    MAPPINGTABLE_BASLINE_ID = 'MAPPINGTABLE_BASLINE_ID'
    MAPPINGTABLE_POINT_ID = 'MAPPINGTABLE_POINT_ID'
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr('points_bore_axis_multi_baseline_datadriven')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Points (incl. Bore Axis) Multi Baseline - Data Driven')

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
        return self.tr("This algorithm performs the function 'Points (incl. Bore Axis)' for all lines of a line layer.")

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/TransformToProfil_Points_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_PointsForAllLinesDataDriven()

    def initAlgorithm(self, config=None):
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
                self.tr('Profile Multi Baseline Layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        #self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Input layer'), types=[QgsProcessing.TypeVector]))
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.MAPPINGTABLE, #INPUTBUFFER,
                self.tr('Mappingtable(baseline primary key ; point primary key)'),
                [QgsProcessing.TypeVector]
                
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

        self.addParameter(
            QgsProcessingParameterExpression(
                self.SOURCE_BASLINE_ID,
                self.tr('Field with baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE
            )
        )

        self.addParameter(
            QgsProcessingParameterExpression(
                self.SOURCE_POINT_ID,
                self.tr('Field with point layer primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTPOINTLAYER
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.MAPPINGTABLE_BASLINE_ID,
                self.tr('Field with baseline primary key in Mapping Table'),
                parentLayerParameterName=self.MAPPINGTABLE
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.MAPPINGTABLE_POINT_ID,
                self.tr('Field with point layer primary key in Mapping Table'),
                parentLayerParameterName=self.MAPPINGTABLE
            )
        )

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

        ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        baseLineLayer= self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        pointLayer =  self.parameterAsVectorLayer(parameters, self.INPUTPOINTLAYER, context)
        zFieldName =  self.parameterAsString(parameters, self.INPUTZFIELD, context)
        startZFieldName = self.parameterAsString(parameters, self.INPUTZFIELDSTART, context)
        endZFieldName = self.parameterAsString(parameters, self.INPUTZFIELDEND, context)
        mappingTable = self.parameterAsVectorLayer(parameters, self.MAPPINGTABLE, context)

        #bufferWidth = self.parameterAsDouble(parameters, self.INPUTBUFFER, context)
        exprBaselineID = self.parameterAsExpression(parameters, self.SOURCE_BASLINE_ID, context)
        exprPointID = self.parameterAsExpression(parameters, self.SOURCE_POINT_ID, context)
        exprMappingBaselineID = self.parameterAsExpression(parameters, self.MAPPINGTABLE_BASLINE_ID, context)
        exprMappingPointID = self.parameterAsExpression(parameters, self.MAPPINGTABLE_POINT_ID, context)     

        # fix output geometry type
        outputGeomType = QgsWkbTypes.Point # initial
        if endZFieldName=="" and startZFieldName=="": #No Depth
            outputGeomType = QgsWkbTypes.Point #Output Geometry Type Point

        else:
            outputGeomType = QgsWkbTypes.LineString
            
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=pointLayer.fields()
        fields.append( QgsField( "station" ,  QVariant.Double ) ) # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        fields.append( QgsField( "abstand" ,  QVariant.Double ) ) # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        fields.append( QgsField( "z_factor" ,  QVariant.Int ) )   # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        fields.append( QgsField( "profil_id" ,  QVariant.Int ) ) 

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if baseLineLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUTBASELINE))

        if pointLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUTPOINTLAYER))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            outputGeomType,
            baseLineLayer.sourceCrs()
        )

        # Send some information to the user
        #feedback.pushInfo('CRS is {}'.format(vectorLayer.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        features=[] #QgsFeatureIterator
        if len( mappingTable.selectedFeatures() ) > 0:
            features = mappingTable.selectedFeatures()
        else:
            features = [feat for feat in mappingTable.getFeatures()]
        feedback.pushInfo( 'Features {} used'.format( len( features ) ) )

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len( features ) if len( features ) else 0
        
        #Clear Selection
        baseLineLayer.removeSelection()
        mappingTable.removeSelection()
        pointLayer.removeSelection()
        counter=0
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            
            #select to current feature
            baseLineLayer.select( feature.id() )

            exprContextMT = QgsExpressionContext()
            exprContextMT.setFeature(feature)
            # getting profile Id from MappingTable Feature
            expr1 = QgsExpression( exprMappingBaselineID )
            profilID = expr1.evaluate ( exprContextMT )          

            # getting point Id from MappingTable Feature
            expr2 = QgsExpression( exprMappingPointID )
            pointID = expr2.evaluate ( exprContextMT )             
            

            #ToDo Select Point layer by point id
            exprPoint=QgsExpression( str(exprPointID) + ' = ' + str(pointID) )#'my_field &gt; 20')
            pointLayer.selectByExpression(exprPoint.expression())
            #feedback.pushInfo('pointLayer: '+ exprPoint.expression()+ ' selected:'+str(pointLayer.selectedFeatureCount()))
            #requestBaseLine = QgsFeatureRequest().setFilterExpression(exprBaseLine) 
            #baseLineFeature=next(baseLineLayer.getFeatures(requestBaseLine.setLimit(1))) #for feature in vector_layer.getFeatures(request):
            #ToDo Select baseline Layer by baseline id
            exprBaseLine=QgsExpression( str(exprBaselineID) + ' = ' + str(profilID) )#'my_field &gt; 20')
            baseLineLayer.selectByExpression(exprBaseLine.expression())
            feedback.pushInfo(exprBaseLine.expression()+ ' AND '+ exprPoint.expression()++ '('+str(pointLayer.selectedFeatureCount())+' Points)')
            #feedback.pushInfo('pointLayer: '+ exprPoint.expression()+ ' selected:'+str(pointLayer.selectedFeatureCount()))
            
            profil_features = None
            # try:
            bufferWidth=0
            profil_features = self.runPointsForBaseline( sink, profilID, pointLayer, baseLineLayer, bufferWidth, rasterLayer, ueberhoehung, zFieldName, startZFieldName, endZFieldName, context, feedback)
            
            
            # count=0
            # if profil_features is None:
                # feedback.reportError("Profil: " + str(profilID) + ' Point: ' + str(pointID) + ' no valid Data')
            # else:
                # for grFeature in profil_features:
                    # #feedback.pushInfo("Type: " + str(type(grFeature)) )
                    # if not str(type(grFeature)) == "<class 'qgis._core.QgsFeature'>":
                        # feedback.pushInfo("Abbruch Type: " + str(type(grFeature))+ '  ' + str( grFeature.attributes() )  )
                        # break
                    

                    # newFeature = QgsFeature( fields )
                    # attrs = grFeature.attributes()
                    # #len1 = len(attrs)
                    # attrs.append( profilID )
                    # #len2 = len(attrs)
                    # #feedback.pushInfo( str(count)+': '+ str(attrs) +" "+ str(len1) + '--> ' + str(len2) )
                    # newFeature.setAttributes( attrs )
                    # newFeature.setGeometry( grFeature.geometry() )
                    # feedback.pushInfo('Profile( ' + str( profilID ) + ") Feature:("+ str(count)+'): ' + str(newFeature))
                    # # Add a feature in the sink
                    # sink.addFeature( newFeature, QgsFeatureSink.FastInsert)
                    # count=count+1
            #print( "Count: " + str(count) + ' at profile ' + str( profilID ) )
            #feedback.pushInfo("Count: " + str(count) + ' at profile ' + str( profilID ) )

            # except QgsProcessingException as err:
                # feedback.pushInfo("ERROR at profile " + str( profilID ) + ': '+ str(err.args) + " " + str(repr( err )) + " Fehler: "  )
            
            
            #Clear Selection
            baseLineLayer.removeSelection()

            # Update the progress bar
            feedback.setProgress(int(current * total))
            counter=counter+1
        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancelation and progress reports!)


            
            
            
        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}

    def runPointsForBaseline(self, sink, profilID, pointLayer, baseLineLayer, bufferWidth, rasterLayer, ueberhoehung, zFieldName, startZFieldName, endZFieldName, context, feedback):

    
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
            modus=1
            #feedback.pushInfo("1 self.hasZGeometries(pointLayer):"+str(self.hasZGeometries(pointLayer, feedback)))
            # if self.hasZGeometries(pointLayer, feedback) == True:
                # reply = QMessageBox.question(None, 'Continue?', 
                                 # 'Overide Z by field ' + zFieldName, QMessageBox.Yes, QMessageBox.No)
                # if reply == QMessageBox.Yes:
                    # modus=1
                # else:
                    # modus=3
            # else:
                # modus=1
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
        #fidx=[None, None] #Field Indizes for the Z values
        modusDepth=-1
        if endZFieldName=="" and startZFieldName=="": #No Depth
            modusDepth=1
            #keep featuresWithZ 
            wkbTyp=QgsWkbTypes.Point
        else:
            if endZFieldName and startZFieldName:
                idx1 = pointLayer.fields().lookupField(startZFieldName)
                idx2 = pointLayer.fields().lookupField(endZFieldName)
                #fidx=[idx1, idx2]
                modusDepth=2
            elif endZFieldName and startZFieldName=="":

                idx1 = -1
                idx2 = pointLayer.fields().lookupField(endZFieldName)
                #fidx=[-1, idx2]
            elif endZFieldName=="" and startZFieldName:
                idx1 = pointLayer.fields().lookupField(startZFieldName)
                idx2 = -1
                #fidx=[idx1, -1]

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
        sinkFields.append(QgsField("z_factor", QVariant.Double))
        sinkFields.append(QgsField("profil_id", QVariant.Double))
    
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
                    attrs.append( profilItem.station )
                    attrs.append( profilItem.abstand )
                    attrs.append( ueberhoehung )
                    attrs.append( profilID )
                    profilFeat.setAttributes( attrs )
                    # Add a feature in the sink
                    sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)
                    iNewFeatures=iNewFeatures+1

            # Update the progress bar
            feedback.setProgress(int(current * total))
        

        #feedback.pushInfo(str(iNewFeatures) +" transformed to profile coordinates.")

    
    def createBohrungSchichtLineFeatures(self, pointfeaturesWithZ, tiefeVonIdx, tiefeBisIdx, richtungHz, azimut, feedback):
        featuresWithZ=[]
        for current, srcFeat in enumerate(pointfeaturesWithZ):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            #create a Line Geometry
            if tiefeVonIdx==-1:
                tiefeVon=srcFeat.geometry().vertexAt(0).z()
                tiefeVon=0
            
            else:
                tiefeVon=srcFeat.attribute(tiefeVonIdx)
            if tiefeBisIdx==-1:
                tiefeBis=srcFeat.geometry().vertexAt(0).z()
                tiefeBis=0
            
            else:
                tiefeBis=srcFeat.attribute(tiefeBisIdx)         
            
            #tiefeBis=srcFeat.attribute(tiefeBisIdx)
            if tiefeBis is None or str(tiefeBis)=="":
                tiefeBis=0
                feedback.pushInfo("tiefeBis:"+str(tiefeBis))
            if tiefeVon is None or str(tiefeVon)=="":
                tiefeVon=0
                feedback.pushInfo("tiefeVon:" + str(tiefeVon))
            
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
                #points=[]
                for pxy in multiGeom:
                    #for pxy in i:
                    ptProfil=None
                    station, abstand=laengsProfil.linearRef.transformToLineCoords(pxy)
                    if not station is None and not abstand is None:
                        ptProfil=QgsPointXY(station, pxy.z() * zFactor)
                        #points.append(ptProfil)
                    else:
                        isOnBaseLine=False
                    if isOnBaseLine==True:
                        geometries.append(QgsGeometry().fromPointXY(ptProfil))
                        item=ProfilItem(geom, QgsGeometry().fromPointXY(ptProfil), station, abstand, zFactor)
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
            feedback.pushInfo("def extractProfilGeom: Geometrietyp: "+str( geom.type())+str(geom.wkbType())+ geom.asWkt()+ " nicht zugeordnet")
       
        return profilItems, isOnBaseLine

    def hasZGeometries(self, vectorLayer, feedback):
        #feedback.pushInfo("hasZGeometries: ")

        try:
            for feat in vectorLayer.getFeatures():
                if feat.isValid(): # get the first valid Feature
                    vertex=feat.geometry().vertexAt(0) #QgsPoint

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
    
    
    
    
    
    
    
    

    def runPointsForBaseline_alt(self, pointLayer, baseLineLayer, buffer, rasterLayer, ueberhoehung, zField, zFieldStart, zFieldEnd, context, feedback):
        profil_points_layer = processing.run("thtoolbox:points_bore_axis", { 
                        'INPUTBUFFER' : buffer,
                        'INPUTPOINTLAYER' : pointLayer.source(),
                        'INPUTRASTER' : rasterLayer.source(), #'//tlugjfs2/laserscandaten/dgm1_grid/dgm1'
                        'INPUTBASELINE' : baseLineLayer.source(), #'M:/transfer/Kürbs/TH-Profile/th_profile.shp|layername=th_profile'
                        'INPUTZFACTOR' : ueberhoehung,
                        'INPUTZFIELD' : zField,
                        'INPUTZFIELDEND' : zFieldEnd,
                        'INPUTZFIELDSTART' : zFieldStart,
                        'OUTPUT' : 'memory'
                            }, context=context, feedback = feedback)['OUTPUT']
        feedback.pushInfo("Sub-Process finished: " + profil_points_layer.layerName() )
        
        return profil_points_layer.getFeatures()


