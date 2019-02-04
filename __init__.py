# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 A QGIS plugin
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
__date__ = '2018-07-31'
__copyright__ = '(C) 2018 by Michael Kürbs by Thüringer Landesamt für Umwelt, Bergbau und Naturschutz (TLUBN)'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TlugProcessingPlugin class from file TlugProcessingPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .TlugProcessingPlugin import TlugProcessingPlugin
    return TlugProcessingPlugin()
