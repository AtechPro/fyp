// Function to update the list of devices (called periodically)
function updateDevices() {
    fetch('/device')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('deviceTilesContainer');
            container.innerHTML = '';  // Clear existing tiles

            data.forEach(device => {
                const tile = document.createElement('div');
                tile.classList.add('device-tile');

                // Only show Device Title and Description if paired
                if (device.paired) {
                    // Device Title
                    const titleElement = document.createElement('div');
                    titleElement.classList.add('device-title');
                    titleElement.textContent = device.title || 'No Title';
                    tile.appendChild(titleElement);

                    // Device Description
                    const descriptionElement = document.createElement('div');
                    descriptionElement.classList.add('device-description');
                    descriptionElement.textContent = device.description || 'No Description';
                    tile.appendChild(descriptionElement);
                }

                // Device ID
                const deviceIdElement = document.createElement('div');
                deviceIdElement.classList.add('device-id');
                deviceIdElement.textContent = device.device_id;
                tile.appendChild(deviceIdElement);

                // Status
                const statusElement = document.createElement('div');
                statusElement.classList.add('status');
                if (device.status !== 'online') {
                    statusElement.classList.add('offline');  // Add 'offline' class
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

                if (device.paired) {
                    // Edit Button
                    const editButton = document.createElement('button');
                    editButton.textContent = 'Edit';
                    editButton.onclick = () => editDeviceFromTile(device.device_id);
                    actionsContainer.appendChild(editButton);

                    // Delete Button
                    const deleteButton = document.createElement('button');
                    deleteButton.textContent = 'Delete';
                    deleteButton.style.marginLeft = '10px';
                    deleteButton.onclick = () => removeDevice(device.device_id);
                    actionsContainer.appendChild(deleteButton);
                } else {
                    // Pair Button
                    const pairButton = document.createElement('button');
                    pairButton.textContent = 'Pair';
                    pairButton.onclick = () => pairDeviceFromTile(device.device_id);
                    actionsContainer.appendChild(pairButton);
                }

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
    const title = prompt('Enter a title for the device:');
    const description = prompt('Enter a description for the device:');

    fetch('/add_device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            device_id: deviceId,
            title: title,
            description: description
        })
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

// Edit Device from Tile (for tile action)
function editDeviceFromTile(deviceId) {
    const newTitle = prompt('Enter new title for the device:');
    const newDescription = prompt('Enter new description for the device:');
    if (newTitle || newDescription) {
        fetch('/edit_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                title: newTitle,
                description: newDescription
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    alert(data.message);
                    updateDevices();  // Update the device tiles after editing
                }
            })
            .catch(error => {
                console.error('Error editing device:', error);
                alert('Failed to edit the device.');
            });
    }
}

// Periodically update the device list every 5 seconds
setInterval(updateDevices, 5000);

// Initial load of devices when the page is loaded
window.onload = updateDevices;
