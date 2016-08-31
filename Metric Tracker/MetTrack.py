# -*- coding: utf-8 -*-
"""
Created on Tue May 03 11:01:54 2016

@author: vince
"""
############################################################################
# "TTE", "MTC", "NMTER", "PREMTTER", "POSTMTTER", "ICFR", "MTR", "MR", "GD"#
############################################################################
import os
import csv
import time
import matplotlib.pyplot as plt
from collections import defaultdict

class metTrack(object):
    
    def __init__(self, macCabFileName='Mac Cab Details'):
        start_time = time.time()
        self.cabFile = macCabFileName + ".csv"
        loadAndHold = self.dataLoader(self.cabFile)
        self.metricInfo = loadAndHold[0]
        self.cabInfo = loadAndHold[1]
        self.trendData = self.macTrendData(loadAndHold[0])
        self.variationData = self.metricVariation(loadAndHold[0])
        self.severeMacs = self.severity(self.variationData)
        print("Compilation Time --- %s seconds ---" % (time.time() - start_time))
        
    def dataLoader(self, cabFileName):
        csvList = []
        master = {}
        columns = defaultdict(list) 

        with open(cabFileName) as f:
            reader = csv.DictReader(f) 
            for row in reader: 
                for (k,v) in row.items(): 
                    columns[k].append(v)
    
        for csvFile in os.listdir(os.getcwd()):
            if csvFile.endswith(".csv") and csvFile != cabFileName: 
                with open(csvFile) as f:
                    reader = csv.reader(f)
                    csvList.append(list(reader)[1:])
                    
        for fileList in csvList:
            for item in fileList:
                try:
                    master[(item[0], item[1])].append(map(float, item[2:len(item)]))
                    #print item[2:]
                except(KeyError):
                    master[(item[0], item[1])] = []
                    master[(item[0], item[1])].append(map(float, item[2:len(item)]))
        
        return (master, columns)

    def macTrendData(self, metricData):
        allMacs = {}
        
        for key in metricData:
            result = {}
            result['TTE'] = self.column(metricData[key], 0)
            result['MTC'] = self.column(metricData[key], 1)
            result['NMTER'] = self.column(metricData[key], 2)
            result['PREMTTER'] = self.column(metricData[key], 3)
            result['POSTMTTER'] = self.column(metricData[key], 4)
            result['ICFR'] = self.column(metricData[key], 5)
            result['MTR'] = self.column(metricData[key], 6)
            result['MR'] = self.column(metricData[key], 7)
            result['GD'] = self.column(metricData[key], 8)
            allMacs[key] = result
            
        return allMacs 

    def metricVariation(self, metricData): 
        results = {}          
        for key in metricData:
            results[key] = []
            for l in range(len(metricData[key][0])):
                temp = []
                for i in range(len(metricData[key])):
                    temp.append(float(metricData[key][i][l]))
                results[key].append(round(max(temp) - min(temp), 3))
        
        return results
        
    def severity(self, variation):
        result = {}
        for key in variation:
            if variation[key][6] > 3 or variation[key][5] > 1:
                result[key] = variation[key]
                
        return result

    def column(self, matrix, i):
        return [row[i] for row in matrix]
        
    
    def macTrend(self, mac, us, fignum):
        master = self.trendData
        result = master[(mac,str(us))]
        i = 0
        
        fig = plt.figure(fignum)
        plt.xticks([])
        plt.yticks([])
        plt.title(mac + ": " + str(us), y=1.05)
        
        for metric in result:
            data = result[metric]
            if metric == 'MTR' or metric == 'MR' or metric == 'GD':
                #plt.figure(i)
                ax = fig.add_subplot(int("31" + str(i+1)))
                ax.scatter(range(len(data)), data)
                
                ax.set_title(metric)
                if max(data) - min(data) > 3: #or (metric == 'ICFR' and max(data) - min(data) > 1): 
                    ax.plot(range(len(data)), data, color='r')
                else:
                    ax.plot(range(len(data)), data)
                ax.set_xticklabels([])
                
                #plt.title("Variation of metric: " + metric)
                
                if metric == 'NMTER' or metric == 'MTR' or metric == 'PREMTTER' or metric == 'POSTMTTER' or metric == 'MR' or metric == 'GD':
                    plt.ylim([min(data)-5, max(data)+5])
                elif metric == 'MTC':
                    plt.ylim([min(data)-0.01, max(data)+0.01])
                elif metric == 'ICFR':
                    plt.ylim([min(data)-1, max(data)+1])
                elif metric == 'TTE':
                    plt.ylim([min(data)-0.1, max(data)+0.1])
                    
                i = i+1
            
        plt.show
    
    def macTrendSingle(self, mac, us, fignum):
        master = self.trendData
        result = master[(mac,str(us))]
        i = 0
        Max, Min = 0,100
        for metric in result:
            plt.figure(fignum)
            data = result[metric]
            if metric == 'MTR' or metric == 'MR' or metric == 'GD':  
                if max(data) > Max: Max = max(data)
                if min(data) < Min: Min = min(data)  
                plt.plot(range(len(data)), data, label=metric)
                plt.scatter(range(len(data)), data)
            i = i+1
        
        plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., prop={'size':20})
        plt.ylim([Min-5, Max+5])  
        plt.title(mac + ": " + str(us))
        plt.show

    def printSevere(self):
        severityKeys = self.severeMacs
        
        i = 0
        for key in severityKeys:
            #self.macTrend(key[0], key[1], i)
            self.macTrendSingle(key[0], key[1], i)
            i = i+1
            
        return i 
    
    def severeCount(self):
        severe = self.severeMacs
        unique = set()
        for modem in severe: unique.add(modem[0])
        return [len(unique), len(severe)]

    def printAll(self):
        allKeys = self.metricInfo
        
        i = 0
        for key in allKeys:  
            self.macTrend(key[0], key[1], i)
            i = i+1            

                
