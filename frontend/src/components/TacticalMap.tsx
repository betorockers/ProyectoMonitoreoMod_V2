"use client";
import dynamic from "next/dynamic";

const TacticalMapInner = dynamic(() => import("./TacticalMapInner"), { 
  ssr: false, 
  loading: () => (
    <div style={{
      height: "100%", width: "100%", display: "flex", alignItems: "center", 
      justifyContent: "center", background: "var(--panel-inset)", 
      color: "var(--cyan-trace)", border: "1px solid var(--border-soft)",
      borderRadius: "var(--radius-panel)"
    }}>
      Inicializando Sistema Geospacial...
    </div>
  ) 
});

export function TacticalMap({ targets, results }: { targets: any[], results: any }) {
  return <TacticalMapInner targets={targets} results={results} />;
}
