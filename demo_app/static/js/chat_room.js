// Create a new WebSocket connection to the server
const ws = new WebSocket("ws://127.0.0.1:8000/myws");

// Listen for connection open event
ws.onopen = function() {
    console.log("WebSocket connection opened");
};

// Listen for messages from the server
ws.onmessage = function(event) {
    console.log("Message from server:", event.data);
    const messagesList = document.getElementById("messages");
    const newMessage = document.createElement("li");
    newMessage.textContent = event.data;
    messagesList.appendChild(newMessage);
};

// Listen for WebSocket errors
ws.onerror = function(error) {
    console.log("WebSocket error:", error);
};

// Listen for WebSocket close event
ws.onclose = function() {
    console.log("WebSocket connection closed");
};

// Send message when the button is clicked or Enter is pressed
document.getElementById("sendButton").addEventListener("click", sendMessage);
document.getElementById("messageInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

function sendMessage() {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value;
    if (message) {
        ws.send(message);
        messageInput.value = '';  // Clear input field after sending
    }
}