"use client";

import { useState } from "react";
import Image from "next/image";
import { Lock, User, AlertCircle, ShieldAlert, Eye, EyeOff } from "lucide-react";
import logoArgosGuard from "@/img/LogoArgosGuard.png";
import { apiBaseUrl } from "@/lib/telemetry";

export function LoginScreen({ onLoginSuccess }: { onLoginSuccess: (token: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (!res.ok || data.status === "error") {
        if (res.status === 429) {
          throw new Error("Demasiados intentos. Intente más tarde.");
        }
        throw new Error(data.message || "Error al autenticar");
      }

      try {
        sessionStorage.setItem("argos_user_token", data.user_token);
      } catch (e) {
        console.warn("sessionStorage no disponible:", e);
      }
      
      onLoginSuccess(data.token);
      
    } catch (err: any) {
      setError(err.message || "Error de conexión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", alignItems: "center", justifyContent: "center", background: "var(--void)", color: "var(--text-primary)", position: "relative", overflow: "hidden" }}>
      {/* Background elements */}
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: "800px", height: "800px", background: "radial-gradient(circle, rgba(42, 161, 152, 0.05) 0%, rgba(0, 0, 0, 0) 70%)", zIndex: 0 }} />
      <div className="scanline" style={{ zIndex: 1 }} />
      
      <div style={{ zIndex: 2, display: "flex", flexDirection: "column", alignItems: "center", width: "100%", maxWidth: "400px", background: "rgba(0, 43, 54, 0.6)", padding: "2.5rem 2rem", borderRadius: "8px", border: "1px solid var(--cyan-trace)", boxShadow: "0 0 30px rgba(42, 161, 152, 0.15), inset 0 0 10px rgba(42, 161, 152, 0.1)", backdropFilter: "blur(10px)" }}>
        
        <Image src={logoArgosGuard} alt="Argos Guard" width={80} height={80} style={{ marginBottom: "1rem" }} />
        
        <h1 style={{ color: "var(--cyan-trace)", fontSize: "1.5rem", marginBottom: "0.2rem", textAlign: "center" }}>Argos Guard Enterprise</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "2rem", textTransform: "uppercase", letterSpacing: "1px" }}>Secure Tactical Terminal</p>



        {error && (
          <div style={{ width: "100%", padding: "0.8rem", background: "rgba(220, 50, 47, 0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", marginBottom: "1.5rem", borderRadius: "4px", display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", fontWeight: "bold" }}>
            <AlertCircle size={16} /> <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} style={{ width: "100%", display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ position: "relative" }}>
            <User size={18} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)" }} />
            <input 
              type="text" 
              placeholder="Identificación de Usuario" 
              value={username}
              onChange={e => setUsername(e.target.value)}
              style={{ width: "100%", padding: "0.8rem 1rem 0.8rem 2.5rem", background: "rgba(0, 0, 0, 0.5)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "4px", outline: "none", fontSize: "0.95rem", transition: "border 0.2s" }}
              onFocus={e => e.target.style.border = "1px solid var(--cyan-trace)"}
              onBlur={e => e.target.style.border = "1px solid var(--border-soft)"}
            />
          </div>

          <div style={{ position: "relative" }}>
            <Lock size={18} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)" }} />
            <input 
              type={showPassword ? "text" : "password"} 
              placeholder="Código de Acceso" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{ width: "100%", padding: "0.8rem 2.5rem", background: "rgba(0, 0, 0, 0.5)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "4px", outline: "none", fontSize: "0.95rem", transition: "border 0.2s" }}
              onFocus={e => e.target.style.border = "1px solid var(--cyan-trace)"}
              onBlur={e => e.target.style.border = "1px solid var(--border-soft)"}
            />
            <button 
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            style={{ width: "100%", padding: "0.8rem", background: "var(--mint-live)", color: "var(--void)", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer", fontSize: "0.95rem", fontWeight: "bold", textTransform: "uppercase", letterSpacing: "1px", marginTop: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", transition: "opacity 0.2s", opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "Verificando..." : <><ShieldAlert size={16} /> Inicializar Enlace</>}
          </button>
        </form>
        
        <div style={{ marginTop: "1.5rem", padding: "0.8rem", width: "100%", border: "1px dashed rgba(42, 161, 152, 0.3)", borderRadius: "4px", display: "flex", justifyContent: "center", background: "rgba(0, 0, 0, 0.3)" }}>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>Para salir del modo Kiosko presione</span> 
            <kbd style={{ color: "var(--cyan-trace)", fontWeight: "bold", padding: "2px 6px", border: "1px solid var(--cyan-trace)", borderRadius: "4px", background: "rgba(42, 161, 152, 0.1)", fontFamily: "monospace", letterSpacing: "1px" }}>ALT + F4</kbd>
          </p>
        </div>
        
        <p style={{ marginTop: "1.5rem", fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
          <Lock size={10} /> ACCESO RESTRINGIDO - NIVEL TÁCTICO
        </p>
      </div>
    </div>
  );
}
