"""RaspBee
Modulo para operar el XBee Coordinador OpenHAS ZigPi
Utilizando las librerias xbee, sqlite3, serial y datetime"""
from xbee import ZigBee
from datetime import datetime
import serial
import sqlite3

def xbeeCONNECT(): 
    "Devuelve un objeto ZigBee coordinador"
    ser = serial.Serial('/dev/ttyAMA0', 9600)
    ser.flushInput()
    return ZigBee(ser)

def xbeeAT(xb,comm="ND"): 
    "Node Discovery Command"
    xb.at(command=comm)
    
def xbeeREMOTEAT(xb,dest='\x00\x00\x00\x00\x00\x00\xff\xff',comm="IS",param=None):
    "Comando Remoto ZigBee"
    xb.remote_at(dest_addr_long=dest,command=comm,parameter=param)
    	
def DBData(packet): 
    "Guardar los datos de pines de estado en la base de datos."
    if "source_addr" in packet:
        srclong = packet["source_addr_long"]
        srclong = srclong.encode('hex')
        print 'add data desde 0x',srclong
        if "samples" in packet:
            packet = packet["samples"]
            sampl = dict(packet[0])
            if 'adc-1' in sampl:
                adc1 = sampl["adc-1"]
            else:
                adc1 = None
            if 'adc-2' in sampl:
                adc2 = float(sampl["adc-2"])
                print adc2,' bin'
                adc2 = float((((adc2*1200/1023)-100)/10)-40)
                print adc2,' grados C'
            else:
                adc2 = None
            if 'adc-3' in sampl:
                adc3 = sampl["adc-3"]
            else:
                adc3 = None
            if 'dio-4' in sampl:
                dio4 = sampl["dio-4"]            
            else:
                dio4 = None
            if 'dio-6' in sampl:
                dio6 = sampl["dio-6"]
            else:
                dio6 = None
            if 'dio-10' in sampl:
                dio10 = sampl["dio-10"]
            else:
                dio10 = None
            if 'dio-11' in sampl:
                dio11 = sampl["dio-11"]

            else:
                dio11 = None
            t=datetime.now()
            print t
        else:               
            pass
        try:
	    db = sqlite3.connect('/home/pi/flaskr/OpenHAS.db')
            curs = db.cursor()
            curs.execute("""BEGIN""")
            curs.execute("""INSERT INTO Datas (addr,datetime,Luz,Temp,SensorAnalogo,Actuador,SensorDigi1,Interruptor,SensorDigi2) VALUES ((?),(?),(?),(?),(?),(?),(?),(?),(?))""", [(srclong),(t),(adc1),(adc2),(adc3),(dio4),(dio6),(dio10),(dio11)])
            db.commit()
            
        except sqlite3.OperationalError:
            print "Database Locked While Datasing"
            pass
    else:
        pass

def getZone(src): 
    "Obtener la ubicacion [Zone] de un nodo desde la base de datos segun una direccion de red ZigBee [addr]"
    try:
        db = sqlite3.connect('/home/pi/flaskr/OpenHAS.db')
        curs = db.cursor()
        curs.execute("""BEGIN""")
        zone=curs.execute("""select zone from NodesInfo where addr=(?)""", [src])
        db.commit()
        zone=zone.fetchall()[0]
        zone=str(zone[0])
        print src, " Getting zone: ",zone 
        return zone
    except IndexError:
        return "None"


def getDataNames(src): 
    "Obtener el nombre de los sensores adicionales de un nodo desde la base de datos, segun su direccion de red ZigBee."
    try:
        db = sqlite3.connect('/home/pi/flaskr/OpenHAS.db')
        curs = db.cursor()
        curs.execute("""BEGIN""")
        adc3=curs.execute("""select adc3 from NodesInfo where addr=(?)""", [src])
        adc3=adc3.fetchall()[0]
        dio6=curs.execute("""select dio6 from NodesInfo where addr=(?)""", [src])
        dio6=dio6.fetchall()[0]
        dio11=curs.execute("""select dio11 from NodesInfo where addr=(?)""", [src])
        db.commit()
        dio11=dio11.fetchall()[0]
        return [(adc3[0]), (dio6[0]), (dio11[0])]
    except IndexError:
        return   [('SensorAnalog'),('SensorDig1'),('SensorDig2')]

def DBNodes(packet): 
    "Obtiene la informacion de un nodo nuevo o un nodo existente donde se ha presionado el Comissioning Button o si se ha solicitado un node Discovery, y la guarda en la base de datos."
    print packet["id"]
    t=datetime.now()
    if "parameter" in packet:
	packet=packet["parameter"]
        srclong = packet["source_addr_long"]
        srclong = srclong.encode('hex')
        name = packet["node_identifier"]
    elif "node_id" in packet:
        srclong = packet["source_addr_long"]
        srclong = srclong.encode('hex')
	name = packet["node_id"]
    elif "node_identifier" in packet:
        srclong = packet["source_addr_long"]
        srclong = srclong.encode('hex')
        name = packet["node_identifier"]
    else:        
        srclong = packet["source_addr_long"]
        srclong = srclong.encode('hex')
        name = packet["node_identification"]
    db = sqlite3.connect('/home/pi/flaskr/OpenHAS.db')
    curs = db.cursor()
    curs.execute("""BEGIN""")
    while(True):
        try:
            curs.execute("""INSERT OR REPLACE INTO Nodes(addr,name,datetime) values((?),(?),(?))""", [(srclong),(name),(t)])
            curs.execute("""INSERT OR IGNORE INTO NodesInfo(addr) values(?)""",[srclong])
            db.commit()    
            break
        except sqlite3.OperationalError:
            print "Database Locked while DBNoding"
    print "DBNodes: Nuevo nodo ->",name," SourceAddr ->", srclong
