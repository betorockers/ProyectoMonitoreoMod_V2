"use client";

import { useEffect, useState } from "react";
import { apiBaseUrl } from "@/lib/telemetry";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const COLORS = ['var(--mint-live)', 'var(--amber-warn)', 'var(--cyan-trace)', '#a29bfe', '#fd79a8'];

export function EventHistory({ targets = [] }: { targets?: any[] }) {
  const [events, setEvents] = useState<any[]>([]);

  const getLabel = (id: string) => {
    const t = targets.find(t => t.id === id);
    return t ? t.label : id;
  };

  useEffect(() => {
    async function fetchEvents() {
      try {
        const token = sessionStorage.getItem("argos_token") || "";

        // Fetch enough events to cover the whole session/day (backend defaults to 100 if not specified, let's ask for 2000)
        const res = await fetch(`${apiBaseUrl}/api/v1/events?limit=2000`, {
          headers: { "X-Argos-Token": token }
        });
        if (res.ok) {
          const data = await res.json();
          // Filter to strictly show events from the current day (Jornada)
          const today = new Date().toDateString();
          const todayEvents = data.filter((e: any) => new Date(e.timestamp).toDateString() === today);
          setEvents(todayEvents.reverse()); // chronological order for charts
        }
      } catch (err) {
        console.error("Failed to fetch events", err);
      }
    }
    
    fetchEvents();
    const interval = setInterval(fetchEvents, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  // Process data for Line Chart (Latency over time)
  const latencyData = events.map(ev => ({
    time: new Date(ev.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
    [getLabel(ev.target_id)]: ev.latency_ms > 0 ? ev.latency_ms : null
  }));

  const uniqueTargets = Array.from(new Set(events.map(ev => ev.target_id)));

  return (
    <div style={{ padding: "1rem", color: "var(--text-primary)", height: "100%", overflowY: "auto" }}>
      <h2 style={{ color: "var(--mint-live)", marginBottom: "1rem" }}>Análisis y Eventos</h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "2rem", marginBottom: "2rem" }}>
        
        {/* Latency Line Chart */}
        <div style={{ background: "var(--panel-inset)", padding: "1rem", borderRadius: "var(--radius-panel)", border: "1px solid var(--border-soft)" }}>
          <h3 style={{ color: "var(--cyan-trace)", marginBottom: "1rem" }}>Latencia Global (Jornada)</h3>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-soft)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" />
                <YAxis stroke="var(--text-muted)" />
                <RechartsTooltip contentStyle={{ backgroundColor: "var(--panel)", border: "1px solid var(--border-soft)" }} />
                {uniqueTargets.map((target, idx) => (
                  <Line key={target} type="monotone" dataKey={getLabel(target as string)} stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Uptime Donut Charts */}
        <div style={{ background: "var(--panel-inset)", padding: "1rem", borderRadius: "var(--radius-panel)", border: "1px solid var(--border-soft)" }}>
          <h3 style={{ color: "var(--cyan-trace)", marginBottom: "1rem" }}>Disponibilidad por Equipo</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem", justifyContent: "center" }}>
            {uniqueTargets.map((target, idx) => {
              const targetEvents = events.filter(e => e.target_id === target);
              const onlineCount = targetEvents.filter(e => e.status === "online").length;
              const offlineCount = targetEvents.length - onlineCount;
              const data = [
                { name: "Online", value: onlineCount || 1 },
                { name: "Offline", value: offlineCount }
              ];
              
              return (
                <div key={target} style={{ textAlign: "center" }}>
                  <h4 style={{ color: "var(--text-secondary)", marginBottom: "-20px" }}>{getLabel(target as string)}</h4>
                  <PieChart width={200} height={120}>
                    <Pie
                      data={data}
                      cx={100}
                      cy={100}
                      startAngle={180}
                      endAngle={0}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell fill="var(--mint-live)" />
                      <Cell fill="var(--red-alert)" />
                    </Pie>
                    <RechartsTooltip contentStyle={{ backgroundColor: "var(--panel)", border: "none" }} />
                  </PieChart>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Heatmap de Continuidad */}
        <div style={{ background: "var(--panel-inset)", padding: "1rem", borderRadius: "var(--radius-panel)", border: "1px solid var(--border-soft)" }}>
          <h3 style={{ color: "var(--cyan-trace)", marginBottom: "1rem" }}>Continuidad (Últimos Eventos)</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {uniqueTargets.map(target => {
              const targetEvents = events.filter(e => e.target_id === target).slice(-40);
              const blocks = Array.from({ length: 40 }).map((_, i) => targetEvents[i]);
              
              return (
                <div key={target} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <span style={{ width: "120px", color: "var(--text-secondary)", fontSize: "0.9rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={getLabel(target as string)}>{getLabel(target as string)}</span>
                  <div style={{ display: "flex", gap: "4px", flex: 1 }}>
                    {blocks.map((ev, i) => {
                      let color = "var(--border-soft)"; 
                      if (ev) {
                        if (ev.status === "online") color = "var(--mint-live)";
                        else if (ev.status === "degraded") color = "var(--amber-warn)";
                        else color = "var(--red-alert)";
                      }
                      return (
                        <div key={i} title={ev ? `${new Date(ev.timestamp).toLocaleTimeString()} - ${ev.status}` : "Sin datos"} style={{ 
                          height: "24px", 
                          flex: 1, 
                          background: color, 
                          borderRadius: "2px",
                          opacity: ev ? 1 : 0.3
                        }} />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      <h3 style={{ color: "var(--mint-live)", marginBottom: "1rem" }}>Registro de Sucesos</h3>
      <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border-soft)", color: "var(--text-muted)" }}>
            <th style={{ padding: "0.5rem" }}>Timestamp</th>
            <th style={{ padding: "0.5rem" }}>Equipo</th>
            <th style={{ padding: "0.5rem" }}>Estado</th>
            <th style={{ padding: "0.5rem" }}>Latencia (ms)</th>
            <th style={{ padding: "0.5rem" }}>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {[...events].reverse().map((ev, i) => {
            const lat = ev.latency_ms;
            let latColor = "var(--text-muted)";
            if (lat !== null && lat !== undefined) {
              if (lat <= 100) latColor = "var(--mint-live)";
              else if (lat <= 300) latColor = "var(--amber-warn)";
              else latColor = "var(--red-alert)";
            }
            return (
              <tr key={i} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                <td style={{ padding: "0.5rem", fontSize: "0.85rem" }}>{new Date(ev.timestamp.replace(' ', 'T') + 'Z').toLocaleString('es-CL')}</td>
                <td style={{ padding: "0.5rem" }} title={ev.target_id}>{getLabel(ev.target_id)}</td>
                <td style={{ padding: "0.5rem", color: ev.status === 'online' ? 'var(--mint-live)' : ev.status === 'degraded' ? 'var(--amber-warn)' : 'var(--red-alert)', fontWeight: 'bold' }}>{ev.status.toUpperCase()}</td>
                <td style={{ padding: "0.5rem", fontFamily: "monospace", color: latColor }}>
                  {lat !== null && lat !== undefined ? `${lat} ms` : "—"}
                </td>
                <td style={{ padding: "0.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>{ev.detail}</td>
              </tr>
            );
          })}
          {events.length === 0 && (
            <tr><td colSpan={5} style={{ padding: "1rem", textAlign: "center", color: "var(--text-muted)" }}>No hay eventos registrados.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
