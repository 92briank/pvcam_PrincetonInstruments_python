# -*- coding: utf-8 -*-
"""
Class for user frendly use of a Princeton Instruments camera with PVCAM

Uses Princeton class from https://github.com/ColinBrosseau/pvcam_PrincetonInstruments_python

:Author:
  Colin-N. Brosseau

:Organization:
  Laboratoire Richard Leonelli, Universite de Montreal, Quebec

:Version: 2017.09

"""
from Princeton_wrapper import Princeton
from master_Header_wrapper import *
import matplotlib.pyplot as plt
import numpy as np
import yaml


class Easy_pvcam(Princeton):
    def __init__(self, number=0):
        super(Easy_pvcam, self).__init__()
        chip_name = self.getParameterCurrentValue('CHIP_NAME').decode('UTF-8').replace(' ','')

        # import cameras configuration        
        with open("config.yaml", 'r') as ymlfile:
            camera_cfg = yaml.load(ymlfile)
            
        # Set camera parameters
        # Temperature (celcius)
        self.setpoint_temperature = camera_cfg[chip_name]['setpoint_temperature']
        # ADC speed index
        self.speed = camera_cfg[chip_name]['speed']
        # ADC gain
        self.gain = camera_cfg[chip_name]['gain']  
        # Exposure time in second
        self.exposureTime = camera_cfg[chip_name]['exposureTime']  
        
        #By default, camera is in full frame mode, set it to spectroscopy mode
        #set camera to 1D (vertical binning) acquisition
        self.setSpectroscopy()

        # Mecanical Shutter
        if 'shutter' in cfg[chip_name]:
            self._initShutter()  # initialise Logic Output to drive the shutter
            # Delay (second) for setting of a mecanical shutter
            self.delayShutter = cfg[chip_name]['shutter']['delay']
            # This enum is perticular to our setup. You migth have to reverse it.
            # We connect the shutter to the Logic Output
            self._ShutterMode = {'closed':ShutterOpenMode.never, 'opened':ShutterOpenMode.presequence}
            # This is the reversed setup
            #PixisShutterMode = {'closed':ShutterOpenMode.presequence, 'opened':ShutterOpenMode.never}
            #reverse of the Shutter Mode (for reading)
            self._reverseShutterMode = {v.name:k for k, v in self._ShutterMode.items()}

    def setImage(self):
        self._ROI = []
        self.addExposureROI(self._ROIfull)

    def setSpectroscopy(self):
        self._ROI = []
        self.addExposureROI(self._ROIspectroscopy)

#   Typical measurement
    def measure(self, exposureTime=False, removeBackgound=False):
        if exposureTime:
            self.exposureTime = exposureTime
        if removeBackgound:
            self.shutter = 'closed'
            background = np.squeeze(self.takePicture())
            self.shutter = 'opened'
            spectrum = np.squeeze(self.takePicture())
            spectrum[0] = np.squeeze(spectrum[0] - background[0])
        else:
            spectrum = np.squeeze(self.takePicture())
            spectrum[0] = np.squeeze(spectrum[0])
        return spectrum
       
    # Exposure time is in second. These functions replace the ones from super as there is no unit involved.
    def _getExposureTime(self):
        """Get the exposure time in units given by EXP_RES."""
        PropertyFastExposureResolutionConstant = {0:1e-3,
            1:1e-6}
        factor = PropertyFastExposureResolutionConstant.get(self.getParameterCurrentValue('EXP_RES_INDEX'))
        expTime = self.getParameterCurrentValue('EXP_TIME')
        return expTime * factor
        
    def _setExposureTime(self, exposureTime):
        """Set the exposure time.
        
        Parameters
        ----------
        exposureTime : exposure time in seconds 
                        unsigned int (0 - 65535)
        """
        if exposureTime < 0.065535:  #short exposure, microsecond resolution
            exposureUnits = ExposureUnits.microsecond
            self.expTime = int(exposureTime * 1e6)
        else:  #long exposure, millisecond resolution
            exposureUnits = ExposureUnits.millisecond
            self.expTime = int(exposureTime * 1e3)
                        
        self.setParameterValue('EXP_RES_INDEX', exposureUnits.value)
        self.setParameterValue('EXP_TIME', self.expTime)

    exposureTime = property(_getExposureTime, _setExposureTime)      
       
    def close(self):
           self.closeCamera()
           
    def _initShutter(self):
        self.logicOutput = LogicOutput.SHUTTER
        
    def _getShutter(self):
        return self._reverseShutterMode[self.shutterOpenMode.name]

    def _setShutter(self, value):
        exposureTime = self.exposureTime  # Save exposure time
        self.shutterOpenMode = self._ShutterMode[value]
        # The shutter needs to have an exposure to apply.
        self.measure(self.delayShutter)  # the delay also let time to shutter to set  
        self.exposureTime = exposureTime  # Restore exposure time
    
    shutter = property(_getShutter, _setShutter)

if __name__ == '__main__':
     camera = Easy_pvcam()
     print("ROI:")
     print(camera.ROI)
     print("Actual temperature (C):")
     print(camera.temperature)
     print("Setpoint temperature (C):")
     print(camera.setpoint_temperature)
     print("Gain index:")
     print(camera.gain)
     print("ADC speed index:")
     print(camera.speed)
     print("Camera Size:")
     print(camera.getCameraSize())
     print("Exposure time (second):")
     print(camera.exposureTime)
     print("Simple measurement")
     a = camera.measure(2)  # exposure time = 2 seconds
     plt.plot(a[0])
     print("Exposure parameters:")
     print(a[1])
     print("Simple measurement with backgound removal")
     a = camera.measure(2)  # exposure time = 2 seconds
     plt.plot(a[0])
     camera.close()
     
