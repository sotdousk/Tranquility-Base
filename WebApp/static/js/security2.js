document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const nodesContainer = document.getElementById("nodes-container");

    if (!nodesContainer) {
        console.error("Error: #nodes-container element not found in the DOM.");
        return;
    }

    // Handle individual node switches
    nodesContainer.addEventListener("change", (event) => {
        if (event.target.classList.contains("toggle-node")) {
            const nodeName = event.target.id.replace("toggle-", "");
            const isOn = event.target.checked;
            console.log(`Toggle switched for ${nodeName}: ${isOn}`);

            // Emit update for the specific node
            socket.emit("toggle_node", { node: nodeName, on_alert: isOn });

            // Update the status field immediately in the view
            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            if (nodeCard) {
                const statusField = nodeCard.querySelector(".status");
                statusField.textContent = isOn ? "Status: Active." : "Status: On Standby.";
            }

        }
    });

    // Receive updates from the server
    socket.on("update_node", (data) => {
        console.log("Received WebSocket data:", data);

        for (const [nodeName, nodeData] of Object.entries(data)) {
            if (nodeName === "Intrusion_detected") continue;

            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            const securityData = nodeData.sensors ? nodeData.sensors.security : null; // Retrieve security data

            if (nodeCard) {
                // Update existing node card
                nodeCard.querySelector(".door").textContent = `Door: ${securityData.door || "N/A"}`;
                nodeCard.querySelector(".motion").textContent = `Motion: ${securityData.motion || "N/A"}`;

            } else {
                // Create a new card for the node
                const newCard = document.createElement("div");
                newCard.classList.add("node-card");
                newCard.id = `node-card-${nodeName}`;
                newCard.innerHTML = `
                    <h2>${nodeName}</h2>
                    <p class="door">Door: ${securityData.door || "N/A"}</p>
                    <p class="motion">Motion: ${securityData.motion || "N/A"}</p>
                    <p class="status">Status: ${nodeData.on_alert ? "Active" : "On Standby"}</p>
                `;
                nodesContainer.appendChild(newCard);
            }
        }

    });

});
