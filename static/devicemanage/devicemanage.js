document.addEventListener("DOMContentLoaded", function () {
    const deviceContainer = document.getElementById("device-container");

    // Function to fetch and update devices
    function fetchAndUpdateDevices() {
        fetch('/devices')
            .then(response => response.json())
            .then(data => {
                displayDevices(data);
            })
            .catch(error => console.error('Error fetching devices:', error));
    }

    function displayDevices(devices) {
        deviceContainer.innerHTML = ""; // Clear container

        if (Object.keys(devices).length === 0) {
            deviceContainer.innerHTML = "<p>No devices found.</p>";
            return;
        }

        // Iterate through each device
        for (const [deviceId, deviceInfo] of Object.entries(devices)) {
            const deviceDiv = document.createElement("div");
            deviceDiv.className = "device";

            const statusClass = deviceInfo.status === "online" ? "online" : "offline";
            const lastSeen = new Date(deviceInfo.last_seen).toLocaleString();

            // Generate device card
            deviceDiv.innerHTML = `
                <h3>${deviceId} <span class="${statusClass}">(${deviceInfo.status})</span></h3>
                <p>IP Address: ${deviceInfo.ip_address}</p>
                <p>Last Seen: ${lastSeen}</p>
                <h4>Sensors:</h4>
                <ul class="sensors"></ul>
            `;

            const sensorsList = deviceDiv.querySelector(".sensors");
            const sensors = deviceInfo.sensors;

            if (Object.keys(sensors).length === 0) {
                sensorsList.innerHTML = "<li>No sensors detected.</li>";
            } else {
                // Add sensor types only
                for (const sensorName of Object.keys(sensors)) {
                    const sensorItem = document.createElement("li");
                    sensorItem.textContent = sensorName; // Only display sensor type
                    sensorsList.appendChild(sensorItem);
                }
            }

            deviceContainer.appendChild(deviceDiv);
        }
    }

    // Initial fetch and update
    fetchAndUpdateDevices();

    // Set interval to fetch and update every 3 seconds
    setInterval(fetchAndUpdateDevices, 3000);
});
