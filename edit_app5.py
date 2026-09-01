with open('app/frontend/src/App.jsx.bak', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
code = code.replace(
    \"import React, { useState, useEffect, useRef } from 'react';\",
    \"import React, { useState, useEffect, useRef } from 'react';\\nimport EmojiPicker from 'emoji-picker-react';\"
)

# 2. Add Voice / Emoji States
states_str = \"\"\"
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const voiceRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
\"\"\"
code = code.replace(\"const [aiStatus, setAiStatus] = useState('loading');\", \"const [aiStatus, setAiStatus] = useState('loading');\" + states_str)

# 3. Add Voice Recording Functions BEFORE handleFileUpload
voice_fns = \"\"\"
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const file = new File([audioBlob], 'voice_note.webm', { type: 'audio/webm' });
        uploadFileAndSend(file);
        stream.getTracks().forEach(track => track.stop());
      };
      recorder.start();
      voiceRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (e) {
      console.error(e);
      alert("Microphone permission denied.");
    }
  };

  const stopVoiceRecording = () => {
    if (voiceRecorderRef.current && isRecording) {
      voiceRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const uploadFileAndSend = async (file) => {
      if (!file) return;
      if (file.size > 20 * 1024 * 1024) {
        alert("File is too large for this demo (Max 20MB).");
        return;
      }
  
      setIsScanningMedia(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('contact_id', activeChat);
      const msgId = generateId();
  
      try {
        const res = await axios.post(\\/scan_local_media\, formData);
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
            axios.post(\\/scan_cloud\, {
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
                  explanation: report.explanation || 'Cloud verification completed.',
                  scamType: report.scam_type
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
  };
\"\"\"
code = code.replace(\"const handleFileUpload = async (e) => {\", voice_fns + \"\\n  const handleFileUpload = async (e) => {\\n    const file = e.target.files[0];\\n    if(file) uploadFileAndSend(file);\\n    e.target.value = '';\\n    return;\\n\\n  /*\")
code = code.replace(\"reader.readAsDataURL(file);\\n      } catch (err) {\\n        console.error(\\\"Local Agent Error:\\\", err);\\n        alert(\\\"Local Security Agent is offline.\\\");\\n      }\\n    };\", \"*/\\n    };\")

# 4. Input Area (Emoji / Mic)
import re
input_replacement = \"\"\"
              {/* Chat Input */}
              <div className="bg-[#202c33] p-3 flex items-center gap-3 z-10 border-t border-[#313d45] relative">
                <div className="relative">
                  <Smile className="w-6 h-6 text-[#8696a0] cursor-pointer hover:text-[#d1d7db]" onClick={() => setShowEmojiPicker(!showEmojiPicker)} />
                  {showEmojiPicker && (
                    <div className="absolute bottom-14 left-0 z-50 shadow-2xl">
                      <EmojiPicker onEmojiClick={(e) => { setMessageInput(prev => prev + e.emoji); setShowEmojiPicker(false); }} theme="dark" />
                    </div>
                  )}
                </div>
                <button onClick={() => fileInputRef.current.click()} disabled={isScanningMedia || isRecording}>
                  <Paperclip className={w-6 h-6  cursor-pointer} />
                </button>
                <input 
                  type="text" 
                  value={messageInput}
                  onChange={e => setMessageInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  placeholder={isRecording ? "Recording voice note... (Click Mic to stop)" : "Type a message"} 
                  disabled={isScanningMedia || isRecording}
                  className="flex-1 py-[9px] px-4 rounded-lg outline-none text-[15px] bg-[#2a3942] text-[#d1d7db] placeholder-[#8696a0] border-none shadow-sm"
                />
                <button 
                  onClick={() => {
                      if (messageInput.trim()) sendMessage();
                      else if (isRecording) stopVoiceRecording();
                      else startVoiceRecording();
                  }} 
                  disabled={isScanningMedia} 
                  className={p-2 rounded-full transition-colors }
                >
                  {messageInput.trim() ? <Send className="w-6 h-6 text-[#8696a0]" /> : <Mic className={w-6 h-6 } />}
                </button>
              </div>
\"\"\"
code = re.sub(r'\{\/\* Chat Input \*\/\}.*?<\/button>\s*<\/div>', input_replacement, code, flags=re.DOTALL)

# 5. Apply Dark Theme + Green Accents

# Body wrapper
code = code.replace(\"bg-white md:shadow-lg md:rounded-lg overflow-hidden\", \"bg-[#111b21] md:shadow-lg md:rounded-lg overflow-hidden text-[#e9edef]\")

# Left Pane
code = code.replace(\"bg-[#f0f2f5] flex items-center justify-between px-4\", \"bg-[#202c33] flex items-center justify-between px-4\") # Header
code = code.replace(\"border-r border-gray-200 flex flex-col bg-white\", \"border-r border-[#313d45] flex flex-col bg-[#111b21]\")
code = code.replace(\"text-gray-800\", \"text-[#e9edef]\")
code = code.replace(\"text-gray-600\", \"text-[#d1d7db]\")
code = code.replace(\"border-b border-gray-100\", \"border-b border-[#313d45]\")
code = code.replace(\"p-2 bg-white border-b\", \"p-2 bg-[#111b21] border-b\")
code = code.replace(\"bg-[#f0f2f5] flex items-center rounded-lg\", \"bg-[#202c33] flex items-center rounded-lg\") # Search box
code = code.replace(\"text-gray-500\", \"text-[#8696a0]\")
code = code.replace(\"text-gray-700\", \"text-[#d1d7db]\")
code = code.replace(\"hover:bg-[#f5f6f6]\", \"hover:bg-[#202c33]\")
code = code.replace(\"bg-[#f0f2f5]' : ''\", \"bg-[#2a3942]' : ''\")
code = code.replace(\"bg-blue-100 rounded-full flex items-center justify-center text-blue-600\", \"bg-[#005c4b] rounded-full flex items-center justify-center text-[#e9edef]\")
code = code.replace(\"text-[#111b21] font-normal\", \"text-[#e9edef] font-normal\")

# Chat Pane
code = code.replace(\"bg-[#efeae2]\", \"bg-[#0b141a]\")
code = code.replace(\"bg-white rounded-lg p-6 shadow max-w-sm\", \"bg-[#202c33] rounded-lg p-6 shadow max-w-sm text-[#e9edef]\")
code = code.replace(\"border border-gray-300\", \"border border-[#313d45] bg-[#2a3942] text-[#d1d7db]\")

# Bubbles
code = code.replace(\"bg-[#d9fdd3]\", \"bg-[#005c4b]\")
code = code.replace(\"bg-white rounded-tl-none\", \"bg-[#202c33] rounded-tl-none\")
code = code.replace(\"text-[#111b21]\", \"text-[#e9edef]\")

# Landing
code = code.replace(\"text-[#41525d]\", \"text-[#e9edef]\")
code = code.replace(\"text-[#667781]\", \"text-[#8696a0]\")
code = code.replace(\"z-10 bg-[#f0f2f5]\", \"z-10 bg-[#202c33]\")

with open('app/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Injected perfectly!")
