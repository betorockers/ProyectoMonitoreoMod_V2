import core.ping_logic as core_ping_logic
import ping_logic as legacy_ping_logic


class _DummyResult:
    def __init__(self, returncode=0, stdout="time=12ms"):
        self.returncode = returncode
        self.stdout = stdout


class _DummyMonitor:
    def __init__(self):
        self._ping_thread_active = True
        self.calls = []
        self.mac = "Buscando MAC..."

    def update_status(self, status, mac, latency):
        self.calls.append((status, mac, latency))
        self._ping_thread_active = False

    def winfo_exists(self):
        raise RuntimeError("winfo_exists no debe llamarse desde el hilo de ping")


def test_legacy_ping_logic_avoids_widget_tk_calls(monkeypatch):
    monitor = _DummyMonitor()

    monkeypatch.setattr(legacy_ping_logic, "get_mac_address", lambda ip: "AA:BB:CC:DD:EE:FF")
    monkeypatch.setattr(legacy_ping_logic.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        legacy_ping_logic.subprocess,
        "check_output",
        lambda *args, **kwargs: "Respuesta desde 127.0.0.1: bytes=32 time=12ms TTL=64",
    )

    legacy_ping_logic.ping_ip("127.0.0.1", monitor, 0)

    assert monitor.calls == [("Conectado", "AA:BB:CC:DD:EE:FF", 12.0)]


def test_core_ping_logic_avoids_widget_tk_calls(monkeypatch):
    monitor = _DummyMonitor()

    monkeypatch.setattr(core_ping_logic, "get_mac_address", lambda ip: "AA:BB:CC:DD:EE:FF")
    monkeypatch.setattr(core_ping_logic.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        core_ping_logic.subprocess,
        "run",
        lambda *args, **kwargs: _DummyResult(returncode=0, stdout="time=8ms"),
    )

    core_ping_logic.ping_ip("127.0.0.1", monitor, 0)

    assert monitor.calls == [("Conectado", "AA:BB:CC:DD:EE:FF", 8.0)]
