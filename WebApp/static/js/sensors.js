// Function to toggle individual alarm
function toggleAlarm(node) {
    const toggle = document.getElementById(`alarm-toggle-${node}`);
    toggle.disabled = true; // Temporarily disable toggle

    fetch('/api/toggle_alarm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node: node })
    })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            toggle.disabled = false; // Re-enable toggle
            updateAllToggleState(); // Update "Enable All" state dynamically
        })
        .catch(error => {
            console.error('Error:', error);
            toggle.disabled = false; // Re-enable toggle
            alert('Failed to toggle alarm. Please try again.');
        });
}

// Function to toggle all alarms
function toggleAllAlarms(enable) {
    console.log(`Toggling all alarms: ${enable}`);
    const masterToggle = document.getElementById("toggle-all-alarms");
    masterToggle.disabled = true; // Temporarily disable master toggle

    $.ajax({
        url: "/api/toggle_all_alarms",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ enable: enable }),
        success: function (response) {
            alert(enable ? "All alarms enabled successfully!" : "All alarms disabled successfully!");
            document.querySelectorAll('.form-check-input[id^="alarm-toggle-"]').forEach(toggle => {
                toggle.checked = enable;
            });
            updateAllToggleState(); // Sync the master toggle state
            masterToggle.disabled = false; // Re-enable master toggle
        },
        error: function (xhr, status, error) {
            console.error("Error toggling all alarms:", xhr.responseJSON?.error || error);
            alert("Failed to update all alarms. Please try again.");
            masterToggle.disabled = false; // Re-enable master toggle
        },
    });
}

// Function to update the "Enable All Alarms" switch dynamically
function updateAllToggleState() {
    const allToggle = document.getElementById("toggle-all-alarms");
    const sensorToggles = document.querySelectorAll(".form-check-input[id^='alarm-toggle-']");

    if (allToggle && sensorToggles.length > 0) {
        const areAllEnabled = Array.from(sensorToggles).every(toggle => toggle.checked);
        allToggle.checked = areAllEnabled;
    }
}

// Function to update a specific node's card
function updateNodeCard(nodeName, nodeData) {
    console.log(`Updating card for node: ${nodeName}`, nodeData);

    // Find the card for the given node
    const card = document.querySelector(`#node-card-${nodeName}`); // Locate the existing card

    if (!card) {
        console.warn(`Card for node "${nodeName}" not found.`);
        return;
    }

    if (!nodeData || !nodeData.sensors) {
        console.error(`Invalid node data for "${nodeName}".`, nodeData);
        return;
    }

    // Safely update the temperature
    const tempElement = card.querySelector('.temperature');
    if (tempElement) {
        tempElement.textContent = `Temperature: ${parseFloat(nodeData.sensors.temperature).toFixed(2) || 'N/A'} ℃`;
    } else {
        console.warn(`Temperature element not found in card for node "${nodeName}".`);
    }

    // Safely update the door status
    const doorElement = card.querySelector('.door');
    if (doorElement) {
        doorElement.textContent = `Door: ${nodeData.sensors.door || 'Unknown'}`;
    } else {
        console.warn(`Door element not found in card for node "${nodeName}".`);
    }

    // Safely update the motion status
    const motionElement = card.querySelector('.motion');
    if (motionElement) {
        motionElement.textContent = `Motion: ${nodeData.sensors.motion || 'Unknown'}`;
    } else {
        console.warn(`Motion element not found in card for node "${nodeName}".`);
    }

    if (!card) {
        // Create a new card if it doesn't exist
        console.log(`Card for node "${nodeName}" does not exist. Creating a new one.`);
        const newCardHtml = `
            <div class="card" id="node-card-${nodeName}">
                <h3>${nodeName}</h3>
                <p class="temperature">Temperature: ${parseFloat(nodeData.sensors.temperature).toFixed(2) || 'N/A'} ℃</p>
                <p class="door">Door: ${nodeData.sensors.door || 'Unknown'}</p>
                <p class="motion">Motion: ${nodeData.sensors.motion || 'Unknown'}</p>
            </div>`;
        document.querySelector('#nodes-container').insertAdjacentHTML('beforeend', newCardHtml);
        return;
    }

    // Ensure the "Enable All Alarms" toggle is updated
    updateAllToggleState();
}

// Initialize event listeners and Socket.IO
function initializeSensors() {
    console.log("Inside initializeSensors...");

    const cardContainer = document.getElementById('cards-container');
    if (!cardContainer) {
        console.error("Card container (#cards-container) is missing from the DOM!");
        return;
    }

    const allToggle = document.getElementById("toggle-all-alarms");
    const sensorToggles = document.querySelectorAll(".form-check-input[id^='alarm-toggle-']");

    if (allToggle) {
        allToggle.addEventListener("change", event => toggleAllAlarms(event.target.checked));
    }

    sensorToggles.forEach(toggle => {
        toggle.addEventListener("change", () => updateAllToggleState());
    });

    console.log("Defining socket...");
    const socket = io();
    console.log("After socket definition...");

    // Handle node updates
    socket.on('update_node', (payload) => {
        console.log("Node update received:", payload);

        if (!payload || typeof payload !== 'object' || Object.keys(payload).length === 0) {
            console.error("Invalid or empty payload received for update_node:", payload);
            return;
        }

        const nodeName = Object.keys(payload)[0];
        console.log(`Node Name: "${nodeName}"`);
        const nodeData = payload[nodeName];

        console.log("Extracted nodeName:", nodeName);
        console.log("Extracted nodeData:", nodeData);

        if (!nodeData || typeof nodeData !== 'object') {
            console.error(`Malformed data for node "${nodeName}":`, nodeData);
            return;
        }

        if (!nodeData || !nodeData.sensors) {
            console.error(`Invalid node data for "${nodeName}".`, nodeData);
            return;
        }

        const card = document.querySelector(`#node-card-${nodeName}`);
        if (!card) {
            console.warn(`Card for node "${nodeName}" not found.`);
            return;
        }

        const sensors = nodeData.sensors || {};
        card.querySelector('.temperature').textContent = `Temperature: ${sensors.temperature || 'N/A'} ℃`;
        card.querySelector('.door').textContent = `Door: ${sensors.door || 'Unknown'}`;
        card.querySelector('.motion').textContent = `Motion: ${sensors.motion || 'Unknown'}`;

        updateNodeCard(nodeName, nodeData);
    });

    // Handle updates for all nodes
    socket.on('update_all', (data) => {
        console.log("All nodes updated:", data);
        const enable = data.alarm;
        document.querySelectorAll(".form-check-input[id^='alarm-toggle-']").forEach((toggle) => {
            toggle.checked = enable;
        });
        updateAllToggleState();
    });

//    // Optional: Throttle updates for high-frequency data
//    let updateTimeout;
//    socket.on('update_node', function (payload) {
//        const node = payload.node;
//        const card = document.getElementById(`node-card-${node}`);
//        if (!card) {
//            console.warn(`Card for node ${node} not found in the DOM.`);
//            return;
//        }
//
//        clearTimeout(updateTimeout);
//        updateTimeout = setTimeout(() => {
//            // Your DOM update logic here
//        }, 100);
//
//        // Update card content
//        card.querySelector('.alarm-status span').textContent = payload.alarm ? 'Enabled' : 'Disabled';
//        card.querySelector('.alarm-status span').className = payload.alarm ? 'text-success' : 'text-danger';
//        card.querySelector('.temperature').textContent = `Temperature: ${payload.sensors.temperature || 'N/A'} ℃`;
//        card.querySelector('.door').textContent = `Door: ${payload.sensors.door || 'Unknown'}`;
//        card.querySelector('.motion').textContent = `Motion: ${payload.sensors.motion || 'Unknown'}`;
//    });

//    socket.on('update_node', (data) => {
//        clearTimeout(updateTimeout);
//        updateTimeout = setTimeout(() => {
//            // Your DOM update logic here
//        }, 100);
//    });
}

// Run initialization on DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
    console.log("Initializing sensors...");
    initializeSensors();
});
