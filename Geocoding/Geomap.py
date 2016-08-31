# -*- coding: utf-8 -*-
"""
Created on Fri May 20 09:18:12 2016

@author: vince
"""
from collections import defaultdict
import csv
import gmplot
import sys
sys.path.append('../Eq Analysis')
import DbConnect 

def loader(fileName):
    """
    load csv data
    @param fileName - name of file to be loaded
    @return columns - dictionary of key: column name, values: list of column data
    """
    fileName = fileName + '.csv'
    columns = defaultdict(list) 

    with open(fileName) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)
    
    return columns

def loaderSQL(dbname, dbuser, pwd, node, franchise):
    """
    load latitude and longitude data from the SQL db
    @param dbname - name of database
    @param dbuser - corresponding user for database
    @param node - name of node to grab information from
    @param franchise - badger franchise of node
    @return db.getLatLon - list of row elements [lat,lon]
    """
    db = DbConnect.psql(dbname, dbuser, pwd)
    return db.getLatLon(node, franchise)

def plotGMapDb(dbname, dbuser, pwd, node, franchise):
    """
    loads location data from db and plots it to a html file
    @param dbname - name of database
    @param dbuser - corresponding user for database
    @param node - name of node to grab information from
    @param franchise - badger franchise of node
    """
    data = loaderSQL(dbname, dbuser, pwd, node, franchise)
    gmap = gmplot.GoogleMapPlotter(data[0][0], data[0][1], 16)
    tracker = set()
    counter = {}
    for pair in data:
        element = pair
        
        tracker.add(element)
        
        try:
            counter[element] += 1
        except(KeyError):
            counter[element] = 0
            counter[element] += 1
    
    for count in counter:
        if counter[count] >= 10: 
            gmap.marker(count[0], count[1], color = 'b')
            print count 
            print counter[count]
    
    for pair in data:
        element = pair
        
        if counter[element] < 10:
            gmap.marker(element[0], element[1], color = "#7FFF00")
    
    gmap.draw(node + '.html')

def plotGMapCsv():
    """
    loads location data from csv and plots it to a html file
    @param dbname - name of database
    @param dbuser - corresponding user for database
    @param node - name of node to grab information from
    @param franchise - badger franchise of node
    """
    data = loader()
    gmap = gmplot.GoogleMapPlotter(data['Lat'][0], data['Long'][0], 16)
    tracker = set()
    counter = {}
    step = 0.00009
    for i in range(len(data['Latitude'])):
        lat = float(data['Latitude'][i])
        lon = float(data['Longitude'][i])
        element = (lat,lon)
#        
#        if element in tracker and counter[element] > 4:
#            gmap.marker(lat, lon, color = 'b')
        #else:
         #   gmap.marker(lat, lon, color = "#7FFF00")
        #gmap.marker(lat, lon, color = "#7FFF00")
        
        tracker.add(element)
        
        try:
            counter[element] += 1
        except(KeyError):
            counter[element] = 0
            counter[element] += 1
    
    for count in counter:
        if counter[count] >= 10: 
            gmap.marker(count[0], count[1], color = 'b')
            print count 
            print counter[count]
    
    for i in range(len(data['Latitude'])):
        lat = float(data['Latitude'][i])
        lon = float(data['Longitude'][i])
        element = (lat,lon)
        
        if counter[element] < 10:
            gmap.marker(lat, lon, color = "#7FFF00")
        
    gmap.draw('location.html')
    
    

