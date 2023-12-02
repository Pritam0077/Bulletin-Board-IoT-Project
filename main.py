import secrets
import time
import network
import socket
import rp2
 
from ubinascii import unhexlify
 
import machine
from machine import I2C
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

LCD_ADDR = 0x27
LCD_NUM_ROWS = 2
LCD_NUM_COLS = 16
LCD_SDA = 16
LCD_SCL = 17
 
i2c = I2C(0, sda=machine.Pin(LCD_SDA), scl=machine.Pin(LCD_SCL), freq=400000)
lcd = I2cLcd(i2c, LCD_ADDR, LCD_NUM_ROWS, LCD_NUM_COLS)
lcd.putstr('Connected to WiFi')
 

rp2.country('IN')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.ssid, secrets.passwd)
 

print('Connecting to WiFi...')
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  time.sleep(1)
 

if wlan.status() != 3:
  raise RuntimeError('could not connect !!!')
 
print('Connected with WiFi')
status = wlan.ifconfig()
ipserv = status[0]
print('ip = ' + ipserv)
lcd.clear()
#lcd.putstr(ipserv)
 

html = """<!DOCTYPE html>
<html>
  <head>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Lora&family=Raleway:wght@300&display=swap"
      rel="stylesheet"
    />
    <title>Smart Notice Board</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
      body {
        font-family: "Lora", serif;
        font-family: "Raleway", sans-serif;
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        height: 100vh;
        text-align: center;
        margin: 0;
        padding: 0;
      }
      @keyframes gradient {
        0% {
          background-position: 0% 50%;
        }
        50% {
          background-position: 100% 50%;
        }
        100% {
          background-position: 0% 50%;
        }
      }
      header {
        background-color: #333;
        color: #fff;
        padding: 10px;
      }
      marquee {
        font-size: 2em;
        color: #e4d5d5;
      }

      h1 {
        font-size: 2em;
        margin: 10px 0 20px;
      }

      form {
        display: inline-block;
        text-align: center;
        margin-top: 20px;
      }

      label {
        font-size: 1.2em;
        display: block;
        margin-bottom: 10px;
      }

      input[type="text"] {
        font-size: 1em;
        padding: 10px;
        width: 250px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        box-sizing: border-box;
      }

      input[type="submit"] {
        font-size: 1.2em;
        padding: 10px 20px;
        background-color: #4caf50;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
      }

      input[type="submit"]:hover {
        background-color: #45a049;
      }

      footer {
        background-color: #333;
        color: #fff;
        padding: 10px;
        position: fixed;
        bottom: 0;
        width: 100%;
      }
    </style>
  </head>
  <body>
    <header>
      <h1>Smart Notice Board</h1>
      <marquee><b>Smart Notice Board</b></marquee>
    </header>
    <form method="post">
      <label for="msg"><b>Message:</b></label>
      <input
        type="text"
        id="msg"
        name="Message"
        placeholder="Enter your message"
      />
      <br />
      <input type="submit" value="Send" />
    </form>
    <footer>&copy; 2023 Smart Notice Board</footer>
  </body>
</html>

    
"""

# Scroll delay in seconds
SCROLL_DELAY = 0.5

def txtDecode(txt):
    res = ''
    i = 0
    while i < len(txt):
        car = txt[i]
        if car == '+':
            car = ' '
        elif car == '%':
            code = unhexlify(txt[i+1:i+3])
            if (code[0] >= 32) and (code[0] < 127):
                car = str(code)[2:-1]
            else:
                car = '?'
            i = i + 2
        if (car >= ' ') and (car <= '~'):
            res = res + car
            i = i + 1
        else:
            res = res + '?'
            i = i + 1
    return res

def scroll_text(text):
    while True:
        for i in range(len(text) + LCD_NUM_COLS):
            lcd.move_to(0, 0)
            lcd.putstr(text[i:i+LCD_NUM_COLS])
            time.sleep(SCROLL_DELAY)
            
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
  
print('Connection with ', addr)
 

while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
 
        request = cl.recv(1024)
        req = str(request)[2:-1]
        if req[0:5] == 'POST ':
          
            pos = req.find('Message')
            if pos != -1:
                resp = (txtDecode(req[pos+9:])+ 16*' ')[0:16]
                lcd.move_to(0,0)
                #lcd.putstr(resp)
                scroll_text(resp)

         
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(html)
        cl.close()

  
    except OSError as e:
        cl.close()
