# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ThToolBox
                                 WMS Ripper
 TLUG Algorithms
                              -------------------
        begin                : 2018-03-23
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
__date__ = '2019-02-15'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

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
                       QgsProcessingException,
                       QgsProcessingParameterExpression,
                       QgsExpression,
                       QgsExpressionContext)
from PyQt5.QtGui import QIcon
import os

class WmsRipper(QgsProcessingAlgorithm):
    """
    Download WMS images from a WMS server based of features bounding box.
    World files will be created.
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
    fieldNameBBOX='bbox'
    fieldNameUrl='getmap_url'
    fieldNamePath='path'
    fieldNameFile='file'
    fieldNameResponseType='content'
    fieldNameHttpStatusCode='httpstatus'
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

        # self.addParameter(
            # QgsProcessingParameterField(
                # self.FILENAME_FIELD,
                # self.tr('Field with Filenames'),
                # None,
                # self.INPUT_LAYER,
                # QgsProcessingParameterField.Any,
                # optional=False

            # )
        # )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.FILENAME_FIELD,
                self.tr('Filenames'),
                parentLayerParameterName=self.INPUT_LAYER
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
        
        exprFileNameString = self.parameterAsString(parameters, self.FILENAME_FIELD, context)
        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        self.path = self.parameterAsFile(parameters, self.DOWNLOAD_DIR, context)

        # fileNameFileIndex=-1
        # if not fileNameField=="":
            # fileNameFileIndex = vectorLayer.fields().lookupField(fileNameField)
        exprFileName=QgsExpression(exprFileNameString)
        if exprFileName.hasParserError():
            raise QgsProcessingException("Invalid Filename Expression: " + exprFileName.parserErrorString())

        exprContext = QgsExpressionContext()
            
        if baseUrl=="":
            raise ###

        fields = vectorLayer.fields()
        fields.append( QgsField( self.fieldNameBBOX, QVariant.String ) )
        fields.append( QgsField( self.fieldNameUrl, QVariant.String ) )
        fields.append( QgsField( self.fieldNamePath, QVariant.String ) )
        fields.append( QgsField( self.fieldNameFile, QVariant.String ) )
        fields.append( QgsField( self.fieldNameResponseType, QVariant.String ) )
        fields.append( QgsField( self.fieldNameHttpStatusCode, QVariant.Int) )
        #take CRS from Project
        crsProject=QgsProject.instance().crs()
        feedback.pushInfo("CRS " + str(crsProject))

        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, fields, vectorLayer.wkbType(), crsProject)

        total=1
               
        #Check if any features are selected
        if vectorLayer.selectedFeatureCount() > 0:
            # Take only the selected features
            iter=vectorLayer.selectedFeatures()
            total = 100.0 / vectorLayer.selectedFeatureCount()
        else:

            iter = vectorLayer.getFeatures()
            try:
                total = 100.0 / vectorLayer.featureCount() #Division durch 0
            except:
                msg = self.tr("no Features to process")
                feedback.reportError(msg)
                raise QgsProcessingException(msg)
        feedback.pushInfo("Pixel size: " + str(pixelSize))

        countDownload=0 
        for i, feature in enumerate(iter):
        
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():

                msg = self.tr("Process was canceled!")

                raise QgsProcessingException(msg)
                
            hasError=False
            loopText=''
            attrs=feature.attributes()
            geom = feature.geometry()
            bbox = geom.boundingBox()
            xMin = round( bbox.xMinimum(), 2)
            xMax = round( bbox.xMaximum(), 2)
            yMin = round( bbox.yMinimum(), 2)
            yMax = round( bbox.yMaximum(), 2)
            
            bboxText ='{0},{1},{2},{3}'.format( xMin, yMin, xMax, yMax )
            pixelsX = int( (xMax - xMin) / pixelSize )
            pixelsY = int( (yMax - yMin) / pixelSize )
            feedback.pushInfo("BBox: " + str(i) + bboxText + " --> Tile width: " + str(pixelsX) + " height: " + str(pixelsY) )
            
            epsg=vectorLayer.crs().authid()
            url = unicode( baseUrl + 'request=GetMap&Service=WMS&Version=' + wmsVersion + '&SRS=' + str(epsg) + '&LAYERS=' + layers + '&STYLES=' + style_name + '&BBOX=' + bboxText + '&FORMAT=image/' + self.imageFormats[imageFormatIdx].lower() +'&WIDTH=' + str(pixelsX)+ '&HEIGHT=' + str(pixelsY) )
            #qUrl=QUrl(url)
            
            #get File type combo item
            fileExt = self.imageFormats[imageFormatIdx]
            
            
            exprContext.setFeature(feature)
            file_name = exprFileName.evaluate(exprContext)
            if file_name is None or file_name == '':
                file_name = "WMS_Tile_"+ str( i+1 )
                feedback.pushInfo("Invalid Filename Expression on Feature: " + str(i) + " saved as " + file_name)

            contentType=None
            httpStatusCode=None
            writeModus = 'wb' # binary
            numTrials = 5 # 'Number of trial (Anzahl der Versuche)
            if type(file_name) == int or type(file_name) == float:
                # if filename is numeric
                file_name = str(file_name)
            else:
                #Replace Special Characters
                file_name=file_name.replace(":","_")
                file_name=file_name.replace("*","_")
                file_name=file_name.replace("\\","_")
                file_name=file_name.replace("/","_")


            if not str(url) == "":
            
                try:
           
                    feedback.pushInfo( "----------------------------\n Start Download for feature " + str(i)+ " ("+ file_name +")" )
                    feedback.pushInfo( "\nGetMap-URL: "+ unicode(url) + "\n"  ) #+ url" \n" + str(url.encode("utf-8"))+

                    result = self.getResponse(feedback, url, numTrials, 0) # % Versuche
                    if result is not None:
                        feedback.pushInfo(".. trials executed. ")
                        # To Do: es gibt result is not null und trotzdem wird keine Looptext-Augabe oder Datei erzeugt
                        try:
                            httpStatusCode = result.status_code

                        
                            if not result.headers is None and not result.status_code is None:
                            
                                contentType = result.headers.get('Content-Type')
                                contentType = contentType.lower()

                            else:
                                feedback.pushInfo("No Header and Status_Code" + str(i) +' '+ file_name + ' ('+str(httpStatusCode)+') ' + url)
                                fileExt='xml'
                                writeModus = 'w'


                        except Exception as resultErr:  #Result has No Header or status_code
                            fileExt='xml'
                            writeModus = 'w'
                            loopText = loopText + "\n\t Download Result has No Header or status_code " + str(i) + "(" + file_name + "): " + " URL: " + unicode(url) + " " + str(resultErr.args) + ";" + str(repr(resultErr) + "\n  HTTP Status Code: " + str( httpStatusCode ) + '\n Content-Type: ' + str(contentType) )
                            
                  
                        # change file type if not a image
                        if contentType.find('image') == -1 and contentType.find('jpeg') == -1 and  contentType.find('jpg') == -1 and  contentType.find('png') == -1 and  contentType.find('gif') == -1 and contentType.find('tif') == -1:
                            isImage = False
                            feedback.pushInfo("!!! Result is no valid WMS-image !!!!")
                            writeModus = 'w'
                            fileExt='xml'
                        else:
                            isImage=True

                        feedback.pushInfo("contentType: " + str(contentType))
                        feedback.pushInfo('httpStatusCode: '+str( httpStatusCode ))
                        feedback.pushInfo('Filetype: ' + str( fileExt ) )


                        filePath=self.path + "\\" + file_name + '.' + fileExt.lower()

                        with open(filePath, writeModus) as fd:
                        
                            #contentType='application/application/vnd.ogc.se_xml'
                            if writeModus== 'wb': #binary
                                fd.write( result.content ) 
                            else: # string
                                fd.write( result.text ) 
                            

                        fd.close()
                        feedback.pushInfo('File saved: ' + str( filePath ) )
                        
                        if httpStatusCode == 200 and isImage==True:
                                                
                           
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
                            outWld.write( '\n' + str( xMin + pixelSize/2 ) ) #Nimm Zentrum des linken oberen Pixels 
                            outWld.write( '\n' + str( yMax - pixelSize/2) )
                            outWld.close()
                            feedback.pushInfo('WorldFile saved: ' + str( filePathWld ) )

                        else:
                            hasError=True
                            feedback.pushInfo("Problem at Feature " + str(i) + "(" + file_name + "): " + unicode(url) + "  HTTP Status Code:" + str(httpStatusCode) )
                    

                    else:
                        # Result is empty
                        feedback.pushInfo(".. trials without Result: " + str(result))

                        loopText = loopText + " Result is empty for (" + file_name + "): " + unicode(url) + "\n WMS-Server delivers no data to create a file. " + str(numTrials) + ' trials were excecuted.'

                    
                except Exception as err:
                    hasError=True
                    loopText = loopText + "\n\t Download error: On Feature " + str(i) + "(" + file_name + "): " + " URL: " + unicode(url) + " " + str(err.args) + ";" + str(repr(err) + "\n  HTTP Status Code: " + str( httpStatusCode ) + '\n Content-Type: ' + str(contentType) )


            attrs.append( bboxText )
            attrs.append( url )
            attrs.append( self.path + "\\")
            attrs.append( file_name + '.' + fileExt.lower() )
            attrs.append( contentType )
            attrs.append( httpStatusCode )
           

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
                loopText = loopText + "\n\t Error while taking over the feature " + str(i) + "(" + file_name + "): " +" "+ str(err.args) + ";" + str(repr(err))
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

    def getResponse(self, feedback, url, maxIteration, curIterartion=0):
        feedback.pushInfo( str(curIterartion+1)+'. ')
        #proxies = { "http": "http://IP:PORT" }  #"http://user:password@IP:PORT"
        #result = requests.get(url, proxies=proxies)
        result = requests.get(url)#, stream=False)
        feedback.pushInfo( str( result )) # + " " + result.status_code)
        if not result.status_code == 200 and curIterartion < maxIteration:
            result = self.getResponse(feedback, url, maxIteration, curIterartion + 1)
        
        return result

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Store_WMS_Images_By_Features'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Store WMS Images By Features')

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

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(self.__doc__)

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/StoreWMS_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return WmsRipper()