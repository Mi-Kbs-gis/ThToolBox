# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 Find duplicates
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
"""

__author__ = 'Michael Kürbs'
__date__ = '2018-07-31'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)


class FindDuplicates(QgsProcessingAlgorithm):
    """
    This is an algorithm that selects all duplicates in a table field.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    USE_NULL = 'USE_NULL'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        
        # self.addParameter(
            # ParameterTable(self.INPUT_LAYER,
                                        # self.tr('Input layer'), False
            # )
        # )
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_LAYER,
                                        self.tr('Input layer'), types=[QgsProcessing.TypeVectorAnyGeometry]))

        self.addParameter(QgsProcessingParameterField(self.FIELD,
                                                      self.tr('Selection attribute'),
                                                      parentLayerParameterName=self.INPUT_LAYER))

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT, self.tr('Selected (attribute)')))


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        fieldName = self.parameterAsString(parameters, self.FIELD, context)
        fields = vectorLayer.fields()
        fidx = vectorLayer.fields().lookupField(fieldName)
        print("Field ", fidx, fields[fidx].name())
        fieldType = fields[fidx].type()
        total = 100.0 / vectorLayer.featureCount() if vectorLayer.featureCount() else 0

        # And now we can process
        attributes=[]
        duplicates=[]
        index=0
        protokoll=[]
        #Iterating over Vector Layer
        iter = vectorLayer.getFeatures()
        for current, feature in enumerate(iter):
            try:
                #is the attribut in the list yet
                index=attributes.index(feature[fidx])

            except ValueError: # value is not in the list
                index = -1
            protokoll.append([str(feature[fidx]), "-->", str(index)])
            if index == -1: # add new attribute in the list
                attributes.append(feature[fidx])
          
            else: # it is a duplicate
                duplicates.append(feature.id())

            # Update the progress bar
            feedback.setProgress(int(current * total))
            
        vectorLayer.select(duplicates)#setSelectedFeatures(duplicates) 
        for item in protokoll:
            try:
                print(item)
            except:
                print("Fehler beim print")
        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        #print(str(len(duplicates)) + " objects selected.")
        return {self.OUTPUT: parameters[self.INPUT_LAYER]}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Find Duplicates'

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
        return 'Vector selection tools'

    def metadata(self):
        return self.tr('TLUG:Find Duplicates, Select duplicate values in a feature field.')

    def description(self):
        return self.tr('Processing', 'Select duplicate values in a feature field.')

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FindDuplicates()
