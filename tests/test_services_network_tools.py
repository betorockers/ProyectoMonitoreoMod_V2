import builtins
from types import ModuleType, SimpleNamespace
import sys
import warnings

from services.network_tools import NetworkTools


class _FakeResponse:
    def __init__(self, url, status_code=200, headers=None, text=""):
        self.url = url
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


class _FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_execute_maintenance_rejects_invalid_command():
    ok, message = NetworkTools.execute_maintenance("nope")
    assert ok is False
    assert "no v" in message.lower()


def test_get_ip_geolocation_skips_private_ip():
    assert NetworkTools.get_ip_geolocation("192.168.1.5", enabled=True) == ""
    assert NetworkTools.get_ip_geolocation("10.0.0.5", enabled=True) == ""


def test_get_ip_geolocation_disabled_skips_external_lookup(monkeypatch):
    def fake_get(*args, **kwargs):
        raise AssertionError("requests.get no deberia ejecutarse cuando la geolocalizacion externa esta desactivada")

    fake_requests = ModuleType("requests")
    fake_requests.get = fake_get
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    assert NetworkTools.get_ip_geolocation("8.8.8.8", enabled=False) == ""


def test_normalize_url_adds_scheme():
    assert NetworkTools.normalize_url("example.com") == "http://example.com"
    assert NetworkTools.normalize_url("https://example.com") == "https://example.com"


def test_extract_host_from_url():
    assert NetworkTools.extract_host("https://demo.local:8443/status") == "demo.local"
    assert NetworkTools.extract_host("10.0.0.15") == "10.0.0.15"


def test_parse_ports_deduplicates_and_limits():
    ports = NetworkTools.parse_ports("80,443,554-556,443", max_ports=5)
    assert ports == [80, 443, 554, 555, 556]


def test_check_http_endpoint_returns_summary(monkeypatch):
    def fake_get(url, timeout, verify, allow_redirects):
        assert url == "http://demo.local"
        assert timeout == 5
        assert verify is False
        assert allow_redirects is True
        return _FakeResponse(
            url="http://demo.local/login",
            status_code=200,
            headers={"Server": "nginx", "Content-Type": "text/html"},
            text="<html><title>Panel LPR</title></html>",
        )

    fake_requests = ModuleType("requests")
    fake_requests.get = fake_get
    fake_requests.RequestException = Exception
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    ok, data = NetworkTools.check_http_endpoint("demo.local")

    assert ok is True
    assert data["url"] == "http://demo.local/login"
    assert data["status_code"] == 200
    assert data["server"] == "nginx"
    assert data["content_type"] == "text/html"
    assert data["title"] == "Panel LPR"


def test_safe_requests_get_suppresses_insecure_warning(monkeypatch):
    class _FakeInsecureRequestWarning(Warning):
        pass

    def fake_get(url, verify=True, **kwargs):
        warnings.warn("tls off", _FakeInsecureRequestWarning)
        return _FakeResponse(url=url, status_code=200)

    fake_requests = ModuleType("requests")
    fake_requests.get = fake_get

    fake_urllib3 = ModuleType("urllib3")
    fake_exceptions = ModuleType("urllib3.exceptions")
    fake_exceptions.InsecureRequestWarning = _FakeInsecureRequestWarning
    fake_urllib3.exceptions = fake_exceptions

    monkeypatch.setitem(sys.modules, "urllib3", fake_urllib3)
    monkeypatch.setitem(sys.modules, "urllib3.exceptions", fake_exceptions)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        response = NetworkTools.safe_requests_get(
            fake_requests,
            "https://demo.local",
            verify_tls=False,
            timeout=5,
        )

    assert response.status_code == 200
    assert captured == []


def test_scan_ports_reports_open_and_closed(monkeypatch):
    def fake_create_connection(address, timeout):
        host, port = address
        assert host == "demo.local"
        assert timeout == 1.5
        if port == 80:
            return _FakeConnection()
        raise OSError("closed")

    def fake_getservbyport(port):
        return {80: "http", 554: "rtsp"}[port]

    monkeypatch.setattr("services.network_tools.socket.create_connection", fake_create_connection)
    monkeypatch.setattr("services.network_tools.socket.getservbyport", fake_getservbyport)

    ok, data = NetworkTools.scan_ports("http://demo.local", "80,554", timeout=1.5, max_ports=8)

    assert ok is True
    assert len(data) == 2
    assert data[0]["port"] == 80
    assert data[0]["open"] is True
    assert data[0]["service"] == "http"
    assert data[1]["port"] == 554
    assert data[1]["open"] is False
    assert data[1]["service"] == "rtsp"


def test_scan_ports_rejects_invalid_port_spec():
    ok, message = NetworkTools.scan_ports("demo.local", "abc")
    assert ok is False
    assert "inv" in message.lower()


def test_resolve_snmp_oid_alias_returns_standard_oid():
    assert NetworkTools.resolve_snmp_oid("sysName") == "1.3.6.1.2.1.1.5.0"


def test_snmp_get_returns_summary(monkeypatch):
    fake_hlapi = ModuleType("pysnmp.hlapi")

    fake_hlapi.SnmpEngine = lambda: "engine"
    fake_hlapi.CommunityData = lambda community, mpModel=1: (community, mpModel)
    fake_hlapi.UdpTransportTarget = lambda target, timeout=2, retries=0: (target, timeout, retries)
    fake_hlapi.ContextData = lambda: "context"
    fake_hlapi.ObjectIdentity = lambda oid: oid
    fake_hlapi.ObjectType = lambda identity: ("object", identity)

    def fake_get_cmd(*args):
        yield (None, None, 0, [("1.3.6.1.2.1.1.5.0", "Switch Core")])

    fake_hlapi.getCmd = fake_get_cmd

    fake_pysnmp = ModuleType("pysnmp")
    fake_pysnmp.hlapi = fake_hlapi
    monkeypatch.setitem(sys.modules, "pysnmp", fake_pysnmp)
    monkeypatch.setitem(sys.modules, "pysnmp.hlapi", fake_hlapi)

    ok, data = NetworkTools.snmp_get("10.0.0.20", community="public", oid="sysName")

    assert ok is True
    assert data["host"] == "10.0.0.20"
    assert data["oid"] == "1.3.6.1.2.1.1.5.0"
    assert data["entries"] == [{"oid": "1.3.6.1.2.1.1.5.0", "value": "Switch Core"}]


def test_snmp_get_reports_missing_dependency(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pysnmp.hlapi":
            raise ModuleNotFoundError("missing pysnmp")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    ok, data = NetworkTools.snmp_get("10.0.0.20", oid="sysName")

    assert ok is False
    assert "pysnmp" in data["error"]


def test_ssh_run_command_returns_summary(monkeypatch):
    class _FakeChannel:
        def recv_exit_status(self):
            return 0

    class _FakeStream:
        def __init__(self, content):
            self._content = content
            self.channel = _FakeChannel()

        def read(self):
            return self._content

    class _FakeSSHClient:
        def load_system_host_keys(self):
            self.loaded_system = True

        def set_missing_host_key_policy(self, policy):
            self.policy = policy

        def connect(self, **kwargs):
            self.kwargs = kwargs

        def exec_command(self, command, timeout=5):
            assert command == "hostname"
            assert timeout == 5
            return None, _FakeStream(b"edge-gateway\n"), _FakeStream(b"")

        def get_transport(self):
            class _FakeKey:
                def get_name(self):
                    return "ssh-rsa"

                def asbytes(self):
                    return b"fake-host-key"

            class _FakeTransport:
                def get_remote_server_key(self):
                    return _FakeKey()

            return _FakeTransport()

        def close(self):
            self.closed = True

    fake_paramiko = ModuleType("paramiko")
    fake_paramiko.SSHClient = _FakeSSHClient
    fake_paramiko.AutoAddPolicy = lambda: "policy"
    monkeypatch.setitem(sys.modules, "paramiko", fake_paramiko)

    ok, data = NetworkTools.ssh_run_command(
        "10.0.0.30",
        username="admin",
        password="secret",
        command="hostname",
        port=22,
        timeout=5,
        verify_host_key=False,
    )

    assert ok is True
    assert data["host"] == "10.0.0.30"
    assert data["username"] == "admin"
    assert data["command"] == "hostname"
    assert data["exit_status"] == 0
    assert data["stdout"] == "edge-gateway"
    assert data["stderr"] == ""
    assert data["host_key_mode"] == "insecure"
    assert data["host_key_type"] == "ssh-rsa"
    assert data["host_key_fingerprint"].startswith("SHA256:")


def test_ssh_run_command_strict_mode_uses_known_hosts(monkeypatch, tmp_path):
    class _FakeChannel:
        def recv_exit_status(self):
            return 0

    class _FakeStream:
        def __init__(self, content):
            self._content = content
            self.channel = _FakeChannel()

        def read(self):
            return self._content

    class _FakeSSHClient:
        def __init__(self):
            self.loaded_path = None

        def load_system_host_keys(self):
            self.loaded_system = True

        def load_host_keys(self, path):
            self.loaded_path = path

        def set_missing_host_key_policy(self, policy):
            self.policy = policy

        def connect(self, **kwargs):
            self.kwargs = kwargs

        def exec_command(self, command, timeout=5):
            return None, _FakeStream(b"ok\n"), _FakeStream(b"")

        def get_transport(self):
            class _FakeKey:
                def get_name(self):
                    return "ssh-ed25519"

                def asbytes(self):
                    return b"strict-host-key"

            class _FakeTransport:
                def get_remote_server_key(self):
                    return _FakeKey()

            return _FakeTransport()

        def close(self):
            pass

    known_hosts = tmp_path / "ssh_known_hosts"
    known_hosts.write_text("existing", encoding="utf-8")

    fake_paramiko = ModuleType("paramiko")
    fake_paramiko.SSHClient = _FakeSSHClient
    fake_paramiko.AutoAddPolicy = lambda: "policy"
    monkeypatch.setitem(sys.modules, "paramiko", fake_paramiko)

    ok, data = NetworkTools.ssh_run_command(
        "10.0.0.30",
        username="admin",
        password="secret",
        command="hostname",
        verify_host_key=True,
        trust_on_first_use=False,
        known_hosts_path=str(known_hosts),
    )

    assert ok is True
    assert data["host_key_mode"] == "strict"
    assert data["host_key_type"] == "ssh-ed25519"


def test_ssh_run_command_reports_missing_dependency(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "paramiko":
            raise ModuleNotFoundError("missing paramiko")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    ok, data = NetworkTools.ssh_run_command(
        "10.0.0.30",
        username="admin",
        password="secret",
        command="hostname",
    )

    assert ok is False
    assert "paramiko" in data["error"]


def test_ssh_run_command_requires_credentials():
    ok, data = NetworkTools.ssh_run_command(
        "10.0.0.30",
        username="",
        password="",
        command="hostname",
    )

    assert ok is False
    assert "usuario" in data["error"].lower()


def test_stop_diagnostic_terminates_process():
    class _FakeProcess:
        def __init__(self):
            self.terminated = False
            self.wait_timeout = None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            self.wait_timeout = timeout

    process = _FakeProcess()

    NetworkTools.stop_diagnostic(process)

    assert process.terminated is True
    assert process.wait_timeout == 2


def test_stop_diagnostic_kills_when_timeout_occurs():
    class _FakeProcess:
        def __init__(self):
            self.terminated = False
            self.killed = False

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            raise __import__("subprocess").TimeoutExpired(cmd="ping", timeout=timeout)

        def kill(self):
            self.killed = True

    process = _FakeProcess()

    NetworkTools.stop_diagnostic(process)

    assert process.terminated is True
    assert process.killed is True


def test_get_arp_table_parses_entries(monkeypatch):
    sample_output = """
Interfaz: 192.168.1.2 --- 0xb
  Direccion de Internet      Direccion fisica      Tipo
  192.168.1.1                aa-bb-cc-dd-ee-ff     dinamico
  192.168.1.50               11-22-33-44-55-66     dinamico
"""

    monkeypatch.setattr(NetworkTools, "_get_startupinfo", staticmethod(lambda: None))
    monkeypatch.setattr(
        "services.network_tools.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=sample_output, stderr=""),
    )

    ok, data = NetworkTools.get_arp_table()

    assert ok is True
    assert len(data) == 2
    assert data[0]["ip"] == "192.168.1.1"
    assert data[0]["mac"] == "aa-bb-cc-dd-ee-ff"


def test_get_netstat_parses_connections(monkeypatch):
    sample_output = """
  TCP    127.0.0.1:49670      127.0.0.1:49671      ESTABLISHED
  UDP    0.0.0.0:5353         *:*
"""

    monkeypatch.setattr(NetworkTools, "_get_startupinfo", staticmethod(lambda: None))
    monkeypatch.setattr(
        "services.network_tools.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=sample_output, stderr=""),
    )

    ok, data = NetworkTools.get_netstat()

    assert ok is True
    assert len(data) == 2
    assert data[0]["proto"] == "TCP"
    assert data[0]["state"] == "ESTABLISHED"
    assert data[1]["proto"] == "UDP"
    assert data[1]["state"] == "N/A"


def test_get_service_status_detects_running(monkeypatch):
    sample_output = "STATE              : 4  RUNNING"

    monkeypatch.setattr(NetworkTools, "_get_startupinfo", staticmethod(lambda: None))
    monkeypatch.setattr(
        "services.network_tools.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout=sample_output),
    )

    ok, state = NetworkTools.get_service_status("Spooler")

    assert ok is True
    assert state == "Corriendo"


def test_get_service_status_detects_missing_service(monkeypatch):
    sample_output = "OpenService FAILED 1060"

    monkeypatch.setattr(NetworkTools, "_get_startupinfo", staticmethod(lambda: None))
    monkeypatch.setattr(
        "services.network_tools.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout=sample_output),
    )

    ok, state = NetworkTools.get_service_status("NoExiste")

    assert ok is True
    assert state == "No existe"
