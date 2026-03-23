import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, Lightbulb, ToggleLeft, Cpu, Download, Zap, RefreshCcw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_URL = "http://localhost:8002";
const WS_URL = "ws://localhost:8002/ws/soc_feed";

export default function App() {
  const [data, setData] = useState({ inventory: {}, logs: [] });
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setData(payload);
        
        const devices = Object.values(payload.inventory || {});
        if(devices.length > 0) {
            const avgScore = devices.reduce((acc, dev) => acc + (dev.anomaly_score || 0), 0) / devices.length;
            setChartData(prev => {
                const updated = [...prev, { time: new Date().toLocaleTimeString().split(' ')[0], score: avgScore * 100 }];
                return updated.slice(-30);
            });
        }
      } catch (err) {
        console.error("WS Parsing Error:", err);
      }
    };
    return () => ws.close();
  }, []);

  const sendAction = async (device_id, action) => {
    await fetch(`${API_URL}/api/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id, action })
    });
  };

  const getStatusColor = (status) => {
    if (status === 'ONLINE') return 'text-green-400 border-green-500 bg-green-900/20';
    if (status === 'UPDATING') return 'text-blue-400 border-blue-500 bg-blue-900/40 animate-pulse';
    if (status === 'QUARANTINED') return 'text-red-500 border-red-500 bg-red-900/40 animate-pulse outline outline-2 outline-red-500';
    if (status === 'ATTACKING') return 'text-orange-400 border-orange-500 bg-orange-900/40 animate-ping';
    return 'text-slate-400 border-slate-600 bg-slate-800';
  };

  const getDeviceIcon = (type) => {
    if (type === 'bulb') return <Lightbulb className="w-8 h-8 opacity-80" />;
    if (type === 'switch') return <ToggleLeft className="w-8 h-8 opacity-80" />;
    return <Cpu className="w-8 h-8 opacity-80" />; // hub
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-4 font-mono select-none">
      <header className="flex flex-col md:flex-row justify-between items-center mb-6 border-b border-slate-700/60 pb-4 gap-4">
        <div className="flex items-center gap-4">
          <ShieldAlert className="text-cyan-500 w-12 h-12" />
          <div>
            <h1 className="text-2xl font-bold tracking-widest text-slate-100">SMART HOME <span className="text-cyan-500">EDR SOC</span></h1>
            <h2 className="text-xs text-slate-400 tracking-widest">CONTEXT-AWARE ML TOPOLOGY</h2>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Device Matrix Column */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-bold tracking-widest border-b border-slate-800 pb-2 text-slate-300 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500"/> IOT MESH INVENTORY
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.values(data.inventory).map(device => {
              const isIso = device.status === 'QUARANTINED';
              const isAttacking = device.status === 'ATTACKING';
              return (
                <div key={device.metrics.device_id} className="bg-slate-900/80 border border-slate-700/50 rounded-lg p-4 shadow-xl flex flex-col gap-3 transition-colors relative">
                  
                  {isIso && <div className="absolute inset-0 bg-red-900/10 pointer-events-none"></div>}
                  
                  <div className="flex justify-between items-start z-10">
                    <div className="flex items-center gap-3">
                      <div className={isIso ? 'text-red-500' : 'text-cyan-400'}>
                        {getDeviceIcon(device.device_type)}
                      </div>
                      <div>
                        <div className="font-bold text-sm tracking-wider text-slate-200">
                          {device.metrics.device_id.toUpperCase().replace(/_/g, " ")}
                        </div>
                        <div className="text-[10px] text-slate-400 font-bold">
                          PROFILE: {device.device_type.toUpperCase()} | SCORE: {(device.anomaly_score * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                    <div className={`px-2 py-0.5 text-[10px] tracking-widest font-bold rounded border ${getStatusColor(device.status)}`}>
                      {device.status}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] text-slate-400 mt-1 bg-[#0a0f18] p-2 rounded z-10 border border-slate-800/80">
                    <div>Pkt/s: <span className="text-slate-200 font-bold">{device.metrics.packet_rate}</span></div>
                    <div>Port: <span className="text-slate-200 font-bold">{device.metrics.port}</span></div>
                    <div>Out: <span className="text-slate-200 font-bold">{device.metrics.bytes_out} B</span></div>
                    <div>In: <span className="text-slate-200 font-bold">{device.metrics.bytes_in} B</span></div>
                  </div>
                  
                  <div className="mt-2 flex gap-2 w-full z-10">
                    <button 
                        onClick={() => sendAction(device.metrics.device_id, 'ota')} 
                        disabled={isIso || isAttacking} 
                        className={`flex-1 text-[10px] tracking-widest py-2 rounded flex justify-center items-center gap-1 font-bold transition-all border
                        ${(isIso || isAttacking) ? 'bg-slate-800/50 text-slate-600 border-slate-700/50 cursor-not-allowed' : 'bg-blue-900/10 border-blue-800 text-blue-400 hover:bg-blue-600 hover:text-white'}`}>
                      <Download className="w-3 h-3"/> FORCE OTA
                    </button>
                    <button 
                        onClick={() => sendAction(device.metrics.device_id, 'attack')} 
                        disabled={isIso || isAttacking} 
                        className={`flex-1 text-[10px] tracking-widest py-2 rounded flex justify-center items-center gap-1 font-bold transition-all border
                        ${(isIso || isAttacking) ? 'bg-slate-800/50 text-slate-600 border-slate-700/50 cursor-not-allowed' : 'bg-orange-900/10 border-orange-800 text-orange-400 hover:bg-orange-600 hover:text-white'}`}>
                      <Zap className="w-3 h-3"/> INJECT BOT
                    </button>
                    {isIso && (
                      <button 
                        onClick={() => sendAction(device.metrics.device_id, 'restore')} 
                        className="flex-1 text-[10px] tracking-widest py-2 rounded flex justify-center items-center gap-1 font-bold bg-green-900/20 border border-green-700 text-green-400 hover:bg-green-600 hover:text-white transition-all">
                        <RefreshCcw className="w-3 h-3"/> RESTORE
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
            {Object.keys(data.inventory).length === 0 && <div className="text-slate-500 italic text-sm p-4">Awaiting nodes to join mesh network...</div>}
          </div>
          
          {/* Global Mean Threat Chart */}
          <div className="bg-slate-900/80 border border-slate-700/50 rounded-lg p-4 shadow-xl h-[18rem] mt-6">
             <h2 className="text-xs font-bold tracking-widest text-slate-400 mb-4 flex justify-between">
                ECOSYSTEM THREAT TRAJECTORY (Mean ML Density)
             </h2>
             <ResponsiveContainer width="100%" height="90%">
               <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickMargin={8} />
                  <YAxis stroke="#64748b" fontSize={10} domain={[0, 'auto']}/>
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', borderRadius: '4px' }} 
                    itemStyle={{fontSize: '12px'}}
                  />
                  <Line type="stepAfter" dataKey="score" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
               </LineChart>
             </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Logs Terminal */}
        <div className="bg-[#050505] border border-slate-800 rounded-lg p-5 shadow-2xl flex flex-col h-[calc(100vh-8rem)]">
          <h2 className="text-xs font-bold tracking-widest text-slate-500 mb-4 border-b border-slate-800/80 pb-3">SIEM AUDIT TERMINAL</h2>
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 custom-scrollbar flex flex-col justify-end">
            {data.logs.map((log) => (
              <div key={log.id} className="text-[11px] font-mono leading-relaxed border-l-2 pl-2 border-slate-800">
                <span className="text-slate-600 opacity-80">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>{' '}
                <span className="text-cyan-600 font-bold">{log.device_id.toUpperCase()}</span>{' '}
                <br/>
                <span className={`
                  ${log.level === 'error' ? 'text-red-400 font-bold' 
                  : log.level === 'success' ? 'text-green-400 font-bold' 
                  : log.level === 'warning' ? 'text-orange-400' 
                  : 'text-slate-300'}
                `}>
                  » {log.message}
                </span>
              </div>
            ))}
            {data.logs.length === 0 && <span className="text-slate-600 italic text-xs">Listening to secure event bus...</span>}
          </div>
        </div>
        
      </div>
    </div>
  );
}
