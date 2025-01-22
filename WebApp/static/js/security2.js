document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const nodesContainer = document.getElementById("nodes-container");
    const intrusionMessageContainer = document.getElementById("intrusion-message-container");
    const resetButton = document.getElementById("reset-intrusion-button");

    if (!nodesContainer || !intrusionMessageContainer || !resetButton) {
        console.error("Error:Required elements not found in the DOM.");
        return;
    }

    // Handle individual node switches
    nodesContainer.addEventListener("change", (event) => {
        // Check if the event target is a custom toggle switch
        if (event.target.classList.contains("custom-toggle")) {
            const nodeName = event.target.id.replace("toggle-", ""); // Extract node name from the ID
            const isOn = event.target.checked; // Determine the toggle state (checked or not)

            // Emit an update for the specific node through Socket.IO
            socket.emit("toggle_node", { node: nodeName, on_alert: isOn });

            // Immediately update the status field in the UI
            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            if (nodeCard) {
                const statusField = nodeCard.querySelector(".status");
                if (statusField) {
                    statusField.textContent = isOn ? "Status: Active." : "Status: On Standby.";

                    // Add visual feedback (e.g., color change) to the status field
                    statusField.style.color = isOn ? "green" : "gray";
                }
            } else {
                console.warn(`Node card with ID 'node-card-${nodeName}' not found.`);
            }
        }
    });


    // Handle reset button click
    resetButton.addEventListener("click", () => {
        console.log("Reset button clicked!");

        fetch("/reset_intrusion", {method: "POST"})
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to reset intrusion alarm.");
            }
            return response.json();
        })
        .then(data => {
            console.log("Intrusion reset successful:", data);

            // Clear the intrusion message
            intrusionMessageContainer.textContent = "No intrusion detected.";
            intrusionMessageContainer.classList.remove("alert-danger");
            intrusionMessageContainer.classList.add("alert-success");
        })
        .catch(error => {
            console.error("Error resetting intrusion:", error);
        });
    });

    // Receive updates from the server
    socket.on("update_node", (data) => {
        console.log("Received WebSocket data:", data);

        // Update intrusion message
        if (data.Intrusion_detected) {
            const { status, nodes_detected } = data.Intrusion_detected;

            if (status) {
                intrusionMessageContainer.textContent = `Intrusion detected in nodes: ${nodes_detected.join(", ")}`;
                intrusionMessageContainer.classList.remove("alert-success");
                intrusionMessageContainer.classList.add("alert-danger");
            } else {
                intrusionMessageContainer.textContent = "No intrusion detected.";
                intrusionMessageContainer.classList.remove("alert-danger");
                intrusionMessageContainer.classList.add("alert-success");
            }
        }

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
        // Update intrusion message
        if (data.Intrusion_detected && data.Intrusion_detected.status) {
            const nodes = data.Intrusion_detected.nodes_detected.join(", ");
            intrusionMessageContainer.textContent = `Intrusion detected in nodes: ${nodes}`;
            intrusionMessageContainer.classList.add("alert", "alert-danger");
        }
    });

});
