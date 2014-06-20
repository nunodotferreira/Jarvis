import pygame
import os
import time
import socket

PORT = 9808
SW,SH = 1920, 1080
DELTA = 500
SCALE_DELTA = 10
VSTART = 0
IMW, IMH = SW+2*DELTA, SH+SCALE_DELTA

class ScreenCMD():
  SLIDE_TO = "slideto"
  ZOOM_TO = "zoomto"
  SET_IMG = "setimg"
  SEP = '|'

  @classmethod
  def pack(self, cmd, path):
    return "%s%s%s\n" % (cmd, self.SEP, path)

  @classmethod
  def unpack(self, cmd):
    return cmd.strip().split(self.SEP)

class ScreenServer():
  def __init__(self, host, port=PORT):
    self.s = socket.socket()         # Create a socket object
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.settimeout(0.5)
    self.s.bind((host, port))        # Bind to the port
    self.s.listen(5)                 # Now wait for client connection.
    self.delta = DELTA
    self.last_img = None

    self.cmd_map = {
      ScreenCMD.SLIDE_TO: self.sweep,
      ScreenCMD.ZOOM_TO: self.zoom,
      ScreenCMD.SET_IMG: self.setimg,
    }

    if os.name is not 'nt':
      os.environ["DISPLAY"] = ":0"
    os.environ["SDL_FBDEV"] = "/dev/fb1"
    self.screen = pygame.display.set_mode(
      (SW,SH), 
      pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    self.clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

  def handle_forever(self):
    while True:
      try:
        c, addr = self.s.accept()     # Establish connection with client.
      except socket.timeout:
        pygame.event.pump()
        continue

      print 'Got connection from', addr

      msg = c.recv(1024)
      (cmd,path) = ScreenCMD.unpack(msg)
      self.cmd_map[cmd](loadimg(path))
      c.close()      
      last_img = img

  @classmethod
  def easeInOutQuad(self, currtime, start, delta, duration):
    currtime = float(currtime)
    start = float(start)
    delta = float(delta)
    duration = float(duration)
    currtime /= duration/2;
    # First half of easing
    if (currtime < 1): 
      return delta/2*currtime*currtime + start;

    # Second half of easing
    currtime -= 1; 
    return -delta/2 * (currtime*(currtime-2) - 1) + start;

  def sweep(self, img):
    start = 0
    mid = 50
    overlap = 10
    end = 120
    alpha_end = 150
    img1_start = float(-self.delta)
    img2_start = float(-2*self.delta)

    for i in xrange(start, end):
      v = ScreenServer.easeInOutQuad(i, start, self.delta, end) 

      if i < mid+overlap:
        alpha = i * (alpha_end/float(mid+overlap))  
        self.last_img.set_alpha((alpha_end-alpha))
        self.screen.blit(self.last_img,(img1_start+v,VSTART))
    
      if i > mid-overlap:
        alpha = (i-(mid-overlap)) * (alpha_end/float(end-(mid-overlap)))  
        img.set_alpha(alpha)
        self.screen.blit(img,(img2_start+v,VSTART))
  
      pygame.display.flip()
      pygame.event.pump()
      self.clock.tick(30)

  def zoom(self, img):
    start = 0
    mid = 50
    overlap = 15
    end = 80
    alpha_end = 150
    img1_start = float(-self.delta)
    img2_start = float(-self.delta)
    delta = self.delta / 8
    aspect = float(IMW)/float(IMH)

    for i in xrange(start, end):
      v = ScreenServer.easeInOutQuad(i, start, delta, end) 

      if i < mid+overlap:
        alpha = i * (alpha_end/float(mid+overlap))  
        img1_scale = pygame.transform.smoothscale(img1, (int(aspect*(IMH+v)), int(IMH+v)))
        self.last_img.blit(img1_scale, (-aspect*v/2,-v/2))
        img1_scale.set_alpha((alpha_end-alpha))
        self.screen.blit(img1_scale,(img1_start,VSTART))
      
      if i >= mid-overlap:
        s = i-(mid-overlap)
        alpha = s * alpha_end / float(end-(mid-overlap))
        img2_scale = pygame.transform.smoothscale(img, (int(aspect*(IMH+s)), int(IMH+s)))
        img2_scale.set_alpha(alpha)
        self.screen.blit(img2_scale,(img2_start-aspect*(s/2),VSTART-s/2))
    
      pygame.display.flip()
      pygame.event.pump()
      self.clock.tick(45)

  def setimg(self, img):
    img_start = float(-self.delta)
    self.screen.blit(img, (img_start,VSTART))
    pygame.display.flip()

class ScreenController():
  def __init__(self, host, imgpath="", port=PORT):
    self.host = host
    self.port = port
    self.path = imgpath
    self.last_img = None

  def send_cmd(self, cmd, img):
    if img != self.last_img:
      s = socket.socket()         # Create a socket object
      s.connect((self.host, self.port))
      s.send(ScreenCMD.pack(cmd, path+img))
      s.close()
      self.last_img = img

  def slide_to(self, img):
    self.send_cmd(ScreenCMD.SLIDE_TO, img)

  def set_img(self, img):
    self.send_cmd(ScreenCMD.SET_IMG, img)

  def zoom_to(self, img):
    self.send_cmd(ScreenCMD.ZOOM_TO, img)

def loadimg(path):
  img = pygame.image.load(path).convert()
  img = pygame.transform.scale(img, (IMW,IMH))   
  return img

if __name__ == '__main__':
  host = socket.gethostname() # Get local machine name
  srv = ScreenServer(host)
  srv.handle_forever()
 
