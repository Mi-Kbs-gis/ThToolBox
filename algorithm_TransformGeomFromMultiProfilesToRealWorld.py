# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 algorithm_TransformGeomFromMultiProfilesToRealWorld.py
 TLUBN Algorithms
                              -------------------
        begin                : 2019-12-13
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
__date__ = '2019-12-13'
__copyright__ = '(C) 2019 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
#import processing
#from PyQt5 import QtGui
#from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QCoreApplication, QVariant#, ZeroDivisionError
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsField,
                       QgsProject,
                       QgsFeature,
                       QgsExpression,
                       QgsExpressionContext)
from tlug_utils.LinearReferencingMaschine import LinearReferencingMaschine
from tlug_utils.TerrainModel import TerrainModel
from tlug_utils.LaengsProfil import LaengsProfil
from tlug_utils.LayerUtils import LayerUtils
import math
from ThToolBox.tlug_utils.ProfilItem import ProfilItem
from PyQt5.QtGui import QIcon
import os

class TransformToProfil_PointsForAllLines(QgsProcessingAlgorithm):
    """
    Transforms a point layer or selection to profile coordinates with considering of elevation.
    If points has z values, they will used. 
    If the the point z value are in a feature attribute, you can use it for elevation.
    If the points have no realtionship to an elevation value, elevation is used from a Raster DEM.
    This Function is processing only the points inside a buffer around the Baseline or if there is a selection, all selected points.
    Extrapolation is not supported. Points have to be perpendicular to the baseline.
    Select one line feature or use an one feature layer as Baseline.
    A baseline can have breakpoints.
    If the baseline is a polylinestring, there could be blind spots. Points in blind spots will be ignored.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUTVECTORLAYER='INPUTVECTORLAYER'
    INPUTBASELINE = 'INPUTBASELINE'
    INPUTZFACTOR='INPUTZFACTOR'
    OFFSETFIELD = 'OFFSETFIELD'
    INPUTVECTORLAYER_BASLINE_ID = 'INPUTVECTORLAYER_BASLINE_ID'
    PROFIL_BASELINE_ID = 'PROFIL_BASELINE_ID'




    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTVECTORLAYER,
                self.tr('Layer in Profile Coordinates'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUTVECTORLAYER_BASLINE_ID,
                self.tr('Field with baseline foreign key'),
                parentLayerParameterName=self.INPUTVECTORLAYER
            )
        )
        

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE,
                self.tr('Profil Baselines'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterExpression(
                self.PROFIL_BASELINE_ID,
                self.tr('Field with baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE
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
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.OFFSETFIELD,
                self.tr('Offset'),
                "0",
                self.INPUTVECTORLAYER,#DoTo: set Datatyp Numeric
                optional=True

            )
        )


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Real World Geometries')
            )
        )



        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsDouble(parameters, self.INPUTZFACTOR, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        vectorLayer =  self.parameterAsVectorLayer(parameters, self.INPUTVECTORLAYER, context)
        baselineIDFieldName =self.parameterAsExpression(parameters, self.PROFIL_BASELINE_ID, context)
        offsetFieldName = self.parameterAsString(parameters, self.OFFSETFIELD, context)
        vectorLayerBaselineIDFieldName = self.parameterAsExpression(parameters, self.INPUTVECTORLAYER_BASLINE_ID, context)

        outputGeomType = vectorLayer.wkbType() #Output Geometry Type Point
        
        offsetExpr=QgsExpression(offsetFieldName)
        if offsetExpr.hasParserError():
            feedback.reportError("Offset Expression failed: " + offsetExpr.parserErrorString())
            offsetExpr="0"

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=vectorLayer.fields()
        #fields.append( QgsField( "station" ,  QVariant.Double ) ) # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        #.append( QgsField( "abstand" ,  QVariant.Double ) ) # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        #fields.append( QgsField( "z_factor" ,  QVariant.Int ) )   # will be added and filled by Subprocess (algorithm_TransformToProfil_LineIntersection.py)
        #fields.append( QgsField( "profil_id" ,  QVariant.Int ) ) 

        if vectorLayer is None:
            raise QgsProcessingException(self.invalidSourceError( parameters, self.INPUTVECTORLAYER))
        if vectorLayer is None:
            raise QgsProcessingException(self.invalidSourceError( parameters, self.OUTPUT))

        #check if vectorlayer has Features
        if vectorLayer.featureCount()==0:
            msg = self.tr("Error: Layer " , vectorLayer.name() , "is emty! ")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        #check if baselineLayer has Features
        if baseLineLayer.featureCount()==0:
            msg = self.tr("Error: Layer " , baseLineLayer.name() , "is emty! ")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)

        #take CRS from Project
        crsProject=QgsProject.instance().crs()   
            
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            outputGeomType,
            vectorLayer.sourceCrs()
        )

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        offsetExprContext = QgsExpressionContext()
        # Send some information to the user
        #feedback.pushInfo('CRS is {}'.format(vectorLayer.sourceCrs().authid()))


        features=[] #QgsFeatureIterator
        if len( vectorLayer.selectedFeatures() ) > 0:
            features = vectorLayer.selectedFeatures()
        else:
            features = [feat for feat in vectorLayer.getFeatures()]
        feedback.pushInfo( 'Features {} used'.format( len( features ) ) )

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len( features ) if len( features ) else 0
        #names = [field.name()+"; " for field in fields]
        #feedback.pushInfo(''.join( names ) )
        #Clear Selection
        vectorLayer.removeSelection()
        i=0       
        for current, feature in enumerate(features):
        
            try:


                # Stop the algorithm if cancel button has been clicked
                if feedback.isCanceled():
                    break

                # Offset
                abstand=0
                offsetExprContext.setFeature( feature )
                try:
                    abstand = offsetExpr.evaluate( offsetExprContext )
                except:
                    msg = self.tr("Error while calculating Offset from Expression. Feature " + str(feat.attributes()) )
                    feedback.reportError(msg)
                    raise QgsProcessingException(msg)
                try:
                    #check for numeric Expression Data type 
                    a=int(abstand)
                    b=float(abstand) 
                except:
                    msg = self.tr("Feature(" + feature.id() + "): "+"Error Offset Experession result must be numeric, not " + str( type( abstand )) )
                    feedback.reportError(msg)
                    raise QgsProcessingException(msg)

                # get Profile Baseline by ID

                #profil_id of the profile feature
                expr = QgsExpression( vectorLayerBaselineIDFieldName )
                exprContext = QgsExpressionContext()
                exprContext.setFeature(feature)
                profil_id = expr.evaluate ( exprContext )   
                
                # baseline ID
                exprBaseLineID = QgsExpression( baselineIDFieldName )

                # remove quotes ""
                if baselineIDFieldName.startswith('\"'):
                    baselineIDFieldName = baselineIDFieldName.replace('\"', '')
                
                
                
                exprText = baselineIDFieldName + '=' + str(profil_id) 
                #feedback.pushInfo('waehle Basislinie: ' + exprText )
                exprBaseLine = QgsExpression( exprText )

                selection = baseLineLayer.getFeatures( QgsFeatureRequest( exprBaseLine ) )
                
                baseLineFeature = next( selection )
                linRef = LinearReferencingMaschine( baseLineFeature.geometry(), crsProject, feedback)
                
                #feedback.pushInfo("Profil_id: " + str( profil_id ) + ' feature: ' + str( feature.attributes() ) )
                geom = feature.geometry()
                
                feedback.pushInfo( "srcgeom: " + str( geom.asWkt() ) )

                subFeatureList=[]

                layerUtils=LayerUtils( crsProject, feedback)
                subFeatureList=layerUtils.multiPartToSinglePartFeature( feature )
                feedback.pushInfo( "subFeatureList: " + str( len( subFeatureList ) ) )

      
                
                #preparation of profile geometrys
                prepSubFeatureList=[]
                for iP, f in enumerate(subFeatureList):
                    if linRef.isSimpleLine or vectorLayer.geometryType() == 0 or vectorLayer.geometryType() == 1: #Point (Line nur temporär):
                        prepSubFeatureList.append( f ) #keep old feature                
                    else:
                        # Basisline hat Knickpunkte, Profilgeometrien müssen ggf. mit zusätzlichen Stützpunkten gefüllt werden
                        # Baseline has breakpoints, we have to fill the profile geometrys with additional vertices
                        filledSingleGeom = None
                        if vectorLayer.geometryType() == 2: #Polygon
                            filledSingleGeomList = self.fillPolygonVertices( f.geometry() , linRef, crsProject, feedback)
                        #elif vectorLayer.geometryType() == 1: #Line
                        
                        if len(filledSingleGeomList) > 0:
                            for g in filledSingleGeomList:
                                #create a feature for each filled sub geometry
                                filledFeature=QgsFeature( f )
                                filledFeature.setGeometry( g )
                                filledFeature.setAttributes( f.attributes() )
                                prepSubFeatureList.append( filledFeature )
                        else:
                            prepSubFeatureList.append( f ) #keep old feature
                            feedback.reportError( "Feature geometry can not be filled: " + str( f.attributes() ) )

                feedback.pushInfo( "prepSubFeatureList: " + str( len( prepSubFeatureList ) ) )
                
                
                #Back to Real World Transformation for each sub Feature
                realWorldSubFeatureList=[]
                for pFeat in prepSubFeatureList:
                
                    #Create Real World geometry with LinearReferencingMaschine
                    realWorldFeat=linRef.transformProfileFeatureToRealWorld( pFeat, vectorLayer.crs(), feedback, abstand, ueberhoehung )
                    realWorldSubFeatureList.append( realWorldFeat )
                    feedback.pushInfo( str( realWorldFeat.geometry().asWkt() ) )
                    
                ##### ggf features könnten hier wieder gruppiert werden ######
                    
                #write real worl Features to output layer
                for rwFeat in realWorldSubFeatureList:
                    sink.addFeature(rwFeat, QgsFeatureSink.FastInsert)
     
     
                i=i+1
                # Update the progress bar
                feedback.setProgress(int(i * total))
        
            except:
                msg = self.tr("Error on Feature " + str(i)+ " "+ str(feature.attributes()) )
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
        
        
        
        msgInfo = self.tr(str(i) + " Features were transformed to real world coordinates")
        feedback.pushInfo(msgInfo)
        # Return the results of the algorithm. In this case our only result is
        return {self.OUTPUT: dest_id}
        #
        #    print("ERROR:", err.args, repr( err ), "Fehler: " )
        
        
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
        feedback.pushInfo( str( counter ) + " Profile Baslines processed" )
        
        return {self.OUTPUT: dest_id}


    def runPointsForBaseline(self, vectorLayer, baseLineLayer, buffer, rasterLayer, ueberhoehung, zField, zFieldStart, zFieldEnd, context, feedback):
    
        profil_points_layer = processing.run("thtoolbox:points_bore_axis", { 
                            'INPUTBUFFER' : buffer,
                            'INPUTVECTORLAYER' : vectorLayer.source(),
                            'INPUTRASTER' : rasterLayer.source(), #'//tlugjfs2/laserscandaten/dgm1_grid/dgm1'
                            'INPUTVECTOR' : baseLineLayer.source(), #'M:/transfer/Kürbs/TH-Profile/th_profile.shp|layername=th_profile'
                            'INPUTZFACTOR' : ueberhoehung,
                            'INPUTZFIELD' : zField,
                            'INPUTZFIELDEND' : zFieldEnd,
                            'INPUTZFIELDSTART' : zFieldStart,
                            'OUTPUT' : 'TEMPORARY_OUTPUT'
                            }, context=context, feedback = feedback)['OUTPUT']

        return profil_points_layer.getFeatures()
        
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr('points_bore_axis_all_baselines')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Points (incl. Bore Axis) All Baselines')


    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self.__doc__)

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('To Profile Coordinates')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'To Profile Coordinates'
        
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_Points_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_PointsForAllLines()

