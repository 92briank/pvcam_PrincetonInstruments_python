# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 10:53:50 2015

@author: tempo
"""

from __future__ import division, print_function

import ctypes as ctw
import ctypes.wintypes as ctww
from enum import Enum

__version__ = '2013.01.18'
__docformat__ = 'restructuredtext en'
#__all__ = ['API', 'Lucam', 'LucamEnumCameras', 'LucamNumCameras',
#           'LucamError', 'LucamGetLastError', 'LucamSynchronousSnapshots',
#           'LucamPreviewAVI', 'LucamConvertBmp24ToRgb24']



    
#/*****************************************************************************/
#/*        Copyright (C) Roper Scientific, Inc. 2002 All rights reserved.     */
#/*****************************************************************************/
#ifndef _MASTER_H
#define _MASTER_H
#static const char *_master_h_="$Header: /PVCAM/SourceWindows/master.h 1     7/18/02 8:17a Dtrent $";
#
##ifndef WIN32
#    #error OS Not Supported
##endif
#
#/******************************** ANSI Types *********************************/
#if defined  __cplusplus        /* BORLAND   C++                             */
#define PV_C_PLUS_PLUS
#elif defined  __cplusplus__    /* MICROSOFT C++   This allows us to         */
  #define PV_C_PLUS_PLUS        /*   insert the proper compiler flags,       */
#endif                          /*   in PVCAM.H for example, to cope         */
#                                /*   properly with C++ definitions.          */
#/**************************** Calling Conventions ****************************/
#define PV_CDECL __cdecl
#if defined CDECL_CALL_CONV                      /* Use the '_cdecl' calling convention */
  #define PV_DECL __declspec(dllexport) PV_CDECL /*  or '__stdcall' calling convention  */
#else                                            /*  as appropriate.                    */
  #define PV_DECL __declspec(dllexport) __stdcall
#endif

#   /**************************** PVCAM Pointer Types ****************************/
#PV_PTR_DECL = ctw.c_void_p
#PV_BUFP_DECL= ctw.c_void_p

#/******************************** PVCAM Types ********************************/
PV_FAIL = 0
PV_OK = 1

rs_bool = ctww.USHORT
rs_bool_ptr = ctww.POINTER(rs_bool)
rs_bool_const_ptr = rs_bool_ptr
char = ctw.c_char
char_ptr = ctw.c_char_p
char_const_ptr = char_ptr
int8 = ctw.c_int8
int8_ptr = ctw.POINTER(int8)
int8_const_ptr = int8_ptr
uns8 = ctw.c_uint8
uns8_ptr = ctw.POINTER(uns8)
uns8_const_ptr = uns8_ptr
int16 = ctw.c_int16
int16_ptr = ctw.POINTER(int16)
int16_const_ptr = int16_ptr
uns16 = ctw.c_uint16
uns16_ptr = ctw.POINTER(uns16)
uns16_const_ptr = uns16_ptr
int32 = ctw.c_int32
int32_ptr = ctw.POINTER(int32)
int32_const_ptr = int32_ptr
uns32 = ctw.c_uint32
uns32_ptr = ctw.POINTER(uns32)
uns32_const_ptr = uns32_ptr
flt64 = ctw.c_double
flt64_ptr = ctw.POINTER(flt64)
flt64_const_ptr = flt64_ptr
void_ptr = ctw.c_void_p
void_ptr_ptr = ctw.POINTER(void_ptr)
#/* deprecated types */
boolean = ctw.c_bool
boolean_ptr = ctw.POINTER(boolean)
boolean_const_ptr = boolean_ptr


#/****************************** PVCAM Constants ******************************/
FALSE = PV_FAIL      # FALSE == 0                                  */
TRUE =  PV_OK        # TRUE  == 1                                  */


BIG_ENDIAN = FALSE # TRUE for Motorola byte order, FALSE for Intel */
CAM_NAME_LEN = 32  # Max length of a cam name (includes null term) */

#/************************ PVCAM-Specific Definitions *************************/
MAX_CAM = 16          # Maximum number of cameras on this system.     */

class ExposureMode(Enum):
    timed = 0
    strobed = 1
    bulb = 2
    triggerFirst = 3
    flash = 4
    variableTimed = 5
    intStrobed = 6
    
class ReadoutStatus(Enum):
    readoutNotActive = 0
    exposureInProgress = 1
    readoutInProgress = 2
    readoutComplete_frameAvailable = 3
    readoutFailed = 4
    acquisitionInProgress = 5
    maxCameraStatus = 6
    
class AttributeType(Enum):
    currentValue = 0
    count = 1
    typeValue = 2
    minValue = 3
    maxValue = 4
    defaultValue = 5
    increment = 6
    access = 7
    available = 8
    
class CircularBufferMode(Enum):
    none = 0
    overwrite = 1
    nooverwrite = 2
    
class CameraControlState(Enum):
    noChange = 0
    halt = 1
    closeShutter = 2
    clear = 3
    clearCloseShutter = 4
    openShutter = 5
    clearOpenShutter = 6
    
class ScriptLocation(Enum):
    preOpenShutter = 0
    postOpenShutter = 1
    preFlash = 2
    postFlash = 3
    preIntegrate = 4
    postIntegrate = 5
    preReadout = 6
    postReadout = 7
    preCloseShutter = 8
    postCloseShutter = 9
    
class ExposureUnits(Enum):
    millisecond = 0
    microsecond = 1
    #second = 2 # Not available for our camera
    
class LogicOutput(Enum):
    NOT_SCAN = 0
    SHUTTER = 1
    NOT_RDY = 2
    LOGIC0 = 3
    CLEARING = 4
    NOT_FT_IMAGE_SHIFT = 5 
    RESERVED = 6
    LOGIC1 = 7
    EXPOSE_PROG = 8 
    EXPOSE = 9
    IMAGE_SHIFT = 10
    READOUT = 11
    ACQUIRING = 12
    WAIT_FOR_TRIG = 13
    
class BufferPrec(Enum):
    int8precision = 0
    uns8precision = 1
    int16precision = 2
    uns16precision = 3
    int32precision = 4
    uns32precision = 5
    
class ShutterState(Enum):
    fault = 0
    opening = 1
    opened = 2
    closing = 3
    closed = 4
    unknown = 5
    
class ShutterOpenMode(Enum):
    never = 0
    preexposure = 1
    presequence = 2
    pretrigger = 3
    nochange = 4
