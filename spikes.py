# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 16:44:05 2015

:Author:
  Colin-N. Brosseau

:Organization:
  Laboratoire Richard Leonelli, Universite de Montreal, Quebec

:Version: 
  2017.09
"""
from lmfit.models import LinearModel
import numpy as np
from copy import deepcopy

def removeSpike1D(y, threshold=3, kernelSize=5):
    """
    Find spikes in a 1D array
    Used for independent values (ex. a spectrum)
    """
    import copy
    import scipy.ndimage as spn 
    out = copy.copy(y)
    medi = spn.median_filter(y, kernelSize)  # moving median
    z = np.abs(y-medi)/np.std(y-medi)  # departure from stantard deviation
    I = z > threshold
    out[I] = medi[I]  # replace bad values by median
    return out

def findSpike(y, threshold=2):
    """
    I = findSpike(y, threshold)
    Detect a spike in y.
    It works by detecting points too far from the median value.
    Returns index of the bad points
    Works better for points representing the same value
    """
    m = np.median(y)
    s = np.std(y)
#    print(m)
#    print(s)
#    print(threshold)
    I = (abs(y-m) > s*threshold)
#    print(abs(y-m)/m > s/m)
    #I = np.any([(m+s*threshold)<y, (m-s*threshold)>y], axis=0)
    #print(I)
    return np.where(I)

def replaceSpike(x, y, I):
    """
    y = replaceSpike(x, y, I)
    Replace bad points in y by good ones.
    I is the index of bad points.
    Works by doing a linear fit over the data.
    """
    mod = LinearModel()
    params = mod.guess(data=np.delete(y, I), x=np.delete(x, I))
#    print(params)
#    print(np.delete(y, I))
    result = mod.fit(np.delete(y, I), params, x=np.delete(x, I))    
#    print(result.fit_report())
#    print(result.best_values)
    yy = mod.eval(x=x, slope=result.best_values['slope'], intercept=result.best_values['intercept'])
    y[I] = yy[I]
    return y

def cleanSpikes(y, threshold=2):
    """
    y = cleanSpikes(y, threshold=3)
    Clean y from "cosmic ray" spikes.
    The filtering works by comparing the same "position" taken few times.
    One has to have at least 5 repetitions to have this function work. 
    If not, return original y.
    """
    yy = deepcopy(y)
    if len(np.shape(y)) > 1:
        if np.size(y, 0) >= 5:
            #print(np.size(y, 1))
            for I in range(np.size(y, 1)):
                yyy = yy[:, I]
                xxx = np.arange(np.size(y, 0))

                J = findSpike(yyy, threshold)
                yy[:, I] = replaceSpike(xxx, yyy, J)
                
    yy = np.median(y, axis=0) * np.size(y, 0)
            
    return yy    
