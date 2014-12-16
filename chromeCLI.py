import os,sys,time,threading
from optparse import OptionParser
from chromeDesk import ChromeDesk

def test():
  print "Test Running"

if __name__ == "__main__":
  period = 0
  download = ''
  parser = OptionParser()

  parser.add_option( '-t',  action="store",      dest="period",       help = "Period in seconds" )
  parser.add_option( '-d',  action="store",      dest="download",     help = "Name of download directory" )
  parser.add_option( '-r',  action="store",      dest="rotation",     help = "Rotation mode. 0 = Random , 1 = Increment" )
  parser.add_option( '-c', action="store_true",  dest="cleanup",      help = " (boolean) Delete wallpaper file,after it is replaced " )

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
  if opts.rotation == 0:
    chomepsr.set_image_picker( "random" )
  elif opts.rotation == 1:
    chomepsr.set_image_picker( "incremental" )

  if opts.cleanup:
     chomepsr.set_image_cleanup( True )

  chomepsr.attach_periodic_callback(chomepsr.next)
  #chomepsr.stop_periodic_callback()
  while ( True ):
    time.sleep(60)