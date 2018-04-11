from __future__ import print_function
import serial
import re
from time import sleep
from datetime import datetime

class SERIAL_TESTER:
    def __init__(self, tty_name = "/dev/ttyS0", baudrate = 115200):
        self.ser = serial.Serial()
        self.ser.port = tty_name

        self.userstring     = "Username:"
        self.passwdstring   = "Password:"
        self.continuestring = "-- more --, next page: Space, continue: g, quit: ^C"
        self.linegreeting   = "[0-9,a-z,A-Z]*@[0-9,a-z,A-Z,(,)]*#"
        self.debug = False
        self.print = True

        self.serConf(baudrate)
        self.ser.open()
        self.ser.flushInput()
        self.ser.flushOutput()

    def serConf(self, baudrate):
        self.ser.baudrate = baudrate
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = .1
        self.ser.xonxoff = False # Disable Software Flow Control
        self.ser.rtscts = False # Disable (RTS/CTS) flow Control
        self.ser.dsrdtr = False # Disable (DSR/DTR) flow Control
        self.ser.writeTimeout = 2

    def close(self):
        self.ser.close()

    def micros(self):
        time = datetime.now()
        return (time.microsecond) + (time.second * pow(10,6)) + (time.minute * 60 * pow(10,6)) + (time.hour * 60 * 60 * pow(10,6))

    def millis(self):
        return self.micros() / 1000

    def cmdin(self, cmdstr = ""):
        sendstr = cmdstr + "\r\n"
        if self.debug:
            print("send: %s" % repr(sendstr))
        length = self.ser.write(sendstr) - 2
        return length

    def cmdout(self, begin, end = None, timeout = 5000):
        end = end if end else self.linegreeting
        out     = False
        todo    = True
        success = True
        full    = ""
        outtime = self.millis() + timeout
        while todo:
            line = self.ser.readline()
            # check timeout
            if timeout != 0:
                if outtime < self.millis():
                    todo = False
                    success = False
            # check buffer size
            if (len(line) == 0):
                continue
            # print debug
            if self.debug:
                print("receive: %s" % repr(line))

            if line == self.continuestring:
                self.cmdin("g")
            # check end regex
            if end is not None:
                if out or begin is None:
                    if self.debug:
                        print("end: %s line: %s" % (end, repr(line)))
                    if re.search(end, line) is not None:
                        todo = False
            # check begin regex
            if begin is not None:
                if not out:
                    if self.debug:
                        print("begin: %s line: %s" % (begin, repr(line)))
                    if re.search(begin, line) is not None:
                        out = True
            # print
            if out:
                if len(line) > 0:
                    print(line, end='')
                    full += line

        # print(full)
        return success

    def cmdinout(self, cmdin, cmdout = None, timeout = 5000):
        self.cmdin(cmdin)
        cmdin = self.escapchar(cmdin)
        self.cmdout(cmdin, cmdout, timeout)
        pass

    def checklive(self, timeout = 1000):
        self.cmdin()
        return self.cmdout(None, self.linegreeting, timeout)

    def login(self, user = "admin", passwd = "admin", timeout = 1000):
        if self.checklive(timeout):
            print("already login")
            return True
        self.cmdin();
        while True:
            br = self.cmdout(None, self.userstring, timeout)
            if br:
                break
            else:
                self.cmdin()
                
        self.cmdin(user)
        while True:
            br = self.cmdout(None, self.passwdstring, timeout)
            if br:
                break
            else:
                self.cmdin()
        self.cmdin(passwd)
        login = self.checklive(timeout)
        if login:
            print("login successful")
        return

    # add escaping characters
    def escapchar(self, string):
        return string.replace("*", "\*")

    def debugallow(self):
        self.debug = True

    def debugdeny(self):
        self.debug = False

def test():
    sr = SERIAL_TESTER("/dev/ttyUSB0")
    sr.login()

    for x in xrange(1,10):
        print("TEST %d" % x)
        sr.cmdinout("show version", timeout = 60000)

    sr.close()