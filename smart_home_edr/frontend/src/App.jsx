import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, Activity, Lightbulb, ToggleLeft, Cpu,
  RefreshCcw, ShieldOff, Wifi, WifiOff, Wind, Droplets
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';

const API_URL = "http://localhost:8002";
const WS_URL  = "ws://localhost:8002/ws/soc_feed";

// ── Helpers ──────────────────────────────────────────────
const STATUS_STYLES = {
  ON:          "text-green-400 border-green-600 bg-green-900/20",
  OFF:         "text-slate-500 border-slate-700 bg-slate-900/40",
  ONLINE:      "text-green-400 border-green-600 bg-green-900/20",
  CHARGING:    "text-sky-400 border-sky-600 bg-sky-900/20",
  CLEANING:    "text-blue-400 border-blue-600 bg-blue-900/30 animate-pulse",
  WATERING:    "text-teal-400 border-teal-600 bg-teal-900/30 animate-pulse",
  IDLE:        "text-slate-400 border-slate-600 bg-slate-900/30",
  UPDATING:    "text-blue-400 border-blue-500 bg-blue-900/40 animate-pulse",
  ATTACKING:   "text-orange-400 border-orange-500 bg-orange-900/40",
  QUARANTINED: "text-red-500 border-red-500 bg-red-900/40 outline outline-2 outline-red-500",
};

function getStatusStyle(status) {
  return STATUS_STYLES[status] ?? "text-slate-400 border-slate-600 bg-slate-800";
}

function DeviceIcon({ type, status }) {
  const cls = `w-7 h-7 ${status === 'QUARANTINED' ? 'text-red-500' : status === 'ATTACKING' ? 'text-orange-400' : 'text-cyan-400'}`;
  if (type === 'bulb')     return <Lightbulb className={cls} />;
  if (type === 'switch')   return <ToggleLeft className={cls} />;
  if (type === 'roomba')   return <Wind className={cls} />;
  if (type === 'sprinkler')return <Droplets className={cls} />;
  return <Cpu className={cls} />;
}

function ThreatBar({ score }) {
  const pct = Math.min(Math.max(score * 100, 0), 100);
  const color = pct > 60 ? '#ef4444' : pct > 30 ? '#f97316' : '#22c55e';
  return (
    <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1">
      <div className="h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────
export default function App() {
  const [data, setData]       = useState({ inventory: {}, logs: [] });
  const [chartData, setChart] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws;
    function connect() {
      ws = new WebSocket(WS_URL);
      ws.onopen  = () => setConnected(true);
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000); };
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setData(payload);
          const devs = Object.values(payload.inventory || {});
          if (devs.length > 0) {
            const avg = devs.reduce((a, d) => a + (d.anomaly_score || 0), 0) / devs.length;
            setChart(prev => [...prev, {
              t: new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
              v: +(avg * 100).toFixed(2)
            }].slice(-40));
          }
        } catch (e) { console.error("WS parse error", e); }
      };
    }
    connect();
    return () => ws?.close();
  }, []);

  const sendAction = async (device_id, action) => {
    await fetch(`${API_URL}/api/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id, action }),
    });
  };

  const devices = Object.values(data.inventory);
  const quarantined = devices.filter(d => d.status === 'QUARANTINED').length;
  const attacking   = devices.filter(d => d.status === 'ATTACKING').length;

  return (
    <div className="min-h-screen bg-[#060b14] text-slate-200 font-mono select-none p-4">
      {/* ── Header ── */}
      <header className="flex flex-col sm:flex-row justify-between items-center mb-6 border-b border-slate-800 pb-4 gap-4">
        <div className="flex items-center gap-4">
          <ShieldAlert className="text-cyan-500 w-12 h-12 flex-shrink-0" />
          <div>
            <h1 className="text-2xl font-bold tracking-widest text-slate-100">
              SMART HOME <span className="text-cyan-500">EDR</span>
            </h1>
            <p className="text-[10px] text-slate-500 tracking-widest">
              CONTEXT-AWARE · AUTONOMOUS ISOLATION · ZERO-TRUST
            </p>
          </div>
        </div>
        <div className="flex gap-6 text-xs">
          <div className={`flex items-center gap-2 ${connected ? 'text-green-400' : 'text-red-400'}`}>
            {connected ? <Wifi className="w-4 h-4"/> : <WifiOff className="w-4 h-4"/>}
            {connected ? 'SOC FEED LIVE' : 'RECONNECTING...'}
          </div>
          <div className="text-orange-400 flex items-center gap-1">
            <ShieldOff className="w-4 h-4"/>{attacking} ATTACKING
          </div>
          <div className="text-red-500 flex items-center gap-1">
            <ShieldAlert className="w-4 h-4"/>{quarantined} ISOLATED
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ── Device Grid ── */}
        <div className="xl:col-span-2 space-y-4">
          <h2 className="text-xs font-bold tracking-widest text-slate-400 border-b border-slate-800 pb-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500"/> IoT MESH INVENTORY ({devices.length} NODES)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices.map(device => {
              const id         = device.metrics?.device_id;
              const isIso      = device.status === 'QUARANTINED';
              const isAttacking= device.status === 'ATTACKING';
              const score      = device.anomaly_score || 0;

              return (
                <div
                  key={id}
                  className={`relative bg-slate-900/80 border rounded-lg p-4 shadow-xl flex flex-col gap-3 transition-all duration-300
                    ${isIso ? 'border-red-600/60' : isAttacking ? 'border-orange-500/60' : 'border-slate-700/40'}`}
                >
                  {/* Status badge + icon */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <DeviceIcon type={device.device_type} status={device.status} />
                      <div>
                        <div className="text-sm font-bold text-slate-100 tracking-wide capitalize">
                          {id?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest">
                          {device.device_type}
                        </div>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-bold tracking-widest rounded border ${getStatusStyle(device.status)}`}>
                      {device.status}
                    </span>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] bg-[#0a1020] rounded p-2 border border-slate-800/60">
                    <div>Pkt/s: <span className="text-slate-200 font-bold">{device.metrics?.packet_rate ?? '-'}</span></div>
                    <div>Port: <span className="text-slate-200 font-bold">{device.metrics?.port ?? '-'}</span></div>
                    <div>In: <span className="text-slate-200 font-bold">{device.metrics?.bytes_in ?? '-'} B</span></div>
                    <div>Out: <span className="text-slate-200 font-bold">{device.metrics?.bytes_out ?? '-'} B</span></div>
                  </div>

                  {/* Threat score bar */}
                  <div className="text-[10px] text-slate-500">
                    THREAT SCORE: <span className={`font-bold ${score > 0.5 ? 'text-red-400' : score > 0.25 ? 'text-orange-400' : 'text-green-400'}`}>
                      {(score * 100).toFixed(1)}%
                    </span>
                    <ThreatBar score={score} />
                  </div>

                  {/* EDR Actions — defensive only */}
                  <div className="flex gap-2 mt-1">
                    {!isIso && (
                      <button
                        onClick={() => sendAction(id, 'quarantine')}
                        className="flex-1 text-[10px] tracking-widest py-1.5 rounded flex justify-center items-center gap-1 font-bold
                          bg-red-900/20 border border-red-700 text-red-400 hover:bg-red-600 hover:text-white transition-all"
                      >
                        <ShieldOff className="w-3 h-3"/> ISOLATE
                      </button>
                    )}
                    {isIso && (
                      <button
                        onClick={() => sendAction(id, 'restore')}
                        className="flex-1 text-[10px] tracking-widest py-1.5 rounded flex justify-center items-center gap-1 font-bold
                          bg-green-900/20 border border-green-700 text-green-400 hover:bg-green-600 hover:text-white transition-all"
                      >
                        <RefreshCcw className="w-3 h-3"/> RESTORE
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
            {devices.length === 0 && (
              <p className="text-slate-600 italic text-sm p-4 col-span-2">
                Awaiting nodes to join mesh network...
              </p>
            )}
          </div>

          {/* ── Global Threat Chart ── */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 shadow-xl h-60 mt-4">
            <p className="text-[10px] font-bold tracking-widest text-slate-500 mb-3">
              ECOSYSTEM MEAN THREAT TRAJECTORY
            </p>
            <ResponsiveContainer width="100%" height="85%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="t" stroke="#475569" fontSize={9} tickMargin={6} />
                <YAxis stroke="#475569" fontSize={9} domain={[0, 'auto']} />
                <Tooltip
                  contentStyle={{ background: 'rgba(10,16,32,0.95)', border: '1px solid #334155', borderRadius: 4 }}
                  labelStyle={{ color: '#94a3b8', fontSize: 10 }}
                  itemStyle={{ fontSize: 11 }}
                />
                <ReferenceLine y={30} stroke="#f97316" strokeDasharray="4 4" label={{ value: 'WARN', fill:'#f97316', fontSize:9 }} />
                <ReferenceLine y={60} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'CRIT', fill:'#ef4444', fontSize:9 }} />
                <Line type="stepAfter" dataKey="v" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── SIEM Terminal ── */}
        <div className="bg-[#040810] border border-slate-800 rounded-lg p-4 shadow-2xl flex flex-col h-[calc(100vh-7rem)]">
          <p className="text-[10px] font-bold tracking-widest text-slate-500 mb-3 border-b border-slate-800 pb-3">
            ⬛ SIEM AUDIT TERMINAL
          </p>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 flex flex-col justify-end">
            {data.logs.map(log => (
              <div key={log.id} className="text-[11px] leading-relaxed border-l-2 pl-2 border-slate-800">
                <span className="text-slate-600">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>{' '}
                <span className="text-cyan-700 font-bold">{log.device_id?.toUpperCase()}</span>
                <br />
                <span className={
                  log.level === 'error'   ? 'text-red-400 font-bold'
                  : log.level === 'success' ? 'text-green-400 font-bold'
                  : log.level === 'warning' ? 'text-orange-400'
                  : 'text-slate-300'
                }>
                  » {log.message}
                </span>
              </div>
            ))}
            {data.logs.length === 0 && (
              <span className="text-slate-700 italic text-xs">Listening to event bus...</span>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
