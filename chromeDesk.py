import urllib2,ctypes,os,random,threading

def extract_img( text ):
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
  return output

def download_img ( img_dict ):
  output = {}
  #Check if download directory exits and make it if not
  if not os.path.exists("Wallpapers"):
    os.makedirs("Wallpapers")
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

    fname = os.path.join("Wallpapers",fname)
    with open(fname,'wb') as f:
      f.write(output[author])
    f.close()
  return output

SPI_SETDESKWALLPAPER = 20 
response = urllib2.urlopen('https://clients3.google.com/cast/chromecast/home')
html = response.read()

#extract the image links
imagelinks = extract_img(html)

#download and save images
imagedb = download_img(imagelinks)

#Get a list of the files in wallpaper directory
wallpapers = os.listdir("Wallpapers")

#Select one at random
rimage = os.path.join("Wallpapers",random.choice(wallpapers))

#Set it as wallpaper
ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, rimage , 0)

