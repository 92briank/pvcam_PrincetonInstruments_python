# -*- coding: utf-8 -*-
"""
Class to use a Pixis 256 camera thru Pvcam32.dll

Uses Princeton class from https://github.com/ColinBrosseau/PythonPrincetonCamera

:Author:
  Colin-N. Brosseau

:Organization:
  Laboratoire Richard Leonelli, Universite de Montreal, Quebec

:Version: 2015.12.16

"""
from Princeton_wrapper import Princeton
from master_Header_wrapper import *
import matplotlib.pyplot as plt


class Pixis(Princeton):
    def __init__(self, number=0):
        #   Mecanical Shutter
        self._initShutter()  # initialise Logic Output to drive the shutter
        # Delay (second) for setting of a mecanical shutter
        self.delayShutter = 0.1  # second
        # This enum is perticular to our setup. You migth have to reverse it.
        # We connect the shutter to the Logic Output
        self._PixisShutterMode = {'closed':ShutterOpenMode.never, 'opened':ShutterOpenMode.presequence}
        # This is the reversed setup
        #PixisShutterMode = {'closed':ShutterOpenMode.presequence, 'opened':ShutterOpenMode.never}
        #reverse of the Shutter Mode (for reading)
        self._reversePixisShutterMode = {v.name:k for k, v in PixisShutterMode.items()}

        super(Pixis, self).__init__()
        self.setpoint_temperature = -70  #set temperature (celcius)
        self.speed = 0  #set ADC speed index
        
        #By default, camera is in full frame mode, set it to spectroscopy mode
        #set camera to 1D (vertical binning) acquisition
        self.setSpectroscopy()

        self.gain = 1  #set ADC gain
        self.exposureTime = 1  # exposure time in second

    def setImage(self):
        self._ROI = []
        self.addExposureROI(self._ROIfull)

    def setSpectroscopy(self):
        self._ROI = []
        self.addExposureROI(self._ROIspectroscopy)

    def measure(self, exposureTime=False):
        if exposureTime:
            self.exposureTime = exposureTime
        spectrum = self.takePicture()
        plt.plot(spectrum[0][0][0][0])
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
        return self._reversePixisShutterMode[self.shutterOpenMode.name]

    def _setShutter(self, value):
        exposureTime = self.exposureTime  # Save exposure time
        self.shutterOpenMode = self._PixisShutterMode[value]
        # The shutter needs to have an exposure to apply.
        self.measure(self.delayShutter)  # the delay also let time to shutter to set  
        self.exposureTime = exposureTime  # Restore exposure time
    
    shutter = property(_getShutter, _setShutter)

if __name__ == '__main__':
     camera = Pixis()
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
     plt.plot(a[0][0][0][0])
     print("Exposure parameters:")
     print(a[1][0][0])
     camera.close()
     
