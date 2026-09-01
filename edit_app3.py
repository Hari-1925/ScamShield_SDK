import re

with open('app/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

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

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if(file) uploadFileAndSend(file);
    e.target.value = '';
  };
\"\"\"

# Find where const handleFileUpload = async (e) => { is and replace it up to the next const sendMessage = async () => {
code = re.sub(r'const handleFileUpload = async \(e\) => \{.*?const sendMessage = async \(\) => \{', voice_fns + '\\n\\n  const sendMessage = async () => {', code, flags=re.DOTALL)

with open('app/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Injected Voice functions!")
