# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 Find duplicates
 TLUG Algorithms
                              -------------------
        begin                : 2017-10-25
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
"""

__author__ = 'Michael Kürbs'
__date__ = '2018-12-21'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (QgsExpression,
                       QgsProcessing,
                       QgsExpressionContext,
                       QgsVectorLayer,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterEnum,
                       QgsProcessingOutputVectorLayer)
from PyQt5.QtCore import QCoreApplication
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from PyQt5.QtGui import QIcon
import os



class SelectDuplicates(QgisAlgorithm):#QgsProcessingAlgorithm):
    """
    This is an algorithm that selects all duplicates in a table field or based of an Expression.
    """

    INPUT = 'INPUT'
    EXPRESSION = 'EXPRESSION'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Input layer'), types=[QgsProcessing.TypeVector]))

        self.addParameter(QgsProcessingParameterExpression(self.EXPRESSION,
                                                           self.tr('Expression'), parentLayerParameterName=self.INPUT))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT, self.tr('Selected (attribute)')))



    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT, context)
        expression = self.parameterAsString(parameters, self.EXPRESSION, context)
        expr=QgsExpression(expression)
        if expr.hasParserError():
            raise QgsProcessingException(expr.parserErrorString())

        context = QgsExpressionContext()

        count = vectorLayer.featureCount() if vectorLayer.featureCount() else 0
        total = 100.0 / count

        # And now we can process
        attributes=[]
        duplicates=[]
        index=0
        protokoll=[]
        #Iterating over Vector Layer
        iter = vectorLayer.getFeatures()
        for current, feature in enumerate(iter):
            try:
                #create value from Expression
                context.setFeature(feature)
                
                value=expr.evaluate(context)
            except:
                msg="Error while run Expression" + str( expr.expression() ) + " on feature " + str( feature.attributes() ) 
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
                
            try:
                #is the attribut in the list yet
                index=attributes.index(value)
                #index=attributes.index(feature[fidx])

            except ValueError: # value is not in the list
                index = -1
            except KeyError: # value is not in the list
                index = -1
            
            if index == -1: # add new attribute in the list
                attributes.append(value)
          
            else: # it is a duplicate
                duplicates.append(feature.id())

            # Update the progress bar
            proz=int( (current+1) * total)
            feedback.setProgress( proz )
        feedback.pushInfo( str( len(duplicates) ) +  "  duplicates were selected!")
        if len( duplicates ) > 0:
            vectorLayer.select(duplicates)
            

        return {self.OUTPUT: parameters[self.INPUT]}

    def name(self):

        return 'Select_Duplicates'

    def displayName(self):

        return self.tr('Select Duplicates')

    def group(self):
        return self.tr('Vector selection')

    def groupId(self):
        return 'vectorselection'

    def __init__(self):
        super().__init__()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def metadata(self):
        return self.tr('TLUG:Find Duplicates, Select duplicate values in a feature field.')

    def description(self):
        return self.tr('Processing', 'Select duplicate values in a feature field.')

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self.__doc__)
    
    def helpUrl(self):
        return self.tr('https://github.com/Mi-Kbs-gis/TlugProcessing')

    def tags(self):
        tags=[]
        tags.append("duplicate")
        tags.append("Duplikate")
        tags.append("redundant")
        tags.append("doppelt Einträge")
        tags.append("select")
        tags.append("mark")
        tags.append("Auswahl")
        tags.append("auswählen")
        return tags
        
   
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/SelectDuplicates_Logo.png'))


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SelectDuplicates()

