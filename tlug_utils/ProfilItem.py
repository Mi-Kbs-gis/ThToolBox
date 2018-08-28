# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 ProfilItem
 TLUG Algorithms
                              -------------------
        begin                : 2018-08-27
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Michael Kürbs'
__date__ = '2018-08-08'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

from qgis.PyQt.QtCore import QObject
from qgis.core import *
from qgis.core import QgsGeometry

class ProfilItem(QObject):
    
    def __init__(self, srcGeom, profilGeom, station, abstand, ueberhoehung):
        self.srcGeom = srcGeom
        self.profilGeom = profilGeom
        self.station = station
        self.abstand = abstand
        self.ueberhoehung = ueberhoehung