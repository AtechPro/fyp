// Function to update the devices table
function updateDevices() {
    fetch('/device')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('deviceTableBody');
            tbody.innerHTML = '';  // Clear existing table rows

            data.forEach(device => {
                const tr = document.createElement('tr');

                // Device ID
                const deviceIdCell = document.createElement('td');
                deviceIdCell.textContent = device.device_id;
                tr.appendChild(deviceIdCell);

                // Status
                const statusCell = document.createElement('td');
                const statusText = device.status === 'online' ? 'Online' : 'Offline';
                const statusColor = device.status === 'online' ? 'green' : 'red';
                statusCell.innerHTML = `<span style="color: ${statusColor};">${statusText}</span>`;
                tr.appendChild(statusCell);

                // Last Seen
                const lastSeenCell = document.createElement('td');
                lastSeenCell.textContent = device.last_seen
                    ? new Date(device.last_seen).toLocaleString()
                    : 'N/A';
                tr.appendChild(lastSeenCell);

                // Paired Status
                const pairedCell = document.createElement('td');
                const pairedText = device.paired ? 'Paired' : 'Not Paired';
                pairedCell.innerHTML = `<span>${pairedText}</span>`;
                tr.appendChild(pairedCell);

                // Sensors
                const sensorCell = document.createElement('td');
                if (device.sensors && Object.keys(device.sensors).length > 0) {
                    const sensorList = document.createElement('ul');
                    sensorList.style.paddingLeft = '20px';
                    sensorList.style.margin = '0';

                    // Populate sensor keys
                    Object.keys(device.sensors).forEach(sensorKey => {
                        const sensorItem = document.createElement('li');
                        sensorItem.textContent = sensorKey;
                        sensorList.appendChild(sensorItem);
                    });

                    sensorCell.appendChild(sensorList);
                } else {
                    sensorCell.textContent = 'No Sensors';
                }
                tr.appendChild(sensorCell);

                // Actions
                const actionsCell = document.createElement('td');

                // Pair Button (only if not paired)
                if (!device.paired) {
                    const pairButton = document.createElement('button');
                    pairButton.textContent = 'Pair';
                    pairButton.onclick = () => pairDeviceFromTable(device.device_id);
                    actionsCell.appendChild(pairButton);
                }

                // Remove Button
                const removeButton = document.createElement('button');
                removeButton.textContent = 'Remove';
                removeButton.style.marginLeft = '10px';
                removeButton.onclick = () => removeDevice(device.device_id);
                actionsCell.appendChild(removeButton);

                tr.appendChild(actionsCell);
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
            alert('Failed to fetch device list. Try again.');
        });
}

// Existing functions remain the same
function pairDeviceFromTable(deviceId) {
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
                updateDevices();  // Update the device table after pairing
            }
        })
        .catch(error => {
            console.error('Error pairing device:', error);
            alert('Failed to pair the device.');
        });
}

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
                updateDevices();  // Update the device table after removal
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