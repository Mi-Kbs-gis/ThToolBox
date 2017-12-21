# -*- coding: utf-8 -*-

"""
***************************************************************************
    tlugUtils.py
    ---------------------
    Date                 : October 2017
    copyright            : (C) 2017 by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)
    email                : Michael.Kuerbs@tlug.thueringen.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Michael Kürbs'
__date__ = '2017-10-25'
__copyright__ = '(C) 2017 Michael Kürbs by Thüringer Landesanstalt für Umwelt und Geologie (TLUG)'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import subprocess
from qgis.core import QgsApplication
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools.system import isWindows, isMac, userFolder

class tlugUtils():

    TLUG_FOLDER = "TLUG_FOLDER"

    @staticmethod
    def tlugPath():
        folder = ProcessingConfig.getSetting(tlugUtils.TLUG_FOLDER)

        # if folder is None or folder == '':
            # if isWindows():
                # testfolder = os.path.join(os.path.dirname(QgsApplication.prefixPath()), 'TlugProcessing')
                # testfolder = os.path.join(testfolder, 'bin')
                # if os.path.exists(os.path.join(testfolder, 'pkinfo')):
                    # folder = testfolder
                # folder = testfolder
            # else:
                # testfolder = "/usr/bin"
                # if os.path.exists(os.path.join(testfolder, "pkinfo")):
                    # folder = testfolder
                # else:
                    # testfolder = "/usr/local/bin"
                    # if os.path.exists(os.path.join(testfolder, "pkinfo")):
                        # folder = testfolder
                    # folder = testfolder
        return folder

    @staticmethod
    def runTlugProcessing(commands, progress):
        settings = QSettings()#from gdal
        loglines = []
        loglines.append("tlug execution console output")
        loglines.append(commands)
        progress.setInfo('tlug command:')
        commandline = " ".join(commands)
        progress.setCommand(commandline)
        proc = subprocess.Popen(
            commandline,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=open(os.devnull),
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ).stdout
        progress.setInfo('tlug command output:')

        for line in iter(proc.readline, ""):
            progress.setConsoleInfo(line)
            loglines.append(line)
        ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)

        ProcessingLog.addToLog(ProcessingLog.LOG_INFO, commandline)
        pktoolsUtils.consoleOutput = loglines

#    @staticmethod
#    def getConsoleOutput():
#        return pktoolsUtils.consoleOutput
