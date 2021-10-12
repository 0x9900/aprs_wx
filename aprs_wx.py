#!/usr/bin/env python
#
import configparser
import logging
import os
import sys
import time

import aprslib

from aprslib.util import latitude_to_ddm, longitude_to_ddm

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

def make_aprs_wx(wind_dir=None, wind_speed=None, wind_gust=None, temperature=None,
                 rain_last_hr=None, rain_last_24_hrs=None, rain_since_midnight=None,
                 humidity=None, pressure=None):

  wx_fmt = lambda n, l=3: '.' * l if n is None else "{:0{l}d}".format(int(n), l=l)

  return '%s/%sg%st%sr%sp%sP%sh%sb%s' % (
    wx_fmt(wind_dir),
    wx_fmt(wind_speed),
    wx_fmt(wind_gust),
    wx_fmt(temperature),
    wx_fmt(rain_last_hr),
    wx_fmt(rain_last_24_hrs),
    wx_fmt(rain_since_midnight),
    wx_fmt(humidity, 2),
    wx_fmt(pressure, 5)
  )

def w1_read(device):
  with open(device) as fdw:
    for line in fdw:
      if 't=' not in line:
        continue

      _, temp = line.split('=')
      temp = float(temp) / 1000.0
  return ((temp * 1.8) + 32)


def connect(call, password):
  ais = aprslib.IS(call, passwd=password, port=14580)
  for retry in range(5):
    try:
      ais.connect()
    except ConnectionError as err:
      logging.warning(err)
      time.sleep(5 * retry)
    else:
      return ais
  raise IOError('Connection failed')

def main():
  config = configparser.ConfigParser()
  config.read('/etc/aprs_wx.conf')
  try:
    call = config.get('APRS', 'call')
    passcode = config.get('APRS', 'passcode')
    lat = config.getfloat('APRS',  'latitude')
    lon = config.getfloat('APRS',  'longitude')
    w1_temp = config.get('APRS', 'w1_temp')
    sleep_time = config.getint('APRS', 'sleep', fallback=900)
  except configparser.Error as err:
    logging.error(err)
    sys.exit(os.EX_CONFIG)

  from IPython import embed
  embed()
  while True:
    try:
      ais = connect(call, passcode)
      temp = w1_read(w1_temp)
      logging.info('Current temperature: %f', temp)
      weather = make_aprs_wx(temperature=temp)
      ais.sendall("{}>APRS,TCPIP*:={}/{}_{}X".format(
        call, latitude_to_ddm(lat), longitude_to_ddm(lon), weather
      ))
      ais.close()
    except IOError as err:
      logging.error(err)
      sys.exit(os.EX_IOERR)
    except Exception as err:
      logging.error(err)

    time.sleep(sleep_time)

if __name__ == "__main__":
  main()
