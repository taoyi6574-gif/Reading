import matlab.engine
from time import sleep

from server.app.core.config import settings


class MatlabN():
    def __init__(self):
        self.eng = matlab.engine.start_matlab()
        # 允许通过配置调整 NDI 工具包目录
        self.eng.cd(settings.NDI_PACKAGE_DIR, nargout=0)
        self.ndi = self.eng.ndiInit(0)


    def connect(self):
        ip = settings.NDI_IP
        port = settings.NDI_PORT
        self.eng.ndiConnect(self.ndi, ip, port, nargout=0)
        sleep(1)
        if (self.eng.ndiIsConnected(self.ndi)):
            return 1
        else:
            return 0

    def getSD(self):
        r1, r2 = self.eng.ndiGetSDData(self.ndi, nargout=2)
        return r2

    def disconnect(self):
        """断开 NDI 连接。若工具包无 ndiDisconnect，则仅作占位。"""
        try:
            if hasattr(self.eng, "ndiDisconnect"):
                self.eng.ndiDisconnect(self.ndi, nargout=0)
        except Exception:
            pass

    def is_connected(self) -> bool:
        """查询当前是否已连接。"""
        try:
            return bool(self.eng.ndiIsConnected(self.ndi))
        except Exception:
            return False

    def getData(self):
        isSuccess, frameData, mark, time = self.eng.ndiGetFrameData(self.ndi, nargout=4)
        return frameData

