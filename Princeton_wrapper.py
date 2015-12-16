# -*- coding: utf-8 -*-
"""Princeton(r) USB Camera Interface.

The module contains two main interfaces to the Lumenera pvcam API:

*API*, a low level ctypes interface to the Pvcam32.dll,
    exposing all definitions/declarations found in the lucam.h C header.

*Princeton*, a high level object interface wrapping most of the ctypes interface,
    featuring exception based error handling and numpy.array type images.

:Author:
  `Laura Corman`_

:Organization:
  Laboratoire Kastler Brossel, Paris

:Version: 2015.01.29

Requirements
------------
* `CPython 2.7 or 3.3 <http://www.python.org>`_
* `Numpy 1.7 <http://www.numpy.org>`_
* `Princeton camera and drivers Pvcam32.dll`_

Notes
-----

This module has been tested only with the Pixis 1024 monochrome camera on Windows.

The function for taking pictures / generating buffer are implemented for 16 bits pictures.

Some fuctions are implemented but were never tested (hardware problems, etc).

Documentation in HTML format can be generated with Epydoc.


Examples
--------
>>> from Princeton_wrapper import Princeton
>>> import matplotlib.pyplot as plt
>>> camera = Princeton()  # initialise with 2D ROI 
>>> camera.setpoint_temperature = -70  #set temperature (celcius)
>>> camera.gain = 1  #set gain
>>> 
>>> image = camera.takePicture()  # acquisition
>>> plt.imshow(image[0][0][0])
>>>
>>> #set camera to 1D (vertical binning) acquisition
>>> camera.removeLastExposureROI()
>>> camera.addExposureROI(camera._ROIspectroscopy)
>>> spectrum = camera.takePicture()
>>> plt.plot(spectrum[0][0][0][0])
>>>
>>  #close communication
>>> camera.close()


"""
from __future__ import division

import sys
import ctypes as ct
import numpy
from master_Header_wrapper import *
import time
__version__ = '2013.01.18'
__docformat__ = 'restructuredtext en'


def API():
    """Return ctypes interface to the Pvcam32.dll dynamic library.."""
    
#    /*********************** Constant & Type Definitions *************************/
#    
#    /************************ Class 2: Data types ********************************/
#    /* Data type used by pl_get_param with attribute type (ATTR_TYPE).           */
    TYPE_CHAR_PTR = 13
    TYPE_INT8 = 12
    TYPE_UNS8 = 5
    TYPE_INT16 = 1
    TYPE_UNS16 = 6
    TYPE_INT32 = 2
    TYPE_UNS32 = 7
    TYPE_UNS64 = 8
    TYPE_FLT64 = 4
    TYPE_ENUM = 9
    TYPE_BOOLEAN = 11
    TYPE_VOID_PTR = 14
    TYPE_VOID_PTR_PTR = 15
    
    # defines for classes                                                       */
    CLASS0 = 0          # Camera Communications                      */
    CLASS1 = 1          # Error Reporting                            */
    CLASS2 = 2          # Configuration/Setup                        */
    CLASS3 = 3          # Data Acuisition                            */
    CLASS4 = 4          # Buffer Manipulation                        */
    CLASS5 = 5          # Analysis                                   */
    CLASS6 = 6          # Data Export                                */
    CLASS29 = 29         # Buffer Functions                           */
    CLASS30 = 30         # Utility functions                          */
    CLASS31 = 31         # Memory Functions                           */
    CLASS32 = 32         # CCL Engine                                 */
    CLASS90 = 90         # EM Calibration                             */
    CLASS91 = 91         # RS170                                      */
    CLASS92 = 92         # Defect Mapping                             */
    CLASS93 = 93         # Fast frame operations (PIV/ACCUM/Kinetics) */
    CLASS94 = 94         # PTG                                        */
    CLASS95 = 95         # Virtual Chip                               */
    CLASS96 = 96         # Acton diagnostics.                         */
    CLASS97 = 97         # Custom Chip                                */
    CLASS98 = 98         # Custom timing                              */
    CLASS99 = 99         # Trenton diagnostics.                       */
    #*********************** Parameter IDs **************************************/
    # Format: TTCCxxxx, where TT = Data type, CC = Class, xxxx = ID number      */
    
            # DEVICE DRIVER PARAMETERS (CLASS 0) */
    
    #  Class 0 (next available index for class zero = 6) */
    
    PARAM_DD_INFO_LENGTH = ((CLASS0<<16) + (TYPE_INT16<<24) + 1) # Not available for our camera //Laura 16/01/2015
    PARAM_DD_VERSION = ((CLASS0<<16) + (TYPE_UNS16<<24) + 2) # 512 for us  //Laura 16/01/2015
    PARAM_DD_RETRIES = ((CLASS0<<16) + (TYPE_UNS16<<24) + 3) # Not available for our camera //Laura 16/01/2015
    PARAM_DD_TIMEOUT = ((CLASS0<<16) + (TYPE_UNS16<<24) + 4) # Not available for our camera //Laura 16/01/2015
    PARAM_DD_INFO = ((CLASS0<<16) + (TYPE_CHAR_PTR<<24) + 5) # Not available for our camera //Laura 16/01/2015
    
    # Camera Parameters Class 2 variables */
    
    # Class 2 (next available index for class two = 544) */
    
    # Camera Type enum for PI cameras */
    PARAM_CAMERA_TYPE = ((CLASS2<<16) + (TYPE_INT32<<24)     + 350) # 26 for us //Laura 16/01/2015
    
    # Sensor Type enum for PI cameras */
    PARAM_SENSOR_TYPE = ((CLASS2<<16) + (TYPE_INT32<<24)     + 270) # 102 for us //Laura 16/01/2015
    
    # Pixel Bias Correction Enable/Disable for Common Platform */
    PARAM_PBC = ((CLASS2<<16) + (TYPE_ENUM<<24)      + 351) # Not available for our camera //Laura 16/01/2015
    
    # SKIP_SREG_CLEAN */
    PARAM_SKIP_SREG_CLEAN = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 330) # Not available for our camera //Laura 16/01/2015
    
    # CCD skip parameters                                                       */
    # Min Block. amount to group on the shift register, to through way.         */
    PARAM_MIN_BLOCK = ((CLASS2<<16) + (TYPE_INT16<<24)     +  60) # 4 for us //Laura 16/01/2015
    # number of min block groups to use before valid data.                      */
    PARAM_NUM_MIN_BLOCK = ((CLASS2<<16) + (TYPE_INT16<<24)     +  61) # 250 for us //Laura 16/01/2015
    # number of strips to clear at one time, before going to the                */
    # minblk/numminblk scheme                                                   */
    PARAM_SKIP_AT_ONCE_BLK = ((CLASS2<<16) + (TYPE_INT32<<24)     + 536) # 0 for us //Laura 16/01/2015
    # Strips per clear. Used to define how many clears to use for continous     */
    # clears and with clears to define the clear area at the beginning of an    */
    # experiment.                                                               */
    PARAM_NUM_OF_STRIPS_PER_CLR = ((CLASS2<<16) + (TYPE_INT16<<24)     +  98) # 1024 for us //Laura 16/01/2015
    # Set Continuous Clears for Trenton Cameras. This is for clearing while     */
    # in external trigger.                                                      */
    PARAM_CONT_CLEARS = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 540) # Not available for our camera //Laura 16/01/2015
    
    # Clean while expose available for Common Platform cameras                  */
    PARAM_CLN_WHILE_EXPO = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 352) # Not available for our camera //Laura 16/01/2015
    
    # PreExpose (actually after reading out) Cleans                             */
    PARAM_PREEXP_CLEANS = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 354) # Not available for our camera //Laura 16/01/2015
    
    # Only applies to Thompson ST133 5Mhz                                       */
    # enables or disables anti-blooming.                                        */
    # Does not apply for our camera : removed //Laura 16/01/2015
    PARAM_ANTI_BLOOMING = ((CLASS2<<16) + (TYPE_ENUM<<24)      + 293)
    
    # This applies to ST133 1Mhz and 5Mhz and PentaMax V5 controllers. For the  */
    # ST133 family this controls whether the BNC (not scan) is either not scan  */
    # or shutter for the PentaMax V5, this can be not scan, shutter, not ready, */
    # clearing, logic 0, logic 1, clearing, and not frame transfer image shift. */
    # See enum below for possible values                                        */
    PARAM_LOGIC_OUTPUT = ((CLASS2<<16) + (TYPE_ENUM<<24)      +  66) # 1 for us //Laura 16/01/2015
    
    # Invert the LOGIC OUT signal                                               */
    PARAM_LOGIC_OUTPUT_INVERT = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 548) # Not available for our camera //Laura 16/01/2015
    
    # Edge Trigger defines whether the external sync trigger is positive or     */
    # negitive edge active. This is for the ST133 family (1 and 5 Mhz) and      */
    # PentaMax V5.0.                                                            */
    # see enum below for possible values.                                       */
    PARAM_EDGE_TRIGGER = ((CLASS2<<16) + (TYPE_ENUM<<24)      + 106) # 3 for us //Laura 16/01/2015
    
    # Intensifier gain is currently only used by the PI-Max and has a range of  */
    # 0-255                                                                     */
    PARAM_INTENSIFIER_GAIN = ((CLASS2<<16) + (TYPE_INT16<<24)     + 216) # 0 for us //Laura 16/01/2015
    
    # Enable control of IIT gain and EM gain by an unified GAIN for PI-Max4     */
    PARAM_UNIFIED_GAIN_ENABLED = ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 357) # Not available for our camera //Laura 16/01/2015
    # Unified gain for PI-Max4.                                                 */
    PARAM_UNIFIED_GAIN = ((CLASS2<<16) + (TYPE_INT32<<24)     + 358) # Not available for our camera //Laura 16/01/2015
    
    # Shutter, Gate, or Safe mode, for the PI-Max.                              */
    PARAM_SHTR_GATE_MODE = ((CLASS2<<16) + (TYPE_ENUM<<24)      + 217) # 0 for us //Laura 16/01/2015
    
    # Installed Timing Generator's option board (enum OPTN_BD_SPEC)             */
    PARAM_TG_OPTION_BD_TYPE = ((CLASS2<<16) + (TYPE_ENUM<<24)      + 353) # 1 for us //Laura 16/01/2015
    
    # ADC offset setting. Commented out because manual says it should not be modified //Laura 16/01/2015
    PARAM_ADC_OFFSET = ((CLASS2<<16) + (TYPE_INT16<<24)     + 195)
    # CCD chip name.    */
    PARAM_CHIP_NAME = ((CLASS2<<16) + (TYPE_CHAR_PTR<<24)  + 129) # 'EEV 1024x1024 CC' for us //Laura 16/01/2015
    
    PARAM_COOLING_MODE =        ((CLASS2<<16) + (TYPE_ENUM<<24)      + 214) # 0 for us //Laura 16/01/2015
    PARAM_HEAD_COOLING_CTRL =   ((CLASS2<<16) + (TYPE_ENUM<<24)      + 338) # 1 for us //Laura 16/01/2015
    PARAM_COOLING_FAN_CTRL =    ((CLASS2<<16) + (TYPE_ENUM<<24)      + 339) # 1 for us //Laura 16/01/2015
    PARAM_PREAMP_DELAY =        ((CLASS2<<16) + (TYPE_UNS16<<24)     + 502) # Not available for our camera //Laura 16/01/2015
    PARAM_PREFLASH =            ((CLASS2<<16) + (TYPE_UNS16<<24)     + 503) # Not available for our camera //Laura 16/01/2015
    PARAM_COLOR_MODE =          ((CLASS2<<16) + (TYPE_ENUM<<24)      + 504) # Not available for our camera //Laura 16/01/2015
    PARAM_MPP_CAPABLE =         ((CLASS2<<16) + (TYPE_ENUM<<24)      + 224) # 0 for us //Laura 16/01/2015
    PARAM_PREAMP_OFF_CONTROL =  ((CLASS2<<16) + (TYPE_UNS32<<24)     + 507) # Not available for our camera //Laura 16/01/2015
    PARAM_SERIAL_NUM =          ((CLASS2<<16) + (TYPE_UNS16<<24)     + 508) # Not available for our camera //Laura 16/01/2015
    
    # CCD Dimensions and physical characteristics                               */
    # pre and post dummies of CCD.                                              */
    PARAM_PREMASK =             ((CLASS2<<16) + (TYPE_UNS16<<24)     +  53) # 0 for us //Laura 16/01/2015
    PARAM_PRESCAN =             ((CLASS2<<16) + (TYPE_UNS16<<24)     +  55) # 24 for us //Laura 16/01/2015
    PARAM_POSTMASK =            ((CLASS2<<16) + (TYPE_UNS16<<24)     +  54) # 8 for us //Laura 16/01/2015
    PARAM_POSTSCAN =            ((CLASS2<<16) + (TYPE_UNS16<<24)     +  56) # 24 for us //Laura 16/01/2015
    PARAM_PIX_PAR_DIST =        ((CLASS2<<16) + (TYPE_UNS16<<24)     + 500) # Distance center-to-center between pixels (parallel direction) in nanometer  13000 for us //Laura 16/01/2015
    PARAM_PIX_PAR_SIZE =        ((CLASS2<<16) + (TYPE_UNS16<<24)     +  63) # Size of a single pixel's active area (parallel direction) in nanometer  13000 for us //Laura 16/01/2015
    PARAM_PIX_SER_DIST =        ((CLASS2<<16) + (TYPE_UNS16<<24)     + 501) # Distance center-to-center between pixels (serial direction) in nanometer 13000 for us //Laura 16/01/2015
    PARAM_PIX_SER_SIZE =        ((CLASS2<<16) + (TYPE_UNS16<<24)     +  62) # Size of a single pixel's active area (serial direction) in nanometer  13000 for us //Laura 16/01/2015
    PARAM_SUMMING_WELL =        ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 505) # Not available for our camera //Laura 16/01/2015
    PARAM_FWELL_CAPACITY =      ((CLASS2<<16) + (TYPE_UNS32<<24)     + 506) # Not available for our camera //Laura 16/01/2015
    # Y dimension of active area of CCD chip */
    PARAM_PAR_SIZE =            ((CLASS2<<16) + (TYPE_UNS16<<24)     +  57) # 1024 for us //Laura 16/01/2015
    # X dimension of active area of CCD chip */
    PARAM_SER_SIZE =            ((CLASS2<<16) + (TYPE_UNS16<<24)     +  58) # 1024 for us //Laura 16/01/2015
    # Can camera perform HW accumulation */
    PARAM_ACCUM_CAPABLE =        ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 538) # Not available for our camera //Laura 16/01/2015
    
    PARAM_FTSCAN =              ((CLASS2<<16) + (TYPE_UNS16<<24)     +  59) # 0 for us //Laura 16/01/2015
    
    # customize chip dimension */
    PARAM_CUSTOM_CHIP =         ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   +  87) # 0 for us //Laura 16/01/2015
    
    # customize chip timing */
    PARAM_CUSTOM_TIMING =       ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   +  88) # 0 for us //Laura 16/01/2015
    PARAM_PAR_SHIFT_TIME =      ((CLASS2<<16) + (TYPE_UNS32<<24)     + 545)
    PARAM_SER_SHIFT_TIME =      ((CLASS2<<16) + (TYPE_UNS32<<24)     + 546)
    PARAM_PAR_SHIFT_INDEX =     ((CLASS2<<16) + (TYPE_UNS32<<24)     + 547)
    
    # Kinetics Window Size */
    PARAM_KIN_WIN_SIZE =        ((CLASS2<<16) + (TYPE_UNS16<<24)     + 126) # 1 for us //Laura 16/01/2015
    
    # General parameters */
    # Is the controller on and running? */
    PARAM_CONTROLLER_ALIVE =   ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 168)
    # Readout time of current ROI, in ms */
    PARAM_READOUT_TIME =        ((CLASS2<<16) + (TYPE_FLT64<<24)     + 179)
    
    
            # CAMERA PARAMETERS (CLASS 2) */
    
    PARAM_CLEAR_CYCLES =        ((CLASS2<<16) + (TYPE_UNS16<<24)     + 97)  # 1 for us //Laura 16/01/2015
    PARAM_CLEAR_MODE =          ((CLASS2<<16) + (TYPE_ENUM<<24)      + 523)
    PARAM_FRAME_CAPABLE =       ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 509) # Not available for our camera //Laura 16/01/2015
    PARAM_PMODE =               ((CLASS2<<16) + (TYPE_ENUM <<24)     + 524)
    PARAM_CCS_STATUS =          ((CLASS2<<16) + (TYPE_INT16<<24)     + 510) # Not available for our camera //Laura 16/01/2015
    
    # This is the actual temperature of the detector. This is only a get, not a */
    # set                                                                       */
    PARAM_TEMP =                ((CLASS2<<16) + (TYPE_INT16<<24)     + 525) 
    # This is the desired temperature to set. */
    PARAM_TEMP_SETPOINT =       ((CLASS2<<16) + (TYPE_INT16<<24)     + 526)
    PARAM_CAM_FW_VERSION =      ((CLASS2<<16) + (TYPE_UNS16<<24)     + 532) # Not available for our camera //Laura 16/01/2015
    PARAM_HEAD_SER_NUM_ALPHA =  ((CLASS2<<16) + (TYPE_CHAR_PTR<<24)  + 533)
    PARAM_PCI_FW_VERSION =      ((CLASS2<<16) + (TYPE_UNS16<<24)     + 534) # Not available for our camera //Laura 16/01/2015
    PARAM_CAM_FW_FULL_VERSION = ((CLASS2<<16) + (TYPE_CHAR_PTR<<24)  + 534) # Not available for our camera //Laura 16/01/2015
    
    # Exsposure mode, timed strobed etc, etc */
    PARAM_EXPOSURE_MODE =       ((CLASS2<<16) + (TYPE_ENUM<<24)      + 535)
    
            # SPEED TABLE PARAMETERS (CLASS 2) */
    
    PARAM_BIT_DEPTH =           ((CLASS2<<16) + (TYPE_INT16<<24)     + 511) # 16 for us //Laura 16/01/2015
    PARAM_GAIN_INDEX =           ((CLASS2<<16) + (TYPE_INT16<<24)     + 512) # 3 for us //Laura 16/01/2015
    PARAM_SPDTAB_INDEX =        ((CLASS2<<16) + (TYPE_INT16<<24)     + 513) # 1 for us //Laura 16/01/2015
    # define which port (amplifier on shift register) to use. */
    PARAM_READOUT_PORT =        ((CLASS2<<16) + (TYPE_ENUM<<24)      + 247)
    PARAM_PIX_TIME =            ((CLASS2<<16) + (TYPE_UNS16<<24)     + 516) # 500 for us //Laura 16/01/2015
    
            # SHUTTER PARAMETERS (CLASS 2) */
    
    PARAM_SHTR_CLOSE_DELAY =    ((CLASS2<<16) + (TYPE_UNS16<<24)     + 519) # Not available for our camera //Laura 16/01/2015
    PARAM_SHTR_OPEN_DELAY =     ((CLASS2<<16) + (TYPE_UNS16<<24)     + 520) # Not available for our camera //Laura 16/01/2015
    PARAM_SHTR_OPEN_MODE =      ((CLASS2<<16) + (TYPE_ENUM <<24)     + 521)
    PARAM_SHTR_STATUS =         ((CLASS2<<16) + (TYPE_ENUM <<24)     + 522)
    PARAM_SHTR_CLOSE_DELAY_UNIT = ((CLASS2<<16) + (TYPE_ENUM <<24)     + 543)
    PARAM_SHTR_RES =            ((CLASS2<<16) + (TYPE_ENUM <<24)     + 343)
    
    
            # I/O PARAMETERS (CLASS 2) */
    
    PARAM_IO_ADDR =             ((CLASS2<<16) + (TYPE_UNS16<<24)     + 527) # Not available for our camera //Laura 16/01/2015
    PARAM_IO_TYPE =             ((CLASS2<<16) + (TYPE_ENUM<<24)      + 528)
    PARAM_IO_DIRECTION =        ((CLASS2<<16) + (TYPE_ENUM<<24)      + 529)
    PARAM_IO_STATE =            ((CLASS2<<16) + (TYPE_FLT64<<24)     + 530)
    PARAM_IO_BITDEPTH =         ((CLASS2<<16) + (TYPE_UNS16<<24)     + 531) # Not available for our camera //Laura 16/01/2015
    
            # DIAGNOSTIC PARAMETERS (CLASS 2) */
    PARAM_DIAG =                ((CLASS2<<16) + (TYPE_UNS32<<24)     + 180)
    PARAM_DIAG_P1 =             ((CLASS2<<16) + (TYPE_UNS32<<24)     + 181)
    PARAM_DIAG_P2 =             ((CLASS2<<16) + (TYPE_UNS32<<24)     + 182)
    PARAM_DIAG_P3 =             ((CLASS2<<16) + (TYPE_UNS32<<24)     + 183)
    PARAM_DIAG_P4 =             ((CLASS2<<16) + (TYPE_UNS32<<24)     + 184)
    PARAM_DIAG_P5 =             ((CLASS2<<16) + (TYPE_UNS32<<24)     + 185)
    
            # GAIN MULTIPLIER PARAMETERS (CLASS 2) */
    
    PARAM_GAIN_MULT_FACTOR =    ((CLASS2<<16) + (TYPE_UNS16<<24)     + 537) # Not available for our camera //Laura 16/01/2015
    PARAM_GAIN_MULT_ENABLE =    ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 541) # Not available for our camera //Laura 16/01/2015
    
            # TTL Lines */
    
    PARAM_TTL_LINES =           ((CLASS2<<16) + (TYPE_INT32<<24)     +  91)
    PARAM_TTL_DIR_CTRL =        ((CLASS2<<16) + (TYPE_INT32<<24)     + 355)
    
            # Special Features */
    
    PARAM_DITHERING =           ((CLASS2<<16) + (TYPE_BOOLEAN<<24)   + 359) # Not available for our camera //Laura 16/01/2015
    
    
            # ACQUISITION PARAMETERS (CLASS 3) */
            # (next available index for class three = 11) */
    
    PARAM_EXP_TIME =            ((CLASS3<<16) + (TYPE_UNS16<<24)     +   1)
    PARAM_EXP_RES =             ((CLASS3<<16) + (TYPE_ENUM<<24)      +   2)
    PARAM_EXP_MIN_TIME =        ((CLASS3<<16) + (TYPE_FLT64<<24)     +   3)
    PARAM_EXP_RES_INDEX =       ((CLASS3<<16) + (TYPE_UNS16<<24)     +   4)
    
            # PARAMETERS FOR  BEGIN and END of FRAME Interrupts */
    PARAM_BOF_EOF_ENABLE =      ((CLASS3<<16) + (TYPE_ENUM<<24)      +   5)
    PARAM_BOF_EOF_COUNT =       ((CLASS3<<16) + (TYPE_UNS32<<24)     +   6)
    PARAM_BOF_EOF_CLR =         ((CLASS3<<16) + (TYPE_BOOLEAN<<24)   +   7)
    
    
    # Test to see if hardware/software can perform circular buffer */
    PARAM_CIRC_BUFFER =         ((CLASS3<<16) + (TYPE_BOOLEAN<<24)   + 299)
    
    # Hardware Will Automatically Stop After A Specified Number of Frames */
    PARAM_HW_AUTOSTOP =         ((CLASS3<<16) + (TYPE_INT16<<24)     + 166)
    PARAM_HW_AUTOSTOP32 =       ((CLASS3<<16) + (TYPE_INT32<<24)     + 166)
    
    
#     ********************* Class 0: Open Camera Modes ***************************/
#     
#       Function: pl_cam_open()
#       PI Conversion: CreateController()
#    */
    OPEN_EXCLUSIVE = 0

#*********************** Class 1: Error message size ************************/
    ERROR_MSG_LEN = 255      # No error message will be longer than this */
    
#********************** Class 2: Cooling type flags *************************/
# used with the PARAM_COOLING_MODE parameter id.                            
#  PI Conversion: NORMAL_COOL = TE_COOLED
#                 CRYO_COOL   = LN_COOLED
#*/
    NORMAL_COOL = 0 
    CRYO_COOL = 1
    
    # PARAM_HEAD_COOLING_CTRL */
    HEAD_COOLING_CTRL_NA = 0 # Not Available */
    HEAD_COOLING_CTRL_ON = 1     # Turn ON the head cooling */
    HEAD_COOLING_CTRL_OFF = 2     # Turn OFF the head cooling */
    # PARAM_COOLING_FAN_CTRL */
    COOLING_FAN_CTRL_NA = 0  # Not Available */
    COOLING_FAN_CTRL_ON = 1      # Enable the cooling fan */
    COOLING_FAN_CTRL_OFF = 2     # Disable the cooling fan */

#************************* Class 2: Name/ID sizes ***************************/
    CCD_NAME_LEN =  17           # Includes space for the null terminator */
    MAX_ALPHA_SER_NUM_LEN = 32   # Includes space for the null terminator */

#********************** Class 2: MPP capability flags ***********************/
# used with the PARAM_MPP_CAPABLE parameter id.     
    MPP_UNKNOWN = 0
    MPP_ALWAYS_OFF = 1
    MPP_ALWAYS_ON = 2
    MPP_SELECTABLE = 3
#************************* Class 2: Shutter flags ***************************/
# used with the PARAM_SHTR_STATUS parameter id.                            
#  PI Conversion: n/a   (returns SHTR_OPEN)
#*/
    SHTR_FAULT = 0
    SHTR_OPENING = 1
    SHTR_OPEN = 2
    SHTR_CLOSING = 3
    SHTR_CLOSED = 4
    SHTR_UNKNOWN = 5
#*********************** Class 2: Pmode constants ***************************/
# used with the PARAM_PMODE parameter id.                                   */
    PMODE_NORMAL = 0
    PMODE_FT = 1
    PMODE_MPP = 2
    PMODE_FT_MPP = 3
    PMODE_ALT_NORMAL = 4 
    PMODE_ALT_FT = 5
    PMODE_ALT_MPP = 6
    PMODE_ALT_FT_MPP = 7
    PMODE_INTERLINE = 8
    PMODE_KINETICS = 9
    PMODE_DIF = 10
    PMODE_SPECTRA_KINETICS = 11

#*********************** Class 2: Color support constants *******************/
# used with the PARAM_COLOR_MODE parameter id.                              */
    COLOR_NONE = 0
    COLOR_RGGB = 2 

#*********************** Class 2: Attribute IDs *****************************/
#
#  Function: pl_get_param()
#*/
    ATTR_CURRENT = 0
    ATTR_COUNT = 1
    ATTR_TYPE = 2
    ATTR_MIN = 3
    ATTR_MAX = 4
    ATTR_DEFAULT = 5
    ATTR_INCREMENT = 6
    ATTR_ACCESS = 7
    ATTR_AVAIL = 8

#*********************** Class 2: Access types ******************************/
#
#  Function: pl_get_param( ATTR_ACCESS )
#*/
    ACC_ERROR = 0
    ACC_READ_ONLY = 1 
    ACC_READ_WRITE = 2
    ACC_EXIST_CHECK_ONLY = 3
    ACC_WRITE_ONLY = 4
# This enum is used by the access Attribute */

#*********************** Class 2: I/O types *********************************/
# used with the PARAM_IO_TYPE parameter id.                                 */
    IO_TYPE_TTL = 0
    IO_TYPE_DAC = 1

#*********************** Class 2: I/O direction flags ***********************/
# used with the PARAM_IO_DIRECTION parameter id.                            */
    IO_DIR_INPUT = 0
    IO_DIR_OUTPUT = 1
    IO_DIR_INPUT_OUTPUT = 2

#*********************** Class 2: I/O port attributes ***********************/
    IO_ATTR_DIR_FIXED = 0
    IO_ATTR_DIR_VARIABLE_ALWAYS_READ = 1

#*********************** Class 2: Trigger polarity **************************/
# used with the PARAM_EDGE_TRIGGER parameter id.                            */
    EDGE_TRIG_POS = 2
    EDGE_TRIG_NEG = 3

#*********************** Class 2: Logic Output ******************************/
# used with the PARAM_LOGIC_OUTPUT parameter id.                            */
    OUTPUT_NOT_SCAN = 0
    OUTPUT_SHUTTER = 1
    OUTPUT_NOT_RDY = 2
    OUTPUT_LOGIC0 = 3
    OUTPUT_CLEARING = 4
    OUTPUT_NOT_FT_IMAGE_SHIFT = 5 
    OUTPUT_RESERVED = 6
    OUTPUT_LOGIC1 = 7
    OUTPUT_EXPOSE_PROG = 8 
    OUTPUT_EXPOSE = 9
    OUTPUT_IMAGE_SHIFT = 10
    OUTPUT_READOUT = 11
    OUTPUT_ACQUIRING = 12
    OUTPUT_WAIT_FOR_TRIG = 13

#*********************** Class 2: PI-Max intensifer gating settings *********/
# used with the PARAM_SHTR_GATE_MODE parameter id.                          */
    INTENSIFIER_SAFE = 0
    INTENSIFIER_GATING = 1
    INTENSIFIER_SHUTTER = 2

#*********************** Class 2: PI-Max Option Board Specifiers ************/
# for PARAM_TG_OPTION_BD_TYPE                                               */
    OPTN_BD_SPEC = ct.c_int
# enum OPTN_BD_SPEC       
    OPTN_BD_NONE = 0              # Standard Option bd                     */
    OPTN_BD_PTG_FAST_GATE = 1           # PTG Fast gate bd                       */
    OPTN_BD_SS_FAST_GATE = 2            # SuperSynchro Fast Gate bd.             */
    OPTN_BD_SS_RF_MOD = 3               # SuperSynchro RF modulation bd.         */
    
    OPTN_BD_FOR_SPR = 100
    OPTN_BD_SPR_3917 = 101                # SPR-3917                               */
    
    OPTN_BD_END = 999
#*********************** Class 2: Readout Port ******************************/
# used with the PARAM_READOUT_PORT parameter id.                            */
    READOUT_PORT_MULT_GAIN = 0,
    READOUT_PORT_NORMAL = 1
    READOUT_PORT_LOW_NOISE = 2
    READOUT_PORT_HIGH_CAP = 3
    READOUT_PORT_HIGH_SPEED = 4
    # deprecated */
    READOUT_PORT1 = 0
    READOUT_PORT2 = 1

#*********************** Class 2: Anti Blooming *****************************/
# used with the PARAM_ANTI_BLOOMING parameter id.                           */
    ANTIBLOOM_NOTUSED = 0
    ANTIBLOOM_INACTIVE = 1
    ANTIBLOOM_ACTIVE = 2
#*********************** Class 2: Clearing mode flags ***********************/
# used with the PARAM_CLEAR_MODE parameter id.                              */
    CLEAR_NEVER = 0
    CLEAR_PRE_EXPOSURE = 1
    CLEAR_PRE_SEQUENCE = 2
    CLEAR_POST_SEQUENCE = 3
    CLEAR_PRE_POST_SEQUENCE = 4
    CLEAR_PRE_EXPOSURE_POST_SEQ = 5
#*********************** Class 2: Shutter mode flags ************************/
#
#  Function: pl_set_param ( PARAM_SHTR_OPEN_MODE )
#
#  PI Conversion: OPEN_NEVER:        SHUTTER_CLOSE
#                 OPEN_PRE_EXPOSURE: SHUTTER_OPEN  & CMP_SHT_PREOPEN = FALSE
#                 OPEN_PRE_SEQUENCE: SHUTTER_DISABLED_OPEN
#                 OPEN_PRE_TRIGGER:  SHUTTER_OPEN & CMP_SHT_PREOPEN = TRUE
#                 OPEN_NO_CHANGE:    SHUTTER_OPEN
#*/
    OPEN_NEVER = 0
    OPEN_PRE_EXPOSURE = 1
    OPEN_PRE_SEQUENCE = 2
    OPEN_PRE_TRIGGER = 3
    OPEN_NO_CHANGE = 4
#*********************** Class 2: Pixel Bias Correction *********************/
# used with the PARAM_PBC parameter id.                                     */
    PBC_DISABLED = 0
    PBC_ENABLED = 1
#*********************** Class 2: Shutter delay time resolution *************/
# used with the PARAM_SHTR_RES parameter id.                                */
    SHTR_RES_100_NANO_SEC = 1
    SHTR_RES_100_MICRO_SEC = 2
    SHTR_RES_1_MILLI_SEC = 3
#*********************** Class 2: Exposure mode flags ***********************/
# used with the PARAM_EXPOSURE_MODE parameter id.                    
#-----------------------------------------------------------------------------*/
    TIMED_MODE = 0
    STROBED_MODE = 1
    BULB_MODE = 2
    TRIGGER_FIRST_MODE = 3
    FLASH_MODE = 4
    VARIABLE_TIMED_MODE = 5
    INT_STROBE_MODE = 6
#********************* Class 3: Readout status flags ************************/
#
#  Function: pl_exp_check_status()
#  PI Conversion: PICM_LockCurrentFrame()
#                 PICM_Chk_Data()
#
#    if NEWDATARDY or NEWDATAFIXED     READOUT_COMPLETE
#    else if RUNNING                   ACQUISITION_IN_PROGRESS
#    else if INITIALIZED or DONEDCOK   READOUT_NOT_ACTIVE
#    else                              READOUT_FAILED
#
#*/
    READOUT_NOT_ACTIVE = 0
    EXPOSURE_IN_PROGRESS = 1
    READOUT_IN_PROGRESS = 2
    READOUT_COMPLETE = 3                 # Means frame available for a circular buffer acq */
    FRAME_AVAILABLE = READOUT_COMPLETE  # New camera status indicating at least one frame is available */
    READOUT_FAILED = 4
    ACQUISITION_IN_PROGRESS = 5
    MAX_CAMERA_STATUS = 6
#********************* Class 3: Abort Exposure flags ************************/
#
#  Function: pl_exp_abort()
#  PI Conversion: controller->Stop(), enum spec ignored
#*/
    CCS_NO_CHANGE = 0
    CCS_HALT = 1
    CCS_HALT_CLOSE_SHTR = 2
    CCS_CLEAR = 3
    CCS_CLEAR_CLOSE_SHTR = 4
    CCS_OPEN_SHTR = 5
    CCS_CLEAR_OPEN_SHTR = 6
#*********************** Class 3: Event constants ***************************/
    EVENT_START_READOUT = 0
    EVENT_END_READOUT = 1
#*********************** Class 3: EOF/BOF constants *************************/
# used with the PARAM_BOF_EOF_ENABLE parameter id.                          */
    NO_FRAME_IRQS = 0
    BEGIN_FRAME_IRQS = 1
    END_FRAME_IRQS = 2
    BEGIN_END_FRAME_IRQS = 3
#*********************** Class 3: Continuous Mode constants *****************/
#
#  Function: pl_exp_setup_cont()
#*/
    CIRC_NONE = 0
    CIRC_OVERWRITE = 1
    CIRC_NO_OVERWRITE = 2
#*********************** Class 3: Fast Exposure Resolution constants ********/
# used with the PARAM_EXP_RES parameter id.                                 */
    EXP_RES_ONE_MILLISEC = 0
    EXP_RES_ONE_MICROSEC = 1
    EXP_RES_ONE_SEC = 2
#*********************** Class 3: I/O Script Locations **********************/
    SCR_PRE_OPEN_SHTR = 0
    SCR_POST_OPEN_SHTR = 1
    SCR_PRE_FLASH = 2
    SCR_POST_FLASH = 3
    SCR_PRE_INTEGRATE = 4
    SCR_POST_INTEGRATE = 5
    SCR_PRE_READOUT = 6
    SCR_POST_READOUT = 7
    SCR_PRE_CLOSE_SHTR = 8
    SCR_POST_CLOSE_SHTR = 9
#************************ Class 3: Region Definition ************************/
    class rgn_type(ct.Structure):
        """Region definition structure."""
        _fields_ = [
            ('s1', uns16),                 # First pixel in the serial register */
            ('s2', uns16),                 # Last pixel in the serial register */
            ('sbin', uns16),               # Serial binning for this region */
            ('p1', uns16),                 # First row in the parallel register */
            ('p2', uns16),                 # Last row in the parallel register */
            ('pbin', uns16)]               # Parallel binning for this region */
            
    rgn_ptr = ct.POINTER(rgn_type)
    rgn_const_ptr = rgn_ptr

#********************* Class 4: Buffer bit depth flags **********************/
    PRECISION_INT8 = 0
    PRECISION_UNS8 = 1
    PRECISION_INT16 = 2
    PRECISION_UNS16 = 3
    PRECISION_INT32 = 4
    PRECISION_UNS32 = 5
#************************* Class 6: Export Control **************************/
    class export_ctrl_type(ct.Structure):
        """Export Control."""
        _fields_ = [
            ('rotate', rs_bool),           # TRUE=Rotate the data during export
            ('x_flip', rs_bool),           # TRUE=Flip the data horizontally during export
            ('y_flip', rs_bool),           # TRUE=Flip the data vertically during export
            ('precision', int16),          # Bits in output data, see constants
            ('windowing', int16),          # See list of constants
            ('max_inten', int32),          # Highest intensity, if windowing
            ('min_inten', int32),          # Lowest intensity, if windowing
            ('output_x_size', int16),      # Controls output array size
            ('output_y_size', int16)]      # Controls output array size
            
    export_ctrl_ptr = ct.POINTER(export_ctrl_type)
    export_ctrl_const_ptr = export_ctrl_ptr
#************************* Classless Entries       **************************/
# used with the PARAM_SHTR_CLOSE_DELAY_UNIT parameter id.                   */
    TIME_UNITS = ct.c_int
    TU_DAY    = 10	
    TU_HOUR   = 5
    TU_MINUTE = 4
    TU_SEC    = 3
    TU_MSEC   = 2      # millisecond  */
    TU_USEC   = 1      # microsecond  */
    TU_NSEC   = 7      # nanosecond   */
    TU_PSEC   = 8      # picosecond   */
    TU_FSEC   = 9      # femtosecond  */

#*************************** Function Prototypes ****************************/

#****************************************************************************/
#             Class 0: Camera Communications Function Prototypes            */
#****************************************************************************/
    pl_pvcam_get_ver = (rs_bool, uns16_ptr)
    pl_pvcam_init = (rs_bool, )
    pl_pvcam_uninit = (rs_bool, )
    
    pl_cam_check = (rs_bool, int16)
    pl_cam_close = (rs_bool, int16)
    pl_cam_get_diags = (rs_bool, int16)
    pl_cam_get_name = (rs_bool, int16, char_ptr)
    pl_cam_get_total = (rs_bool, int16_ptr)
    pl_cam_open = (rs_bool, char_ptr, int16_ptr, int16)
    
    pl_ddi_get_ver = (rs_bool, uns16_ptr)

#****************************************************************************/
#                Class 1: Error Reporting Function Prototypes               */
#****************************************************************************/

    pl_error_code = (int16, )
    pl_error_message = (rs_bool, int16, char_ptr)
#****************************************************************************/
#              Class 2: Configuration/Setup Function Prototypes             */
#****************************************************************************/
    
    pl_get_param = (rs_bool, int16, uns32, int16, void_ptr)
    pl_set_param = (rs_bool, int16, uns32, void_ptr)
    pl_get_enum_param = (rs_bool, int16, uns32, uns32, int32_ptr, char_ptr, uns32)
    pl_enum_str_length = (rs_bool, int16, uns32, uns32, uns32_ptr)
#****************************************************************************/
#               Class 3: Data Acquisition Function Prototypes               */
#****************************************************************************/
    
    pl_exp_init_seq = (rs_bool, )
    pl_exp_uninit_seq = (rs_bool, )
    pl_exp_get_driver_buffer = (rs_bool, int16, void_ptr_ptr, uns32_ptr)
    pl_exp_setup_seq = (rs_bool, int16, uns16, uns16, rgn_const_ptr, int16, uns32, uns32_ptr)
    pl_exp_start_seq = (rs_bool, int16, void_ptr)
    pl_exp_setup_cont = (rs_bool, int16, uns16, rgn_const_ptr, int16, uns32, uns32_ptr, int16)
    pl_exp_start_cont = (rs_bool, int16, void_ptr, uns32)
    pl_exp_check_status = (rs_bool, int16, int16_ptr, uns32_ptr)
    pl_exp_check_cont_status = (rs_bool, int16, int16_ptr, uns32_ptr, uns32_ptr)
    pl_exp_get_latest_frame = (rs_bool, int16, void_ptr_ptr)
    pl_exp_get_oldest_frame = (rs_bool, int16, void_ptr_ptr)
    pl_exp_unlock_oldest_frame = (rs_bool, int16)
    pl_exp_stop_cont = (rs_bool, int16, int16)
    pl_exp_abort = (rs_bool, int16, int16)
    pl_exp_finish_seq = (rs_bool, int16, void_ptr, int16)
    pl_exp_unravel = (rs_bool, int16, uns16, void_ptr, uns16, rgn_const_ptr, uns16_ptr) # small doubt : uns16_ptr * array_list ??
    pl_exp_wait_start_xfer = (rs_bool, int16, uns32)
    pl_exp_wait_end_xfer = (rs_bool, int16, uns32)
    
    pl_io_script_control = (rs_bool, int16, uns16, flt64, uns32)
    pl_io_clear_script_control = (rs_bool, int16)
    
#****************************************************************************/
#             Class 4: Buffer Manipulation Function Prototypes              */
#****************************************************************************/
    
    pl_buf_init = (rs_bool, )
    pl_buf_uninit = (rs_bool, )
    pl_buf_alloc = (rs_bool, int16_ptr, int16, int16, int16, rgn_const_ptr)
    pl_buf_get_bits = (rs_bool, int16, int16_ptr)
    pl_buf_get_exp_date = (rs_bool, int16, int16, int16_ptr, uns8_ptr, uns8_ptr, uns8_ptr, uns8_ptr, uns8_ptr, uns16_ptr)
    pl_buf_set_exp_date = (rs_bool, int16, int16, int16, uns8, uns8, uns8, uns8, uns8, uns16)
    pl_buf_get_exp_time = (rs_bool, int16, int16, uns32_ptr)
    pl_buf_get_exp_total = (rs_bool, int16, int16_ptr)
    pl_buf_get_img_bin = (rs_bool, int16, int16_ptr, int16_ptr)
    pl_buf_get_img_handle = (rs_bool, int16, int16, int16, int16_ptr)
    pl_buf_get_img_ofs = (rs_bool, int16, int16_ptr, int16_ptr)
    pl_buf_get_img_ptr = (rs_bool, int16, void_ptr_ptr)
    pl_buf_get_img_size = (rs_bool, int16, int16_ptr, int16_ptr)
    pl_buf_get_img_total = (rs_bool, int16, int16_ptr)
    pl_buf_get_size = (rs_bool, int16, uns32_ptr)
    pl_buf_free = (rs_bool, int16)

##****************************************************************************/
## The following functions are obsolete and their corresponding PARAM_       */
## parameters should be used with pl_get_param(), pl_set_param(),            */
## pl_get_enum_param(), and pl_enum_str_length()                             */
##****************************************************************************/
#    pl_dd_get_info = (rs_bool, int16, int16, char_ptr) # Use PARAM_DD_INFO    
#    pl_dd_get_info_length = (rs_bool, int16, int16_ptr) # Use PARAM_DD_INFO_LENGTH
#    pl_dd_get_ver = (rs_bool, int16, uns16_ptr) # Use PARAM_DD_VERSION
#    pl_dd_get_retries = (rs_bool, int16, uns16_ptr)
#    pl_dd_set_retries = (rs_bool, int16, uns16) # Use PARAM_DD_RETRIES
#    pl_dd_get_timeout = (rs_bool, int16, uns16_ptr)
#    pl_dd_set_timeout = (rs_bool, int16, uns16) # Use PARAM_DD_TIMEOUT
#    pl_ccd_get_adc_offset = (rs_bool, int16, int16_ptr)
#    pl_ccd_set_adc_offset = (rs_bool, int16, int16) # Use PARAM_ADC_OFFSET
#    pl_ccd_get_chip_name = (rs_bool, int16, char_ptr) # Use PARAM_CHIP_NAME
#    pl_ccd_get_clear_cycles = (rs_bool, int16, uns16_ptr)
#    pl_ccd_set_clear_cycles = (rs_bool, int16, uns16) # Use PARAM_CLEAR_CYCLES
#    pl_ccd_get_clear_mode = (rs_bool, int16, int16_ptr)
#    pl_ccd_set_clear_mode = (rs_bool, int16, int16) # Use PARAM_CLEAR_MODE
#    pl_ccd_get_color_mode = (rs_bool, int16, uns16_ptr) # Use PARAM_COLOR_MODE
#    pl_ccd_get_cooling_mode = (rs_bool, int16, int16_ptr) # Use PARAM_COOLING_MODE
#    pl_ccd_get_frame_capable = (rs_bool, int16, rs_bool_ptr) # Use PARAM_FRAME_CAPABLE
#    pl_ccd_get_fwell_capacity = (rs_bool, int16, uns32_ptr) # Use PARAM_FWELL_CAPACITY
#    pl_ccd_get_mpp_capable = (rs_bool, int16, int16_ptr) # Use PARAM_MPP_CAPABLE
#    pl_ccd_get_preamp_dly = (rs_bool, int16, uns16_ptr) # Use PARAM_PREAMP_DELAY
#    pl_ccd_get_preamp_off_control = (rs_bool, int16, uns32_ptr)
#    pl_ccd_set_preamp_off_control = (rs_bool, int16, uns32) # Use PARAM_PREAMP_OFF_CONTROL
#    pl_ccd_get_preflash = (rs_bool, int16, uns16_ptr) # Use PARAM_PREFLASH 
#    pl_ccd_get_pmode = (rs_bool, int16, int16_ptr)
#    pl_ccd_set_pmode = (rs_bool, int16, int16)  # Use PARAM_PMODE 
#    pl_ccd_get_premask = (rs_bool, int16, uns16_ptr) # Use PARAM_PREMASK 
#    pl_ccd_get_prescan = (rs_bool, int16, uns16_ptr) # Use PARAM_PRESCAN
#    pl_ccd_get_postmask = (rs_bool, int16, uns16_ptr) # Use PARAM_POSTMASK
#    pl_ccd_get_postscan = (rs_bool, int16 , uns16_ptr ) # Use PARAM_POSTSCAN
#    pl_ccd_get_par_size = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PAR_SIZE
#    pl_ccd_get_ser_size = (rs_bool, int16 , uns16_ptr ) # Use PARAM_SER_SIZE
#    pl_ccd_get_serial_num = (rs_bool, int16 , uns16_ptr ) # Use PARAM_SERIAL_NUM
#    pl_ccs_get_status = (rs_bool, int16 , int16_ptr ) # Use PARAM_CCS_STATUS
#    pl_ccd_get_summing_well = (rs_bool, int16 , rs_bool_ptr ) # Use PARAM_SUMMING_WELL
#    pl_ccd_get_tmp = (rs_bool, int16 , int16_ptr )
#    pl_ccd_get_tmp_range = (rs_bool, int16 , int16_ptr , int16_ptr ) # Use PARAM_TEMP
#    pl_ccd_get_tmp_setpoint = (rs_bool, int16 , int16_ptr )
#    pl_ccd_set_tmp_setpoint = (rs_bool, int16 , int16 ) # Use PARAM_TEMP_SETPOINT
#    pl_ccd_set_readout_port = (rs_bool, int16 , int16 )
#    pl_ccd_get_pix_par_dist = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PIX_PAR_DIST
#    pl_ccd_get_pix_par_size = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PIX_PAR_SIZE
#    pl_ccd_get_pix_ser_dist = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PIX_SER_DIST
#    pl_ccd_get_pix_ser_size = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PIX_SER_SIZE
#    pl_spdtab_get_bits = (rs_bool, int16 , int16_ptr ) # Use PARAM_BIT_DEPTH
#    pl_spdtab_get_gain = (rs_bool, int16 , int16_ptr )
#    pl_spdtab_set_gain = (rs_bool, int16 , int16 )
#    pl_spdtab_get_max_gain = (rs_bool, int16 , int16_ptr ) # Use PARAM_GAIN_INDEX
#    pl_spdtab_get_num = (rs_bool, int16 , int16_ptr )
#    pl_spdtab_set_num = (rs_bool, int16 , int16 ) # Use PARAM_SPDTAB_INDEX
#    pl_spdtab_get_entries = (rs_bool, int16 , int16_ptr ) # Use PARAM_SPDTAB_INDEX (ATTR_MAX)
#    pl_spdtab_get_port = (rs_bool, int16 , int16_ptr )
#    pl_spdtab_get_port_total = (rs_bool, int16 , int16_ptr ) # Use PARAM_READOUT_PORT
#    pl_spdtab_get_time = (rs_bool, int16 , uns16_ptr ) # Use PARAM_PIX_TIME
#    pl_shtr_get_close_dly = (rs_bool, int16 , uns16_ptr )
#    pl_shtr_set_close_dly = (rs_bool, int16 , uns16 ) # Use PARAM_SHTR_CLOSE_DELAY
#    pl_shtr_get_open_dly = (rs_bool, int16 , uns16_ptr )
#    pl_shtr_set_open_dly = (rs_bool, int16 , uns16 ) # Use PARAM_SHTR_OPEN_DELAY
#    pl_shtr_get_open_mode = (rs_bool, int16 , int16_ptr )
#    pl_shtr_set_open_mode = (rs_bool, int16 , int16 ) # Use PARAM_SHTR_OPEN_MODE
#    pl_shtr_get_status = (rs_bool, int16 , int16_ptr ) # Use PARAM_SHTR_STATUS
#    pl_exp_get_time_seq = (rs_bool, int16 , uns16_ptr )
#    pl_exp_set_time_seq = (rs_bool, int16 , uns16 ) # Use PARAM_EXP_TIME
#    pl_exp_check_progress = (rs_bool, int16 , int16_ptr , uns32_ptr ) # Use pl_exp_check_status or pl_exp_check_cont_status


#****************************************************************************/
# End of function definitions.                                              */
#****************************************************************************/
    
    
    if sys.platform == 'win32':
        _api = ct.windll.LoadLibrary('Pvcam32.dll')
    else:
        raise NotImplementedError("Only Windows is supported")

    for _name, _value in locals().items():
#        print('Hello ' + _name)
        if _name.startswith('pl_'):
            _func = getattr(_api, _name)
            setattr(_func, 'restype', _value[0])
            setattr(_func, 'argtypes', _value[1:])
        elif not _name.startswith('_'):
            setattr(_api, _name, _value)
#            print("        " + "'" + _name + "':\t" + str(_value) + ',')
    return _api

API = API()

class Princeton(object):
    """Princeton camera interface.

    Names of wrapper functions have the 'Lucam' prefix removed from
    their API counterparts.

    Member functions raise LucamError() if an error occurs in the
    underlying API function call.

    Camera properties can be accessed in different ways. E.g. the property
    LUCAM_PROP_BRIGHTNESS of a Lucam instance 'lucam' can is accessible as:

    * lucam.GetProperty(API.LUCAM_PROP_BRIGHTNESS)
    * lucam.GetProperty('brightness')
    * lucam.brightness

    """
    
    numberPicturesToTake = 1
    
    PropertyLengthStrings = {'CCD_NAME_LEN':	17,
        'ERROR_MSG_LEN':	255,
        'MAX_ALPHA_SER_NUM_LEN':	32}
        
    PropertyReadoutStatus = {0:'Readout not active',
        1:'Exposure in progress',
        2:'Readout in progress',
        3:'Readout complete/Frame available',
        4:'Readout failed',
        5:'Acquisition in progress',
        6:'MAX_CAMERA_STATUS'}
        
    ParamSet = {'ACCUM_CAPABLE':	184680986,
        'ADC_OFFSET':	16908483,
        'ANTI_BLOOMING':	151126309,
        'BIT_DEPTH':	16908799,
        'BOF_EOF_CLR':	184745991,
        'BOF_EOF_COUNT':	117637126,
        'BOF_EOF_ENABLE':	151191557,
        'CAMERA_TYPE':	33685854,
        'CAM_FW_FULL_VERSION':	218235414,
        'CAM_FW_VERSION':	100794900,
        'CCS_STATUS':	16908798,
        'CHIP_NAME':	218235009,
        'CIRC_BUFFER':	184746283,
        'CLEAR_CYCLES':	100794465,
        'CLEAR_MODE':	151126539,
        'CLN_WHILE_EXPO':	184680800,
        'COLOR_MODE':	151126520,
        'CONTROLLER_ALIVE':	184680616,
        'CONT_CLEARS':	184680988,
        'COOLING_FAN_CTRL':	151126355,
        'COOLING_MODE':	151126230,
        'CUSTOM_CHIP':	184680535,
        'CUSTOM_TIMING':	184680536,
        'DD_INFO':	218103813,
        'DD_INFO_LENGTH':	16777217,
        'DD_RETRIES':	100663299,
        'DD_TIMEOUT':	100663300,
        'DD_VERSION':	100663298,
        'DIAG':	117571764,
        'DIAG_P1':	117571765,
        'DIAG_P2':	117571766,
        'DIAG_P3':	117571767,
        'DIAG_P4':	117571768,
        'DIAG_P5':	117571769,
        'DITHERING':	184680807,
        'EDGE_TRIGGER':	151126122,
        'EXPOSURE_MODE':	151126551,
        'EXP_MIN_TIME':	67305475,
        'EXP_RES':	151191554,
        'EXP_RES_INDEX':	100859908,
        'EXP_TIME':	100859905,
        'FRAME_CAPABLE':	184680957,
        'FTSCAN':	100794427,
        'FWELL_CAPACITY':	117572090,
        'GAIN_INDEX':	16908800,
        'GAIN_MULT_ENABLE':	184680989,
        'GAIN_MULT_FACTOR':	100794905,
        'HEAD_COOLING_CTRL':	151126354,
        'HEAD_SER_NUM_ALPHA':	218235413,
        'HW_AUTOSTOP':	16973990,
        'HW_AUTOSTOP32':	33751206,
        'INTENSIFIER_GAIN':	16908504,
        'IO_ADDR':	100794895,
        'IO_BITDEPTH':	100794899,
        'IO_DIRECTION':	151126545,
        'IO_STATE':	67240466,
        'IO_TYPE':	151126544,
        'KIN_WIN_SIZE':	100794494,
        'LOGIC_OUTPUT':	151126082,
        'LOGIC_OUTPUT_INVERT':	184680996,
        'MIN_BLOCK':	16908348,
        'MPP_CAPABLE':	151126240,
        'NUM_MIN_BLOCK':	16908349,
        'NUM_OF_STRIPS_PER_CLR':	16908386,
        'PAR_SHIFT_INDEX':	117572131,
        'PAR_SHIFT_TIME':	117572129,
        'PAR_SIZE':	100794425,
        'PBC':	151126367,
        'PCI_FW_VERSION':	100794902,
        'PIX_PAR_DIST':	100794868,
        'PIX_PAR_SIZE':	100794431,
        'PIX_SER_DIST':	100794869,
        'PIX_SER_SIZE':	100794430,
        'PIX_TIME':	100794884,
        'PMODE':	151126540,
        'POSTMASK':	100794422,
        'POSTSCAN':	100794424,
        'PREAMP_DELAY':	100794870,
        'PREAMP_OFF_CONTROL':	117572091,
        'PREEXP_CLEANS':	184680802,
        'PREFLASH':	100794871,
        'PREMASK':	100794421,
        'PRESCAN':	100794423,
        'READOUT_PORT':	151126263,
        'READOUT_TIME':	67240115,
        'SENSOR_TYPE':	33685774,
        'SERIAL_NUM':	100794876,
        'SER_SHIFT_TIME':	117572130,
        'SER_SIZE':	100794426,
        'SHTR_CLOSE_DELAY':	100794887,
        'SHTR_CLOSE_DELAY_UNIT':	151126559,
        'SHTR_GATE_MODE':	151126233,
        'SHTR_OPEN_DELAY':	100794888,
        'SHTR_OPEN_MODE':	151126537,
        'SHTR_RES':	151126359,
        'SHTR_STATUS':	151126538,
        'SKIP_AT_ONCE_BLK':	33686040,
        'SKIP_SREG_CLEAN':	184680778,
        'SPDTAB_INDEX':	16908801,
        'SUMMING_WELL':	184680953,
        'TEMP':	16908813,
        'TEMP_SETPOINT':	16908814,
        'TG_OPTION_BD_TYPE':	151126369,
        'TTL_DIR_CTRL':	33685859,
        'TTL_LINES':	33685595,
        'UNIFIED_GAIN':	33685862,
        'UNIFIED_GAIN_ENABLED':	184680805
    }
        
    ParamType = {API.PARAM_ACCUM_CAPABLE:	rs_bool,
        API.PARAM_ADC_OFFSET:	int16,
        API.PARAM_ANTI_BLOOMING:	uns32,
        API.PARAM_BIT_DEPTH:	int16,
        API.PARAM_BOF_EOF_CLR:	rs_bool,
        API.PARAM_BOF_EOF_COUNT:	uns32,
        API.PARAM_BOF_EOF_ENABLE:	uns32,
        API.PARAM_CAMERA_TYPE:	int32,
        API.PARAM_CAM_FW_FULL_VERSION:	char_ptr,
        API.PARAM_CAM_FW_VERSION:	uns16,
        API.PARAM_CCS_STATUS:	int16,
        API.PARAM_CHIP_NAME:	char_ptr,
        API.PARAM_CIRC_BUFFER:	rs_bool,
        API.PARAM_CLEAR_CYCLES:	uns16,
        API.PARAM_CLEAR_MODE:	uns32,
        API.PARAM_CLN_WHILE_EXPO:	boolean,
        API.PARAM_COLOR_MODE:	uns32,
        API.PARAM_CONTROLLER_ALIVE:	rs_bool,
        API.PARAM_CONT_CLEARS:	boolean,
        API.PARAM_COOLING_FAN_CTRL:	uns32,
        API.PARAM_COOLING_MODE:	uns32,
        API.PARAM_CUSTOM_CHIP:	rs_bool,
        API.PARAM_CUSTOM_TIMING:	rs_bool,
        API.PARAM_DD_INFO:	char_ptr,
        API.PARAM_DD_INFO_LENGTH:	int16,
        API.PARAM_DD_RETRIES:	uns16,
        API.PARAM_DD_TIMEOUT:	uns16,
        API.PARAM_DD_VERSION:	uns16,
        API.PARAM_DIAG:	uns32,
        API.PARAM_DIAG_P1:	uns32,
        API.PARAM_DIAG_P2:	uns32,
        API.PARAM_DIAG_P3:	uns32,
        API.PARAM_DIAG_P4:	uns32,
        API.PARAM_DIAG_P5:	uns32,
        API.PARAM_DITHERING:	uns32,
        API.PARAM_EDGE_TRIGGER:	uns32,
        API.PARAM_EXPOSURE_MODE:	uns32,
        API.PARAM_EXP_MIN_TIME:	flt64,
        API.PARAM_EXP_RES:	uns32,
        API.PARAM_EXP_RES_INDEX:	uns16,
        API.PARAM_EXP_TIME:	uns16,
        API.PARAM_FRAME_CAPABLE:	rs_bool,
        API.PARAM_FTSCAN:	uns16,
        API.PARAM_FWELL_CAPACITY:	uns32,
        API.PARAM_GAIN_INDEX:	int16,
        API.PARAM_GAIN_MULT_ENABLE:	rs_bool,
        API.PARAM_GAIN_MULT_FACTOR:	uns16,
        API.PARAM_HEAD_COOLING_CTRL:	uns32,
        API.PARAM_HEAD_SER_NUM_ALPHA:	char_ptr,
        API.PARAM_HW_AUTOSTOP:	int16,
        API.PARAM_HW_AUTOSTOP32:	int32,
        API.PARAM_INTENSIFIER_GAIN:	int16,
        API.PARAM_IO_ADDR:	uns16,
        API.PARAM_IO_BITDEPTH:	uns16,
        API.PARAM_IO_DIRECTION:	uns32,
        API.PARAM_IO_STATE:	flt64,
        API.PARAM_IO_TYPE:	uns32,
        API.PARAM_KIN_WIN_SIZE:	uns16,
        API.PARAM_LOGIC_OUTPUT:	uns32,
        API.PARAM_LOGIC_OUTPUT_INVERT:	rs_bool,
        API.PARAM_MIN_BLOCK:	int16,
        API.PARAM_MPP_CAPABLE:	uns32,
        API.PARAM_NUM_MIN_BLOCK:	int16,
        API.PARAM_NUM_OF_STRIPS_PER_CLR:	int16,
        API.PARAM_PAR_SHIFT_INDEX:	uns32,
        API.PARAM_PAR_SHIFT_TIME:	int16,
        API.PARAM_PAR_SIZE:	uns16,
        API.PARAM_PBC:	uns32,
        API.PARAM_PCI_FW_VERSION:	uns16,
        API.PARAM_PIX_PAR_DIST:	uns16,
        API.PARAM_PIX_PAR_SIZE:	uns16,
        API.PARAM_PIX_SER_DIST:	uns16,
        API.PARAM_PIX_SER_SIZE:	uns16,
        API.PARAM_PIX_TIME:	uns16,
        API.PARAM_PMODE:	uns32,
        API.PARAM_POSTMASK:	uns16,
        API.PARAM_POSTSCAN:	uns16,
        API.PARAM_PREAMP_DELAY:	uns16,
        API.PARAM_PREAMP_OFF_CONTROL:	uns32,
        API.PARAM_PREEXP_CLEANS:	boolean,
        API.PARAM_PREFLASH:	uns16,
        API.PARAM_PREMASK:	uns16,
        API.PARAM_PRESCAN:	uns16,
        API.PARAM_READOUT_PORT:	uns32,
        API.PARAM_READOUT_TIME:	flt64,
        API.PARAM_SENSOR_TYPE:	int32,
        API.PARAM_SERIAL_NUM:	uns16,
        API.PARAM_SER_SHIFT_TIME:	int16,
        API.PARAM_SER_SIZE:	uns16,
        API.PARAM_SHTR_CLOSE_DELAY:	uns16,
        API.PARAM_SHTR_CLOSE_DELAY_UNIT:	uns32,
        API.PARAM_SHTR_GATE_MODE:	uns32,
        API.PARAM_SHTR_OPEN_DELAY:	uns16,
        API.PARAM_SHTR_OPEN_MODE:	uns32,
        API.PARAM_SHTR_RES:	uns32,
        API.PARAM_SHTR_STATUS:	uns32,
        API.PARAM_SKIP_AT_ONCE_BLK:	int32,
        API.PARAM_SKIP_SREG_CLEAN:	boolean,
        API.PARAM_SPDTAB_INDEX:	int16,
        API.PARAM_SUMMING_WELL:	rs_bool,
        API.PARAM_TEMP:	int16,
        API.PARAM_TEMP_SETPOINT:	int16,
        API.PARAM_TG_OPTION_BD_TYPE:	uns32,
        API.PARAM_TTL_DIR_CTRL:	int32,
        API.PARAM_TTL_LINES:	int32,
        API.PARAM_UNIFIED_GAIN:	int32,
        API.PARAM_UNIFIED_GAIN_ENABLED:	boolean
    }
    
    ParamCType = {
        13:'char_ptr',
        12:'int8',
        5:'uns8',
        1:'int16',
        6:'uns16',
        2:'int32',
        7:'uns32',
        8:'uns64',
        4:'flt64',
        9:'enum',
        11:':boolean',
        14:'void_ptr',
        15:'void_ptr_ptr'}
        
    PropertyForATTR_ACCESS = {0:	'error',
        1:	'read only',
        2:	'read/write',
        3:	'existCheckOnly',
        4:	'write only'}
    
        
    class ParamAccess(Enum):
        error = 0
        readOnly = 1 
        ReadWrite = 2
        existCheckOnly = 3
        WriteOnly = 4
    
    
    def __init__(self, number=0):
        """Open connection to Princeton camera.

        number : int
            Camera number. Must be in range 0 through PrincetonNumCameras()-1.

        """
        res = API.pl_pvcam_init()
        if res == 0:
            errorcode = API.pl_error_code()
            if not errorcode == 2001:
                raise PrincetonError(errorcode)
        self.exposureInitSequential()
        self.bufferInit()
        self._camname = ""
        self._handle = int16(0)
        camname = ct.create_string_buffer(CAM_NAME_LEN)
        phandle = int16_ptr(int16(0))
        if API.pl_cam_get_name(number, camname) == 0:
            raise PrincetonError(API.pl_error_code())
        self._camname = camname.value
        if API.pl_cam_open(camname, phandle, API.OPEN_EXCLUSIVE) == 0:
            raise PrincetonError(API.pl_error_code())
        self._handle = phandle.contents
#       Set the temperature to 20°C just in case
        self.setpoint_temperature = 20
#       Set the exposure time
        self.setExposureTime(1, ExposureUnits.microsecond)
        self.setParameterValue('EXP_TIME', self.expTime)
#       Set the camera ROI
        Camerasizes, Camerasizep = self.getCameraSize()
        bins = 1  # for ROIfull
        binp = 1  # for ROIfull
        self._ROIfull = (0, Camerasizes-1, bins, 0, Camerasizep-1, binp)  # full detector acquisition
        self._ROIspectroscopy = (0, Camerasizes-1, bins, 0, Camerasizep-1, Camerasizep)  # spectroscopy mode ("vertical" binning)
        self._ROI = []  # initialise empty ROI
        self.addExposureROI(self._ROIfull)  # set ROI to full (2D)
#       Set the exposure mode
        self._exposureMode = ExposureMode.timed
        
        self._currentBuffer = int16(0) 
        self._circularBufferMode = CircularBufferMode.overwrite
        self.abortMode = CameraControlState.clearCloseShutter
        self._continuousPixelStream = None
    
#==============================================================================
#     Class 0 functions
#==============================================================================
        
    def openCamera(self, number):
        """Open connection to Princeton camera."""
        self.getCameraNameWithNumber(number)
        phandle = int16_ptr(int16(0))
        camname = ct.create_string_buffer(self._camname)
        if API.pl_cam_open(camname, phandle, API.OPEN_EXCLUSIVE) == 0:
            if self.getLastErrorForCamera() == 117:
                print('Camera already opened')
                return
            raise PrincetonError(API.pl_error_code())
        self._handle = phandle.contents
        return
        
        
    def getCameraNameWithNumber(self, number):
        """Gets the name of the camera with ID number.

        number : int
            Camera number. Must be in range 0 through PrincetonNumCameras()-1.
        """
        camname = ct.create_string_buffer(CAM_NAME_LEN)
        if API.pl_cam_get_name(number, camname) == 0:
            raise PrincetonError(API.pl_error_code())
        self._camname = camname.value
        return self._camname
        
    def getCameraSize(self):
        """Returns the detector's dimensions in pixels."""
        return self.getParameterCurrentValue(API.PARAM_SER_SIZE), self.getParameterCurrentValue(API.PARAM_PAR_SIZE)   
        
    def getCameraName(self):
        """Returns the name of the camera given by the program."""
        return self._camname
        
    def close(self):
        """Closes all (connection to Princeton camera, pvcam, sequence mode, bufferfunctions)."""
        if not self._currentBuffer.value == 0:
            self.bufferFree(self._currentBuffer)
        self.closeCamera()
        self.exposureUninit()
        self.bufferUninit()
        self.uninitPVCAM()
            
    def closeCamera(self):
        """Close connection to Princeton camera."""
        if API.pl_cam_close(self._handle) == 0:
            raise PrincetonError(API.pl_error_code())
            
    
    def checkValidHandle(self):
        """Checks that the handle of the camera is a valid one."""
        return API.pl_cam_check(self._handle) == 1
    
    def checkCameraOK(self):
        """Checks that there is no problem with the camera that would prevent
        from taking a picture.
        """
        if API.pl_cam_get_diags(self._handle) == 0:
            raise PrincetonError(API.pl_error_code())
        return True
        
        
    def getTotalNumberCamera(self):
        """Returns the number of camera detected or raises an error."""
        some_int = int16()
        if API.pl_cam_get_total(ct.byref(some_int)) == 0:
            raise PrincetonError(API.pl_error_code())
        return some_int.value
    
    def getDDIversion(self):
        """Returns the version number of the current DDI (device driver interface)."""
        ddi = uns16()
        if API.pl_ddi_get_ver(ct.byref(ddi)) == 0:
            raise PrincetonError(API.pl_error_code())
        return ddi.value
            
    
    def initPVCAM(self):
        """Checks that there is no problem with the camera that would prevent
        from taking a picture.
        """
        if API.pl_pvcam_init() == 0:
            raise PrincetonError(API.pl_error_code())
            
    def uninitPVCAM(self):
        """Checks that there is no problem with the camera that would prevent
        from taking a picture.
        """
        if API.pl_pvcam_uninit() == 0:
            raise PrincetonError(API.pl_error_code())
            
    def versionPVCAM(self):
        """Checks that there is no problem with the camera that would prevent
        from taking a picture.
        """
        v = uns16()
        if API.pl_pvcam_get_ver(ct.byref(v)) == 0:
            raise PrincetonError(API.pl_error_code())
        return v.value 
        
#==============================================================================
#     Class 1 functions
#==============================================================================
            
    def getLastErrorForCamera(self):
        """Return code of last error that occurred in a API function.

        Error codes and messages can be found in PrincetonError.CODES.

        """
        return API.pl_error_code()
        
    def getErrorMessage(self, IDerrorCode):
        """Return code meesage the error defined by IDerrorCode.

        Error codes and messages can be found in PrincetonError.CODES.
        
        Parameters
        ----------
        IDerrorCode = int

        """
        errorMessage = PrincetonError.CODES.get(IDerrorCode)
        return errorMessage
        
            
#==============================================================================
#     Class 2 functions
#==============================================================================
            
    def _getEnumeratedParameter(self, parameter, index, length):
        """Return the current value of the parameter defined by parameter.
        
        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name of the parameter to read. All possible names are in the 
            dictionary Princeton.ParamSet.
        mode : one of the enumerated type AttributeType :
            currentValue = 0
            count = 1
            typeValue = 2
            minValue = 3
            maxValue = 4
            defaultValue = 5
            increment = 6
            access = 7
            available = 8
            or the corresponding int

        Returns
        ----------
        The value of the parameter in the right type
        """
        paramCode = parameter
        if type(parameter) == str:
            if not self.ParamSet.has_key(parameter):
                raise PrincetonError(2018)
            paramCode = self.ParamSet.get(parameter)
        description = ct.create_string_buffer(length)
        indexC = uns32(index)
        valueEnum = int32()
        if API.pl_get_enum_param(self._handle, paramCode, indexC, ct.byref(valueEnum), description, length) == 0:
            raise PrincetonError(API.pl_error_code())
        return (description.value, valueEnum.value)
        
    def _enumDescriptionLength(self, parameter, index):
        """Gives the length of the descriptive string the parameter defined by parameter.
        
        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name of the parameter to read. All possible names are in the 
            dictionary Princeton.ParamSet.
        index : the int corresponding to the value at which we want to look for the descriptive string

        Returns
        ----------
        The length of the char buffer to allocate
        """
        paramCode = parameter
        if type(parameter) == str:
            if not self.ParamSet.has_key(parameter):
                raise PrincetonError(2018)
            paramCode = self.ParamSet.get(parameter)
        indexC = uns32(index)
        lengthC = uns32()
        if API.pl_enum_str_length(self._handle, paramCode, indexC, ct.byref(lengthC)) == 0:
            raise PrincetonError(API.pl_error_code())
        return lengthC.value
        
            
    def getEnumeratedParameterAsString(self, paramCode, value):
        """Return the string that corresponds to the value of the parameter 
        defined by paramCode. This works only if paramCode is of type enumerated.

        
        Parameters
        ----------
        paramCode : long that defines the parameter
            ID of the parameter to read. All possible names/ID are in the 
            dictionary Princeton.ParamSet.
        value : python int which is returned by the bare function to get the parameter 
            value (pl_get_param), to be converted to human-readable message

        Returns
        ----------
        description : string that describes the value of the parameter

        """
        length = self._enumDescriptionLength(paramCode, value)
        description = ct.create_string_buffer(length)
        numberPossibleParam = self.getParameterValue(paramCode, AttributeType.count)
        i = 0
        while i < numberPossibleParam:
            (description, valueEnum) = self._getEnumeratedParameter(paramCode, i, length)
            if valueEnum == value:
                return description
            i = i + 1
            
    def getParameterValue(self, parameter, mode):
        """Return the current value of the parameter defined by parameter.
        
        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name of the parameter to read. All possible names are in the 
            dictionary Princeton.ParamSet.
        mode : one of the enumerated type AttributeType :
        
            currentValue = 0 (result in type of param)
            count = 1 (result in int)
            typeValue = 2 (result in string)
            minValue = 3 (result in type of param)
            maxValue = 4 (result in type of param)
            defaultValue = 5 (result in type of param)
            increment = 6 (result in type of param)
            access = 7 (result in string)
            available = 8 (result in bool)

            or the corresponding int

        Returns
        ----------
        The value of the parameter in the right type
        """
#        Checks the type of the parameters and changes it if necessary
        paramCode = parameter
        modevalue = mode
        if type(mode) == AttributeType :
            modevalue = mode.value
        modevalue = int16(modevalue)
        if type(parameter) == type('bla'):
            if not self.ParamSet.has_key(parameter):
                raise PrincetonError(2018)
            paramCode = self.ParamSet.get(parameter)
#        Defines the type of the return value (depends on the mode of the attribute
#            of the parameter on wants to access)
        returnValue = self.ParamType.get(paramCode) # if we want the min/max/increment/default/current value
        if returnValue == char_ptr:
            returnValue = ct.create_string_buffer(255) # unsubtle buffer
        else:
            returnValue = returnValue()
        
        if mode == AttributeType.typeValue: # if we want the type
            returnValue = uns32()
        elif mode == AttributeType.access: # if we want the access type
            returnValue = uns32()
        elif mode == AttributeType.count: # if we want the number of elements in an enumerated type
            returnValue = uns32()
        elif mode == AttributeType.available: # if we want to know if the parameter is available
            returnValue = boolean()
            
        if API.pl_get_param(self._handle, paramCode, modevalue, ct.byref(returnValue)) == 0:
            raise PrincetonError(API.pl_error_code())
        
        if mode == AttributeType.typeValue: # if we want the type
            returnValue = returnValue.value
            return self.ParamCType.get(returnValue)
        elif mode == AttributeType.available: # if we want to know if the parameter is available
            return returnValue.value
        elif mode == AttributeType.count: # if we want the number of elements in an enumerated type
            return returnValue.value
        elif mode == AttributeType.access: # if we want the access type
            returnValue = returnValue.value
            return self.PropertyForATTR_ACCESS.get(returnValue)
         # if we want the min/max/increment/default/current value
        elif mode == AttributeType.currentValue or mode == AttributeType.defaultValue or mode == AttributeType.minValue or mode == AttributeType.maxValue or mode == AttributeType.increment:
#            Check if is an enum to get the proper string
            attributeType = uns32()
            if API.pl_get_param(self._handle, paramCode, API.ATTR_TYPE, ct.byref(attributeType)) == 0:
                raise PrincetonError(API.pl_error_code())
            if attributeType.value == 9:
                return (self.getEnumeratedParameterAsString(paramCode, returnValue.value), returnValue.value)
            else:
                return returnValue.value
            
    def getParameterCurrentValue(self, parameter):
        """Return the current value of the parameter defined by parameter.

        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name of the parameter to read. All possible names are in the 
            dictionary Princeton.ParamSet.
            
        Returns
        ----------
        The value of the parameter in the right type
        """
        return self.getParameterValue(parameter, AttributeType.currentValue)
            
    def getParameterDefaultValue(self, parameter):
        """Return the current value of the parameter defined by paramString.

        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name of the parameter to read. All possible names are in the 
            dictionary Princeton.ParamSet.

        Returns
        ----------
        The value of the parameter in the right type
        """
        return self.getParameterValue(parameter, AttributeType.defaultValue)
            
    def setParameterValue(self, parameter, setValue):
        """Sets the value of the parameter defined by parameter to the value 
        setValue if possible.

        Parameters
        ----------
        parameter : string or long that defines the parameter
            Name/ID of the parameter to be changed. All possible names are in the 
            dictionary Princeton.ParamSet.
            

        Returns
        ----------
        boolean True if the parameter has been changed

        """
        paramCode = parameter
        if type(parameter) == str:
            if not self.ParamSet.has_key(parameter):
                raise PrincetonError(2018)
            paramCode = self.ParamSet.get(parameter)
            paramString = parameter
        else:
            paramString = str(parameter)
        returnValue = uns16()
        if API.pl_get_param(self._handle, paramCode, API.ATTR_ACCESS, ct.byref(returnValue)) == 0:
            raise PrincetonError(API.pl_error_code())
        accessType = returnValue.value
        if accessType == 0 or accessType == 1 or accessType == 3:
            print('The parameter ' + paramString + ' is not writeable')
            return False
        setValueC = self.ParamType.get(paramCode)
        setValueC = setValueC(setValue)
        if API.pl_set_param(self._handle, paramCode, ct.byref(setValueC)) == 0:
            raise PrincetonError(API.pl_error_code())
        return True    

            
#==============================================================================
#     Class 3 functions
#==============================================================================
        
    def exposureInitSequential(self):
        """Initialize camera for data taking in sequential mode."""
        if API.pl_exp_init_seq() == 0:
            raise PrincetonError(API.pl_error_code())
        
    def _getCircularBufferMode(self):
        """NOT TESTED
        
        Gets the writing mode for circular buffers. Possible modes are values of CircularBufferMode
        enumerator:
        
        none = 0
        overwrite = 1
        nooverwrite = 2
        """
        return self._circularBufferMode
        
    def _setCircularBufferMode(self, val):
        """NOT TESTED
        
        Sets the exposure mode. Possible modes are values of ExposureMode
        enumerator:
        
        timed = 0
        strobed = 1
        bulb = 2
        triggerFirst = 3
        flash = 4
        variableTimed = 5
        intStrobed = 6
        """
        self._circularBufferMode = val 
        
    circularBufferMode = property(_getCircularBufferMode,_setCircularBufferMode)
        
    def setupExposureSequential(self):
        """Initializes all parameters to take a sequence of pictures.
        
        Returns the size of the buffer to allocate before taking the pictures.
        Uses some properties of the instance :
        
        _handle : identifier of the camera
        
        numberPicturesToTake : number of images to take
        
        ROI : regions to record
        
        expTime : exposure duration (in EXP_RES units)
        """
        nPictures = uns16(self.numberPicturesToTake)
        sizeBuffer = uns32()
        mode = int16(self._exposureMode.value)
        (numberROIsC, arrayROIs) = self._processROIforAPI()
        if API.pl_exp_setup_seq(self._handle, nPictures, numberROIsC, arrayROIs, mode, uns32(self.expTime), ct.byref(sizeBuffer)) == 0:
            raise PrincetonError(API.pl_error_code())
        return sizeBuffer.value
        
    def setupExposureContinuous(self):
        """NOT TESTED
        
        Initializes all parameters to take continuous pictures in a circular buffer.
        
        _handle : identifier of the camera
        
        numberPicturesToTake : number of images to take
        
        ROI : region to record
        
        expTime : exposure duration (in EXP_RES units)
            
        Returns
        ----------
        sizeStream : required size of pixel stream
        """
        sizeStream = uns32()
        mode = int16(self._exposureMode.value)
        circBuffMode = int16(self._circularBufferMode.value)
        (numberROIsC, arrayROIs) = self._processROIforAPI()
        if API.pl_exp_setup_cont(self._handle, numberROIsC, arrayROIs, mode, uns32(self.expTime), ct.byref(sizeStream), circBuffMode) == 0:
            raise PrincetonError(API.pl_error_code())
        return sizeStream.value
        
    def _getCurrentBuffer(self):
        """NOT TESTED
        
        Gets the current buffer
        """
        return self._currentBuffer
        
    def _setCurrentBuffer(self, val):
        """NOT TESTED
        
        Sets the current buffer to the value which will be converted to an int16.
        """
        self._currentBuffer = int16(val) 
        
    currentBuffer = property(_getCurrentBuffer,_setCurrentBuffer)
        
    def startExposureSequential(self, sizeStream):
        """Starts the acquisition of a sequence of pictures after the call of setupExposureSequential().
        
        Parameters
        ----------
        sizeStream : size of the buffer to be allocated (in bytes) given the 
            camera, the number of pictures, the regions of interest
            
        Returns
        ----------
        pixelStream : c_types array of int16
        """
#        For our 16-bit camera :
        pixelStreamtype = int32 * int(sizeStream / 2)
        pixelStream = pixelStreamtype()
        if API.pl_exp_start_seq(self._handle, pixelStream) == 0:
            raise PrincetonError(API.pl_error_code())
        return pixelStream
        
    def _startExposureContinuous(self, sizeStream, sizeBuffer):
        """ Starts the acquisition of a sequence of pictures after the call of setupExposureSequential().
        
        Parameters
        ----------
        sizeStream : size of the buffer to be allocated (in bytes) given the 
            camera, the number of pictures, the regions of interest
            
        sizeBuffer : indicates the number of bytes the buffer can hold. sizeBuffer must be an integer multiple of sizeStream
            
        Returns
        ----------
        pixelStream : c_types array of int16
        """
#        For our 16-bit camera :
        pixelStreamtype = uns16 * int(sizeBuffer / 2)
        pixelStream = pixelStreamtype()
        sizeBufferC = uns32(sizeBuffer)
        if API.pl_exp_start_cont(self._handle, pixelStream, sizeBufferC) == 0:
            raise PrincetonError(API.pl_error_code())
        return pixelStream
        
    def finishExposureSequential(self, pixelStream):
        """Finishes the acquisition of a sequence of pictures after the call of _startExposureSequential().
        
        Parameters
        ----------
        pixelStream : c_types array of int16 where the pixels will be recorded
            
        Returns
        ----------
        pixelStream : c_types array of int16
        handleBuffer : int16 handle for a buffer
        """
        handleBuffer = self._currentBuffer
        if API.pl_exp_finish_seq(self._handle, pixelStream, handleBuffer) == 0:
            raise PrincetonError(API.pl_error_code())
        return pixelStream
        
    def _stopExposureContinuous(self, pixelStream):
        """Finishes the acquisition of a sequence of pictures after the call of _startExposureSequential().
        
        Parameters
        ----------
        pixelStream : c_types array of int16 where the pixels will be recorded
            """
        if API.pl_exp_stop_cont(self._handle, self.abortMode.value) == 0:
            raise PrincetonError(API.pl_error_code())
        
    def _abortExposure(self, pixelStream):
        """NOT TESTED
        
        Finishes the acquisition of a sequence of pictures after the call of _startExposureSequential().
        
        Parameters
        ----------
        pixelStream : c_types array of int16 where the pixels will be recorded
        """
        if API.pl_exp_abort(self._handle, self.abortMode.value) == 0:
            raise PrincetonError(API.pl_error_code())
        
    def _takePictureStream(self, sizeStream):
        """Does one acquisition of a sequence of pictures after the call of setupExposureSequential().
        
        Parameters
        ----------
        sizeStream : size of the buffer to be allocated (in bytes) given the 
            camera, the number of pictures, the regions of interest
            
        Returns
        ----------
        pixelStream : c_types array of int16
        """
        pixelStream = self.startExposureSequential(sizeStream)
        (statusString, statusNumber, byteCount) = cam.exposureCheckStatus()
        statusNumberOld = statusNumber
        print(statusString)
        while statusNumber == statusNumberOld:
            time.sleep(0.01)
            (statusString, statusNumber, byteCount) = cam.exposureCheckStatus()
        print(statusString)
        pixelStream = self.finishExposureSequential(pixelStream)
        return pixelStream
        
    def exposureCheckStatus(self):
        """Check the status of the camera exposure. Returns a string 
        corresponding to the status and a number according to the following dictionary :
        
        0: Readout not active
        1: Exposure in progress
        2: Readout in progress
        3: Readout complete/Frame available
        4: Readout failed
        5: Acquisition in progress
        6: MAX_CAMERA_STATUS
        """
        statusC = int16()
        byteCount = uns32()
        if API.pl_exp_check_status(self._handle, ct.byref(statusC), ct.byref(byteCount)) == 0:
            return
            raise PrincetonError(API.pl_error_code())
        status = statusC.value
        byteCounted = byteCount.value
        return self.PropertyReadoutStatus.get(status), status, byteCounted
        
    def exposureCheckContinuousStatus(self):
        """NOT TESTED
        
        Check the status of the camera exposure. Returns a string 
        corresponding to the status and a number according to the following dictionary :
        
        0: Readout not active
        1: Exposure in progress
        2: Readout in progress
        3: Readout complete/Frame available
        4: Readout failed
        5: Acquisition in progress
        6: MAX_CAMERA_STATUS
        """
        statusC = int16()
        bufferCount = uns32()
        byteCount = uns32()
        if API.pl_exp_check_cont_status(self._handle, ct.byref(statusC), ct.byref(byteCount), ct.byref(bufferCount)) == 0:
            raise PrincetonError(API.pl_error_code())
        status = statusC.value
        byteCounted = byteCount.value
        bufferCounted = bufferCount.value
        return self.PropertyReadoutStatus.get(status), status, byteCounted, bufferCounted
        
    def _exposureGetDriverBuffer(self):
        """NOT TESTED
        
        Retrieves a pointer to the buffer that may be allocated and its size if it exists.
        If not, bufferPtr is None and sizeBuffer is 0.
            
        Returns
        ----------
        bufferPtr : void_ptr_ptr pointing to the pixel stream
        sizeBuffer : size of the pointed to array
        """
        bufferPtr = void_ptr()
        sizeBuffer = uns32()
        if API.pl_exp_get_driver_buffer(self._handle, ct.byref(bufferPtr), ct.byref(sizeBuffer)) == 0:
            raise PrincetonError(API.pl_error_code())
        if not bufferPtr:
            bufferPtr = None
            print('No buffer')
        return (bufferPtr, sizeBuffer.value)
        
    def _exposureGetLatestFrame(self):
        """Retrieves a pointer to the latest frame that has been taken in the circular buffer.
            
        Returns
        ----------
        frame : void_ptr_ptr pointing to the last frame if it exists, None otherwise
        """
        bufferPtr = void_ptr()
        bufferPtrPtr = ct.pointer(bufferPtr)
        if API.pl_exp_get_latest_frame(self._handle, bufferPtrPtr) == 0:
            raise PrincetonError(API.pl_error_code())
        if not bufferPtrPtr.contents:
            frame = None
            print('No latest frame in the circular buffer')
        else:
            frame = ct.cast(bufferPtrPtr.contents, uns16_ptr)
        return frame
        
    def _exposureGetOldestFrame(self):
        """NOT TESTED
        
        Retrieves a pointer to the oldest unretrieved frame that has been taken.
            
        Returns
        ----------
        frame : void_ptr_ptr pointing to the oldest frame if it exists, None otherwise
        """
        bufferPtr = void_ptr()
        if API.pl_exp_get_oldest_frame(self._handle, ct.byref(bufferPtr)) == 0:
            raise PrincetonError(API.pl_error_code())
#        if not bufferPtr:
#            frame = None
#            print('No oldest unretrieved frame')

#        else:
#            frame = bufferPtr.contents
        return bufferPtr
        
    def exposureUninit(self):
        """Uninitializes the data collection function."""
        if API.pl_exp_uninit_seq() == 0:
            raise PrincetonError(API.pl_error_code())
            
    def unlockOldestFrame(self):
        """NOT TESTED
        
        Makes the oldest frame in the buffer overwriteable.
        """
        if API.pl_exp_unlock_oldest_frame(self._handle) == 0:
            raise PrincetonError(API.pl_error_code())
    
    def unravelData(self, frame, exposureBuffer = 0):
        """NOT TESTED
        
        From the pixel stream where a frame is stored, gives an array of numpy arrays with the various ROIs.
            
        Parameters
        ----------
        frame : void_ptr being a frame
            
        Returns
        ----------
        images : list of numpy arrays each one being one of the defined ROIs
        """
        exposureC = uns16(exposureBuffer)
        (numberROIsC, arrayROIs) = self._processROIforAPI()
        pixelPerROI = numpy.array(self.ROIsizep) * numpy.array(self.ROIsizes) / numpy.array(self.ROIbinp) * numpy.array(self.ROIbins)
        pixelPerROI = pixelPerROI.astype(int)
        numberROIs = numberROIsC.value
        arraylist = uns16_ptr * numberROIs
        arraylist = arraylist()
        for i in range(numberROIS):
            arraylist[i] = (uns16 * pixelPerROI[i])()
        if API.pl_exp_unravel(self._handle, exposureC, frame, numberROIsC, arrayROIs, arraylist) == 0:
            raise PrincetonError(API.pl_error_code())
        images = []
        for i in range(numberROIS):
            table = arraylist[i]
            table = table[:]
            images.append(numpy.reshape(numpy.array(table), (self.ROIsizep[i] / self.ROIbinp[i], self.ROIsizes[i] / self.ROIbins[i])))
        return images
            
    def ioClearScriptControl(self):
        """NOT TESTED
        
        Clears the current setup for control of the available I/O lines within a camera script
        """
        if API.pl_io_clear_script_control(self._handle) == 0:
            raise PrincetonError(API.pl_error_code())
            
    def ioScriptControl(self, locationInSequence, addressIO, stateIOtoWrite):
        """NOT TESTED
        
        From the pixel stream where a frame is stored, gives an array of numpy arrays with the various ROIs.
            imageNumber
        Parameters
        ----------
        locationInSequence : element of ScriptLocation indicating at which moment of the data acquisition the IO should be setted
        
        addressIO : address specifying which I/O to control
        
        stateIOtoWrite : thing to write in IO (bit pattern if IO is TTL, analog value for DAC)
        """
        location = uns32(locationInSequence.value)
        addressIOC = uns16(addressIO)
        state = flt64(stateIOtoWrite)
        if API.pl_io_clear_script_control(self._handle, addressIOC, state, location) == 0:
            raise PrincetonError(API.pl_error_code())
            
#==============================================================================
#     Class 4 functions
#==============================================================================
    
            
    def bufferAllocate(self, bufferPrecision):
        """Allocate a buffer based on exposure status.
            
        Parameters
        ----------
        bufferPrecision : element of enumerated type BufferPrec 
        """
        if not self._currentBuffer.value == 0:
            self.bufferFree(self._currentBuffer)
        numberExposure = int16(self.numberPicturesToTake)
        (numberROIsC, arrayROIs) = self._processROIforAPI()
        numberROIsC = int16(numberROIsC.value)
        handleBufferC = int16()
        bufferPrecisionC = int16(bufferPrecision.value)
        
        if API.pl_buf_alloc(ct.byref(handleBufferC), numberExposure, bufferPrecisionC, numberROIsC, arrayROIs) == 0:
            raise PrincetonError(API.pl_error_code())
        self._currentBuffer = handleBufferC
        return handleBufferC
            
    def bufferFree(self, handleBuffer = None):
        """Frees the memory and the handle used by self._currentBuffer buffer."""
        if type(handleBuffer) == type(None):
            handleBuffer = self._currentBuffer
        if API.pl_buf_free(handleBuffer) == 0:
            raise PrincetonError(API.pl_error_code())
            
    def bufferGetPrecision(self):
        """Gets the bit  used by self._currentBuffer buffer.
            
        Returns
        -------
        bufferPrecision : element of enumerated type BufferPrec 
        """
        bitDepthC = int16()
        if API.pl_buf_get_bits(self._currentBuffer, ct.byref(bitDepthC)) == 0:
            raise PrincetonError(API.pl_error_code())
        return BufferPrec(bitDepthC.value)
            
    def bufferGetExposureDateRaw(self, exposureNumber):
        """Gets date of the exposure defined by exposureNumber in self._currentBuffer buffer.
            
        Parameters
        ----------
        exposureNumber : number characterizing the exposure from which to retrieve the date
            
        Returns
        -------
        tuple with (year, month, day, hour, minuts, sec, millisec)
        """
        yearC = int16()
        monthC = uns8()
        dayC = uns8()
        hourC = uns8()
        minC = uns8()
        secC = uns8()
        millisecC = uns16()
        exposureNumberC = int16(exposureNumber)
        if API.pl_buf_get_exp_date(self._currentBuffer, exposureNumberC, ct.byref(yearC), ct.byref(monthC), ct.byref(dayC), ct.byref(hourC), ct.byref(minC), ct.byref(secC), ct.byref(millisecC)) == 0:
            raise PrincetonError(API.pl_error_code())
        year = yearC.value
        month = monthC.value
        day = dayC.value
        hour = hourC.value
        minuts = minC.value
        sec = secC.value
        millisec = millisecC.value
        return (year, month, day, hour, minuts, sec, millisec)
            
    def bufferGetExposureDuration(self, exposureNumber):
        """Gets the exposure duration of an exposure in the self._currentBuffer buffer.
            
        Parameters
        ----------
        exposureNumber : number characterizing the exposure from which to retrieve the exposure duration
            
        Returns
        -------
        exposureDuration in msec
        """
        exposureTimeC = uns32()
        exposureNumberC = int16(exposureNumber)
        if API.pl_buf_get_exp_time(self._currentBuffer, exposureNumberC, ct.byref(exposureTimeC)) == 0:
            raise PrincetonError(API.pl_error_code())
        exposureTime = exposureTimeC.value
        return exposureTime
            
    def bufferGetNumberExposure(self):
        """Gets the total number of exposure in the self._currentBuffer buffer.
            
        Returns
        -------
        exposureNumbers 
        """
        exposureNumbersC = int16()
        if API.pl_buf_get_exp_total(self._currentBuffer, ct.byref(exposureNumbersC)) == 0:
            raise PrincetonError(API.pl_error_code())
        exposureNumbers = exposureNumbersC.value
        return exposureNumbers
            
    def bufferGetImageBinningFactors(self, handleImageC):
        """Gets the binning factors of an image.
            
        Parameters
        ----------
        handleImageC : handle for an image (int16)
            
        Returns
        -------
        (ibin, jbin) : binning factors on the i and j axis 
        """
        ibin = int16()
        jbin = int16()
        if API.pl_buf_get_img_bin(handleImageC, ct.byref(ibin), ct.byref(jbin)) == 0:
            raise PrincetonError(API.pl_error_code())
        return ibin.value, jbin.value
            
    def bufferGetImageHandle(self, exposureNumber, ROInumber):
        """Gets the handle for an image in self._currentBuffer buffer and the coordinates of the image (exposure number, ROI number).
            
        Parameters
        ----------
        exposureNumber : index of the exposure
        ROInumber : index of the ROI
            
        Returns
        -------
        handleImageC : handle for an image (int16)
        """
        handleImageC = int16()
        exposureNumberC = int16(exposureNumber)
        ROInumber = int16(ROInumber)
        if API.pl_buf_get_img_handle(self._currentBuffer, exposureNumberC, ROInumber, ct.byref(handleImageC)) == 0:
            raise PrincetonError(API.pl_error_code())
        return handleImageC
            
    def bufferGetImagePositionOffset(self, handleImageC):
        """STRANGE BEHAVIOUR
        
        Gets the CCD coordinates of the upper left corner of an image.
            
        Parameters
        ----------
        handleImageC : handle for an image (int16)
            
        Returns
        -------
        s1 : beginning position on serial axis
        p1 : beginning position on parallel axis
        """
        s1 = int16()
        p1 = int16()
        if API.pl_buf_get_img_bin(handleImageC, ct.byref(s1), ct.byref(p1)) == 0:
            raise PrincetonError(API.pl_error_code())
        return s1.value, p1.value
            
    def bufferGetImagePointer(self, handleImageC):
        """Gets a pointer to an image given its handle.
            
        Parameters
        ----------
        handleImageC : handle for an image (int16)
            
        Returns
        -------
        imagePointer : int16 pointer to the image
        """
        imagePointer = void_ptr()
        if API.pl_buf_get_img_ptr(handleImageC, ct.byref(imagePointer)) == 0:
            raise PrincetonError(API.pl_error_code())
        return ct.cast(imagePointer, uns16_ptr) # Our camera is 16-bits, need to cast the pointer to the right type
            
    def bufferGetImageSize(self, handleImageC):
        """Returns the number of pixel of each dimension of a region.
            
        Parameters
        ----------
        handleImageC : handle for an image (int16)
            
        Returns
        -------
        idim : i dimension
        jdim : j dimension
        """
        idim = int16()
        jdim = int16()
        if API.pl_buf_get_img_size(handleImageC, ct.byref(idim), ct.byref(jdim)) == 0:
            raise PrincetonError(API.pl_error_code())
        return idim.value, jdim.value
            
    def bufferGetImageNumberPerExposure(self):
        """Returns the number of region of interest per exposure.
            
        Returns
        -------
        imageNumber : number of image (ROI) per exposure
        """
        imageNumber = int16()
        if API.pl_buf_get_img_total(self._currentBuffer, ct.byref(imageNumber)) == 0:
            raise PrincetonError(API.pl_error_code())
        return imageNumber.value
            
            
    def bufferGetSize(self):
        """Returns the size of the buffer, in bytes.
            
        Parameters
        ----------
        handleBufferC : handle for a buffer (int16)
            
        Returns
        -------
        sizeBuffer : size of the buffer in bytes
        """
        sizeBuffer = uns32_ptr(uns32(0))
        if API.pl_buf_get_size(self._currentBuffer, sizeBuffer) == 0:
            raise PrincetonError(API.pl_error_code())
        return sizeBuffer.contents.value
            
    def bufferSetExposureDate(self, exposureNumber, year, month, day, hour, minuts, sec, millisec):
        """NOT TESTED
        
        Sets date of the exposure defined by exposureNumber.
            
        Parameters
        ----------
        exposureNumber : number characterizing the exposure from which to retrieve the date
        year, month, day, hour, minuts, sec, millisec : date to be set
        """
        yearC = int16(year)
        monthC = uns8(month)
        dayC = uns8(day)
        hourC = uns8(hour)
        minC = uns8(minuts)
        secC = uns8(sec)
        millisecC = uns16(millisec)
        exposureNumberC = int16(exposureNumber)
        if API.pl_buf_get_exp_date(self._currentBuffer, exposureNumberC, yearC, monthC, dayC, hourC, minC, secC, millisecC) == 0:
            raise PrincetonError(API.pl_error_code())
            
    def bufferInit(self):
        """Initializes the buffer functions, useful for exposures with multiple regions or complex sequences."""
        if API.pl_buf_init() == 0:
            raise PrincetonError(API.pl_error_code())
            
    def bufferUninit(self):
        """Uninitializes the buffer functions, useful for exposures with multiple regions or complex sequences"""
        if API.pl_buf_uninit() == 0:
            raise PrincetonError(API.pl_error_code())
            
#==============================================================================
#     Properties for our application
#============================================================================== 

#   Actual Temperature
    def _get_temperature(self):
        """ Get the current temperature """
        return self.getParameterCurrentValue('TEMP') / 100.

    temperature = property(_get_temperature)

#   Setpoint Temperature
    def _get_setpoint_temperature(self):
        """ Get the setpoint temperature """
        return self.getParameterCurrentValue('TEMP_SETPOINT') / 100.

    def _set_setpoint_temperature(self, val):
        """ Set the setpoint temperature """
        if  val < -110 or val > 20:  # some camera operate at -100 C
            raise Exception("setpoint temperature should be between -110 and 20, not {val}".format(val=val))
        return self.setParameterValue('TEMP_SETPOINT', val * 100)
        
    setpoint_temperature = property(_get_setpoint_temperature, _set_setpoint_temperature)      

#    for key in ...:
#        _tmp = property(lambda self:self.setParameterCurrentValue(key))
#        name = key.lower()
#        exec(key + '=_tmp')
        
#   Gain
    def _get_gain(self):
        """ Get the ADC gain index """
        return self.getParameterCurrentValue('GAIN_INDEX')

    def _set_gain(self, val):
        """ Set the ADC gain index """
        return self.setParameterValue('GAIN_INDEX', val)
                
    gain = property(_get_gain, _set_gain)      
          
#   ADC speed
    def _get_speed(self):
        """ Get the ADC speed index """
        return self.getParameterCurrentValue('SPDTAB_INDEX')

    def _set_speed(self, val):
        """ Set the ADC speed index """
        return self.setParameterValue('SPDTAB_INDEX', val)
                
    speed = property(_get_speed, _set_speed)      
                    
#   pixel pitch
    def _get_pixel_pitch(self):
        """ Get the pixel pitch
        
        Returns
        -------
        pitchs : distance center-to-center between pixels (serial direction) in nanometer
        pitchp : distance center-to-center between pixels (parallel direction) in nanometer
       
        """
        return self.getParameterCurrentValue('PIX_SER_DIST'), self.getParameterCurrentValue('PIX_PAR_DIST')
              
    pitch = property(_get_pixel_pitch)      

#   Exposure time

    def setExposureTime(self, exposureTime, exposureUnits):
        """Set the exposure time.
        
        Parameters
        ----------

        exposureTime : long that defines the exposure time in the unit defined 
            somewhere else.
            
        exposureUnits : units defined in the enumerated typ ExposureUnits
        """
        if exposureUnits.value == 0:
            self.expTime = long(exposureTime)
        elif exposureUnits.value == 1:
            self.expTime = long(exposureTime)
        self.setParameterValue(API.PARAM_EXP_RES_INDEX, exposureUnits.value)
        self.setParameterValue('EXP_TIME', self.expTime)
          
    def _getExposureTime(self):
        """Get the exposure time in units given by EXP_RES."""
        PropertyFastExposureResolutionConstant = {0:' ms',
            1:' us'}
        units = PropertyFastExposureResolutionConstant.get(self.getParameterCurrentValue(API.PARAM_EXP_RES_INDEX))
        return str(self.expTime) + units
        
    exposureTime = property(_getExposureTime)      
        
#   ROI
    def addExposureROI(self, ROI):
        """Adds the exposure Region Of Interest (ROI) in the lists _ROI. Takes a tuple 
        (s1, s2, sbin, p1, p2, pbin) 
        
        Parameters
        ----------
        
        ROI = (s1, s2, sbin, p1, p2, pbin)
            s1 : first series of pixel to be taken into account (starts at 0)
            s2 : last series of pixel to be taken into account (max at sizeCCD-1)
            sbin : data binning on the s-axis
            p1 : first parallel row of pixel to be taken into account (starts at 0)
            p2 : last parallel row of pixel to be taken into account (max at sizeCCD-1)
            pbin : data binning on the ps-axis
        """
        s1, s2, sbin, p1, p2, pbin = ROI

        self._ROI.append(API.rgn_type(s1, s2, sbin, p1, p2, pbin))
        
    def removeLastExposureROI(self):
        """Removes the last exposure Region Of Interest (ROI) in the lists _ROI."""
        self._ROI.pop()
        
    def changeLastExposureROI(self, ROI):
        """Changes the last the exposure Region Of Interest (ROI) in the lists _ROI. Takes a tuple 
        (s1, s2, sbin, p1, p2, pbin) 
        
        Parameters
        ----------
        
        ROI = (s1, s2, sbin, p1, p2, pbin)
            s1 : first series of pixel to be taken into account (starts at 0)
            s2 : last series of pixel to be taken into account (max at sizeCCD-1)
            sbin : data binning on the s-axis
            p1 : first parallel row of pixel to be taken into account (starts at 0)
            p2 : last parallel row of pixel to be taken into account (max at sizeCCD-1)
            pbin : data binning on the ps-axis
        """
        s1, s2, sbin, p1, p2, pbin = ROI
        self.removeLastExposureROI()
        self.addExposureROI(ROI)
        
    def _processROIforAPI(self):
        """Prepares an uns16 that gives the number of ROI and an rgn_pointer to an
        array of rgn_type that are the ROIs to be taken by.
        
        Returns
        -------
        numberROIsC : uns16 that gives the number of regions of interest
        arrayROIs : ctypes array of ROI of type rgn_type
        """
        numberROIs = len(self.ROI)
        arrayROIs = API.rgn_type * numberROIs
        arrayROIs = arrayROIs()
        numberROIsC = uns16(numberROIs)
        print(numberROIsC)
        print(arrayROIs)
        #print(self._ROI)
        for i in range(numberROIs):
            arrayROIs[i] = self._ROI[i]
        return numberROIsC, arrayROIs
        
    def _getExposureROI(self):
        """Get the exposure Region Of Interest (ROI). Returns a tuple 
        (s1, s2, sbin, p1, p2, pbin) 
        
        Parameters
        ----------
        
        s1 : first series of pixel to be taken into account (starts at 0)
        s2 : last series of pixel to be taken into account (max at sizeCCD-1)
        sbin : data binning on the s-axis
        p1 : first parallel row of pixel to be taken into account (starts at 0)
        p2 : last parallel row of pixel to be taken into account (max at sizeCCD-1)
        pbin : data binning on the ps-axis
        """
        ROIs = []
        for i in range(len(self._ROI)):
            currentROI = self._ROI[i]
            s1 = currentROI.s1
            s2 = currentROI.s2
            sbin = currentROI.sbin
            p1 = currentROI.p1
            p2 = currentROI.p2
            pbin = currentROI.pbin
            ROIs.append(((s1, s2, sbin, p1, p2, pbin)))
        return ROIs
        
    ROI = property(_getExposureROI)  
        
    def _getROIsizep(self):
        """Get the p-size of the Region Of Interest (ROI). """
        ROIs = self.ROI
        size = []
        for i in range(len(ROIs)): 
            s1, s2, sbin, p1, p2, pbin = ROIs[i] 
            size.append(p2-p1+1)
        return size
        
    ROIsizep = property(_getROIsizep)  
        
    def _getROIsizes(self):
        """Get the s-size of the Region Of Interest (ROI). """
        ROIs = self.ROI
        size = []
        for i in range(len(ROIs)): 
            s1, s2, sbin, p1, p2, pbin = ROIs[i] 
            size.append(s2-s1+1)
        return size
        
    ROIsizes = property(_getROIsizes)  
        
    def _getROIbins(self):
        """Get the p-binning of the Region Of Interest (ROI). """
        ROIs = self.ROI
        bin = []
        for i in range(len(ROIs)): 
            s1, s2, sbin, p1, p2, pbin = ROIs[i] 
            bin.append(sbin)
        return bin
        
    ROIbins = property(_getROIbins) 
        
    def _getROIbinp(self):
        """Get the s-binning of the Region Of Interest (ROI). """
        ROIs = self.ROI
        bin = []
        for i in range(len(ROIs)): 
            s1, s2, sbin, p1, p2, pbin = ROIs[i] 
            bin.append(pbin)
        return bin
        
    ROIbinp = property(_getROIbinp) 
        
#   Exposure Mode
    def _getExposureMode(self):
        """Gets the exposure mode. Possible modes are values of ExposureMode
        enumerator:
        
        timed = 0
        strobed = 1
        bulb = 2
        triggerFirst = 3
        flash = 4
        variableTimed = 5
        intStrobed = 6
        """
        return self._exposureMode
        
    def _setExposureMode(self, val):
        """Sets the exposure mode. Possible modes are values of ExposureMode
        enumerator:
        
        timed = 0
        strobed = 1
        bulb = 2
        triggerFirst = 3
        flash = 4
        variableTimed = 5
        intStrobed = 6
        """
        self._exposureMode = val 
        
    exposureMode = property(_getExposureMode,_setExposureMode)
    
#   Kinetics
    def _isKineticsEnabled(self):
        return self.getParameterCurrentValue(API.PARAM_PMODE)[0] == 'Kinetics'
        
    kineticsEnabled = property(_isKineticsEnabled)
    
    def _getKineticsWindowSize(self):
        return self.getParameterCurrentValue(API.PARAM_KIN_WIN_SIZE)
        
    kineticsWindowSize = property(_getKineticsWindowSize)
   
#   Shutter
    def _getShutterState(self):
        return ShutterState(self.getParameterCurrentValue(API.PARAM_SHTR_OPEN_MODE)[1])
        
    shutterState = property(_getShutterState)
    
    def _getShutterOpenMode(self):
        return ShutterOpenMode(self.getParameterCurrentValue(API.PARAM_SHTR_OPEN_MODE)[1])
    
    def _setShutterOpenMode(self, shutterMode):
        self.setParameterValue(API.PARAM_SHTR_OPEN_MODE, shutterMode.value)
        
    shutterOpenMode = property(_getShutterOpenMode,_setShutterOpenMode)
            
#==============================================================================
#     Functions for our application
#==============================================================================
        
    def takePicture(self, optionDisplayMessage = True):
        """Takes picture(s) according to the parameters defined in the object."""
        sizeStream = self.setupExposureSequential()
        self.bufferAllocate(BufferPrec.uns16precision)
        pixelStream = self.startExposureSequential(sizeStream)
        (statusString, statusNumber, byteCount) = self.exposureCheckStatus()
        statusNumberOld = statusNumber
        if optionDisplayMessage:
            print(statusString)
        while statusNumber == statusNumberOld:
            time.sleep(0.2)
#            print('statusNumber = ' + str(statusNumberOld)
            (statusString, statusNumber, byteCount) = self.exposureCheckStatus()
        if optionDisplayMessage:
            print(statusString)
        time.sleep(0.01)
        pixelStream = self.finishExposureSequential(pixelStream)
        time.sleep(0.01)
        return self.convertStream(pixelStream)
        
        
    def takeTriggedPicture(self):
        """Takes pictures in strobed mode (external trigger & internal timer 
        for all pictures)."""
        oldMode  = self.exposureMode
        self.exposureMode = ExposureMode.strobed
        images = self.takePicture()
        self.exposureMode = oldMode
        return images
        
    def convertStream(self, pixelStream):
        """Converts the pixel stream to numpy arrays after the call of 
        takePictureStream().
        
        Parameters
        ----------
        pixelStream : c_types array of int16 being filled with pixel data
            
        Returns
        ----------
        images : list of list of numpy arrays corresponding to the different exposures and ROI ; 
            images[exposureNumber][ROInumber]
        infos : list of list of strings
        """
#        if self.numberPicturesToTake == 1 and len(self.ROI) == 1:
#            print('This is a simple picture with one exposure - No need for complex buffer manipulation')
        numberExposure = self.bufferGetNumberExposure()
        numberROI = self.bufferGetImageNumberPerExposure()
        
        images = []
        infos = []
        for i1 in range(numberExposure):
            imageHandle = self.bufferGetImageHandle(i1, 0)
            date = self.bufferGetExposureDateRaw(i1)
            expTime = self.bufferGetExposureDuration(i1)
            precision = self.bufferGetPrecision().name
            regions = []
            infoRegions = []
            for i2 in range(numberROI):
                imageHandle = self.bufferGetImageHandle(i1, i2)
                (sizei, sizej) = self.bufferGetImageSize(imageHandle)
#                Get the image
                imagePointer = self.bufferGetImagePointer(imageHandle)
                image = imagePointer[0:(sizei * sizej)]
                regions.append(numpy.reshape(numpy.array(image), (sizei, sizej)))
#                Get the informations
                (bini, binj) = self.bufferGetImageBinningFactors(imageHandle)
                (offsets, offsetp) = self.bufferGetImagePositionOffset(imageHandle)
                infoRegion = 'Exposure\t' + str(i1+1) + '/' + str(numberExposure) + '\n'
                infoRegion = infoRegion + 'ROI\t' + str(i2+1) + '/' + str(numberROI) + '\n'
                infoRegion = infoRegion + 'year\t' + str(date[0]) + '\n'
                infoRegion = infoRegion + 'month\t' + str(date[1]) + '\n'
                infoRegion = infoRegion + 'day\t' + str(date[2]) + '\n'
                infoRegion = infoRegion + 'hour\t' + str(date[3]) + '\n'
                infoRegion = infoRegion + 'min\t' + str(date[4]) + '\n'
                infoRegion = infoRegion + 'sec\t' + str(date[5]) + '\n'
                infoRegion = infoRegion + 'ms\t' + str(date[6]) + '\n'
                infoRegion = infoRegion + 'sizei\t' + str(sizei) + '\n'
                infoRegion = infoRegion + 'sizej\t' + str(sizej) + '\n'
                infoRegion = infoRegion + 'bini\t' + str(bini) + '\n'
                infoRegion = infoRegion + 'binj\t' + str(binj) + '\n'
                infoRegion = infoRegion + 'offsets\t' + str(offsets) + '\n'
                infoRegion = infoRegion + 'offsetp\t' + str(offsetp) + '\n'
                infoRegion = infoRegion + 'exposureTime (ms)\t' + str(expTime) + '\n'
                infoRegion = infoRegion + 'precision (ms)\t' + str(precision) + '\n'
                infoRegions.append(infoRegion)
            images.append(regions)
            infos.append(infoRegions)
        return images, infos
        
    
        
    def enableKineticsMode(self, kineticsWindow = 256, parallelShiftTime = None):
        """Enables the kinetics mode.
            
        Parameters
        ----------
        kineticsWindow : number of rows which will be exposed
        
        parallelShiftTime : time in ns to shift one parallel row (if unvalid, set to minimum value)
        """
#        Checks that the shift times for parallel and serial register is of the right
#        type and within bounds, otherwise sets it to the minimal value
        minParallelShiftTime = self.getParameterValue(API.PARAM_PAR_SHIFT_TIME, AttributeType.minValue)
        maxParallelShiftTime = self.getParameterValue(API.PARAM_PAR_SHIFT_TIME, AttributeType.maxValue)
        if not (type(parallelShiftTime) == int or type(parallelShiftTime) == long):
            parallelShiftTime = minParallelShiftTime
            print('parallelShiftTime set to the minimum possible value.')
        elif parallelShiftTime < minParallelShiftTime or parallelShiftTime > maxParallelShiftTime:
            parallelShiftTime = minParallelShiftTime
            print('parallelShiftTime set to the minimum possible value.')
        
#        Checks that the size for the kinetics mode is within the right range
        maxKineticsWindowsSize = self.getParameterValue(API.PARAM_PAR_SIZE, AttributeType.currentValue)
        if kineticsWindow < 1:
            kineticsWindow = 1
            print('Given size for kinetics window is too small. Set to 1 row.')
        elif kineticsWindow>maxKineticsWindowsSize:
            kineticsWindow = maxKineticsWindowsSize
            print('Given size for kinetics window is too small. Set to the total number of rows.')
        
#        Sets the kinetics mode
        self.setParameterValue(API.PARAM_PMODE, 9)
        self.setParameterValue(API.PARAM_KIN_WIN_SIZE, kineticsWindow)
        self.setParameterValue(API.PARAM_PAR_SHIFT_TIME, parallelShiftTime)
        
    def disableKineticsMode(self):
        """Disables the kinetics mode. The involved parameters go back to the 
        default parameters.
        """
        if self.kineticsEnabled:
#            Go back to default parameters
            defaultParallelShiftTime = self.getParameterValue(API.PARAM_PAR_SHIFT_TIME, AttributeType.defaultValue)
            defaultKineticsWindowsSize = self.getParameterValue(API.PARAM_KIN_WIN_SIZE, AttributeType.defaultValue)
            
#            Unsets the kinetics mode
            self.setParameterValue(API.PARAM_KIN_WIN_SIZE, defaultKineticsWindowsSize)
            self.setParameterValue(API.PARAM_PAR_SHIFT_TIME, defaultParallelShiftTime)
            self.setParameterValue(API.PARAM_PMODE, 0)
            
    def startContinuous(self):
        sizeStream = self.setupExposureContinuous()
        sizeBuffer = 5 * sizeStream
        pixelStream = self._startExposureContinuous(sizeStream, sizeBuffer)
        self._continuousPixelStream = pixelStream
        
    def stopContinuous(self):
        self._stopExposureContinuous(self._continuousPixelStream)
        
    def retrieveContinuousFrame(self):
        frame = self._exposureGetLatestFrame()
        if len(self.ROI) == 1:
            roi = self.ROI[0]
            sizei = int((roi[1] - roi[0] + 1) / roi[2])
            sizej = int((roi[4] - roi[3] + 1) / roi[5])
            image = frame[0:(sizei * sizej)]
            return numpy.reshape(numpy.array(image), (sizei, sizej))
        


class PrincetonError(Exception):
    """Exception to report Princeton problems."""

    def __init__(self, arg=None):
        """Initialize PrincetonError instance.

        Parameters
        ----------
        arg : int, Princeton instance, or None
            If arg is None or a Princeton instance, the last error that occured
            in the API is raised. Else arg is an error code number.

        """
        if arg is None:
            self.value = API.pl_error_code()
        elif isinstance(arg, Princeton):
            self.value = arg.GetLastErrorForCamera()
        else:
            self.value = int(arg)

    def __str__(self):
        """Return error message."""
        return self.CODES.get(self.value, "Unknown error: %i" % self.value)

    CODES = {
        0: """No error.""",
        1: """C0_UNKNOWN_ERROR
        Unexpected, unanticipated, or undocumented.""",
        2: """DDI_NOT_PV_DEVICE
        This device driver is not a Roper device.""",
        3: """DDI_BAD_DEV_NAME
        No driver found with the specified name.""",
        4: """DDI_DRIVER_IN_USE
        This driver is already in use by another user.""",
        5: """DDI_ALREADY_OPEN
        This driver has already been opened.""",
        6: """DDI_CANT_OPEN_DRIVER
        The driver was found, but could not be opened.""",
        7: """DDI_CANT_CLOSE_DRIVER
        Driver is not currently open; it can't be closed.""",
        8: """DDI_CLOSE_ERROR
        An error occured while trying to close the driver.""",
        9: """DDI_ALREADY_ACTIVE
        Camera is already taking data; finish or abort.""",
        10: """DDI_ZERO_SEND_SIZE
        Invalid request: transmit zero bytes.""",
        11: """DDI_ZERO_RECV_SIZE
        Invalid request: receive zero bytes.""",
        12: """DDI_IOPORT_CONFLICT
        2 cameras are using the same I/O port.""",
        13: """DDI_BOARD_NOT_FOUND
        Communications board is not at expected location.""",
        14: """DDI_CABLE_DISCONNECTED
        Camera electronics unit cable is not connected.""",
        15: """DDI_MEM_ALLOC_FAILED
        Device driver could not allocate needed memory.""",
        16: """DDI_IRQID_CONFLICT
        2 open cameras are using the same interrupt ID.""",
        17: """DDI_DRV_CLOS_CLOSE_CAM
        Driver not yet opened: pd_cam_close.""",
        18: """DDI_DRV_CLOS_READ_BYTE
        Driver not yet opened: pd_cam_write_read, read.""",
        19: """DDI_DRV_CLOS_SEND_BYTE
        Driver not yet opened: pd_cam_write_read, write.""",
        20: """DDI_DRV_CLOS_GET_RETRY
        Driver not yet opened: pd_driver_get_retries.""",
        21: """DDI_DRV_CLOS_SET_RETRY
        Driver not yet opened: pd_driver_set_retries.""",
        22: """DDI_DRV_CLOS_GET_TIME
        Driver not yet opened: pd_driver_get_timeout.""",
        23: """DDI_DRV_CLOS_SET_TIME
        Driver not yet opened: pd_driver_set_timeout.""",
        24: """DDI_DRV_CLOS_INFO_LEN
        Driver not yet opened: pd_driver_get_info_length.""",
        25: """DDI_DRV_CLOS_INFO_DUMP
        Driver not yet opened: pd_driver_get_info_dump.""",
        26: """DDI_DRV_CLOS_DRV_VER
        Driver not yet opened: pd_driver_get_ver.""",
        27: """DDI_DRV_CLOS_IM_STATUS
        Driver not open: pd_driver_get_image_data_status.""",
        28: """DDI_DRV_CLOS_IM_ABORT
        Driver not open: pd_driver_set_image_data_idle.""",
        29: """DDI_DRV_CLOS_IM_ACTIVE
        Driver not open: pd_driver_set_image_data_active.""",
        30: """DDI_DRV_CLOS_IM_GRAN
        Driver not open: pd_driver_get_image_data_gran.""",
        31: """DDI_BAD_DEVH_CLOSE_CAM
        Illegal device handle: pd_cam_close.""",
        32: """DDI_BAD_DEVH_READ_BYTE
        Illegal device handle: pd_cam_write_read, read.""",
        33: """DDI_BAD_DEVH_SEND_BYTE
        Illegal device handle: pd_cam_write_read, write.""",
        34: """DDI_BAD_DEVH_GET_RETRY
        Illegal device handle: pd_driver_get_retries.""",
        35: """DDI_BAD_DEVH_SET_RETRY
        Illegal device handle: pd_driver_set_retries.""",
        36: """DDI_BAD_DEVH_GET_TIME
        Illegal device handle: pd_driver_get_timeout.""",
        37: """DDI_BAD_DEVH_SET_TIME
        Illegal device handle: pd_driver_set_timeout.""",
        38: """DDI_BAD_DEVH_INFO_LEN
        Illegal device handle: pd_driver_get_info_length.""",
        39: """DDI_BAD_DEVH_INFO_DUMP
        Illegal device handle: pd_driver_get_info_dump.""",
        40: """DDI_BAD_DEVH_DRV_VER
        Illegal device handle: pd_driver_get_ver.""",
        41: """DDI_BAD_DEVH_IM_STATUS
        Bad dev handle: pd_driver_get_image_data_status.""",
        42: """DDI_BAD_DEVH_IM_ABORT
        Bad dev handle: pd_driver_set_image_data_idle.""",
        43: """DDI_BAD_DEVH_IM_ACTIVE
        Bad dev handle: pd_driver_set_image_data_active.""",
        44: """DDI_BAD_DEVH_IM_GRAN
        Bad dev handle: pd_driver_get_image_data_gran.""",
        45: """DDI_SYS_ERR_DEV_DRIVER
        System error while accessing the device driver.""",
        46: """DDI_SYS_ERR_INIT
        System error in pd_ddi_init.""",
        47: """DDI_SYS_ERR_UNINIT
        System error in pd_ddi_uninit.""",
        48: """DDI_SYS_ERR_TOTL_CAMS
        System error in pd_ddi_get_total_cams.""",
        49: """DDI_SYS_ERR_CAM_NAME
        System error in pd_ddi_get_all_cam_names.""",
        50: """DDI_SYS_ERR_OPEN_CAM
        System error in pd_cam_open.""",
        51: """DDI_SYS_ERR_CLOSE_CAM
        System error in pd_cam_close.""",
        52: """DDI_SYS_ERR_READ_BYTE
        System error in pd_cam_write_read, read.""",
        53: """DDI_SYS_ERR_SEND_BYTE
        System error in pd_cam_write_read, write.""",
        54: """DDI_SYS_ERR_GET_RETRY
        System error in pd_driver_get_retries.""",
        55: """DDI_SYS_ERR_SET_RETRY
        System error in pd_driver_set_retries.""",
        56: """DDI_SYS_ERR_GET_TIME
        System error in pd_driver_get_timeout.""",
        57: """DDI_SYS_ERR_SET_TIME
        System error in pd_driver_set_timeout.""",
        58: """DDI_SYS_ERR_INFO_LEN
        System error in pd_driver_get_info_length.""",
        59: """DDI_SYS_ERR_INFO_DUMP
        System error in pd_driver_get_info_dump.""",
        60: """DDI_SYS_ERR_DRV_VER
        System error in pd_driver_get_ver.""",
        61: """DDI_SYS_ERR_IM_STATUS
        System error in pd_driver_get_image_data_status.""",
        62: """DDI_SYS_ERR_IM_ABORT
        System error in pd_driver_set_image_data_idle.""",
        63: """DDI_SYS_ERR_IM_ACTIVE
        System error in pd_driver_set_image_data_active.""",
        64: """DDI_SYS_ERR_IM_GRAN
        System error in pd_driver_get_image_data_gran.""",
        65: """DDI_UNKNOWN_DEV_DRIVER
        Unknown error while accessing the device driver.""",
        66: """DDI_UNKNOWN_INIT
        Unknown error in pd_ddi_init.""",
        67: """DDI_UNKNOWN_UNINIT
        Unknown error in pd_ddi_uninit.""",
        68: """DDI_UNKNOWN_TOTL_CAMS
        Unknown error in pd_ddi_get_total_cams.""",
        69: """DDI_UNKNOWN_CAM_NAME
        Unknown error in pd_ddi_get_all_cam_names.""",
        70: """DDI_UNKNOWN_OPEN_CAM
        Unknown error in pd_cam_open.""",
        71: """DDI_UNKNOWN_CLOSE_CAM
        Unknown error in pd_cam_close.""",
        72: """DDI_UNKNOWN_READ_BYTE
        Unknown error in pd_cam_write_read, read.""",
        73: """DDI_UNKNOWN_SEND_BYTE
        Unknown error in pd_cam_write_read, write.""",
        74: """DDI_UNKNOWN_GET_RETRY
        Unknown error in pd_driver_get_retries.""",
        75: """DDI_UNKNOWN_SET_RETRY
        Unknown error in pd_driver_set_retries.""",
        76: """DDI_UNKNOWN_GET_TIME
        Unknown error in pd_driver_get_timeout.""",
        77: """DDI_UNKNOWN_SET_TIME
        Unknown error in pd_driver_set_timeout.""",
        78: """DDI_UNKNOWN_INFO_LEN
        Unknown error in pd_driver_get_info_length.""",
        79: """DDI_UNKNOWN_INFO_DUMP
        Unknown error in pd_driver_get_info_dump.""",
        80: """DDI_UNKNOWN_DRV_VER
        Unknown error in pd_driver_get_ver.""",
        81: """DDI_UNKNOWN_IM_STATUS
        Unknown error in pd_driver_get_image_data_status.""",
        82: """DDI_UNKNOWN_IM_ABORT
        Unknown error in pd_driver_set_image_data_idle.""",
        83: """DDI_UNKNOWN_IM_ACTIVE
        Unknown error in pd_driver_set_image_data_active.""",
        84: """DDI_UNKNOWN_IM_GRAN
        Unknown error in pd_driver_get_image_data_gran.""",
        85: """DDI_SCSI_NOT_PV_CAMERA
        This SCSI device is not a Tucson camera.""",
        86: """DDI_SCSI_NO_PROTOCOL
        SCSI protocol breakdown: no device or termination.""",
        87: """DDI_SCSI_NO_ARBITRATE
        SCSI arbitration failure: the bus is busy.""",
        88: """DDI_SCSI_BAD_XFER
        SCSI bad instruction in transfer instruction bloc.""",
        89: """DDI_SCSI_PHASE_ERROR
        SCSI phase error: host & camera disagree on type.""",
        90: """DDI_SCSI_DATA_ERROR
        SCSI data comparison error verifying transfer.""",
        91: """DDI_SCSI_MGR_BUSY
        SCSI manager is busy with another operation.""",
        92: """DDI_SCSI_SEQUENCE_ERR
        SCSI sequencing error.""",
        93: """DDI_SCSI_BUS_TIMEOUT
        SCSI bus timeout waiting for data transfer.""",
        94: """DDI_SCSI_COMPLETE_ERR
        SCSI completion error.""",
        95: """DDI_SCSI_INTERNAL_ERR
        SCSI device indicates an internal error.""",
        96: """DDI_XM_SNDOK
        XMODEM.""",
        97: """DDI_XM_NOSOH
        XMODEM.""",
        98: """DDI_XM_OVERFLOW
        XMODEM.""",
        99: """DDI_XM_RCVOK
        XMODEM.""",
        100: """DDI_XM_RCVCAN
        XMODEM.""",
        101: """DDI_XM_NOACK
        XMODEM no ACKnowledge signal received.""",
        102: """DDI_XM_LASTACK
        XMODEM.""",
        103: """DDI_XM_SNDACK
        XMODEM.""",
        104: """DDI_XM_SNDCAN
        XMODEM.""",
        105: """DDI_XM_MSGEND
        XMODEM.""",
        106: """DDI_XM_BADCKV
        XMODEM.""",
        107: """DDI_XM_BADSOH
        XMODEM.""",
        108: """DDI_XM_NODATA
        XMODEM.""",
        109: """DDI_XM_BADPAK
        XMODEM.""",
        110: """DDI_XM_PAKNUM
        XMODEM.""",
        111: """DDI_XM_PAKSEQ
        XMODEM.""",
        112: """DDI_XM_NOSYNC
        XMODEM no SYNC character seen.""",
        113: """DDI_XM_SYNCTOUT
        XMODEM timout while waiting for SYNC character.""",
        114: """DDI_XM_XMITLOCK
        XMODEM transmit ... ?.""",
        115: """DDI_XM_BADCMD
        XMODEM bad command.""",
        116: """C0_INVALID_HANDLE
        This is not the handle of an open camera.""",
        117: """C0_CAM_ALREADY_OPEN
        This user has already opened this camera.""",
        118: """C0_CAM_NEVER_OPENED
        Camera was not opened, so this task can't be done.""",
        119: """C0_CAM_RESERVED
        The camera is in use by another user.""",
        120: """C0_DRIVER_OUT_OF_MEM
        Driver or DDI ran out of (specialized?) memory.""",
        121: """C0_CANT_READ_TIMEOUT
        System couldn't read the timeout for this driver.""",
        122: """C0_CANT_WRIT_TIMEOUT
        System couldn't set the timeout for this driver.""",
        123: """C0_CANT_READ_RETRIES
        System couldn't read the retries for this driver.""",
        124: """C0_CANT_WRIT_RETRIES
        System couldn't set the retries for this driver.""",
        125: """C0_CAM_TIMEOUT
        No response at all from the camera.""",
        126: """C0_CAM_TIMEOUT_NOISE
        Timeout, but some response (noisy line?).""",
        127: """C0_RETRIES_EXCEEDED
        Not a timeout, but retries didn't work (noisy?).""",
        128: """C0_CAM_NAME_OUT_OF_RNG
        The number must be in the range 1 <= num <= totl_cams.""",
        129: """C0_CAM_NAME_NOT_FOUND
        This is not a valid name for opening the camera.""",
        130: """C0_PACKET_TOO_LARGE
        A send or read request used a packet >32768 bytes.""",
        131: """C0_STATUS_TOO_LARGE
        The status info returned contained too many bytes.""",
        132: """C0_STATUS_TOO_SMALL
        The status info returned contained too few  bytes.""",
        133: """C0_NEED_POSITIVE_VAL
        The input value must be greater than zero.""",
        134: """C0_NEED_ZERO_OR_MORE
        The input value must be zero or above.""",
        135: """C0_NULL_POINTER
        Input pointer is null, it must be a legal address.""",
        136: """C0_STSF_EU_CPU
        Subsystem fault: electronics unit main CPU.""",
        137: """C0_STSF_EU_SYS_INTEG
        Subsystem fault: EU internal communications.""",
        138: """C0_STSF_EU_TO_HOST
        Subsystem fault: EU-to-host cables.""",
        139: """C0_STSF_POWER_SUPPLY
        Subsystem fault: power supply voltage error.""",
        140: """C0_STSF_CCS_CHIP
        Subsystem fault: CCS chip or memory.""",
        141: """C0_STSF_CCS_SCRIPT_MEM
        Subsystem fault: CCS script memory.""",
        142: """C0_STSF_CCS_PORTS
        Subsystem fault: CCS ports.""",
        143: """C0_STSF_DISPLAY
        Subsystem fault: EU front panel display.""",
        144: """C0_STSF_SHUTTER_DRIVE
        Subsystem fault: shutter driver circuit.""",
        145: """C0_STSF_TEMP_CONT
        Subsystem fault: temperature control circuit.""",
        146: """C0_STSF_PAR_CLOCK_DRV
        Subsystem fault: parallel clock driver.""",
        147: """C0_STSF_CH_CABLES
        Subsystem fault: camera head cables.""",
        148: """C0_STSF_CH_CPU
        Subsystem fault: camera head CPU board.""",
        149: """C0_STSF_CH_CLOCK_BRD
        Subsystem fault: camera head clock board.""",
        150: """C0_STSF_CH_POWER_BRD
        Subsystem fault: camera head power board.""",
        151: """C0_STSF_CH_VID_BRD_1
        Subsystem fault: camera head video board #1.""",
        152: """C0_STSF_CH_VID_BRD_2
        Subsystem fault: camera head video board #2.""",
        153: """C0_STSF_CH_VID_BRD_3
        Subsystem fault: camera head video board #3.""",
        154: """C0_STSF_CH_VID_BRD_4
        Subsystem fault: camera head video board #4.""",
        155: """C0_STSF_ADC_BOARD_1
        Subsystem fault: A/D board #1.""",
        156: """C0_STSF_ADC_BOARD_2
        Subsystem fault: A/D board #2.""",
        157: """C0_STSF_ADC_BOARD_3
        Subsystem fault: A/D board #3.""",
        158: """C0_STSF_ADC_BOARD_4
        Subsystem fault: A/D board #4.""",
        159: """C0_STSF_OPTION_CARD_1
        Subsystem fault: option card #1.""",
        160: """C0_STSF_OPTION_CARD_2
        Subsystem fault: option card #2.""",
        161: """C0_STSF_OPTION_CARD_3
        Subsystem fault: option card #3.""",
        162: """C0_STSF_OPTION_CARD_4
        Subsystem fault: option card #4.""",
        163: """C0_NO_IMG_DATA
        Can't collect data: expected data is zero bytes.""",
        164: """C0_CCL_SCRIPT_INVALID
        Can't collect data: CCS script is invalid.""",
        165: """C0_EXP_FIFO_OVERFLOW
        AIA input buffer has overflowed.""",
        166: """C0_EXP_NO_ACK
        Camera didn't acknowledge request for image data.""",
        167: """C0_EXP_XFER_ERR
        Last data transfer from the camera was garbled.""",
        168: """C0_EXP_EXTRA_DATA
        Finished data transfer, but extra data exists.""",
        169: """C0_EXP_MISSING_DATA
        Finished data transfer, some data was missing.""",
        170: """C0_OPEN_MODE_UNAVAIL
        Camera may not be opened in the mode specified.""",
        171: """C0_WRONG_READ_CLASS
        Read operations require the HOST_COMMANDS class.""",
        172: """C0_WRITE_BYTES_TOO_SML
        Command sent to camera must be at least 1 byte.""",
        173: """C0_WRITE_BYTES_TOO_LRG
        Cannot send over 32768 bytes in one transaction.""",
        174: """C0_READ_BYTES_TOO_SML
        A read transaction must transfer at least 1 byte.""",
        175: """C0_READ_BYTES_TOO_LRG
        Cannot read over 32768 bytes in one transaction.""",
        176: """C0_WRONG_READ_CMD
        'read' command is improperly formatted.""",
        177: """DDI_DRV_CLOS_GET_PIXTIME
        Driver not yet opened: pd_driver_get_pixtime.""",
        178: """DDI_SYS_ERR_GET_PIXTIME
        System error in pd_driver_get_pixtime.""",
        179: """DDI_BAD_DEVH_GET_PIXTIME
        Bad dev handle: pd_driver_get_pixtime.""",
        180: """DDI_UNKNOWN_GET_PIXTIME
        Unknown error in pd_driver_get_pixtime.""",
        181: """DDI_CAM_XOFF
        Camera can't communicate after sending an X-OFF.""",
        182: """C0_BAD_CONTROLLER
        Controller for camera not valid.""",
        183: """C0_CNTRL_CREATE_FAILED
        Could not create controller object for camera.""",
        184: """C0_NO_CONT_STATUS
        Status not available for continuous exposure.""",
        185: """C0_STAT_CNTRL_ERROR
        Controller error while requesting status.""",
        186: """C0_STAT_CMD_ERROR
        Command error while requesting status.""",
        187: """C0_STAT_DMA_OVERRUN
        DMA data overrun has occurred.""",
        188: """C0_STAT_TAXI_VIOLATION
        Violation in TAXI communication protocol occurred.""",
        189: """C0_STAT_MAILBOX_ERROR
        Mailbox error while requesting status.""",
        190: """C0_STAT_CH0_ERROR
        Channel 0 transfer not enabled.""",
        191: """C0_STAT_CH1_ERROR
        Channel 1 transfer not enabled.""",
        192: """C0_CANT_READ_ID
        System couldn't read the subsystem part numbers.""",
        193: """C0_CANT_READ_NAME
        System couldn't read the name for this subsystem.""",
        194: """C0_DEV_HANDLE_UNAVAIL
        Camera device handle unavailable.""",
        195: """C0_PVCAM_NOT_INITED
        Camera library not initialized.""",
        1000: """C01_START_ERROR
        unknown error.""",
        2000: """C2_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        2001: """C2_PVCAM_ALREADY_INITED
        Init_pvcam has been called twice without closing.""",
        2002: """C2_PVCAM_NOT_INITED
        The PVCAM library was never initialized.""",
        2003: """C2_FAILED_TO_SET_VALUE
        The camera did not accept the new setting.""",
        2004: """C2_NEED_POSITIVE_VAL
        The input value must be greater than zero.""",
        2005: """C2_NEED_ZERO_OR_MORE
        The input value must be zero or above.""",
        2006: """C2_NULL_POINTER
        Input pointer is null, it must be a legal address.""",
        2007: """C2_FRAME_XFER_ILLEGAL
        This CCD does not allow frame transfer operation.""",
        2008: """C2_FRAME_XFER_REQUIRED
        This CCD must be operated in frame transfer mode.""",
        2009: """C2_MPP_MODE_ILLEGAL
        This CCD does not allow mpp-mode clocking.""",
        2010: """C2_MPP_MODE_REQUIRED
        This CCD requires mpp-mode clocking.""",
        2011: """C2_CLEAR_MODE_INVALID
        Requested clear mode is not an allowed choice.""",
        2012: """C2_SPEED_INVALID
        No valid speeds between camera/electronics/host.""",
        2013: """C2_SPEED_OUT_OF_RANGE
        Selected a non-existant speed table entry.""",
        2014: """C2_CANT_SET_ADC_OFFSET
        Camera does not allow offset to be read or set.""",
        2015: """C2_BAD_CONTROLLER
        Controller for camera not valid.""",
        2016: """C2_NOT_AVAILABLE
        Parameter is not available for camera.""",
        2017: """C2_FAILED_TO_GET_VALUE
        The camera did not return the setting.""",
        2018: """C2_PARAMETER_INVALID
        The requested parameter is invalid.""",
        2019: """C2_ATTRIBUTE_INVALID
        The requested attribute is invalid.""",
        2020: """C2_INDEX_OUT_OF_RANGE
        The requested parameter index is out of range.""",
        2021: """C2_NOT_INPUT
        The requested I/O port is not an input port.""",
        2022: """C2_IO_TYPE_INVALID
        The requested I/O port type is not supported.""",
        2023: """C2_ADDR_OUT_OF_RANGE
        The I/O address is out of range.""",
        2024: """C2_ACCESS_ATTR_INVALID
        The I/O port returned access attribute is invalid.""",
        2025: """C2_CANT_SET_PARAMETER
        The requested parameter cannot be set.""",
        2026: """C2_IO_DIRECTION_INVALID
        The returned direction for the I/O port is invalid.""",
        2027: """C2_NO_ALPHA_SER_NUM
        Alphanumeric serial # unavailable for this camera.""",
        2028: """C2_CANT_OVERSCAN
        Camera does not allow overscanning the CCD.""",
        2029: """C2_CANT_SET_GAIN_MULT
        Camera does not allow setting the gain multiplier.""",
        3000: """C3_INVALID_PIC_TRIGGER_MODE.""",
        3001: """C3_NO_COMMUNICATIONS_LINK
        Bogus temp.""",
        3002: """C3_INVALID_SCRIPT
        CCL program is not loaded or is invalid..""",
        3003: """C3_EXP_EXTRA_DATA
        Extra data acquired during exposure.""",
        3004: """C3_EXP_NO_DATA_ACQ
        No data acquired during exposure.""",
        3005: """C3_EXP_FIFO_OVERFLOW
        FIFO overflow during exposure.""",
        3006: """C3_EXP_NO_ACKNOWLEDGE
        Camera did not acknowledge request during exp.""",
        3007: """C3_EXP_TRANSFER_ERROR
        Transfer error during exposure.""",
        3008: """C3_EXP_UNKNOWN_STATE
        Camera went into unknown state during exp.""",
        3009: """C3_CANT_DECODE_IN_PROGRESS
        Can't decode while readout is in progress.""",
        3010: """C3_RGN_MAX_EXCEEDED
        Trying to exceed the maximum # of regions.""",
        3011: """C3_RGN_ILLEGAL_DEFN
        Dimensions of region to be added is illegal.""",
        3012: """C3_RGN_ILLEGAL_BINNING
        Binning of region to be added is illegal.""",
        3013: """C3_RGN_OUTSIDE_CCD_DIMENS
        Region def extends beyond CCD dimensions.""",
        3014: """C3_RGN_OVERLAP
        Region to be added overlaps a previous region.""",
        3015: """C3_RGN_INVALID_NUM
        Invalid region number.""",
        3016: """C3_RGN_NOT_FOUND
        Region not found.""",
        3017: """C3_STREAM_PTR_NOT_DEFINED
        Pointer to pixel stream is not defined.""",
        3018: """C3_GROUPS_PTR_NOT_DEFINED
        Pointer to decode info structure undefined.""",
        3019: """C3_NOT_INITIALIZED
        pl_init_exp_seq() has not been called.""",
        3020: """C3_FAILED_TO_SET_VALUE
        The value can not be set in the camera.""",
        3021: """C3_EVENT_NUMBER_INVALID
        Frame count for generating event <= 0.""",
        3022: """C3_EVENT_NOT_SUPPORTED
        Specified event is not supported by the O.S..""",
        3023: """C3_BAD_CONTROLLER
        Controller for camera not valid.""",
        3024: """C3_EVENT_NOT_SET
        Event was not set up.""",
        3025: """C3_CNTRL_INIT_FAILED
        Controller initialization failed.""",
        3026: """C3_EXP_MODE_NOT_SUPPORTED
        Exposure mode not supported by this camera.""",
        3027: """C3_ILLEGAL_BUFFER_SIZE
        Buffer must be integer-multiple of frame size.""",
        3028: """C3_GET_FRAME_NOT_SUPPORTED
        Camera cannot return the specified frame.""",
        3029: """C3_FRAME_NOT_RETURNED
        Specified frame could not be returned.""",
        3030: """C3_FRAME_BAD_MODE
        Frame could not be returned in current mode.""",
        3031: """C3_NO_DRIVER_BUFFER
        Camera does not provide a driver buffer.""",
        3032: """C3_BUF_NOT_RETURNED
        Pointer to buffer could not be returned.""",
        3033: """C3_BUFFER_OVERRUN
        Data Buffer is full no place to xfer data.""",
        3034: """C3_TAXI_VIOLATION
        Communication with device failed, link broken.""",
        3035: """C3_EXP_RES_OUT_OF_RANGE
        Exposure resolution index non-existent.""",
        3036: """C3_NOT_AVAILABLE
        Parameter is not available for camera.""",
        3037: """C3_IO_PORT_INVALID
        Specified I/O port is invalid.""",
        3038: """C3_FAILED_TO_GET_VALUE
        The camera did not return the setting.""",
        3039: """C3_IO_STATE_OUT_OF_RANGE
        Requested I/O state out of range for port.""",
        3040: """C3_IO_LOCATION_INVALID
        Specified script location is invalid.""",
        3041: """C3_IO_NOT_OUTPUT
        Specified I/O port is not an output port.""",
        3042: """C3_EXP_XFER_ERR
        Last data transfer from the camera was garbled.""",
        3043: """C3_EXP_MISSING_DATA
        Finished data transfer, some data was missing.""",
        3044: """C3_STAT_CNTRL_ERROR
        Controller error while requesting status.""",
        3045: """C3_STAT_CMD_ERROR
        Command error while requesting status.""",
        3046: """C3_CAM_NEVER_OPENED
        Camera was not opened, so this task can't be done.""",
        3047: """C3_STAT_DMA_OVERRUN
        DMA data overrun has occurred.""",
        3048: """C3_STAT_TAXI_VIOLATION
        Violation in TAXI communication protocol occurred.""",
        3049: """C3_STAT_MAILBOX_ERROR
        Mailbox error while requesting status.""",
        3050: """C3_STAT_CH0_ERROR
        Channel 0 transfer not enabled.""",
        3051: """C3_STAT_CH1_ERROR
        Channel 1 transfer not enabled.""",
        3052: """C3_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        4000: """C04_HBUF_OUTOFRANGE.""",
        4001: """C04_HIMG_OUTOFRANGE.""",
        4002: """C04_NO_FREE_BUFFER_HANDLES.""",
        4003: """C04_NO_FREE_IMAGE_HANDLES.""",
        4004: """C04_BUFFER_ENTRY_ALREADY_SET.""",
        4005: """C04_BUFFER_ENTRY_ALREADY_CLEARED.""",
        4006: """C04_IMAGE_ENTRY_ALREADY_SET.""",
        4007: """C04_IMAGE_ENTRY_ALREADY_CLEARED.""",
        4008: """C04_INVALID_IMAGE_HANDLE.""",
        4009: """C04_INVALID_BUFFER_HANDLE.""",
        4010: """C04_INVALID_BITDEPTH_VALUE
        Bit depth must be enum PRECISION_....""",
        4011: """C04_INVALID_IMAGE_NUMBER.""",
        4012: """C04_INVALID_EXPOSURE_NUMBER.""",
        4013: """C04_INVALID_TIME
        The time or date is out of range.""",
        4014: """C04_INVALID_REGION
        A region is out of range.""",
        14000: """C14_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        14001: """C14_CANT_READ_INI_FILE
        Unable to read the current INI file. Please run RSConfig.exe.""",
        29000: """C29_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        29001: """C29_BDEPTH_ILLEGAL
        Bit depth must be enum PRECISION_....""",
        29002: """C29_BDEPTH_DIFFER
        Bit depth source much match destination.""",
        29003: """C29_BUF_NEEDS_1_EXP
        A buffer needs at least 1 exposure.""",
        29004: """C29_BUF_NEEDS_1_IMG
        A buffer needs at least 1 image.""",
        29005: """C29_IMG_DEF_TOO_LARGE
        Image definition used too large a value.""",
        29006: """C29_IMG_DEF_TOO_SMALL
        Image size/bin must be larger than zero.""",
        29007: """C29_IMG_DEF_DIFFER
        Image source definition must match dest.""",
        29008: """C29_IMG_NUM_DIFFER
        Source # of images must match dest.""",
        30000: """C30_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        30001: """C30_CANT_READ_TIME
        Unable to read the current system time.""",
        30000: """C30_UNKNOWN_ERROR
        Unexpected, unanticipated, undocumented.""",
        30001: """C30_CANT_READ_TIME
        Unable to read the current system time.""",
        31000: """C31_INVALID_HEAP
        Invalid heap ID: PUBLIC_MEM, PRIVATE_MEM.""",
        31001: """C31_MEMALLOC_FAILED
        Not enough memory to perform alloc.""",
        31002: """C31_MEMCALLOC_FAILED
        Not enough memory to perform calloc.""",
        31003: """C31_MEMREALLOC_FAILED
        Not enough memory to perform realloc.""",
        31004: """C31_PRIV_MEM_BLOCK_TOO_BIG
        Excceeds 64k limit for PRIVATE_MEM.""",
        31005: """C31_MEMLOCK_FAILED
        Memory page locking failed.""",
        32000: """CCL_TOO_COMPLEX
        Too many script entries..""",
        32001: """CCL_CANT_FRAME_TRANSFER
        No frame transfer hardware support..""",
        32002: """CCL_SCRIPT_IS_NOT_VALID
        .""",
        32003: """CCL_REGIONS_OVERLAP
        Regions contain some of the same pixels.""",
        32004: """CCL_INVALID_SERIAL_BINNING
        Serial binning == 0 or > region size.""",
        32005: """CCL_INVALID_PARALLEL_BINNING
        Parallel binning == 0 or > region size.""",
        32006: """CCL_NONMATCHED_PARALLEL_BINNING
        Conflicting parallel binning values.""",
        32007: """CCL_PARALLEL_BINNING_MISALIGNED
        Conflicting parallel binning alignment.""",
        32008: """CCL_INVALID_REGION
        Region is not on the CCD.""",
        32009: """CCL_INVALID_IO_PORT_TYPE
        Requested I/O port is not a valid type.""",
        32010: """C32_NOT_INITIALIZED
        The pg_decode_info structure is not initialized."""}
        
def PrincetonEnumCamera():
    some_int = int16()
    res = API.pl_pvcam_init()
    if res == 0:
        errorcode = API.pl_error_code()
        if not errorcode == 2001:
            raise PrincetonError(errorcode)
    if API.pl_cam_get_total(ct.byref(some_int)) == 0:
        raise PrincetonError(API.pl_error_code())
    return some_int.value
        
def PrincetonForceClose(number):
    res = API.pl_pvcam_init()
    if res == 0:
        errorcode = API.pl_error_code()
        if not errorcode == 2001:
            raise PrincetonError(errorcode)
    handle = int16(number)
    if API.pl_cam_close(handle) == 0:
        raise PrincetonError(API.pl_error_code())
        
