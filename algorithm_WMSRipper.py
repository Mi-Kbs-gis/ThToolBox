# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 WMS Ripper
 TLUG Algorithms
                              -------------------
        begin                : 2018-03-23
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
__date__ = '2018-09-20'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
import requests
from PyQt5.QtCore import QCoreApplication, QUrl, QFile, QIODevice, QVariant, QEventLoop
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply 
import math

from qgis.core import (QgsProcessing,
                       QgsNetworkAccessManager,
                       QgsExpression, 
                       QgsFeatureRequest, 
                       QgsError,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProject,
                       QgsFeature,
                       QgsField,
                       QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsCoordinateTransform,
                       QgsProcessingException)

class WmsRipper(QgsProcessingAlgorithm):
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

    INPUT_LAYER = 'INPUT_LAYER'
    
    BASE_URL = 'BASE_URL'
    WMS_VERSION = 'WMS_VERSION'
    LAYERS = 'LAYERS'
    STYLE_NAME = 'STYLE_NAME'
    IMAGE_FORMAT = 'IMAGE_FORMAT'
    PIXEL_SIZE = 'PIXEL_SIZE'
    
    FILENAME_FIELD = 'FILENAME_FIELD'
    OUTPUT = 'OUTPUT'
    DOWNLOAD_DIR = 'DOWNLOAD_DIR'
    USE_NULL = 'USE_NULL'

    #globals
    path = ''
    fieldNamePath='path'
    fieldNameFile='file'
    fieldNameResponseType='content'
    imageFormats = ['jpeg',
              'png',
              'jpg'
              ]      
    
    feedback = None
    
    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr('Input Vector Layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                 self.BASE_URL,
                 self.tr('WMS-Base-URL'),
                 defaultValue='',
                 optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                 self.LAYERS,
                 self.tr('Layers (layer1,layer2,...)'),
                 defaultValue='',
                 optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                 self.STYLE_NAME,
                 self.tr('Style names'),
                 defaultValue='',
                 optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                 self.WMS_VERSION,
                 self.tr('Wms Version'),
                 defaultValue='1.1.1',
                 optional=False
            )
        )
  
        self.addParameter(QgsProcessingParameterEnum(
            self.IMAGE_FORMAT,
            self.tr('Image Format'),
            options=self.imageFormats, defaultValue=0))

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PIXEL_SIZE,
                self.tr('spatial resolution (pixel size)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10,
                optional=False,
                #minValue=0,
                #maxValue=100
                
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FILENAME_FIELD,
                self.tr('Field with Filenames'),
                None,
                self.INPUT_LAYER,
                QgsProcessingParameterField.Any,
                optional=False

            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.DOWNLOAD_DIR,
                self.tr('Download Directory')
               
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Features With File Link')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        self.feedback = feedback
        """
        Here is where the processing itself takes place.
        """
        baseUrl = self.parameterAsString(parameters, self.BASE_URL, context)
        layers = self.parameterAsString(parameters, self.LAYERS, context)
        style_name = self.parameterAsString(parameters, self.STYLE_NAME, context)
        wmsVersion = self.parameterAsString(parameters, self.WMS_VERSION, context)
        imageFormatIdx = self.parameterAsEnum(parameters, self.IMAGE_FORMAT, context)
        pixelSize = self.parameterAsDouble(parameters, self.PIXEL_SIZE, context)
        
        fileNameField = self.parameterAsString(parameters, self.FILENAME_FIELD, context)
        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        self.path = self.parameterAsFile(parameters, self.DOWNLOAD_DIR, context)

        fileNameFileIndex=-1
        if not fileNameField=="":
            fileNameFileIndex = vectorLayer.fields().lookupField(fileNameField)

        if baseUrl=="":
            raise ###

        fields = vectorLayer.fields()
        fields.append(QgsField(self.fieldNamePath, QVariant.String))
        fields.append(QgsField(self.fieldNameFile, QVariant.String))
        fields.append(QgsField(self.fieldNameResponseType, QVariant.String))
        #take CRS from Project
        crsProject=QgsProject.instance().crs()         

        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, fields, vectorLayer.wkbType(), crsProject)

        try:
            total = 100.0 / vectorLayer.featureCount()
        except:
            msg = self.tr("no Features to process")
            feedback.reportError(msg)
            raise QgsProcessingException(msg)
            
               
        #Check if any features are selected
        if vectorLayer.selectedFeatureCount() > 0:
            # Take only the selected features
            iter=vectorLayer.selectedFeatures()
        else:
            iter = vectorLayer.getFeatures()
        countDownload=0 
        for i, feature in enumerate(iter):
            hasError=False
            loopText=''
            attrs=feature.attributes()
            geom = feature.geometry()
            bbox = geom.boundingBox()
            xMin = round( bbox.xMinimum(), 1)
            xMax = round( bbox.xMaximum(), 1 )
            yMin = round( bbox.yMinimum(), 1)
            yMax = round( bbox.yMaximum(), 1 )
            
            bboxText ='{0},{1},{2},{3}'.format( xMin, yMin, xMax, yMax )
            pixelsX = int( (xMax - xMin) / pixelSize )
            pixelsY = int( (yMax - yMin) / pixelSize )
            
            epsg=vectorLayer.crs().authid()
            url = unicode( baseUrl + 'request=GetMap&Service=WMS&Version=' + wmsVersion + '&SRS=' + str(epsg) + '&LAYERS=' + layers + '&STYLES=' + style_name + '&BBOX=' + bboxText + '&FORMAT=image/' + self.imageFormats[imageFormatIdx].lower() +'&WIDTH=' + str(pixelsX)+ '&HEIGHT=' + str(pixelsY) )
            #qUrl=QUrl(url)
            
            #get File type combo item
            fileExt = self.imageFormats[imageFormatIdx]

            if fileNameFileIndex > -1:
                file_name = str(feature[fileNameFileIndex])
            else:
                file_name = "WMS_Tile_"+ str( i+1 )
            contentType=None
            #Replace Special Characters
            file_name=file_name.replace(":","_")
            file_name=file_name.replace("*","_")
            file_name=file_name.replace("\\","_")
            file_name=file_name.replace("/","_")

            
            #loopText = str(i) +": "+ file_name +": "  + url
            if not str(url) == "":
            
                try:
            
                    #result = requests.get(qUrl.url().replace('&amp;','&'), stream=False)
                    result = requests.get(url, stream=False)
                    
                    contentType=result.headers.get('Content-Type')
                    feedback.pushInfo(str(i) + ' ('+str(contentType)+') ' + url)
                    if result.status_code == 200:
                        filePath=self.path + "\\" + file_name + '.' + fileExt.lower()
                        #image = result.raw.read()
                        #open(filePath, 'wb').write(image)
                        if result:
                            with open(filePath, 'wb') as fd:
                                for chunk in result.iter_content(chunk_size=128):
                                    fd.write(chunk)
                            fd.close()
                        
                        #create World File
                        #first and last Character of image extension
                        wldExt=''
                        try:
                            wldExt = fileExt[0] + fileExt[-1] + 'w'
                        except:
                            wldExt='wld'
                        filePathWld=self.path + "\\" + file_name + '.' + wldExt.lower()
                        outWld = open( filePathWld , 'w')
                        outWld.write( str( pixelSize )  )
                        outWld.write( '\n' + str(0) )
                        outWld.write( '\n' + str(0) )
                        outWld.write( '\n' + str( - pixelSize ) )
                        outWld.write( '\n' + str( xMin + pixelSize) ) #Nimm Zentrum des linken oberen Pixels
                        outWld.write( '\n' + str( yMax - pixelSize) )
                        outWld.close()
                        
                    else:
                        hasError=True
                        feedback.pushInfo(str(i) + ": " + str(url) + "  HTTP Status Code:" + str(result.status_code) )
            

                    loopText = loopText + " Download finished"
                except Exception as err:
                    hasError=True
                    loopText = loopText + "\n\t Download error: On Feature " + str(i) + " URL: " + url + " " + str(err.args) + ";" + str(repr(err))
                

            if hasError == True or str(url) == "NULL" or str(url) == "":
                #add a emty String if no Url
                attrs.append( None )
                attrs.append( None )
                attrs.append( None )
            else:
                #add String attributes to link the file
                attrs.append( self.path + "\\")
                attrs.append( file_name + '.' + fileExt.lower() )
                attrs.append( contentType )
            

            try:
                out_feat = QgsFeature()
                #check if source is a spatial layer
                if vectorLayer.wkbType() != 100:
                    out_feat.setGeometry(geom)
                out_feat.setAttributes(attrs)
                # Add a feature in the sink
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)
            except IOError as e:
                hasError=True
                loopText = loopText + "\n\t" + "DP I/O error({0}): {1}".format(e.errno, e.strerror)
            except ValueError:
                hasError=True
                loopText = loopText + "\n\t" + "Value-Error"
            except QgsError as qGisErr:
                hasError=True
                loopText = loopText + "\n\t" +  " QgsError: " + qGisErr.message()
                loopText = loopText + "\n\t" +  qGisErr.summary()
            except Exception as err:
                hasError=True
                loopText = loopText + "\n\t Error while taking over the feature " + str(i) +" "+ str(err.args) + ";" + str(repr(err))
                pass

            feedback.setProgress( int( i * total ) )
            if hasError==True:
                feedback.pushInfo(loopText)
            else:
                countDownload=countDownload+1
            


        msgInfo=self.tr( str( countDownload ) + " Downloads from " + str(i+1) + " Features to Directory " + self.path)
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
        return 'Store WMS images by Features'

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
        return 'Web'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return WmsRipper()