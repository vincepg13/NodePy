# -*- coding: utf-8 -*-
"""
Created on Fri Jul 08 14:16:19 2016

@author: vince
"""

import psycopg2 as db

#PNM, postgres
class psql:
    """
    class to handle the connections between the python model and a PSQL database.
    by default set to localhost. change db origin in connect: host='orgin address'
    """
    
    def __init__(self, dbname, user, pwd):
        self.cursor = self.connect(dbname, user, pwd)

    def connect(self, dbname, user, pwd):
        """
        handles the connection to the database
        @param dbname - name of the databse being connected to
        @param user - the user name for the db, by default is 'postgres'
        @param pwd - password for the databse
        """
        try:
            conn = db.connect("dbname='" + dbname + "' user='" + user + "' host='localhost' password='" + pwd + "'")
            conn.autocommit = True            
            cur = conn.cursor()
            return cur
        except:
            print "failed to connect to database"
    
    def getEqData(self, node, date):
        """
        Query to retrieve eq data
        @param node - the node to request data for
        @param date - the date required
        @return rows - list of lists. each list is one row of data from the query result
                     format: [MAC, US, EQHEX, NODE, AMP, CAB, LAT, LON]
        """
        cur = self.cursor
        try:
            cur.execute("SELECT eq_data.mac, eq_data.us, eq_data.eqHex, mac_info.node, mac_info.amp, mac_info.cab, mac_info.lat, mac_info.lon FROM eq_data JOIN mac_info ON eq_data.mac = mac_info.mac WHERE eq_data.pollDate = '" + date + "' AND mac_info.node LIKE '" + node + "%'")
        except:
            print "query failed"
    
        rows = cur.fetchall()
        return rows
    
    def insertMac(self, dataTup):
        """
        Singular insert of data into mac_info table
        @param dataTup - tuple containing the required data for the table
        """
        cur = self.cursor
        try:
            SQL = "INSERT INTO mac_info VALUES (%s);"
            cur.execute(SQL, dataTup)
        except:
            print "Insert Failed"
            
    def insertBatchMac(self, dataListDict):
        """
        batch insert of data into mac_info table
        @param dataListDict - dictionary containing the required data for insert
        """
        cur = self.cursor
        try:
            SQL = "INSERT INTO mac_info(mac, node, amp, cab, road, postcode, lat, lon, franchise) VALUES(%(mac)s, %(node)s, %(amp)s, %(cab)s, %(road)s, %(postcode)s, %(lat)s, %(lon)s, %(franchise)s );"
            cur.executemany(SQL, dataListDict)
        except:
            print "Batch Insert Failed"
            
    def insertBatchEq(self, dataListDict):
        cur = self.cursor
        try:
            SQL = "INSERT INTO eq_data(mac, us, eqhex, polldate) VALUES(%(mac)s, %(us)s, %(eqhex)s, %(polldate)s );"
            cur.executemany(SQL, dataListDict)
        except:
            print "Batch Insert Failed"
            
    def getLatLon(self, node, franchise):
        cur = self.cursor
        nodeName = node.upper()
        franchiseName = franchise.upper()
        
        try:
            cur.execute("SELECT lat, lon FROM mac_info WHERE node = '" + nodeName + "' AND franchise = '" + franchiseName + "'")
        except:
            print "query failed"
    
        rows = cur.fetchall()
        return rows
            