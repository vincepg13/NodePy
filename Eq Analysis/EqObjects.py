#Imports 
import sys
import math
import cmath
import CableLabs
import numpy as np
import matplotlib.pyplot as plt
from operator import itemgetter

class EqAnalyser(object):
    """
    Class: EqObjects 
    
    instances replicate cable modems containing equalisation information and 
    network information
    
    @author: vince
    """  
    limitList = ([-40, -40, -40, -40, -30, -25, -20, 0, -20, -25, -30, 
                  -40, -40, -40, -40, -40, -40, -40, -40, -40, -40, -40, -40, -40])
    limitList2 = ([30, 30, 30, 30, 40, 45, 50, 70, 50, 45, 40, 
                  30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30])
    
    def __init__(self, macAddress, upStream, hexString, node="NULL", amp="NULL", cab="NULL", location="NULL"):
        """
        the constructor of the EqAnalyser class
        @param macAddress - the mac address of the modem
        @param upStream - the upstream corresponding to the equalisation data
        @param hexString - 200 character hexadecimal equalisation string
        @param node - the name of the node the mac address belongs to, defaults to NULL
        @param amp - the name of the amp the mac address belongs to, defaults to NULL
        @param cab - the name of the cab the mac address belongs to, defaults to NULL  
                     this could also be the tap reference (SID area)
        """        
        self.mac = macAddress
        self.up = upStream
        self.zeroCount = 0
        self.node = node
        self.amp = amp
        self.cab = cab
        self.location = location
        
        returnHold = self.hexBreaker(hexString)
        self.header = returnHold[0]
        self.coefHolder = returnHold[1]
        returnHold2 = self.energyAmplitude(self.coefHolder)
        self.energyHolder = returnHold2[0]
        self.ampGraph = returnHold2[1]
        
        self.ICFRdataRaw = self.fourier(self.fourierLists(self.coefHolder), 7)
        self.ICFRdataAmp = self.icfrAmplitudes(self.ICFRdataRaw)[0]
        self.ICFRdataPhase = self.icfrAmplitudes(self.ICFRdataRaw)[1]
        self.metrics = self.keyMetrics(self.energyHolder, self.ICFRdataAmp)

    def hex2dec4N2(self, hexValue):
        """
        converts hex to decimal under the 4 nibbles twos complement 
        @param hexValue - a four nibble hex string, e.g. "F06A"
        @return - the decimal value as an integer
        """
        x='0x' + hexValue   
        y = int(x, 16)
        return -(y & 0x8000) | (y & 0x7fff)
    
    def hex2dec3N2(self, hexValue):
        """
        converts hex to decimal under the 4 nibbles twos complement 
        @param hexValue - a four nibble hex string, e.g. "F06A"
        @return - the decimal value as an integer
        """    
        x='0x' + hexValue   
        y = int(x, 16)
        return -(y & 0x800) | (y & 0x7ff)
    
    def hex2dec(self, hexValue):
        """
        converts hex to decimal under the 4 or 3 nibbles twos complement 
        @param hexValue - a four nibble hex string, e.g. "F06A"
        @return - the decimal value as an integer
        """
        if hexValue.startswith('0'):
            return self.hex2dec3N2(hexValue)
        else:
            return self.hex2dec4N2(hexValue)
        
    def scaler(self, real, imag):
        """
        sets the scale value for equalisation coefficients
        @param real - the real part of an eq coefficient
        @param imag - the imaginary part of an eq coefficient
        @return - the scale value
        """
        magnitude = ((real*real)+(imag*imag))**0.5
        if magnitude <= 768:
            scaleValue = 512
        elif magnitude <= 1536:
            scaleValue = 1024
        elif magnitude <= 3072:
            scaleValue = 2048
        elif magnitude <= 6144:
            scaleValue = 4096
        elif magnitude <= 12288:
            scaleValue = 8192
        elif magnitude <= 24576:
            scaleValue = 16384
        else:
            scaleValue = 32768
        return(scaleValue)
        
    def hexBreaker(self, hexString):
        """
        converts a 200 character equalisation hex string into decimal values.
        @param hexString - the hexString, read in from a file
        
        @return - a two element holding list
        "head" - this is the header section of the hexString, corresponding to 
        the first 8 characters
        "holder" - a 24 element list where each element is a list of length two. 
        The first element is the real value, the second is the imaginary. 
        """
        n = 4
        m = 2
        head = [hexString[i:i+m] for i in range(0, 6, m)]
        real = [hexString[i:i+n] for i in range(8, len(hexString), n+4)]
        imag = [hexString[i:i+n] for i in range(12, len(hexString), n+4)]
        holder = []
        
        for i in range(len(real)):
            if i < len(head): head[i] = self.hex2dec(head[i])
            holder.append([real[i], imag[i]])
        
        scaleFactor = self.scaler(self.hex2dec(holder[7][0]), self.hex2dec(holder[7][1]))
        
        for i in range(len(holder)):
            if scaleFactor > 2048:
                holder[i][0] = self.hex2dec4N2(holder[i][0])/float(scaleFactor)
                holder[i][1] = self.hex2dec4N2(holder[i][1])/float(scaleFactor)
            else:
                holder[i][0] = self.hex2dec3N2(holder[i][0])/float(scaleFactor)
                holder[i][1] = self.hex2dec3N2(holder[i][1])/float(scaleFactor)
        return([head, holder])
    
    def energyAmplitude(self, coefList):
        """
        converts real and imaginary coefficients into energies and amplitudes
        @param coefList - a 24x2 list of the eq coefficients
        
        @return - a two element holding list
        "energy" - the energy values 
        "amp" - the amplitude values offset by + 70 (for graphical purposes)
        """
        energy = []
        amp = []        
        for i in range(len(coefList)):
            hold = (((coefList[i][0])**2) + (coefList[i][1])**2)
            energy.append(hold)

            if coefList[i][0] == 0 and coefList[i][1] == 0 :
                amp.append(0)
                self.zeroCount += 1
            else:
                amp.append(10*math.log10(energy[i]) + 70)
        return([energy, amp])
    
    def keyMetrics(self, energyList, freqDomainAmps):
        """
        calculates the key metrics
        @param energyList - 24 element list of coefficient energies
        @freqDomainAmps - list of values for the in channel frequency response
        @return - a 7 element holding list of all the metrics 
        """
        PreMTE = sum(energyList[0:7])
        MTE = energyList[7]
        PostMTE = sum(energyList[8:24])
        TTE = PreMTE + MTE + PostMTE
        MTC = 10*math.log10(TTE/MTE)
        NMTER = 10*math.log10((PreMTE + PostMTE)/TTE)
        PREMTTER = 10*math.log10(PreMTE/TTE)
        POSTMTTER = 10*math.log10(PostMTE/TTE)
        ICFR = max(freqDomainAmps) - min(freqDomainAmps)
        MTR = 10*math.log10((MTE/(PreMTE + PostMTE)))
        return([TTE, MTC, NMTER, PREMTTER, POSTMTTER, ICFR, MTR])  

    def icfrAmplitudes(self, icfrRawList):
        """
        converts raw frequency values into amplitudes and phases
        @param icfrRawList - the list of ICFR values
        
        @return - a two element holding list
        "ampTemp" - the amplitude result
        "phaseTemp" - the phase result
        """
        ampTemp = []
        phaseTemp = []
        for i in range(len(icfrRawList)):
            ampTemp.append(20*math.log10(abs(icfrRawList[i])))
            phaseTemp.append(cmath.phase(icfrRawList[i]))
        
        return [ampTemp, phaseTemp]          
    
    def fourierLists(self, coefList):
        """
        formats the input into the fourier transform
        @param coefList - 24 element list of equalisation coefficients
        @return complexInput - a list of complex elements, of power 2
        """
        mainpost = coefList[7:24]
        premain = coefList[0:7]
        zeroPadding =[[0,0], [0,0], [0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
        temp = (mainpost + zeroPadding + zeroPadding + zeroPadding + zeroPadding + zeroPadding +
        zeroPadding + zeroPadding + zeroPadding + zeroPadding + zeroPadding + zeroPadding + 
        zeroPadding + zeroPadding + premain)
        complexInput = []
                
        for i in range(len(temp)):
            complexInput.append(complex(temp[i][0], temp[i][1]))
        
        return complexInput
    
    def fourier(self, x, m):
        """
        conducts an FFT on a complex input, whose size is of 2^m
        @param x - the complex input
        @param m - 2^m gives the size of x
        @return x - the output of the FFT
        
        @Credit - Cable Labs, Mohit
        """
        if m == 0:
            sys.exit(1)
        n = 2 ** m
        le = n // 2 
        w = [complex(0, 0) for i in range(le - 1)]
        arg = 4.0 * math.atan(1.0) / le
        wrecur_real = w_real =  math.cos(arg)
        wrecur_imag = w_imag = -math.sin(arg)
        for i in range(len(w)):
            w[i] = complex(wrecur_real, wrecur_imag)
            wtemp_real = wrecur_real * w_real - wrecur_imag * w_imag
            wrecur_imag = wrecur_real * w_imag + wrecur_imag * w_real
            wrecur_real = wtemp_real
        le = n
        windex = 1
        for l in range(m):
            le //= 2
            for i in range(0, n, 2 * le):
                xi = i
                xip = i + le
                temp = x[xi] + x[xip]
                x[xip] = x[xi] - x[xip]
                x[xi] = complex(temp)
            wptr = windex - 1
            for j in range(1, le, 1):
                u = w[wptr]
                for i in range(j, n, 2 * le):
                    xi = i
                    xip = i + le
                    temp = x[xi] + x[xip]
                    tm = x[xi] - x[xip]
                    x[xip] = complex(tm.real * u.real - tm.imag * u.imag,
                                     tm.real * u.imag + tm.imag * u.real)
                    x[xi] = temp
                wptr += windex
            windex *= 2
        j = 0
        for i in range(1, n - 1, 1):
            k = n // 2
            while k <= j:
                j -= k
                k //= 2
            j += k
            if i < j:
                temp = x[j]
                x[j] = x[i]
                x[i] = temp
        return x

### FUNCTIONS NOT CALLED IN CREATION ###

### 1 - getters, mere formalities
    def getMTC(self):
        return self.metrics[1]
    def getNMTER(self):
        return self.metrics[2]
    def getICFR(self):
        return self.metrics[5]
    def getMTR(self):
        return self.metrics[6]
    def getMrLevel(self):
        energyList = self.energyHolder
        MTE = energyList[7]
        PostMTE = sum(energyList[8:24])
        return 10*math.log10(MTE/PostMTE)
    def getGdLevel(self):
        energyList = self.energyHolder
        PreMTE = sum(energyList[0:7])
        MTE = energyList[7]        
        return 10*math.log10(MTE/PreMTE)
    def getRawAmplitude(self):
        ampData = [x-70 for x in self.ampGraph]
        return ampData
        
### 2 - printing and plotting
    def pltAmp(self, subplot):
        bars = self.ampGraph
        for i in range(len(bars)):
            if bars[i] < 0: bars[i] = 0
        plt.bar(range(len(self.ampGraph)),self.ampGraph, width=0.9)
        plt.plot(np.arange(0,24,0.5)[1::2], self.limitList2, "o", markersize=6, color='r')
        plt.ylim([0, 70])
        plt.xlim([0, 24])
        locs, labels = plt.yticks()
        labels = [int(item)-70 for item in locs]
        plt.yticks(locs, labels)
        ax=plt.subplot(subplot)
        ax.plot([0., 24.], [20, 20], linewidth=4, color='g')
        
    def pltICFR(self):
        plt.ylim([-4, 4])
        plt.xlim([0, 128])
        plt.plot(range(128), self.ICFRdataAmp, label=self.mac)
        
    def pltPhase(self):
        plt.plot(range(128), self.ICFRdataPhase, label=self.mac)
        plt.ylim([-1, 1])
        plt.xlim([0, 128])
        
    def printResults(self, withGraph):
        print ("Mac: " + self.mac + ", Upstream: " + self.up + '\n' + "Key metrics: TTE=" + str(round(self.metrics[0], 5))
        + " MTC=" + str(round(self.metrics[1], 5)) + " NMTER=" + str(round(self.metrics[2], 5)) + 
        " PREMTTER=" + str(round(self.metrics[3], 5)) + " POSTMTTER=" + str(round(self.metrics[4], 5))
        + " MTR=" + str(round(self.metrics[6], 5)) + " ICFR=" + str(round(self.metrics[5], 5)))
        
        if withGraph == 0:
            pass
        elif withGraph == 1:
            plt.title(str(self.mac) + ": " + str(self.up))
            self.pltICFR()
        elif withGraph == 2:
            plt.figure(1)
            plt.title(str(self.mac) + ": " + str(self.up))
            plt.subplot(211)
            self.pltICFR()
            plt.subplot(212)
            self.pltAmp(212)
        elif withGraph == 3:            
            plt.figure(1)
            plt.title(str(self.mac) + ": " + str(self.up))
            plt.subplot(311)
            self.pltICFR()            
            plt.subplot(312)
            self.pltAmp(312)
            plt.subplot(313)
            self.pltPhase()
        elif withGraph == 4:
            self.pltAmp(111)
        else:
            pass
            
        plt.show  
        
    def printer(self, numerator):
        plt.figure(numerator)
        #plt.subplot(311)
        #self.pltICFR()
        #plt.subplot(312)
        #self.pltAmp(312)
        #plt.subplot(313)
        #self.pltPhase()
        self.pltAmp(111)
        plt.show 
        
### 3 - Other stuff
    def complexFormat(self, listToFormat):
        formattedList = list()
        for i in range(len(listToFormat)):
            formattedList.append(complex(listToFormat[i][0], listToFormat[i][1]))
        return formattedList
        
    def interpolationEnergy(self):
        energy = []        
        for i in range(len(self.coefHolder)):
            hold = (((self.coefHolder[i][0])**2) + (self.coefHolder[i][1])**2)**0.5
            energy.append(hold)

        return(energy)
    
    def getHighTaps(self):
        tapResults = []
        tapVals = self.getRawAmplitude()
        
        for i in range(len(tapVals)):
            if tapVals[i] > self.limitList[i] + 2:
                tapResults.append((i+1, (tapVals[i] - self.limitList[i])))
                
        tapResults.sort(key=itemgetter(1), reverse = True)
        #maxVal = max(tapResults,key=itemgetter(1))[0]  
        
        return tapResults
        
    def getHighMrTaps(self):
        taps = self.getHighTaps()
        mrTaps = []
        
        for tap in taps:
            if tap[0] > 8: mrTaps.append(tap)
    
        return mrTaps

    def getHighGdTaps(self):
        taps = self.getHighTaps()
        gdTaps = []
        
        for tap in taps:
            if tap[0] < 8: gdTaps.append(tap)
    
        return gdTaps
    
    def vTDR(self):
        taps = self.getHighMrTaps()
        if len(taps) > 0:
            try:
                guiltyTap = CableLabs.Eq.interpolateTap(self, taps[0][0])[0]
                dist = CableLabs.Eq.interpolateTap(self, taps[0][0])[0] - 8
                if abs(guiltyTap - taps[0][0]) > 1:
                    return 24.4*(taps[0][0] - 8)
                else:
                    return dist*24.4
            except(ValueError):
                return (taps[0][0] - 8)*24.4
        else:
            return 0

### 4 - Raising custom exceptions, non implemented      
#class TapPositionException(Exception):
#    pass
#class D1DataException(Exception):
#    pass
