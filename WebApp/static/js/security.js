document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const nodesContainer = document.getElementById("nodes-container");
    if (!nodesContainer) {
        console.error("Error: #nodes-container element not found in the DOM.");
        return;
    }

    socket.on("update_node", (data) => {
        console.log("Received WebSocket data:", data);

        for (const [nodeName, nodeData] of Object.entries(data)) {
            if (nodeName === "Intrusion_detected") {
                // Skip the "Intrusion_detected" key
                continue;
            }

            if (!nodeData.sensors || !nodeData.sensors.security) {
                console.warn(`Node ${nodeName} is missing security sensor data.`);
                continue;
            }

            const securityData = nodeData.sensors.security;
            console.log(`Node ${nodeName} has security sensor data ${securityData.door}.`);

            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            console.log(`Node ${nodeName} has card ${nodeCard}.`);
            if (nodeCard) {
                // Update existing node card
                nodeCard.querySelector(".door").textContent = `Door: ${securityData.door || "N/A"}`;
                nodeCard.querySelector(".motion").textContent = `PIR: ${securityData.motion || "N/A"}`;
                nodeCard.querySelector(".status").textContent = nodeData.on_alert
                    ? "Status: Active."
                    : "Status: On Standby.";
            } else {
                // Create a new card for the node
                const newCard = document.createElement("div");
                newCard.classList.add("node-card");
                newCard.id = `node-card-${nodeName}`;
                newCard.innerHTML = `
                    <h2>${nodeName}</h2>
                    <p class="door">Door: ${securityData.door || "N/A"}</p>
                    <p class="pir">PIR: ${securityData.motion || "N/A"}</p>
                    <p class="status">${nodeData.on_alert ? "Status: Active." : "Status: On Standby."}</p>
                `;
                nodesContainer.appendChild(newCard);
            }
        }
    });
});
