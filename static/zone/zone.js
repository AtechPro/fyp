// Utility function to handle API calls
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`/zone${endpoint}`, options);
    return await response.json();
}

// Function to get CSRF token
function getCSRFToken() {
    return document.querySelector('[name=csrf-token]').value;
}

// Function to create a new zone with sensors
async function createZone() {
    const zoneName = document.getElementById('zone-name').value;
    const zoneDesc = document.getElementById('zone-desc').value;
    const selectedSensors = Array.from(document.getElementById('sensor-select').selectedOptions)
        .map(option => parseInt(option.value));

    const data = await apiCall('/create', 'POST', {
        zone_name: zoneName,
        zone_desc: zoneDesc,
        sensor_ids: selectedSensors
    });

    const resultDiv = document.getElementById('create-result');
    resultDiv.innerHTML = `
        <p>${data.message}</p>
        ${data.newly_assigned.length ? `<p>Newly assigned sensors: ${data.newly_assigned.join(', ')}</p>` : ''}
        ${data.already_assigned.length ? `<p>Already assigned sensors: ${data.already_assigned.join(', ')}</p>` : ''}
    `;
    
    loadZonesWithSensors();
    loadUnassignedSensors();
}

// Function to load all unassigned sensors
async function loadUnassignedSensors() {
    const sensors = await apiCall('/unassigned-sensors');
    const sensorSelect = document.getElementById('sensor-select');
    sensorSelect.innerHTML = '';

    sensors.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor.sensor_id;
        option.text = `${sensor.name} (${sensor.sensor_key})`;
        sensorSelect.appendChild(option);
    });
}

// Function to load zones with their sensors
async function loadZonesWithSensors() {
    const zones = await apiCall('/zones/with-sensors');
    const zoneTilesContainer = document.getElementById('zone-tiles-container');
    zoneTilesContainer.innerHTML = '';

    zones.forEach(zone => {
        const tile = createZoneTile(zone);
        zoneTilesContainer.appendChild(tile);
    });
}

// Function to create a zone tile with sensor information
function createZoneTile(zone) {
    const tile = document.createElement('div');
    tile.classList.add('zone-tile');
    
    // Zone header
    const header = document.createElement('div');
    header.classList.add('zone-header');
    
    const title = document.createElement('h3');
    title.innerText = zone.name;
    header.appendChild(title);
    
    const description = document.createElement('p');
    description.innerText = zone.description || 'No description';
    header.appendChild(description);
    
    tile.appendChild(header);

    // Sensors section
    const sensorsSection = document.createElement('div');
    sensorsSection.classList.add('zone-sensors');
    
    const sensorsList = document.createElement('ul');
    zone.sensors.forEach(sensor => {
        const listItem = document.createElement('li');
        listItem.classList.add('sensor-item');
        
        const sensorInfo = document.createElement('span');
        sensorInfo.innerText = `${sensor.name} (${sensor.sensor_key})`;
        listItem.appendChild(sensorInfo);
        
        const removeButton = document.createElement('button');
        removeButton.innerText = 'Remove';
        removeButton.onclick = () => removeSensorFromZone(sensor.sensor_id);
        listItem.appendChild(removeButton);
        
        sensorsList.appendChild(listItem);
    });
    
    sensorsSection.appendChild(sensorsList);
    tile.appendChild(sensorsSection);

    // Add sensor section
    const addSensorSection = createAddSensorSection(zone.zone_id);
    tile.appendChild(addSensorSection);

    // Actions section
    const actions = document.createElement('div');
    actions.classList.add('zone-actions');
    
    const deleteButton = document.createElement('button');
    deleteButton.innerText = 'Delete Zone';
    deleteButton.onclick = () => deleteZone(zone.zone_id);
    actions.appendChild(deleteButton);
    
    tile.appendChild(actions);

    return tile;
}

// Function to create the add sensor section for a zone
function createAddSensorSection(zoneId) {
    const section = document.createElement('div');
    section.classList.add('add-sensor-section');
    
    const select = document.createElement('select');
    select.id = `add-sensor-${zoneId}`;
    select.multiple = true;
    
    // Will be populated when unassigned sensors are loaded
    loadUnassignedSensorsForZone(zoneId, select);
    
    const button = document.createElement('button');
    button.innerText = 'Add Sensors';
    button.onclick = () => reassignSensors(zoneId);
    
    section.appendChild(select);
    section.appendChild(button);
    
    return section;
}

// Function to load unassigned sensors for a specific zone
async function loadUnassignedSensorsForZone(zoneId, selectElement) {
    const sensors = await apiCall('/unassigned-sensors');
    selectElement.innerHTML = '';

    sensors.forEach(sensor => {
        const option = document.createElement('option');
        option.value = sensor.sensor_id;
        option.text = `${sensor.name} (${sensor.sensor_key})`;
        selectElement.appendChild(option);
    });
}

// Function to reassign sensors to a zone
async function reassignSensors(zoneId) {
    const select = document.getElementById(`add-sensor-${zoneId}`);
    const selectedSensors = Array.from(select.selectedOptions).map(option => parseInt(option.value));
    
    const data = await apiCall(`/reassign/${zoneId}`, 'POST', {
        sensor_ids: selectedSensors
    });

    alert(`
        Sensors reassigned successfully
        Success: ${data.success.length} sensors
        Already in zone: ${data.already_in_zone.length} sensors
        Not found: ${data.not_found.length} sensors
    `);

    loadZonesWithSensors();
    loadUnassignedSensors();
}

// Function to remove a sensor from its zone
async function removeSensorFromZone(sensorId) {
    await apiCall(`/remove_sensor/${sensorId}`, 'DELETE');
    loadZonesWithSensors();
    loadUnassignedSensors();
}

// Function to delete a zone
async function deleteZone(zoneId) {
    if (confirm('Are you sure you want to delete this zone? All sensors will be unassigned.')) {
        await apiCall(`/delete/${zoneId}`, 'DELETE');
        loadZonesWithSensors();
        loadUnassignedSensors();
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    loadZonesWithSensors();
    loadUnassignedSensors();
});