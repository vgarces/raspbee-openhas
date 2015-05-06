#!/bin/bash
set -e
LOGFILE=/home/pi/flaskr/flaskr.log
LOGDIR=$(dirname $LOGFILE)

cd /home/pi/flaskr
source /home/pi/flaskr/openhas/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn flaskr:app -w 3 -b 0.0.0.0:8000 -D --log-file=$LOGFILE 2>>$LOGFILE
