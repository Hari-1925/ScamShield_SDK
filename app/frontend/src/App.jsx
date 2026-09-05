import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import Peer from 'simple-peer';
import axios from 'axios';
import { 
  Send, Phone, Video, Mic, VideoOff, MicOff, PhoneOff, AlertTriangle, 
  Search, MoreVertical, Paperclip, Smile, ShieldCheck, ShieldAlert, Loader, Activity
} from 'lucide-react';

const SOCKET_SERVER_URL = import.meta.env.VITE_SOCKET_URL || (window.location.hostname === 'localhost' ? 'http://localhost:3000' : 'https://scamshield-signaling.onrender.com');
const LOCAL_AGENT_URL = import.meta.env.VITE_LOCAL_AGENT_URL || 'http://localhost:8001';

const socket = io(SOCKET_SERVER_URL);

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function App() {
  const [me, setMe] = useState('');
  const [name, setName] = useState('');
  const [aiStatus, setAiStatus] = useState('loading');
  
  const [stream, setStream] = useState();
  const [receivingCall, setReceivingCall] = useState(false);
  const [caller, setCaller] = useState('');
  const [callerSignal, setCallerSignal] = useState();
  const [callAccepted, setCallAccepted] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [callType, setCallType] = useState('video');
  
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [users, setUsers] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  
  const [callAlert, setCallAlert] = useState(null);
  const [terminateCountdown, setTerminateCountdown] = useState(null);
  const [isScanningMedia, setIsScanningMedia] = useState(false);
  const [editingName, setEditingName] = useState(false);

  const myVideo = useRef();
  const userVideo = useRef();
  const connectionRef = useRef();
  const agentWsRef = useRef();
  const mediaRecorderRef = useRef();
  const fileInputRef = useRef();
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (terminateCountdown === null) return;
    if (terminateCountdown <= 0) {
      leaveCall();
      setTerminateCountdown(null);
      setCallAlert(null);
      return;
    }
    const timer = setTimeout(() => {
      setTerminateCountdown(prev => prev - 1);
    }, 1000);
    return () => clearTimeout(timer);
  }, [terminateCountdown]);

  useEffect(() => {
    const checkAiHealth = async () => {
      try {
        const res = await axios.get(`${LOCAL_AGENT_URL}/health`);
        if (res.data.status === 'ready') {
          setAiStatus('ready');
        } else {
          setTimeout(checkAiHealth, 2000);
        }
      } catch (err) {
        setAiStatus('error');
        setTimeout(checkAiHealth, 5000);
      }
    };
    checkAiHealth();
  }, []);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ 
      video: true, 
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
    }).then((mediaStream) => {
      setStream(mediaStream);
      if (myVideo.current) {
        myVideo.current.srcObject = mediaStream;
      }
    });

    const onConnect = () => {
      setMe(socket.id);
      setName(`User_${socket.id.substring(0,4)}`);
    };

    const onUpdateUsers = (usersList) => {
      setUsers(usersList.filter(id => id !== socket.id));
    };

    const onReceiveMessage = async (data) => {
      // Add the message to UI immediately so chat feels fast
      setMessages((prev) => [...prev, data]);
      
      // If it's a regular text message from SOMEONE ELSE that hasn't been flagged yet
      if (!data.mediaUrl && !data.isMalicious && data.user !== name) {
          try {
              // The RECEIVER'S edge AI scans the message natively
              const res = await axios.post(`${LOCAL_AGENT_URL}/scan_local_text`, { text: data.text, contact_id: data.user });
              const localData = res.data;
              
              if (localData.is_scam && !localData.error) {
                  // Instantly update the UI to warn the receiver!
                  setMessages((prev) => prev.map(m => m.id === data.id ? { ...m, isMalicious: true, isPending: true, alert: 'yellow', explanation: 'Locally assessed as suspicious. Pending Cloud AI verification...' } : m));
                  
                  // Escalate to Cloud for final verification
                  const cloudRes = await axios.post(`${LOCAL_AGENT_URL}/scan_cloud`, {
                      modality: localData.modality,
                      vectors: localData.vectors,
                      gate_score: localData.gate_score
                  });
                  
                  const report = cloudRes.data;
                  const newAlert = report.alert_level || 'red';
                  setMessages((prev) => prev.map(m => m.id === data.id ? { 
                      ...m, 
                      isPending: false,
                      isMalicious: (newAlert !== 'none' && newAlert !== 'green'), 
                      alert: newAlert, 
                      explanation: report.explanation || 'Cloud verification completed.',
                      scamType: report.scam_type 
                  } : m));
              }
          } catch (e) {
              console.error("Local incoming scan failed:", e);
          }
      }
    };

    const onMessageUpdated = (data) => {
      setMessages((prev) => prev.map(m => m.id === data.id ? { ...m, ...data.updates } : m));
    };

    const onCallMade = (data) => {
      setReceivingCall(true);
      setCaller(data.socket);
      setCallerSignal(data.offer);
      setCallType(data.callType);
    };

    socket.on('connect', onConnect);
    socket.on('update-users', onUpdateUsers);
    socket.on('receive-message', onReceiveMessage);
    socket.on('message-updated', onMessageUpdated);
    socket.on('call-made', onCallMade);

    return () => {
      socket.off('connect', onConnect);
      socket.off('update-users', onUpdateUsers);
      socket.off('receive-message', onReceiveMessage);
      socket.off('message-updated', onMessageUpdated);
      socket.off('call-made', onCallMade);
    };
  }, []);

  const startScamShieldScanner = (streamToScan) => {
    const ws = new WebSocket('ws://localhost:8001/scan_call_stream');
    agentWsRef.current = ws;

    ws.onopen = () => {
      let active = true;
      const recordChunk = () => {
        if (!active || ws.readyState !== WebSocket.OPEN) return;
        
        try {
          const mediaRecorder = new MediaRecorder(streamToScan);
          mediaRecorderRef.current = mediaRecorder;
          const chunks = [];
          
          mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) chunks.push(e.data);
          };
          
          mediaRecorder.onstop = async () => {
            if (ws.readyState === WebSocket.OPEN && chunks.length > 0) {
              const blob = new Blob(chunks, { type: 'audio/webm' });
              const buffer = await blob.arrayBuffer();
              ws.send(buffer);
            }
          };
          
          mediaRecorder.start();
          
          setTimeout(() => {
            if (mediaRecorder.state === 'recording') {
              mediaRecorder.stop();
            }
            recordChunk();
          }, 3000);
        } catch (e) {
          console.error("MediaRecorder error:", e);
        }
      };
      
      recordChunk();
      
      ws.onclose = () => {
        active = false;
      };
    };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "LOCAL_WARNING") {
          setCallAlert(prev => {
            if (prev && prev.type === 'cloud') return prev;
            return { type: 'local', message: data.reason };
          });
        } else if (data.action === "CLOUD_VERDICT") {
          console.log("REACT UI: Received CLOUD_VERDICT from Edge AI!", data);
          if (data.is_scam) {
            console.log("REACT UI: Setting Red Banner and 5-second countdown...");
            setCallAlert({ type: 'cloud', message: data.explanation });
            setTerminateCountdown(5);
          } else {
            setCallAlert({ type: 'safe', message: 'Cloud verified this call is safe.' });
            setTimeout(() => setCallAlert(null), 3000);
          }
        }
    };
  };

  const initiateCall = (id, type) => {
    if (stream) {
      stream.getVideoTracks().forEach(t => t.enabled = (type === 'video'));
    }
    setCallType(type);
    
    const peer = new Peer({ initiator: true, trickle: false, stream: stream });

    peer.on('signal', (data) => {
      socket.emit('call-user', { userToCall: id, offer: data, socket: socket.id, callType: type });
    });

    peer.on('stream', (userStream) => {
      if (userVideo.current) userVideo.current.srcObject = userStream;
      startScamShieldScanner(userStream);
    });

    socket.on('answer-made', (signal) => {
      setCallAccepted(true);
      peer.signal(signal.answer);
    });

    connectionRef.current = peer;
  };

  const answerCall = () => {
    setCallAccepted(true);
    if (stream) {
      stream.getVideoTracks().forEach(t => t.enabled = (callType === 'video'));
    }
    const peer = new Peer({ initiator: false, trickle: false, stream: stream });

    peer.on('signal', (data) => {
      socket.emit('make-answer', { answer: data, to: caller });
    });

    peer.on('stream', (userStream) => {
      if (userVideo.current) userVideo.current.srcObject = userStream;
      startScamShieldScanner(userStream);
    });

    peer.signal(callerSignal);
    connectionRef.current = peer;
  };

  const leaveCall = () => {
    setCallEnded(true);
    if (connectionRef.current) connectionRef.current.destroy();
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (agentWsRef.current) agentWsRef.current.close();
    
    // reset streams for next call
    if (stream) {
      stream.getVideoTracks().forEach(t => t.enabled = true);
    }
    
    setReceivingCall(false);
    setCallAccepted(false);
    setTerminateCountdown(null);
  };

  const sendMessage = async () => {
      if (!messageInput.trim()) return;
      
      const currentText = messageInput;
      setMessageInput('');

      // Secret cheat-code to change username
      if (currentText.startsWith('/name ')) {
          const newName = currentText.replace('/name ', '').trim();
          setName(newName);
          return;
      }

      if (aiStatus !== 'ready') {
        alert("AI Models are still loading. Please wait.");
        return;
      }

      const msgId = Date.now().toString();

    try {
      const res = await axios.post(`${LOCAL_AGENT_URL}/scan_local_text`, { 
        text: currentText, 
        contact_id: activeChat,
        sender_id: name 
      });
      const localData = res.data;

      const initialPayload = {
        id: msgId,
        user: name,
        text: currentText,
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        isMalicious: localData.is_scam,
        isPending: localData.is_scam,
        alert: localData.is_scam ? 'yellow' : 'none',
        explanation: localData.is_scam ? 'Locally assessed as suspicious. Pending Cloud AI verification...' : ''
      };
      
      socket.emit('send-message', initialPayload);

      if (localData.is_scam && !localData.error) {
        axios.post(`${LOCAL_AGENT_URL}/scan_cloud`, {
          modality: localData.modality,
          vectors: localData.vectors,
          gate_score: localData.gate_score
        }).then((cloudRes) => {
          const report = cloudRes.data;
          const newAlert = report.alert_level || 'yellow';
          socket.emit('update-message', {
            id: msgId,
            updates: {
              isPending: false,
              isMalicious: (newAlert !== 'none' && newAlert !== 'green'),
              alert: newAlert,
              explanation: report.explanation || 'Cloud verification completed.'
            }
          });
        }).catch((err) => {
          socket.emit('update-message', {
            id: msgId,
            updates: {
              isPending: false,
              explanation: 'Cloud verification failed or timed out.'
            }
          });
        });
      }

    } catch (err) {
      console.error("Local Agent Error:", err);
      alert("Local Security Agent is offline.");
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 20 * 1024 * 1024) {
      alert("File is too large for this demo (Max 20MB).");
      e.target.value = '';
      return;
    }

    setIsScanningMedia(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('contact_id', activeChat);
    const msgId = generateId();

    try {
      const res = await axios.post(`${LOCAL_AGENT_URL}/scan_local_media`, formData);
      const localData = res.data;
      
      const reader = new FileReader();
      reader.onload = () => {
        socket.emit('send-message', {
          id: msgId,
          user: name,
          text: '',
          mediaUrl: reader.result,
          mediaType: file.type,
          fileName: file.name,
          time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          isMalicious: localData.is_scam,
          isPending: localData.is_scam,
          alert: localData.is_scam ? 'yellow' : 'none',
          explanation: localData.is_scam ? 'Locally assessed as suspicious. Pending Cloud AI verification...' : ''
        });
        setIsScanningMedia(false);

        if (localData.is_scam && !localData.error) {
          axios.post(`${LOCAL_AGENT_URL}/scan_cloud`, {
            modality: localData.modality,
            vectors: localData.vectors,
            gate_score: localData.gate_score
          }).then((cloudRes) => {
            const report = cloudRes.data;
            const newAlert = report.alert_level || 'yellow';
            socket.emit('update-message', {
              id: msgId,
              updates: {
                isPending: false,
                isMalicious: (newAlert !== 'none' && newAlert !== 'green'),
                alert: newAlert,
                explanation: report.explanation || 'Cloud verification completed.'
              }
            });
          }).catch((err) => {
            socket.emit('update-message', {
              id: msgId,
              updates: {
                isPending: false,
                explanation: 'Cloud verification failed or timed out.'
              }
            });
          });
        }
      };
      reader.readAsDataURL(file);
    } catch (err) {
      console.error(err);
      alert("Local Security Agent failed to scan media.");
      setIsScanningMedia(false);
    }
    
    e.target.value = '';
  };

  if (aiStatus === 'loading') {
    return (
      <div className="min-h-screen bg-[#111b21] flex flex-col items-center justify-center text-white">
        <ShieldCheck className="w-24 h-24 text-[#00a884] mb-8 animate-pulse" />
        <div className="flex items-center gap-3 text-xl">
          <Loader className="w-6 h-6 animate-spin text-[#00a884]" />
          <span>Starting ScamShield Edge AI...</span>
        </div>
        <p className="text-gray-400 mt-4 text-sm max-w-md text-center">
          Loading AI models into local memory for end-to-end scam protection. This takes a few seconds on the first run.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 font-sans text-gray-100">
      {/* BACKGROUND EFFECTS */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-green-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="flex w-full h-full max-w-[1600px] mx-auto bg-black/40 overflow-hidden backdrop-blur-xl border border-white/5 shadow-2xl relative z-10">
        
        {/* LEFT PANE */}
        <div className="w-full md:w-[300px] flex flex-col bg-gray-900/70 border-r border-white/10 backdrop-blur-md relative z-20">
          {/* Header */}
          <div className="h-16 flex items-center justify-between px-4 bg-gray-800/70 border-b border-white/10">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-green-500 to-green-600 flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(99,102,241,0.4)]">
                {name.charAt(0).toUpperCase()}
              </div>
              {editingName ? (
                <input
                  autoFocus
                  defaultValue={name}
                  className="bg-black/40 border border-green-500/50 rounded-lg px-2 py-1 text-sm text-gray-100 outline-none w-36"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const v = e.target.value.trim();
                      if (v) setName(v);
                      setEditingName(false);
                    } else if (e.key === 'Escape') {
                      setEditingName(false);
                    }
                  }}
                  onBlur={(e) => {
                    const v = e.target.value.trim();
                    if (v) setName(v);
                    setEditingName(false);
                  }}
                />
              ) : (
                <div className="font-semibold text-gray-100 tracking-wide cursor-pointer hover:text-green-400 transition-colors flex items-center gap-1.5" onClick={() => setEditingName(true)} title="Click to change username">
                  {name}
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                </div>
              )}
            </div>
            <div className="flex gap-4 text-gray-400">
              <Activity className="w-5 h-5 hover:text-green-400 cursor-pointer transition-colors" />
              <MoreVertical className="w-5 h-5 hover:text-green-400 cursor-pointer transition-colors" />
            </div>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-white/10 bg-black/10">
            <div className="bg-black/40 flex items-center rounded-xl px-4 py-2.5 border border-white/5 focus-within:border-green-500/50 transition-all shadow-inner">
              <Search className="w-4 h-4 text-gray-500 mr-3" />
              <input type="text" placeholder="Search or start new chat" className="bg-transparent outline-none text-sm w-full text-gray-200 placeholder-gray-600" />
            </div>
          </div>

          {/* Users List */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-white/10">
            {users.map((u, i) => (
              <div 
                key={i} 
                onClick={() => setActiveChat(u)}
                className={`flex items-center gap-4 px-5 py-4 cursor-pointer transition-all duration-300 border-l-2 ${activeChat === u ? 'bg-green-500/10 border-green-500' : 'hover:bg-white/5 border-transparent'}`}
              >
                <div className="relative">
                  <div className="w-12 h-12 bg-gradient-to-br from-gray-700 to-gray-900 rounded-full flex items-center justify-center text-gray-300 font-bold border border-white/10">
                    U
                  </div>
                  <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-[#09090b] shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                </div>
                <div className="flex-1 border-b border-white/5 pb-2 pt-1">
                  <div className="flex justify-between items-center mb-1">
                    <div className="font-medium text-gray-100">User {u.substring(0,4)}</div>
                    <div className="text-[11px] text-gray-500">Now</div>
                  </div>
                  <div className="text-sm text-gray-400 truncate w-48">Online and ready to chat...</div>
                </div>
              </div>
            ))}
            {users.length === 0 && (
              <div className="text-center text-gray-500 mt-12 text-sm flex flex-col items-center gap-3">
                <Activity className="w-8 h-8 opacity-20" />
                Scanning network...
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANE */}
        <div className="hidden md:flex flex-1 flex-col min-h-0 bg-gray-900/70 overflow-hidden relative">
          
          {/* TOP SCAM ALERT OVERLAY (Z-50) */}
          {callAlert && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 w-full max-w-md z-50 animate-slide-down bg-yellow-500/10 border border-yellow-500/30 backdrop-blur-xl text-yellow-200 p-4 rounded-xl shadow-md flex items-center">
              {callAlert.type === 'local' ? (
                <div className="bg-yellow-500/10 border border-yellow-500/50 backdrop-blur-xl text-yellow-200 p-4 rounded-2xl shadow-[0_0_30px_rgba(234,179,8,0.2)] flex items-center justify-between">
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
                      <Activity className="w-5 h-5 animate-pulse text-yellow-400" />
                    </div>
                    <p className="font-medium text-sm leading-snug">{callAlert.message}</p>
                  </div>
                </div>
              ) : callAlert.type === 'cloud' ? (
                <div className="w-full max-w-md mx-auto bg-red-950/80 border border-red-500/50 backdrop-blur-2xl text-red-100 p-4 rounded-xl shadow-[0_0_40px_rgba(220,38,38,0.3)]">
                  <div className="flex gap-4 items-start mb-4">
                    <div className="w-12 h-12 rounded-full bg-red-500/20 flex flex-shrink-0 items-center justify-center shadow-[0_0_15px_rgba(220,38,38,0.5)]">
                      <AlertTriangle className="w-6 h-6 text-red-400" />
                    </div>
                    <div className="flex-1 pt-1">
                      <h3 className="font-bold text-lg mb-1 tracking-wide text-red-400">THREAT INTERCEPTED</h3>
                      <p className="text-sm leading-relaxed text-red-200/80">{callAlert.message}</p>
                    </div>
                  </div>
                  
                  {terminateCountdown !== null && (
                    <div className="bg-black/40 p-4 rounded-xl flex items-center justify-between border border-red-500/30">
                      <div className="font-medium flex items-center gap-3 text-red-300 text-sm">
                        <PhoneOff className="w-5 h-5 animate-pulse" /> 
                        Auto-Terminating in <span className="text-2xl font-bold text-red-500 w-6 text-center">{terminateCountdown}</span>s
                      </div>
                      <button 
                        onClick={() => setTerminateCountdown(null)} 
                        className="bg-white/5 hover:bg-white/10 text-gray-300 font-medium px-4 py-2 rounded-lg transition-all text-xs border border-white/10 uppercase tracking-wider"
                      >
                        Override
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-emerald-950/80 border border-emerald-500/50 backdrop-blur-xl text-emerald-200 p-4 rounded-2xl shadow-[0_0_30px_rgba(16,185,129,0.2)] flex items-center justify-between">
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <ShieldCheck className="w-5 h-5 text-emerald-400" />
                    </div>
                    <p className="font-medium text-sm leading-snug">{callAlert.message}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeChat ? (
            <>
              {/* Chat Header */}
              <div className="h-16 flex items-center px-4 bg-gray-800/70 border-b border-white/10 shadow-md">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-gray-300 font-bold border border-white/10">U</div>
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 rounded-full border-2 border-[#1a1a1a]"></div>
                  </div>
                  <div className="flex flex-col justify-center">
                    <div className="font-medium text-gray-100 tracking-wide">User {activeChat.substring(0,4)}</div>
                    <div className="text-xs text-emerald-400/80 font-medium">Secured Connection</div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => initiateCall(activeChat, 'video')} className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-300 hover:text-green-400 transition-all border border-white/5"><Video className="w-5 h-5" /></button>
                  <button onClick={() => initiateCall(activeChat, 'audio')} className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-300 hover:text-green-400 transition-all border border-white/5"><Phone className="w-5 h-5" /></button>
                </div>
              </div>

              {/* Chat Messages */}
              <div ref={messagesContainerRef} className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-6 flex flex-col gap-4 z-0 relative bg-gray-900/70">
                <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '20px 20px'}}></div>

                {messages.map((m, i) => {
                  const isMe = m.user === name;
                  const isSuspicious = m.isMalicious && !isMe;
                  const isPending = m.isPending;
                  
                  return (
                    <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} mb-2 relative z-10 animate-in slide-in-from-bottom-2 fade-in duration-300`}>
                      <div className={`relative max-w-[75%] rounded-2xl text-[15px] leading-relaxed flex flex-col shadow-xl ${isMe ? 'bg-gradient-to-r from-green-500 to-green-600 text-white rounded-br-sm' : 'bg-[#2a2a2e] text-gray-200 rounded-bl-sm border border-white/5'}`}>
                        
                        <div className="p-3.5">
                            {!isMe && <div className="text-[11px] font-bold text-green-300 mb-1.5 px-1 uppercase tracking-wider">{m.user}</div>}
                            
                            <div className="px-1">
                            {m.mediaUrl ? (
                                m.mediaType?.startsWith('image/') ? (
                                <img src={m.mediaUrl} alt="shared" className="max-w-xs rounded-xl border border-white/10 shadow-md" />
                                ) : m.mediaType?.startsWith('video/') ? (
                                <video src={m.mediaUrl} controls className="max-w-sm rounded-xl border border-white/10 shadow-md" />
                                ) : m.mediaType?.startsWith('audio/') ? (
                                <audio src={m.mediaUrl} controls className="w-64 mt-1 opacity-90" />
                                ) : (
                                <a href={m.mediaUrl} download={m.fileName} className="text-green-300 hover:text-green-200 underline text-sm break-all flex items-center gap-2 bg-black/20 p-3 rounded-xl">
                                    <Paperclip className="w-4 h-4" /> {m.fileName}
                                </a>
                                )
                            ) : (
                                <span>{m.text}</span>
                            )}
                            </div>
                            
                            <span className={`absolute bottom-2 right-3 text-[10px] font-medium ${isMe ? 'text-green-200/70' : 'text-gray-500'}`}>{m.time}</span>
                        </div>

                        {/* Scam Alert Bubble Append */}
                        {isSuspicious && (
                            <div className="w-full bg-red-950/90 border border-red-500/30 rounded-2xl flex flex-col gap-1.5 p-5 shadow-[0_0_40px_rgba(220,38,38,0.3)]">
                                <div className="flex items-center gap-2 font-bold text-[10px] tracking-widest uppercase text-red-400">
                                    {isPending ? (
                                      <><Activity className="w-3.5 h-3.5 animate-pulse" /> AI Analyzing...</>
                                    ) : (
                                      <><AlertTriangle className="w-3.5 h-3.5" /> Threat Detected ({m.alert})</>
                                    )}
                                </div>
                                <div className="text-[13px] leading-snug text-red-200/90 font-medium">
                                    {m.explanation || 'Suspicious content detected.'}
                                </div>
                            </div>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input */}
              <div className="h-16 bg-black/5 backdrop-blur-xl flex items-center gap-4 z-10 border-t border-white/10">
                <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-green-400">
                  <Smile className="w-6 h-6" />
                </button>
                <button onClick={() => fileInputRef.current.click()} disabled={isScanningMedia} className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-green-400 disabled:opacity-50">
                  <Paperclip className="w-5 h-5" />
                </button>
                
                <div className="flex-1 bg-black/40 border border-white/10 rounded-full flex items-center px-2 py-1 focus-within:border-green-500/50 focus-within:bg-black/60 transition-all shadow-inner">
                  <input 
                    type="text" 
                    value={messageInput}
                    onChange={e => setMessageInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="Type a message..." 
                    disabled={isScanningMedia}
                    className="flex-1 bg-transparent py-2.5 px-4 outline-none text-[15px] text-gray-200 placeholder-gray-600"
                  />
                  <button onClick={sendMessage} disabled={isScanningMedia || !messageInput.trim()} className="w-10 h-10 bg-green-600 hover:bg-green-500 rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:bg-gray-800 shadow-[0_0_15px_rgba(34,197,94,0.4)]">
                    <Send className="w-4 h-4 text-white ml-1" />
                  </button>
                <input type="file" ref={fileInputRef} style={{position: 'absolute', left: '-9999px'}} onChange={handleFileUpload} disabled={isScanningMedia} />
                </div>
                
                {!messageInput.trim() && (
                  <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-green-400">
                    <Mic className="w-5 h-5" />
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 z-10 bg-black/20">
              <div className="relative w-32 h-32 mb-8">
                <div className="absolute inset-0 bg-green-500/20 rounded-full blur-2xl animate-pulse"></div>
                <div className="w-full h-full bg-black/50 border border-white/10 backdrop-blur-xl rounded-full flex items-center justify-center shadow-2xl relative z-10">
                  <ShieldAlert className="w-12 h-12 text-green-400" />
                </div>
              </div>
              <h2 className="text-3xl font-light text-gray-200 mb-4 tracking-wide">ScamShield <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">Edge</span></h2>
              <p className="text-sm text-gray-400 text-center max-w-md leading-relaxed px-6">
                Send and receive messages with military-grade Edge AI protection. <br/>
                Your chats are monitored locally before ever leaving your device.
              </p>
              <div className="mt-8 flex items-center gap-2 text-xs text-green-400/60 uppercase tracking-widest font-bold bg-green-500/10 px-4 py-2 rounded-full border border-green-500/20">
                <ShieldCheck className="w-4 h-4" /> End-to-end Protected
              </div>
            </div>
          )}

          {/* WebRTC Call Overlay (Glassmorphism HUD) */}
          {(receivingCall || callAccepted) && !callEnded && (
            <div className="absolute inset-0 z-40 flex flex-col bg-black/80 backdrop-blur-2xl animate-in zoom-in-95 fade-in duration-300 overflow-hidden">
              
              {/* Ambient Call Background Glow */}
              <div className="absolute inset-0 bg-gradient-to-b from-green-900/20 via-transparent to-black pointer-events-none" />
              
              <div className="p-6 flex justify-between items-center relative z-10">
                <div className="text-green-200 text-sm flex items-center gap-2 font-bold uppercase tracking-widest bg-white/5 px-4 py-2 rounded-full border border-white/10">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" /> Secured Stream
                </div>
              </div>
              
              <div className="flex-1 relative flex items-center justify-center px-8">
                {callAccepted ? (
                  <video 
                    playsInline 
                    ref={userVideo} 
                    autoPlay 
                    className={`w-full max-w-4xl max-h-[70vh] rounded-3xl object-cover shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/10 ${callType === 'audio' ? 'hidden' : 'block'}`} 
                  />
                ) : (
                  <div className="text-white text-center flex flex-col items-center relative z-10">
                    <div className="w-32 h-32 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-full mb-6 flex items-center justify-center text-5xl shadow-[0_0_40px_rgba(79,70,229,0.6)] font-bold animate-pulse border-4 border-black">
                      U
                    </div>
                    <h2 className="text-4xl font-light mb-2 tracking-tight">Incoming <span className="font-bold">{callType}</span> call...</h2>
                    <p className="text-gray-400 text-lg uppercase tracking-widest">User {caller.substring(0,4)}</p>
                  </div>
                )}
                
                {callType === 'audio' && callAccepted && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                     <div className="relative">
                       {/* Audio Ring Waves */}
                       <div className="absolute inset-0 bg-indigo-500 rounded-full animate-ping opacity-20"></div>
                       <div className="absolute inset-[-20px] bg-purple-500 rounded-full animate-ping opacity-10 animation-delay-200"></div>
                       
                       <div className="w-40 h-40 bg-gradient-to-br from-indigo-600 to-purple-800 rounded-full mb-8 flex items-center justify-center text-7xl shadow-[0_0_50px_rgba(79,70,229,0.5)] text-white font-bold relative z-10 border-4 border-black">
                         U
                       </div>
                     </div>
                     <div className="text-3xl text-white mb-3 font-light tracking-wide">User {activeChat?.substring(0,4) || 'Unknown'}</div>
                     <div className="text-emerald-400 flex items-center gap-3 font-mono text-xl bg-black/40 px-5 py-2 rounded-full border border-white/5">
                       <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]"></div> 
                       00:00
                     </div>
                  </div>
                )}

                <video 
                  playsInline 
                  muted 
                  ref={myVideo} 
                  autoPlay 
                  className={`absolute top-0 right-8 w-40 h-60 bg-black/50 object-cover rounded-2xl border border-white/20 shadow-2xl z-20 ${callType === 'audio' ? 'hidden' : 'block'}`} 
                />
              </div>

              <div className="h-32 flex items-center justify-center gap-10 pb-8 relative z-10">
                {!callAccepted && receivingCall && (
                  <button onClick={answerCall} className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.4)] hover:bg-emerald-400 hover:scale-110 transition-all">
                    <Phone className="w-7 h-7 text-white" />
                  </button>
                )}
                {callType === 'video' && (
                  <button className="w-14 h-14 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center hover:bg-white/20 text-white transition-all border border-white/5">
                    <VideoOff className="w-6 h-6" />
                  </button>
                )}
                <button className="w-14 h-14 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center hover:bg-white/20 text-white transition-all border border-white/5">
                  <MicOff className="w-6 h-6" />
                </button>
                <button onClick={leaveCall} className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.4)] hover:bg-red-400 hover:scale-110 text-white transition-all">
                  <PhoneOff className="w-7 h-7" />
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
