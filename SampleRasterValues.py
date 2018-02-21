# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 Extract Raster Values to Point Layer
 TLUG Algorithms
                              -------------------
        begin                : 2017-11-28
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
__date__ = '2017-11-28'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import sys
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import QVariant
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorDataProvider
from qgis.core import QgsPoint
from qgis.core import QgsFeature
from qgis.core import QgsGeometry
from qgis.core import QgsError
from qgis.core import QgsField
from qgis.core import QgsWKBTypes
from qgis.core import QgsRaster
from qgis.core import QGis


import datetime
import struct
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException


from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.parameters import ParameterRaster
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector


class SampleRasterValues(GeoAlgorithm):
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
    INPUT_POINT_LAYER = 'INPUT_POINT_LAYER'
    INPUT_RASTER_LAYER = 'INPUT_RASTER_LAYER'
    #FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    USE_NULL = 'USE_NULL'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name, self.i18n_name = self.trAlgorithm('Sample Raster Values to Point Layer')

        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('Raster tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterRaster(self.INPUT_RASTER_LAYER, self.tr('Input Raster')))
        
        #set to optional
        self.addParameter(ParameterVector(self.INPUT_POINT_LAYER, self.tr('Point Layer'),[ParameterVector.VECTOR_TYPE_POINT]))
        
        # We add a Vectorlayer as Output
        self.addOutput(OutputVector(self.OUTPUT, self.tr('Points with Raster Values'), [ParameterVector.VECTOR_TYPE_POINT]))

  
    
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputRasterFilename = self.getParameterValue(self.INPUT_RASTER_LAYER)
        inputPointFilename=self.getParameterValue(self.INPUT_POINT_LAYER)
        outputFileName = self.getOutputValue(self.OUTPUT) #self.getParameterValue(self.OUTPUT)
        

        rasterLayer=dataobjects.getObjectFromUri(inputRasterFilename)
        inputPoints=dataobjects.getObjectFromUri(inputPointFilename)
        
        vectorWriter = None
        
        try:
            
            #Raster Konfiguration
            
            #GDAL
            dataset = gdal.Open(inputRasterFilename, GA_ReadOnly)
            geotransform = dataset.GetGeoTransform()
            band = dataset.GetRasterBand(1)
            bandtype = gdal.GetDataTypeName(band.DataType)

            newFieldName=rasterLayer.name()
            #check the field name-lenght because shapefile support max 10 characters
            if len(newFieldName)>10:
                newFieldName=left(newFieldName,10)
            
            fields = inputPoints.pendingFields()
            
            #check if the Fieldname already exists. if True, add a Number on the end of the Fieldname
            isDuplicate=self.isNameInQgsFieldList(newFieldName, fields, True)
            if isDuplicate:
                newFieldName=self.getUniqueFieldName(newFieldName, fields, 0)
            
            fieldType=self.getDataTypeFromRasterBand(bandtype)
            newField=QgsField( newFieldName, fieldType)
            fields.append(newField)
            
            vectorWriter = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields,
            QgsWKBTypes.multiType(QGis.fromOldWkbType(inputPoints.wkbType())),
            inputPoints.crs())
            
            #Index new Field
            fidx = len(fields)-1 

            fieldType = fields[fidx].type()
            
            startTime= datetime.datetime.now()
            print startTime
            
            #check if pointsLayer is emty
            if inputPoints.featureCount!=0:
                # get Raster Values for each point features in the vectorlayer
                newFeatures=self.getFeaturesRasterValuesAtFeatures(progress, rasterLayer , inputPoints, fields, fidx, False)
            
            else:
                raise GeoAlgorithmExecutionException(self.tr('source layer is emty'))
            
            #Look if new features are there

            if len(newFeatures)>0:
                self.schreibeFeatures(newFeatures, vectorWriter)
                progress.setInfo(str(len(newFeatures))+self.tr(' processed'))
            else:
                print "No features were processed"
                raise GeoAlgorithmExecutionException(self.tr("No features were processed"))
                
        except GeoAlgorithmExecutionException as e:
            print e.msg
            print e.stack
            print e.cause

        except Exception as e:
            #print e.errno, e.strerror
            print e.message()
            print e.summary()
            raise GeoAlgorithmExecutionException(self.tr("No features were processed"))
            #ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
            #    self.tr('Feature  error'))
                
        del vectorWriter
        endTime= datetime.datetime.now()
        
        print endTime
    
    def makeSingleFeaturesFromMultiPoint(self, vectorLayer):
        new_features = []
        for feature in vectorLayer.getFeatures():
            geom=feature.geometry()
            if geom.isMultipart():
                for part in geom.asGeometryCollection():
                    temp_feature = QgsFeature(feature)
                    temp_feature.setGeometry(part)
                    new_features.append(temp_feature)
        return new_features

    # get the Raster Values for the existing point features in the vectorlayer
    def getFeaturesRasterValuesAtFeatures(self, progress, rasterLayer, vectorLayer, fields, fieldIndex, interpolation=False):
        featureList=[]
        feats=None
        countFeats=0
        #check layer geometry type
        if not vectorLayer.wkbType()==1: #Point:
            if vectorLayer.wkbType()==4: #MultiPoint:
                #make a Layer with single Features
                feats=self.makeSingleFeaturesFromMultiPoint(vectorLayer)
                countFeats=len(feats)
            else:
                ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, self.tr('Layertype is not Point. Just Point type is supported'))
                raise GeoAlgorithmExecutionException(self.tr('Layertype is not Point. Just Point type is supported'))
        else:
            feats, countFeats = self.getFeatures(vectorLayer)
            print 'Layertype is valid (Point)' 
        
        if interpolation:
            pass # not implemented yet
            #ermittle Abstand von zentrum der Rasterzelle
            #ermittle umgebende Raster-Zellen
    
        
        #iterate points

        if countFeats == 0: 
            raise GeoAlgorithmExecutionException(self.tr('no Features in source layer'))
        for feature in feats:
            geom = feature.geometry()

            total = 100.0 / countFeats # 

            attrs=feature.attributes()
            #new Feature
            newFeature = QgsFeature(fields)

            pinPoint=geom.asPoint()
            rastSample = rasterLayer.dataProvider().identify(pinPoint, QgsRaster.IdentifyFormatValue).results()
            #for rastVal in rastSample:
            rastVal=rastSample[1]
            attrs.append(rastVal)
            newFeature.setAttributes(attrs) #take the attributes from source feature
            newFeature.setGeometry(geom)

            featureList.append(newFeature)
            progress.setPercentage(int(countFeats * total))

        return featureList
    

    
    
    #delivers True, if a name is in a list
    def isNameInQgsFieldList(self, name, list, ignoreCase):

        for field in list:
            #handle ignore case
            fName=field.name()
            if ignoreCase:
                name=name.upper()
                fName=fName.upper()
            #compare the fieldnames
            if fName==name:
                return True
        
        return False
    
    def getUniqueFieldName(self, fieldName, fields, counter):
        print 'Counter:', counter
        lenCounter=len(str(counter))
        lenFieldname=len(fieldName)
        if (lenFieldname+lenCounter)>10:

            lenStr=10-lenCounter
            newFieldName=fieldName[:lenStr] + str(counter)
        else:
            newFieldName=fieldName+str(counter)

        isDuplicte=self.isNameInQgsFieldList(newFieldName, fields, True)
        if isDuplicte:
            newFieldName=self.getUniqueFieldName(fieldName, fields, counter+1)
        return newFieldName

    def schreibeFeatures(self, features, vectorWriter):
        
        try:
        
            for feat in features:
                vectorWriter.addFeature(feat)

            print len(features), self.tr("Features wrote")
            
        except IOError as e:
            print "DP I/O error({0}): {1}".format(e.errno, e.strerror)
        except ValueError:
            print "Werte-Error"
        except QgsError as qGisErr:
            print qGisErr.message()
            print qGisErr.summary()
        except:
            #print "Unexpected error:", str(sys.exc_info()[0])
            print "Error VectorWriter"
            #print "Error Dataprovider" + str(vectorLayer.dataProvider().error())
            raise GeoAlgorithmExecutionException(self.tr('Can not write features to new layer!'))# + str(sys.exc_info()[0]))

    
    #This function is for getting the features for the processing "ALL" or "SELECTED"
    def getFeatures(self, vectorLayer):
        selCount=vectorLayer.selectedFeatureCount()
        count=0
        features=None
        if selCount>0: #Check the Connection Condition
            features = vectorLayer.selectedFeatures()
            count=selCount
        else:
            features = vectorLayer.getFeatures()
            count=vectorLayer.featureCount()
        #print 'Src-Layer:', count, " Objekte"
        return features,count
    
    def getDataTypeFromRasterBand(self, bandtype):
        if bandtype == 'Byte':
            return QVariant.Int
        elif bandtype == 'Int16':
            return QVariant.Int
        elif bandtype == 'UInt16':
            return QVariant.Int
        elif bandtype == 'Int32':
            return QVariant.Int
        elif bandtype == 'UInt32':
            return QVariant.Int
        elif bandtype == 'Float32':
            return QVariant.Double
        elif bandtype == 'Float64':
            return QVariant.Double
        else:
            raise GeoAlgorithmExecutionException(self.tr('Raster format not supported'))
            