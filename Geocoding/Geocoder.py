# -*- coding: utf-8 -*-
"""
Created on Thu May 19 13:53:36 2016

@author: vince
"""
### My Key: AIzaSyDT2i1GLDJsTZ_RD6H1HqWGAn1RpAXVZ3Y
### Nilans Key: AIzaSyB65Jci79rBoMsoVHhDgToEI5FQi-8oR-w

import sys
sys.path.append('../Eq Analysis')
import csv
import DbConnect
from geopy import geocoders
from collections import defaultdict

def loader(fileName):
    """
    load csv data
    @param fileName - name of file to be loaded
    @return columns - dictionary of key: column name, values: list of column data
    """
    columns = defaultdict(list) 

    with open(fileName) as f:
        reader = csv.DictReader(f) 
        for row in reader: 
            for (k,v) in row.items(): 
                columns[k].append(v)
    
    return columns
    
def saveGeoData(fileName):
    """
    reads & writes over file with the addition of a latitude and longitude column
    @param fileName - name of csv file to be loaded, no extension required
    """
    filename = fileName + '.csv'
    data = loader(filename)
    lats = []
    lons = []
    head = ["Cabinet","Catv Node","Amplifier","Mac Address","Address","Postcode", "Lat", "Long"]; 
    
    for i in range(len(data['Mac Address'])):
        road = data['Address'][i]
        postcode = data['Postcode'][i]
        
        try:
            LatLon = gcode(road + " " + postcode)
            lat = LatLon[0]
            lon = LatLon[1]
        except(AttributeError):
            lat, lon = 0, 0
        
        lats.append(lat)
        lons.append(lon)
        
    with open(filename, 'wb') as fp:
        a = csv.writer(fp)
        a.writerow(head)

        for i in range(len(data['Mac Address'])):
            rowData = []
            rowData = ([data['Mac Address'][i].replace('.',''), data['Catv Node'][i],
                     data['Amplifier'][i], data['Cabinet'][i], data['Address'][i],
                        data['Postcode'][i], lats[i], lons[i]])
                
            a.writerow(rowData)
        
    
def loadServerData(fileName, franchiseName, dbname, dbuser, pwd):
    """
    takes in a file and pushes all its data into a database with the addition of 
    latitude and longitude fields
    @param fileName - name of csv file to be loaded, no extension required
    @param franchiseName - franchise of the node as seen on badger
    """
    filename = fileName + '.csv'
    data = loader(filename)
    dataInsert = list()
    franchise = franchiseName.upper()
    
    for i in range(len(data['Mac Address'])):
        mac = data['Mac Address'][i].replace('.','')
        node = data['Catv Node'][i]
        amp = data['Amplifier'][i]
        cab = data['Cabinet'][i]
        road = data['Address'][i]
        postcode = data['Postcode'][i]
        
        #DEBUG#print road + " " + postcode
        try:
            LatLon = gcode(road + " " + postcode)
            lat = LatLon[0]
            lon = LatLon[1]
        except(AttributeError):
            lat, lon = 0, 0
        #DEBUG#print LatLon
        
        row = {"mac":mac, "node":node, "amp":amp, "cab":cab, "road":road, "postcode":postcode, "lat":lat, "lon":lon, "franchise": franchise}
        dataInsert.append(row)
        
    insertServer(dataInsert, dbname, dbuser, pwd)
    #return dataInsert
    
def insertServer(data, dbname, dbuser, pwd):
    """
    connection to the database to push the geocoded set of data
    @param data - data to be pushed, created in loadServerData
    @param dbname - name of the database to push to
    @param dbuser - user of db
    """
    db = DbConnect.psql(dbname, dbuser, pwd)
    db.insertBatchMac(data)
    
def gcode(address):
    """
    takes an address and retrieves the latitude and longitude coordinates from 
    the google maps geocoding service
    @param address - address in the format: " number road postcode" e.g. "23 Bay Tree Way RG215QG"
    @return tuple of the lat, long coordinates
    """
    g = geocoders.GoogleV3(api_key='AIzaSyDT2i1GLDJsTZ_RD6H1HqWGAn1RpAXVZ3Y')
    inputAddress = address 
    location = g.geocode(inputAddress, timeout=10)
    return (location.latitude, location.longitude)