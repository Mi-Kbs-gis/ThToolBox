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
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorDataProvider
from qgis.core import QgsPoint
from qgis.core import QgsFeature
from qgis.core import QgsGeometry
from qgis.core import QgsError

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


class ExtractRasterValues(GeoAlgorithm):
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
        self.name, self.i18n_name = self.trAlgorithm('Extract Raster Values to Point Layer')

        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('Raster tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterRaster(self.INPUT_LAYER, self.tr('Input Raster')))


        # We add a Vectorlayer as Output
        self.addParameter(ParameterVector(self.OUTPUT_LAYER, self.tr('Target Point Layer'),[ParameterVector.VECTOR_TYPE_POINT]))
        #self.addOutput(OutputVector(self.OUTPUT, self.tr('Target Layer'), [ParameterVector.VECTOR_TYPE_POINT]))

        self.addParameter(ParameterTableField(self.FIELD,
                                              self.tr('Selection attribute'), self.OUTPUT_LAYER)) #self.OUTPUT))
    
    
    
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        fieldName = self.getParameterValue(self.FIELD)
        outputFileName = self.getParameterValue(self.OUTPUT_LAYER) #self.getOutputValue(self.OUTPUT_LAYER)

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        rasterLayer=dataobjects.getObjectFromUri(inputFilename)
        vectorLayer = dataobjects.getObjectFromUri(outputFileName)
        
        print rasterLayer.name() +" CRS " + str(rasterLayer.crs().authid ())
        print vectorLayer.name() +" CRS " + str(vectorLayer.crs().authid ())
        
        fields = vectorLayer.pendingFields()

        fidx = vectorLayer.fieldNameIndex(fieldName)
        fieldType = fields[fidx].type()
        
        startTime= datetime.datetime.now()
        print startTime

        # Teste ob Schreibrechte auf Ziel-Layer bestehen
        caps = vectorLayer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddFeatures:
            fields=vectorLayer.pendingFields()
            anzFeat=0
            #Raster Konfiguration
            dataset = gdal.Open(inputFilename, GA_ReadOnly)
            geotransform = dataset.GetGeoTransform()
            band = dataset.GetRasterBand(1)
            nodata = band.GetNoDataValue()
            bandtype = gdal.GetDataTypeName(band.DataType)
            
            numFeats=0
            features=[]
            for y in xrange(band.YSize):
                progress.setPercentage(y / float(band.YSize) * 100)
                scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1,
                                           band.DataType)
                if bandtype == 'Byte':
                    values = struct.unpack('B' * band.XSize, scanline)
                elif bandtype == 'Int16':
                    values = struct.unpack('h' * band.XSize, scanline)
                elif bandtype == 'UInt16':
                    values = struct.unpack('H' * band.XSize, scanline)
                elif bandtype == 'Int32':
                    values = struct.unpack('i' * band.XSize, scanline)
                elif bandtype == 'UInt32':
                    values = struct.unpack('I' * band.XSize, scanline)
                elif bandtype == 'Float32':
                    values = struct.unpack('f' * band.XSize, scanline)
                elif bandtype == 'Float64':
                    values = struct.unpack('d' * band.XSize, scanline)
                else:
                    raise GeoAlgorithmExecutionException('Raster format not supported')
                
                col=0
                #features=[]
                for value in values:
                    if value != nodata:
                        try:
                            geo=self.pixelToMap(col,y,geotransform)
                            feat = QgsFeature(fields)
                            
                            feat.setAttribute(fidx, value)
                            feat.setGeometry(QgsGeometry.fromPoint(geo))
                            features.append(feat)
                            #print str(geo.x()) + " " + str(geo.y()) + " " + str(value)
                        except IOError as e:
                            print "I/O error({0}): {1}".format(e.errno, e.strerror)
                        except ValueError:
                            print "Werte -Error"
                        except QgsError as qGisErr:
                            print qGisErr.message()
                            print qGisErr.summary()
                        except:
                            print str(geo.x()) + " " + str(geo.y()) + " " + str(value)
                            print "Unexpected error:", sys.exc_info()[0]
                            raise
                    col=col+1
                    
                    if len(features)==1000: #Datensaetze werden in Bloecken geschrieben-->Performance
                        #print len(features)
                        self.schreibeFeatures(features, vectorLayer)
                        features[:]=[] #.clear()
                        #print len(features)
                    
                    
                    
            #Zum Schluss schaue ob noch neue Features in der Liste sind
            if len(features)>0:
                #print "Rest:" + str(len(features))
                self.schreibeFeatures(features, vectorLayer) 

            endTime= datetime.datetime.now()
            
            print endTime
        

        #self.setOutputValue(self.OUTPUT, inputFilename)

    def schreibeFeatures(self, features, vectorLayer):
        try:
            (res, outFeats) = vectorLayer.dataProvider().addFeatures(features)
            print len(outFeats), "Features geschrieben"
            
        except IOError as e:
            print "DP I/O error({0}): {1}".format(e.errno, e.strerror)
        except ValueError:
            print "DataProvider Werte-Error"
        except QgsError as qGisErr:
            print qGisErr.message()
            print qGisErr.summary()
        except:
            print "Unexpected error:", str(sys.exc_info()[0])
            print "Error Dataprovider" + str(vectorLayer.dataProvider().error())
            raise
    
    def pixelToMap(self, pX, pY, geoTransform):
        ptArr=gdal.ApplyGeoTransform(geoTransform, pX + 0.5, pY + 0.5)
        return QgsPoint(ptArr[0], ptArr[1])
    