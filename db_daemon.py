#!/usr/bin/python
#Daemon - Lee todos los packetes que llegan, los clasifica y decide que hacer con cada uno de ellos.
from RaspBee import *
import sys

#Daemon CONFIG

import logging
import logging.handlers
import argparse
import sys


# Deafults
LOG_FILENAME = "/tmp/db_daemon.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="OpenHAS simple Python Data Base Daemon")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
	LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


##INICIO DEL LOOP PRINCIPAL
try:
    xb=xbeeCONNECT()
    print "Connected"
except RuntimeError:
    print "Error al conectarse con el modulo ZigBee, por favor vuelva a conectarlo y reinicie el sistema."

while True:
    try:
        packet = xb.wait_read_frame()
    except KeyError:
        continue
    if packet['id']=='node_id_indicator':
        DBNodes(packet)
    elif packet['id']=='at_response':          
        DBNodes(packet)
    elif packet['id']=='rx_io_data_long_addr':
        DBData(packet)
    else:
        continue
