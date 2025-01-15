// Utility Class for Sensor Configuration
class SensorConfigManager {
    constructor() {
        this.sensorTypes = {
            temperature: {
                unit: '°C',
                type: 'chart',
                states: null,
                color: '#FF0000',
                maxDataPoints: 10,
                min: 0,
                max: 50  // Set max value for temperature to 50
            },
            humidity: {
                unit: '%',
                type: 'chart',
                states: null,
                color: '#0000FF',
                maxDataPoints: 10,
                min: 0,
                max: 100
            },
            photoresistor: {
                unit: 'Lux',
                type: 'chart',
                states: null,
                color: '#FFA500',
                maxDataPoints: 10,
                min: 0,
                max: 1000
            },
            pir: {
                unit: 'N/A',
                type: 'status',
                states: {
                    'MOTION': { label: 'Motion Detected', color: 'red', icon: '🚨' },
                    'NO MOTION': { label: 'No Motion', color: 'green', icon: '✅' }
                },
                color: '#00FF00',
                maxDataPoints: 10,
                min: 0,
                max: 1
            },
            reed_switch: {
                unit: 'N/A',
                type: 'status',
                states: {
                    'OPEN': { label: 'Open', color: 'red', icon: '🔓' },
                    'CLOSED': { label: 'Closed', color: 'green', icon: '🔒' }
                },
                color: '#00FF00',
                maxDataPoints: 10,
                min: 0,
                max: 1
            },
            photo_interrupter: {
                unit: 'N/A',
                type: 'status',
                states: {
                    'CLEAR': { label: 'Clear', color: 'green', icon: '✅' },
                    'BLOCKED': { label: 'Blocked', color: 'red', icon: '🚫' }
                },
                color: '#FFFF00',
                maxDataPoints: 10,
                min: 0,
                max: 1
            },
            relay: {
                unit: 'N/A',
                type: 'status',
                states: {
                    'ON': { label: 'ON', color: 'green', icon: '⚡' },
                    'OFF': { label: 'OFF', color: 'gray', icon: '❌' }
                },
                color: '#FFA500',
                maxDataPoints: 10,
                min: 0,
                max: 1,
                controllable: true
            }
        };
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

    getAllSensorTypes() {
        return Object.keys(this.sensorTypes);
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

    createSingleTile(sensorType, deviceId, sensorId, dashboardSensorId) {
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
    
        // Store necessary data attributes
        tile.dataset.sensorType = sensorType;
        tile.dataset.deviceId = deviceId;
        tile.dataset.sensorId = sensorId;
        tile.dataset.dashboardSensorId = dashboardSensorId;  // Store the dashboard sensor id
    
        // Generate tile content (using your generateTileContent function)
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
    
        
        const deleteIcon = tile.querySelector('.delete-icon');
        if (deleteIcon) {
            // Set the dashboard_sensor_id as a data attribute
            const dashboardSensorId = tile.dataset.dashboardSensorId; // Get the dashboard_sensor_id from the tile dataset
            deleteIcon.setAttribute('data-dashboard-sensor-id', dashboardSensorId);

            // Add click event listener for the delete icon
            deleteIcon.addEventListener('click', async () => {
                const clickedDashboardSensorId = deleteIcon.getAttribute('data-dashboard-sensor-id');
                console.log(`Delete clicked for Dashboard Sensor ID: ${clickedDashboardSensorId}`);
                
                try {
                    const response = await fetch(`/dashboard/remove_sensor/${clickedDashboardSensorId}`, {
                        method: 'DELETE',
                    });
                    const data = await response.json();

                    if (response.ok) {
                        console.log(data.message); // Success message
                        // Remove the tile from DOM
                        tile.remove();
                    } else {
                        console.error('Error:', data.message); // Error handling
                    }
                } catch (error) {
                    console.error('Error deleting sensor:', error);
                }
            });
        }

    
        this.tiles[tileId] = tile;
        return tile;
    }
    

    // Function to handle tile removal (delete)
    removeTile(dashboardSensorId) {
        // Find the tile by dashboard_sensor_id
        const tile = Object.values(this.tiles).find(t => t.dataset.dashboardSensorId === dashboardSensorId);
        if (tile) {
            tile.remove();
            delete this.tiles[tile.id];  // Remove tile from tiles object
            console.log(`Tile with Dashboard Sensor ID: ${dashboardSensorId} removed`);
        }
    }
    

    generateTileContent(sensorType, config, deviceId, sensorId) {
        const formattedName = this.configManager.formatSensorName(sensorType);
        const valueId = `${deviceId}_${sensorId}_${sensorType}Value`;
        const iconId = `${deviceId}_${sensorId}_${sensorType}Icon`;

        // Add a delete icon
        const deleteIcon = `<span class="delete-icon" style="cursor: pointer; float: right;">🗑️</span>`;

        if (config.type === 'chart') {
            return `
                <div class="tile-header">
                    <h3>${formattedName} (${deviceId})</h3>
                    ${deleteIcon}
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
                ${deleteIcon}
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
    
        // Create the toggle button
        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Toggle';
        toggleButton.classList.add('btn', 'btn-secondary');
        toggleButton.dataset.state = 'OFF'; // Initialize state
    
        // Create a loading spinner
        const spinner = document.createElement('span');
        spinner.classList.add('spinner-border', 'spinner-border-sm', 'd-none');
        spinner.setAttribute('role', 'status');
        spinner.setAttribute('aria-hidden', 'true');
    
        // Create an error message container
        const errorMessage = document.createElement('div');
        errorMessage.classList.add('text-danger', 'mt-2', 'd-none');
    
        // Add event listener for the toggle button
        toggleButton.addEventListener('click', async () => {
            const currentState = toggleButton.dataset.state;
            const newState = currentState === 'ON' ? 'OFF' : 'ON';
    
            // Disable the button and show the spinner
            toggleButton.disabled = true;
            spinner.classList.remove('d-none');
    
            try {
                // Send a POST request to the backend to control the relay
                const response = await fetch(`/dashboard/${deviceId}/relay/command`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ state: newState })
                });
    
                // Check if the response is OK
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Failed to set relay state. HTTP Status: ${response.status}, Response: ${errorText}`);
                }
    
                // Parse the JSON response
                const result = await response.json();
    
                // Update the button state and UI
                toggleButton.dataset.state = newState;
                const valueElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Value`);
                if (valueElement) {
                    valueElement.textContent = newState === 'ON' ? 'ON' : 'OFF';
                }
    
                // Hide the error message if previously shown
                errorMessage.classList.add('d-none');
            } catch (error) {
                // Show the error message
                errorMessage.textContent = `Error: ${error.message}`;
                errorMessage.classList.remove('d-none');
            } finally {
                // Re-enable the button and hide the spinner
                toggleButton.disabled = false;
                spinner.classList.add('d-none');
            }
        });
    
        // Append elements to the control container
        toggleButton.appendChild(spinner);
        controlContainer.appendChild(toggleButton);
        controlContainer.appendChild(errorMessage);
        tile.appendChild(controlContainer);
    }

    initializeChart(sensorType, config, deviceId, sensorId) {
        const ctx = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Chart`);
        if (!ctx) return null;
    
        const chartColor = config.color || '#000000'; // Default to black if no color provided
    
        this.charts[`${deviceId}_${sensorId}_${sensorType}`] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: this.configManager.formatSensorName(sensorType),
                    data: [],
                    borderColor: chartColor, // Line color
                    backgroundColor: chartColor, // Not used, but left for consistency
                    tension: 0.1, // Smooth the line
                    fill: false // Disable fill under the line
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
                        display: false // Hide x-axis labels
                    }
                },
                plugins: {
                    legend: {
                        display: false // Hide legend
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
    
        // Convert value to a number if it's a string
        const numericValue = typeof value === 'string' ? parseFloat(value) : value;
    
        if (config.type === 'chart') {
            this.updateChart(sensorType, numericValue, deviceId, sensorId);
            valueElement.textContent = numericValue.toFixed(1); // Ensure value is a number
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

        chart.update('none');  // Update without animation
    }
}

// Data Fetching and Processing Class
class DataManager {
    constructor(tileRenderer, configManager) {
        this.tileRenderer = tileRenderer;
        this.configManager = configManager;
    }

    async fetchCategorizedSensors() {
        try {
            const response = await fetch('/dashboard/dashboardsensor');
            if (!response.ok) {
                console.error(`Failed to fetch categorized sensors. HTTP Status: ${response.status}`);
                return;
            }

            const categorizedData = await response.json();
            this.processCategorizedSensors(categorizedData);
        } catch (error) {
            console.error('Error fetching categorized sensors:', error);
        }
    }

    processCategorizedSensors(categorizedData) {
        // Loop through each sensor category (grouped by sensor_key)
        Object.keys(categorizedData).forEach(category => {
            const sensors = categorizedData[category];
            
            // Loop through each sensor data point within the category
            sensors.forEach(sensor => {
                const { dashboard_sensor_id, sensor_id, device_id, sensor_key, value } = sensor;
    
                if (!dashboard_sensor_id) {
                    console.warn(`Missing dashboard_sensor_id for sensor_id: ${sensor_id} in category: ${category}`);
                    return; // Skip this sensor if it doesn't have a dashboard_sensor_id
                }
    
                // Find the configuration for the sensor (if available)
                const config = this.configManager.getSensorConfig(sensor_key);
    
                if (config) {
                    // Ensure device_id and sensor_id are strings for consistency
                    const deviceIdStr = String(device_id);
                    const sensorIdStr = String(sensor_id);
    
                    // Create or update the tile for this sensor
                    const tile = this.tileRenderer.createSingleTile(sensor_key, deviceIdStr, sensorIdStr, dashboard_sensor_id);
                    
                    // Store the dashboard sensor id in the tile for future reference
                    const tileKey = `${deviceIdStr}_${sensorIdStr}_${sensor_key}Tile`;
                    if (tile) {
                        tile.dataset.dashboardSensorId = dashboard_sensor_id; // Store the dashboard_sensor_id
                    }
    
                    // Update the display with the latest sensor value
                    this.tileRenderer.updateSensorDisplay(sensor_key, value, config, deviceIdStr, sensorIdStr);
                } else {
                    console.warn(`No configuration found for sensor_key: ${sensor_key}`);
                }
            });
        });
    }
    processCategorizedSensors(categorizedData) {
        // Loop through each sensor category (grouped by sensor_key)
        Object.keys(categorizedData).forEach(category => {
            const sensors = categorizedData[category];
            
            // Loop through each sensor data point within the category
            sensors.forEach(sensor => {
                const { dashboard_sensor_id, sensor_id, device_id, sensor_key, value } = sensor;
    
                if (!dashboard_sensor_id) {
                    console.warn(`Missing dashboard_sensor_id for sensor_id: ${sensor_id} in category: ${category}`);
                    return; // Skip this sensor if it doesn't have a dashboard_sensor_id
                }
    
                // Find the configuration for the sensor (if available)
                const config = this.configManager.getSensorConfig(sensor_key);
    
                if (config) {
                    // Ensure device_id and sensor_id are strings for consistency
                    const deviceIdStr = String(device_id);
                    const sensorIdStr = String(sensor_id);
    
                    // Create or update the tile for this sensor
                    const tile = this.tileRenderer.createSingleTile(sensor_key, deviceIdStr, sensorIdStr, dashboard_sensor_id);
                    
                    // Store the dashboard sensor id in the tile for future reference
                    const tileKey = `${deviceIdStr}_${sensorIdStr}_${sensor_key}Tile`;
                    if (tile) {
                        tile.dataset.dashboardSensorId = dashboard_sensor_id; // Store the dashboard_sensor_id
                    }
    
                    // Update the display with the latest sensor value
                    this.tileRenderer.updateSensorDisplay(sensor_key, value, config, deviceIdStr, sensorIdStr);
                } else {
                    console.warn(`No configuration found for sensor_key: ${sensor_key}`);
                }
            });
        });
    }
        

    async handleRelayControl(event) {
        const { sensorType, deviceId, sensorId, state } = event.detail;
        
        try {
            const response = await fetch(`/relay/${deviceId}/${sensorId}/${state}`);
            const data = await response.json();

            if (data.error) {
                console.error(data.error);
                // Optionally show error to user
            } else {
                console.log(data.message);
                // Optionally show success message
            }
        } catch (error) {
            console.error('Error controlling relay:', error);
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
        this.startMessagePolling();
        this.setupDynamicTileAddition();

        // Fetch and display categorized sensors
        await this.dataManager.fetchCategorizedSensors();
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

    startMessagePolling() {
        // Initial fetch
        this.dataManager.fetchCategorizedSensors();

        // Start periodic polling
        setInterval(() => {
            this.dataManager.fetchCategorizedSensors();
        }, this.config.pollingInterval);
    }

    setupDynamicTileAddition() {
        const addTileButton = document.getElementById('addTileButton');
        const sensorTypeSelect = document.getElementById('sensorTypeSelect');

        if (addTileButton && sensorTypeSelect) {
            addTileButton.addEventListener('click', () => {
                const selectedSensorType = sensorTypeSelect.value;
                if (selectedSensorType) {
                    this.tileRenderer.createSingleTile(selectedSensorType);
                }
            });
        }
    }
}

// Initialize Dashboard on DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Dashboard');
    window.Dashboard = new DashboardManager();
});