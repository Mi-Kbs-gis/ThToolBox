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
from PyQt5.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsField,
                       QgsFeature,
                       QgsExpression,
                       QgsExpressionContext)
import processing
import os


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

    INPUTBASELINE = 'INPUTBASELINE'
    vectorLayer=None
    INPUTRASTER = 'INPUTRASTER'
    rasterLayer = None
    INPUTZFACTOR = 'INPUTZFACTOR'
    ueberhoehung = 0
    use_zerodata = False
    use_nodata = True
    use_negativeData = False

    OUTPUT = 'OUTPUT'
    
    USE_ZERODATA='USE_ZERODATA'
    USE_NEGATIVEDATA='USE_NEGATIVEDATA'
    USE_NODATA='USE_NODATA'
    SOURCE_BASLINE_ID = 'SOURCE_BASLINE_ID'
    
    #USE_SELECTION = 'USE_SELECTION'
    #IS_MULTI = 'IS_MULTI'
    

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
        
        # self.addParameter(
            # QgsProcessingParameterBoolean (
            # self.USE_SELECTION, 
            # self.tr('only the selected base lines'), 
            # True, 
            # False
            # )
        # )            

        # self.addParameter(
            # QgsProcessingParameterBoolean (
            # self.IS_MULTI, 
            # self.tr('Multi-Base-Line-Modus (features will processed for several base line)'), 
            # False, 
            # False
            # )
        # )            

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
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SOURCE_BASLINE_ID,
                self.tr('Field with baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE
            )
        )
        self.addParameter(QgsProcessingParameterBoolean(
            self.USE_ZERODATA,
            self.tr('Use Raster Values = 0'),
            defaultValue=False,
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.USE_NEGATIVEDATA,
            self.tr('Use Raster Values < 0'),
            defaultValue=True,
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.USE_NODATA,
            self.tr('Use Raster NoData'),
            defaultValue=False,
        ))
        
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
        #self.use_selection = self.parameterAsBoolean(parameters, self.USE_SELECTION, context)
        #self.is_multi = self.parameterAsBoolean(parameters, self.IS_MULTI, context)
        self.ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        self.rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        self.vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        self.use_zerodata = self.parameterAsBoolean(parameters, self.USE_ZERODATA, context)
        self.use_nodata = self.parameterAsBoolean(parameters, self.USE_NODATA, context)
        self.use_negativeData = self.parameterAsBoolean(parameters, self.USE_NEGATIVEDATA, context)
        exprBaselineID = self.parameterAsExpression(parameters, self.SOURCE_BASLINE_ID, context)

        
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=self.vectorLayer.fields()
        fields.append( QgsField( "z_factor" ,  QVariant.Int) ) 
        #fields.append( QgsField( "profil_id" ,  QVariant.Int) ) 

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

        features=[] 
        
        # if self.use_selection == True: # use only Selection
        if len( self.vectorLayer.selectedFeatures() ) > 0:
            features = self.vectorLayer.selectedFeatures()
        else:
             # raise QgsProcessingException(self.tr( 'Seletion of base line layer is empty. Uncheck "only the selected base lines" option if not needed!'))
            # else: # use all
            features = [feat for feat in self.vectorLayer.getFeatures()]

       
        if len( features ) == 0:
            raise QgsProcessingException(self.tr( 'No base line features availible. Please check processing parameters configuration and base line layer including selection!'))
        
        # if self.is_multi == False:
            # if len( features ) > 1:
                # raise QgsProcessingException(self.tr('More than 1 base line features comes from the base line layer ({}) by this processing parameters configuration. If you would like to proceed it on 1 profile base line, select your mean base line and check "only the selected base lines". If you need to process by several profile base lines, check "Multi-Base-Line-Modus".'.format(self.vectorLayer.name())))
        
        feedback.pushInfo( 'Features {} used'.format( len( features ) ) )
         
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len( features ) if len( features ) else 0
        
        #Clear Selection
        self.vectorLayer.removeSelection()
        counter=0
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            expr = QgsExpression( exprBaselineID )
            exprContext = QgsExpressionContext()
            exprContext.setFeature(feature)
            
            profilID = expr.evaluate ( exprContext ) #, baseLineLayer.fields() )
            feedback.pushInfo(str(exprBaselineID) + ": Profil-ID: " + str(profilID) )
            #select to current feature
            self.vectorLayer.select( feature.id() )
            #create profile feature for selected line 
            #if False:
            feedback.pushInfo( "Selection " + str( self.vectorLayer.selectedFeatureCount() ) + " Objects"  )
            feedback.pushInfo("Counter: " + str(counter) )
            gradient_features = self.runBaseLine(self.vectorLayer, context, feedback)
            feedback.pushInfo(' Profil ' + str(exprBaselineID) +': '+ str(profilID))
            i=0
            for gradient_feature in gradient_features:
                if not str(type(gradient_feature)) == "<class 'qgis._core.QgsFeature'>":
                    feedback.pushInfo("Abort because of wrong object type: " + str(type(gradient_feature)) + ' --> QgsFeature needed' )
                    break
                # kommt hier nicht an !!!!
                newFeature = QgsFeature( fields )
                attrs=gradient_feature.attributes()
                attrs.append( self.ueberhoehung )
                #attrs.append( profilID )
                newFeature.setAttributes( attrs )
                newFeature.setGeometry( gradient_feature.geometry() )
                feedback.pushInfo(str( profilID) +' Part '+ str(i)+' isValid: '+str(newFeature.isValid())+' attrs: '+str(attrs)+' geom: '+gradient_feature.geometry().asWkt())

                # Add a feature in the sink
                sink.addFeature(newFeature, QgsFeatureSink.FastInsert)
                #feedback.pushInfo('sink.addFeature( ' + str(status)+ '   '+ str(type(status)))
                i=i+1

            #Clear Selection
            self.vectorLayer.removeSelection()

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
    
    def runBaseLine(self, baselineLayer, context, feedback):
    
        profil_gradient_layer = processing.run("thtoolbox:raster_gradient", { 
                            'INPUTRASTER' : self.rasterLayer.source(), #'//tlugjfs2/laserscandaten/dgm1_grid/dgm1'
                            'INPUTBASELINE' : self.vectorLayer.source(), #'M:/transfer/Kürbs/TH-Profile/th_profile.shp|layername=th_profile'
                            'INPUTZFACTOR' : self.ueberhoehung,
                            'USE_ZERODATA' : self.use_zerodata,
                            'USE_NEGATIVEDATA' : self.use_negativeData,
                            'USE_NODATA' : self.use_nodata,
                            'OUTPUT' : 'memory:' 
                            }, context=context, feedback=feedback)['OUTPUT']
                        
                            
        return profil_gradient_layer.getFeatures()
       

        
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
        return 'raster_gradient_multi_baseline'

    
    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr( 'Raster Gradient (Multi Baseline)' )

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
        return self.tr("This algorithm performs the function 'Raster_Gradient' for all lines of a line layer.")

   
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_Gradient_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TransformToProfil_GradientForAllLines()