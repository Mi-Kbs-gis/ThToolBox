# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 Extract Raster Values to CSV
 TLUG Algorithms
                              -------------------
        begin                : 2017-12-07
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
__date__ = '2017-12-07'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'


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
from processing.core.outputs import OutputVector, OutputFile, OutputTable
from processing.tools import dataobjects, vector


import struct
import datetime
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from PyQt4 import QtSql


class RasterToCSV(GeoAlgorithm):
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

    INPUT_LAYER = 'INPUT_LAYER'
    OUTPUT = 'OUTPUT'
    USE_NULL = 'USE_NULL'
    
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name, self.i18n_name = self.trAlgorithm('Extract Raster Values to CSV')

        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('Raster tools')

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterRaster(self.INPUT_LAYER, self.tr('Input Raster')))#[ParameterVector.VECTOR_TYPE_ANY]


        # We add a Vectorlayer as Output
        #self.addParameter(ParameterVector(self.OUTPUT_LAYER, self.tr('Target CSV')))
        self.addOutput(OutputTable(self.OUTPUT, self.tr('Output CSV')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        outputFileName = self.getOutputValue(self.OUTPUT)

        #------ hole Layer -------

        dataset = gdal.Open(inputFilename, GA_ReadOnly)
        geotransform = dataset.GetGeoTransform()
        band = dataset.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        bandtype = gdal.GetDataTypeName(band.DataType)
        print nodata
        print bandtype
        print inputFilename


        #---- Datei zum Schreiben -----
        print outputFileName
        file= open(outputFileName, 'w')

        startTime= datetime.datetime.now()
        print "Start", startTime


        for y in xrange(band.YSize):
            prozent=int(y / float(band.YSize) * 100) #xrange(band.YSize)*100)
            if prozent >0:
                if prozent%100==0:
                    print str(prozent) + " %"
                
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
            #jeder Zeile des Rasters
            for value in values:
                if value != nodata:
                    geo=self.pixelToMap(col,y,geotransform) #[4477091.0, 5663949.0]
        #           print str(geo.x()) +" "+ str(geo.y()) +" "+ str(value)
                    csvString=str(int(geo.x())) + ";" + str(int(geo.y())) + ";" + str(value)+ "\n"
                    
                    file.write(csvString)
                    
               
                col=col+1
                        

        file.close()
        endTime= datetime.datetime.now()
        print "Ende", endTime
        self.printTimeDiff(startTime, endTime)
        
    
    # transform from pixel to Geo-Coordinates
    def pixelToMap(self, pX, pY, geoTransform):
        ptArr=gdal.ApplyGeoTransform(geoTransform, pX + 0.5, pY + 0.5)
        return QgsPoint(ptArr[0], ptArr[1])
        
    def printTimeDiff(self, startTime, endTime):
        timeDelta=endTime-startTime
        totalSeconds=timeDelta.total_seconds()
        print "totalSeconds", totalSeconds
        
        minsDecimal=str(totalSeconds/60)
        splitMins=minsDecimal.split(".")
        mins=int(splitMins[0])
        if len(splitMins)>1:
            seconds=int(float("0."+splitMins[1])*60) #Sekunden abzueglich der vollen Minuten
        hoursDecimal=str(mins/60)
        splitHours=hoursDecimal.split(".")
        hours=int(splitHours[0])
        if len(splitHours)>1:
            mins=int(float("0."+splitHours[1])*60) #mins abzueglich der vollen Stunden
        print "Dauer h:min:sec", hours, ":",mins, ":", seconds


