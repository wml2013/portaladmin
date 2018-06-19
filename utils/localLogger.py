#----------------------------------------------------------------------------------
# Author:        Mark Casson
# Date:          24/12/2015
# Description:   Defines the Logger class and a number of module level
#                methods to aid in logging.
#
# (C) Copyright ESRI (UK) Limited 2015. All rights reserved
# ESRI (UK) Ltd, Millennium House, 65 Walton Street, Aylesbury, HP21 7QG
# Tel: +44 (0) 1296 745500  Fax: +44 (0) 1296 745544
#
# Edited:       Wai-Ming Lee
# Date:         31/05/2018
# Notes:        Disabled the ability to log to a local file
#----------------------------------------------------------------------------------

import logging
import logging.handlers
import datetime
import os, json
from utils.exceptions import *

_rootLogger = None
_logFileHandlers = {}

class Logger(object):
    """
    Class allowing writing of indented multiline messages and setting up
    of a logger with some default settings
    """
    _logIndentLevel = 0
    _dateFormat = "%d-%m-%Y %H:%M:%S"
    _formatter = None

    def __init__(self, logFile, noConsoleOutput, loggingMode = logging.INFO):
        """
        Initialise the logging environment to write to the specified logFile
        """

        global _rootLogger
        global _logFileHandlers
        global _formatter

        if _rootLogger != None:
            raise Exception("localLogger has already been initialised")

        rootLogger = logging.getLogger()
        rootLogger.setLevel(loggingMode)

        _formatter = logging.Formatter('%(asctime)s %(message)s', datefmt=self._dateFormat)

        self._dateTimePad = " ".ljust(len(datetime.datetime.now().strftime(self._dateFormat)) + 1, " ")

# logging to console only

        if logFile != None:
            if not os.path.exists(os.path.dirname(logFile)):
                os.makedirs(os.path.dirname(logFile))

            isNewLogFile = self.addLogFile(logFile)
            if not isNewLogFile:
                logging.info("*".rjust(80,"*"))

# logging to file and console

#        if not os.path.exists(os.path.dirname(logFile)):
#           os.makedirs(os.path.dirname(logFile))
#
#        isNewLogFile = self.addLogFile(logFile)
#        if not isNewLogFile:
#                logging.info("*".rjust(80,"*"))

        if not noConsoleOutput:
            stdch = logging.StreamHandler()
            stdch.setFormatter(_formatter)
            rootLogger.addHandler(stdch)

        _rootLogger = self

    def addLogFile(self, logFile):
        """
        Add the specified logFile to the list of handlers.
        """
        global _logFileHandlers

        logFilePath = os.path.abspath(logFile)
        isNewLogFile = False
        if logFilePath.lower() not in _logFileHandlers:
            logFileDir = os.path.dirname(logFilePath)
            if not os.path.exists(logFileDir):
                try:
                    os.makedirs(logFileDir)
                except Exception as ex:
                    raise ApplicationError("Failed to create folder: {}".format(logFileDir), ex)
            isNewLogFile = not os.path.exists(logFilePath)

            filech = logging.handlers.RotatingFileHandler(filename=logFilePath, maxBytes=2000000, backupCount=10)
            filech.setFormatter(_formatter)
            logging.getLogger().addHandler(filech)
            _logFileHandlers[logFilePath.lower()] = filech

        return isNewLogFile

    def removeLogFile(self, logFile):
        """
        Remove the specified logFile from the list of handlers.
        """
        global _logFileHandlers
        logFilePath = os.path.abspath(logFile)
        if logFilePath.lower() in _logFileHandlers:
            handler = _logFileHandlers.pop(logFilePath.lower())
            logging.getLogger().removeHandler(handler)

    def write(self, message, indentMsg = False):
        """
        Write a message to the log file(s) and/or console
        """
        indentPad = "".rjust(self._logIndentLevel * 2)
        if indentMsg: indentPad += "  "

        if isinstance(message, str):
            msgArray = message.splitlines()
        elif isinstance(message, list):
            msgArray = message
        elif isinstance(message, dict):
            msgArray = [json.dumps(message)]
        else:
            msgArray = message.splitlines()

        if len(msgArray) == 0:
            logging.info("")
        else:
            logging.info(indentPad + "\n{}{}".format(self._dateTimePad, indentPad).join(msgArray))

    def incIndent(self):
        """
        Increment the indent level
        """
        self._logIndentLevel += 1

    def decIndent(self):
        """
        Decrement the indent level
        """
        if self._logIndentLevel > 0:
            self._logIndentLevel -= 1

    def setIndent(self, indentLevel):
        """
        Set the indent level
        """
        if indentLevel >= 0:
            self._logIndentLevel = indentLevel

class DisableAPILogging():
    """
    Can be used in a "with..." statement to temporarily change the logging level
    to suppress INFO messages being output from called methods.
    """
    def __enter__(self):
        logger = logging.getLogger()
        self.loggingLevel = logger.getEffectiveLevel()
        if self.loggingLevel == logging.INFO:
            logger.setLevel(logging.ERROR)
    def __exit__(self, a, b, c):
        logger = logging.getLogger()
        logger.setLevel(self.loggingLevel)

def initialise(logFile, noConsoleOutput = False, loggingMode = logging.INFO):
    """
    Initialise the logging environment
    """
    logger = Logger(logFile, noConsoleOutput, loggingMode)

def write(message, indentMsg = False):
    """
    Write a "logging.info" message.
    """
    if _rootLogger != None:
        _rootLogger.write(message, indentMsg)
    else:
        logging.info(message)

def writeJson(message, jsonData):
    """
    Write a message and the supplied jsonData as a Json string.
    The jsonData is typically a dictionary object.
    """
    jsonOutputStr = json.dumps(jsonData, sort_keys=True, indent=4, separators=(',', ': '))
    write(message + jsonOutputStr)

def addLogFile(logFile):
    """
    Add a log file to which output is to be written.
    """
    if _rootLogger is None:
        raise Exception("localLogger has not been initialised")
    _rootLogger.addLogFile(logFile)

def removeLogFile(logFile):
    """
    Remove and close the specified log file.
    """
    if _rootLogger is None:
        raise Exception("localLogger has not been initialised")
    _rootLogger.removeLogFile(logFile)

def incIndent():
    """
    Increment the indent level.
    Returns the indent level prior to the increment.
    """
    if _rootLogger != None:
        curLevel = _rootLogger._logIndentLevel
        _rootLogger.incIndent()
        return curLevel
    else:
        return 0

def decIndent():
    """
    Decrement the indent level
    """
    if _rootLogger != None:
        _rootLogger.decIndent()

def isEnabledFor(level):
    """
    Returns whether logging is enabled for the specified
    logging level (eg, logging.DEBUG or localLogger.logging.DEBUG)
    """
    return logging.getLogger().isEnabledFor(level)

def indentLevel():
    if _rootLogger != None:
        return _rootLogger._logIndentLevel
    else:
        return 0

def setIndentLevel(indentLevel):
    if _rootLogger != None:
        _rootLogger.setIndent(indentLevel)

#def setAPILoggingLevel():
#    '''
#    Set the internal logging level to ERROR if the current logging level is INFO.
#    This is to avoid INFO messages being written by other APIs
#    '''
#    logger = logging.getLogger()
#    cl = logger.getEffectiveLevel()
#    if cl == logging.INFO:
#        logger.setLevel(logging.ERROR)
#    return cl

#def resetAPILoggingLevel(level):
#    logging.getLogger().setLevel(level)
