# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                TransformToProfil_Gradient
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
__date__ = '2023-12-20'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProject,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsProcessingException)
from .tlug_utils.TerrainModel import TerrainModel
from .tlug_utils.LaengsProfil import LaengsProfil
from PyQt5.QtGui import QIcon
import os

class TransformToProfil_Gradient(QgsProcessingAlgorithm):
    """
    Transforms a single Line to profile coordinates with considering of elevation.
    A baseline can have breakpoints.
    Select one line feature or use an one feature layer as Baseline.
    NoData, zero and negative Values in the elevation raster can excluded in the final output line.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUTBASELINE = 'INPUTBASELINE'
    INPUTRASTER = 'INPUTRASTER'
    INPUTZFACTOR='INPUTZFACTOR'
    USE_ZERODATA='USE_ZERODATA'
    USE_NEGATIVEDATA='USE_NEGATIVEDATA'
    USE_NODATA='USE_NODATA'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
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
                self.tr('Baseline Gradient')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        ueberhoehung = self.parameterAsInt(parameters, self.INPUTZFACTOR, context)
        rasterLayer = self.parameterAsRasterLayer(parameters, self.INPUTRASTER, context)
        noDataValue = -9999 # defined in TerrainModel()
        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUTBASELINE, context)
        use_zerodata = self.parameterAsBoolean(parameters, self.USE_ZERODATA, context)
        use_nodata = self.parameterAsBoolean(parameters, self.USE_NODATA, context)
        use_negativeData = self.parameterAsBoolean(parameters, self.USE_NEGATIVEDATA, context)
        
        
        
        feedback.pushInfo("use_nodata:" + str(use_nodata))
        feedback.pushInfo("use_negativeData:" + str(use_negativeData))
        feedback.pushInfo("use_zerodata:" + str(use_zerodata))
        
        baseLineFeature=None
        baseLine=None
        #Basline Layer must have only 1 Feature
        if vectorLayer.featureCount()==1:
        #baseLine must be the first feature
            baseLineFeature=next(vectorLayer.getFeatures(QgsFeatureRequest().setLimit(1)))
            baseLine=baseLineFeature.geometry()
        elif len(vectorLayer.selectedFeatures())==1:
            selection=vectorLayer.selectedFeatures()
            #baseLine must be the first feature
            selFeats=[f for f in selection]
            baseLineFeature=selFeats[0]
            baseLine=baseLineFeature.geometry() 
        else:
            msg = self.tr("Error: BaseLine layer needs exactly one line feature! "+ str(vectorLayer.featureCount()) + " Just select one feature!")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        #take CRS from Rasterlayer 
        crsProject=QgsProject.instance().crs()         
        #check if layers have the same crs
        if not vectorLayer.crs().authid()==crsProject.authid():
            # if not, transform to raster crs()
            trafo=QgsCoordinateTransform(vectorLayer.crs(),crsProject,QgsProject.instance())
            #transform BaseLine
            opResult=baseLine.transform(trafo,QgsCoordinateTransform.ForwardTransform, False)

        tm=TerrainModel(rasterLayer, feedback)
        noDataValue=tm.nodata
        #feedback.pushInfo("TerrainModel.nodata:" + str(noDataValue))
        lp=LaengsProfil(baseLine, tm, crsProject, feedback) # use baseLine in Projekt.crs
        lp.calc3DProfile()
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, vectorLayer.fields(), vectorLayer.wkbType(), crsProject)

        try:
            total = 100.0 / baseLine.length()
        except:
            msg = self.tr("No Baseline")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
        
        #bereinige LinienGeometry des Laengsprofils 
        profilLineFeats=[]
        try:
            profilLineFeats = lp.getCleanGradient(baseLineFeature, ueberhoehung, noDataValue, use_nodata, use_zerodata, use_negativeData)
        except:
            msg = self.tr("ProfilGradient can not clean on feature " + str(baseLineFeature.id()))
            feedback.reportError(msg)
           
        if len(profilLineFeats)>0:
            for i, profilFeat in enumerate(profilLineFeats):
                sink.addFeature(profilFeat, QgsFeatureSink.FastInsert)

            
        feedback.setProgress(int(100))

        msgInfo=self.tr("BaseLine was transformed to profile coordinates")
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
        return self.tr( 'raster_gradient' )

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr( 'Raster Gradient' )

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
        return TransformToProfil_Gradient()
