# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 11:29:28 2016

@author: vince
"""
#from __future__ import division 
import math
import sys

class Eq:
    """
    Code translated from Cable Labs Java eq-analysis program. Set of functions accessible
    via the creation of an Eq object.
    """
    
    def modemMatcher(self, modem1, modem2, dbMatch):
        complexDiv = list()
        if modem1.metrics[6] > modem2.metrics[6]: 
            num = modem1
        else: 
            num = modem2
        
        if modem1 == num:
            denom = modem2
        else:
            denom = modem1
        
        for i in range(len(num.ICFRdataRaw)):
            complexDiv.append(self.div(num.ICFRdataRaw[i], denom.ICFRdataRaw[i]))
                
        self.ifft(complexDiv)
        mer = self.calcMtr(complexDiv)
        if mer - num.metrics[6] >= dbMatch:
            return True
        else:
            return False
        
    def calcMtr(self, complexList):
        main = self.magSquared(complexList[0])
        denom = 0
        for i in range(1,len(complexList),1):
            denom = denom + self.magSquared(complexList[i])
        return 10*math.log10(main/denom)
        
    def magSquared(self, complexNumber):
        return complexNumber.real**2 + complexNumber.imag ** 2
               
        
    def div(self, com1, com2):
        denom = com2.real * com2.real + com2.imag * com2.imag
        real = (com1.real * com2.real + com1.imag * com2.imag)/denom
        imag = (com1.imag * com2.real - com1.real * com2.imag)/denom
        return complex(real, imag)
        
    def lookup(self, num):
        if num == 0:
            sys.exit(1)
        
        w = list()
        arg = math.pi / abs(num)

        if (num >= 0):
             wrecur = complex(math.cos(arg), -math.sin(arg))
        else:
             wrecur = complex(math.cos(arg), math.sin(arg))
        
        cmplx = wrecur
        top = abs(num) - 1
        for i in range(top):
            w.append(wrecur)
            wrecur = self.mul(wrecur, cmplx)

        return w

    def mul(self, complexNum, otherComplex):
        real = complexNum.real * otherComplex.real - complexNum.imag * otherComplex.imag
        imag = complexNum.imag * otherComplex.real + complexNum.real * otherComplex.imag
        
        return complex(real, imag)

    def fftWorker(self, data, w):
        n = len(data)
        exponent = int(math.log(n)/math.log(2.0))
        #le = n/2
        le = n
        wOffset = 1
        
        for i in range(exponent):
            le2 = le
            le = le/2
            
            for j in range(0, n, le2):
                k = j + le
                tmp = complex(data[j].real + data[k].real, data[j].imag + data[k].imag)
                data[k] = complex(data[j].real - data[k].real, data[j].imag - data[k].imag)
                data[j] = tmp 
            
            wIdx = wOffset - 1
            for l in range(1,le,1):
                for m in range(l, n, le2):
                    o = m + le
                    tmp = complex(data[m].real + data[o].real, data[m].imag + data[o].imag) 
                    data[o] = complex(data[m].real - data[o].real, data[m].imag - data[o].imag)
                    data[o] = self.mul(data[o], w[wIdx])
                    data[m] = tmp
                wIdx = wIdx + wOffset
            wOffset = wOffset * 2

        j = 0
        for i in range(1, n-1, 1):
            k = n/2
            while k <= j:
                j = j-k
                k = k/2
            j = j+k
            if i<j:
                tmp = data[j]
                data[j] = data[i]
                data[i] = tmp
        
    def fft(self, complexDataList):
        n = len(complexDataList)
        le = int(n/2)
        
        w = self.lookup(le)
        
        self.fftWorker(complexDataList, w)   
    
    def ifft(self, complexDataList):
        n = len(complexDataList)
        le = int(n/2)
        
        w = self.lookup(-le)
        
        self.fftWorker(complexDataList, w)   
        scale = float(1/float(n))
        for i in range(n):
            real = complexDataList[i].real * scale
            imag = complexDataList[i].imag * scale
            complexDataList[i] = complex(real, imag)
            
    @staticmethod
    def interpolateTap (modem, tapLocation):
        if tapLocation <= 1 or tapLocation >=24:
            return "Invalid interpolation tap"
        elif tapLocation == 9:
            return [9, modem.ICFRdataAmp[8]]
        else:
            tapIndex = tapLocation - 1 
            
            x1 = tapIndex - 1
            x1Sqr = (x1)**2
            y1 = modem.interpolationEnergy()[x1]
        
            x2 = tapIndex
            x2Sqr = (x2)**2
            y2 = modem.interpolationEnergy()[x2]
            
            x3 = tapIndex + 1
            x3Sqr = (x3)**2
            y3 = modem.interpolationEnergy()[x3]
            
            a = [[x1Sqr, x1, 1],[x2Sqr, x2, 1], [x3Sqr, x3, 1]]
            
            det = float(a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - 
            a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) + 
            a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
            
            first = [(a[1][1] * a[2][2] - a[1][2] * a[2][1]) / det, (a[0][2] * a[2][1] - a[0][1] * a[2][2]) / det, (a[0][1] * a[1][2] - a[0][2] * a[1][1]) / det]      
            second = [(a[1][2] * a[2][0] - a[1][0] * a[2][2]) / det, (a[0][0] * a[2][2] - a[0][2] * a[2][0]) / det, (a[0][2] * a[1][0] - a[0][0] * a[1][2]) / det]      
            third = [(a[1][0] * a[2][1] - a[1][1] * a[2][0]) / det, (a[0][1] * a[2][0] - a[0][0] * a[2][1]) / det, (a[0][0] * a[1][1] - a[0][1] * a[1][0]) / det ]       
            
            b = [first, second, third]
             
            A = y1 * b[0][0] + y2 * b[0][1] + y3 * b[0][2]
            B = y1 * b[1][0] + y2 * b[1][1] + y3 * b[1][2]
            C = y1 * b[2][0] + y2 * b[2][1] + y3 * b[2][2]
             
            xPeak = (-B / float(2 * A)) 
            yPeak = (A * (xPeak**2)) + (B * xPeak) + C
             
            return [round(xPeak + 1, 3), round(20*math.log10(yPeak/modem.energyHolder[7]),3)]
    

                        
                        
                        
                        
                        
                        
                        
    
    