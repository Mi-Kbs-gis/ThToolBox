# -*- coding: utf-8 -*-
#from ggis.processing import alg
#@alg(name= profileEachLine, label="Baselinefor all Lines of Layer",groop="To Profile Coordinates"


__author__ = 'Michael Kürbs'
__date__ = '2019-06-03'
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
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsField,
                       QgsFeature,
                       QgsExpression,
                       QgsExpressionContext)
import processing
import os


class TransformToProfil_PolygonIntersectionForAllLines(QgsProcessingAlgorithm):
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
    OUTPUTGEOMTYPE = 'OUTPUTGEOMTYPE'
    SOURCE_BASLINE_ID = 'SOURCE_BASLINE_ID'

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUTINTERSECTIONLAYER,
                self.tr('Intersection Polygon Layer'),
                [QgsProcessing.TypeVectorPolygon]
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
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SOURCE_BASLINE_ID,
                self.tr('Field with baseline primary key (must be unique!)'),
                parentLayerParameterName=self.INPUTBASELINE
            )
        )
        geomTypes = [self.tr('Lines'),
                      self.tr('Points')]        
        self.addParameter(QgsProcessingParameterEnum(
            self.OUTPUTGEOMTYPE,
            self.tr('Output Geometry Type'),
            options=geomTypes, defaultValue=0))


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Profil_Polygon Intersections')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        baseLineLayer = self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        polygonLayer =  self.parameterAsVectorLayer(parameters, self.INPUTINTERSECTIONLAYER, context)
        outputGeomType = self.parameterAsEnum(parameters, self.OUTPUTGEOMTYPE, context)
        exprBaselineID = self.parameterAsExpression(parameters, self.SOURCE_BASLINE_ID, context)
        
        mywkbType=None
        if outputGeomType == 1: #'Points':
            mywkbType = 1
            
        else: #0 Lines
        
            mywkbType = 2
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        fields=polygonLayer.fields()
        fields.append( QgsField( "z_factor" ,  QVariant.Int) ) # will be added and filled by Subprocess (algorithm_TransformToProfil_PolygonIntersection.py)
        fields.append( QgsField( "profil_id" ,  QVariant.Int) ) 

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if polygonLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            mywkbType,
            polygonLayer.sourceCrs()
        )
        #try:

        # Send some information to the user
        #feedback.pushInfo('CRS is {}'.format(polygonLayer.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features=[] #QgsFeatureIterator
        if len( baseLineLayer.selectedFeatures() ) > 0:
            features = baseLineLayer.selectedFeatures()
        else:
            features = [feat for feat in baseLineLayer.getFeatures()]
        feedback.pushInfo( 'Features {} used'.format( len( features ) ) )

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len( features ) if len( features ) else 0
        #names = [field.name()+"; " for field in fields]
        #feedback.pushInfo(''.join( names ) )
        #Clear Selection
        baseLineLayer.removeSelection()
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
            baseLineLayer.select( feature.id() )
            #create profile feature for selected line 
            #if False:
            #feedback.pushInfo( "Selection " + str( polygonLayer.selectedFeatureCount() ) + " Objects"  )
            feedback.pushInfo("Counter: " + str(counter) )
            gradient_features = None
            try:
                gradient_features = self.runPolygonIntersection( polygonLayer, baseLineLayer, rasterLayer, ueberhoehung, outputGeomType, context, feedback)
                count=0
                for grFeature in gradient_features:
                    #feedback.pushInfo("Type: " + str(type(grFeature)) )
                    if not str(type(grFeature)) == "<class 'qgis._core.QgsFeature'>":
                        feedback.pushInfo("Abbruch Type: " + str(type(grFeature)) )
                        break

                    newFeature = QgsFeature( fields )
                    attrs = grFeature.attributes()
                    #attrs.append( ueberhoehung ) # Wird bereits in runPolygonIntersection zugefügt
                    attrs.append( profilID )
                
                    newFeature.setAttributes( attrs )
                    newFeature.setGeometry( grFeature.geometry() )
                    # Add a feature in the sink
                    sink.addFeature( newFeature, QgsFeatureSink.FastInsert)
                    count=count+1
                print( "Count: " + str(count) + ' at profile ' + str( profilID ) )
                feedback.pushInfo("Count: " + str(count) + ' at profile ' + str( profilID ) )
            except Exception as err:
                print("ERROR at profile " + str( profilID ) + ': '+ str(err.args) + " " + str(repr( err )) + " Fehler: "  )
                feedback.pushInfo("ERROR at profile " + str( profilID ) + ': '+ str(err.args) + " " + str(repr( err )) + " Fehler: "  )


            #Clear Selection
            baseLineLayer.removeSelection()

            # Update the progress bar
            feedback.setProgress(int(current * total))
            counter=counter+1
        #except Exception as err:
        #    feedback.pushInfo("ERROR: "+ str(err.args) + " " + str(repr( err )) + " Fehler: "  )
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
        return {self.OUTPUT: dest_id}
    
    def runPolygonIntersection(self, polygonLayer, baseLineLayer, rasterLayer, ueberhoehung, outputGeomType,  context, feedback):
    
        profil_gradient_layer = processing.run("thtoolbox:Polygon_Baseline_Intersections", { 
                            'INPUTINTERSECTIONLAYER' : polygonLayer.source(),
                            'INPUTRASTER' : rasterLayer.source(), #'//tlugjfs2/laserscandaten/dgm1_grid/dgm1'
                            'INPUTVECTOR' : baseLineLayer.source(), #'M:/transfer/Kürbs/TH-Profile/th_profile.shp|layername=th_profile'
                            'INPUTZFACTOR' : ueberhoehung,
                            'OUTPUT' : 'memory:',
                            'OUTPUTGEOMTYPE' : outputGeomType #2-->Lines
                            }, context=context, feedback=feedback)['OUTPUT']
        #gradient_feature = next(profil_gradient_layer.getFeatures(QgsFeatureRequest().setLimit(1)))
        
        return profil_gradient_layer.getFeatures()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'polygon_baseline_intersection_all_lines'



    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr( 'Polygon - Baseline Intersections (Multi Baseline)' )

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("This algorithm performs the function 'Polygon - Baseline Intersection' for all lines of a line layer.")

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
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/TransformToProfil_LineIntersection_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
    
    def createInstance(self):
        return TransformToProfil_PolygonIntersectionForAllLines()