import threading
import time
from typing import Optional, Callable
import cv2
from PIL import Image

class CameraScannerService:
    """
    Background thread worker for capturing webcam frames and decoding QR tokens.
    Thread-safe and handles missing camera hardware gracefully without UI freezing.
    """
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.detector = cv2.QRCodeDetector()
        
        self.frame_callback: Optional[Callable[[Image.Image], None]] = None
        self.qr_callback: Optional[Callable[[str], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None

    def start(self, frame_callback: Optional[Callable] = None, qr_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """Start the background video capture and QR decoding loop."""
        if self.is_running:
            return

        self.frame_callback = frame_callback
        self.qr_callback = qr_callback
        self.status_callback = status_callback
        self.is_running = True

        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        try:
            # DirectShow on Windows avoids camera startup delays
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                if self.status_callback:
                    self.status_callback("NO_CAMERA")
                return

            if self.status_callback:
                self.status_callback("RUNNING")

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            while self.is_running:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

                # QR Decoding
                try:
                    data, bbox, _ = self.detector.detectAndDecode(frame)
                    if data and data.strip():
                        if self.qr_callback and self.is_running:
                            self.qr_callback(data.strip())
                except Exception:
                    pass

                # Draw targeting guide reticle
                h, w, _ = frame.shape
                box_size = 220
                top_left = ((w - box_size) // 2, (h - box_size) // 2)
                bottom_right = (top_left[0] + box_size, top_left[1] + box_size)
                
                # Corner reticles
                corner_len = 24
                cv2.line(frame, top_left, (top_left[0] + corner_len, top_left[1]), (79, 70, 229), 3)
                cv2.line(frame, top_left, (top_left[0], top_left[1] + corner_len), (79, 70, 229), 3)

                cv2.line(frame, (bottom_right[0], top_left[1]), (bottom_right[0] - corner_len, top_left[1]), (79, 70, 229), 3)
                cv2.line(frame, (bottom_right[0], top_left[1]), (bottom_right[0], top_left[1] + corner_len), (79, 70, 229), 3)

                cv2.line(frame, (top_left[0], bottom_right[1]), (top_left[0] + corner_len, bottom_right[1]), (79, 70, 229), 3)
                cv2.line(frame, (top_left[0], bottom_right[1]), (top_left[0], bottom_right[1] - corner_len), (79, 70, 229), 3)

                cv2.line(frame, bottom_right, (bottom_right[0] - corner_len, bottom_right[1]), (79, 70, 229), 3)
                cv2.line(frame, bottom_right, (bottom_right[0], bottom_right[1] - corner_len), (79, 70, 229), 3)

                # Convert BGR to RGB for UI
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)

                if self.frame_callback and self.is_running:
                    self.frame_callback(pil_img)

                time.sleep(0.03)  # ~30 FPS

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"ERROR: {str(e)}")
        finally:
            if self.cap and self.cap.isOpened():
                self.cap.release()

    def stop(self):
        """Safely release webcam hardware and terminate background thread."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
