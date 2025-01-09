document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const resetButton = document.getElementById("reset-intrusion");

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            console.log("Reset intrusion button clicked.");
            socket.emit("reset_intrusion");
        });
    }

    const nodesContainer = document.getElementById("nodes-container");
    const toggleAllSwitch = document.getElementById("toggle-all");

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

            // Save the updated status locally
            saveNodeStatusLocally(nodeName, isOn);

            // Update global switch state
            updateGlobalSwitchState();
        }
    });

    // Handle global toggle switch
    if (toggleAllSwitch) {
        toggleAllSwitch.addEventListener("change", (event) => {
            const enableAll = event.target.checked;
            console.log("Global toggle switched:", enableAll);

            // Emit update for all nodes
            socket.emit("toggle_all", { on_alert: enableAll });

            // Update all individual switches and their status fields
            document.querySelectorAll(".toggle-node").forEach((toggle) => {
                toggle.checked = enableAll;

                const nodeName = toggle.id.replace("toggle-", "");
                const nodeCard = document.getElementById(`node-card-${nodeName}`);
                if (nodeCard) {
                    const statusField = nodeCard.querySelector(".status");
                    statusField.textContent = enableAll ? "Status: Active." : "Status: On Standby.";
                }
            });

            // Save the updated global status locally
            saveGlobalStatusLocally(enableAll);
        });
    }

    // Update global switch state dynamically
    function updateGlobalSwitchState() {
        const totalNodes = document.querySelectorAll(".toggle-node").length;
        const activeNodes = document.querySelectorAll(".toggle-node:checked").length;

        toggleAllSwitch.checked = totalNodes === activeNodes;
    }

    // Save the updated status locally
    function saveNodeStatusLocally(nodeName, isOn) {
        fetch("/api/save_node_status", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ node: nodeName, on_alert: isOn })
        })
            .then((response) => {
                if (!response.ok) {
                    console.error(`Failed to save status for ${nodeName}`);
                }
            })
            .catch((error) => {
                console.error(`Error saving status for ${nodeName}:`, error);
            });
    }

    // Save the updated status of all nodes locally
    function saveGlobalStatusLocally(enableAll) {
        fetch("/api/save_global_status", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ on_alert: enableAll }),
        }).catch((error) => {
            console.error("Error saving global status:", error);
        });
    }

    function fetchIntrusionStatus() {
        fetch('/api/get_intrusion_status')
            .then(response => response.json())
            .then(data => {
                const alertContainer = document.getElementById('alert-container');
                const intrusionMessageElement = document.getElementById('intrusion-message');
                const intrusionStatusElement = document.getElementById('intrusion-status');

                if (alertContainer && intrusionMessageElement && intrusionStatusElement) {
                    // Set the message to a fallback if undefined
                    const message = data.message || "No Intrusion Detected";
                    intrusionMessageElement.innerHTML = message;

                    if (data.intrusion_detected) {
                        alertContainer.classList.remove('alert-success');
                        alertContainer.classList.add('alert-danger');
                        intrusionStatusElement.innerText = "Intrusion Detected";

                        // Add the reset button if it doesn't exist
                        if (!document.getElementById('reset-intrusion')) {
                            const resetButton = document.createElement('button');
                            resetButton.id = 'reset-intrusion';
                            resetButton.className = 'btn btn-warning btn-sm';
                            resetButton.innerText = 'Reset Alarm';
                            alertContainer.appendChild(resetButton);

                            // Attach the reset button event listener
                            resetButton.addEventListener('click', resetIntrusion);
                        }
                    } else {
                        alertContainer.classList.remove('alert-danger');
                        alertContainer.classList.add('alert-success');
                        intrusionStatusElement.innerText = "No Intrusion";

                        // Remove the reset button if present
                        const resetButton = document.getElementById('reset-intrusion');
                        if (resetButton) {
                            resetButton.remove();
                        }
                    }
                } else {
                    console.error('Required elements not found in the DOM.');
                }
            })
            .catch(error => console.error('Error fetching intrusion status:', error));
    }

    function resetIntrusion() {
        fetch('/reset_intrusion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then(response => response.json())
            .then(data => {
                const alertContainer = document.getElementById('alert-container');
                const intrusionMessageElement = document.getElementById('intrusion-message');
                const intrusionStatusElement = document.getElementById('intrusion-status');
                const resetButton = document.getElementById('reset-intrusion');

                if (alertContainer && intrusionMessageElement && intrusionStatusElement) {
                    // Update UI to reflect reset state
                    alertContainer.classList.remove('alert-danger');
                    alertContainer.classList.add('alert-success');

                    // Update message and status
                    intrusionMessageElement.innerHTML = "No Intrusion Detected.";
                    intrusionStatusElement.innerText = "No Intrusion";

                    // Remove the reset button
                    if (resetButton) {
                        resetButton.remove();
                    }
                }
            })
            .catch(error => console.error('Error resetting intrusion:', error));
    }

    // Periodically fetch the status every 5 seconds
    setInterval(fetchIntrusionStatus, 5000);

    // Receive updates from the server
    socket.on("update_node", (data) => {
        console.log("Received WebSocket data:", data);
        const alertBox = document.querySelector(".alert");
        const messageElements = document.querySelectorAll('.intrusion-message');
        messageElements.forEach(message => {
            console.log(message.textContent); // Example of accessing messages
        });

        // Update intrusion message based on Intrusion_detected state
        if (data["Intrusion_detected"]) {
            alertBox.classList.remove("alert-success");
            alertBox.classList.add("alert-danger");
            messageElements.textContent = "Intrusion detected! Please check your system!";
        } else {
            alertBox.classList.remove("alert-danger");
            alertBox.classList.add("alert-success");
            messageElements.textContent = "All clear. No intrusions detected.";
        }

        for (const [nodeName, nodeData] of Object.entries(data)) {
            if (nodeName === "Intrusion_detected") continue;

            const nodeCard = document.getElementById(`node-card-${nodeName}`);
            const securityData = nodeData.sensors ? nodeData.sensors.security : null; // Retrieve security data

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

        // Update global switch state after receiving data
        updateGlobalSwitchState();
    });

    socket.on("intrusion_status", (data) => {
        const alertContainer = document.getElementById('alert-container');
        const intrusionMessageElement = document.getElementById('intrusion-message');
        const intrusionStatusElement = document.getElementById('intrusion-status');

        if (alertContainer && intrusionMessageElement && intrusionStatusElement) {
            const message = data.message || "No Intrusion Detected";
            intrusionMessageElement.innerHTML = message;

            if (data.intrusion_detected) {
                alertContainer.classList.remove('alert-success');
                alertContainer.classList.add('alert-danger');
                intrusionStatusElement.innerText = "Intrusion Detected";
            } else {
                alertContainer.classList.remove('alert-danger');
                alertContainer.classList.add('alert-success');
                intrusionStatusElement.innerText = "No Intrusion";
            }
        }
    });

});
