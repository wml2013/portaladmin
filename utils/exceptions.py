#----------------------------------------------------------------------------------
# Author:        Mark Casson
# Date:          24/12/2015
# Description:   Defines the ApplicationError and OperationError classes, together
#                with a module level method FormatExceptions
#
# (C) Copyright ESRI (UK) Limited 2015. All rights reserved
# ESRI (UK) Ltd, Millennium House, 65 Walton Street, Aylesbury, HP21 7QG
# Tel: +44 (0) 1296 745500  Fax: +44 (0) 1296 745544
#----------------------------------------------------------------------------------

import traceback

class ApplicationError(Exception):
    """
    An exception class derived from Exception which is used to create an
    exception stack.
    This class is used to mimic the C# exception handling functionality
    whereby exceptions may be thrown in nested called methods but only
    handled in an outer method, at which point the "exception stack" is
    output.
    """

    def __init__(self, msg, innerEx = None):
        """
        Creates an exception object, storing a message and an inner exception.
        """
        self.msg = msg
        self.innerEx = innerEx
        if innerEx != None:
            self.traceback = traceback.format_exc()
            if self.traceback != None and self.traceback == "None\n":
                self.traceback = None
        else:
            self.traceback = None

class OperationError(Exception):
    """
    Exception thrown due to a user error (eg, invalid argument or
    configuration file format error), so that the call stack is not
    output when the exception is logged.
    """
    pass

def FormatExceptions(msg, ex, incStackTrace = True):
    """
    Method to output a message stack where exceptions have been raised
    using the ApplicationError exception class
    """
    try:
        tracebackMsg = traceback.format_exc()

        exceptionList = []
        innerEx = ex
        haveOperationError = False
        #
        # Create a list of exceptions in reverse
        # order - ie, first exception at the front.
        #
        while innerEx != None:
            exceptionList.insert(0,innerEx)
            if type(innerEx) is ApplicationError:
                innerEx = innerEx.innerEx
            else:
                if type(innerEx) is OperationError:
                    haveOperationError = True
                innerEx = None
        #
        # Create a list of exception messages
        #
        outputMsgs = []
        for innerEx in exceptionList:
            if type(innerEx) is ApplicationError:
                for m in innerEx.msg.splitlines():
                    outputMsgs.append(m.rstrip())
            else:
                #
                # Sometimes innerEx can contain unicode characters, which can
                # cause the following to throw an exception.
                #
                try:
                    for m in str(innerEx).splitlines():
                        m = m.rstrip()
                        if len(m) > 0:
                            outputMsgs.append(m)
                except:
                    outputMsgs.append("FormatException: Unable to process inner exception")

        if msg != None:
            for m in msg.splitlines():
                m = m.rstrip()
                if len(m) > 0:
                    outputMsgs.append(m)
        #
        # Add the call stack to the messages
        #
        stackMsgs = []
        if incStackTrace and not haveOperationError:
            for innerEx in exceptionList:
                if type(innerEx) is ApplicationError:
                    if innerEx.traceback != None:
                        for m in innerEx.traceback.splitlines():
                            m = m.rstrip()
                            if len(m) > 0:
                                stackMsgs.append(m)

            for m in tracebackMsg.splitlines():
                m = m.rstrip()
                if len(m) > 0:
                    stackMsgs.append(m)
    except:
        return "Error in FormatExceptions\n" + traceback.format_exc()
    #
    # Return the message stack as a single string.
    #
    tracebackHdr = "Traceback (most recent call last):"
    foundHdr = False
    result = ""
    for m in outputMsgs:
        result += m + "\n"
    #
    # Add the traceback info, but don't repeat the messages
    #
    outputMsgs = [tracebackHdr]
    if len(stackMsgs) > 0:
        result += "Traceback:\n"
        for m in stackMsgs:
            if m != "ApplicationError":
                if m not in outputMsgs:
                    outputMsgs.append(m)
                    while not m.startswith("  "):
                        m = " " + m
                    result += m + "\n"

    return result.rstrip()
