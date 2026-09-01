const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    },
    maxHttpBufferSize: 5e7 // 50 MB limit
});

let connectedUsers = {};

io.on('connection', (socket) => {
    console.log('User connected:', socket.id);
    connectedUsers[socket.id] = socket.id;

    io.emit('update-users', Object.keys(connectedUsers));

    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
        delete connectedUsers[socket.id];
        io.emit('update-users', Object.keys(connectedUsers));
    });

    socket.on('send-message', (data) => {
        console.log('Message received. Type:', data.mediaType ? data.mediaType : 'text');
        io.emit('receive-message', data);
    });

    socket.on('update-message', (data) => {
        console.log('Message report updated:', data.id);
        io.emit('message-updated', data);
    });

    socket.on('call-user', (data) => {
        io.to(data.userToCall).emit('call-made', { offer: data.offer, socket: socket.id });
    });

    socket.on('make-answer', (data) => {
        io.to(data.to).emit('answer-made', { socket: socket.id, answer: data.answer });
    });

    socket.on('ice-candidate', (data) => {
        io.to(data.to).emit('ice-candidate', { socket: socket.id, candidate: data.candidate });
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Backend Signaling Server running on port ${PORT}`);
});
