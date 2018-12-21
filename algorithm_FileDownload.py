# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TlugProcessing
                                 File Download
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
__date__ = '2018-12-21'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
import requests
from PyQt5.QtCore import QCoreApplication, QUrl, QFile, QIODevice, QVariant, QEventLoop
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply 

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
                       QgsProject,
                       QgsFeature,
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

class FileDownload(QgsProcessingAlgorithm):
    """
    Download files from a url based of a feature attribute.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_LAYER = 'INPUT_LAYER'
    FIELD = 'FIELD'
    FIELDFILENAME='FIELDFILENAME'
    OUTPUT = 'OUTPUT'
    DOWNLOAD_DIR = 'DOWNLOAD_DIR'
    USE_NULL = 'USE_NULL'

    #globals
    path = ''
    fieldNamePath='path'
    fieldNameFile='file'
    fieldNameResponseType='content'
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
            QgsProcessingParameterField(
                self.FIELD,
                self.tr('URL Field'),
                None,
                self.INPUT_LAYER,
                QgsProcessingParameterField.String,
                optional=False

            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDFILENAME,
                self.tr('Field with file names (must be unique!)'),
                None,
                self.INPUT_LAYER,
                QgsProcessingParameterField.Any,
                optional=True
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
        urlField = self.parameterAsString(parameters, self.FIELD, context)
        fileNameField = self.parameterAsString(parameters, self.FIELDFILENAME, context)

        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        self.path = self.parameterAsFile(parameters, self.DOWNLOAD_DIR, context)


        urlFieldIndex=-1
        if not urlField=="":
            fields = vectorLayer.fields()
            urlFieldIndex = vectorLayer.fields().lookupField(urlField)

        fileNameFileIndex=-1
        if not fileNameField=="":
            fileNameFileIndex = vectorLayer.fields().lookupField(fileNameField)
            
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
            self.url =str( feature[ urlFieldIndex ] )
            

            contentType=None

            
            #loopText = str(i) +": "+ file_name +": "  + self.url
            if not str(self.url) == "" and not feature[ urlFieldIndex ] == None:
            
                try:
            
                    result = requests.get(self.url, stream=False)
                    
                    contentType=result.headers.get('Content-Type')
                    if result.status_code == 200:
                        #get File type from Headers 'Content-Type'
                        fileExt=""
                        try:
                            fileExt=contentType.split("/")[1]
                        except Exception as err:
                            fileExt="unkwown"
                        #get File Name
                        file_name=None
                        if fileNameFileIndex > -1:
                            file_name=str( feature[ fileNameFileIndex ] ) +'.'+ fileExt
                        else:
                            file_name = "File_" + str(i+1)+'.'+ fileExt

                        #Replace Special Characters
                        file_name=file_name.replace(":","_")
                        file_name=file_name.replace("*","_")
                        file_name=file_name.replace("\\","_")
                        file_name=file_name.replace("/","_")

                    
                        filePath=self.path + "\\" + file_name
                        if result:
                            with open(filePath, 'wb') as fd:
                                for chunk in result.iter_content(chunk_size=128):
                                    fd.write(chunk)
                            fd.close()
                    else:
                        hasError=True
                        feedback.pushInfo(str(i) + ": " + str(self.url) + "  HTTP Status Code:" + str(result.status_code) )
            

                    loopText = loopText + " Download finished"
                except Exception as err:
                    hasError=True
                    loopText = loopText + "\n\t Download error: On Feature " + str(i) + " URL: " + self.url + " " + str(err.args) + ";" + str(repr(err))
                

            if hasError == True or str(self.url) == "NULL" or str(self.url) == "" or feature[ urlFieldIndex ] == None:
                #add a emty String if no Url
                attrs.append( None )
                attrs.append( None )
                attrs.append( None )
            else:
                #add String attributes to link the file
                attrs.append( self.path + "\\")
                attrs.append( file_name )
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
        return 'Download_By_Features'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Download by Features')

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
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/DowmloadByFile_Logo.png'))



    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FileDownload()

