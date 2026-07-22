"use client";

import { useState, useRef, useEffect } from "react";
import { apiBaseUrl } from "@/lib/telemetry";

export function ControlPanel({ onReload, onActionMsg }: { onReload?: () => void, onActionMsg?: (msg: string, type: 'success' | 'error') => void }) {
  const [ip, setIp] = useState("");
  const [label, setLabel] = useState("");
  const [instalacion, setInstalacion] = useState("");
  const [pingInterval, setPingInterval] = useState("5");
  const [deleteIp, setDeleteIp] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getHeaders = () => {
    const token = sessionStorage.getItem("argos_token") || "";
    const uToken = sessionStorage.getItem("argos_user_token") || "";
    return {
      "Content-Type": "application/json",
      "X-Argos-Token": token,
      "X-User-Token": uToken
    };
  };

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/config`, { headers: getHeaders() });
        if (res.ok) {
          const data = await res.json();
          if (data.ping_interval_sec) {
            setPingInterval(data.ping_interval_sec);
          }
        }
      } catch (err) {
        console.error("Failed to load config", err);
      }
    };
    loadConfig();
  }, []);

  const handleReload = () => {
    if (onReload) onReload();
  };

  const handleAdd = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!ip || !label || !instalacion) {
      if (onActionMsg) onActionMsg("Ingresa IP, nombre e instalación", "error");
      return;
    }
    const targetId = ip.replace(/\./g, "-");
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/targets`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          id: targetId,
          label,
          host: ip,
          port: 443,
          protocol: "tcp",
          instalacion: instalacion
        })
      });
      if (!res.ok) throw new Error("Error al agregar equipo");
      setIp("");
      setLabel("");
      setInstalacion("");
      if (onActionMsg) onActionMsg("Equipo agregado exitosamente", "success");
      else if (onReload) onReload();
    } catch (err) {
      if (onActionMsg) onActionMsg("Error al agregar el nodo", "error");
    }
  };

  const handleDelete = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!deleteIp) {
      if (onActionMsg) onActionMsg("Ingresa una IP para eliminar", "error");
      return;
    }
    const targetId = deleteIp.replace(/\./g, "-");
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/targets/${targetId}`, {
        method: "DELETE",
        headers: getHeaders()
      });
      if (!res.ok) throw new Error("Error al eliminar equipo");
      setDeleteIp("");
      if (onActionMsg) onActionMsg("Equipo eliminado exitosamente", "success");
      else if (onReload) onReload();
    } catch (err) {
      if (onActionMsg) onActionMsg("Error al eliminar el nodo", "error");
    }
  };



  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const token = getHeaders()["X-Argos-Token"];
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/system/import?token=${token}`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error("Error al importar");
      if (onActionMsg) onActionMsg("Equipos y configuración cargados", "success");
    } catch (err) {
      if (onActionMsg) onActionMsg("Error al cargar la configuración", "error");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (onReload) onReload();
  };

  return (
    <div style={{ padding: "0.5rem 1rem", display: "flex", flexDirection: "column", gap: "0.6rem", height: "100%", overflowY: "auto", fontFamily: "Inter, sans-serif" }}>
      <div style={{ textAlign: "left", marginBottom: "0.2rem" }}>
        <h3 style={{ color: "var(--cyan-trace)", fontSize: "1.1rem", margin: 0 }}>Panel de Control</h3>
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Gestión de Nodos TCP</span>
      </div>

      <button onClick={handleReload} style={{ width: "100%", background: "rgba(42, 161, 152, 0.15)", border: "1px solid var(--mint-live)", color: "var(--mint-live)", padding: "0.5rem", borderRadius: "var(--radius-control)", cursor: "pointer", fontSize: "0.85rem", fontWeight: "bold" }}>
        Recargar Equipos
      </button>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "bold" }}>Intervalo Ping (s)</label>
        <input 
          type="number" 
          value={pingInterval} 
          onChange={e => setPingInterval(e.target.value)}
          style={{ background: "var(--panel)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", padding: "0.4rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem" }}
        />
      </div>

      <div style={{ height: "1px", background: "var(--border-soft)", margin: "0.2rem 0" }} />

      <form onSubmit={handleAdd} style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "bold" }}>Agregar Nodo (IP o Dominio)</label>
        <input 
          placeholder="ej. 192.168.1.1 o betograf.cl" 
          value={ip} 
          onChange={e => setIp(e.target.value.trim().toLowerCase())}
          required
          style={{ background: "var(--panel)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", padding: "0.4rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem" }}
        />
        <input 
          placeholder="ej. Servidor Core" 
          value={label} 
          onChange={e => setLabel(e.target.value)}
          required
          style={{ background: "var(--panel)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", padding: "0.4rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem" }}
        />
        <input 
          placeholder="ej. Quilicura Norte" 
          value={instalacion} 
          onChange={e => setInstalacion(e.target.value)}
          required
          style={{ background: "var(--panel)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", padding: "0.4rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem" }}
        />
        <button type="submit" style={{ background: "var(--mint-live)", color: "var(--void)", border: "none", padding: "0.5rem", borderRadius: "var(--radius-control)", cursor: "pointer", fontWeight: "bold", fontSize: "0.85rem", marginTop: "0.2rem", transition: "opacity 0.2s" }}>
          Guardar Equipo
        </button>
      </form>

      <div style={{ height: "1px", background: "var(--border-soft)", margin: "0.2rem 0" }} />

      <form onSubmit={handleDelete} style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "bold" }}>Eliminar Nodo (IP o Dominio)</label>
        <input 
          placeholder="ej. 192.168.1.1 o betograf.cl" 
          value={deleteIp} 
          onChange={e => setDeleteIp(e.target.value.trim().toLowerCase())}
          required
          style={{ background: "var(--panel)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", padding: "0.4rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem" }}
        />
        <button type="submit" style={{ background: "transparent", color: "var(--red-alert)", border: "1px solid var(--red-alert)", padding: "0.5rem", borderRadius: "var(--radius-control)", cursor: "pointer", fontWeight: "bold", fontSize: "0.85rem", marginTop: "0.2rem" }}>
          Eliminar Equipo
        </button>
      </form>

      <div style={{ marginTop: "1rem", paddingTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <input 
          type="file" 
          accept=".json" 
          ref={fileInputRef} 
          style={{ display: "none" }} 
          onChange={handleImport} 
        />
        <button onClick={() => fileInputRef.current?.click()} style={{ width: "100%", background: "rgba(42, 161, 152, 0.15)", border: "1px solid var(--mint-live)", color: "var(--mint-live)", padding: "0.5rem", borderRadius: "var(--radius-control)", cursor: "pointer", fontSize: "0.85rem", fontWeight: "bold" }}>
          Cargar Equipos
        </button>
      </div>
    </div>
  );
}
