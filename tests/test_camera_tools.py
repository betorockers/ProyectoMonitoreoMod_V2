from types import ModuleType
import sys

from services.camera_tools import CameraTools


class _FakeResponse:
    def __init__(self, url, status_code=200, headers=None, content=b""):
        self.url = url
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content

    def raise_for_status(self):
        return None


def test_extract_rtsp_endpoint_uses_default_port():
    host, port = CameraTools.extract_rtsp_endpoint("rtsp://cam.local/stream")
    assert host == "cam.local"
    assert port == 554


def test_normalize_rtsp_url_injects_credentials():
    url = CameraTools.normalize_rtsp_url(
        "rtsp://cam.local/live",
        username="admin",
        password="secret",
    )
    assert url == "rtsp://admin:secret@cam.local/live"


def test_fetch_snapshot_returns_summary(monkeypatch):
    def fake_get(url, timeout, verify, auth, allow_redirects):
        assert url == "http://cam.local/snapshot.jpg"
        assert auth == ("admin", "secret")
        return _FakeResponse(
            url="http://cam.local/snapshot.jpg",
            status_code=200,
            headers={"Content-Type": "image/jpeg"},
            content=b"jpeg-bytes",
        )

    fake_requests = ModuleType("requests")
    fake_requests.get = fake_get
    fake_requests.RequestException = Exception
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    ok, data = CameraTools.fetch_snapshot(
        "cam.local/snapshot.jpg",
        username="admin",
        password="secret",
    )

    assert ok is True
    assert data["status_code"] == 200
    assert data["content_type"] == "image/jpeg"
    assert data["image_bytes"] == b"jpeg-bytes"


def test_probe_rtsp_stream_uses_network_tools(monkeypatch):
    monkeypatch.setattr(
        "services.camera_tools.NetworkTools.scan_ports",
        lambda target, ports, timeout=1.0, max_ports=1: (
            True,
            [{"port": 554, "open": True, "latency_ms": 4.2, "service": "rtsp"}],
        ),
    )

    ok, data = CameraTools.probe_rtsp_stream("rtsp://cam.local/live")

    assert ok is True
    assert data["host"] == "cam.local"
    assert data["port"] == 554
    assert data["open"] is True
    assert data["service"] == "rtsp"


def test_fetch_rtsp_frame_reports_missing_dependency(monkeypatch):
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cv2":
            raise ModuleNotFoundError("missing cv2")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    ok, data = CameraTools.fetch_rtsp_frame("rtsp://cam.local/live")

    assert ok is False
    assert "opencv-python" in data["error"]


def test_fetch_rtsp_frame_returns_encoded_image(monkeypatch):
    class _FakeEncoded:
        def tobytes(self):
            return b"jpeg-bytes"

    class _FakeFrame:
        shape = (720, 1280, 3)

    class _FakeCapture:
        def __init__(self, url, backend=None):
            self.url = url
            self.backend = backend
            self.props = []

        def set(self, prop, value):
            self.props.append((prop, value))
            return True

        def isOpened(self):
            return True

        def read(self):
            return True, _FakeFrame()

        def release(self):
            self.released = True

    fake_cv2 = ModuleType("cv2")
    fake_cv2.CAP_FFMPEG = 1
    fake_cv2.CAP_PROP_BUFFERSIZE = 2
    fake_cv2.CAP_PROP_OPEN_TIMEOUT_MSEC = 3
    fake_cv2.CAP_PROP_READ_TIMEOUT_MSEC = 4
    fake_cv2.VideoCapture = lambda url, backend=None: _FakeCapture(url, backend)
    fake_cv2.imencode = lambda ext, frame: (True, _FakeEncoded())
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    ok, data = CameraTools.fetch_rtsp_frame(
        "rtsp://cam.local/live",
        username="admin",
        password="secret",
        timeout=4,
    )

    assert ok is True
    assert data["host"] == "cam.local"
    assert data["port"] == 554
    assert data["width"] == 1280
    assert data["height"] == 720
    assert data["image_bytes"] == b"jpeg-bytes"
    assert data["source"] == "rtsp"
