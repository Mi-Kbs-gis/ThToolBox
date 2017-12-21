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
__date__ = '2017-10-25'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterTable #ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector


class FindDuplicates(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    USE_NULL = 'USE_NULL'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name, self.i18n_name = self.trAlgorithm('Find duplicates')

        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('Vector selection tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterTable(self.INPUT_LAYER,
            self.tr('Input layer'), False))
        # self.addParameter(ParameterVector(self.INPUT_LAYER,
            # self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_ANY], False))

        self.addParameter(ParameterTableField(self.FIELD,
                                              self.tr('Selection attribute'), self.INPUT_LAYER))
        # We add a Selection as Output
        self.addOutput(OutputVector(self.OUTPUT, self.tr('Selected (attribute)'), True))


    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        fieldName = self.getParameterValue(self.FIELD)
        output = self.getOutputValue(self.OUTPUT_LAYER)

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        
        fields = vectorLayer.pendingFields()

        fidx = vectorLayer.fieldNameIndex(fieldName)
        fieldType = fields[fidx].type()

        # And now we can process
        attributes=[]
        duplicates=[]
        index=0
        #Iterating over Vector Layer
        iter = vectorLayer.getFeatures()
        for feature in iter:
            try:
                #is the attribut in the list yet
                index=attributes.index(feature[fidx])

            except ValueError: # value is not in the list
                index = -1

            if index == -1: # add new attribute in the list
                attributes.append(feature[fidx])
          
            else: # it is a duplicate
                duplicates.append(feature.id())

        vectorLayer.select(duplicates)#setSelectedFeatures(duplicates) 
        print str(len(duplicates)) + " objects selected."
        self.setOutputValue(self.OUTPUT, inputFilename)

