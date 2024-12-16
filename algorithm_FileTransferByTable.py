# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                FileTransferByTable
 TLUG Algorithms
                              -------------------
        begin                : 2023-04-06
        copyright            : (C) 2023 by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
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
 This script is a processing algorithm to sample raster values to line vertices
"""

__author__ = 'Michael Kürbs'
__date__ = '2023-04-06'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import shutil
from PyQt5.QtCore import QFileInfo, QVariant
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsExpression,
                       QgsExpressionContext,
                       QgsProcessingException)
from PyQt5.QtGui import QIcon
from shutil import copyfile, copytree, move
from pathlib import Path
from PyQt5.QtCore import QFileInfo

class FileTransferByTable(QgsProcessingAlgorithm):
    """
    Algorithm perfomrs a file transfer, 
    which is defined via a table.
    """

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    #INPUTDIR = 'INPUTDIR'
    EXPRESSION_SRC = 'EXPRESSION_SRC'
    EXPRESSION_TARGET = 'EXPRESSION_TARGET'
    BACKUP_DIR = 'BACKUP_DIR'
    MAKEBACKUP = 'BACKUP'

    MAKECOPY = 'MAKECOPY'
    OVERWRITE = 'OVERWRITE'

    
    def initAlgorithm(self, config='default'):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
#        self.addParameter(
#            QgsProcessingParameterFile(
#                self.INPUTDIR,
#                self.tr('Files Directory'),
#                behavior=QgsProcessingParameterFile.Folder
#            )
#        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT, 
                self.tr('Input layer'), 
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.EXPRESSION_SRC,
                self.tr('Source Path'), 
                parentLayerParameterName=self.INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.EXPRESSION_TARGET,
                self.tr('Target Path'), 
                parentLayerParameterName=self.INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MAKECOPY,
                self.tr('copy (not move)'),
                optional=False,
                defaultValue = True
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE,
                self.tr('overwrite files in target path if existing'),
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MAKEBACKUP,
                self.tr('backup overwritten files'),
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.BACKUP_DIR,
                #self.tr('Backup Directory'),
                description='Directory to Backup Files',
                optional = True,
                defaultValue = None
            )
        )
        
        #defaultValue: Any = None, optional: bool = False
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('transfer results')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        vectorLayer= self.parameterAsVectorLayer(parameters, self.INPUT, context)
        expression_src = self.parameterAsString(parameters, self.EXPRESSION_SRC, context)
        expr_src=QgsExpression(expression_src)
        if expr_src.hasParserError():
            raise QgsProcessingException(expr_src.parserErrorString())
            
        expression_tar = self.parameterAsString(parameters, self.EXPRESSION_TARGET, context)
        expr_tar=QgsExpression(expression_tar)
        if expr_tar.hasParserError():
            raise QgsProcessingException(expr_tar.parserErrorString())

        modusCopy = self.parameterAsBool(parameters, self.MAKECOPY, context)
        modusOverwrite = self.parameterAsBool(parameters, self.OVERWRITE, context)

        makeBackup = self.parameterAsBool(parameters, self.MAKEBACKUP, context)
        backupDir = self.parameterAsFile(parameters, self.BACKUP_DIR, context)
        feedback.pushInfo( 'BackUp: ' + str(makeBackup) + '   Dir: ' + backupDir )
        if makeBackup == True: 
            backupFolderInfo = QFileInfo( backupDir )
            #falls Verzeichnis existiert
            #feedback.pushInfo( 'backupFolderInfo.exists' + str(backupFolderInfo.exists()))
            if backupFolderInfo.exists() == False:
                # mode
                mode = 0o666
                os.mkdir(backupDir, mode)
                if backupFolderInfo.exists() == False:
                    raise QgsProcessingException('Backup-Directory can not be created: '+ backupDir)
                feedback.pushInfo( 'Backup Directory does not exist. It will be created! ' + backupDir)
        
        exprContext = QgsExpressionContext()

        count = vectorLayer.featureCount() if vectorLayer.featureCount() else 0
        total = 100.0 / count
        
        #Iterating over Vector Layer
        feedback.pushInfo( "Processing ")
        
        fields = vectorLayer.fields()
        fields.append( QgsField( "transfer_comment", QVariant.String ) )
        fields.append( QgsField( "transfer_warning", QVariant.String ) )
        fields.append( QgsField( "transfer_error", QVariant.String ) )
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
        context, fields, vectorLayer.wkbType(), vectorLayer.crs()) #100=WKBUnknown
        
        iter = vectorLayer.getFeatures()
        for current, feature in enumerate(iter):
            hasError = False
            commentTxt=''
            warningTxT=''
            errorTxt=''
            # Check for cancelation
            if feedback.isCanceled():
                return {}
            exprContext.setFeature(feature)
            sourcePath=''
            targetPath=''
            try:
                #create Source value from Expression
                sourcePath=expr_src.evaluate(exprContext)


            except Exception as err:
                msg = "Error while run Source Expression" + str( expr_src.expression() ) + " on feature " + str( feature.attributes() ) + ": " + str( err.args ) + ";" + str( repr( err ) ) 
                errorTxt=errorTxt + msg
                feedback.reportError(msg)
                hasError = True
                #raise QgsProcessingException(msg)

            try:
                #create Target value from Expression
                targetPath=expr_tar.evaluate(exprContext)
                if targetPath[-1] == '\\' or targetPath[-1] == '/':
                    targetPath=targetPath[:-1] # remove last character if its a slash or backslash

            except Exception as err:
                msg = "Error while run Target Expression" + str( expr_tar.expression() ) + " on feature " + str( feature.attributes() ) + ": " + str( err.args ) + ";" + str( repr( err ) ) 
                errorTxt=errorTxt + msg
                feedback.reportError(msg)
                hasError = True
                #raise QgsProcessingException(msg)        

            srcFile=QFileInfo(sourcePath)
            newFile = None
            newFileFolder = None
            if str(targetPath) == 'NULL' or str(targetPath) == 'None' or str(targetPath) == '' or len(str(targetPath)) ==0:
                feedback.reportError('There are NULL values on the defined taget path expression: ' + str( expr_tar.expression() ))
                raise Exception
            try:            

                newFile=QFileInfo(targetPath)
                newFileFolder = QFileInfo( newFile.absoluteDir().absolutePath() )
            except Exception as err:
                errorTxt=errorTxt + 'Target File not defined ' #Tagetfile nicht definert
                feedback.reportError('Target File not defined on file:' + targetPath)
                hasError = True
                
            if srcFile.exists() == False:
                errorTxt=errorTxt + 'Source File does not exist ' #Quelldatei existiert nicht
                #feedback.pushInfo('Source File does not exist: ' + sourcePath)
                feedback.reportError('Source File does not exist: ' + sourcePath)
                hasError = True

            else:
                if newFileFolder.exists() == False:
                    mode = 0o666
                    try:
                        feedback.pushInfo('Path: ' + newFile.absoluteDir().absolutePath() + '  File Abspath: ' + targetPath)

                        feedback.pushInfo('mkdir(' + newFile.absoluteDir().absolutePath()+')')
                        
                        #create dirs recursivly
                        path = Path(newFile.absoluteDir().absolutePath())
                        path.mkdir(parents=True, exist_ok=True)
                        
                        #if newFile.absoluteDir().absolutePath() != newFile.absoluteDir():
                        #    os.mkdir(newFile.absoluteDir().absolutePath(), mode)
                    except FileNotFoundError as err:
                        msg = "Target Directory can not be created! May be the root directory does not exist. " + newFile.absoluteDir().absolutePath() + ' for file '+  srcFile.fileName()#Zielverzeichnis existiert nicht 
                        errorTxt=errorTxt + msg
                        feedback.reportError(msg)
                        hasError = True
                    if newFileFolder.exists() == False:
                        msg = "Target Directory can not be created! " + newFile.absoluteDir().absolutePath() + ' for file '+  srcFile.fileName()#Zielverzeichnis existiert nicht 
                        errorTxt=errorTxt + msg
                        feedback.reportError(msg)
                        hasError = True
                        #raise QgsProcessingException(msg)

                #feat['error'] = 'existiert bereits, nicht kopiert'
                #feedback.pushInfo('if makeBackup == True:' + str(makeBackup == True))
                if hasError == False and newFile.exists() == True:
                    if modusOverwrite==False:
                            feedback.pushWarning('Target File already exists, file not overwritten: ' + targetPath)
                            warningTxT=warningTxT + 'Target File already exists, file not overwritten'
                    else:    
                        if makeBackup == True:
                            try:
                                backupFilePath=backupDir + "\\"+  srcFile.fileName()
                                #feedback.pushInfo('Backup file' + backupFilePath)
                                if srcFile.isFile():
                                    msg_cp = copyfile(srcFile.absoluteFilePath(), backupFilePath)
                                else: # Dir
                                    msg_cp = copytree(srcFile.absoluteFilePath(), backupFilePath)
                                feedback.pushInfo('Backup file at: ' + backupFilePath)
                            except Exception as err:
                                msg = "Backup can not be created! " + backupFilePath + ' for file '+  srcFile.fileName() +  str( err.args ) + ";" + str( repr( err ) )
                                errorTxt=errorTxt + msg
                                feedback.reportError(msg)
                                hasError = True
                        feedback.pushInfo('Target File already exists, file has been overwritten: ' + targetPath)
                        warningTxT=warningTxT + 'overwritten'
                
                if hasError == False:     
                    try:
                        if hasError == False:                                    
                            if modusCopy == True:
                                if srcFile.isFile():
                                    msg_cp = copyfile(srcFile.absoluteFilePath(), targetPath)
                                else: # dir
                                    msg_cp = copytree(srcFile.absoluteFilePath(), targetPath)
                                    
                                feedback.pushInfo('copy ' + srcFile.fileName() + ' --> ' + newFile.absoluteDir().absolutePath())
                                commentTxt=commentTxt + str(msg_cp)
                            else:
                                msg_mv = move(srcFile.absoluteFilePath(), targetPath) 
                                feedback.pushInfo('move ' + srcFile.fileName() + ' --> ' + newFile.absoluteDir().absolutePath())
                                commentTxt=commentTxt + str(msg_mv)
                 
                    except Exception as err:
                        msg = "Transfer File aborted! " + srcFile.fileName() + ' -> ' + newFile.absoluteDir().absolutePath() +  str( err.args ) + ";" + str( repr( err ) )
                        errorTxt=errorTxt + msg
                        feedback.reportError(msg)
                        hasError = True

#                    if newFile.exists() == True:  # gibt zu diesem Zeitpunkt immer False zurück
#                        commentTxt=commentTxt + srcFile.fileName() + ' successfull '
#                    else:
#                        feedback.reportError( srcFile.fileName() + ' failed')

            #Erzeuge Feature
            transferFeat = QgsFeature(fields) 
            if feature.hasGeometry():
                transferFeat.setGeometry(feature.geometry())
                
            attrs=feature.attributes()
            attrs.append( commentTxt )
            attrs.append( warningTxT )
            attrs.append( errorTxt )
            transferFeat.setAttributes(attrs)
            
#                transferFeat['transfer_comment']=commentTxt
#                transferFeat['transfer_warning']=warningTxT
#                transferFeat['transfer_error']=errorTxt


            # Add a feature in the sink
            sink.addFeature(transferFeat, QgsFeatureSink.FastInsert)
            total = 100.0 / count

            feedback.setProgress(int(current * total))

        feedback.pushInfo("beendet")
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
        return self.tr( 'FileTransferByTable' )

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('File Transfer By Table')

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
        return 'File Tools'

    def shortHelpString(self):
        """
        Returns a table with entrys for each file in a directory. 
        Include some file properties.
        """
        return self.tr(self.__doc__)

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/FileTransferByTable_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FileTransferByTable()
