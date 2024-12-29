document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    socket.on("update_node", (data) => {
        const nodeName = Object.keys(data)[0];
        const nodeData = data[nodeName];

        const nodeCard = document.getElementById(`node-card-${nodeName}`);
        if (nodeCard) {
            nodeCard.querySelector(".pir").textContent = `PIR: ${nodeData.sensors.motion || "N/A"}`;
            nodeCard.querySelector(".door").textContent = `Door: ${nodeData.sensors.door || "N/A"}`;
            nodeCard.querySelector(".status").textContent = nodeData.alarm
                ? "Status: Intrusion Detected!"
                : "Status: No intrusion detected.";
        } else {
            // Create a new card for the node
            const newCard = document.createElement("div");
            newCard.classList.add("node-card");
            newCard.id = `node-card-${nodeName}`;
            newCard.innerHTML = `
                <h2>${nodeName}</h2>
                <p>PIR: ${nodeData.sensors.motion || "N/A"}</p>
                <p>Door: ${nodeData.sensors.door || "N/A"}</p>
                <p>Status: ${nodeData.alarm ? "Intrusion Detected!" : "No intrusion detected."}</p>
            `;
            document.getElementById("nodes-container").appendChild(newCard);
        }
    });
});
