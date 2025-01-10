// Utility Class for Sensor Configuration
class SensorConfigManager {
    constructor() {
        this.sensorTypes = {}; // Will be populated dynamically from the backend
    }

    async fetchSensorTypes() {
    try {
        const response = await fetch('/dashboard/sensor_types');
        if (!response.ok) {
            throw new Error(`Failed to fetch sensor types. HTTP Status: ${response.status}`);
        }

        const sensorTypes = await response.json();
        console.log('Fetched sensor types:', sensorTypes); // Log fetched data

        this.sensorTypes = sensorTypes.reduce((acc, sensor) => {
            acc[sensor.type_key] = {
                unit: sensor.unit,
                type: sensor.states ? 'status' : 'chart',
                states: sensor.states,
                color: this.getDefaultColor(sensor.type_key),
                maxDataPoints: 10,
                min: 0,
                max: this.getDefaultMaxValue(sensor.type_key),
                controllable: sensor.type_key === 'relay'
            };
            return acc;
        }, {});

        console.log('Processed sensor types:', this.sensorTypes); // Log processed data
    } catch (error) {
        console.error('Error fetching sensor types:', error);
    }
}

    getSensorConfig(sensorType) {
        return this.sensorTypes[sensorType] || null;
    }

    formatSensorName(sensorType) {
        return sensorType
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    getDefaultColor(sensorType) {
        const colors = {
            temperature: '#FF0000',
            humidity: '#0000FF',
            photoresistor: '#FFA500',
            pir: '#00FF00',
            reed_switch: '#00FF00',
            photo_interrupter: '#FFFF00',
            relay: '#FFA500'
        };
        return colors[sensorType] || '#000000';
    }

    getDefaultMaxValue(sensorType) {
        const maxValues = {
            temperature: 50,
            humidity: 100,
            photoresistor: 1000,
            pir: 1,
            reed_switch: 1,
            photo_interrupter: 1,
            relay: 1
        };
        return maxValues[sensorType] || 100;
    }
}

// Tile Rendering Class
class TileRenderer {
    constructor(configManager, container) {
        this.configManager = configManager;
        this.container = container;
        this.charts = {};
        this.tiles = {};
    }

    createSensorTiles(sensorData) {
        sensorData.forEach(sensor => {
            const { device_id, sensor_id, sensor_type } = sensor;
            this.createSingleTile(sensor_type, device_id, sensor_id);
        });
    }

    createSingleTile(sensorType, deviceId, sensorId) {
        const config = this.configManager.getSensorConfig(sensorType);
        if (!config) {
            console.warn(`No configuration found for sensor type: ${sensorType}`);
            return null;
        }

        const tileId = `${deviceId}_${sensorId}_${sensorType}Tile`;

        // Prevent duplicate tiles
        if (this.tiles[tileId]) {
            console.warn(`Tile for ${sensorType} already exists`);
            return this.tiles[tileId];
        }

        const tile = document.createElement('div');
        tile.classList.add('dashboard-tile', `tile-${sensorType}`);
        tile.id = tileId;
        tile.dataset.sensorType = sensorType;
        tile.dataset.deviceId = deviceId;
        tile.dataset.sensorId = sensorId;

        tile.innerHTML = this.generateTileContent(sensorType, config, deviceId, sensorId);
        this.container.appendChild(tile);

        // Add control button for controllable sensors
        if (config.controllable) {
            this.addControlButton(tile, sensorType, deviceId, sensorId);
        }

        // Initialize chart if needed
        if (config.type === 'chart') {
            this.initializeChart(sensorType, config, deviceId, sensorId);
        }

        this.tiles[tileId] = tile;
        return tile;
    }

    generateTileContent(sensorType, config, deviceId, sensorId) {
        const formattedName = this.configManager.formatSensorName(sensorType);
        const valueId = `${deviceId}_${sensorId}_${sensorType}Value`;
        const iconId = `${deviceId}_${sensorId}_${sensorType}Icon`;

        if (config.type === 'chart') {
            return `
                <div class="tile-header">
                    <h3>${formattedName} (${deviceId})</h3>
                    <button class="btn btn-danger delete-tile-button" data-tile-id="${sensorId}">Delete</button>
                </div>
                <div class="tile-content">
                    <canvas id="${deviceId}_${sensorId}_${sensorType}Chart"></canvas>
                    <div class="tile-value-container">
                        <span id="${iconId}"></span>
                        <p>Current: <span id="${valueId}">N/A</span>${config.unit}</p>
                    </div>
                </div>
            `;
        }

        return `
            <div class="tile-header">
                <h3>${formattedName} (${deviceId})</h3>
                <button class="btn btn-danger delete-tile-button" data-tile-id="${sensorId}">Delete</button>
            </div>
            <div class="tile-content">
                <span id="${iconId}" class="tile-icon"></span>
                <p>${formattedName}: <span id="${valueId}">N/A</span></p>
            </div>
        `;
    }

    addControlButton(tile, sensorType, deviceId, sensorId) {
        const controlContainer = document.createElement('div');
        controlContainer.classList.add('tile-controls');

        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Toggle';
        toggleButton.classList.add('btn', 'btn-secondary');
        toggleButton.dataset.state = 'OFF';

        const spinner = document.createElement('span');
        spinner.classList.add('spinner-border', 'spinner-border-sm', 'd-none');
        spinner.setAttribute('role', 'status');
        spinner.setAttribute('aria-hidden', 'true');

        const errorMessage = document.createElement('div');
        errorMessage.classList.add('text-danger', 'mt-2', 'd-none');

        toggleButton.addEventListener('click', async () => {
            const currentState = toggleButton.dataset.state;
            const newState = currentState === 'ON' ? 'OFF' : 'ON';

            toggleButton.disabled = true;
            spinner.classList.remove('d-none');

            try {
                const response = await fetch(`/dashboard/${deviceId}/relay/command`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ state: newState })
                });

                if (!response.ok) {
                    throw new Error(`Failed to set relay state. HTTP Status: ${response.status}`);
                }

                const result = await response.json();
                toggleButton.dataset.state = newState;
                const valueElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Value`);
                if (valueElement) {
                    valueElement.textContent = newState === 'ON' ? 'Active' : 'Inactive';
                }

                errorMessage.classList.add('d-none');
            } catch (error) {
                errorMessage.textContent = `Error: ${error.message}`;
                errorMessage.classList.remove('d-none');
            } finally {
                toggleButton.disabled = false;
                spinner.classList.add('d-none');
            }
        });

        toggleButton.appendChild(spinner);
        controlContainer.appendChild(toggleButton);
        controlContainer.appendChild(errorMessage);
        tile.appendChild(controlContainer);
    }

    initializeChart(sensorType, config, deviceId, sensorId) {
        const ctx = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Chart`);
        if (!ctx) return null;

        const chartColor = config.color || '#000000';

        this.charts[`${deviceId}_${sensorId}_${sensorType}`] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: this.configManager.formatSensorName(sensorType),
                    data: [],
                    borderColor: chartColor,
                    backgroundColor: chartColor,
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        min: config.min,
                        max: config.max,
                        title: {
                            display: true,
                            text: config.unit
                        }
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        return this.charts[`${deviceId}_${sensorId}_${sensorType}`];
    }

    updateSensorDisplay(sensorType, value, config, deviceId, sensorId) {
        const valueElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Value`);
        const iconElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Icon`);

        if (!valueElement) return;

        const numericValue = typeof value === 'string' ? parseFloat(value) : value;

        if (config.type === 'chart') {
            this.updateChart(sensorType, numericValue, deviceId, sensorId);
            valueElement.textContent = numericValue.toFixed(1);
        } else if (config.type === 'status') {
            const state = config.states[String(value)];
            if (state) {
                valueElement.textContent = state.label;
                valueElement.style.color = state.color;
                iconElement.textContent = state.icon;
            } else {
                valueElement.textContent = 'Unknown';
                valueElement.style.color = 'gray';
                iconElement.textContent = '?';
            }
        } else {
            valueElement.textContent = String(value);
        }
    }

    updateChart(sensorType, value, deviceId, sensorId) {
        const chart = this.charts[`${deviceId}_${sensorId}_${sensorType}`];
        const config = this.configManager.getSensorConfig(sensorType);

        if (!chart || typeof value !== 'number') return;

        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(value);

        if (chart.data.labels.length > config.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.update('none');
    }
}

// Data Fetching and Processing Class
class DataManager {
    constructor(tileRenderer, configManager) {
        this.tileRenderer = tileRenderer;
        this.configManager = configManager;
        this.sensors = []; // Store fetched sensors here
    }

    async fetchUserTiles() {
        try {
            const response = await fetch('/dashboard/tiles');
            if (!response.ok) {
                throw new Error(`Failed to fetch user tiles. HTTP Status: ${response.status}`);
            }

            const tiles = await response.json();
            this.tileRenderer.createSensorTiles(tiles);
        } catch (error) {
            console.error('Error fetching user tiles:', error);
        }
    }

    async fetchSensorTypes() {
        try {
            const response = await fetch('/dashboard/sensor_types', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
    
            if (!response.ok) {
                throw new Error(`Failed to fetch sensor types. HTTP Status: ${response.status}`);
            }
    
            const sensorTypes = await response.json();
            return sensorTypes;
        } catch (error) {
            console.error('Error fetching sensor types:', error);
            return [];
        }
    }

    findSensorByType(sensorType) {
        return this.sensors.find(sensor => sensor.type_key === sensorType);
    }

    async addTile(sensorId) {
        try {
            // Fetch sensor types
            const sensorTypes = await fetchSensorTypes();
    
            // Check if the selected sensor ID is available
            const sensorAvailable = sensorTypes.some(sensor => sensor.id === parseInt(sensorId));
            if (!sensorAvailable) {
                alert('Selected sensor is not available.');
                return;
            }
    
            // Create a new tile
            const response = await fetch('/dashboard/add_tiles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ sensor_id: sensorId }),
            });
    
            if (response.ok) {
                const result = await response.json();
                console.log('Tile added successfully:', result);
                fetchAndDisplayTiles(); // Refresh the tiles
            } else {
                console.error('Failed to add tile:', response.statusText);
            }
        } catch (error) {
            console.error('Error adding tile:', error);
        }
    }

    async deleteTile(tileId) {
        try {
            const response = await fetch(`/dashboard/tiles/${tileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to delete tile. HTTP Status: ${response.status}`);
            }

            const result = await response.json();
            console.log(result.message);
            this.fetchUserTiles(); // Refresh the tiles after deleting
        } catch (error) {
            console.error('Error deleting tile:', error);
        }
    }
}

// Main Dashboard Manager Class
class DashboardManager {
    constructor(config = {}) {
        this.config = {
            pollingInterval: 5000,
            ...config
        };

        this.configManager = new SensorConfigManager();
        this.container = this.initializeDashboardContainer();
        this.tileRenderer = new TileRenderer(this.configManager, this.container);
        this.dataManager = new DataManager(this.tileRenderer, this.configManager);

        this.initializeDashboard();
    }

    async initializeDashboard() {
        await this.configManager.fetchSensorTypes(); // Fetch sensor types first
        this.setupEventListeners();
        await this.dataManager.fetchUserTiles();
    }

    initializeDashboardContainer() {
        let container = document.querySelector('.dashboard-grid');
        if (!container) {
            container = document.createElement('div');
            container.classList.add('dashboard-grid');

            const dashboardContainer = document.querySelector('.dashboard-container') || document.body;
            dashboardContainer.appendChild(container);
        }
        return container;
    }

    populateSensorTypeSelect(sensorTypes) {
        const sensorTypeSelect = document.getElementById('sensorTypeSelect');
        if (!sensorTypeSelect) {
            console.error('sensorTypeSelect element not found');
            return;
        }
    
        // Clear existing options (except the default one)
        while (sensorTypeSelect.options.length > 1) {
            sensorTypeSelect.remove(1);
        }
    
        // Add new options based on the fetched sensor types
        sensorTypes.forEach(sensorType => {
            const option = document.createElement('option');
            option.value = sensorType.type_key; // Use type_key as the value
            option.textContent = sensorType.display_name; // Use display_name as the label
            sensorTypeSelect.appendChild(option);
        });
    
        console.log('Dropdown populated with sensor types:', sensorTypes); // Log populated data
    }

    async fetchAndPopulateSensorTypes() {
        try {
            const response = await fetch('/dashboard/sensor_types');
            if (!response.ok) {
                throw new Error(`Failed to fetch sensor types. HTTP Status: ${response.status}`);
            }
    
            const sensorTypes = await response.json();
            console.log('Fetched sensor types:', sensorTypes); // Log fetched data
    
            this.populateSensorTypeSelect(sensorTypes); // Call the method to populate the dropdown
        } catch (error) {
            console.error('Error fetching sensor types:', error);
        }
    }

    async initializeDashboard() {
        await this.fetchAndPopulateSensorTypes(); // Fetch and populate sensor types
        this.setupEventListeners();
        await this.dataManager.fetchUserTiles();
    }

    
    setupEventListeners() {
        const addTileButton = document.getElementById('addTileButton');
        const sensorTypeSelect = document.getElementById('sensorTypeSelect');

        console.log('addTileButton:', addTileButton); // Log the button element
        console.log('sensorTypeSelect:', sensorTypeSelect); // Log the select element

        if (addTileButton && sensorTypeSelect) {
            addTileButton.addEventListener('click', () => {
                console.log('Add Tile button clicked'); // Log button click
                const selectedSensorType = sensorTypeSelect.value;
                console.log('Selected sensor type:', selectedSensorType); // Log selected value

                if (selectedSensorType) {
                    const sensor = this.dataManager.findSensorByType(selectedSensorType);
                    console.log('Found sensor:', sensor); // Log found sensor

                    if (sensor) {
                        this.dataManager.addTile(sensor.sensor_id);
                    }
                }
            });
        } else {
            console.error('addTileButton or sensorTypeSelect not found');
        }

        // Handle tile deletion
        this.container.addEventListener('click', (event) => {
            if (event.target.classList.contains('delete-tile-button')) {
                console.log('Delete Tile button clicked'); // Log button click
                const tileId = event.target.dataset.tileId;
                console.log('Tile ID to delete:', tileId); // Log tile ID

                this.dataManager.deleteTile(tileId);
            }
        });
    }


}


document.addEventListener('DOMContentLoaded', () => {
    const sensorSelect = document.getElementById('sensorSelect'); // Replace 'sensorSelect' with the actual ID of your sensor select element
    const addTileButton = document.getElementById('addTileButton'); // Replace 'addTileButton' with the actual ID of your add tile button
    const tilesContainer = document.getElementById('tilesContainer'); // Replace 'tilesContainer' with the actual ID of your tiles container

    // Debugging: Log elements to ensure they are found
    console.log('Tiles Container:', tilesContainer);
    console.log('Add Tile Button:', addTileButton);
    console.log('Sensor Select:', sensorSelect);

    if (!addTileButton || !sensorSelect || !tilesContainer) {
        console.error('One or more required elements not found!');
        return;
    }

    // Fetch and display existing tiles
    async function fetchAndDisplayTiles() {
        try {
            const response = await fetch('/dashboard/tiles');
            const tiles = await response.json();
            tilesContainer.innerHTML = ''; // Clear existing tiles
    
            tiles.forEach(tile => {
                const tileElement = document.createElement('div');
                tileElement.className = 'tile';
                tileElement.innerHTML = `
                    <h3>${tile.sensor_type}</h3>
                    <p>Value: ${tile.value} ${tile.unit}</p>
                    <button onclick="deleteTile(${tile.id})">Delete</button>
                `;
                tilesContainer.appendChild(tileElement);
            });
        } catch (error) {
            console.error('Error fetching tiles:', error);
        }
    }

    // Add a new tile
    addTileButton.addEventListener('click', async () => {
        const selectedSensorId = sensorSelect.value;

        if (!selectedSensorId) {
            alert('Please select a sensor.');
            return;
        }
        
        await addTile(selectedSensorId);
    });

    // Delete a tile
    window.deleteTile = async (tileId) => {
        try {
            const response = await fetch(`/dashboard/tiles/${tileId}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                console.log('Tile deleted successfully');
                fetchAndDisplayTiles(); // Refresh the tiles
            } else {
                console.error('Failed to delete tile:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting tile:', error);
        }
    };

    // Populate the sensor dropdown
    async function populateSensorDropdown() {
        try {
            const response = await fetch('/dashboard/sensor_types');
            const sensorTypes = await response.json();
            sensorSelect.innerHTML = '<option value="" disabled selected>Select a sensor type</option>';

            sensorTypes.forEach(sensor => {
                const option = document.createElement('option');
                option.value = sensor.id; // Use sensor ID as the value
                option.textContent = sensor.display_name; // Use display name as the label
                sensorSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching sensor types:', error);
        }
    }

    // Initial fetch to populate the sensor dropdown and display tiles
    populateSensorDropdown();
    fetchAndDisplayTiles();
});

// Define the necessary HTML elements
const sensorSelect = document.getElementById('sensorSelect'); // Replace with the actual ID of your sensor select element
const addTileButton = document.getElementById('addTileButton'); // Replace with the actual ID of your add tile button
const tilesContainer = document.getElementById('tilesContainer'); // Replace with the actual ID of your tiles container

// Function to fetch sensor types
async function fetchSensorTypes() {
    try {
        const response = await fetch('/dashboard/sensor_types', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch sensor types. HTTP Status: ${response.status}`);
        }

        const sensorTypes = await response.json();
        return sensorTypes;
    } catch (error) {
        console.error('Error fetching sensor types:', error);
        return [];
    }
}

// Function to add a new tile
async function addTile(sensorId) {
    try {
        // Fetch sensor types
        const sensorTypes = await fetchSensorTypes();

        // Check if the selected sensor ID is available
        const sensorAvailable = sensorTypes.some(sensor => sensor.id === parseInt(sensorId));
        if (!sensorAvailable) {
            alert('Selected sensor is not available.');
            return;
        }

        // Create a new tile
        const response = await fetch('/dashboard/add_tiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sensor_id: sensorId }),
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Tile added successfully:', result);
            fetchAndDisplayTiles(); // Refresh the tiles
        } else {
            console.error('Failed to add tile:', response.statusText);
        }
    } catch (error) {
        console.error('Error adding tile:', error);
    }
}

// Function to fetch and display existing tiles
async function fetchAndDisplayTiles() {
    try {
        const response = await fetch('/dashboard/tiles');
        const tiles = await response.json();
        tilesContainer.innerHTML = ''; // Clear existing tiles

        tiles.forEach(tile => {
            const tileElement = document.createElement('div');
            tileElement.className = 'tile';
            tileElement.innerHTML = `
                <h3>${tile.sensor_type}</h3>
                <p>Value: ${tile.value} ${tile.unit}</p>
                <button onclick="deleteTile(${tile.id})">Delete</button>
            `;
            tilesContainer.appendChild(tileElement);
        });
    } catch (error) {
        console.error('Error fetching tiles:', error);
    }
}

// Event listener for the add tile button
addTileButton.addEventListener('click', async () => {
    const selectedSensorId = sensorSelect.value;

    if (!selectedSensorId) {
        alert('Please select a sensor.');
        return;
    }

    await addTile(selectedSensorId);
});