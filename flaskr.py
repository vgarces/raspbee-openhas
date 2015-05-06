#!/usr/bin/python
import sqlite3, serial
from xbee import ZigBee
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug.contrib.fixers import ProxyFix
import RaspBee as has
from contextlib import closing
#conf
DATABASE = '/home/pi/flaskr/OpenHAS.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

#app
app = Flask(__name__)
app.config.from_object(__name__)

def IS():
    xb=has.xbeeCONNECT()
    has.xbeeREMOTEAT(xb)

           
def updateName(src,name):
    print src,name,"UPDATENAME",src.decode('hex')
    xb=has.xbeeCONNECT()
    src=src.decode('hex')
    xb.remote_at(dest_addr_long=src,command='NI',parameter=name)
    xb.remote_at(dest_addr_long=src,command='WR')
    xb.at(command='ND')

@app.route('/ON', methods={'POST','GET'})
def turnON():
    src=request.form['addr']
    xb=has.xbeeCONNECT()
    xb.remote_at(dest_addr_long=src.decode('hex'),command='D4',parameter='\x05')
    xb.remote_at(dest_addr_long=src.decode('hex'),command='WR')
    print src," on"
    return redirect(url_for('show_nodes'))

@app.route('/OFF', methods={'POST','GET'})
def turnOFF():
    src=request.form['addr']
    xb=has.xbeeCONNECT()
    print src," off"
    xb.remote_at(dest_addr_long=src.decode('hex'),command='D4',parameter='\x04')
    xb.remote_at(dest_addr_long=src.decode('hex'),command='WR')
    return redirect(url_for('show_nodes'))

@app.route('/ND', methods={'POST','GET'})
def run_nodediscovery():
    has.xbeeAT(has.xbeeCONNECT())
    flash('New Node Discovery was succesfully made.')
    return redirect(url_for('show_nodes'))

@app.route('/RST', methods={'POST','GET'})
def run_reset():
    init_db()
    flash('Reset was succesfully made.')
    return redirect(url_for('show_nodes'))

def connect_db():
    return sqlite3.connect(app.config['DATABASE'],timeout=1)
   

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request_():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
    
    
@app.route('/')
def show_nodes():
    while(True):
        try:
            cur = g.db.execute('select addr,name from Nodes order by name')
            nodes = [dict(addr=row[0], name=row[1]) for row in cur.fetchall()]
            for node in nodes:
                cur = g.db.execute('select datetime, Luz, Temp, SensorAnalogo, Actuador, SensorDigi1, Interruptor, SensorDigi2 from Datas where addr=(?) order by id DESC LIMIT 1',[str(node['addr'])])
                row=cur.fetchone()
                node.update(t=row[0], luz=row[1], temp=row[2], sensoranalogo=row[3], actuador=row[4], sensordigi1=row[5], interruptor=row[6], sensordigi2=row[7])
                cur = g.db.execute('select zone, adc3, dio6, dio11 from NodesInfo where addr=(?)',[str(node['addr'])])
	        row=cur.fetchone()
	        node.update(zone=row[0],adc3=row[1],dio6=row[2],dio11=row[3])
            break
        except sqlite3.OperationalError:
            pass

    return render_template('show_nodes.html', nodes=nodes)


@app.route('/rename', methods=['POST'])
def rename_node():
    if not session.get('logged_in'):
        abort(401)
    addr=request.form['addr']
    rename=str(request.form['rename'])
    updateName(addr,rename)
    zone = str(request.form['zone'])
    dio6 = str(request.form['dio6'])
    dio11 = str(request.form['dio11'])
    adc3 = str(request.form['adc3'])
    print addr,zone,rename, dio6
    while(True):
        try:
            g.db.execute('update NodesInfo set zone=(?),adc3=(?),dio6=(?),dio11=(?) where addr=(?)', [zone,adc3,dio6,dio11,str(addr)])
            g.db.commit()
            break
        except sqlite3.OperationalError:
            print "Database Locked while Zoning"
    flash('New rename was succesfully posted.')
    return redirect(url_for('show_nodes'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username']!=app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password']!=app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_nodes'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.')
    return redirect(url_for('show_nodes'))

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__=='__main__':
    app.run('0.0.0.0',port=8000)
