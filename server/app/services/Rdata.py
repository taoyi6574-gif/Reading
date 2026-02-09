import matlab.engine
from time import sleep


class MatlabN():
    def __init__(self):
        self.eng = matlab.engine.start_matlab()
        self.eng.cd('NDI Package V1.3.2/NDI', nargout=0)
        self.ndi = self.eng.ndiInit(0)


    def connect(self):
        ip = '0.0.0.0'
        port = 5566
        self.eng.ndiConnect(self.ndi, ip, port, nargout=0)
        sleep(1)
        if (self.eng.ndiIsConnected(self.ndi)):
            return 1
        else:
            return 0

    def getSD(self):
        r1, r2 = self.eng.ndiGetSDData(self.ndi, nargout=2)
        return r2

    def getData(self):
        isSuccess, frameData, mark, time = self.eng.ndiGetFrameData(self.ndi, nargout=4)
        return frameData

