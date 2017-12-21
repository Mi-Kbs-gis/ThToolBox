# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TlugProcessing
                                 A QGIS plugin
 TLUG Algorithms
                              -------------------
        begin                : 2017-10-25
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
__date__ = '2017-10-25'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TlugProcessing class from file TlugProcessing.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .TlugProcessingPlugin import TlugProcessingPlugin
    return TlugProcessingPlugin()
