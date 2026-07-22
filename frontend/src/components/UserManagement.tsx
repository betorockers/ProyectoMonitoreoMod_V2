"use client";

import { useState, useEffect } from "react";
import { apiBaseUrl } from "@/lib/telemetry";
import { AlertCircle } from "lucide-react";

export function UserManagement() {
  const [users, setUsers] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUsers() {
      try {
        const token = sessionStorage.getItem("argos_token") || "";
        const userToken = sessionStorage.getItem("argos_user_token") || "";
        const headers: any = {
          "X-Argos-Token": token,
        };
        if (userToken) headers["X-User-Token"] = userToken;
        
        const res = await fetch(`${apiBaseUrl}/api/v1/users`, { headers });
        if (!res.ok) throw new Error("No se pudo cargar los usuarios");
        const data = await res.json();
        setUsers(data);
      } catch (err: any) {
        setError(err.message);
      }
    }
    fetchUsers();
  }, []);

  return (
    <div style={{ padding: "1rem", color: "#fff", height: "100%", overflowY: "auto" }}>
      <h2 style={{ color: "var(--accent-mint)", marginBottom: "1rem" }}>Gestión de Usuarios</h2>
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "1rem" }}>
        <p>Listado de operadores y administradores del sistema.</p>
        
        {error && (
          <div style={{ padding: "0.8rem", background: "rgba(220, 50, 47, 0.1)", border: "1px solid var(--red-alert)", color: "var(--red-alert)", margin: "1rem 0", borderRadius: "4px", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <AlertCircle size={16} /> <span>{error}</span>
          </div>
        )}
        
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--muted)", textAlign: "left" }}>
              <th style={{ padding: "0.5rem" }}>Nombre Real</th>
              <th style={{ padding: "0.5rem" }}>Usuario</th>
              <th style={{ padding: "0.5rem" }}>Rol</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.username} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                <td style={{ padding: "0.5rem" }}>{u.full_name}</td>
                <td style={{ padding: "0.5rem", color: "var(--cyan-trace)" }}>{u.username}</td>
                <td style={{ padding: "0.5rem" }}>{u.role}</td>
              </tr>
            ))}
            {users.length === 0 && !error && (
              <tr>
                <td colSpan={3} style={{ padding: "1rem", textAlign: "center", color: "var(--text-secondary)" }}>
                  Cargando usuarios...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
