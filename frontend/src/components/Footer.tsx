"use client";

export function Footer() {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "5px",
        left: "50%",
        transform: "translateX(-50%)",
        fontFamily: "monospace",
        color: "rgba(0, 255, 255, 0.4)", // Cian eléctrico muy sutil
        fontSize: "11px",
        zIndex: 9999,
        pointerEvents: "none",
        textShadow: "0 0 5px rgba(0,255,255,0.1)",
        letterSpacing: "0.5px"
      }}
    >
      Argos Guard Enterprise &copy; Agencia de desarrollo y programacion @BetoGraf_Inc 2026
    </div>
  );
}
