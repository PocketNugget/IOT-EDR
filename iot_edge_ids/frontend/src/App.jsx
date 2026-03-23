import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, ShieldCheck, Zap, Activity } from 'lucide-react';

const API_URL = "http://localhost:8001";
const WS_URL = "ws://localhost:8001/ws/telemetry";

export default function App() {
  const [data, setData] = useState([]);
  const [logs, setLogs] = useState([]);
  const [sensorState, setSensorState] = useState({
    status: 'UNKNOWN',
    score: 0,
    isAnomaly: 0,
    bytesIn: 0,
    bytesOut: 0
  });

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const sensor = payload["sensor_01"];
        
        if (sensor) {
          setSensorState({
            status: sensor.status || 'UNKNOWN',
            score: typeof sensor.anomaly_score === 'number' ? (sensor.anomaly_score * 100).toFixed(2) : '0.00',
            isAnomaly: sensor.is_anomaly || 0,
            bytesIn: sensor.bytes_in || 0,
            bytesOut: sensor.bytes_out || 0
          });

          // Event Engine Logging Logic
          if (sensor.is_anomaly === 1 || sensor.status === 'QUARANTINED') {
            const warningMsg = sensor.status === 'QUARANTINED' 
              ? 'ACTIVE RESPONSE SECURED: Device isolated successfully from network.' 
              : `Zero-Day Threat Signature Evaluated (Score: ${typeof sensor.anomaly_score === 'number' ? sensor.anomaly_score.toFixed(3) : 0})!`;
            
            const logType = sensor.status === 'QUARANTINED' ? 'success' : 'error';
            addLog(`[${new Date().toLocaleTimeString()}] ${warningMsg}`, logType);
          } else if (sensor.status === 'UNDER_ATTACK') {
             addLog(`[${new Date().toLocaleTimeString()}] CRITICAL: Massive Exfiltration Burst Detected vs Active Baseline!`, 'error');
          }

          // State Array Graph Data Management (Time-Series FIFO Window - Keep last 30 frames)
          setData(prevData => {
            const timeStr = new Date().toLocaleTimeString();
            const newData = [...prevData, {
              time: timeStr.split(" ")[0], // Extract only mapping timespan to reduce clutter
              bytesOut: parseFloat(sensor.bytes_out) || 0,
              anomalyScoreScale: typeof sensor.anomaly_score === 'number' ? parseFloat(sensor.anomaly_score) * 10000 : 0 // Scaled to visualize vs Bytes effectively 
            }];
            return newData.slice(-30);
          });
        }
      } catch (err) {
        console.error("Payload parse error:", err);
      }
    };

    return () => ws.close();
  }, []);

  const addLog = (msg, type = 'info') => {
    // Only add log if last msg isn't exactly identical for flooding logic
    setLogs(prev => {
      if (prev.length > 0 && prev[prev.length - 1].msg === msg) return prev;
      return [...prev.slice(-12), { msg, type, id: Date.now() + Math.random() }];
    });
  };

  const executeAttack = async () => {
    addLog(`[${new Date().toLocaleTimeString()}] INJECT: Sending Payload vector -> ZeroDay Simulation (Sensor_01).`, 'warning');
    await fetch(`${API_URL}/api/attack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor_id: "sensor_01" })
    });
  };

  const executeRestore = async () => {
    addLog(`[${new Date().toLocaleTimeString()}] COMMAND SENT: Revoking strict Edge quarantine constraints.`, 'info');
    await fetch(`${API_URL}/api/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor_id: "sensor_01" })
    });
  };

  const isQuarantined = sensorState.status === 'QUARANTINED';

  return (
    <div className="min-h-screen max-w-7xl mx-auto p-4 md:p-8 font-mono">
      {/* HUD Header */}
      <header className="flex flex-col md:flex-row justify-between items-center mb-8 border-b border-slate-700/60 pb-5 gap-4">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-cyan-400 w-10 h-10" />
          <h1 className="text-3xl font-bold tracking-widest text-slate-100">EDGE_EDR <span className="text-opacity-80 text-cyan-500">SOC</span></h1>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Status Tracker Widget */}
          <div className={`px-4 py-2 font-bold tracking-widest text-sm rounded border shadow-lg ${isQuarantined ? 'bg-red-900/30 border-red-500/50 text-red-400 animate-pulse w-48 text-center' : (sensorState.status === 'UNDER_ATTACK' ? 'bg-orange-900/40 border-orange-500 text-orange-400 w-48 text-center animate-pulse' : 'bg-slate-800/80 border-cyan-800/50 text-cyan-400 w-48 text-center')}`}>
            STATUS: {sensorState.status}
          </div>
          
          {/* Score Threat Widget */}
          <div className="px-4 py-2 font-bold tracking-widest text-sm rounded bg-slate-800/80 border border-slate-700/80 text-yellow-300 w-44 text-center">
            SCORE: {sensorState.score} %
          </div>
        </div>
      </header>

      {/* Grid Architecture Array */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Analytics Live Telemetry Mapping Graph Panel (Primary) */}
        <div className="lg:col-span-2 bg-slate-800/40 backdrop-blur-sm border border-slate-700/60 rounded-xl p-5 shadow-2xl relative overflow-hidden group">
          {/* Neon Accent Glow */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-600/0 via-cyan-500/80 to-cyan-600/0"></div>
          
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-sm font-bold tracking-widest flex items-center gap-2 text-slate-300">
              <Activity className="text-cyan-400 w-5 h-5" /> EXFILTRATION TELEMETRY (IF-ML)
            </h2>
            <div className="text-xs text-slate-500">Real-time Node: Sensor_01 | Latency: {'<'}1s</div>
          </div>
          
          <div className="h-80 w-full bg-slate-900/40 rounded-lg p-2 border border-slate-800/50">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickMargin={10} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0', fontSize: '13px' }}
                  labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                <Line name="Network Flow (Bytes/s)" type="monotone" dataKey="bytesOut" stroke="#06b6d4" strokeWidth={2} dot={false} activeDot={{ r: 6, fill: '#06b6d4' }} />
                <Line name="ML Threat Density" type="stepAfter" dataKey="anomalyScoreScale" stroke="#ef4444" strokeWidth={2} dot={false} strokeOpacity={0.8} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* C2 Command Structure Engine and Live Logging Board */}
        <div className="flex flex-col gap-6">
          
          {/* Offensive Injection / Sandbox Platform */}
          <div className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/60 rounded-xl p-5 shadow-2xl relative">
            <h2 className="text-sm font-bold tracking-widest text-slate-400 border-b border-slate-700/80 pb-3 mb-5">ACTIVE RESPONSES & CONTROL</h2>
            
            <div className="flex flex-col gap-4">
              <button 
                onClick={executeAttack}
                disabled={isQuarantined}
                className={`group relative flex items-center justify-center gap-3 w-full py-4 px-2 
                  border-2 rounded font-bold tracking-widest transition-all duration-300
                  ${isQuarantined 
                    ? 'bg-slate-800/50 border-slate-700/50 text-slate-600 cursor-not-allowed' 
                    : 'bg-red-900/10 border-red-500/40 text-red-400 hover:bg-red-500 hover:text-white hover:border-red-400 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]'
                  }`}
              >
                <AlertTriangle className={`w-5 h-5 ${!isQuarantined ? 'group-hover:animate-pulse' : ''}`} />
                {isQuarantined ? 'SYSTEM ISOLATED' : 'INJECT ZERO-DAY TRAFFIC'}
              </button>
              
              <button 
                onClick={executeRestore}
                disabled={!isQuarantined}
                className={`flex items-center justify-center gap-3 w-full py-4 px-2 
                  border-2 rounded font-bold tracking-widest transition-all duration-300
                  ${!isQuarantined 
                    ? 'bg-slate-800/50 border-slate-700/50 text-slate-600 cursor-not-allowed' 
                    : 'bg-cyan-900/10 border-cyan-500/40 text-cyan-400 hover:bg-cyan-500 hover:text-slate-900 hover:border-cyan-400 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  }`}
              >
                <Zap className="w-5 h-5" />
                OVERRIDE QUARANTINE
              </button>
            </div>
          </div>

          {/* Audit Trail Terminal Pipeline Log */}
          <div className="flex-1 bg-[#0a0f18] border border-slate-800 rounded-xl p-4 shadow-2xl flex flex-col min-h-[16rem]">
            <h2 className="text-xs font-bold tracking-widest text-slate-500 mb-3 border-b border-slate-800/80 pb-2">AUDIT INCIDENT TRAIL (LOG)</h2>
            <div className="flex-1 overflow-y-auto flex flex-col justify-end space-y-1.5 scrollbar-thin scrollbar-thumb-slate-700">
              {logs.map((log) => (
                <div key={log.id} className={`text-xs pl-2 border-l-2 py-0.5 animate-fadeIn
                  ${log.type === 'error' ? 'text-red-400 border-red-500/50' 
                  : log.type === 'success' ? 'text-cyan-400 border-cyan-500/50' 
                  : log.type === 'warning' ? 'text-orange-400 border-orange-500/50'
                  : 'text-slate-400 border-slate-600'}`}>
                  {log.msg}
                </div>
              ))}
              {logs.length === 0 && <div className="text-slate-600 text-xs italic opacity-70">Awaiting edge node events...</div>}
            </div>
          </div>

        </div>
      </div>
      
      <div className="mt-8 text-center text-xs tracking-wider text-slate-600 border-t border-slate-800/50 pt-4">
        EDGE EDR - AUTONOMOUS RESPONSE PROTOCOLS ACTIVE - {new Date().getFullYear()}
      </div>
    </div>
  );
}
