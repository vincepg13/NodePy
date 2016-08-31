# -*- coding: utf-8 -*-
"""
Created on Thu Apr 07 14:09:03 2016

@author: vince
"""
import time
import EqObjects
import CableLabs
import csv
import os
import sys 
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
import matplotlib
from collections import defaultdict, Counter
from tabulate import tabulate
from operator import itemgetter
#import pygmaps
import gmplot
import DbConnect

#filename = 'A1M 2305.csv'
#filename = 'KAG7000 2705.csv'
#filename = 'M17A 2305.csv'
#filename = 'M17B 2305.csv'
#filename = 'AVG.csv'

filename = ''
nodeName = ''
redS = 22
amberS = 28
matplotlib.rcParams.update({'font.size': 10})

##############################################################################
################################ DATA LOADING ################################
################################ FILE WRITING ################################
##############################################################################
"""
the following set of functions handle the loading of data and writing the outputs
to/from CSV files. As well as this, methods for internal loading, such as collating 
objects into lists for further manipulation can be found here.
"""
def openCsv(csvFile):
    global nodeName
    columns = defaultdict(list) 
    filePath = os.path.join('./Data', csvFile)

    with open(filePath) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)
    
    try:
        nodeName = Counter(columns['Node']).most_common(1)[0][0]
    except(IndexError):
        print "No node name available"
    return columns
    
def multiFileLoad(beginsWith):
    columns = defaultdict(list)

    for csvFile in os.listdir(os.path.join(os.getcwd(), 'Data')):
        tester = os.path.join('./Data', csvFile)
        if csvFile.endswith(".csv") and csvFile.startswith(beginsWith):    
            with open(tester) as f:
                reader = csv.DictReader(f) 
                for row in reader: 
                    for (k,v) in row.items(): 
                        columns[k].append(v)      
    
    return columns

def csvRW(modemList):
    global filename
    File = 'Metrics ' + filename
    filePath = os.path.join('./Metrics', File)
    with open(filePath, 'wb') as fp:
        a = csv.writer(fp)
        a.writerow(["Mac Adress","Upstream","TTE", "MTC", "NMTER", "PREMTTER",
                    "POSTMTTER", "ICFR", "MTR", "MRLevel", "GDLevel"])        
        
        for modem in modemList:
            a.writerow([modem.mac,modem.up,modem.metrics[0],
            modem.metrics[1],modem.metrics[2],modem.metrics[3],modem.metrics[4],
            modem.metrics[5], modem.metrics[6], modem.getMrLevel(), modem.getGdLevel()]) 
            
def objLoader():
    global filename
    start_time = time.time()
    objList = list()
    columns = openCsv(filename)
    csvLength = 0

    for i in range(len(columns['Mac'])):
        csvLength += 1
        try:
            if len(columns['Amp']) == 0 or len(columns['Lat']) == 0:
                objList.append(EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i]))
            else:
                objList.append(EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i], columns['Node'][i], columns['Amp'][i],columns['Cab'][i], (float(columns['Lat'][i]), float(columns['Long'][i]))))
        except (ZeroDivisionError, ValueError, IndexError):
            pass#print("Invalid string, mac address: " + columns['Mac'][i] + " upstream: " + columns['US'][i])
    
    print("--- %s seconds ---" % (time.time() - start_time))
    print("objects loaded: " + str(len(objList)) + "/" + str(csvLength))
    
    return objList
    
def objLoaderDb(node, date, pwd):
    start_time = time.time()
    objList = list()
    db = DbConnect.psql('PNM', 'postgres', pwd)
    eq = db.getEqData(node, date)    
    rows = 0
    for row in eq:
        rows += 1
        try:
            #if rows == 1: print row[2]
            objList.append(EqObjects.EqAnalyser(row[0], row[1], row[2], row[3], row[4],row[5], (float(row[6]), float(row[7]))))
        except (ZeroDivisionError, ValueError, IndexError):
            pass#print("Invalid string, mac address: " + columns['Mac'][i] + " upstream: " + columns['US'][i])

    print("--- %s seconds ---" % (time.time() - start_time))
    print("objects loaded: " + str(len(objList)) + "/" + str(rows))
    return objList

def upstreamSplitter(modemList):
    data = {}
    keys = []
    dataL = []
    
    for modem in modemList:
        key = modem.up
        try:
            data[key].append(modem)
        except(KeyError):
            data[key]=[]
            data[key].append(modem)
    
    for key in data:
        keys.append(key)
    
    keys.sort()
    for val in keys:
        dataL.append(data[val])
    
    return dataL
    
def multiSetLoader(beginsWith):
    start_time = time.time()
    objList = list()
    columns = multiFileLoad(beginsWith)
    csvLength = 0
    data = {}

    for i in range(len(columns['Mac'])):
        csvLength += 1
        try:
            if len(columns['Amp']) == 0 or len(columns['Lat']) == 0:
                objList.append(EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i]))
            else:
                objList.append(EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i], columns['Node'][i], columns['Amp'][i],columns['Cab'][i], (float(columns['Lat'][i]), float(columns['Long'][i]))))
        except (ZeroDivisionError, ValueError, IndexError):
            pass#print("Invalid string, mac address: " + columns['Mac'][i] + " upstream: " + columns['US'][i])
    
    print("--- %s seconds ---" % (time.time() - start_time))
    print("objects loaded: " + str(len(objList)) + "/" + str(csvLength))
    
    for obj in objList:
        key = (obj.mac, obj.up)
        try:
            data[key].append(obj)
        except(KeyError):
            data[key] = []
            data[key].append(obj)
            
    return data
    
def severityLoader(upstream, severityMTR=200, severityICFR=0):
    global filename    
    start_time = time.time()
    objList = list()
    columns = openCsv(filename)
    csvLength = 0

    for i in range(len(columns['Mac'])):
        csvLength += 1
        if abs(float(columns['US'][i]) - upstream) < 3.4:
            try:
                if len(columns['Amp']) == 0:
                    loader = EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i])
                else:
                    loader = EqObjects.EqAnalyser(columns['Mac'][i], columns['US'][i], columns['EqHex'][i], columns['Node'][i], columns['Amp'][i],columns['Cab'][i], (float(columns['Lat'][i]), float(columns['Long'][i])))
                    
                if loader.metrics[6] <= (severityMTR) and loader.metrics[5] >= (severityICFR):    
                    objList.append(loader)
            except (ZeroDivisionError, ValueError, IndexError):
                pass                   
    
    print("--- %s seconds ---" % (time.time() - start_time))
    print("objects loaded: " + str(len(objList)) + "/" + str(csvLength))
    
    return (objList)
    
def macSearch(mac, up, graphType):
    global filename
    filePath = os.path.join('./Data', filename)
    with open(filePath, mode='r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] in [mac] and (abs(float(row[1]) - float(up)) < 3.4):  
                r= row[2]
    
    search = EqObjects.EqAnalyser(mac, up, r, "NULL")
    if graphType >= 0:  search.printResults(graphType) 
    
    return search
    
def correlationAlgorithm(inputList, strength):
    print "######### HAVE YOU REMEMBERED ASSIGNMENT??? ######### "
    sys.stdout.flush()
    
    start_time = time.time()
    worker = CableLabs.Eq()
    modems = inputList
    macsTested = []
    correlationSet = []
    correlationFlag = False
    correlationCount = 0
    
    for i in range(len(modems)):
        modem = modems[i]
        temp = []
        correlationFlag = False
        
        if modem.mac in macsTested:
            pass
        else:
            for l in range(len(modems)):
                if modem.mac == modems[l].mac or modems[l].mac in macsTested:
                    pass
                else: 
                    condition = worker.modemMatcher(modem, modems[l], strength)
                    if condition is True:
                        temp.append(modems[l])
                        macsTested.append(modems[l].mac)
                        correlationCount += 1
                        correlationFlag = True
            
            if correlationFlag is True: 
                temp.append(modem)
                correlationCount +=1 
                
            if len(temp) != 0: 
                correlationSet.append(temp)
                
            macsTested.append(modem.mac)
        
    print("--- %s seconds ---" % (time.time() - start_time))
    corPrint(correlationSet)
    print  ("Correlated: " + str(correlationCount) + " - Groups: " + str(len(correlationSet)))   
    return correlationSet


##############################################################################
############################# GRAPHICS CREATORS ##############################
############################# GRAPHICS CREATORS ##############################
##############################################################################
"""
This set of methods deal with the creation of graphical elements of the program.
all graphical objects are rendered inline and displayed in the ipython terminal.
"""
def completeResponse(inputList):
### D3 Upstreams: 25.8, 32.6, 39.4, 46.2, 53.7, 60.3
    #matplotlib.interactive(True)    
    macCount = 0
    #start_time = time.time()
    plt.figure(1, figsize=(15,12))
    
    for i in range(len(inputList)):
        objHolder = inputList[i]
        objHolder.pltICFR()
        macCount += 1  
    plt.title(objHolder.up)
    control = plt.gca()
    control.axes.get_xaxis().set_visible(False)
    matplotlib.rcParams.update({'font.size': 15})
    plt.show()
    print("Mac Addresses in upstream: " + str(macCount))
    #print("--- %s seconds ---" % (time.time() - start_time))
    #print("  ")

def ampResponse(inputList):   
    macCount, mtrSum = 0, 0
    plt.figure(1, figsize=(15,12))
    for i in range(len(inputList)):
        objHolder = inputList[i]
        objHolder.pltICFR()
        mtrSum += objHolder.getMTR()
        macCount += 1  
    plt.title("Amp: " + objHolder.amp + " - Group MTR = " + str(mtrSum/float(macCount)))
    control = plt.gca()
    control.axes.get_xaxis().set_visible(False)
    matplotlib.rcParams.update({'font.size': 15})
    plt.show()
    print("Mac Addresses in upstream: " + str(macCount))

    
def groupAnalyser(inputGroup):
    highTaps = groupHighTap(inputGroup)
    MTR = 0
    objsMet = []
    widthTotal = 24
    stepWidth = 1
    sepWidth = 0.9
    ups = inputGroup[0].up
    for MTRvals in inputGroup:  
        MTR += MTRvals.metrics[6] 
        objsMet.append([MTRvals.mac] + [round(MTRvals.metrics[1],4)] + [round(MTRvals.metrics[6],4)]
        + [round(MTRvals.metrics[5],4)] + [round(MTRvals.vTDR(),2)] + [MTRvals.cab])
    
    print '----------------------------------------------------------------'
    print tabulate(objsMet, headers=['Mac Address','MTC','MTR','ICFR','vTDR','Cab'], tablefmt='orgtbl')
    print '----------------------------------------------------------------' 
        
        
    plt.figure(0, figsize=(15,12))
    test = range(0,widthTotal,stepWidth)
    for l in range(len(inputGroup)):
        inputGroup[l].pltICFR()
    if len(inputGroup)<12:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("GROUP ICFR (" + ups + ") : Macs - " + str(len(inputGroup)) + ", MTR - " + str(round(MTR/len(inputGroup), 2)))
    
    plt.figure(1, figsize=(15,12))
    for l in range(len(inputGroup)):
        bars = inputGroup[l].ampGraph
        for i in range(len(bars)):
            if bars[i] < 0: bars[i] = 0
        ax=plt.subplot(111)
        plt.bar(range(len(bars)),bars, color=cm.jet(1.*l/len(inputGroup)), label=inputGroup[l].mac)
        plt.plot(np.arange(0,24,0.5)[1::2], EqObjects.EqAnalyser.limitList2, "o", color='r')        
        plt.ylim([0, 70])
        plt.xlim([0,24])
        locs, labels = plt.yticks()
        labels = [int(item)-70 for item in locs]
        plt.yticks(locs, labels)
        ax.plot([0., 24.], [20, 20], linewidth=3, color='g')
    if len(inputGroup)<12:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("Macs - " + str(len(inputGroup)) + ", MTR - " + str(round(MTR/len(inputGroup), 2)))
    
    plt.figure(2, figsize=(15,12))
    for l in range(len(inputGroup)):
        bars = inputGroup[l].ampGraph
        for i in range(len(bars)):
            if bars[i] < 0: bars[i] = 0
        for i in range(len(test)): test[i] = test[i]+(sepWidth/float(len(inputGroup)))
        ax=plt.subplot(111)
        ax.bar(test, bars,width=(sepWidth/float(len(inputGroup))),color=cm.jet(1.*l/len(inputGroup)),align='center', label=inputGroup[l].mac)            
        plt.plot(np.arange(0.1,24.1,0.5)[1::2], EqObjects.EqAnalyser.limitList2, "o", color='r')        
        plt.ylim([0, 70])
        plt.xlim([0,24])
        locs, labels = plt.yticks()
        labels = [int(item)-70 for item in locs]
        plt.yticks(locs, labels)
        ax.plot([0., 24.], [20, 20], linewidth=5, color='g')
    if len(inputGroup)<12:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("GROUP TAP RESPONSE (" + ups + ") : Macs - " + str(len(inputGroup)) + ", MTR - " + str(round(MTR/len(inputGroup), 2)))
    
    plt.figure(3, figsize=(15,12))
    for l in range(len(inputGroup)):
        inputGroup[l].pltPhase()
    if len(inputGroup)<12:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("GROUP PHASE RESPONSE (" + ups + ") : Macs - " + str(len(inputGroup)) + ", MTR - " + str(round(MTR/len(inputGroup), 2)))

    plt.show

def corPrint(correlationSet):
    disableFigWarn()
    for i in range(len(correlationSet)):
        plt.figure(i, figsize=(10,8))
        groupMTR = 0
        for l in range(len(correlationSet[i])):
            plt.plot(range(128), correlationSet[i][l].ICFRdataAmp, label=correlationSet[i][l].mac + ": MTR- " + str(round(correlationSet[i][l].metrics[6],2)) + ", " + str(correlationSet[i][l].amp))
            groupMTR = groupMTR + correlationSet[i][l].metrics[6]
        plt.ylim(-4,4)
        plt.xlim(0,128)
        plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
        plt.title("Correlation Group: " + str(i+1) + ", Macs - " + str(len(correlationSet[i])) + ", MTR - " + str(round(groupMTR/float(len(correlationSet[i])), 2)))
        #plt.savefig("Correlation Group" + str(i+1))
        #plt.clf()
        #matplotlib.rcParams.update({'font.size': 10})
        #matplotlib.rc('xtick', labelsize=15) 
        #matplotlib.rc('ytick', labelsize=15) 
    plt.show() 
    
##############################################################################
############################# STATISTIC RUNNERS ##############################
############################# STATISTIC RUNNERS ##############################
##############################################################################
"""
Any object manipulation for the purpose of retrieving statistical data will 
live here.
"""
def cabGroup(upstreamGroup, cabName):
    results = []
    for objects in upstreamGroup:
        if objects.cab.startswith(cabName):
            results.append(objects)          
    return results

def cabCounter(inputGroup):
    cabDict = {}
    
    for objects in inputGroup:
        try:
            cabDict[objects.cab] = cabDict[objects.cab] + 1
        except(KeyError):
            cabDict[objects.cab] = 1
            
    return cabDict

def getAmpSet(modemGroup):
    hold = []
    for modem in modemGroup:
        hold.append(modem.amp)
    return set(hold)

def getAmpGraph(ampNames, upstream):
    for modem in upstream:
        for amp in ampNames:
            if modem.amp == amp:
                modem.pltICFR()
    
def ampGroup(upstreamGroup, ampName):
    results = []
    for objects in upstreamGroup:
        if objects.amp == ampName:
            results.append(objects)          
    return results

def ampCounter(inputGroup):
    ampDict = {}
    
    for objects in inputGroup:
        try:
            ampDict[objects.amp] = ampDict[objects.amp] + 1
        except(KeyError):
            ampDict[objects.amp] = 1
            
    return ampDict
    
def getRed(inputGroup):
    result = []
    for modem in inputGroup:
        if modem.getMTR() < redS:
            result.append(modem)
    return result
    
def getCmCount(inputGroup):
    counter = set()
    
    for modem in inputGroup:
        counter.add(modem.mac)
    
    return len(counter)

def getCmSet(inputGroup):
    storer = {}
    output = []
    
    for modem in inputGroup:
        try:
            storer[modem.mac].append(modem)
        except(KeyError):
            storer[modem.mac] = []
            storer[modem.mac].append(modem)
            output.append(modem)
        
    return output

def getNodeHealth(inputGroup):
    global redS
    global amberS
    data = {}
    tableData = []
    red, yellow, green = 0,0,0
    mtrSum = 0
    modemCount = 0
   # size = len(inputGroup)    

    for modem in inputGroup:
        mtrSum += modem.getMTR()
        modemCount += 1
        if modem.getMTR() < redS:
            red = red + 1
            try:
                data[modem.up][0] += 1
            except(KeyError):
                #data[modem.up] = [0,0,0,0,0,0]
                data[modem.up] = [0,0,0,0]
                data[modem.up][0] += 1
        elif modem.getMTR() < amberS:
            yellow = yellow + 1
            try:
                data[modem.up][1] += 1
            except(KeyError):
                #data[modem.up] = [0,0,0,0,0,0]
                data[modem.up] = [0,0,0,0]
                data[modem.up][1] += 1
        else:
            green = green + 1
            try:
                data[modem.up][2] += 1
            except(KeyError):
                #data[modem.up] = [0,0,0,0,0,0]
                data[modem.up] = [0,0,0,0]
                data[modem.up][2] += 1
        
        data[modem.up][3] += modem.getMTR()
        #data[modem.up][4] += modem.getMrLevel()
        #data[modem.up][5] += modem.getGdLevel()

    for key in data: 
        data[key][3] = round(data[key][3]/sum(data[key][0:3]),2)
        #data[key][4] = round(data[key][4]/sum(data[key][0:3]),2)
        #data[key][5] = round(data[key][5]/sum(data[key][0:3]),2)
        tableData.append([key] + data[key])
    
    totals = ['Total: '] 
    totals.append(sum([item[1] for item in tableData]))
    totals.append(sum([item[2] for item in tableData]))
    totals.append(sum([item[3] for item in tableData]))
    totals.append(round(mtrSum/float(modemCount),2))
    #totals.append(round(sum([item[5] for item in tableData])/len(data),2))
    #totals.append(round(sum([item[6] for item in tableData])/len(data),2))
    tableData.append(totals)
    tableData.sort(key=itemgetter(0))
    #print tabulate(tableData, headers=['Upstream','Red(<22)','Amber(<28)','Green(>28)','AvgMTR','AvgMR','AvgGD'], tablefmt='orgtbl')
    print tabulate(tableData, headers=['Upstream','Red(<22)','Amber(<28)','Green(>28)','AvgMTR'], tablefmt='orgtbl')

    total = red + yellow + green
    healthScore = 10 * (1 - ((red + (yellow*0.5))/total))
    return round(healthScore,2)     

def getAmpStats(inputGroup, Graphs):
    global redS
    global amberS
    data = {}
    tableData = []
    red, yellow, green = 0,0,0
    mtrSum = 0
    modemCount = 0
   # size = len(inputGroup)    

    for modem in inputGroup:
        mtrSum += modem.getMTR()
        modemCount += 1
        if modem.getMTR() < redS:
            red = red + 1
            try:
                data[modem.amp][0] += 1
            except(KeyError):
                data[modem.amp] = [0,0,0,0]
                data[modem.amp][0] += 1
        elif modem.getMTR() < amberS:
            yellow = yellow + 1
            try:
                data[modem.amp][1] += 1
            except(KeyError):
                data[modem.amp] = [0,0,0,0]
                data[modem.amp][1] += 1
        else:
            green = green + 1
            try:
                data[modem.amp][2] += 1
            except(KeyError):
                data[modem.amp] = [0,0,0,0]
                data[modem.amp][2] += 1
        
        data[modem.amp][3] += modem.getMTR()

    for key in data: 
        data[key][3] = round(data[key][3]/sum(data[key][0:3]),2)
        tableData.append([key] + data[key])
    
    totals = ['Z Total: '] 
    totals.append(sum([item[1] for item in tableData]))
    totals.append(sum([item[2] for item in tableData]))
    totals.append(sum([item[3] for item in tableData]))
    totals.append(round(mtrSum/float(modemCount),2))
    tableData.append(totals)
    tableData.sort(key=itemgetter(0))
    print tabulate(tableData, headers=['Amplifier','Red','Amber','Green','AvgMTR'], tablefmt='orgtbl')
    
    total = red + yellow + green
    healthScore = 10 * (1 - ((red + (yellow*0.5))/total))
    
    if Graphs is True:
        for A in range(len(tableData)-1):
            group = ampGroup(inputGroup, tableData[A][0])
            ampResponse(group)
        
    return round(healthScore,2)  
    
def getCabStats(inputGroup, Graphs):
    global redS
    global amberS
    data = {}
    tableData = []
    red, yellow, green = 0,0,0
    mtrSum = 0
    modemCount = 0
   # size = len(inputGroup)    

    for modem in inputGroup:
        mtrSum += modem.getMTR()
        modemCount += 1
        if modem.getMTR() < redS:
            red = red + 1
            try:
                data[modem.cab][0] += 1
            except(KeyError):
                data[modem.cab] = [0,0,0,0]
                data[modem.cab][0] += 1
        elif modem.getMTR() < amberS:
            yellow = yellow + 1
            try:
                data[modem.cab][1] += 1
            except(KeyError):
                data[modem.cab] = [0,0,0,0]
                data[modem.cab][1] += 1
        else:
            green = green + 1
            try:
                data[modem.cab][2] += 1
            except(KeyError):
                data[modem.cab] = [0,0,0,0]
                data[modem.cab][2] += 1
        
        data[modem.cab][3] += modem.getMTR()

    for key in data: 
        data[key][3] = round(data[key][3]/sum(data[key][0:3]),2)
        tableData.append([key] + data[key])
    
    totals = ['Z Total: '] 
    totals.append(sum([item[1] for item in tableData]))
    totals.append(sum([item[2] for item in tableData]))
    totals.append(sum([item[3] for item in tableData]))
    totals.append(round(mtrSum/float(modemCount),2))
    tableData.append(totals)
    tableData.sort(key=itemgetter(0))
    print tabulate(tableData, headers=['Cabinet','Red','Amber','Green','AvgMTR'], tablefmt='orgtbl')
    
    total = red + yellow + green
    healthScore = 10 * (1 - ((red + (yellow*0.5))/total))
    
    if Graphs is True:
        for A in range(len(tableData)-2):
            group = cabGroup(inputGroup, tableData[A][0])
            ampResponse(group)
            
    return round(healthScore,2)    
    
def getMacStats(inputGroup):
    tableData = []
    unique = getCmSet(inputGroup)
    
    for modem in unique:
        tableData.append([modem.mac, modem.node, modem.amp, modem.cab])
            
    print tabulate(tableData, headers=['Mac','Node','Amp','Cab'], tablefmt='orgtbl')
##############################################################################
################################ GEOMAPPING ##################################
################################ GEOMAPPING ##################################
##############################################################################
"""
functions which make use of the GmPlot module to geomap modem locations onto 
google maps. should really be part of the Geomap file but i simply cannot be 
fucked.
"""
def plotBaseMap(fileName, Map, dontPlot):
    columns = defaultdict(list) 

    with open(fileName + '.csv') as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)
    
    for i in range(len(columns['Mac'])):
        lat = float(columns['Latitude'][i])
        lon = float(columns['Longitude'][i])
        element = (lat, lon)
        
        if element not in dontPlot:
            Map.marker(lat, lon, color="m")
    
def plotGMapp(inputList):
    global redS
    global amberS
    unique = set()
    tracker = {}
    step = 0.00001
    vmul, hmul = {}, {}
    gmap = gmplot.GoogleMapPlotter(inputList[0].location[0], inputList[0].location[1], 16)
    
    for item in inputList:
        lat = item.location[0]
        lon = item.location[1]
        
        if item.getMTR() >= amberS:
            color = "#7FFF00"
        elif item.getMTR() < redS:
            color = "#FF0000"
        else:
            color = "#FFA500"
                
        element = (lat,lon)
        if element in unique:
            tracker[element] += 1
            multiplier = tracker[element]
            gmap.marker(lat, lon + (multiplier*step), color)
        else:
            gmap.marker(lat, lon, color)
            tracker[element] = 0
            vmul[element], hmul[element] = 0, 0
            unique.add(element)
    
    #plotBaseMap('MacLatLong', gmap, unique)
    mapName = raw_input("Map Name: ")
    gmap.draw(mapName + '.html')

def plotGMapGroups(inputSet):
    colours = ['b','g','r','c','m','y','k','w']
    gmap = gmplot.GoogleMapPlotter(inputSet[0][0].location[0], inputSet[0][0].location[1], 16)
    l = 0
    #colors = iter(cm.rainbow(np.linspace(0, 1, len(inputSet))))
    for List in inputSet:
        color=colours[l]
        for modem in List:
            gmap.marker(modem.location[0], modem.location[1], color=color)
        l = l+1
    gmap.draw('corGroups.html')
    
    

##############################################################################
################################# SIDE TINGS #################################
################################# SIDE TINGS #################################
##############################################################################
"""
think of it as the sandpit
"""
def orderByICFR(inputList, worstFirst):
    disableFigWarn()
    objList = inputList
    objList.sort(key=lambda x: x.metrics[5], reverse = worstFirst)
    tableList = []
    
    for i in range(len(objList)):
        if objList[i].getICFR() >= 2:
            tableList.append([objList[i].mac] + [objList[i].up] + [objList[i].metrics[1]] + 
            [objList[i].metrics[6]]+[objList[i].metrics[5]]
            +[round(objList[i].vTDR(),1)])
            plt.figure(i)
            plt.subplot(211)
            plt.title(objList[i].mac)
            inputList[i].pltICFR()
            plt.subplot(212)
            inputList[i].pltAmp(212)
        
    
    print tabulate(tableList, headers=['Mac Address','US','MTC', 'MTR','ICFR', 'vTDR'], tablefmt='orgtbl')
    plt.show

def orderByICFR2(modemList, worstFirst):
    disableFigWarn()  
    tableList = []
    objList = modemList
    objList2 = getWorstICFR(objList, 2)
    objList2.sort(key=lambda x: x.metrics[5], reverse = worstFirst)
    objList3 = [x for x in objList if x not in objList2]
    print objList3[10].mac
    
    completeResponse(objList)
    completeResponse(objList3)
    completeResponse(objList2)
    
    for i in range(len(objList2)):
        modem = objList2[i]
        tableList.append([modem.mac] + [modem.up] + [modem.metrics[1]] + 
        [modem.metrics[6]]+[modem.metrics[5]]
        +[round(modem.vTDR(),1)])
        plt.figure(i)
        plt.subplot(211)
        plt.title(modem.mac + " - " + modem.up)
        modem.pltICFR()
        plt.subplot(212)
        modem.pltAmp(212)
    
    print tabulate(tableList, headers=['Mac Address','US','MTC', 'MTR','ICFR', 'vTDR'], tablefmt='orgtbl')
    plt.show     

def worstInDict(inputDict, worstFirst):
    objList = []
    for key in inputDict: 
        inputDict[key].sort(key=lambda x: x.metrics[5], reverse = worstFirst)
        objList.append(inputDict[key][0])
    
    objList.sort(key=lambda x: x.metrics[5], reverse = worstFirst)
    return objList

def getWorstICFR(inputList, severity):
    objList = [] 
    for obj in inputList:
        if obj.getICFR() >= 2: objList.append(obj)
    return objList
    
def groupHighTap(inputGroup):
    loader = {}
    for modem in inputGroup:
        highTaps = modem.getHighTaps()
        if len(highTaps) > 0:
            for i in range(len(highTaps)):
                if highTaps[i][0] >= 12:
                    try:
                        loader[i].append(highTaps[i][0])
                    except(KeyError):
                        loader[i] = []
                        loader[i].append(highTaps[i][0])
    
    return loader

def testCorrelation(targetObject, compareList, strength):
    labs = CableLabs.Eq()
    reference = targetObject
    results = []
    MTR = reference.metrics[6]
    
    for i in range(len(compareList)):
        if reference.mac in compareList[i].mac:
            pass
        else:
            condition = labs.modemMatcher(reference, compareList[i], strength)
            if condition is True:   
                results.append(compareList[i])
                MTR = MTR + compareList[i].metrics[6]
        
    if len(results) > 0:    
        results.append(reference)
    
    groupAnalyser(results)
    
def corTable(corSet):
    colLabels = ('Mac', 'MTC', 'ICFR', 'Amp')
    colWidths = [0.25, 0.25, 0.25, 0.25]
    data = []
    
    
    for item in corSet: 
        data.append([item.mac, item.metrics[1], item.metrics[5], item.amp])
    
    the_table = plt.table(cellText=data,rowLoc = 'left', colLoc='left', cellLoc='left',
              colLabels=colLabels,
              loc='right', colWidths = colWidths, fontsize = 20)

def corPrintT2(correlationSet):
    disableFigWarn()
    colLabels = ('Mac', 'MTC', 'ICFR', 'Amp')
    colWidths = [0.25, 0.25, 0.25, 0.25]
    for i in range(len(correlationSet)):
        data = []
        plt.figure(i, figsize=(10,8))
        groupMTR = 0
        for l in range(len(correlationSet[i])):
            modem = correlationSet[i][l]
            plt.plot(range(128), modem.ICFRdataAmp, label=modem.mac + ": MTR- " + str(round(modem.metrics[6],2)) + ", " + str(modem.amp))
            groupMTR = groupMTR + modem.metrics[6]
            data.append([modem.mac, modem.metrics[1], modem.metrics[5], modem.amp])
        plt.ylim(-4,4)
        plt.xlim(0,128)
        #plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
        plt.title("Correlation Group: " + str(i+1) + ", Macs - " + str(len(correlationSet[i])) + ", MTR - " + str(round(groupMTR/float(len(correlationSet[i])), 2)))
        the_table = plt.table(cellText=data,rowLoc = 'left', colLoc='left', cellLoc='left',
                  colLabels=colLabels,
                  loc='right', colWidths = colWidths)
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(20)        
        #plt.savefig("Correlation Group" + str(i+1))
        #plt.clf()
    plt.show() 
    
def correlationTest(inputList, SPhase, SNorm):
    print "######### HAVE YOU REMEMBERED ASSIGNMENT??? ######### "
    sys.stdout.flush()
    worker = CableLabs.Eq()
    start_time = time.time()
    modems = inputList
    macsTested = []
    correlationSet = []
    correlationFlag = False
    correlationCount = 0
    
    for i in range(len(modems)):
        modem = modems[i]
        temp = []
        correlationFlag = False
        
        if modem.mac in macsTested:
            pass
        else:
            for l in range(len(modems)):
                if modem.mac == modems[l].mac or modems[l].mac in macsTested:
                    pass
                else: 
                    condition = worker.modemMatcher(modem, modems[l], SNorm)
                    #condition1 = correlationcoef(modem.ICFRdataAmp, modems[l].ICFRdataAmp)
                    condition2 = correlationcoef(modem.ICFRdataPhase, modems[l].ICFRdataPhase)
                    if condition2 > S2 and condition:
                        temp.append(modems[l])
                        macsTested.append(modems[l].mac)
                        correlationCount += 1
                        correlationFlag = True
            
            if correlationFlag is True: 
                temp.append(modem)
                correlationCount +=1 
                
            if len(temp) != 0: 
                correlationSet.append(temp)
                
            macsTested.append(modem.mac)
        
    print("--- %s seconds ---" % (time.time() - start_time))
    corPrint2(correlationSet)
    print  ("Correlated: " + str(correlationCount) + " - Groups: " + str(len(correlationSet)))   
    return correlationSet

def corPrint2(correlationSet):
    disableFigWarn()
    for i in range(len(correlationSet)):
        plt.figure(i, figsize=(10,8))
        groupMTR = 0
        for l in range(len(correlationSet[i])):
            plt.subplot(211)
            plt.plot(range(128), correlationSet[i][l].ICFRdataAmp, label=correlationSet[i][l].mac + ": MTR- " + str(round(correlationSet[i][l].metrics[6], 4)))
            plt.ylim(-4,4)
            plt.xlim(0,128)            
            plt.subplot(212)
            plt.ylim(-.4,.4)
            plt.xlim(0,128)  
            plt.plot(range(128), correlationSet[i][l].ICFRdataPhase)
            groupMTR = groupMTR + correlationSet[i][l].metrics[6]
        plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
        plt.title("Correlation Group: " + str(i+1) + ", Macs - " + str(len(correlationSet[i])) + ", MTR - " + str(round(groupMTR/float(len(correlationSet[i])), 2)))
        #plt.savefig("Correlation Group" + str(i+1))
        #plt.clf()
    plt.show() 

def correlationcoef(v1,v2):
    return np.corrcoef(np.array((v1, v2)))[0, 1]
    
def testMatch(number):
    labs = CableLabs.Eq()
    test1 = macSearch('a021b72a52c4','24.4')
    test2 = macSearch('a021b71e7890', '24.4')
    
    return labs.modemMatcher(test1, test2, number)
    
def plotAndSave(inputList):                
    for i in range(len(inputList)):
        inputList[i].printer(i)
        plt.savefig(inputList[i].mac + "-" + inputList[i].up.replace('.', ''))
        plt.clf()

def plotAndPrint(inputList):
    disableFigWarn()
    
    for i in range(10):
        inputList[i].printer(i)
    
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def disableFigWarn():
    plt.rcParams.update({'figure.max_open_warning':0})
    
    
def groupAnalyserP(inputGroup):
    highTaps = groupHighTap(inputGroup)
    MTR = 0
    objsMet = []
    widthTotal = 24
    stepWidth = 1
    sepWidth = 0.9
    ups = inputGroup[0].up
    for MTRvals in inputGroup:  
        MTR += MTRvals.metrics[6] 
        objsMet.append([MTRvals.mac] + [round(MTRvals.metrics[1],4)] + [round(MTRvals.metrics[6],4)]
        + [round(MTRvals.metrics[5],4)] + [round(MTRvals.vTDR(),2)] + [MTRvals.cab])
    
    print '----------------------------------------------------------------'
    print tabulate(objsMet, headers=['Mac Address','MTC','MTR','ICFR','vTDR','Cab'], tablefmt='orgtbl')
    print '----------------------------------------------------------------' 
        
    test = range(0,widthTotal,stepWidth)  
    fig = plt.figure(0, figsize=(20,16))
    
    plt.subplot(211)
    for l in range(len(inputGroup)):
        inputGroup[l].pltICFR()
    #if len(inputGroup)<20:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("GROUP ICFR")
    plt.ylabel("Amplitude (dB)")
    plt.subplot(211).yaxis.set_label_position("right")
    plt.subplot(211).yaxis.label.set_fontsize(30)
  
    plt.subplot(212)
    for l in range(len(inputGroup)):
        bars = inputGroup[l].ampGraph
        for i in range(len(bars)):
            if bars[i] < 0: bars[i] = 0
        for i in range(len(test)): test[i] = test[i]+(sepWidth/float(len(inputGroup)))
        ax=plt.subplot(212)
        ax.bar(test, bars,width=(sepWidth/float(len(inputGroup))),color=cm.jet(1.*l/len(inputGroup)),align='center', label=inputGroup[l].mac)            
        plt.plot(np.arange(0,24,0.5)[1::2], EqObjects.EqAnalyser.limitList2, "o", color='r')        
        plt.ylim([0, 70])
        plt.xlim([0,24])
        locs, labels = plt.yticks()
        labels = [int(item)-70 for item in locs]
        plt.yticks(locs, labels)
        plt.ylabel("Amplitude (dB)")
        ax.yaxis.set_label_position("right")
        ax.yaxis.label.set_fontsize(30)
        ax.plot([0., 24.], [20, 20], linewidth=5, color='g')
    #if len(inputGroup)<20:  plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
    plt.title("GROUP TAP RESPONSE")
    fig.patch.set_facecolor('grey')
    matplotlib.rcParams.update({'font.size': 25})
    matplotlib.rc('xtick', labelsize=25) 
    matplotlib.rc('ytick', labelsize=25) 

    plt.show
    