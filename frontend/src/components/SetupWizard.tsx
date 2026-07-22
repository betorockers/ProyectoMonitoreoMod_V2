"use client";

import { useState, useMemo } from "react";
import Image from "next/image";
import { apiBaseUrl } from "@/lib/telemetry";
import logoArgosGuard from "@/img/LogoArgosGuard.png";
import { KeyRound, UserPlus, ShieldCheck, CheckCircle2, XCircle, Eye, EyeOff } from "lucide-react";

export function SetupWizard({ onComplete }: { onComplete: () => void }) {
  const [serial, setSerial] = useState("");
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Validaciones de contraseña
  const passLength = password.length >= 8 && password.length <= 12;
  const passUpper = /[A-Z]/.test(password);
  const passLower = /[a-z]/.test(password);
  const passNumber = /[0-9]/.test(password);
  const passSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const passMatch = password !== "" && password === confirmPassword;

  const isPasswordValid = passLength && passUpper && passLower && passNumber && passSpecial && passMatch;

  const handleSetup = async () => {
    if (!isPasswordValid) return;
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/system/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ serial, full_name: fullName, username, password })
      });
      const data = await res.json();
      
      if (data.status === "error") {
        setError(data.message);
      } else {
        onComplete();
      }
    } catch (err) {
      setError("Error de red contactando al validador.");
    } finally {
      setLoading(false);
    }
  };

  const ValidationItem = ({ label, valid }: { label: string, valid: boolean }) => (
    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: valid ? "var(--mint-live)" : "var(--text-secondary)", fontSize: "0.75rem" }}>
      {valid ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
      <span>{label}</span>
    </div>
  );

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, width: "100%", height: "100vh",
      background: "var(--void)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "Inter, sans-serif"
    }}>
      <div style={{
        background: "var(--panel)", border: "1px solid var(--cyan-trace)",
        borderRadius: "var(--radius-panel)", padding: "2rem", width: "100%", maxWidth: "500px",
        boxShadow: "0 0 40px rgba(42, 161, 152, 0.15)"
      }}>
        <div style={{ textAlign: "center", marginBottom: "1rem" }}>
          <Image src={logoArgosGuard} alt="Argos Guard" width={60} height={60} style={{ margin: "0 auto", opacity: 0.9 }} />
          <h2 style={{ color: "var(--text-primary)", marginTop: "0.5rem", fontSize: "1.1rem" }}>Inicialización del Sistema</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>Registro de SuperAdministrador</p>
        </div>

        {error && (
          <div style={{ background: "rgba(220, 50, 47, 0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", padding: "0.5rem", borderRadius: "var(--radius-control)", marginBottom: "1rem", fontSize: "0.85rem", textAlign: "center" }}>
            {error}
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
          
          <div>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--cyan-trace)", fontSize: "0.8rem", marginBottom: "0.4rem", fontWeight: "bold" }}>
              <UserPlus size={16} /> DATOS DEL ADMINISTRADOR
            </label>
            <input 
              type="text" 
              placeholder="Nombre Real del Usuario"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              style={{ width: "100%", padding: "0.8rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)", marginBottom: "0.8rem" }}
            />
            <input 
              type="text" 
              placeholder="Nombre de Usuario (Login)"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: "100%", padding: "0.8rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)", marginBottom: "0.8rem" }}
            />
            <div style={{ position: "relative", marginBottom: "0.8rem" }}>
              <input 
                type={showPassword ? "text" : "password"} 
                placeholder="Contraseña Maestra"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ width: "100%", padding: "0.8rem", paddingRight: "2.5rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)" }}
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            
            <div style={{ position: "relative", marginBottom: "0.5rem" }}>
              <input 
                type={showConfirmPassword ? "text" : "password"} 
                placeholder="Confirmar Contraseña"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={{ width: "100%", padding: "0.8rem", paddingRight: "2.5rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)" }}
              />
              <button 
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "0.8rem", borderRadius: "4px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
              <ValidationItem label="8-12 Caracteres" valid={passLength} />
              <ValidationItem label="1 Mayúscula" valid={passUpper} />
              <ValidationItem label="1 Minúscula" valid={passLower} />
              <ValidationItem label="1 Número" valid={passNumber} />
              <ValidationItem label="1 Símbolo (!@#$%...)" valid={passSpecial} />
              <ValidationItem label="Contraseñas coinciden" valid={passMatch} />
            </div>
          </div>

          <div style={{ height: "1px", background: "var(--border-soft)", margin: "0.2rem 0" }} />

          <div>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--cyan-trace)", fontSize: "0.85rem", marginBottom: "0.5rem", fontWeight: "bold" }}>
              <KeyRound size={16} /> CLAVE DE ACTIVACIÓN
            </label>
            <input 
              type="text" 
              placeholder="ARGOS-XXXX-XXXX-XXXX-XXXX"
              value={serial}
              onChange={(e) => setSerial(e.target.value.toUpperCase())}
              style={{ width: "100%", padding: "0.8rem", background: "var(--panel-inset)", border: "1px solid var(--border-soft)", color: "var(--text-primary)", borderRadius: "var(--radius-control)", fontFamily: "monospace", letterSpacing: "1px" }}
            />
          </div>

          <button 
            onClick={handleSetup}
            disabled={loading || !serial || !username || !fullName || !isPasswordValid}
            style={{ 
              width: "100%", padding: "1rem", background: "var(--mint-live)", color: "var(--void)", 
              border: "none", borderRadius: "var(--radius-control)", fontWeight: "bold", fontSize: "1rem",
              cursor: (loading || !serial || !username || !fullName || !isPasswordValid) ? "not-allowed" : "pointer", opacity: (loading || !serial || !username || !fullName || !isPasswordValid) ? 0.7 : 1,
              display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", marginTop: "0.5rem",
              boxShadow: "0 4px 15px rgba(133, 153, 0, 0.3)"
            }}
          >
            <ShieldCheck size={20} />
            {loading ? "VALIDANDO FIRMA..." : "INICIALIZAR SISTEMA"}
          </button>
        </div>
      </div>
    </div>
  );
}
