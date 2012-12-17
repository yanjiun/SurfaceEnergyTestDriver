import signal


class TimeoutException(Exception):
    pass

def handler1(signum,frame):
    print "handler1"
    raise TimeoutException()

def handler2(signum,frame):
    print "handler2"
    raise Exception

signal.signal(signal.SIGALRM,handler1)

boo = True

signal.alarm(3)
signal.alarm(0)

signal.alarm(3)
while boo:
    try:
        print "running"
    except TimeoutException:
        print "quiting"
        break
signal.alarm(0)

#signal.signal(signal.SIGALRM,handler2)
#signal.alarm(3)
#while boo:
#    print "running again"
#signal.alarm(0)

#while boo:
#    print "proof there's no alarm"
#
#print "test finished"
