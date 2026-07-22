import { useState } from "react";
import { Camera, Trash2, X } from "lucide-react";
import { apiBaseUrl, CameraStream } from "@/lib/telemetry";

export function CameraViewer({ streams, onReload }: { streams: CameraStream[], onReload: () => void }) {
  const [zoomedStream, setZoomedStream] = useState<CameraStream | null>(null);

  const handleDelete = async (id: string) => {
    if (confirm("¿Estás seguro de eliminar esta cámara?")) {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/streams/${id}`, { method: 'DELETE' });
        if (response.ok) {
          onReload();
        }
      } catch (e) {
        console.error("Error deleting stream:", e);
      }
    }
  };

  return (
    <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column", gap: "1rem", overflow: "hidden" }}>
      
      {/* GRILLA DE CÁMARAS RESPONSIVA */}
      <div style={{ 
        flex: 1, 
        display: "grid", 
        gridTemplateColumns: streams.length <= 4 ? "1fr 1fr" : "repeat(auto-fill, minmax(320px, 1fr))", 
        gridAutoRows: streams.length <= 4 ? "calc(50% - 0.5rem)" : "220px", 
        gap: "1rem", 
        overflowY: "auto",
        minHeight: 0 
      }}>
        {streams.length === 0 ? (
          <div style={{ color: "var(--text-muted)", gridColumn: "1 / -1", textAlign: "center", padding: "2rem" }}>
            No hay streams de videovigilancia configurados o la API está desconectada.
          </div>
        ) : (
          streams.map((stream) => (
            <div 
              key={stream.id} 
              onClick={() => setZoomedStream(stream)}
              style={{ 
                position: "relative", 
                borderRadius: "var(--radius-panel)", 
                overflow: "hidden", 
                border: "1px solid var(--border-soft)", 
                background: "#000", 
                height: "100%",
                cursor: "pointer",
                transition: "transform 0.2s, box-shadow 0.2s"
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.01)";
                e.currentTarget.style.boxShadow = "0 0 15px rgba(0, 255, 255, 0.1)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <img 
                src={`${apiBaseUrl}/api/v1/osint/streams/${stream.id}`} 
                style={{ width: "100%", height: "100%", objectFit: "cover", opacity: stream.status.toLowerCase() === 'active' ? 1 : 0.4 }}
                alt={`Live Stream ${stream.label}`}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=800&q=80";
                }}
              />
              
              <div style={{ position: "absolute", top: "10px", left: "10px", background: "rgba(0,0,0,0.7)", color: stream.status.toLowerCase() === 'active' ? "var(--red-alert)" : "var(--amber-warn)", padding: "4px 8px", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "bold", display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ display: "inline-block", width: "8px", height: "8px", background: stream.status.toLowerCase() === 'active' ? "var(--red-alert)" : "var(--amber-warn)", borderRadius: "50%" }}></span> 
                {stream.status.toUpperCase()}
              </div>

              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(stream.id);
                }} 
                style={{ position: "absolute", top: "10px", right: "10px", background: "rgba(255,0,0,0.7)", color: "white", border: "none", padding: "4px", borderRadius: "4px", cursor: "pointer", zIndex: 10 }}
              >
                <Trash2 size={16} />
              </button>
              
              {stream.status.toLowerCase() !== 'active' && (
                <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", color: "var(--text-secondary)", fontFamily: "monospace", background: "rgba(0,0,0,0.7)", padding: "10px", borderRadius: "4px" }}>
                  [ CONEXIÓN DEGRADADA / STANDBY ]
                </div>
              )}

              <div style={{ position: "absolute", bottom: "10px", left: "10px", color: "var(--text-primary)", textShadow: "1px 1px 2px #000", fontFamily: "monospace", display: "flex", flexDirection: "column" }}>
                <span>{stream.id.toUpperCase()} / {stream.label}</span>
                <span style={{ fontSize: "0.8em", color: "var(--cyan-trace)" }}>{stream.protocol} | {stream.endpoint}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* ZOOM MODAL DE LA CÁMARA */}
      {zoomedStream && (
        <div 
          onClick={() => setZoomedStream(null)}
          style={{ 
            position: "fixed", 
            top: 0, 
            left: 0, 
            width: "100vw", 
            height: "100vh", 
            background: "rgba(0,0,0,0.9)", 
            zIndex: 99999, 
            display: "flex", 
            justifyContent: "center", 
            alignItems: "center",
            padding: "2rem"
          }}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            style={{ 
              position: "relative", 
              width: "90%", 
              maxWidth: "1000px", 
              background: "#000", 
              borderRadius: "var(--radius-panel)", 
              border: "1px solid var(--cyan-trace)", 
              overflow: "hidden",
              boxShadow: "0 0 30px rgba(0,255,255,0.2)"
            }}
          >
            <div style={{ padding: "1rem", borderBottom: "1px solid var(--border-soft)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--panel)" }}>
              <h3 style={{ margin: 0, color: "var(--cyan-trace)" }}>{zoomedStream.label} / En Vivo</h3>
              <button 
                onClick={() => setZoomedStream(null)} 
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex", alignItems: "center" }}
              >
                <X size={24} />
              </button>
            </div>
            
            <div style={{ position: "relative", width: "100%", paddingBottom: "56.25%", background: "#000" }}>
              <img 
                src={`${apiBaseUrl}/api/v1/osint/streams/${zoomedStream.id}`} 
                style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", objectFit: "contain" }}
                alt={`Zoom Stream ${zoomedStream.label}`}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=800&q=80";
                }}
              />
            </div>
            
            <div style={{ padding: "1rem", background: "var(--panel)", color: "var(--text-secondary)", fontFamily: "monospace", fontSize: "0.9rem" }}>
              <div>ID: {zoomedStream.id.toUpperCase()}</div>
              <div>Protocolo: {zoomedStream.protocol}</div>
              <div>URL: {zoomedStream.endpoint}</div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
