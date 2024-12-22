// Function to update the devices tile view
// Function to update the devices tile view
function updateDevices() {
    fetch('/device')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('deviceTilesContainer');
            container.innerHTML = '';  // Clear existing tiles

            data.forEach(device => {
                const tile = document.createElement('div');
                tile.classList.add('device-tile');

                // Device ID
                const deviceIdElement = document.createElement('div');
                deviceIdElement.classList.add('device-id');
                deviceIdElement.textContent = device.device_id;
                tile.appendChild(deviceIdElement);

                // Status
                const statusElement = document.createElement('div');
                statusElement.classList.add('status');
                // Add 'offline' class only if the device is offline
                if (device.status !== 'online') {
                    statusElement.classList.add('offline');
                }
                statusElement.textContent = device.status === 'online' ? 'Online' : 'Offline';
                tile.appendChild(statusElement);

                // Last Seen
                const lastSeenElement = document.createElement('div');
                lastSeenElement.textContent = device.last_seen ? new Date(device.last_seen).toLocaleString() : 'N/A';
                tile.appendChild(lastSeenElement);

                // Paired Status
                const pairedElement = document.createElement('div');
                pairedElement.textContent = device.paired ? 'Paired' : 'Not Paired';
                tile.appendChild(pairedElement);

                // Sensors
                const sensorElement = document.createElement('div');
                if (device.sensors && Object.keys(device.sensors).length > 0) {
                    const sensorList = document.createElement('ul');
                    sensorList.classList.add('sensor-list');
                    Object.keys(device.sensors).forEach(sensorKey => {
                        const sensorItem = document.createElement('li');
                        sensorItem.textContent = sensorKey;
                        sensorList.appendChild(sensorItem);
                    });
                    sensorElement.appendChild(sensorList);
                } else {
                    sensorElement.textContent = 'No Sensors';
                }
                tile.appendChild(sensorElement);

                // Actions
                const actionsContainer = document.createElement('div');

                // Pair Button (only if not paired)
                if (!device.paired) {
                    const pairButton = document.createElement('button');
                    pairButton.textContent = 'Pair';
                    pairButton.onclick = () => pairDeviceFromTile(device.device_id);
                    actionsContainer.appendChild(pairButton);
                }

                // Remove Button
                const removeButton = document.createElement('button');
                removeButton.textContent = 'Remove';
                removeButton.style.marginLeft = '10px';
                removeButton.onclick = () => removeDevice(device.device_id);
                actionsContainer.appendChild(removeButton);

                tile.appendChild(actionsContainer);
                container.appendChild(tile);
            });
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
            alert('Failed to fetch device list. Try again.');
        });
}


// Pair Device from Tile (for tile action)
function pairDeviceFromTile(deviceId) {
    fetch('/add_device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert(data.message);
                updateDevices();  // Update the device tiles after pairing
            }
        })
        .catch(error => {
            console.error('Error pairing device:', error);
            alert('Failed to pair the device.');
        });
}

// Remove Device from Tile (for tile action)
function removeDevice(deviceId) {
    fetch(`/delete_device/${deviceId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert(data.message);
                updateDevices();  // Update the device tiles after removal
            }
        })
        .catch(error => {
            console.error('Error removing device:', error);
            alert('Failed to remove the device.');
        });
}

// Periodically update the device list every 5 seconds
setInterval(updateDevices, 5000);

// Initial load of devices when the page is loaded
window.onload = updateDevices;
