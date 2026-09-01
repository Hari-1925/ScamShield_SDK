import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { Shield, ShieldAlert, Video, Mic, Send, Paperclip } from 'lucide-react';
import { scamShield } from './sdk/ScamShield';

const SOCKET_URL = 'http://localhost:5000';

type Message = {
  id: string;
  sender: string;
  text: string;
  isScam?: boolean;
  alertLevel?: string;
  explanation?: string;
};

export default function App() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [inCall, setInCall] = useState(false);
  const [sdkReady, setSdkReady] = useState(false);
  const localVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Initialize Local JS Edge AI natively inside the React App!
    scamShield.init().then(() => setSdkReady(true));

    const s = io(SOCKET_URL);
    setSocket(s);
    
    s.on('receive-message', (msg: Message) => {
      setMessages((prev) => [...prev, msg]);
    });

    s.emit('join-room', 'global-room');

    return () => {
      s.disconnect();
    };
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !socket) return;

    // Use Native Local Edge AI inside the APK!
    let isScam = false;
    let alertLevel = 'none';
    let explanation = '';

    if (sdkReady) {
      try {
        const res = await scamShield.scanText(input);
        if (res.alert_level !== 'none') {
          isScam = true;
          alertLevel = res.alert_level;
          explanation = res.explanation;
        }
      } catch (e) {
        console.error('Local Edge AI Error:', e);
      }
    }

    const msg: Message = {
      id: Math.random().toString(36).substr(2, 9),
      sender: 'Me',
      text: input,
      isScam,
      alertLevel,
      explanation
    };

    setMessages((prev) => [...prev, msg]);
    socket.emit('send-message', { ...msg, roomId: 'global-room', sender: 'Them' });
    setInput('');
  };

  const startCall = async (video: boolean) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video, audio: true });
      if (localVideoRef.current && video) {
        localVideoRef.current.srcObject = stream;
      }
      setInCall(true);
      // Native WebRTC call connection logic goes here
    } catch (e) {
      console.error('Media access error:', e);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto bg-white shadow-xl relative">
        {!sdkReady && (
          <div className="absolute top-16 left-0 right-0 bg-yellow-100 text-yellow-800 text-center py-1 text-sm font-semibold">
            Downloading AI Models (80MB) into local storage...
          </div>
        )}
        {/* Header */}
        <header className="bg-indigo-600 text-white p-4 flex justify-between items-center z-10">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6" />
            <h1 className="text-xl font-bold">ScamShield Native</h1>
          </div>
          <div className="flex gap-4">
            <button onClick={() => startCall(false)} className="p-2 bg-indigo-500 rounded hover:bg-indigo-700 transition"><Mic className="w-5 h-5" /></button>
            <button onClick={() => startCall(true)} className="p-2 bg-indigo-500 rounded hover:bg-indigo-700 transition"><Video className="w-5 h-5" /></button>
          </div>
        </header>

        {/* Video Area (if in call) */}
        {inCall && (
          <div className="bg-black h-64 relative">
            <video ref={localVideoRef} autoPlay muted className="w-full h-full object-cover" />
            <button onClick={() => setInCall(false)} className="absolute bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded">End Call</button>
          </div>
        )}

        {/* Chat Feed */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={\lex flex-col \\}>
              <div className={\max-w-[70%] p-3 rounded-lg \\}>
                <p>{m.text}</p>
              </div>
              {m.isScam && (
                <div className="mt-1 flex items-start gap-2 bg-red-50 text-red-700 p-2 rounded max-w-[80%] border border-red-200">
                  <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <strong>Local AI Alert ({m.alertLevel}):</strong> {m.explanation}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Input Area */}
        <footer className="p-4 bg-gray-50 border-t flex gap-2">
          <button className="p-3 text-gray-500 hover:bg-gray-200 rounded-full transition"><Paperclip className="w-5 h-5" /></button>
          <input
            type="text"
            className="flex-1 p-3 border rounded-full focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            placeholder={sdkReady ? "Type a message..." : "Loading AI..."}
            value={input}
            disabled={!sdkReady}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend} disabled={!sdkReady} className="p-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition disabled:opacity-50"><Send className="w-5 h-5" /></button>
        </footer>
      </div>
    </div>
  );
}
