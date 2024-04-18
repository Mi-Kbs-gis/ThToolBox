# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                Files2Table
 TLUG Algorithms
                              -------------------
        begin                : 2018-10-05
        copyright            : (C) 2018 by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)
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
__date__ = '2024-04-17'
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
                       #QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFile,
                       #QgsProcessingParameterVectorLayer,
                       #QgsProcessingParameterFeatureSource,
                       #QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       #QgsProcessingParameterEnum,
                       QgsProject,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingException,
                       QgsWkbTypes)
from PyQt5.QtGui import QIcon

class Files2Table(QgsProcessingAlgorithm):
    """
    Algorithm read file infos from a directory.
    
    Two modes available
    Non-Recursive
    Recursive
    """


    OUTPUT = 'OUTPUT'
    INPUTDIR = 'INPUTDIR'
    USE_SUBDIR = 'USE_SUBDIR'

    
    def initAlgorithm(self, config='default'):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUTDIR,
                self.tr('Files Directory'),
                behavior=QgsProcessingParameterFile.Folder
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.USE_SUBDIR,
                self.tr('Use Sub Directorys'),
                optional=False
            )
        )
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Files')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        dir = self.parameterAsFile(parameters, self.INPUTDIR, context)
        useSubDirs = self.parameterAsBool(parameters, self.USE_SUBDIR, context)
        

        fields = QgsFields()
        fields.append( QgsField( "filename", QVariant.String ) )     #0
        fields.append( QgsField( "path", QVariant.String ) )         #1
        fields.append( QgsField( "abspath", QVariant.String ) )     #2
        fields.append( QgsField( "filetype", QVariant.String ) )     #2
        fields.append( QgsField( "createdate", QVariant.DateTime ) ) #3
        fields.append( QgsField( "modifydate", QVariant.DateTime ) ) #4
        fields.append( QgsField( "size", QVariant.LongLong) )             #5

        #take CRS from Rasterlayer 
        crsProject=QgsProject.instance().crs()         
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, fields, QgsWkbTypes.NoGeometry, crsProject) #100=WKBUnknown
        countFiles=0

#        try:

        self.fileList = [] #list of QFileInfo
        self.readDir(dir, useSubDirs, 1, feedback)       
        for iFeat, fInfo in enumerate(self.fileList):
            attrs=[]
            #feedback.pushInfo(fInfo.absoluteFilePath() + " " +  str(fInfo==None))
            if not fInfo==None:
                # Attributes
                absFilePath=(os.path.join( fInfo.absolutePath(), fInfo.fileName()))
                attrs.append( fInfo.fileName() )                        #0
                attrs.append( fInfo.absoluteDir().absolutePath() )      #1
                attrs.append( fInfo.absoluteFilePath() )                    #2
                if fInfo.isDir():
                    attrs.append( 'folder' )                  #3
                else:
                    attrs.append( fInfo.suffix() )                  #3
                attrs.append( fInfo.birthTime()  )                      #4
                attrs.append( fInfo.lastModified() )                    #5
                if fInfo.isDir():
                    listOfFiles= os.listdir( fInfo.absoluteFilePath() )
                    attrs.append(len(listOfFiles))                         #6
                #Create new Feature
                else:
                    attrs.append( fInfo.size() )                            #6
                #Create new Feature
                newFeat = QgsFeature(fields)

                newFeat.setAttributes(attrs)
                # Add a feature in the sink
                sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
                countFiles=countFiles+1
            else:
                feedback.pushInfo('Error: Feature ' + str( iFeat + 1 ) + finfo.absolutePath() )
            
    
#        except Exception as err:
#            msg = self.tr("Error while writing table features" + ": " + str( err.args ) + ";" + str( repr( err )))
#            feedback.reportError(msg)
#            raise QgsProcessingException(msg)

        msgInfo=self.tr(str(countFiles) + " Files were added to table.")
        feedback.pushInfo(msgInfo)
        # Return the results of the algorithm. In this case our only result is
        return {self.OUTPUT: dest_id}

        
    def readDir(self, dir, readSubs, tiefe, feedback): 
        #fileList = [ QFileInfo ]
        #Schleife für alle Einträge des Verzeichnises
        listOfFiles= os.listdir( dir )
        total=100
        if tiefe==1 and len(listOfFiles) > 0: #ZeroDivisionError
            total = 100.0 / len(listOfFiles) 
        
            
            
        #feedback.pushInfo(str(len(listOfFiles)) + ' Items in dir ' +  dir)
    
    
        #for n,file in enumerate( os.listdir( dir ) ):
        for n, file in enumerate(listOfFiles):

            filePath=(os.path.join(dir, file))
            info=QFileInfo(filePath)
            #feedback.pushInfo(str(info.isFile()) + ' ' +  str(info.isDir()) + ' ' + info.absoluteFilePath())
            #print( dir, info.isFile(), info.isDir( ))
            if info.exists() and info.isFile():
                self.fileList.append( info ) 
                #print (info.fileName(), info.size(), info.birthTime(), info.lastModified())
            elif info.exists() and info.isDir():
                # rekursive if Sub Dir
                if readSubs == True: # read Sub directory if needed
                    self.fileList.append( info ) # add separate item for the directory
                    self.readDir(filePath, True, tiefe + 1, feedback)
            else:
                pass
                #next
            if tiefe == 1:
                # Update the progress bar in level 1
                feedback.setProgress( int( n + 1 * total ) )
                
#        else:
#            if tiefe = 1:
#                feedback.setProgress( int( 100 ) )
#            feedback.pushInfo("No files in directory! " + dir)

        return #fileList
        
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self.tr( 'Files2Table' )

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Files To Table')

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
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/Files2Table_Logo.png'))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Files2Table()
