#from ggis.processing import alg
#@alg(name= profileEachLine, label="Baselinefor all Lines of Layer",groop="To Profile Coordinates"

# -*- coding: utf-8 -*-

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
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsField,
                       QgsFeature)
import processing


class TransformToProfil_GradientForAllLines(QgsProcessingAlgorithm):
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

    INPUTBASELINE = 'INPUTVECTOR'
    vectorLayer=None
    INPUTRASTER = 'INPUTRASTER'
    rasterLayer = None
    INPUTZFACTOR = 'INPUTZFACTOR'
    ueberhoehung = 0
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
        return 'Baseline_all_lines'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Baseline for all Lines of Layer')

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
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTBASELINE,
                self.tr('Profil Baselines'),
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
                self.tr('Raster_Gradients')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        self.ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        self.rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        self.vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=self.vectorLayer.fields()
        fields.append( QgsField( "z_factor" ,  QVariant.Int) ) 

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if self.vectorLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            self.vectorLayer.wkbType(),
            self.vectorLayer.sourceCrs()
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
        if len( self.vectorLayer.selectedFeatures() ) > 0:
            features = self.vectorLayer.selectedFeatures()
        else:
            features = [feat for feat in self.vectorLayer.getFeatures()]
        feedback.pushInfo( 'Features {} used'.format( len( features ) ) )

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len( features ) if len( features ) else 0
        
        #Clear Selection
        self.vectorLayer.removeSelection()
        
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            
            #select to current feature
            self.vectorLayer.select( feature.id() )
            #create profile feature for selected line 
            #if False:
            feedback.pushInfo( "Selection " + str( self.vectorLayer.selectedFeatureCount() ) + " Objects"  )
            gradient_feature = self.runBaseLine(self.vectorLayer, context, feedback)

            newFeature = QgsFeature( fields )
            attrs=gradient_feature.attributes()
            attrs.append( self.ueberhoehung )
            newFeature.setAttributes( attrs )
            newFeature.setGeometry( gradient_feature.geometry() )
            
            #Clear Selection
            self.vectorLayer.removeSelection()
            # Add a feature in the sink
            sink.addFeature(newFeature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

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
    
    def runBaseLine(self, baselineLayer, context, feedback):
    
        profil_gradient_layer = processing.run("Tlug:Raster_Gradient", { 
                            'INPUTRASTER' : self.rasterLayer.source(), #'//tlugjfs2/laserscandaten/dgm1_grid/dgm1'
                            'INPUTVECTOR' : self.vectorLayer.source(), #'M:/transfer/Kürbs/TH-Profile/th_profile.shp|layername=th_profile'
                            'INPUTZFACTOR' : self.ueberhoehung,
                            'OUTPUT' : 'memory:' 
                            }, context=context, feedback=feedback)['OUTPUT']
        gradient_feature = next(profil_gradient_layer.getFeatures(QgsFeatureRequest().setLimit(1)))
        
        return gradient_feature

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr('Raster_Gradient_All_Features')

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr( 'Raster Gradient (All Features)' )

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
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_Gradient_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_GradientForAllLines()