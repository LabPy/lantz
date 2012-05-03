from time import sleep
from c843 import C843


def props(ild):
    stage.qspa(ild, 1)
    stage.qspa(ild, 2)
    stage.qspa(ild, 3)
    stage.qspa(ild, 4)
    stage.qspa(ild, 11)
    stage.qspa(ild, 10)
    stage.qspa(ild, 14)
    stage.qspa(ild, 15)
    stage.qspa(ild, 20)
    stage.qspa(ild, 21)
    stage.qspa(ild, 48)


stage = C843()
stage.connect()
stage.isconnected()

stage.idn()

stage.qcst()
stage.cst()
stage.qcst()

stage.init()

print("$$$$$$$$$$$$$$$$$$$\n")

#X = 4
Y = 4

#props(chn)

def initaxis(chn):
    #stage.qref(chn)
    stage.qlim(chn)
    stage.isrefok(chn)
    if chn == 4:
        stage.ref(chn)
    else:
        stage.mpl(chn)
    sleep(5)
    stage.isrefok(chn)

#initaxis(X)
initaxis(Y)

if Y == 4:
    stage.mov(Y, -30)

#initposX = 0
#initposY = 0
#stepX = 0.25
#stepY = 0.25
#for i in range(5):
    #stage.mov(X, initposX)
    #sleep(2)
    #stage.qont(X)
    #stage.qpos(X)
    #initposX += stepX
    #for j in range(5):
        #stage.mov(Y, initposY)
        #sleep(2)
        #stage.qont(Y)
        #stage.qpos(Y)
        #initposY += stepY
    #initposY = initposY - j*stepY
#
#stage.geterror()
#stage.disconnect()

