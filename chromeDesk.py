import urllib2,ctypes,os,random,threading,platform

class ChromeDesk():
  def __init__( self , t_rotation = 300, dl_dir = 'Wallpapers'):
    self.dl_dir      = dl_dir
    self.t_rotation  = t_rotation
    #self.extract_img( self.get_source() )
    self.image_links = None
    self.running     = False
    self.imgp        = 0
    self.choice      = ""
    self.cleanup_flg = False
    self.platform    = ( platform.system(), os.getenv("DESKTOP_SESSION") )

  def get_source( self ):
    return  urllib2.urlopen('https://clients3.google.com/cast/chromecast/home').read()

  def extract_img( self, text ):
    output = {}
    temp   = []

    #Pre proccessing html clean up
    origin = text.find("JSON.parse")
    end_index = text.find(")). constant")
    text = text[origin+19:end_index]
    text = text.replace("\\","")

    while(True):
      #Extract the image URL
      jpeg_start = text.find("https://l")
      jpeg_end = text.find("x22,x22",jpeg_start+1)
      jpeg = text[jpeg_start:jpeg_end]

      #break if find does not 
      if jpeg_start == -1:
        break

      #extract the Author URL
      author_start = jpeg_end+7
      author_end = text.find("x22",author_start+1)
      author = text[author_start:author_end]
      
      #remove the processed data from the string
      text = text[author_end:]
      output[author] = jpeg

    #download the images
    self.download_img(output)
    self.image_links = output
    return output

  def stop_periodic_callback( self ):
    global t1_run_flag
    t1_run_flag = False

  def attach_periodic_callback ( self, cb ):
    global t1_run_flag
    global callback
    global t_cycle

    #set the configuration
    t1_run_flag = True
    callback    = cb
    t_cycle = self.t_rotation

      #Add background processes
    def background_timer():
      import time
      global t1_run_flag
      global callback
      global t_cycle
      ref_time = time.time()
      while ( t1_run_flag ):
        cur_time = time.time()
        if cur_time - ref_time >= t_cycle:
          ref_time = cur_time
          callback()
        if not t1_run_flag: return
        time.sleep(0.5)
    #covert to a thread and start it
    thread = threading.Thread(target=background_timer)
    thread.daemon = True
    thread.start()


  def download_img ( self, img_dict ):
    output = {}
    #Check if download directory exits and make it if not
    if not os.path.exists( self.dl_dir ):
      os.makedirs( self.dl_dir )
    #Go through the links and download->save each of the files
    for author in img_dict.keys():
      img_name = img_dict[author]
      try:
        output[author] = urllib2.urlopen(img_name).read()

      except urllib2.HTTPError:
        print "Image not found in server",img_name
        continue
      fname = img_name[img_name.lower().rfind("/")+1:img_name.lower().find('.jpg')+4]

      #if the image is a JPEG image
      if not len(fname): fname = img_name[img_name.lower().rfind("/")+1:img_name.lower().find('.jpeg')+4]

      #if the image is a PNG image
      if not len(fname): fname = img_name[img_name.lower().rfind("/")+1:img_name.lower().find('.png')+4]

      if not len(fname):
        #if the image has no extension sneak peak in 
        #the binary data for file descriptor
        newtype = ""
        if "JFIF" in output[author][:15]:
          newtype = '.jpg'
        elif "PNG" in output[author][:15]:
          newtype = '.png'
        #Compose the new filename
        fname = img_name[img_name.lower().rfind("/")+1:]+ newtype

      #If image is of another type
      if not len(fname): 
        print "Error processing image type: ",img_name
        continue

      #Append author
      idx = fname.index('.')
      fname = fname[:idx] + "_by_" + author + fname[idx:]

      #replace chars to make the naming more readable
      fname = fname.replace(" ","_")
      fname = fname.replace("%","_")

      fname = os.path.join( self.dl_dir ,fname)
      with open(fname,'wb') as f:
        f.write(output[author])
      f.close()
    return output

  def set_image_cleanup ( self,mode ):
    self.cleanup_flg = mode

  def set_image_picker ( self, mode ):
    sup_modes = { 'random':0, 'incremental':1 }
    if mode in sup_modes.keys():
      self.imgp = sup_modes[mode]

  def cleanup ( self , filename):
    if self.cleanup_flg:
      file = os.path.join( self.dl_dir, filename)
      os.remove(file)

    #if no images left in directory download new ones
    if not os.listdir( self.dl_dir ):
      self.image_links = self.extract_img( self.get_source() )

  def image_picker ( self ):
    old_file = ''
    #keep a copy of the current filename
    if self.choice:
      old_file = self.choice

    #Get a list of the files in wallpaper directory
    wallpapers = os.listdir( self.dl_dir )
    if self.imgp == 0:
      #Select one at random
      self.choice = random.choice( wallpapers )

    elif self.imgp == 1:
      try:
        self.choice = wallpapers[wallpapers.index(self.choice)+1]
      #If the first time it runs or index overflow
      except (IndexError,ValueError):
        self.choice = wallpapers[0]
      #Compose the path

    if old_file and self.choice:
      self.cleanup( old_file )
    return os.path.join( self.dl_dir, self.choice )

  def next( self ):
    #If the images have not been downloaded yet
    if not ( self.image_links ):
      self.image_links = self.extract_img( self.get_source() )

    #Select the next image file
    rimage = self.image_picker()
    self.change( rimage )

  def change( self, rimage ):
    print "Changing Wallpaper"
    if self.platform[0] == "Windows":
      SPI_SETDESKWALLPAPER = 20 

      #Set it as wallpaper
      ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, rimage , 0)
    elif self.platform[0] == "Linux":
      window_manager = self.platform[1]
      rimage = os.path.abspath(rimage)
      if 'gnome' in window_manager:
        command = 'gconftool-2 -t string -s /desktop/gnome/background/picture_filename %s' % rimage
      elif 'kde' in window_manager:
        command = 'dcop kdesktop KBackgroundIface setWallpaper %s 1' % rimage
      elif "ubuntu" in window_manager:
        command = "gsettings set org.gnome.desktop.background picture-uri file:///%s" % rimage
      os.system(command)
      else:
        print "Unrecognised Desktop Environment %s"%window_manager
    else:
      print "Unrecognised platform %s"%self.platform[0]

if __name__ == '__main__':
  cd = ChromeDesk()
  cd.next()
