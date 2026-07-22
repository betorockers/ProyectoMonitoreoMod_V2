"use client";

import { useState, useEffect } from "react";
import { Globe, MapPin, Search, Car, User, ShieldAlert, KeyRound, Server, FileText } from "lucide-react";
import { apiBaseUrl } from "@/lib/telemetry";

type OsintResult = {
  status: string;
  data: any;
  message: string;
  risk_level?: string;
};

type TabType = "ppu" | "rut" | "ip" | "dns" | "ports" | "subdomains" | "email" | "geoclima" | "web" | "ping" | "breach" | "threat" | "shodan" | "whois";

type TabState = {
  query: string;
  result: OsintResult | null;
  error: string | null;
};

export function IntelPanel() {
  const [activeTab, setActiveTab] = useState<TabType>("ppu");
  const [loadingStore, setLoadingStore] = useState<Partial<Record<TabType, boolean>>>({});
  const [tabStore, setTabStore] = useState<Partial<Record<TabType, TabState>>>({});

  // Current tab getters
  const currentQuery = tabStore[activeTab]?.query || "";
  const currentResult = tabStore[activeTab]?.result || null;
  const currentError = tabStore[activeTab]?.error || null;
  const isCurrentLoading = !!loadingStore[activeTab];

  // Restore state from sessionStorage on mount
  useEffect(() => {
    try {
      const savedTab = sessionStorage.getItem("intel_activeTab");
      const savedStore = sessionStorage.getItem("intel_tabStore");

      if (savedTab) setActiveTab(savedTab as TabType);
      if (savedStore) setTabStore(JSON.parse(savedStore));
    } catch (e) {
      console.warn("Failed to restore IntelPanel state", e);
    }
  }, []);

  // Save state on changes
  useEffect(() => {
    sessionStorage.setItem("intel_activeTab", activeTab);
    sessionStorage.setItem("intel_tabStore", JSON.stringify(tabStore));
  }, [activeTab, tabStore]);

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
  };

  const setTabQuery = (val: string) => {
    setTabStore(prev => ({
      ...prev,
      [activeTab]: {
        ...(prev[activeTab] || { result: null, error: null }),
        query: val
      }
    }));
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const queryToSearch = currentQuery;
    const targetTab = activeTab;
    if (!queryToSearch) return;

    setLoadingStore(prev => ({ ...prev, [targetTab]: true }));
    setTabStore(prev => ({
      ...prev,
      [targetTab]: { query: queryToSearch, result: null, error: null }
    }));

    try {
      let endpoint = "";
      if (targetTab === "ppu") endpoint = "/api/v1/osint/ppu";
      else if (targetTab === "rut") endpoint = "/api/v1/osint/rut";
      else if (targetTab === "geoclima") endpoint = "/api/v1/osint/geoclima";
      else if (targetTab === "web") endpoint = "/api/v1/osint/web";
      else if (targetTab === "ip") endpoint = "/api/v1/osint/ip";
      else if (targetTab === "dns") endpoint = "/api/v1/osint/dns";
      else if (targetTab === "ports") endpoint = "/api/v1/osint/ports";
      else if (targetTab === "subdomains") endpoint = "/api/v1/osint/subdomains";
      else if (targetTab === "email") endpoint = "/api/v1/osint/email";
      else if (targetTab === "ping") endpoint = "/api/v1/osint/traceroute";
      else if (targetTab === "breach") endpoint = "/api/v1/osint/breach";
      else if (targetTab === "threat") endpoint = "/api/v1/osint/threat";
      else if (targetTab === "shodan") endpoint = "/api/v1/osint/shodan";
      else if (targetTab === "whois") endpoint = "/api/v1/osint/whois";

      const payload = (targetTab === "ppu" || targetTab === "rut") ? { [targetTab]: queryToSearch } : { query: queryToSearch };
      const token = sessionStorage.getItem("argos_token") || "";

      const res = await fetch(`${apiBaseUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Argos-Token": token
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("Error en la consulta u origen denegado.");
      }

      const data = await res.json();
      setTabStore(prev => ({
        ...prev,
        [targetTab]: { query: queryToSearch, result: data, error: null }
      }));
    } catch (err: any) {
      setTabStore(prev => ({
        ...prev,
        [targetTab]: { query: queryToSearch, result: null, error: err.message || "Error de red al conectar con módulo OSINT" }
      }));
    } finally {
      setLoadingStore(prev => ({ ...prev, [targetTab]: false }));
    }
  };
;

  const getRiskColorAndLabel = (res: OsintResult) => {
    const risk = res.risk_level?.toUpperCase() || "LOW";
    if (risk === "HIGH") {
      return { color: "#dc322f", glow: "0 0 14px #dc322f", label: "NIVEL CRÍTICO (ALTO RIESGO)", bg: "rgba(220, 50, 47, 0.15)", border: "#dc322f" };
    }
    if (risk === "MEDIUM") {
      return { color: "#b58900", glow: "0 0 14px #b58900", label: "ADVERTENCIA (RIESGO MODERADO)", bg: "rgba(181, 137, 0, 0.15)", border: "#b58900" };
    }
    return { color: "#2aa198", glow: "0 0 14px #2aa198", label: "SEGURO (SIN AMENAZAS / RIESGO BAJO)", bg: "rgba(42, 161, 152, 0.15)", border: "#2aa198" };
  };

  const renderValue = (val: any): React.ReactNode => {
    if (Array.isArray(val)) {
      return (
        <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
          {val.map((v, i) => <li key={i}>{renderValue(v)}</li>)}
        </ul>
      );
    } else if (typeof val === "object" && val !== null) {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
          {Object.entries(val).map(([k, v]) => (
            <div key={k}>
              <strong style={{ color: "var(--cyan-trace)" }}>{k.replace(/_/g, " ")}: </strong>
              {renderValue(v)}
            </div>
          ))}
        </div>
      );
    } else {
      const strVal = String(val);
      if (strVal.includes("\\n") || strVal.includes("\n")) {
        return <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "monospace" }}>{strVal}</pre>;
      }
      return <span>{strVal}</span>;
    }
  };

  const renderTable = (data: any) => {
    if (typeof data !== "object" || data === null || Array.isArray(data)) {
      return (
        <div style={{ background: "var(--panel-inset)", padding: "1rem", borderRadius: "var(--radius-control)" }}>
          {renderValue(data)}
        </div>
      );
    }

    let displayData = { ...data };

    return (
      <div style={{ overflowX: "auto", background: "var(--panel-inset)", borderRadius: "var(--radius-control)", border: "1px solid var(--border-soft)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(0,0,0,0.2)" }}>
              {Object.keys(displayData).map(key => (
                <th key={key} style={{ padding: "0.8rem", color: "var(--cyan-trace)", textTransform: "uppercase", fontSize: "0.85rem", borderBottom: "1px solid var(--border-soft)", borderRight: "1px solid var(--border-soft)" }}>
                  {key.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {Object.values(displayData).map((val, idx) => (
                <td key={idx} style={{ padding: "0.8rem", color: "var(--text-primary)", fontSize: "0.9rem", borderRight: "1px solid var(--border-soft)", verticalAlign: "top" }}>
                  {renderValue(val)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="intel-panel" style={{ padding: "1rem", color: "var(--foreground)", height: "100%", overflowY: "auto" }}>
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Suite de Inteligencia y Vigilancia (15 Módulos)</span>
          <h1>OSINT & THREAT ANALYTICS</h1>
        </div>
      </div>

      <div style={{ marginBottom: "0.5rem", marginTop: "1rem" }}><strong style={{ color: "var(--text-secondary)" }}>INTELIGENCIA LOCAL (CHILE) & CLIMA</strong></div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: "0.5rem", marginBottom: "1rem" }}>
        <button 
          onClick={() => handleTabChange("ppu")}
          style={{ padding: "0.6rem", background: activeTab === "ppu" ? "var(--panel-raised)" : "transparent", color: activeTab === "ppu" ? "var(--cyan-trace)" : "var(--text-secondary)", border: `1px solid ${activeTab === "ppu" ? "var(--cyan-trace)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "ppu" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Car size={16} /> PPU
        </button>
        <button 
          onClick={() => handleTabChange("rut")}
          style={{ padding: "0.6rem", background: activeTab === "rut" ? "var(--panel-raised)" : "transparent", color: activeTab === "rut" ? "var(--cyan-trace)" : "var(--text-secondary)", border: `1px solid ${activeTab === "rut" ? "var(--cyan-trace)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "rut" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <User size={16} /> RUT
        </button>
        <button 
          onClick={() => handleTabChange("geoclima")}
          style={{ padding: "0.6rem", background: activeTab === "geoclima" ? "var(--panel-raised)" : "transparent", color: activeTab === "geoclima" ? "var(--cyan-trace)" : "var(--text-secondary)", border: `1px solid ${activeTab === "geoclima" ? "var(--cyan-trace)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "geoclima" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <MapPin size={16} /> Geografía y Clima
        </button>
      </div>

      <div style={{ marginBottom: "0.5rem" }}><strong style={{ color: "var(--text-secondary)" }}>INTELIGENCIA DE RED, AMENAZAS & AMBIENTE DIGITAL (12 MÓDULOS)</strong></div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <button 
          onClick={() => handleTabChange("breach")}
          style={{ padding: "0.6rem", background: activeTab === "breach" ? "var(--panel-raised)" : "transparent", color: activeTab === "breach" ? "#dc322f" : "var(--text-secondary)", border: `1px solid ${activeTab === "breach" ? "#dc322f" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "breach" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <KeyRound size={16} /> Fugas de Datos
        </button>
        <button 
          onClick={() => handleTabChange("threat")}
          style={{ padding: "0.6rem", background: activeTab === "threat" ? "var(--panel-raised)" : "transparent", color: activeTab === "threat" ? "#cb4b16" : "var(--text-secondary)", border: `1px solid ${activeTab === "threat" ? "#cb4b16" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "threat" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <ShieldAlert size={16} /> Reputación IP
        </button>
        <button 
          onClick={() => handleTabChange("shodan")}
          style={{ padding: "0.6rem", background: activeTab === "shodan" ? "var(--panel-raised)" : "transparent", color: activeTab === "shodan" ? "#b58900" : "var(--text-secondary)", border: `1px solid ${activeTab === "shodan" ? "#b58900" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "shodan" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Server size={16} /> Infraestructura
        </button>
        <button 
          onClick={() => handleTabChange("whois")}
          style={{ padding: "0.6rem", background: activeTab === "whois" ? "var(--panel-raised)" : "transparent", color: activeTab === "whois" ? "#6c71c4" : "var(--text-secondary)", border: `1px solid ${activeTab === "whois" ? "#6c71c4" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "whois" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <FileText size={16} /> Registro WHOIS
        </button>

        <button 
          onClick={() => handleTabChange("ip")}
          style={{ padding: "0.6rem", background: activeTab === "ip" ? "var(--panel-raised)" : "transparent", color: activeTab === "ip" ? "var(--mint-live)" : "var(--text-secondary)", border: `1px solid ${activeTab === "ip" ? "var(--mint-live)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "ip" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <MapPin size={16} /> IP Geo
        </button>
        <button 
          onClick={() => handleTabChange("dns")}
          style={{ padding: "0.6rem", background: activeTab === "dns" ? "var(--panel-raised)" : "transparent", color: activeTab === "dns" ? "var(--mint-live)" : "var(--text-secondary)", border: `1px solid ${activeTab === "dns" ? "var(--mint-live)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "dns" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Globe size={16} /> DNS
        </button>
        <button 
          onClick={() => handleTabChange("web")}
          style={{ padding: "0.6rem", background: activeTab === "web" ? "var(--panel-raised)" : "transparent", color: activeTab === "web" ? "var(--amber-warn)" : "var(--text-secondary)", border: `1px solid ${activeTab === "web" ? "var(--amber-warn)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "web" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Globe size={16} /> Analizador Web
        </button>
        <button 
          onClick={() => handleTabChange("ports")}
          style={{ padding: "0.6rem", background: activeTab === "ports" ? "var(--panel-raised)" : "transparent", color: activeTab === "ports" ? "var(--red-alert)" : "var(--text-secondary)", border: `1px solid ${activeTab === "ports" ? "var(--red-alert)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "ports" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Globe size={16} /> Puertos
        </button>
        <button 
          onClick={() => handleTabChange("subdomains")}
          style={{ padding: "0.6rem", background: activeTab === "subdomains" ? "var(--panel-raised)" : "transparent", color: activeTab === "subdomains" ? "#b58900" : "var(--text-secondary)", border: `1px solid ${activeTab === "subdomains" ? "#b58900" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "subdomains" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Globe size={16} /> Subdominios
        </button>
        <button 
          onClick={() => handleTabChange("email")}
          style={{ padding: "0.6rem", background: activeTab === "email" ? "var(--panel-raised)" : "transparent", color: activeTab === "email" ? "#268bd2" : "var(--text-secondary)", border: `1px solid ${activeTab === "email" ? "#268bd2" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "email" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <User size={16} /> Email
        </button>
        <button 
          onClick={() => handleTabChange("ping")}
          style={{ padding: "0.6rem", background: activeTab === "ping" ? "var(--panel-raised)" : "transparent", color: activeTab === "ping" ? "var(--mint-live)" : "var(--text-secondary)", border: `1px solid ${activeTab === "ping" ? "var(--mint-live)" : "var(--border-soft)"}`, borderRadius: "var(--radius-control)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", fontWeight: activeTab === "ping" ? "bold" : "normal", transition: "all 0.2s" }}
        >
          <Globe size={16} /> Traceroute
        </button>
      </div>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
        <input 
          type="text" 
          placeholder={
            activeTab === "ppu" ? "Ej: AB1234 o ABCD12" : 
            activeTab === "rut" ? "Ej: 12345678-9" : 
            activeTab === "geoclima" ? "Ej: Santiago, Providencia, etc" :
            activeTab === "breach" ? "Ej: usuario@empresa.cl o dominio.com" :
            activeTab === "threat" || activeTab === "shodan" || activeTab === "ip" ? "Ej: 8.8.8.8 o google.com" : 
            "Ej: google.com"
          }
          value={currentQuery}
          onChange={(e) => setTabQuery(e.target.value)}
          style={{ flex: 1, padding: "0.8rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)", outline: "none", fontSize: "1rem", fontFamily: "monospace", letterSpacing: "1px" }}
        />
        <button type="submit" disabled={isCurrentLoading} style={{ padding: "0.8rem 1.5rem", background: "var(--mint-live)", border: "none", color: "var(--void)", borderRadius: "var(--radius-control)", cursor: isCurrentLoading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: "bold", fontSize: "1rem", opacity: isCurrentLoading ? 0.7 : 1 }}>
          <Search size={18} /> {isCurrentLoading ? "EJECUTANDO..." : "BUSCAR"}
        </button>

      </form>

      {currentError && (
        <div style={{ padding: "1rem", background: "rgba(220, 50, 47, 0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", marginBottom: "1rem", borderRadius: "var(--radius-control)", display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: "bold" }}>
          <span>⚠️ {currentError}</span>
        </div>
      )}

      {currentResult && currentResult.status === "error" && !currentError && (
        <div style={{ padding: "1rem", background: "rgba(220, 50, 47, 0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", marginBottom: "1rem", borderRadius: "var(--radius-control)", display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: "bold" }}>
          <span>❌ {currentResult.message}</span>
        </div>
      )}

      {currentResult && currentResult.status === "success" && currentResult.data && (() => {
        const riskMeta = getRiskColorAndLabel(currentResult);
        return (
          <div style={{ background: "var(--panel)", padding: "1.5rem", border: `1px solid ${riskMeta.border}`, borderRadius: "var(--radius-panel)", boxShadow: `0 0 20px ${riskMeta.bg}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", borderBottom: "1px solid var(--border-soft)", paddingBottom: "0.8rem" }}>
              <h3 style={{ color: "var(--cyan-trace)", display: "flex", alignItems: "center", gap: "0.6rem", margin: 0 }}>
                {/* CIRCULAR LED TACTICAL INDICATOR (SEMÁFORO) */}
                <span style={{ display: "inline-block", width: "12px", height: "12px", background: riskMeta.color, borderRadius: "50%", boxShadow: riskMeta.glow }}></span>
                DATOS DE INTELIGENCIA OBTENIDOS
              </h3>

              <div style={{ background: riskMeta.bg, border: `1px solid ${riskMeta.border}`, color: riskMeta.color, padding: "0.3rem 0.8rem", borderRadius: "var(--radius-control)", fontSize: "0.85rem", fontWeight: "bold", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span>NIVEL DE CRITICIDAD: {riskMeta.label}</span>
              </div>
            </div>
            
            {renderTable(currentResult.data)}
          </div>
        );
      })()}
    </div>
  );
}
