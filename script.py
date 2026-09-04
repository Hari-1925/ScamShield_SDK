import sys

with open('app/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

logic = "".join(lines[:467])

new_jsx = """  return (
    <div className="flex h-screen bg-[#09090b] text-gray-100 font-sans overflow-hidden selection:bg-indigo-500/30">
      {/* BACKGROUND EFFECTS */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="flex w-full h-full max-w-[1600px] mx-auto bg-black/40 backdrop-blur-xl border border-white/5 shadow-2xl relative z-10">
        
        {/* LEFT PANE */}
        <div className="w-full md:w-[380px] flex flex-col bg-white/5 border-r border-white/10 backdrop-blur-md relative z-20">
          {/* Header */}
          <div className="h-[72px] flex items-center justify-between px-5 border-b border-white/10 bg-black/20">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(99,102,241,0.4)]">
                {name.charAt(0).toUpperCase()}
              </div>
              <div className="font-semibold text-gray-100 tracking-wide">{name}</div>
            </div>
            <div className="flex gap-4 text-gray-400">
              <Activity className="w-5 h-5 hover:text-indigo-400 cursor-pointer transition-colors" />
              <MoreVertical className="w-5 h-5 hover:text-indigo-400 cursor-pointer transition-colors" />
            </div>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-white/10 bg-black/10">
            <div className="bg-black/40 flex items-center rounded-xl px-4 py-2.5 border border-white/5 focus-within:border-indigo-500/50 transition-all shadow-inner">
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
                className={`flex items-center gap-4 px-5 py-4 cursor-pointer transition-all duration-300 border-l-2 ${activeChat === u ? 'bg-indigo-500/10 border-indigo-500' : 'hover:bg-white/5 border-transparent'}`}
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
        <div className="hidden md:flex flex-1 flex-col relative bg-black/20">
          
          {/* TOP SCAM ALERT OVERLAY (Z-50) */}
          {callAlert && (
            <div className="absolute top-24 left-1/2 transform -translate-x-1/2 z-50 w-[85%] max-w-xl animate-in slide-in-from-top-4 fade-in duration-300">
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
                <div className="bg-red-950/80 border border-red-500/50 backdrop-blur-2xl text-red-100 p-5 rounded-2xl shadow-[0_0_40px_rgba(220,38,38,0.3)]">
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
              <div className="h-[72px] bg-white/5 backdrop-blur-md flex items-center justify-between px-6 z-10 border-b border-white/10 shadow-lg">
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
                  <button onClick={() => initiateCall(activeChat, 'video')} className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-300 hover:text-indigo-400 transition-all border border-white/5"><Video className="w-5 h-5" /></button>
                  <button onClick={() => initiateCall(activeChat, 'audio')} className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-300 hover:text-indigo-400 transition-all border border-white/5"><Phone className="w-5 h-5" /></button>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4 z-0 relative">
                <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '20px 20px'}}></div>

                {messages.map((m, i) => {
                  const isMe = m.user === name;
                  const isSuspicious = m.isMalicious && !isMe;
                  const isPending = m.isPending;
                  
                  return (
                    <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'} mb-2 relative z-10 animate-in slide-in-from-bottom-2 fade-in duration-300`}>
                      <div className={`relative max-w-[75%] rounded-2xl text-[15px] leading-relaxed flex flex-col shadow-xl ${isMe ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-sm' : 'bg-[#2a2a2e] text-gray-200 rounded-bl-sm border border-white/5'}`}>
                        
                        <div className="p-3.5 pb-7">
                            {!isMe && <div className="text-[11px] font-bold text-indigo-300 mb-1.5 px-1 uppercase tracking-wider">{m.user}</div>}
                            
                            <div className="px-1">
                            {m.mediaUrl ? (
                                m.mediaType?.startsWith('image/') ? (
                                <img src={m.mediaUrl} alt="shared" className="max-w-xs rounded-xl border border-white/10 shadow-md" />
                                ) : m.mediaType?.startsWith('video/') ? (
                                <video src={m.mediaUrl} controls className="max-w-sm rounded-xl border border-white/10 shadow-md" />
                                ) : m.mediaType?.startsWith('audio/') ? (
                                <audio src={m.mediaUrl} controls className="w-64 mt-1 opacity-90" />
                                ) : (
                                <a href={m.mediaUrl} download={m.fileName} className="text-indigo-300 hover:text-indigo-200 underline text-sm break-all flex items-center gap-2 bg-black/20 p-3 rounded-xl">
                                    <Paperclip className="w-4 h-4" /> {m.fileName}
                                </a>
                                )
                            ) : (
                                <span>{m.text}</span>
                            )}
                            </div>
                            
                            <span className={`absolute bottom-2 right-3 text-[10px] font-medium ${isMe ? 'text-indigo-200/70' : 'text-gray-500'}`}>{m.time}</span>
                        </div>

                        {/* Scam Alert Bubble Append */}
                        {isSuspicious && (
                            <div className="mt-0 px-4 py-3 bg-red-950/90 border-t border-red-500/30 rounded-b-2xl rounded-bl-sm flex flex-col gap-1.5 shadow-[0_-5px_15px_rgba(220,38,38,0.1)]">
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
              <div className="bg-white/5 backdrop-blur-xl p-4 flex items-center gap-4 z-10 border-t border-white/10">
                <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-indigo-400">
                  <Smile className="w-6 h-6" />
                </button>
                <button onClick={() => fileInputRef.current.click()} disabled={isScanningMedia} className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-indigo-400 disabled:opacity-50">
                  <Paperclip className="w-5 h-5" />
                </button>
                
                <div className="flex-1 bg-black/40 border border-white/10 rounded-full flex items-center px-2 py-1 focus-within:border-indigo-500/50 focus-within:bg-black/60 transition-all shadow-inner">
                  <input 
                    type="text" 
                    value={messageInput}
                    onChange={e => setMessageInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="Type a message..." 
                    disabled={isScanningMedia}
                    className="flex-1 bg-transparent py-2.5 px-4 outline-none text-[15px] text-gray-200 placeholder-gray-600"
                  />
                  <button 
                    onClick={sendMessage} 
                    disabled={isScanningMedia || !messageInput.trim()} 
                    className="w-10 h-10 bg-indigo-600 hover:bg-indigo-500 rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:bg-gray-800 shadow-[0_0_15px_rgba(79,70,229,0.4)]"
                  >
                    <Send className="w-4 h-4 text-white ml-1" />
                  </button>
                </div>
                
                {!messageInput.trim() && (
                  <button className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors text-gray-400 hover:text-indigo-400">
                    <Mic className="w-5 h-5" />
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 z-10 bg-black/20">
              <div className="relative w-32 h-32 mb-8">
                <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-2xl animate-pulse"></div>
                <div className="w-full h-full bg-black/50 border border-white/10 backdrop-blur-xl rounded-full flex items-center justify-center shadow-2xl relative z-10">
                  <ShieldAlert className="w-12 h-12 text-indigo-400" />
                </div>
              </div>
              <h2 className="text-3xl font-light text-gray-200 mb-4 tracking-wide">ScamShield <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Edge</span></h2>
              <p className="text-sm text-gray-400 text-center max-w-md leading-relaxed px-6">
                Send and receive messages with military-grade Edge AI protection. <br/>
                Your chats are monitored locally before ever leaving your device.
              </p>
              <div className="mt-8 flex items-center gap-2 text-xs text-indigo-400/60 uppercase tracking-widest font-bold bg-indigo-500/10 px-4 py-2 rounded-full border border-indigo-500/20">
                <ShieldCheck className="w-4 h-4" /> End-to-end Protected
              </div>
            </div>
          )}

          {/* WebRTC Call Overlay (Glassmorphism HUD) */}
          {(receivingCall || callAccepted) && !callEnded && (
            <div className="absolute inset-0 z-40 flex flex-col bg-black/80 backdrop-blur-2xl animate-in zoom-in-95 fade-in duration-300 overflow-hidden">
              
              {/* Ambient Call Background Glow */}
              <div className="absolute inset-0 bg-gradient-to-b from-indigo-900/20 via-transparent to-black pointer-events-none" />
              
              <div className="p-6 flex justify-between items-center relative z-10">
                <div className="text-indigo-200 text-sm flex items-center gap-2 font-bold uppercase tracking-widest bg-white/5 px-4 py-2 rounded-full border border-white/10">
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
"""

with open("app/frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(logic + new_jsx)
