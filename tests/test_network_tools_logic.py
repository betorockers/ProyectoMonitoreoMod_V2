from network_tools_logic import is_valid_domain, is_valid_ip, run_secure_command


def test_is_valid_ip_accepts_ipv4():
    assert is_valid_ip("192.168.1.10")
    assert is_valid_ip("8.8.8.8")


def test_is_valid_ip_rejects_invalid_values():
    assert not is_valid_ip("999.999.999.999")
    assert not is_valid_ip("host.local")


def test_is_valid_domain_accepts_common_domains():
    assert is_valid_domain("google.com")
    assert is_valid_domain("sub.dominio.cl")


def test_is_valid_domain_rejects_invalid_domains():
    assert not is_valid_domain("localhost")
    assert not is_valid_domain("192.168.1.1")


def test_run_secure_command_returns_missing_command_message(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("network_tools_logic.subprocess.run", fake_run)

    output = run_secure_command(["cmd-que-no-existe"])

    assert "cmd-que-no-existe" in output
    assert "no fue encontrado" in output
