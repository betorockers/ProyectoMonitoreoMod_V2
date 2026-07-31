"""Utilidades base para perfiles de camaras IP."""

import time
from urllib.parse import quote, urlparse, urlunparse

from services.network_tools import NetworkTools


class CameraTools:
    """Helpers para snapshot HTTP y prueba basica de RTSP."""

    @staticmethod
    def extract_rtsp_endpoint(rtsp_url: str) -> tuple[str, int]:
        cleaned = rtsp_url.strip()
        if not cleaned:
            return "", 554
        normalized = cleaned if "://" in cleaned else f"rtsp://{cleaned}"
        parsed = urlparse(normalized)
        return parsed.hostname or "", parsed.port or 554

    @staticmethod
    def normalize_rtsp_url(
        rtsp_url: str,
        username: str = "",
        password: str = "",
    ) -> str:
        """Normaliza una URL RTSP y agrega credenciales si corresponde."""
        cleaned = rtsp_url.strip()
        if not cleaned:
            return ""

        normalized = cleaned if "://" in cleaned else f"rtsp://{cleaned}"
        parsed = urlparse(normalized)
        if not parsed.hostname:
            return normalized
        if parsed.username:
            return normalized
        if not username:
            return normalized

        auth = quote(username, safe="")
        if password:
            auth = f"{auth}:{quote(password, safe='')}"

        netloc = f"{auth}@{parsed.hostname}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"

        return urlunparse(
            (
                parsed.scheme or "rtsp",
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    @staticmethod
    def fetch_snapshot(
        snapshot_url: str,
        username: str = "",
        password: str = "",
        timeout: int = 5,
        verify_tls: bool = False,
    ) -> tuple[bool, dict]:
        url = NetworkTools.normalize_url(snapshot_url, scheme="http")
        if not url:
            return False, {"url": "", "error": "URL de snapshot vacia"}

        try:
            import requests
        except ModuleNotFoundError:
            return False, {
                "url": url,
                "error": "Dependencia 'requests' no disponible en este entorno.",
            }

        auth = (username, password) if username else None
        started = time.perf_counter()
        try:
            response = NetworkTools.safe_requests_get(
                requests,
                url,
                timeout=timeout,
                verify_tls=verify_tls,
                auth=auth,
                allow_redirects=True,
            )
            response.raise_for_status()
            elapsed_ms = (time.perf_counter() - started) * 1000
            return True, {
                "url": response.url,
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed_ms, 1),
                "content_type": response.headers.get("Content-Type", ""),
                "image_bytes": response.content,
            }
        except requests.RequestException as e:
            return False, {
                "url": url,
                "error": str(e),
            }

    @staticmethod
    def probe_rtsp_stream(rtsp_url: str, timeout: float = 1.0) -> tuple[bool, dict]:
        host, port = CameraTools.extract_rtsp_endpoint(rtsp_url)
        if not host:
            return False, {"host": "", "port": 554, "error": "URL RTSP invalida"}

        ok, result = NetworkTools.scan_ports(host, [port], timeout=timeout, max_ports=1)
        if not ok:
            return False, {"host": host, "port": port, "error": result}

        entry = result[0]
        return True, {
            "host": host,
            "port": port,
            "open": entry["open"],
            "latency_ms": entry["latency_ms"],
            "service": entry["service"],
        }

    @staticmethod
    def fetch_rtsp_frame(
        rtsp_url: str,
        username: str = "",
        password: str = "",
        timeout: float = 5.0,
    ) -> tuple[bool, dict]:
        """
        Intenta abrir un stream RTSP y capturar un frame.
        Requiere OpenCV disponible en el entorno.
        """
        normalized_url = CameraTools.normalize_rtsp_url(
            rtsp_url,
            username=username,
            password=password,
        )
        host, port = CameraTools.extract_rtsp_endpoint(normalized_url)
        if not host:
            return False, {
                "url": "",
                "host": "",
                "port": 554,
                "error": "URL RTSP invalida",
            }

        try:
            import cv2
        except ModuleNotFoundError:
            return False, {
                "url": normalized_url,
                "host": host,
                "port": port,
                "error": "Dependencia 'opencv-python' no disponible en este entorno.",
            }

        started = time.perf_counter()
        capture = None
        try:
            backend = getattr(cv2, "CAP_FFMPEG", None)
            capture = (
                cv2.VideoCapture(normalized_url, backend)
                if backend is not None
                else cv2.VideoCapture(normalized_url)
            )

            for prop_name in ("CAP_PROP_OPEN_TIMEOUT_MSEC", "CAP_PROP_READ_TIMEOUT_MSEC"):
                prop = getattr(cv2, prop_name, None)
                if prop is not None:
                    try:
                        capture.set(prop, int(timeout * 1000))
                    except Exception:
                        pass

            buffer_prop = getattr(cv2, "CAP_PROP_BUFFERSIZE", None)
            if buffer_prop is not None:
                try:
                    capture.set(buffer_prop, 1)
                except Exception:
                    pass

            is_opened = getattr(capture, "isOpened", lambda: True)()
            if not is_opened:
                return False, {
                    "url": normalized_url,
                    "host": host,
                    "port": port,
                    "error": "No se pudo abrir el stream RTSP.",
                }

            ok, frame = capture.read()
            if not ok or frame is None:
                return False, {
                    "url": normalized_url,
                    "host": host,
                    "port": port,
                    "error": "No se pudo capturar un frame RTSP.",
                }

            encoded_ok, encoded = cv2.imencode(".jpg", frame)
            if not encoded_ok:
                return False, {
                    "url": normalized_url,
                    "host": host,
                    "port": port,
                    "error": "No se pudo codificar el frame RTSP.",
                }

            elapsed_ms = (time.perf_counter() - started) * 1000
            height, width = frame.shape[:2]
            return True, {
                "url": normalized_url,
                "host": host,
                "port": port,
                "elapsed_ms": round(elapsed_ms, 1),
                "width": int(width),
                "height": int(height),
                "image_bytes": encoded.tobytes(),
                "source": "rtsp",
            }
        except Exception as e:
            return False, {
                "url": normalized_url,
                "host": host,
                "port": port,
                "error": str(e),
            }
        finally:
            if capture is not None:
                try:
                    capture.release()
                except Exception:
                    pass
