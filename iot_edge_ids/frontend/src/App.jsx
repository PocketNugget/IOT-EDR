import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, ShieldCheck, Activity, WifiOff } from 'lucide-react';

const WEBSOCKET_URL = "ws://localhost:8000/ws/telemetry";
const API_URL = "http://localhost:8000/api";
const DEVICE_ID = "sensor_01";

function App() {
  const [data, setData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState("UNKNOWN");
  const ws = useRef(null);

  useEffect(() => {
    // Setup WebSocket
    ws.current = new WebSocket(WEBSOCKET_URL);
    
    ws.current.onopen = () => console.log("WebSocket connectado al backend SOC.");
    
    ws.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const devices = msg.devices;
      
      if (devices && devices[DEVICE_ID]) {
        const telemetry = devices[DEVICE_ID].telemetry || {};
        const scoreData = devices[DEVICE_ID].score || {};
        
        // Mantener las últimas 20 muestras
        setData(prevData => {
          const newData = [...prevData, {
            time: new Date().toLocaleTimeString(),
            bytes_out: telemetry.bytes_out || 0,
            packet_rate: telemetry.packet_rate || 0,
            anomaly_score: scoreData.score || 0,
            is_anomaly: scoreData.is_anomaly ? 100 : 0
          }];
          return newData.slice(-20);
        });

        // Actualizar estado del dispositivo
        setDeviceStatus(telemetry.status || "UNKNOWN");
      }

      // Actualizar Alertas Críticas
      if (msg.alerts) {
        setAlerts([...msg.alerts].reverse()); // Más recientes primero
      }
    };

    ws.current.onclose = () => console.log("WebSocket desconectado. Intentar reconectar...");

    return () => {
        if (ws.current) ws.current.close();
    }
  }, []);

  const triggerAttack = async () => {
    try {
      await fetch(`${API_URL}/attack/${DEVICE_ID}`, { method: "POST" });
    } catch (e) {
      console.error(e);
    }
  };

  const triggerRestore = async () => {
    try {
      await fetch(`${API_URL}/restore/${DEVICE_ID}`, { method: "POST" });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-8 font-mono">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400 tracking-wider">EDGE EDR SOC COMMAND CENTER</h1>
          <p className="text-slate-400 text-sm mt-1">Autonomous IoT Threat Detection Platform</p>
        </div>
        <div className="flex items-center space-x-4 bg-slate-800 p-3 rounded-lg border border-slate-700 shadow-inner">
          <div className={`p-2 rounded-full ${deviceStatus === 'QUARANTINED' ? 'bg-red-500/20 text-red-500' : 'bg-green-500/20 text-green-500'}`}>
            {deviceStatus === 'QUARANTINED' ? <WifiOff size={24} /> : <Activity size={24} />}
          </div>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-widest">DEVICE STATUS: {DEVICE_ID}</div>
            <div className={`text-lg font-bold ${deviceStatus === 'UNDER_ATTACK' ? 'text-yellow-400 animate-pulse' : deviceStatus === 'QUARANTINED' ? 'text-red-500' : 'text-green-400'}`}>
              {deviceStatus}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Gráfico Principal */}
        <div className="lg:col-span-2 bg-slate-800/50 p-6 rounded-xl border border-slate-700 shadow-xl backdrop-blur-sm">
          <h2 className="text-xl text-cyan-400 font-semibold mb-6 flex items-center">
            <Activity className="mr-2 h-5 w-5" /> Live Telemetry & Anomaly Detection (Isolation Forest)
          </h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" tick={{fontSize: 12}} />
                <YAxis yAxisId="left" stroke="#94a3b8" />
                <YAxis yAxisId="right" orientation="right" stroke="#ef4444" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend iconType="circle" />
                <Line yAxisId="left" type="monotone" dataKey="bytes_out" stroke="#22d3ee" strokeWidth={2} dot={false} isAnimationActive={false} name="Network Out (Bytes)" />
                <Line yAxisId="right" type="stepAfter" dataKey="is_anomaly" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} name="Anomaly Alert (ML)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel de Control Industrial */}
        <div className="space-y-8">
          <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 shadow-xl">
            <h2 className="text-xl text-cyan-400 font-semibold mb-6">Action Panel</h2>
            <div className="space-y-4">
              <button 
                onClick={triggerAttack}
                className="w-full relative group overflow-hidden bg-slate-900 border border-red-500/50 hover:border-red-500 p-4 rounded-lg flex items-center justify-center transition-all duration-300"
              >
                <div className="absolute inset-0 bg-red-500/10 group-hover:bg-red-500/20 transition-all"></div>
                <AlertTriangle className="text-red-500 mr-3 h-6 w-6 group-hover:scale-110 transition-transform" />
                <span className="text-red-500 font-bold tracking-widest">INJECT ZERO-DAY TRAFFIC</span>
              </button>

              <button 
                onClick={triggerRestore}
                className="w-full relative group overflow-hidden bg-slate-900 border border-cyan-400/50 hover:border-cyan-400 p-4 rounded-lg flex items-center justify-center transition-all duration-300"
              >
                <div className="absolute inset-0 bg-cyan-400/10 group-hover:bg-cyan-400/20 transition-all"></div>
                <ShieldCheck className="text-cyan-400 mr-3 h-6 w-6 group-hover:scale-110 transition-transform" />
                <span className="text-cyan-400 font-bold tracking-widest">OVERRIDE QUARANTINE</span>
              </button>
            </div>
          </div>

          {/* Log de Incidentes */}
          <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 shadow-xl max-h-[400px] overflow-y-auto">
            <h2 className="text-xl text-cyan-400 font-semibold mb-6 sticky top-0 bg-slate-800/90 py-2 z-10">Incident Log</h2>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="text-slate-500 text-sm italic">No active incidents detected.</div>
              ) : (
                alerts.map((alert, idx) => (
                  <div key={idx} className="bg-red-950/40 border-l-4 border-red-500 p-3 rounded text-sm relative">
                    <div className="text-red-400 font-bold flex items-center justify-between mb-1">
                      <span>{alert.severity} ALERT - {alert.device_id}</span>
                      <span className="text-slate-500 text-xs font-normal">{new Date(alert.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-slate-300">{alert.reason}</div>
                    <div className="mt-2 inline-block px-2 py-1 bg-red-900/50 text-red-200 text-xs font-bold rounded">
                      ACTION: {alert.action_taken}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
