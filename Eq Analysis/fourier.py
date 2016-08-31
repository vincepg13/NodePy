#! /usr/bin/python
import sys
import math
import matplotlib.pyplot as plt
import EqObjects as obj

def fourier(x, m):
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
    
test = obj.EqAnalyser('Mac', 'US', '0801180000000001fff900000005fff7fff6000f000fffe1ffe300380025ff6d07d80000ffca00abffdc000bff14ffd3fff0fff400840083ffc9003ffffdfffffff2fffb0006fffffffb00020001fffcfffffff8fffcfffe00020000000000060000fffd')
newtest = []

for i in range(len(test.ICFRdataRaw)):
    newtest.append(20*math.log10(abs(test.ICFRdataRaw[i])))

print newtest

plt.plot(range(128), newtest)
plt.show

#with open("data.csv", "r") as fs:
#    data = fs.readlines()
#
#lines = []
#for line in data:
#    lines.append(line.rstrip().split(","))
#
#comp = []
#for line in lines:
#    comp.append(complex(float(line[0]), float(line[1])))
#
#ret = fourier(comp, 5)
#
#for line in ret:
#    print(line / 2048)
