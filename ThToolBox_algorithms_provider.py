# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThToolBox
                                 ThToolBoxPluginProvider
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Michael Kürbs'
__date__ = '2018-09-19'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .algorithm_SelectDuplicates import SelectDuplicates
from .algorithm_TransformToProfil_Gradient import TransformToProfil_Gradient
from .algorithm_TransformToProfil_LineIntersection import TransformToProfil_LineIntersection
from .algorithm_TransformToProfil_PolygonIntersection import TransformToProfil_PolygonIntersection
from .algorithm_TransformToProfil_Points import TransformToProfil_Points
from .algorithm_TransformGeomFromProfileToRealWorld import TransformGeomFromProfileToRealWorld
from .algorithm_TransformToProfil_ShiftProfileOrigin import TransformToProfil_ShiftProfileOrigin
from .algorithm_FileDownload import FileDownload
from .algorithm_WMSRipper import WmsRipper
from .algorithm_AttachRasterValuesToLineVertices import AttachRasterValuesToLineVertices
from .algorithm_Files2Table import Files2Table
from .algorithm_TransformToProfil_PointsForAllLines import TransformToProfil_PointsForAllLines
from .algorithm_TransformToProfil_GradientForAllLines import TransformToProfil_GradientForAllLines
from .algorithm_TransformToProfil_PolygonIntersectionForAllLines import TransformToProfil_PolygonIntersectionForAllLines
from .algorithm_TransformToProfil_LineIntersectionForAllLines import TransformToProfil_LineIntersectionForAllLines

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, qVersion
import os
from PyQt5.QtGui import QIcon

class ThToolBoxPluginProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'processing_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)   
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
            
        # Load algorithms
        self.alglist = []
        
        # RASTER TOOLS
        self.alglist.append( AttachRasterValuesToLineVertices() )
        
        # VECTOR SELECTION TOOLS
        self.alglist.append( SelectDuplicates() )
        
        # WEB
        self.alglist.append( FileDownload() )
        self.alglist.append( WmsRipper() )
        
        # TO PROFILE COORDINATES
        self.alglist.append( TransformToProfil_Gradient() )
        self.alglist.append( TransformToProfil_GradientForAllLines() )
        
        self.alglist.append( TransformToProfil_LineIntersection() )
        self.alglist.append( TransformToProfil_LineIntersectionForAllLines() )
        
        self.alglist.append( TransformToProfil_PolygonIntersection() )
        self.alglist.append( TransformToProfil_PolygonIntersectionForAllLines() )
        
        self.alglist.append( TransformToProfil_Points() )
        self.alglist.append( TransformToProfil_PointsForAllLines() )
        
        self.alglist.append( TransformGeomFromProfileToRealWorld() )
        
        self.alglist.append( TransformToProfil_ShiftProfileOrigin() )
        self.alglist.append( Files2Table() )

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        for alg in self.alglist:
            self.addAlgorithm( alg )

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'thtoolbox'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('ThToolBox')

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
    
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__),'icons/ThToolBox_Logo_small.png'))

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Processing', message)
