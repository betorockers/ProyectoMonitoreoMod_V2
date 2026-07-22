export type NodeStatus = "online" | "degraded" | "offline" | "unknown";

export type MonitorTarget = {
  id: string;
  label: string;
  host: string;
  port: number;
  protocol: string;
  latitude: number | null;
  longitude: number | null;
  mac_address?: string;
  isp?: string;
  asn?: string;
  threat_intel?: string;
  country?: string;
  instalacion?: string;
};

export type ProbeResult = {
  target_id: string;
  status: NodeStatus;
  latency_ms: number | null;
  checked_at: string;
  detail: string;
  mac_address?: string;
};

export type TelemetrySnapshot = {
  targets: MonitorTarget[];
  results: ProbeResult[];
};

export type CameraStream = {
  id: string;
  label: string;
  protocol: string;
  endpoint: string;
  status: "standby" | "active" | "degraded";
  fps: number;
  latency_ms: number;
};

export const apiBaseUrl =
  typeof window !== "undefined" && window.location.port !== "3000"
    ? window.location.origin
    : (process.env.NEXT_PUBLIC_ARGOS_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000");

export function telemetrySocketUrl() {
  const base = apiBaseUrl.replace(/^http/, "ws");
  return `${base}/api/v1/ws/telemetry`;
}
