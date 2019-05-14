# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 TransformToProfil_TranslateProfilOrigin
 TLUBN Algorithms
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
__date__ = '2019-05-10'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'


"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsField,
                       QgsFeature)
import processing
import math
import os

class TransformToProfil_ShiftProfileOrigin(QgsProcessingAlgorithm):
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

    INPUTBASELINE_SOURCE = 'INPUTBASELINE_SOURCE'
    INPUTBASELINE_TARGET = 'INPUTBASELINE_TARGET'
    INPUT_PROFILLAYER = 'INPUT_PROFILLAYER'
    
    SOURCE_BASLINE_ID = 'SOURCE_BASLINE_ID'
    TARGET_BASLINE_ID = 'TARGET_BASLINE_ID'
    
    PROFIL_ID = 'PROFIL_ID'


    profileLayer = None
    sourceBaseLineLayer = None
    targetBaseLineLayer = None
    OUTPUT = 'OUTPUT'
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'shift_profil_origin'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Shift Profile-Origin (X-Axis)')

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
        return self.tr("This function is shifting a profile geometry along x axis. The X - Offset is determinated by the distance between 2 related cross section baselines. The relationship between the two baselines is performed by a join based on the profile key.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # input layer with profile geometrys.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_PROFILLAYER,
                self.tr('input profile layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        # baseline in source profil system
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE_SOURCE,
                self.tr('source baseline layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SOURCE_BASLINE_ID,
                self.tr('Field with source baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE_SOURCE
            )
        )

        # baseline in target profil system
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE_TARGET,
                self.tr('target baseline layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )


        self.addParameter(
            QgsProcessingParameterExpression(
                self.TARGET_BASLINE_ID,
                self.tr('Field with target baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE_TARGET
            )
        )

        
        # Profil ID - Manuelle Eingabe
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PROFIL_ID,
                self.tr('Profil-ID / primary key'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                
            )
        )
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('shifted profil layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        self.profil_id = self.parameterAsInt(parameters, self.PROFIL_ID, context)
        self.profileLayer = self.parameterAsVectorLayer(parameters, self.INPUT_PROFILLAYER, context)
        
        self.sourceBaseLineLayer  = self.parameterAsVectorLayer( parameters, self.INPUTBASELINE_SOURCE, context)
        self.targetBaseLineLayer = self.parameterAsVectorLayer( parameters, self.INPUTBASELINE_TARGET, context)
        
        self.sourceExprSourceBaseLineId = self.parameterAsExpression(parameters, self.SOURCE_BASLINE_ID, context)
        self.targetExprSourceBaseLineId = self.parameterAsExpression(parameters, self.TARGET_BASLINE_ID, context)
      
        
        
        # Basislinie des lokaler Layer für die profil_id
        pkt_lokal = self.getFirstVertexOfBaseLine( self.sourceBaseLineLayer, self.profil_id, self.sourceExprSourceBaseLineId, feedback)

        # landesweitem Layer die Basislinie für die profil_id
        pkt_landesweit = self.getFirstVertexOfBaseLine( self.targetBaseLineLayer, self.profil_id, self.targetExprSourceBaseLineId, feedback)

        # Berechne Entfernung zwischen den Punkten, entspricht der Verschiebung in X-Richtung
        xOffset = self.get2PointsDistance( pkt_lokal , pkt_landesweit )
        
        translated_layer = self.runTranslateLayerGeometrys( self.profileLayer, xOffset, context, feedback)
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=self.profileLayer.fields()

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if self.profileLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_PROFILLAYER))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            self.profileLayer.wkbType(),
            self.profileLayer.sourceCrs()
        )

        # Send some information to the user
        #feedback.pushInfo('CRS is {}'.format(profileLayer.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
            
        sink.addFeatures( translated_layer.getFeatures() )

        # # To run another Processing algorithm as part of this algorithm, you can use
        # # processing.run(...). Make sure you pass the current context and feedback
        # # to processing.run to ensure that all temporary layer outputs are available
        # # to the executed algorithm, and that the executed algorithm can send feedback
        # # reports to the user (and correctly handle cancelation and progress reports!)


            
            
            
        # # Return the results of the algorithm. In this case our only result is
        # # the feature sink which contains the processed features, but some
        # # algorithms may return multiple feature sinks, calculated numeric
        # # statistics, etc. These should all be included in the returned
        # # dictionary, with keys matching the feature corresponding parameter
        # # or output names.
        
        
        return {self.OUTPUT: dest_id}
        
    
    #def getFirstVertexOfBaseLine( self, layer, profil_id, fieldId, feedback):
    def getFirstVertexOfBaseLine( self, layer, profil_id, keyExpression, feedback):

        firstPoint = None
        
        #fieldName = layer.fields()[fieldId].name()
        
        # Filter in landesweitem Layer die Basislinie für die profil_id
        #expr = ('"{0}" = {1}').format(fieldName, profil_id)
        exprText = ('{0} = {1}').format(keyExpression, profil_id)
        feedback.pushInfo("Expression: " + exprText )
        expr = QgsExpression( exprText )
        #layer.selectByExpression( expr, QgsVectorLayer.SetSelection)
        selection = layer.getFeatures( QgsFeatureRequest( expr ) )   
        
        feature = next( selection )
        feedback.pushInfo("Profil_id: " + str( profil_id ) + ' feature: ' + str( feature.attributes() ) )
        geom = feature.geometry()
        
        firstPoint = geom.vertexAt(0)
        feedback.pushInfo( 'firstPoint: ' + str( geom.asWkt() ) )

        #request = QgsFeatureRequest().setFilterFid(id)
        #feature = next(vector_layer.getFeatures(request))
        # hole ersten Stützpunkt
        
        return firstPoint
    
    def get2PointsDistance( self, point1, point2 ):
    
        dx = point2.x() - point1.x()
        dy = point2.y() - point1.y()
        
        distance = math.sqrt( dx*dx + dy*dy )
        
        return distance
    
    def runTranslateLayerGeometrys( self, translateLayer, xOffset, context, feedback):
    
        translated_layer = processing.run("native:translategeometry", { 
                            'DELTA_M' : 0, 
                            'DELTA_X' : xOffset, 
                            'DELTA_Y' : 0,
                            'DELTA_Z' : 0,
                            'INPUT' : translateLayer.publicSource(),
                            'OUTPUT' : 'memory:' 
                            }, context=context, feedback=feedback)['OUTPUT']
        #gradient_feature = next(translated_layer.getFeatures(QgsFeatureRequest().setLimit(1)))
        
        return translated_layer

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_ShiftProfileOrigin_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_ShiftProfileOrigin()