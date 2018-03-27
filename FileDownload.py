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
__date__ = '2018-03-23'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QUrl, QFile, QIODevice, QVariant
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply 
from qgis.core import QGis, QgsNetworkAccessManager, QgsFeature, QgsField, QgsWKBTypes, QgsExpression, QgsFeatureRequest, QgsError #, QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterTable
from processing.core.parameters import ParameterString #ParameterVector
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

class FileDownload(GeoAlgorithm):
    """This is an algorithm that takes a Link from a table attribute and
    downloads it to a predefinit directory.
    
    File name and directory will be stored in a new table
    
    """
    
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_LAYER = 'INPUT_LAYER'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    DOWNLOAD_DIR = 'DOWNLOAD_DIR'
    USE_NULL = 'USE_NULL'
    
    #globals
    path = ''
    file_name = ''
    fieldNamePath='path'
    fieldNameFile='file'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        # The name that the user will see in the toolbox
        self.name, self.i18n_name = self.trAlgorithm('File download')
        
        # The branch of the toolbox under which the algorithm will appear
        self.group, self.i18n_group = self.trAlgorithm('Web Tools')
        
        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterTable(self.INPUT_LAYER,
            self.tr('Input layer'), False))
        
        self.addParameter(ParameterTableField(self.FIELD,
                                              self.tr('Selection attribute'), self.INPUT_LAYER))
        self.addParameter(ParameterString(self.DOWNLOAD_DIR,
                                          self.tr("File Directory")))
        # We add a Selection as Output
        self.addOutput(OutputVector(self.OUTPUT, self.tr('downloaded')))#, True))
        
    
    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        self.fieldName = self.getParameterValue(self.FIELD)
        output = self.getOutputValue(self.OUTPUT)
        
        self.path = self.getParameterValue(self.DOWNLOAD_DIR)
        
        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # Qgsself.vectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        self.vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        
        # check if fieldnames already exists
        if self.vectorLayer.fieldNameIndex(self.fieldNameFile)>-1:
            raise GeoAlgorithmExecutionException('Field "/' + self.fieldNameFile + '"/ already exists!')
        if self.vectorLayer.fieldNameIndex(self.fieldNamePath)>-1:
            raise GeoAlgorithmExecutionException('Field "' + self.fieldNamePath + '" already exists!')
        
        
        fields = self.vectorLayer.pendingFields()
        fields.append(QgsField(self.fieldNamePath, QVariant.String))
        fields.append(QgsField(self.fieldNameFile, QVariant.String))

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields,
            QgsWKBTypes.multiType(QGis.fromOldWkbType(self.vectorLayer.wkbType())),
            self.vectorLayer.crs())            
        
        fidx = self.vectorLayer.fieldNameIndex(self.fieldName)
        fieldType = fields[fidx].type()
        
        # And now we can process
        
        #check if the File Directory is valid
        if self.path.endswith("\\")==False or path.endswith("/")==False:
            self.path=self.path + "\\"
        fPath=QFile(self.path)
        if fPath.exists==False:
            #ProcessingLog.addToLog(ProcessingLog.LOG_ERROR,
            #                               self.tr("File Directory does not exist!"))
            raise GeoAlgorithmExecutionException("File Directory does not exist!")
        
        #Config QIS Network-Settings
        networkAccessManager = QgsNetworkAccessManager.instance()
        networkAccessManager.finished.connect(self.urlCallFinished)
        
        #Check if any features are selected
        if self.vectorLayer.selectedFeatureCount() >0:
            # Take only the selected features
            iter=self.vectorLayer.selectedFeatures()
        else:
            iter = self.vectorLayer.getFeatures()
        
        #Iterating over Vector Layer
        i=0
        
        for feature in iter:
            hasError=False
            loopText=''
            attrs=feature.attributes()
            geom = feature.geometry()
            self.url=feature[fidx]
            if str(self.url) == "NULL":
                continue

            self.file_name = self.url.split('/')[-1]
            
            attrs.append(self.path)
            attrs.append(self.file_name)
            
            loopText = str(i) +": "+ self.file_name +": "  + self.url
            try:
        
                req = QNetworkRequest(QUrl(self.url))
                
                reply = networkAccessManager.get(req)

                loopText = loopText + " Download finished"
            except:
                hasError=True
                loopText = loopText + "\n\t Download error: On Feature " + str(i)

            try:
                out_feat = QgsFeature()
                #check if source is a spatial layer
                if self.vectorLayer.wkbType()!=100:
                    out_feat.setGeometry(geom)
                out_feat.setAttributes(attrs)
                writer.addFeature(out_feat)
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

            progress.setPercentage(100.0 * i / self.vectorLayer.featureCount())
            if hasError==True:
                print loopText
            i=i+1
            
        del writer
        
    
    def urlCallFinished(self, reply):
        hasError=False
        url = reply.request().url().toString()
        file_name = url.split('/')[-1]
        byteArray=None
        try:
            byteArray=reply.readAll()
        except:
            print "Response emty"
            hasError=True
        
        if reply.error() == QNetworkReply.NoError and byteArray is not None:

            #data=byteArray.data()
            try:
                #save Response in File
                file=QFile(self.path + file_name)
                print "FileSave: " + file_name
                file.open(QIODevice.WriteOnly)
                file.write(byteArray)
                file.close()
                reply.deleteLater()
            except UnicodeEncodeError as err:
                print "UnicodeEncodeError while saving File " +file_name+" "+str(err.args) + ";" + str(repr(err))
                hasError=True
            except IOError as e:
                print "DP I/O error({0}): {1}".format(e.errno, e.strerror)+" "+file_name
                hasError=True
            except Exception as err:
                print "Error while saving File " + file_name + " " + str(err.args) + " " + str(repr(err)), reply.error()
                hasError=True
        else:
            hasError=True

        #print failed Download Feature Id
        if hasError==True:
            expTxt='\"'+self.fieldName+'"'+"= \'"+ url +'\''
            exp = QgsExpression(expTxt)
            request = QgsFeatureRequest(exp)
            self.vectorLayer.startEditing()
            for feature in self.vectorLayer.getFeatures(request):
                print "Feature", feature.id(), "Download failed"
                
                # reset Attributval of the new Feature
                # fieldIndex=xxxLayer.fieldNameIndex(self.fieldNameFile)
                # xxxLayer.changeAttributeValue(feature.id(), fieldIndex, "Download failed")

