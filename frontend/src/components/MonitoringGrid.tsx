"use client";

import { useState, useRef, useEffect } from "react";
import { MonitorTarget, ProbeResult } from "@/lib/telemetry";
import { Activity, XCircle, CheckCircle, Clock, X, Shield, Globe, Network } from "lucide-react";

interface Props {
  targets: MonitorTarget[];
  results: ProbeResult[];
}

export function MonitoringGrid({ targets, results }: Props) {
  const [selectedTarget, setSelectedTarget] = useState<MonitorTarget | null>(null);
  const [order, setOrder] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem("argos_grid_order");
    if (saved) {
      try {
        setOrder(JSON.parse(saved));
      } catch (e) {}
    }
  }, []);

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData("target_id", id);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, dropId: string) => {
    e.preventDefault();
    const dragId = e.dataTransfer.getData("target_id");
    if (dragId === dropId || !dragId) return;

    const currentOrder = getEffectiveTargets().map(t => t.id);
    const dragIdx = currentOrder.indexOf(dragId);
    const dropIdx = currentOrder.indexOf(dropId);
    if (dragIdx === -1 || dropIdx === -1) return;

    const newOrder = [...currentOrder];
    newOrder.splice(dragIdx, 1);
    newOrder.splice(dropIdx, 0, dragId);

    setOrder(newOrder);
    localStorage.setItem("argos_grid_order", JSON.stringify(newOrder));
  };

  const getEffectiveTargets = () => {
    const effective = [...targets];
    if (order.length > 0) {
      effective.sort((a, b) => {
        const idxA = order.indexOf(a.id);
        const idxB = order.indexOf(b.id);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return 0;
      });
    }
    return effective;
  };
  
  // Close on click outside
  const overlayRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (overlayRef.current && !overlayRef.current.contains(event.target as Node)) {
        setSelectedTarget(null);
      }
    };
    if (selectedTarget) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [selectedTarget]);
  return (
    <div className="monitoring-grid" style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(5cm, 1fr))",
      gap: "0.15rem",
      padding: "0.2rem",
      overflowY: "auto",
      height: "100%",
      justifyItems: "center"
    }}>
      {getEffectiveTargets().map(target => {
        const result = results.find(r => r.target_id === target.id);
        const isOnline = result?.status === "online";
        const isDegraded = result?.status === "degraded";
        
        let bgColor = "var(--panel-inset)";
        let iconColor = "var(--text-muted)";
        let borderColor = "var(--border-soft)";
        
        if (isOnline) {
          bgColor = "rgba(42, 161, 152, 0.15)";
          borderColor = "var(--mint-live)";
          iconColor = "var(--mint-live)";
        } else if (isDegraded) {
          bgColor = "rgba(181, 137, 0, 0.15)";
          borderColor = "var(--amber-warn)";
          iconColor = "var(--amber-warn)";
        } else if (result?.status === "offline") {
          bgColor = "rgba(220, 50, 47, 0.25)";
          borderColor = "var(--red-alert)";
          iconColor = "var(--red-alert)";
        }

        const macAddress = target.mac_address || result?.mac_address || "00:00:00:00:00:00";

        return (
          <div 
            key={target.id} 
            draggable
            onDragStart={(e) => handleDragStart(e, target.id)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, target.id)}
            onClick={() => setSelectedTarget(target)} 
            style={{
            background: bgColor,
            border: `2px solid ${borderColor}`,
            borderRadius: "var(--radius-panel)",
            padding: "0.25rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            width: "5cm",
            height: "4.5cm",
            transition: "all 0.3s ease",
            overflow: "hidden",
            cursor: "grab"
          }}>
            <h3 style={{ margin: "0 0 0.25rem 0", fontSize: "0.9rem", color: isOnline ? "var(--mint-live)" : isDegraded ? "var(--amber-warn)" : "var(--red-alert)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", width: "100%" }} title={target.label}>
              {target.label}
            </h3>
            
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: "0.5rem" }}>
              {isOnline && <CheckCircle size={24} color={iconColor} style={{ margin: "0.25rem 0" }} />}
              {isDegraded && <Clock size={24} color={iconColor} style={{ margin: "0.25rem 0" }} />}
              {(!isOnline && !isDegraded) && <XCircle size={24} color={iconColor} style={{ margin: "0.25rem 0" }} />}
              <strong style={{ color: iconColor, fontSize: "0.75rem" }}>
                {isOnline ? "Conectado" : isDegraded ? "Inestable" : "Offline"}
              </strong>
            </div>

            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", width: "100%", display: "flex", flexDirection: "column", gap: "2px" }}>
              <span style={{ fontFamily: "monospace", background: "rgba(0,0,0,0.3)", padding: "2px", borderRadius: "3px" }}>IP: {target.host}</span>
              <span style={{ fontFamily: "monospace", background: "rgba(0,0,0,0.3)", padding: "2px", borderRadius: "3px" }}>MAC: {macAddress}</span>
              {target.country && <span style={{ fontFamily: "monospace", background: "rgba(0,0,0,0.3)", padding: "2px", borderRadius: "3px" }}>País: {target.country}</span>}
            </div>
          </div>
        );
      })}

      {selectedTarget && (
        <div style={{
          position: "fixed",
          top: "106px",
          right: "20px",
          width: "240px",
          height: "calc(100vh - 126px)",
          background: "rgba(0, 43, 54, 0.95)",
          backdropFilter: "blur(10px)",
          border: "1px solid var(--cyan-trace)",
          borderRadius: "var(--radius-panel)",
          boxShadow: "-5px 0 20px rgba(0,0,0,0.8)",
          zIndex: 1000,
          display: "flex",
          flexDirection: "column"
        }} ref={overlayRef}>
          <div style={{ padding: "1rem", borderBottom: "1px solid var(--border-soft)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, color: "var(--text-primary)" }}>Detalles del Objetivo</h3>
            <button onClick={() => setSelectedTarget(null)} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
              <X size={20} />
            </button>
          </div>
          <div style={{ padding: "1rem", display: "flex", flexDirection: "column", gap: "1rem", overflowY: "auto" }}>
            <div>
              <strong style={{ color: "var(--mint-live)" }}>{selectedTarget.label}</strong>
              <div style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>{selectedTarget.host}</div>
            </div>
            
            <div style={{ display: "grid", gap: "0.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem", background: "var(--panel-inset)", padding: "0.5rem", borderRadius: "4px" }}>
                <Globe size={16} color="var(--blue-marine)" /> 
                <span style={{ color: "var(--text-muted)" }}>País:</span> 
                <span>{selectedTarget.country || "Desconocido"}</span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem", background: "var(--panel-inset)", padding: "0.5rem", borderRadius: "4px" }}>
                <Network size={16} color="var(--blue-marine)" /> 
                <span style={{ color: "var(--text-muted)" }}>ISP:</span> 
                <span>{selectedTarget.isp || "Desconocido"}</span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem", background: "var(--panel-inset)", padding: "0.5rem", borderRadius: "4px" }}>
                <Shield size={16} color="var(--amber-warn)" /> 
                <span style={{ color: "var(--text-muted)" }}>ASN:</span> 
                <span>{selectedTarget.asn || "Desconocido"}</span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.9rem", background: "var(--panel-inset)", padding: "0.5rem", borderRadius: "4px" }}>
                <Activity size={16} color="var(--red-alert)" /> 
                <span style={{ color: "var(--text-muted)" }}>Intel:</span> 
                <span>{selectedTarget.threat_intel || "No disponible"}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
