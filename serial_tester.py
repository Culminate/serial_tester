from __future__ import print_function
import serial
from time import sleep
import re
from datetime import datetime

class SERIAL_TESTER:
    def __init__(self, tty_name, baudrate):
        self.ser = serial.Serial()
        self.ser.port = tty_name

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

    def cmdin(self, cmdstr = "", debug = False):
        sendstr = cmdstr + "\r\n"
        if debug:
            print("send: %s" % repr(sendstr))
        length = self.ser.write(sendstr) - 2
        return length

    def cmdout(self, begin, end, timeout = 5000000, debug = False):
        out     = False
        todo    = True
        success = True
        full    = ""
        outtime = self.micros() + timeout
        while todo:
            line = self.ser.readline()
            # check timeout
            if timeout != 0:
                if outtime < self.micros():
                    todo = False
                    success = False
            # check buffer size
            if (len(line) == 0):
                continue
            # print debug
            if debug:
                print("receive: %s" % repr(line))

            if line == self.continuestring:
                self.cmdin("g")
            # check end regex
            if end is not None:
                if out or begin is None:
                    if debug:
                        print("end: %s line: %s" % (end, repr(line)))
                    if re.search(end, line) is not None:
                        todo = False
            # check begin regex
            if begin is not None:
                if not out:
                    if debug:
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

    def checklive(self, timeout = 1000000, debug = False):
        self.cmdin(debug = debug)
        return self.cmdout(None, self.linegreeting, timeout, debug)

    def login(self, user = "admin", passwd = "admin", timeout = 1000000, debug = False):
        if self.checklive(timeout):
            return True
        self.cmdin(debug = debug);
        while True:
            br = self.cmdout(None, self.userstring, timeout, debug)
            if br:
                break
            else:
                self.cmdin(debug = debug)
                
        self.cmdin("admin", debug)
        while True:
            br = self.cmdout(None, self.passwdstring, timeout, debug)
            if br:
                break
            else:
                self.cmdin(debug = debug)
        self.cmdin("admin", debug)
        return self.checklive(timeout)


sr = SERIAL_TESTER("/dev/ttyUSB0", 115200)
sr.userstring     = "Username:"
sr.passwdstring   = "Password:"
sr.continuestring = "-- more --, next page: Space, continue: g, quit: ^C"
sr.linegreeting   = "[0-9,a-z,A-Z]*@[0-9,a-z,A-Z,(,)]*#"


sr.login()

for x in xrange(1,10):
    print("TEST %d" % x)
    sr.cmdin("ver")
    print(sr.cmdout("ver", sr.linegreeting, 60 * pow(10,6)))

sr.close()