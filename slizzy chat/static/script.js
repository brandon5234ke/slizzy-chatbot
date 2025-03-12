// Add event listener to handle keypress on the input field
function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage(); // Trigger sendMessage when Enter is pressed
    }
}

function displayMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "message " + sender;
    messageDiv.textContent = text;
    document.getElementById("messages").appendChild(messageDiv);
    document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
}

function sendMessage() {
    const inputField = document.getElementById("user-input");
    const message = inputField.value;
    if (message.trim() === "") return; // Avoid sending empty messages

    displayMessage(message, "user");
    inputField.value = ""; // Clear the input field after sending

    // Fetch request to communicate with the backend
    fetch("http://127.0.0.1:5000/chat", {
        method: "POST", // Ensure this is 'POST'
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message }) // Send message as JSON
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => displayMessage(data.response, "bot")) // Display bot response
    .catch(error => {
        console.error("Network error:", error);
        alert("Failed to connect to the server. Please try again later.");
    });
}

// Attach the handleKeyPress function to the input field
document.getElementById("user-input").addEventListener("keypress", handleKeyPress);

// Optional: Attach sendMessage to the button click for redundancy
document.getElementById("btn").addEventListener("click", sendMessage);
