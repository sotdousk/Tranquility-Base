document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const nodesContainer = document.getElementById("nodes-container");

    // Receive updates from the server
    socket.on("update_node", (data) => {
        console.log("Received WebSocket data:", data);

        for (const [nodeName, nodeData] of Object.entries(data)) {
            if (nodeName === "Intrusion_detected") continue;

            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            const thermalsData = nodeData.sensors ? nodeData.sensors.thermals : null; // Retrieve thermals data

            if (nodeCard) {
                // Update existing node card
                nodeCard.querySelector(".temperature").textContent = `Temperature: ${parseFloat(thermalsData.temperature.toFixed(2)) || "N/A"}`;
                nodeCard.querySelector(".humidity").textContent = `Humidity: ${thermalsData.humidity || "N/A"}`;

            } else {
                // Create a new card for the node
                const newCard = document.createElement("div");
                newCard.classList.add("node-card");
                newCard.id = `node-card-${nodeName}`;
                newCard.innerHTML = `
                    <h2>${nodeName}</h2>
                    <p class="temperature">Door: ${thermalsData.temperature || "N/A"}</p>
                    <p class="humidity">Motion: ${thermalsData.humidity || "N/A"}</p>
                `;
                nodesContainer.appendChild(newCard);
            }
        }
    });

});
