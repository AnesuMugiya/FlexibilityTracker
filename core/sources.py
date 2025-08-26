import cv2

class FrameSource:
    def read(self):
        """Return (ret, frame). ret=False when no more frames."""
        raise NotImplementedError
    def release(self):
        pass

class CameraSource(FrameSource):
    def __init__(self, device=0):
        self.cap = cv2.VideoCapture(device)
    def read(self):
        return self.cap.read()
    def release(self):
        if self.cap: self.cap.release()

class VideoFileSource(FrameSource):
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
    def read(self):
        return self.cap.read()
    def release(self):
        if self.cap: self.cap.release()

class ImageSource(FrameSource):
    def __init__(self, path):
        self.frame = cv2.imread(path)  # BGR
        self.done = False
    def read(self):
        if self.frame is None:  # bad path
            return False, None
        if self.done:
            # return one frame repeatedly so GUI keeps showing it
            return True, self.frame.copy()
        self.done = True
        return True, self.frame.copy()
