import { useState } from "react";
import { MapContainer, TileLayer, Popup, CircleMarker, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { apiBaseUrl } from "@/lib/telemetry";

import L from "leaflet";
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png"
});

export default function TacticalMapInner({ targets, results }: { targets: any[], results: any }) {
  const center = [-33.4489, -70.6693] as [number, number]; // Santiago default center
  
  const [tracingId, setTracingId] = useState<string | null>(null);
  const [traceData, setTraceData] = useState<any | null>(null);

  const runTraceroute = async (t: any) => {
    setTracingId(t.id);
    setTraceData(null);
    try {
      const token = sessionStorage.getItem("argos_token") || "";
      const res = await fetch(`${apiBaseUrl}/api/v1/osint/traceroute`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Argos-Token": token },
        body: JSON.stringify({ query: t.host })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          setTraceData(data.data);
        }
      }
    } catch (e) {
      console.error("Traceroute error", e);
    }
    setTracingId(null);
  };

  const getPolylinePositions = () => {
    if (!traceData || !traceData.Hops) return [];
    const positions: [number, number][] = [];
    positions.push(center); // start at center
    
    traceData.Hops.forEach((h: any) => {
      if (h.Latitud && h.Longitud) {
        positions.push([parseFloat(h.Latitud), parseFloat(h.Longitud)]);
      }
    });
    return positions;
  };

  const polylinePositions = getPolylinePositions();

  return (
    <div style={{ height: "100%", width: "100%", borderRadius: "var(--radius-panel)", overflow: "hidden", border: "1px solid var(--border-soft)", position: "relative" }}>
      <MapContainer center={center} zoom={5} style={{ height: "100%", width: "100%", background: "#0a192f" }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />
        
        {polylinePositions.length > 1 && (
          <Polyline positions={polylinePositions} pathOptions={{ color: "var(--cyan-trace)", weight: 3, dashArray: "5, 10" }} />
        )}
        
        {traceData?.Hops?.map((h: any, idx: number) => {
          if (!h.Latitud || !h.Longitud) return null;
          return (
            <CircleMarker key={`hop-${idx}`} center={[parseFloat(h.Latitud), parseFloat(h.Longitud)]} radius={5} pathOptions={{ color: "var(--amber-warn)", fillColor: "var(--amber-warn)", fillOpacity: 1 }}>
              <Popup>
                <div style={{color: "#000"}}>
                  <strong>Salto {h.Salto}</strong><br/>
                  IP: {h["Host / IP"]}<br/>
                  Ubicación: {h["Ubicación"] || "Desconocida"}<br/>
                  RTT: {h["RTT Promedio (ms)"]} ms
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {targets.map((t: any) => {
          if (!t.latitude || !t.longitude) return null;
          const res = Array.isArray(results) ? results.find((r: any) => r.target_id === t.id) : (results ? results[t.id] : null);
          const isOnline = res?.status === "online" || res?.status === "ONLINE";
          const color = isOnline ? "#2aa198" : "#dc322f";

          return (
            <CircleMarker 
              key={t.id} 
              center={[t.latitude, t.longitude]} 
              radius={8} 
              pathOptions={{ color: color, fillColor: color, fillOpacity: 0.7 }}
            >
              <Popup>
                <div style={{color: "#000"}}>
                  <strong>{t.label}</strong><br/>
                  Host: {t.host}:{t.port}<br/>
                  Estado: {isOnline ? "EN LÍNEA" : "CAÍDO"}<br/>
                  Latencia: {res?.latency_ms ?? "-"} ms<br/>
                  <div style={{ marginTop: "10px" }}>
                    <button 
                      onClick={() => runTraceroute(t)}
                      disabled={tracingId === t.id}
                      style={{ padding: "5px 10px", background: "var(--cyan-trace)", color: "#fff", border: "none", borderRadius: "3px", cursor: "pointer", width: "100%" }}
                    >
                      {tracingId === t.id ? "Trazando..." : "Traceroute Map"}
                    </button>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
