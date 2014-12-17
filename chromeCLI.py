#!/usr/bin/env python

"""ChromeCli.py: A simple command like wrapper for ChromeDesk class."""

__author__  = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "2.1"
__email__   = "minos197@gmail.com"

#Import standard libraries
import os
import sys
import time
from optparse import OptionParser

#import ChromeDesk
from chromeDesk import ChromeDesk


if __name__ == "__main__":
  period = 0
  download = ''
  parser = OptionParser()

  parser.add_option( '-t',  action="store",      dest="period",   help = "Period in seconds" )
  parser.add_option( '-d',  action="store",      dest="download", help = "Name of download directory" )
  parser.add_option( '-r',  action="store",      dest="rotation", help = "Rotation mode. 0 = Random , 1 = Increment" )
  parser.add_option( '-c', action="store_true",  dest="cleanup",  help = "(boolean) Delete wallpaper file,after it is replaced " )

  (opts,args) = parser.parse_args()

  #Generate the chromedparser classs
  if opts.period and opts.download:
    chomepsr = ChromeDesk( float( opts.period ), str( opts.download ) )
    print 1,str( str( opts.download ) )
  elif opts.period and not opts.download:
    chomepsr = ChromeDesk( float( opts.period ) )
    print 2
  elif not opts.period and opts.download:
    chomepsr = ChromeDesk( 300 ,str( opts.download ) )
    print 3
  else:
    chomepsr = ChromeDesk()

  #Add extra configuration bits
  if opts.rotation == '0' or opts.rotation == 'random':
    chomepsr.set_image_picker( "random" )
  elif opts.rotation == '1' or opts.rotation == 'incremental' :
    chomepsr.set_image_picker( "incremental" )

  if opts.cleanup:
     chomepsr.set_image_cleanup( True )

  #set the callback to be the change wallpaper method
  chomepsr.attach_periodic_callback(chomepsr.next)

  while ( True ):
    time.sleep(60)