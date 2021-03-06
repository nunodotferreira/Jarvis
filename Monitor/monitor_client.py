import json
import logging
import threading
import Queue
import socket
import logging
from monitor_server import PORT
from mod_pywebsocket.msgutil import MessageReceiver

class MonitorClient():
  TIMEOUT = 1.0

  def __init__(self, ws_request, host, port=PORT):
    self.logger = logging.getLogger(self.__class__.__name__)
    self.logger.setLevel(logging.INFO)
    self.servers = []
    self.q = Queue.Queue()
    self.request = ws_request

    try:
      self.target = socket.create_connection((host,port), timeout=self.TIMEOUT)
      t = threading.Thread(target=self.handle_server)
      t.daemon = True
      t.start()
      self.logger.debug("Connection to %s established" % host)
    except socket.timeout:
      self.logger.error("Connection to %s timed out" % host)
    #except:
    #  self.logger.error("Could not connect to %s:%d" % (host, port))

  def __del__(self):
    self.target.close()

  def send_to_server(self, msg):
    if not msg:
      self.logger.warning("Websocket connection closed")
      self.receiver.stop()
      self.logger.error("TODO: CLOSE TARGET SOCKET")
      return

    if not self.target:
      self.logger.error("Connection closed")
      return

        
    try: 
      self.target.send(msg+"\n")
    except socket.error, e:
      if isinstance(e.args, tuple) and e[0] == errno.EPIPE:
        self.logger.error("Remote \"%s\" disconnected" % (self.target.getpeername()))
      else:
        raise

    self.logger.debug("Sent %s to server" % msg)

  def handle_server(self):
    f = self.target.makefile()
    while True: #TODO: could be done better
      try:
        msg = f.readline()
        if not msg:
          self.logger.warn("Server connection closed")
          return

        self.logger.debug(((msg[:40] + '..') if len(msg) > 40 else msg))
        self.logger.debug("Adding message to queue")
        self.q.put(msg)

      except socket.timeout:
        continue
  
  def handle_print(self):
    # Use when testing, no websockets
    while True:
      try:
        msg = self.q.get(True, 5.0)
      except Queue.Empty:
        continue

      print msg

  def handle_ws(self):
    self.receiver = MessageReceiver(self.request, self.send_to_server)
    while not self.receiver._stop_requested:
      try:
        msg = self.q.get(True, 5.0)
      except Queue.Empty:
        continue
  
      self.request.ws_stream.send_message(msg, binary=False)
      #self.logger.debug("Sent %s" % ((msg[:40] + '..') if len(msg) > 40 else msg))
      self.logger.debug("Sent %s" % msg)


if __name__ == "__main__":
  logging.basicConfig()
  con = MonitorClient(None, socket.gethostname())
  con.handle_print()
