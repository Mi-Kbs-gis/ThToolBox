# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 BohrpunktSettings
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

class BohrpunktSettings(QObject):
    def __init__(self, bohrPunktLayer, feedback):
        self.feedback=feedback
        self.bohrPunktLayer=bohrPunktLayer
        self.IndexBohrPunktLayerFieldZ=-1
        self.indexFieldtiefeOK=-1
        self.indexFieldtiefeUK=-1
        self.fieldIndexRichtungHz=-1
        self.fieldIndexAzimut=-1
        
    def setIndexBohrPunktLayerFieldZ(self, fieldIndex):
        self.IndexBohrPunktLayerFieldZ=fieldIndex

    def setTiefeFieldIndizes(self, fieldIndexTiefeOK, fieldIndexTiefeUK):
        self.indexFieldtiefeOK=fieldIndexTiefeOK
        self.indexFieldtiefeUK=fieldIndexTiefeUK

    def setBohrungsRichtung(self, fieldIndexRichtungHz, fieldIndexAzimut):
        self.fieldIndexRichtungHz=fieldIndexRichtungHz
        self.fieldIndexAzimut=fieldIndexAzimut