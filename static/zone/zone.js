const apiBaseUrl = '/api';

// Fetch and display zones
async function fetchZones() {
    try {
        const response = await fetch(`${apiBaseUrl}/zone`);
        const zones = await response.json();

        const container = document.getElementById('zones-container');
        container.innerHTML = '';

        zones.forEach(zone => {
            const zoneDiv = document.createElement('div');
            zoneDiv.classList.add('zone');

            zoneDiv.innerHTML = `
                <h3>${zone.name}</h3>
                <p>${zone.description}</p>
                <ul>
                    ${zone.sensors.map(sensor => `<li>${sensor.name} (${sensor.type})</li>`).join('')}
                </ul>
                <button class="delete-zone-button" data-zone-id="${zone.zone_id}">Delete Zone</button>
                <button class="edit-zone-button" data-zone-id="${zone.zone_id}">Edit Zone</button>
            `;

            container.appendChild(zoneDiv);
        });

        // Attach event listeners to delete buttons
        document.querySelectorAll('.delete-zone-button').forEach(button => {
            button.addEventListener('click', () => {
                const zoneId = button.dataset.zoneId;
                deleteZone(zoneId);
            });
        });

        // Attach event listeners to edit buttons
        document.querySelectorAll('.edit-zone-button').forEach(button => {
            button.addEventListener('click', () => {
                const zoneId = button.dataset.zoneId;
                openEditZonePopup(zoneId);
            });
        });
    } catch (error) {
        console.error('Error fetching zones:', error);
    }
}

// Open the edit zone popup
function openEditZonePopup(zoneId) {
    const popup = document.getElementById('edit-zone-popup');
    const zoneNameInput = document.getElementById('edit-zone-name');
    const zoneDescriptionInput = document.getElementById('edit-zone-description');
    const saveButton = document.getElementById('save-zone-changes');
    const closeButton = document.getElementById('close-edit-popup');

    // Fetch the current zone details
    fetch(`${apiBaseUrl}/zone`)
        .then(response => response.json())
        .then(zones => {
            const zone = zones.find(z => z.zone_id === parseInt(zoneId));
            if (zone) {
                zoneNameInput.value = zone.name;
                zoneDescriptionInput.value = zone.description;
                popup.style.display = 'block';

                // Save changes when the save button is clicked
                saveButton.onclick = () => {
                    const newName = zoneNameInput.value;
                    const newDescription = zoneDescriptionInput.value;

                    updateZoneDetails(zoneId, newName, newDescription);
                    popup.style.display = 'none';
                };

                // Close the popup when the close button is clicked
                closeButton.onclick = () => {
                    popup.style.display = 'none';
                };
            }
        })
        .catch(error => console.error('Error fetching zone details:', error));
}

// Update zone details
async function updateZoneDetails(zoneId, name, description) {
    try {
        const response = await fetch(`${apiBaseUrl}/zone/${zoneId}/details`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            fetchZones(); // Refresh the zones list
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Error updating zone:', error);
    }
}

// Fetch and display unassigned sensors as tiles
async function fetchUnassignedSensors() {
    try {
        const response = await fetch(`${apiBaseUrl}/unassigned-sensors`);
        const sensors = await response.json();

        const container = document.getElementById('sensor-tiles-container');
        container.innerHTML = ''; // Clear existing tiles

        sensors.forEach(sensor => {
            const sensorDiv = document.createElement('div');
            sensorDiv.classList.add('sensor');
            sensorDiv.dataset.sensorId = sensor.sensor_id;

            sensorDiv.innerHTML = `
                <h3>${sensor.name}</h3>
                <p>Type: ${sensor.type}</p>
            `;

            sensorDiv.addEventListener('click', () => toggleSensorSelection(sensorDiv));
            container.appendChild(sensorDiv);
        });
    } catch (error) {
        console.error('Error fetching unassigned sensors:', error);
    }
}

// Toggle sensor selection
function toggleSensorSelection(sensorDiv) {
    sensorDiv.classList.toggle('selected');
}

// Create a new zone
async function createZone(event) {
    event.preventDefault();

    const name = document.getElementById('zone-name').value;
    const description = document.getElementById('zone-description').value;

    // Collect IDs of selected sensors
    const selectedSensors = Array.from(document.querySelectorAll('.sensor.selected'))
        .map(sensorDiv => sensorDiv.dataset.sensorId);

    try {
        const response = await fetch(`${apiBaseUrl}/zone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, sensor_ids: selectedSensors })
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            fetchZones();
            fetchUnassignedSensors();
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Error creating zone:', error);
    }
}

// Delete a zone
async function deleteZone(zoneId) {
    try {
        const response = await fetch(`${apiBaseUrl}/zone/${zoneId}`, { method: 'DELETE' });
        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            fetchZones();
            fetchUnassignedSensors();
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('Error deleting zone:', error);
    }
}

// Initialize the script after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchZones();
    fetchUnassignedSensors();

    // Attach event listener to the zone creation form
    document.getElementById('create-zone-form').addEventListener('submit', createZone);
});