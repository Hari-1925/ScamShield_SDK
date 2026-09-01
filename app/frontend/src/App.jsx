import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import Peer from 'simple-peer';
import axios from 'axios';
import { 
  Send, Phone, Video, Mic, VideoOff, MicOff, PhoneOff, AlertTriangle, 
  Search, MoreVertical, Paperclip, Smile, ShieldCheck, ShieldAlert, Loader, Activity
} from 'lucide-react';

const SOCKET_SERVER_URL = 'http://localhost:3000';
const LOCAL_AGENT_URL = 'http://localhost:8001';

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

  const myVideo = useRef();
  const userVideo = useRef();
  const connectionRef = useRef();
  const agentWsRef = useRef();
  const mediaRecorderRef = useRef();
  const fileInputRef = useRef();
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
    navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then((mediaStream) => {
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

    const onReceiveMessage = (data) => {
      setMessages((prev) => [...prev, data]);
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
        if (data.is_scam) {
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
    if (aiStatus !== 'ready') {
      alert("AI Models are still loading. Please wait.");
      return;
    }

    const currentText = messageInput;
    setMessageInput('');
    const msgId = generateId();

    try {
      const res = await axios.post(`${LOCAL_AGENT_URL}/scan_local_text`, { text: currentText, contact_id: activeChat });
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
          socket.emit('update-message', {
            id: msgId,
            updates: {
              isPending: false,
              alert: report.alert_level || 'yellow',
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
            socket.emit('update-message', {
              id: msgId,
              updates: {
                isPending: false,
                alert: report.alert_level || 'yellow',
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
    <div className="h-screen w-full bg-[#d1d7db] flex items-center justify-center p-0 md:p-6 font-sans">
      
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileUpload} 
        style={{ display: 'none' }} 
        accept="image/*,video/*,audio/*"
      />

      <div className="flex w-full h-full max-w-[1600px] bg-white md:shadow-lg md:rounded-lg overflow-hidden">
        
        {/* LEFT PANE */}
        <div className="w-full md:w-[30%] lg:w-[30%] max-w-[400px] border-r border-gray-200 flex flex-col bg-white">
          <div className="h-16 bg-[#f0f2f5] flex items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#dfe5e7] rounded-full flex items-center justify-center text-gray-600 font-bold">
                {name.substring(0,1).toUpperCase()}
              </div>
              <div className="font-medium text-gray-800">{name}</div>
            </div>
            <div className="flex text-gray-500 gap-4">
              {aiStatus === 'ready' ? 
                <ShieldCheck className="w-5 h-5 text-[#00a884]" title="ScamShield Active" /> : 
                <ShieldAlert className="w-5 h-5 text-red-500" title="ScamShield Offline" />
              }
              <MoreVertical className="w-5 h-5" />
            </div>
          </div>
          <div className="p-2 bg-white border-b border-gray-100">
            <div className="bg-[#f0f2f5] flex items-center rounded-lg px-3 py-1.5">
              <Search className="w-4 h-4 text-gray-500 mr-3" />
              <input type="text" placeholder="Search or start new chat" className="bg-transparent border-none outline-none text-sm w-full text-gray-700" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {users.map(u => (
              <div 
                key={u} 
                onClick={() => setActiveChat(u)}
                className={`flex items-center px-3 py-3 border-b border-gray-100 cursor-pointer hover:bg-[#f5f6f6] ${activeChat === u ? 'bg-[#f0f2f5]' : ''}`}
              >
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold mr-3 shrink-0">
                  U
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="text-[#111b21] font-normal text-base truncate">User {u.substring(0,4)}</h3>
                    <span className="text-xs text-[#00a884]">Online</span>
                  </div>
                  <p className="text-[13px] text-gray-500 truncate">Tap to open chat</p>
                </div>
              </div>
            ))}
            {users.length === 0 && (
              <div className="text-center text-gray-400 mt-10 text-sm">No contacts online.</div>
            )}
          </div>
        </div>

        {/* RIGHT PANE */}
        <div className="hidden md:flex flex-1 flex-col relative bg-[#efeae2]">
          
          {activeChat ? (
            <>
              {/* Chat Header */}
              <div className="h-16 bg-[#f0f2f5] flex items-center justify-between px-4 shadow-sm z-10 border-l border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">U</div>
                  <div className="flex flex-col justify-center">
                    <div className="font-medium text-[#111b21] leading-tight">User {activeChat.substring(0,4)}</div>
                    <div className="text-[13px] text-gray-500">Online</div>
                  </div>
                </div>
                <div className="flex gap-4 text-[#54656f]">
                  <button onClick={() => initiateCall(activeChat, 'video')} className="hover:text-[#00a884] transition" title="Video Call"><Video className="w-5 h-5" /></button>
                  <button onClick={() => initiateCall(activeChat, 'audio')} className="hover:text-[#00a884] transition" title="Audio Call"><Phone className="w-5 h-5" /></button>
                  <Search className="w-5 h-5 ml-2" />
                </div>
              </div>

              {/* Top Scam Alert Overlay for Calls */}
              {callAlert && (
                <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-50 w-[90%] max-w-2xl">
                  {callAlert.type === 'local' ? (
                    <div className="bg-yellow-50 border-l-4 border-yellow-500 text-yellow-700 p-4 shadow-xl rounded flex items-center justify-between animate-pulse">
                      <div className="flex gap-3 items-center">
                        <Activity className="w-6 h-6 flex-shrink-0" />
                        <p className="font-medium text-sm leading-snug">{callAlert.message}</p>
                      </div>
                    </div>
                  ) : callAlert.type === 'cloud' ? (
                    <div className="bg-red-50 border-l-4 border-red-600 text-red-700 p-5 shadow-2xl rounded">
                      <div className="flex gap-3 items-start mb-3">
                        <AlertTriangle className="w-6 h-6 flex-shrink-0 mt-1" />
                        <div className="flex-1">
                          <h3 className="font-bold text-lg mb-1">Scam Alert (Cloud Verified)</h3>
                          <p className="text-sm leading-relaxed mb-3">{callAlert.message}</p>
                        </div>
                      </div>
                      
                      {terminateCountdown !== null && (
                        <div className="bg-red-100 p-3 rounded-lg flex items-center justify-between border border-red-200">
                          <div className="font-semibold flex items-center gap-2">
                            <PhoneOff className="w-4 h-4" /> 
                            Call will auto-terminate in <span className="text-xl mx-1">{terminateCountdown}</span> seconds
                          </div>
                          <button 
                            onClick={() => setTerminateCountdown(null)} 
                            className="bg-white text-red-600 font-bold px-4 py-2 rounded hover:bg-gray-50 transition shadow-sm text-sm border border-red-300"
                          >
                            Ignore & Keep Call Alive
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-4 shadow-xl rounded flex items-center justify-between">
                      <div className="flex gap-3 items-center">
                        <ShieldCheck className="w-6 h-6 flex-shrink-0" />
                        <p className="font-medium text-sm leading-snug">{callAlert.message}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {isScanningMedia && (
                <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-50 bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-3 shadow-lg rounded flex items-center gap-3">
                  <Loader className="w-5 h-5 animate-spin" />
                  <p className="font-medium text-sm">ScamShield Edge AI is analyzing media...</p>
                </div>
              )}

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 z-0">
                {messages.map((m, i) => {
                  const isMe = m.user === name;
                  const isSuspicious = m.isMalicious;
                  const isPending = m.isPending;
                  
                  let alertColor = '';
                  if (isPending) alertColor = 'bg-yellow-50 text-yellow-700 border-yellow-200';
                  else if (m.alert === 'red') alertColor = 'bg-red-50 text-red-700 border-red-200';
                  else if (m.alert === 'orange') alertColor = 'bg-orange-50 text-orange-700 border-orange-200';
                  else if (m.alert === 'yellow') alertColor = 'bg-yellow-50 text-yellow-700 border-yellow-200';
                  else if (m.alert === 'green') alertColor = 'bg-green-50 text-green-700 border-green-200';

                  return (
                    <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} mb-1`}>
                      <div className={`relative max-w-[70%] rounded-lg shadow-sm text-[15px] leading-relaxed flex flex-col ${isMe ? 'bg-[#d9fdd3] rounded-tr-none' : 'bg-white rounded-tl-none'}`}>
                        
                        <div className="p-2 pb-6">
                            {!isMe && <div className="text-xs font-semibold text-[#1f8753] mb-1 px-1">{m.user}</div>}
                            
                            <div className="mb-1 px-1 text-[#111b21]">
                            {m.mediaUrl ? (
                                m.mediaType?.startsWith('image/') ? (
                                <img src={m.mediaUrl} alt="shared" className="max-w-xs rounded border border-gray-200" />
                                ) : m.mediaType?.startsWith('video/') ? (
                                <video src={m.mediaUrl} controls className="max-w-sm rounded" />
                                ) : m.mediaType?.startsWith('audio/') ? (
                                <audio src={m.mediaUrl} controls className="w-64 mt-1" />
                                ) : (
                                <a href={m.mediaUrl} download={m.fileName} className="text-blue-600 underline text-sm break-all flex items-center gap-1">
                                    <Paperclip className="w-4 h-4" /> {m.fileName}
                                </a>
                                )
                            ) : (
                                <span>{m.text}</span>
                            )}
                            </div>
                            
                            <span className="absolute bottom-1 right-2 text-[10px] text-gray-500 font-medium">{m.time}</span>
                        </div>

                        {isSuspicious && (
                            <div className={`mt-0 px-3 py-2 border-t rounded-b-lg flex flex-col gap-1 ${alertColor}`}>
                                <div className="flex items-center gap-1 font-bold text-xs uppercase">
                                    {isPending ? (
                                      <><Activity className="w-4 h-4 animate-pulse" /> Edge AI Flagged (Verifying...)</>
                                    ) : (
                                      <><AlertTriangle className="w-4 h-4" /> Cloud AI Report ({m.alert})</>
                                    )}
                                </div>
                                <div className="text-xs leading-snug">
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
              <div className="bg-[#f0f2f5] p-3 flex items-center gap-3 z-10 border-t border-gray-200">
                <Smile className="w-6 h-6 text-[#54656f] cursor-pointer" />
                <button onClick={() => fileInputRef.current.click()} disabled={isScanningMedia}>
                  <Paperclip className={`w-6 h-6 ${isScanningMedia ? 'text-gray-300' : 'text-[#54656f] hover:text-gray-800'} cursor-pointer`} />
                </button>
                <input 
                  type="text" 
                  value={messageInput}
                  onChange={e => setMessageInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  placeholder="Type a message" 
                  disabled={isScanningMedia}
                  className="flex-1 py-[9px] px-4 rounded-lg outline-none text-[15px] bg-white border-none shadow-sm"
                />
                <button onClick={sendMessage} disabled={isScanningMedia} className="p-2 hover:bg-gray-200 rounded-full transition-colors">
                  {messageInput.trim() ? <Send className="w-6 h-6 text-[#54656f]" /> : <Mic className="w-6 h-6 text-[#54656f]" />}
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 z-10 bg-[#f0f2f5]">
              <div className="w-72 mb-6 opacity-60">
                <svg viewBox="0 0 100 100" className="w-full h-full fill-current text-gray-300"><path d="M50 0a50 50 0 100 100A50 50 0 0050 0zm0 90A40 40 0 1150 10a40 40 0 010 80z"/><path d="M70 30H30a5 5 0 00-5 5v30a5 5 0 005 5h40a5 5 0 005-5V35a5 5 0 00-5-5z"/></svg>
              </div>
              <h2 className="text-[32px] font-light text-[#41525d] mb-4">ScamShield Web</h2>
              <p className="text-[14px] text-[#667781] text-center max-w-md leading-relaxed">
                Send and receive messages with military-grade Edge AI protection. <br/>
                Your chats are monitored locally before ever leaving your device.
              </p>
              <div className="mt-8 flex items-center gap-2 text-[13px] text-[#8696a0]">
                <ShieldCheck className="w-4 h-4" /> End-to-end Scam Protected
              </div>
            </div>
          )}

          {/* WebRTC Call Overlay */}
          {(receivingCall || callAccepted) && !callEnded && (
            <div className="absolute inset-0 bg-[#0b141a] z-40 flex flex-col">
              <div className="p-6 flex justify-between items-center bg-gradient-to-b from-black/50 to-transparent absolute top-0 w-full z-10">
                <div className="text-white text-lg flex items-center gap-2 font-medium">
                  <ShieldCheck className="w-5 h-5 text-[#00a884]" /> End-to-end encrypted
                </div>
              </div>
              
              <div className="flex-1 relative flex items-center justify-center">
                {callAccepted ? (
                  <video 
                    playsInline 
                    ref={userVideo} 
                    autoPlay 
                    className={`w-full h-full object-cover ${callType === 'audio' ? 'hidden' : 'block'}`} 
                  />
                ) : (
                  <div className="text-white text-center flex flex-col items-center">
                    <div className="w-24 h-24 bg-gray-600 rounded-full mb-4 flex items-center justify-center text-4xl shadow-lg">U</div>
                    <h2 className="text-[28px] font-light mb-1">Incoming {callType} call...</h2>
                    <p className="text-gray-400">User {caller.substring(0,4)}</p>
                  </div>
                )}
                
                {callType === 'audio' && callAccepted && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900">
                     <div className="w-32 h-32 bg-gray-700 rounded-full mb-6 flex items-center justify-center text-6xl shadow-2xl text-white font-bold">U</div>
                     <div className="text-2xl text-white mb-2">User {activeChat.substring(0,4)}</div>
                     <div className="text-green-400 flex items-center gap-2"><div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div> 00:00</div>
                  </div>
                )}

                <video 
                  playsInline 
                  muted 
                  ref={myVideo} 
                  autoPlay 
                  className={`absolute top-6 right-6 w-36 h-52 bg-gray-900 object-cover rounded-xl border-2 border-gray-600 shadow-2xl ${callType === 'audio' ? 'hidden' : 'block'}`} 
                />
              </div>

              <div className="h-28 bg-gradient-to-t from-black/90 to-transparent flex items-center justify-center gap-8 pb-4 absolute bottom-0 w-full">
                {!callAccepted && receivingCall && (
                  <button onClick={answerCall} className="w-14 h-14 bg-[#25D366] rounded-full flex items-center justify-center shadow-lg hover:bg-[#20bd5a] transition animate-bounce">
                    <Phone className="w-6 h-6 text-white" />
                  </button>
                )}
                {callType === 'video' && <button className="w-12 h-12 bg-gray-700/80 rounded-full flex items-center justify-center hover:bg-gray-600 text-white backdrop-blur-sm"><VideoOff className="w-5 h-5" /></button>}
                <button className="w-12 h-12 bg-gray-700/80 rounded-full flex items-center justify-center hover:bg-gray-600 text-white backdrop-blur-sm"><MicOff className="w-5 h-5" /></button>
                <button onClick={leaveCall} className="w-14 h-14 bg-[#ef4444] rounded-full flex items-center justify-center shadow-lg hover:bg-[#dc2626] text-white transition">
                  <PhoneOff className="w-6 h-6" />
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

