#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import configparser
import logging
import os
import sys
import time

from datetime import datetime

import aprslib

from aprslib.util import latitude_to_ddm, longitude_to_ddm

CONFIG_FILE = '/etc/aprs_wx.conf'

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

def make_aprs_wx(wind_dir=None, wind_speed=None, wind_gust=None, temperature=None,
                 rain_last_hr=None, rain_last_24_hrs=None, rain_since_midnight=None,
                 humidity=None, pressure=None, position=False):

  wx_fmt = lambda n, l=3: '.' * l if n is None else "{:0{l}d}".format(int(n), l=l)
  if position == True:
    template = '{}/{}g{}t{}r{}p{}P{}h{}b{}'.format
  else:
    template = 'c{}s{}g{}t{}r{}p{}P{}h{}b{}'.format

  return template(wx_fmt(wind_dir),
                  wx_fmt(wind_speed),
                  wx_fmt(wind_gust),
                  wx_fmt(temperature),
                  wx_fmt(rain_last_hr),
                  wx_fmt(rain_last_24_hrs),
                  wx_fmt(rain_since_midnight),
                  wx_fmt(humidity, 2),
                  wx_fmt(pressure, 5))


def w1_read(device):
  """Read the w1 device and return the temperature in Celsius and
  Fahrenheit."""
  with open(device) as fdw:
    for line in fdw:
      if 't=' not in line:
        continue
      _, temp = line.split('=')
      temp = float(temp) / 1000.0
  return temp, ((temp * 1.8) + 32)


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
  logging.info('Read configuration file %s', CONFIG_FILE)
  config = configparser.ConfigParser()
  config.read(CONFIG_FILE)
  try:
    call = config.get('APRS', 'call')
    passcode = config.get('APRS', 'passcode')
    lat = config.getfloat('APRS', 'latitude', fallback=0.0)
    lon = config.getfloat('APRS', 'longitude', fallback=0.0)
    w1_temp = config.get('APRS', 'w1_temp')
    sleep_time = config.getint('APRS', 'sleep', fallback=900)
    position = config.getboolean('APRS', 'position', fallback=False)
  except configparser.Error as err:
    logging.error(err)
    sys.exit(os.EX_CONFIG)

  logging.info('Send weather data %s position', 'with' if position else 'without')

  while True:
    try:
      ais = connect(call, passcode)
      ctemp, ftemp = w1_read(w1_temp)
      logging.info('Current temperature: %.1f°C (%.1f°F)', ctemp, ftemp)
      weather = make_aprs_wx(temperature=ftemp, position=position)
      if position:
        ais.sendall("{}>APRS,TCPIP*:={}/{}_{}X".format(
          call, latitude_to_ddm(lat), longitude_to_ddm(lon), weather
        ))
      else:
        _date = datetime.utcnow().strftime('%m%d%H%M')
        ais.sendall("{}>APRS,TCPIP*:_{}{}".format(call, _date, weather))

      ais.close()
    except IOError as err:
      logging.error(err)
      sys.exit(os.EX_IOERR)
    except Exception as err:
      logging.error(err)

    time.sleep(sleep_time)


if __name__ == "__main__":
  main()
