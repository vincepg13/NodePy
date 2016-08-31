# -*- coding: utf-8 -*-
"""
Created on Thu Jun 02 10:58:30 2016

@author: vince
"""
import sys
sys.path.append('C:/Users/vince/Documents/Python/Code Lab/Pre-Eq/Eq Analysis')
import DbConnect 
import csv
import os
from collections import defaultdict

def loader(csvFile):
    """
    standard function to load data from a csv
    @param csvFile - the name of the csvFile to be loaded
    @return columns - the csv data parsed into a dictionary, each column header is they key
    """
    columns = defaultdict(list)
    with open(csvFile) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                if len(v) == 0:
                    columns[k].append(v)  
                else:
                    columns[k].append(v.replace('.',''))  
    return columns
    
def combiner(billingName):
    """
    combine an eqData csv with a billing csv to form a csv input for node inspector
    @condition - put the files you want to combine into the file formatting folder, have only these files in there
    @param billingName - the name of the csv from badger, no extension required
    """
    billingName = billingName + '.csv'
    cabData = loader(billingName)
    for csvFile in os.listdir(os.getcwd()):
        eqData = {}
        if csvFile.endswith('.csv') and csvFile != billingName:
            eqData = loader(csvFile)
                
            with open(csvFile, 'wb') as fp:
                a = csv.writer(fp)
                a.writerow(['Mac','US','EqHex','Node','Amp','Cab','Lat','Long'])
                
                for i in range(len(eqData['Mac'])):
                    data = []
                    data = ([eqData['Mac'][i], eqData['US'][i], eqData['EqHex'][i]])
                    try:                    
                        indexPosCab = cabData['Mac Address'].index(eqData['Mac'][i].upper())
                        data = data + [cabData['Catv Node'][indexPosCab], cabData['Amplifier'][indexPosCab], cabData['Cabinet'][indexPosCab]]
                    except(ValueError):
                        data = data + ['NULL', 'NULL', 'NULL']
                    try:
                        indexPosLoc = cabData['Mac Address'].index(eqData['Mac'][i].upper())
                        data = data + [cabData['Lat'][indexPosLoc], cabData['Long'][indexPosLoc]]
                    except(ValueError, IndexError):
                        data = data     
                    a.writerow(data)          

def psqlEqServer(dbname, dbuser, pwd):  
    """
    loops through eq csv files and inserts rows into database. csv file must have
    date at the end as ddmm
    @param dbname - database name, e.g. 'PNM'
    @param dbuser - user for db, e.g. 'postgres'
    @param pwd - password for db
    """
    db = DbConnect.psql(dbname, dbuser, pwd)
    for csvFile in os.listdir(os.getcwd()):
        if csvFile.endswith('.csv'):
            data = []
            columns = loader(csvFile) 
            date = csvFile.replace('.csv', '')
            date = date[len(date)-4:]
            polldate = '2016-' + date[2] + date[3] + '-' +  date[0] + date[1]
            
            for i in range(len(columns['Mac'])):
                mac = columns['Mac'][i].upper()
                if len(mac) == 12:
                    us = columns['US'][i]
                    eqhex = columns['EqHex'][i]
                    row = {"mac":mac, "us":us, "eqhex":eqhex, "polldate":polldate}
                    data.append(row)
                else:
                    pass
                
            db.insertBatchEq(data)     
            print "succesful- " + csvFile
    
def psqlEqCsv():
    """
    loops through eq csv files and formats them to the same format as db for file upload
    """
    for csvFile in os.listdir(os.getcwd()):
        if csvFile.endswith('.csv'):
            columns = defaultdict(list)  
            date = csvFile.replace('.csv', '')
            date = date[len(date)-4:]
            polldate = '2016-' + date[2] + date[3] + '-' +  date[0] + date[1]
            
            with open(csvFile) as f:
                reader = csv.DictReader(f) 
                for row in reader: 
                    for (k,v) in row.items(): 
                        columns[k].append(v)  
            
            with open(csvFile, 'wb') as fp:
                a = csv.writer(fp)
                for i in range(len(columns['Mac'])):
                    if len(columns['Mac'][i]) == 12:
                        a.writerow([columns['Mac'][i].upper(), columns['US'][i], columns['EqHex'][i], polldate])            


###############################################################################
###### set of functions below to average inputs. not recommended to use #######
###############################################################################
def average():
    masterData = {}
    data = {}
    data2 = {}
    data3 = {}
    columns = defaultdict(list) 
    for csvFile in os.listdir(os.getcwd()):
        columns = defaultdict(list) 
        if csvFile.endswith('.csv') and csvFile != 'MacLatLong.csv' and csvFile!= 'Mac Cab Details.csv':
            columns = defaultdict(list)      
            with open(csvFile) as f:
                reader = csv.DictReader(f) 
                for row in reader: 
                    for (k,v) in row.items(): 
                        columns[k].append(v)      
            masterData[csvFile] = columns

    for key in masterData:
        for i in range(len(masterData[key]['Mac'])):
            mac = masterData[key]['Mac'][i]
            up = masterData[key]['US'][i]
            eqData = hexBreaker(masterData[key]['EqHex'][i][8:])
            try:
                data[(mac, up)].append(eqData)
            except(KeyError):
                data[(mac, up)] = []
                data[(mac, up)].append(eqData)
    
    for key in data:
        for i in range(len(data[key][0])):
            summer = 0
            for j in range(len(data[key])):  
                summer += data[key][j][i]
            try:
                data2[key].append(intToHex(int(round(summer/float(len(data[key]))))))
            except(KeyError):
                data2[key] = []
                data2[key].append(intToHex(int(round(summer/float(len(data[key]))))))
    
    for key in data2:
        Str = '08011800'
        for val in data2[key]:
            Str = Str + val
        data3[key] = Str
    #return data3
    
    with open("AVG.csv", 'wb') as g:
        rg = csv.writer(g)
        rg.writerow(['Mac', 'US', 'EqHex'])
        
        for key in data3:
            rg.writerow([key[0], key[1], data3[key]])
                
                
    subject = data[('803773024210', '46.2')]
    for l in subject: 
        print str(l[15]) + " and " + str(l[16])
    #print data[('803773024210', '46.2')]
    print data2[('803773024210', '46.2')][15]
    print data2[('803773024210', '46.2')][16]
    
def hexToInt(hexVal):
    i = int(hexVal, 16)
    if i >= 2**15:
        i -= 2**16
    return i

def intToHex(i):
    return ('%06x'%((i+2**16)%2**16))[2:]
    
def hex2dec4N2(hexValue):
    x='0x' + hexValue   
    y = int(x, 16)
    return -(y & 0x8000) | (y & 0x7fff)

def hex2dec3N2(hexValue):
    x='0x' + hexValue   
    y = int(x, 16)
    return -(y & 0x800) | (y & 0x7ff)

def hex2dec(hexValue):
    if hexValue.startswith('0'):
        return hex2dec3N2(hexValue)
    else:
        return hex2dec4N2(hexValue)
    
def scaler(real, imag):
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
    
def hexBreaker(hexString):
    n = 4
    #m = 2
    #head = [hexString[i:i+m] for i in range(0, 6, m)]
    real = [hexString[i:i+n] for i in range(0, len(hexString), n+4)]
    imag = [hexString[i:i+n] for i in range(4, len(hexString), n+4)]
    holder = []
    
    for i in range(len(real)):
        #if i < len(head): head[i] = hex2dec(head[i])
        holder.append([real[i], imag[i]])

    
    scaleFactor = scaler(hex2dec(holder[7][0]), hex2dec(holder[7][1]))
    
    holder2=[]
    for i in range(len(holder)):
        if scaleFactor > 2048:
            holder[i][0] = hex2dec4N2(holder[i][0])#/float(scaleFactor)
            holder[i][1] = hex2dec4N2(holder[i][1])#/float(scaleFactor)
        else:
            holder[i][0] = hex2dec3N2(holder[i][0])#/float(scaleFactor)
            holder[i][1] = hex2dec3N2(holder[i][1])#/float(scaleFactor)
        holder2.append(holder[i][0])
        holder2.append(holder[i][1])
    return(holder2)
    
###############################################################################
########################### old combination method ############################
###############################################################################

def attatchInfo():
    cabData = {}
    locationData = {}
    for csvFile in os.listdir(os.getcwd()):
        if csvFile == 'MacLatLong.csv' or csvFile == 'Mac Cab Details.csv':
            columns = defaultdict(list)      
            with open(csvFile) as f:
                reader = csv.DictReader(f) 
                for row in reader: 
                    for (k,v) in row.items(): 
                        columns[k].append(v)      
            if csvFile == 'MacLatLong.csv':
                locationData = columns
            else:
                cabData = columns
    
    for csvFile in os.listdir(os.getcwd()):
        eqData = {}
        if csvFile.endswith('.csv') and csvFile != 'MacLatLong.csv' and csvFile!= 'Mac Cab Details.csv':
            columns = defaultdict(list)      
            with open(csvFile) as f:
                reader = csv.DictReader(f) 
                for row in reader: 
                    for (k,v) in row.items(): 
                        columns[k].append(v)      
                eqData = columns
                
            with open(csvFile, 'wb') as fp:
                a = csv.writer(fp)
                a.writerow(['Mac','US','EqHex','Node','Amp','Cab','Lat','Long'])
                
                for i in range(len(eqData['Mac'])):
                    data = []
                    data = ([eqData['Mac'][i], eqData['US'][i], eqData['EqHex'][i]])
                    try:                    
                        indexPosCab = cabData['Mac'].index(eqData['Mac'][i].upper())
                        data = data + [cabData['Node'][indexPosCab], cabData['Amp'][indexPosCab], cabData['Cab'][indexPosCab]]
                    except(ValueError):
                        data = data + ['NULL', 'NULL', 'NULL']
                    try:
                        indexPosLoc = locationData['Mac'].index(eqData['Mac'][i].upper())
                        data = data + [locationData['Latitude'][indexPosLoc], locationData['Longitude'][indexPosLoc]]
                    except(ValueError):
                        data = data + ['NULL', 'NULL']      
                    #print data
                    a.writerow(data)     

def formatBadger(fileName):
    File = fileName + '.csv'
    columns = defaultdict(list)
    
    with open(File) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)
    
    with open('Mac Cab Details.csv', 'wb') as fp:
        a = csv.writer(fp)
        a.writerow(['Mac', 'Cab', 'Node', 'Parent', 'Amp'])
        
        for i in range(len(columns['Mac Address'])):
            data = []
            data = [columns['Mac Address'][i].replace('.',''), columns['Cabinet'][i], columns['Catv Node'][i], columns['Physical Parent'][i], columns['Amplifier'][i]]
            a.writerow(data)
    
    with open('LocationInfo.csv', 'wb') as fg:
        b = csv.writer(fg)
        b.writerow(['Mac', 'Road', 'Postcode'])
        
        for j in range(len(columns['Mac Address'])):
            data = []
            data = [columns['Mac Address'][j].replace('.',''), columns['Address'][j], columns['Postcode'][j]]
            b.writerow(data)
            
def psqlFormat(fileName):
    File = fileName + '.csv'
    columns = defaultdict(list)
    locInfo = defaultdict(list)
    
    with open(File) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)

    with open('MacLatLong.csv') as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                locInfo[k].append(v)

    with open('sqlData.csv', 'wb') as fp:
        a = csv.writer(fp)
        #a.writerow(['Mac', 'Node', 'Amp', 'Cab', 'Road', 'Postcode', 'Lat', 'Lon'])
        
        for i in range(len(columns['Mac Address'])):
            data = []
            data = ([columns['Mac Address'][i].replace('.',''), columns['Catv Node'][i],
                     columns['Amplifier'][i], columns['Cabinet'][i], columns['Address'][i],
                        columns['Postcode'][i]])
            try:
                indexPos = locInfo['Mac'].index(columns['Mac Address'][i].upper().replace('.',''))
                data = data + [locInfo['Latitude'][indexPos], locInfo['Longitude'][indexPos]]
            except(ValueError):
                data = data + [0, 0]
                
            a.writerow(data)