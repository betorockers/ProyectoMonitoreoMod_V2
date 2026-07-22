"use client";

import { useState, useEffect, useCallback } from "react";
import { apiBaseUrl } from "@/lib/telemetry";
import {
  Settings, Users, Bell, Webhook, Sliders, Shield, Trash2,
  CheckCircle, AlertCircle, Save, RefreshCw, UserPlus, Send, Download
} from "lucide-react";

type User = { username: string; full_name: string; role: string };
type SectionKey = "usuarios" | "notificaciones" | "integraciones" | "sistema" | "sla";

const ROLES: Record<string, string> = {
  super_admin: "Super Admin",
  admin: "Administrador (Admin)",
  operador: "Operador",
  observador: "Observador",
};

const sectionStyle: React.CSSProperties = {
  background: "var(--panel-inset)",
  border: "1px solid var(--border-soft)",
  borderRadius: "var(--radius-panel)",
  padding: "1.5rem",
  marginBottom: "1.5rem",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.7rem 1rem",
  background: "var(--panel)",
  border: "1px solid var(--border-soft)",
  color: "var(--text-primary)",
  borderRadius: "var(--radius-control)",
  outline: "none",
  fontFamily: "monospace",
  fontSize: "0.95rem",
  boxSizing: "border-box",
};

const btnPrimary: React.CSSProperties = {
  padding: "0.6rem 1.2rem",
  background: "var(--mint-live)",
  border: "none",
  color: "var(--void)",
  borderRadius: "var(--radius-control)",
  cursor: "pointer",
  fontWeight: "bold",
  display: "flex",
  alignItems: "center",
  gap: "0.4rem",
};

const btnDanger: React.CSSProperties = {
  ...btnPrimary,
  background: "var(--red-alert)",
  color: "#fff",
};

export function ConfigPanel() {
  const [section, setSection] = useState<SectionKey>("usuarios");
  const [users, setUsers] = useState<User[]>([]);
  const [userError, setUserError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  // Form: create user
  const [newUser, setNewUser] = useState({ username: "", full_name: "", password: "", role: "operador" });

  // Config state
  const [cfg, setCfg] = useState<Record<string, string>>({});
  const [cfgLoaded, setCfgLoaded] = useState(false);

  const token = () => sessionStorage.getItem("argos_token") || "";
  const userToken = () => sessionStorage.getItem("argos_user_token") || "";

  const authHeaders = () => ({
    "Content-Type": "application/json",
    "X-Argos-Token": token(),
    "X-User-Token": userToken(),
  });

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 4000);
  };

  const loadUsers = useCallback(async () => {
    try {
      setUserError(null);
      const res = await fetch(`${apiBaseUrl}/api/v1/users`, { headers: authHeaders() });
      if (!res.ok) throw new Error("No se pudo cargar la lista de usuarios");
      setUsers(await res.json());
    } catch (e: any) {
      setUserError(e.message);
    }
  }, []);

  const loadConfig = useCallback(async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/system/config`, { headers: authHeaders() });
      if (res.ok) {
        setCfg(await res.json());
        setCfgLoaded(true);
      }
    } catch {}
  }, []);

  useEffect(() => {
    loadUsers();
    loadConfig();
  }, [loadUsers, loadConfig]);

  const saveConfig = async (key: string, value: string) => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/system/config`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ key, value }),
      });
      if (res.ok) {
        showToast(`✅ "${key}" guardado correctamente`);
        setCfg(prev => ({ ...prev, [key]: value }));
      } else {
        showToast("❌ Error al guardar configuración", false);
      }
    } catch {
      showToast("❌ Error de red", false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.password) {
      showToast("⚠️ Usuario y contraseña son requeridos", false);
      return;
    }
    const res = await fetch(`${apiBaseUrl}/api/v1/users`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(newUser),
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast("✅ Usuario creado correctamente");
      setNewUser({ username: "", full_name: "", password: "", role: "operador" });
      loadUsers();
    } else {
      showToast(`❌ ${data.message}`, false);
    }
  };

  const downloadTemplate = () => {
    const templateContent = {
      "_comentario": "Esta es una plantilla de ejemplo para carga masiva. El 'id' se genera automaticamente de la ip reemplazando puntos por guiones.",
      "targets": [
        {
          "id": "192-168-1-1",
          "label": "Servidor Core",
          "host": "192.168.1.1",
          "port": 443,
          "protocol": "tcp",
          "instalacion": "Quilicura Norte"
        }
      ]
    };
    const blob = new Blob([JSON.stringify(templateContent, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "plantilla_equipos.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`¿Eliminar al usuario "${username}"?`)) return;
    const res = await fetch(`${apiBaseUrl}/api/v1/users/${username}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (res.ok) {
      showToast("✅ Usuario eliminado");
      loadUsers();
    } else {
      const d = await res.json();
      showToast(`❌ ${d.detail || "Error al eliminar"}`, false);
    }
  };

  const testTelegram = async () => {
    const res = await fetch(`${apiBaseUrl}/api/v1/system/config/test-telegram`, {
      method: "POST",
      headers: authHeaders(),
    });
    const d = await res.json();
    showToast(d.sent ? "✅ Mensaje de prueba enviado a Telegram" : "❌ Error al enviar — verifica el token y chat_id", d.sent);
  };

  const navItems: { key: SectionKey; label: string; icon: React.ReactNode }[] = [
    { key: "usuarios", label: "Gestión de Usuarios", icon: <Users size={16} /> },
    { key: "notificaciones", label: "Notificaciones", icon: <Bell size={16} /> },
    { key: "integraciones", label: "Integraciones & Webhooks", icon: <Webhook size={16} /> },
    { key: "sla", label: "SLA & Equipo", icon: <Shield size={16} /> },
    { key: "sistema", label: "Parámetros del Sistema", icon: <Sliders size={16} /> },
  ];

  return (
    <div style={{ display: "flex", height: "100%", gap: "0", overflow: "hidden" }}>

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", top: "120px", right: "24px", zIndex: 9999,
          background: toast.ok ? "rgba(42,161,152,0.95)" : "rgba(220,50,47,0.95)",
          color: "#fff", padding: "0.8rem 1.4rem", borderRadius: "8px",
          fontWeight: "bold", boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
          animation: "slideIn 0.3s ease",
        }}>
          {toast.msg}
        </div>
      )}

      {/* Sidebar nav */}
      <aside style={{
        width: "220px", flexShrink: 0,
        background: "var(--panel-inset)",
        borderRight: "1px solid var(--border-soft)",
        padding: "1.5rem 0.8rem",
        display: "flex", flexDirection: "column", gap: "0.3rem",
      }}>
        <div style={{ color: "var(--cyan-trace)", fontSize: "0.7rem", fontWeight: "bold", marginBottom: "1rem", letterSpacing: "1px" }}>
          ⚙️ CONFIGURACIÓN
        </div>
        {navItems.map(n => (
          <button key={n.key} onClick={() => setSection(n.key)} style={{
            display: "flex", alignItems: "center", gap: "0.6rem",
            padding: "0.7rem 0.8rem",
            background: section === n.key ? "rgba(42,161,152,0.15)" : "transparent",
            border: `1px solid ${section === n.key ? "var(--cyan-trace)" : "transparent"}`,
            color: section === n.key ? "var(--cyan-trace)" : "var(--text-secondary)",
            borderRadius: "var(--radius-control)",
            cursor: "pointer", fontWeight: section === n.key ? "bold" : "normal",
            fontSize: "0.88rem", textAlign: "left",
            transition: "all 0.2s",
          }}>
            {n.icon} {n.label}
          </button>
        ))}
      </aside>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem" }}>

        {/* =================== USUARIOS =================== */}
        {section === "usuarios" && (
          <>
            <h2 style={{ color: "var(--mint-live)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Users size={20} /> Gestión de Usuarios
            </h2>

            {/* Create user */}
            <div style={sectionStyle}>
              <h3 style={{ color: "var(--cyan-trace)", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <UserPlus size={16} /> Crear Nuevo Usuario
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem", marginBottom: "0.8rem" }}>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Nombre Real</label>
                  <input style={inputStyle} placeholder="Pedro González" value={newUser.full_name}
                    onChange={e => setNewUser(p => ({ ...p, full_name: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Usuario</label>
                  <input style={inputStyle} placeholder="pedro.g" value={newUser.username}
                    onChange={e => setNewUser(p => ({ ...p, username: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Contraseña</label>
                  <input type="password" style={inputStyle} placeholder="••••••••" value={newUser.password}
                    onChange={e => setNewUser(p => ({ ...p, password: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Rol</label>
                  <select style={{ ...inputStyle, fontFamily: "inherit" }} value={newUser.role}
                    onChange={e => setNewUser(p => ({ ...p, role: e.target.value }))}>
                    <option value="observador">Observador</option>
                    <option value="operador">Operador</option>
                    <option value="admin">Administrador</option>
                  </select>
                </div>
              </div>
              <button style={btnPrimary} onClick={handleCreateUser}>
                <UserPlus size={16} /> Registrar Usuario
              </button>
            </div>

            {/* Users list */}
            <div style={sectionStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3 style={{ color: "var(--cyan-trace)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <Users size={16} /> Usuarios Registrados
                </h3>
                <button style={{ ...btnPrimary, background: "transparent", color: "var(--cyan-trace)", border: "1px solid var(--cyan-trace)" }}
                  onClick={loadUsers}>
                  <RefreshCw size={14} /> Actualizar
                </button>
              </div>

              {userError && (
                <div style={{ padding: "0.8rem", background: "rgba(220,50,47,0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", marginBottom: "1rem", borderRadius: "4px", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <AlertCircle size={16} /> {userError}
                </div>
              )}

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-soft)", color: "var(--text-muted)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem" }}>Nombre Real</th>
                    <th style={{ padding: "0.6rem" }}>Usuario</th>
                    <th style={{ padding: "0.6rem" }}>Rol</th>
                    <th style={{ padding: "0.6rem" }}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.username} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                      <td style={{ padding: "0.6rem" }}>{u.full_name}</td>
                      <td style={{ padding: "0.6rem", color: "var(--cyan-trace)", fontFamily: "monospace" }}>{u.username}</td>
                      <td style={{ padding: "0.6rem" }}>
                        <span style={{
                          background: u.role === "super_admin" ? "rgba(220,50,47,0.15)" : u.role === "admin" ? "rgba(42,161,152,0.15)" : "rgba(181,137,0,0.15)",
                          color: u.role === "super_admin" ? "var(--red-alert)" : u.role === "admin" ? "var(--mint-live)" : "var(--amber-warn)",
                          padding: "0.2rem 0.6rem", borderRadius: "12px", fontSize: "0.8rem", fontWeight: "bold",
                        }}>
                          {ROLES[u.role] || u.role}
                        </span>
                      </td>
                      <td style={{ padding: "0.6rem" }}>
                        {u.role !== "super_admin" && (
                          <button style={{ ...btnDanger, padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                            onClick={() => handleDeleteUser(u.username)}>
                            <Trash2 size={12} /> Eliminar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && !userError && (
                    <tr><td colSpan={4} style={{ padding: "1rem", textAlign: "center", color: "var(--text-muted)" }}>Cargando usuarios...</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* =================== NOTIFICACIONES =================== */}
        {section === "notificaciones" && (
          <>
            <h2 style={{ color: "var(--mint-live)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Bell size={20} /> Notificaciones
            </h2>

            <div style={sectionStyle}>
              <h3 style={{ color: "#0088cc", marginBottom: "1rem" }}>📱 Telegram</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                Las alertas de cambio de estado y caídas se envían por Telegram. Ingresa el token de tu Bot y el Chat ID de destino.
              </p>
              <div style={{ display: "grid", gap: "1rem", marginBottom: "1rem" }}>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Bot Token</label>
                  <input style={inputStyle} type="password" placeholder="1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={cfg["telegram_bot_token"] || ""}
                    onChange={e => setCfg(p => ({ ...p, telegram_bot_token: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Chat ID</label>
                  <input style={inputStyle} placeholder="-100xxxxxxxxx" value={cfg["telegram_chat_id"] || ""}
                    onChange={e => setCfg(p => ({ ...p, telegram_chat_id: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.8rem" }}>
                <button style={btnPrimary} onClick={() => { saveConfig("telegram_bot_token", cfg["telegram_bot_token"] || ""); saveConfig("telegram_chat_id", cfg["telegram_chat_id"] || ""); }}>
                  <Save size={16} /> Guardar Credenciales
                </button>
                <button style={{ ...btnPrimary, background: "#0088cc" }} onClick={testTelegram}>
                  <Send size={16} /> Probar Conexión
                </button>
              </div>
            </div>
          </>
        )}

        {/* =================== INTEGRACIONES =================== */}
        {section === "integraciones" && (
          <>
            <h2 style={{ color: "var(--mint-live)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Webhook size={20} /> Integraciones & Claves de API OSINT
            </h2>

            {/* OSINT API KEYS */}
            <div style={{ ...sectionStyle, border: "1px solid var(--cyan-trace)" }}>
              <h3 style={{ color: "var(--cyan-trace)", marginBottom: "0.8rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Shield size={18} /> Claves de API de Inteligencia OSINT (Opcional)
              </h3>
              <p style={{ color: "var(--text-secondary)", marginBottom: "1rem", fontSize: "0.85rem" }}>
                Permite habilitar telemetría avanzada en tiempo real para Reputación IP, Shodan e Historias de Filtraciones (HIBP).
              </p>

              {[
                { key: "abuseipdb_api_key", label: "AbuseIPDB API Key (Reputación de IP & Amenazas)", placeholder: "Ej: a1b2c3d4e5f6..." },
                { key: "shodan_api_key", label: "Shodan API Key (Infraestructura Expuesta)", placeholder: "Ej: PSKxxxxxxxxxxxxxxxxxxxx" },
                { key: "hibp_api_key", label: "Have I Been Pwned API Key (Auditoría de Fugas)", placeholder: "Ej: hbp_xxxxxxx..." },
              ].map(({ key, label, placeholder }) => (
                <div style={{ marginBottom: "1rem" }} key={key}>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>{label}</label>
                  <div style={{ display: "flex", gap: "0.8rem" }}>
                    <input style={{ ...inputStyle, flex: 1 }} type="password" placeholder={placeholder}
                      value={cfg[key] || ""}
                      onChange={e => setCfg(p => ({ ...p, [key]: e.target.value }))} />
                    <button style={btnPrimary} onClick={() => saveConfig(key, cfg[key] || "")}>
                      <Save size={16} /> Guardar
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
              Configura webhooks para recibir alertas en tus plataformas de monitoreo y gestión.
            </p>

            {[
              { key: "webhook_slack", label: "Slack", placeholder: "https://hooks.slack.com/services/..." },
              { key: "webhook_teams", label: "Microsoft Teams", placeholder: "https://outlook.office.com/webhook/..." },
              { key: "webhook_pagerduty", label: "PagerDuty", placeholder: "https://events.pagerduty.com/v2/enqueue" },
              { key: "webhook_jira", label: "Jira / Atlassian", placeholder: "https://yourcompany.atlassian.net/..." },
              { key: "webhook_generic", label: "Webhook Genérico", placeholder: "https://tu-endpoint.com/alertas" },
            ].map(({ key, label, placeholder }) => (
              <div style={sectionStyle} key={key}>
                <h3 style={{ color: "var(--cyan-trace)", marginBottom: "0.8rem" }}>{label}</h3>
                <div style={{ display: "flex", gap: "0.8rem" }}>
                  <input style={{ ...inputStyle, flex: 1 }} placeholder={placeholder}
                    value={cfg[key] || ""}
                    onChange={e => setCfg(p => ({ ...p, [key]: e.target.value }))} />
                  <button style={btnPrimary} onClick={() => saveConfig(key, cfg[key] || "")}>
                    <Save size={16} /> Guardar
                  </button>
                </div>
              </div>
            ))}
          </>
        )}


        {/* =================== SLA =================== */}
        {section === "sla" && (
          <>
            <h2 style={{ color: "var(--mint-live)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Shield size={20} /> SLA & Equipo de Soporte
            </h2>

            <div style={sectionStyle}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Nombre del Equipo / Empresa</label>
                  <input style={inputStyle} placeholder="NOC Centro" value={cfg["sla_team_name"] || ""}
                    onChange={e => setCfg(p => ({ ...p, sla_team_name: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>Correo de Soporte SLA</label>
                  <input style={inputStyle} type="email" placeholder="soporte@empresa.cl" value={cfg["sla_email"] || ""}
                    onChange={e => setCfg(p => ({ ...p, sla_email: e.target.value }))} />
                </div>
              </div>
              <button style={btnPrimary} onClick={() => { saveConfig("sla_team_name", cfg["sla_team_name"] || ""); saveConfig("sla_email", cfg["sla_email"] || ""); }}>
                <Save size={16} /> Guardar SLA
              </button>
            </div>
          </>
        )}

        {/* =================== SISTEMA =================== */}
        {section === "sistema" && (
          <>
            <h2 style={{ color: "var(--mint-live)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Sliders size={20} /> Parámetros del Sistema
            </h2>

            <div style={sectionStyle}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>
                    Intervalo de Ping (segundos)
                  </label>
                  <input style={inputStyle} type="number" min="1" max="60" placeholder="5"
                    value={cfg["ping_interval_sec"] || "5"}
                    onChange={e => setCfg(p => ({ ...p, ping_interval_sec: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>
                    Retención de Eventos (días)
                  </label>
                  <input style={inputStyle} type="number" min="1" max="365" placeholder="30"
                    value={cfg["event_retention_days"] || "30"}
                    onChange={e => setCfg(p => ({ ...p, event_retention_days: e.target.value }))} />
                </div>
                <div>
                  <label style={{ display: "block", color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "0.3rem" }}>
                    Sonido de Notificación
                  </label>
                  <select style={{ ...inputStyle, fontFamily: "inherit" }} value={cfg["notification_sound"] || "beep"}
                    onChange={e => setCfg(p => ({ ...p, notification_sound: e.target.value }))}>
                    <option value="beep">Beep estándar</option>
                    <option value="alert">Alerta</option>
                    <option value="none">Sin sonido</option>
                  </select>
                </div>
              </div>
              <button style={btnPrimary} onClick={() => {
                saveConfig("ping_interval_sec", cfg["ping_interval_sec"] || "5");
                saveConfig("event_retention_days", cfg["event_retention_days"] || "30");
                saveConfig("notification_sound", cfg["notification_sound"] || "beep");
              }}>
                <Save size={16} /> Guardar Parámetros
              </button>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ color: "var(--cyan-trace)", marginBottom: "1rem" }}>Gestión de Datos y Reportes</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                Administra tus plantillas, genera informes gerenciales y realiza respaldos de seguridad de la base de datos principal.
              </p>
              
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                {/* JSON */}
                <div style={{ background: "rgba(0,0,0,0.15)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-soft)", display: "flex", flexDirection: "column", gap: "1rem", justifyContent: "space-between" }}>
                  <div>
                    <h4 style={{ color: "var(--mint-live)", marginBottom: "0.5rem", fontSize: "0.9rem" }}>Plantilla JSON</h4>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Plantilla base para importación masiva de equipos.</p>
                  </div>
                  <button style={{ ...btnPrimary, background: "transparent", color: "var(--cyan-trace)", border: "1px solid var(--cyan-trace)", width: "100%", justifyContent: "center" }} onClick={downloadTemplate}>
                    <Download size={16} /> Descargar
                  </button>
                </div>

                {/* PDF */}
                <div style={{ background: "rgba(0,0,0,0.15)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-soft)", display: "flex", flexDirection: "column", gap: "1rem", justifyContent: "space-between" }}>
                  <div>
                    <h4 style={{ color: "var(--mint-live)", marginBottom: "0.5rem", fontSize: "0.9rem" }}>Reporte PDF</h4>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Informe gerencial del estado actual de los nodos y eventos.</p>
                  </div>
                  <button style={{ ...btnPrimary, background: "transparent", color: "var(--cyan-trace)", border: "1px solid var(--cyan-trace)", width: "100%", justifyContent: "center" }} onClick={async () => {
                    showToast("⏳ Generando reporte PDF...");
                    try {
                      const res = await fetch(`${apiBaseUrl}/api/v1/report/pdf/save`, { headers: authHeaders() });
                      if (res.ok) {
                        const data = await res.json();
                        showToast(`✅ ${data.message || "PDF generado y guardado"}`);
                      } else {
                        showToast("❌ Error al generar PDF", false);
                      }
                    } catch {
                      showToast("❌ Error de conexión al generar PDF", false);
                    }
                  }}>
                    <Download size={16} /> Generar
                  </button>
                </div>

                {/* Backup */}
                <div style={{ background: "rgba(0,0,0,0.15)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-soft)", display: "flex", flexDirection: "column", gap: "1rem", justifyContent: "space-between" }}>
                  <div>
                    <h4 style={{ color: "var(--mint-live)", marginBottom: "0.5rem", fontSize: "0.9rem" }}>Respaldo SQLite</h4>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Copia completa de la base de datos local para auditoría o respaldo.</p>
                  </div>
                  <button style={{ ...btnPrimary, background: "transparent", color: "var(--cyan-trace)", border: "1px solid var(--cyan-trace)", width: "100%", justifyContent: "center" }} onClick={async () => {
                    showToast("⏳ Generando respaldo...");
                    try {
                      const res = await fetch(`${apiBaseUrl}/api/v1/backup/db/save`, { headers: authHeaders() });
                      if (res.ok) {
                        const data = await res.json();
                        showToast(`✅ ${data.message || "Respaldo generado y guardado"}`);
                      } else {
                        showToast("❌ Error al generar respaldo", false);
                      }
                    } catch {
                      showToast("❌ Error de conexión al generar respaldo", false);
                    }
                  }}>
                    <Download size={16} /> Respaldar BBDD
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
