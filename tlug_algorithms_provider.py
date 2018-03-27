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
"""

__author__ = 'Michael Kürbs'
__date__ = '2017-10-25'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig

from FindDuplicates import FindDuplicates
from ExtractRasterValues import ExtractRasterValues
from SampleRasterValues import SampleRasterValues
from RasterToCSV import RasterToCSV
from ExtractMinMaxZ import ExtractMinMaxZ
from Force2dExtractMinMaxZ import Force2dExtractMinMaxZ
from FileDownload import FileDownload

from tlugUtils import tlugUtils

class TlugAlgorithmProvider(AlgorithmProvider):

    MY_DUMMY_SETTING = 'MY_DUMMY_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        # Deactivate provider by default
        self.activate = False

        # Load algorithms
        self.alglist = []
        self.alglist.append(FindDuplicates())
        self.alglist.append(ExtractRasterValues())
        self.alglist.append(RasterToCSV())
        self.alglist.append(ExtractMinMaxZ())
        self.alglist.append(Force2dExtractMinMaxZ())
        self.alglist.append(SampleRasterValues())
        self.alglist.append(FileDownload())
        
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        """In this method we add settings needed to configure our
        provider.

        Do not forget to call the parent method, since it takes care
        or automatically adding a setting for activating or
        deactivating the algorithms in the provider.
        """
        AlgorithmProvider.initializeSettings(self)
        ProcessingConfig.addSetting(Setting(self.getDescription(), tlugUtils.TLUG_FOLDER, "tlug folder", tlugUtils.tlugPath()))
#        ProcessingConfig.addSetting(Setting('Example algorithms',
#            TlugProcessingProvider.MY_DUMMY_SETTING,
#            'Example setting', 'Default value'))

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting(TlugAlgorithmProvider.MY_DUMMY_SETTING)
#        ProcessingConfig.removeSetting(
#            TlugProcessingProvider.MY_DUMMY_SETTING)

    def getName(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'TLUG Processing'

    def getDescription(self):
        """This is the provired full name.
        """
        return 'Algorithms of TLUG'

    def getIcon(self):
        """We return the default icon.
        """
        return AlgorithmProvider.getIcon(self)

    def _loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        self.algs = self.alglist
