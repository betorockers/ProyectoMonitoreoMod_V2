"use client";

import {
  Activity,
  Cpu,
  RadioTower,
  Radar,
  RefreshCcw,
  Satellite,
  Server,
  Video,
  Download,
  AlertCircle,
  Bug,
  X,
  Copy,
  CheckCircle,
  Trash2
} from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useState, useRef } from "react";

import logoArgosGuard from "@/img/LogoArgosGuard.png";
import {
  apiBaseUrl,
  CameraStream,
  MonitorTarget,
  ProbeResult,
  TelemetrySnapshot,
  telemetrySocketUrl,
} from "@/lib/telemetry";
import { TacticalMap } from "@/components/TacticalMap";
import { IntelPanel } from "@/components/IntelPanel";
import { LoginScreen } from "@/components/LoginScreen";
import { MonitoringGrid } from "@/components/MonitoringGrid";
import { CameraViewer } from "@/components/CameraViewer";
import { EventHistory } from "@/components/EventHistory";
import { ConfigPanel } from "@/components/ConfigPanel";
import { ControlPanel } from "@/components/ControlPanel";
import { SetupWizard } from "@/components/SetupWizard";

const fallbackTargets: MonitorTarget[] = [];

export function TelemetryConsole() {
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot>({
    targets: fallbackTargets,
    results: [],
  });
  const [streams, setStreams] = useState<CameraStream[]>([]);
  const [connectionState, setConnectionState] = useState<"connecting" | "online" | "offline">(
    "connecting",
  );
  const [lastEvent, setLastEvent] = useState("Inicializando enlace local con FastAPI");
  const [activeView, setActiveView] = useState<"grid" | "map" | "intel" | "history" | "config" | "cameras">("grid");
  
  // Setup & Licensing State
  const [setupComplete, setSetupComplete] = useState<boolean>(false);
  const [licenseTier, setLicenseTier] = useState<string>("none");
  const [isLocked, setIsLocked] = useState<boolean>(false);
  
  // Auth State
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  // Toast and audio alerts state
  const [toasts, setToasts] = useState<any[]>([]);
  const previousStatusRef = useRef<Record<string, string>>({});
  const alertAudioRef = useRef<HTMLAudioElement | null>(null);
  const recoveredAudioRef = useRef<HTMLAudioElement | null>(null);

  const [userRole, setUserRole] = useState<string>("observador");

  // Bug Report system state
  const [systemErrors, setSystemErrors] = useState<any[]>([]);
  const [bugModalOpen, setBugModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deleteInput, setDeleteInput] = useState("");

  useEffect(() => {
    try {
      const token = sessionStorage.getItem("argos_token");
      if (token) setAuthToken(token);
    } catch (e) {
      console.warn("sessionStorage no disponible en inicio:", e);
    } finally {
      setIsInitializing(false);
    }
  }, []);

  useEffect(() => {
    alertAudioRef.current = new Audio("/sound/alerta.mp3");
    recoveredAudioRef.current = new Audio("/sound/recuperado.mp3");
  }, []);

  const showToast = (message: string, type: 'error' | 'success' | 'warning') => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  useEffect(() => {
    let cancelled = false;
    
    async function checkSystemStatus(retries = 5) {
      try {
        let uToken = null;
        try { uToken = sessionStorage.getItem("argos_user_token"); } catch (e) {}
        const headers: HeadersInit = {};
        if (uToken) headers["X-User-Token"] = uToken;
        
        const statusResponse = await fetch(`${apiBaseUrl}/api/v1/system/status`, { cache: "no-store", headers });
        if (statusResponse.ok && !cancelled) {
          const sysData = await statusResponse.json();
          setSetupComplete(sysData.setup_complete);
          setLicenseTier(sysData.license_tier);
          setIsLocked(sysData.is_locked);
          setUserRole(sysData.user_role || "observador");
        }
      } catch (err) {
        console.warn(`Failed to fetch system status (retries left: ${retries}):`, err);
        if (retries > 0 && !cancelled) {
          setTimeout(() => checkSystemStatus(retries - 1), 2000);
        }
      }
    }
    
    checkSystemStatus();
    
    return () => { cancelled = true; };
  }, [authToken]);

  useEffect(() => {
    let cancelled = false;
    async function loadBootstrapData() {
      if (isInitializing || !authToken || !setupComplete || isLocked) return;

      try {
        let uToken = null;
        try { uToken = sessionStorage.getItem("argos_user_token"); } catch (e) {}
        const headers: any = { "X-Argos-Token": authToken };
        if (uToken) headers["X-User-Token"] = uToken;

        const [snapshotResponse, streamsResponse] = await Promise.all([
          fetch(`${apiBaseUrl}/api/v1/snapshot`, { cache: "no-store", headers }),
          fetch(`${apiBaseUrl}/api/v1/streams`, { cache: "no-store", headers }),
        ]);

        if (!snapshotResponse.ok || !streamsResponse.ok) {
          throw new Error("bootstrap request failed");
        }

        const nextSnapshot = (await snapshotResponse.json()) as TelemetrySnapshot;
        const nextStreams = (await streamsResponse.json()) as CameraStream[];

        if (!cancelled) {
          setSnapshot(nextSnapshot);
          setStreams(nextStreams);
          setConnectionState("online");
          
          setLastEvent("Snapshot recibido desde backend local");
          showToast("Sistema iniciado. Grilla de equipos cargada.", "success");
          if (recoveredAudioRef.current) recoveredAudioRef.current.play().catch(() => {});
          
          const initialStatus: Record<string, string> = {};
          nextSnapshot.results.forEach(r => { initialStatus[r.target_id] = r.status; });
          previousStatusRef.current = initialStatus;
        }
      } catch {
        if (!cancelled) {
          setConnectionState("offline");
          setLastEvent("Backend local no disponible; usando modo standby");
        }
      }
    }

    loadBootstrapData();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const socket = new WebSocket(telemetrySocketUrl());

    socket.addEventListener("open", () => {
      setConnectionState("online");
      setLastEvent("Canal WebSocket operativo");
    });

    socket.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      if (data.error === "LICENSE_EXPIRED") {
        setIsLocked(true);
        return;
      }
      const snap = data as Partial<TelemetrySnapshot>;
      
      // Detect changes for audio/toast alerts
      if (data.results) {
        data.results.forEach((r: any) => {
          const prev = previousStatusRef.current[r.target_id];
          if (prev && prev !== r.status) {
            if (r.status === 'offline') {
              showToast(`Equipo ${r.target_id} ha caído!`, 'error');
              if (alertAudioRef.current) alertAudioRef.current.play().catch(() => {});
            } else if (r.status === 'online') {
              showToast(`Equipo ${r.target_id} se ha recuperado.`, 'success');
              if (recoveredAudioRef.current) recoveredAudioRef.current.play().catch(() => {});
            } else if (r.status === 'degraded') {
              showToast(`Equipo ${r.target_id} inestable.`, 'warning');
              if (alertAudioRef.current) alertAudioRef.current.play().catch(() => {});
            }
          }
          previousStatusRef.current[r.target_id] = r.status;
        });
      }

      setSnapshot((current) => ({
        targets: data.targets ?? current.targets,
        results: data.results ?? current.results,
      }));
    });

    socket.addEventListener("close", () => {
      setConnectionState("offline");
    });
    socket.addEventListener("error", () => {
      setConnectionState("offline");
    });

    return () => socket.close();
  }, []);

  const reloadTargets = async () => {
    if (!authToken) return;
    try {
      const headers = { "X-Argos-Token": authToken };
      const response = await fetch(`${apiBaseUrl}/api/v1/snapshot`, { cache: "no-store", headers });
      if (response.ok) {
        const nextSnapshot = await response.json();
        setSnapshot(nextSnapshot);
        showToast("Malla de equipos recargada", "success");
        if (recoveredAudioRef.current) recoveredAudioRef.current.play().catch(() => {});
      }
    } catch (err) {
      showToast("Error al recargar equipos", "error");
    }
  };

  const reloadStreams = async () => {
    if (!authToken) return;
    try {
      const uToken = sessionStorage.getItem("argos_user_token");
      const headers: any = { "X-Argos-Token": authToken };
      if (uToken) headers["X-User-Token"] = uToken;
      
      const response = await fetch(`${apiBaseUrl}/api/v1/streams`, { cache: "no-store", headers });
      if (response.ok) {
        const nextStreams = await response.json();
        setStreams(nextStreams);
      }
    } catch (err) {
      showToast("Error al recargar cámaras", "error");
    }
  };

  const handleControlAction = async (msg: string) => {
    showToast(msg, "success");
    if (recoveredAudioRef.current) recoveredAudioRef.current.play().catch(() => {});
    await reloadTargets();
  };

  const fetchSystemErrors = async () => {
    if (!authToken) return;
    try {
      const uToken = sessionStorage.getItem("argos_user_token");
      const headers: any = { "X-Argos-Token": authToken };
      if (uToken) headers["X-User-Token"] = uToken;
      const res = await fetch(`${apiBaseUrl}/api/v1/system/errors`, { headers, cache: "no-store" });
      if (res.ok) setSystemErrors(await res.json());
    } catch {}
  };

  const resolveSystemErrors = async () => {
    if (!authToken) return;
    try {
      const uToken = sessionStorage.getItem("argos_user_token");
      const headers: any = { "X-Argos-Token": authToken, "Content-Type": "application/json" };
      if (uToken) headers["X-User-Token"] = uToken;
      const res = await fetch(`${apiBaseUrl}/api/v1/system/errors/resolve`, { method: "POST", headers });
      if (res.ok) {
        setSystemErrors([]);
        setBugModalOpen(false);
        showToast("Historial de errores limpiado", "success");
      } else {
        showToast("Error al limpiar historial", "error");
      }
    } catch {
      showToast("Error de conexión", "error");
    }
  };

  useEffect(() => {
    if (authToken) { fetchSystemErrors(); }
    const interval = setInterval(() => { if (authToken) fetchSystemErrors(); }, 60000);
    return () => clearInterval(interval);
  }, [authToken]);

  // Agrupar errores por día para el modal
  const groupedErrors = () => {
    const days: Record<string, any[]> = {};
    systemErrors.forEach(err => {
      const d = new Date(err.timestamp);
      const dayName = d.toLocaleDateString('es-CL', { weekday: 'long' });
      const dateStr = d.toLocaleDateString('es-CL', { day: '2-digit', month: '2-digit', year: 'numeric' });
      const key = `${dayName.charAt(0).toUpperCase() + dayName.slice(1)} ${dateStr}`;
      if (!days[key]) days[key] = [];
      days[key].push(err);
    });
    return days;
  };

  const buildErrorReportText = () => {
    const groups = groupedErrors();
    return Object.entries(groups).map(([day, errors]) => {
      const header = `----- ${day} -----`;
      const body = errors.map(e => `[${e.timestamp}] [${e.module}] ${e.error_message}\n${e.traceback || ''}`.trim()).join('\n\n');
      return `${header}\n${body}`;
    }).join('\n\n');
  };

  const copyBugReport = () => {
    const text = buildErrorReportText();
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      showToast("Copiado al portapapeles", "success");
      setTimeout(() => setCopied(false), 2500);
    }).catch(() => {
      try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopied(true);
        showToast("Copiado al portapapeles", "success");
        setTimeout(() => setCopied(false), 2500);
      } catch (e) {
        showToast("Tu navegador no soporta el portapapeles", "error");
      }
    });
  };

  const deleteCamera = async () => {
    if (!deleteInput.trim()) { showToast("Ingresa un identificador de cámara", "warning"); return; }
    const cam = streams.find(s =>
      s.id === deleteInput.trim() ||
      s.label?.toLowerCase() === deleteInput.trim().toLowerCase() ||
      s.endpoint?.includes(deleteInput.trim())
    );
    if (!cam) { showToast("Cámara no encontrada", "error"); return; }
    const uToken = sessionStorage.getItem("argos_user_token");
    const headers: any = { "X-Argos-Token": authToken };
    if (uToken) headers["X-User-Token"] = uToken;
    const res = await fetch(`${apiBaseUrl}/api/v1/streams/${cam.id}`, { method: "DELETE", headers });
    if (res.ok) {
      showToast(`Cámara '${cam.label}' eliminada`, "success");
      setDeleteInput("");
      await reloadStreams();
    } else {
      showToast("Error al eliminar cámara", "error");
    }
  };

  const downloadReport = async () => {
    if (!authToken) return;
    showToast("Generando reporte PDF...", "success");
    try {
      const uToken = sessionStorage.getItem("argos_user_token");
      const headers: any = { "X-Argos-Token": authToken };
      if (uToken) headers["X-User-Token"] = uToken;
      
      const response = await fetch(`${apiBaseUrl}/api/v1/report/pdf/save`, { headers });
      if (response.ok) {
        const data = await response.json();
        showToast(data.message || "PDF guardado exitosamente", "success");
      } else {
        showToast("Error al generar PDF", "error");
      }
    } catch (e) {
      showToast("Error de conexión al generar PDF", "error");
    }
  };

  const getTabStyle = (id: string, isBlocked: boolean = false) => {
    const isActive = activeView === id;
    // Usar colores base de OSINT si el id es intel
    const activeColor = id === "intel" ? "var(--cyan-trace)" : "var(--mint-live)";
    
    return {
      padding: "0.6rem 1.2rem",
      background: isActive ? "var(--panel-raised)" : "rgba(0, 43, 54, 0.4)", // Contraste contra el gradiente superior
      color: isBlocked ? "var(--text-muted)" : isActive ? "#ffffff" : "var(--text-secondary)", // Texto inactivo más brillante
      border: `1px solid ${isActive ? activeColor : "rgba(131, 148, 150, 0.3)"}`, // Borde más definido
      borderRadius: "var(--radius-control)",
      cursor: isBlocked ? "not-allowed" : "pointer",
      fontWeight: isActive ? "bold" : "600",
      boxShadow: isActive ? `0 0 10px ${id === "intel" ? "rgba(38, 139, 210, 0.4)" : "rgba(42,161,152,0.4)"}` : "0 2px 4px rgba(0,0,0,0.2)",
      transition: "all 0.2s ease",
      opacity: isBlocked ? 0.5 : 1
    };
  };

  const handleTabClick = (view: any, minTier: string) => {
    if (licenseTier === "BASICO" && (minTier === "ESTANDAR" || minTier === "ENTERPRISE")) {
      showToast(`Upgrade a ${minTier} requerido para esta función.`, "warning");
      return;
    }
    setActiveView(view);
  };

  if (isInitializing) {
    return <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--void)", color: "var(--cyan-trace)" }}>INICIALIZANDO TERMINAL...</div>;
  }

  if (!setupComplete) {
    return <SetupWizard onComplete={() => setSetupComplete(true)} />;
  }

  if (!authToken) {
    return <LoginScreen onLoginSuccess={(token) => {
      try {
        sessionStorage.setItem("argos_token", token);
      } catch (e) {
        console.warn("sessionStorage no disponible:", e);
      }
      setAuthToken(token);
    }} />;
  }

  if (isLocked) {
    return (
      <div style={{ padding: "4rem", textAlign: "center", background: "var(--void)", color: "var(--red-alert)", height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <h1>ACCESO BLOQUEADO</h1>
        <p>El sistema requiere activación. Por favor, ingrese una licencia válida.</p>
        <button onClick={() => setSetupComplete(false)} style={{ marginTop: "2rem", padding: "1rem", background: "transparent", color: "var(--cyan-trace)", border: "1px solid var(--cyan-trace)", cursor: "pointer" }}>Abrir Asistente</button>
      </div>
    );
  }

  return (
    <main className="shell">
      <section className="topbar" aria-label="Estado operacional">
        <div className="brand-mark">
          <Image
            src={logoArgosGuard}
            alt="Argos Guard Enterprise"
            className="brand-logo"
            priority
          />
          <div>
            <p style={{ color: "var(--text-primary)" }}>Argos Guard Enterprise</p>
            <span style={{ color: "var(--cyan-trace)" }}>Desktop tactical console / v3.6.3</span>
          </div>
        </div>
        
        {/* Pestañas Principales Top */}
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button onClick={() => handleTabClick("grid", "BASICO")} style={getTabStyle("grid")}>Monitoreo Activo</button>
          <button onClick={() => handleTabClick("map", "ESTANDAR")} style={getTabStyle("map", licenseTier === "BASICO")}>Mapa Táctico</button>
          <button onClick={() => handleTabClick("history", "BASICO")} style={getTabStyle("history")}>Historial Eventos</button>
          
          {(userRole === "super_admin" || userRole === "admin" || userRole === "operador") && (
            <button onClick={() => handleTabClick("cameras", "ENTERPRISE")} style={{ ...getTabStyle("cameras", licenseTier !== "ENTERPRISE" && licenseTier !== "TRIAL" && licenseTier !== "DEV"), lineHeight: "1.1" }}>Video<br/>Vigilancia</button>
          )}
          
          {(userRole === "super_admin" || userRole === "admin" || userRole === "operador") && (
            <button onClick={() => handleTabClick("intel", "ENTERPRISE")} style={getTabStyle("intel", licenseTier !== "ENTERPRISE" && licenseTier !== "TRIAL" && licenseTier !== "DEV")}>OSINT</button>
          )}
          
          {(userRole === "super_admin" || userRole === "admin") && (
            <button onClick={() => handleTabClick("config", "BASICO")} style={getTabStyle("config")}>Configuración</button>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", minWidth: "100px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <div className={`ops-state ${connectionState}`} style={{ flex: 1, margin: 0, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 0.5rem" }}>
              <span className="state-dot" />
              API {connectionState.toUpperCase()}
            </div>
            {/* Icono Bug parpadeante */}
            <button
              title={systemErrors.length > 0 ? `${systemErrors.length} error(es) activo(s)` : "Sin errores"}
              onClick={() => { fetchSystemErrors(); setBugModalOpen(true); }}
              style={{
                background: "transparent",
                border: systemErrors.length > 0 ? "1px solid var(--red-alert)" : "1px solid var(--border-soft)",
                borderRadius: "4px",
                cursor: "pointer",
                color: systemErrors.length > 0 ? "var(--red-alert)" : "var(--text-muted)",
                padding: "0.2rem 0.35rem",
                display: "flex",
                alignItems: "center",
                animation: systemErrors.length > 0 ? "bugBlink 1.2s step-start infinite" : "none"
              }}
            >
              <Bug size={15} />
            </button>
          </div>

          <button 
            onClick={() => {
              sessionStorage.removeItem("argos_token");
              sessionStorage.removeItem("argos_user_token");
              setAuthToken(null);
              // Señal para PyQt6: cerrar la ventana nativa y todos sus subprocesos
              console.log("ARGOS_LOGOUT_CLOSE");
            }}
            style={{
              flex: 1,
              background: "rgba(220, 50, 47, 0.1)",
              border: "1px solid var(--red-alert)",
              color: "var(--red-alert)",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.65rem",
              fontWeight: "bold",
              textTransform: "uppercase",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "0 0.5rem"
            }}
          >
            CERRAR SESIÓN
          </button>
        </div>

        {/* MODAL BUG REPORT */}
        {bugModalOpen && (
          <div style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 9999,
            display: "flex", alignItems: "center", justifyContent: "center"
          }}>
            <div style={{
              background: "var(--panel-raised)", border: "1px solid var(--red-alert)",
              borderRadius: "var(--radius-panel)", padding: "1.5rem", width: "min(720px, 92vw)",
              maxHeight: "80vh", display: "flex", flexDirection: "column", gap: "1rem",
              boxShadow: "0 0 40px rgba(220,50,47,0.3)"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", color: "var(--red-alert)" }}>
                  <Bug size={20} />
                  <strong style={{ fontSize: "1.1rem" }}>Diagnóstico de Errores del Sistema</strong>
                </div>
                <button onClick={() => setBugModalOpen(false)} style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)" }}><X size={20} /></button>
              </div>

              {systemErrors.length === 0 ? (
                <div style={{ textAlign: "center", color: "var(--mint-live)", padding: "2rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
                  <CheckCircle size={32} />
                  <p>Sin errores activos en las últimas 48 horas</p>
                </div>
              ) : (
                <div style={{ overflowY: "auto", flex: 1, fontFamily: "monospace", fontSize: "0.78rem", background: "var(--panel-inset)", padding: "1rem", borderRadius: "var(--radius-control)", color: "var(--text-secondary)" }}>
                  {Object.entries(groupedErrors()).map(([day, errors]) => (
                    <div key={day} style={{ marginBottom: "1.5rem" }}>
                      <div style={{ color: "var(--amber-warn)", fontWeight: "bold", borderBottom: "1px solid var(--border-soft)", paddingBottom: "0.25rem", marginBottom: "0.75rem" }}>
                        ----- {day} -----
                      </div>
                      {errors.map((err, i) => (
                        <div key={i} style={{ marginBottom: "1rem", borderLeft: "2px solid var(--red-alert)", paddingLeft: "0.75rem" }}>
                          <div style={{ color: "var(--red-alert)", fontWeight: "bold" }}>[{err.module}] — {new Date(err.timestamp).toLocaleTimeString('es-CL')}</div>
                          <div style={{ color: "var(--text-primary)", marginTop: "0.2rem" }}>{err.error_message}</div>
                          {err.traceback && <pre style={{ color: "var(--text-muted)", fontSize: "0.7rem", marginTop: "0.3rem", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{err.traceback}</pre>}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                {(userRole === "super_admin" || userRole === "admin") && systemErrors.length > 0 && (
                  <button onClick={resolveSystemErrors} style={{
                    background: "rgba(220,50,47,0.1)", border: "1px solid var(--red-alert)",
                    color: "var(--red-alert)", borderRadius: "var(--radius-control)",
                    padding: "0.5rem 1rem", cursor: "pointer", fontWeight: "bold", fontSize: "0.85rem"
                  }}>Limpiar Historial</button>
                )}
                <button
                  onClick={copyBugReport}
                  disabled={systemErrors.length === 0}
                  style={{
                    background: copied ? "var(--mint-live)" : "var(--panel)",
                    border: "1px solid var(--border-soft)", color: copied ? "var(--void)" : "var(--text-primary)",
                    borderRadius: "var(--radius-control)", padding: "0.5rem 1rem",
                    cursor: systemErrors.length === 0 ? "not-allowed" : "pointer",
                    fontWeight: "bold", fontSize: "0.85rem",
                    display: "flex", alignItems: "center", gap: "0.4rem"
                  }}
                >
                  {copied ? <><CheckCircle size={15} /> Copiado!</> : <><Copy size={15} /> Copiar para Soporte</>}
                </button>
              </div>
              <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textAlign: "center" }}>El log se limpia automáticamente cada 48 horas. Copie el contenido y envíelo al correo de soporte.</p>
            </div>
          </div>
        )}
      </section>

      {/* Reemplazamos command-grid por un layout de 2 columnas donde la derecha es Control Panel o Formulario */}
      <section style={{ display: "grid", gridTemplateColumns: (activeView === "grid" || activeView === "cameras") && (userRole === "super_admin" || userRole === "admin") ? "1fr 240px" : "1fr", flex: 1, gap: "14px", marginTop: "14px", overflow: "hidden" }}>
        
        <section className="map-panel" aria-label="Vista Principal" style={{ background: "var(--panel-inset)", height: "100%", overflow: "hidden", position: "relative" }}>
          {activeView === "grid" && <MonitoringGrid targets={snapshot.targets} results={snapshot.results} />}
          {activeView === "map" && (
            <>
              <div className="panel-heading compact" style={{ position: "absolute", zIndex: 10, padding: "1rem" }}>
                <div>
                  <span className="eyebrow" style={{ color: "var(--cyan-trace)" }}>Capa MapCN preparada</span>
                  <h1 style={{ marginTop: "0.25rem" }}>Malla de vigilancia geográfica</h1>
                </div>
              </div>
              <TacticalMap targets={snapshot.targets} results={snapshot.results} />
            </>
          )}
          {activeView === "intel" && <IntelPanel />}
          {activeView === "history" && <EventHistory targets={snapshot.targets} />}
          {activeView === "config" && <ConfigPanel />}
          {activeView === "cameras" && <CameraViewer streams={streams} onReload={reloadStreams} />}
          
          {/* TOAST CONTAINER */}
          <div style={{ position: "absolute", bottom: "130px", right: "20px", display: "flex", flexDirection: "column", gap: "10px", zIndex: 1000 }}>
            {toasts.map(t => (
              <div key={t.id} style={{
                background: "var(--panel-raised)",
                borderLeft: `4px solid ${t.type === 'error' ? 'var(--red-alert)' : t.type === 'success' ? 'var(--mint-live)' : 'var(--amber-warn)'}`,
                padding: "1rem",
                borderRadius: "var(--radius-control)",
                color: "var(--text-primary)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                animation: "slideIn 0.3s ease"
              }}>
                <AlertCircle color={t.type === 'error' ? 'var(--red-alert)' : t.type === 'success' ? 'var(--mint-live)' : 'var(--amber-warn)'} />
                <span style={{ fontSize: "0.9rem", fontWeight: "bold" }}>{t.message}</span>
              </div>
            ))}
          </div>

        </section>

        {activeView === "grid" && (userRole === "super_admin" || userRole === "admin") && (
          <aside style={{ background: "var(--panel-inset)", border: "1px solid var(--border-soft)", borderRadius: "var(--radius-panel)", display: "flex", flexDirection: "column", overflowY: "auto", overflowX: "hidden" }}>
            {(() => {
              const handleControlAction = (msg: string, type: 'success' | 'error' = 'success') => {
                showToast(msg, type);
                reloadTargets();
              };
              return (
                <ControlPanel onActionMsg={handleControlAction} onReload={reloadTargets} />
              );
            })()}
          </aside>
        )}
        {activeView === "cameras" && (userRole === "super_admin" || userRole === "admin") && (
          <aside style={{ background: "var(--panel-inset)", border: "1px solid var(--border-soft)", borderRadius: "var(--radius-panel)", display: "flex", flexDirection: "column", padding: "1rem", overflowY: "auto", overflowX: "hidden", gap: "1rem" }}>

            {/* Indicador de streams activos */}
            <div style={{ textAlign: "center", padding: "0.5rem", background: "var(--panel-raised)", borderRadius: "var(--radius-control)", border: "1px solid var(--border-soft)" }}>
              <span style={{ color: "var(--cyan-trace)", fontWeight: "bold", fontSize: "0.85rem", letterSpacing: "0.05em" }}>
                📹 CCTV RED: {streams.filter(s => (s as any).status === 'active').length || streams.length} ACTIVOS
              </span>
            </div>

            {/* Formulario: Añadir Cámara */}
            <h3 style={{ color: "var(--cyan-trace)", fontSize: "1rem", margin: 0 }}>Añadir Cámara</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              const data = Object.fromEntries(fd.entries());
              const streamData = {
                id: "cam-" + Math.random().toString(36).substring(2, 8),
                label: data.label,
                protocol: data.protocol,
                endpoint: data.endpoint
              };
              const uToken = sessionStorage.getItem("argos_user_token");
              const headers: any = { "Content-Type": "application/json", "X-Argos-Token": authToken };
              if (uToken) headers["X-User-Token"] = uToken;
              const res = await fetch(`${apiBaseUrl}/api/v1/streams`, {
                method: 'POST', headers, body: JSON.stringify(streamData)
              });
              if (res.ok) {
                showToast("Cámara añadida con éxito", "success");
                (e.target as HTMLFormElement).reset();
                await reloadStreams();
              } else {
                showToast("Error al añadir cámara", "error");
              }
            }} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <input name="label" type="text" placeholder="Nombre / Etiqueta" required style={{ padding: "0.5rem", borderRadius: "var(--radius-control)", border: "1px solid var(--border-soft)", background: "var(--panel)", color: "var(--text-primary)", fontSize: "0.85rem" }} />
              <select name="protocol" required style={{ padding: "0.5rem", borderRadius: "var(--radius-control)", border: "1px solid var(--border-soft)", background: "var(--panel)", color: "var(--text-primary)", fontSize: "0.85rem" }}>
                <option value="RTSP">RTSP (Real Time Streaming)</option>
                <option value="WebRTC">WebRTC</option>
                <option value="HLS">HLS (HTTP Live Streaming)</option>
                <option value="MJPEG">MJPEG</option>
              </select>
              <input name="endpoint" type="text" placeholder="URL del Endpoint" required style={{ padding: "0.5rem", borderRadius: "var(--radius-control)", border: "1px solid var(--border-soft)", background: "var(--panel)", color: "var(--text-primary)", fontSize: "0.85rem" }} />
              <button type="submit" style={{ padding: "0.5rem", background: "var(--cyan-trace)", color: "var(--void)", border: "none", borderRadius: "var(--radius-control)", cursor: "pointer", fontWeight: "bold", fontSize: "0.85rem" }}>Guardar Cámara</button>
            </form>

            {/* Separador */}
            <hr style={{ border: "none", borderTop: "1px solid var(--border-soft)", margin: "0.25rem 0" }} />

            {/* Eliminar Cámara */}
            <h3 style={{ color: "var(--red-alert)", fontSize: "1rem", margin: 0 }}>Eliminar Cámara</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <input
                type="text"
                placeholder="Nombre, IP o ID de cámara"
                value={deleteInput}
                onChange={e => setDeleteInput(e.target.value)}
                style={{ padding: "0.5rem", borderRadius: "var(--radius-control)", border: "1px solid var(--red-alert)", background: "var(--panel)", color: "var(--text-primary)", fontSize: "0.85rem" }}
              />
              <button
                onClick={deleteCamera}
                style={{ padding: "0.5rem", background: "rgba(220,50,47,0.15)", color: "var(--red-alert)", border: "1px solid var(--red-alert)", borderRadius: "var(--radius-control)", cursor: "pointer", fontWeight: "bold", fontSize: "0.85rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.4rem" }}
              >
                <Trash2 size={15} /> Eliminar Cámara
              </button>
            </div>

          </aside>
        )}
      </section>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes bugBlink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.1; }
        }
      `}} />
    </main>
  );
}
