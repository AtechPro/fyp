// Utility Class for Sensor Configuration
class SensorConfigManager {
    constructor() {
        this.sensorTypes = {
            temperature: { unit: '°C', type: 'chart', color: 'rgb(255, 99, 132)', maxDataPoints: 10 },
            humidity: { unit: '%', type: 'chart', color: 'rgb(54, 162, 235)', maxDataPoints: 10 },
            reed_switch: { unit: '', type: 'status', states: { 'OPEN': { color: 'red', label: 'Open' }, 'CLOSED': { color: 'green', label: 'Closed' } } },
            photo_interrupter: { unit: '', type: 'status', states: { 'CLEAR': { color: 'green', label: 'Clear' }, 'BLOCKED': { color: 'red', label: 'Blocked' } } },
            relay: { unit: '', type: 'status', states: { 'ON': { color: 'green', label: 'Active' }, 'OFF': { color: 'red', label: 'Inactive' } } }
        };
    }

    getSensorConfig(sensorType) {
        return this.sensorTypes[sensorType];
    }

    formatSensorName(sensorType) {
        return sensorType.charAt(0).toUpperCase() + sensorType.slice(1).replace('_', ' ');
    }
}

// Tile Rendering Class
class TileRenderer {
    constructor(configManager, container) {
        this.configManager = configManager;
        this.container = container;
        this.charts = {};
    }

    createSensorTiles(sensorTypes) {
        sensorTypes.forEach(sensorType => this.createSingleTile(sensorType));
    }

    createSingleTile(sensorType) {
        const config = this.configManager.getSensorConfig(sensorType);
        const tileId = `${sensorType}Tile`;
        if (document.getElementById(tileId)) return;

        const tile = document.createElement('div');
        tile.classList.add('dashboard-tile', `tile-${sensorType}`);
        tile.id = tileId;

        tile.innerHTML = this.generateTileContent(sensorType, config);
        this.container.appendChild(tile);

        if (config.type === 'chart') {
            this.initializeChart(sensorType, config);
        }
    }

    generateTileContent(sensorType, config) {
        const formattedName = this.configManager.formatSensorName(sensorType);
        const valueId = `${sensorType}Value`;

        if (config.type === 'chart') {
            return `
                <div class="tile-header"><h3>${formattedName}</h3></div>
                <div class="tile-content">
                    <canvas id="${sensorType}Chart"></canvas>
                    <p>Current: <span id="${valueId}">N/A</span>${config.unit}</p>
                </div>
            `;
        }

        return `
            <div class="tile-header"><h3>${formattedName}</h3></div>
            <div class="tile-content">
                <p>${formattedName}: <span id="${valueId}">N/A</span></p>
            </div>
        `;
    }

    initializeChart(sensorType, config) {
        const ctx = document.getElementById(`${sensorType}Chart`);
        if (!ctx) return;

        this.charts[sensorType] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: this.configManager.formatSensorName(sensorType),
                    data: [],
                    borderColor: config.color,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: config.unit
                        }
                    }
                }
            }
        });
    }

    updateSensorDisplay(sensorType, value, config) {
        const valueElement = document.getElementById(`${sensorType}Value`);
        if (!valueElement) return;

        if (config.type === 'chart') {
            this.updateChart(sensorType, value);
            valueElement.textContent = String(value);
        } else if (config.type === 'status') {
            const state = config.states[value];
            if (state) {
                valueElement.textContent = state.label;
                valueElement.style.color = state.color;
            } else {
                valueElement.textContent = 'Unknown';
                valueElement.style.color = 'gray';
            }
        } else {
            valueElement.textContent = String(value);
        }
    }

    updateChart(sensorType, value) {
        const chart = this.charts[sensorType];
        const config = this.configManager.getSensorConfig(sensorType);
        if (!chart || typeof value !== 'number') return;

        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(value);

        if (chart.data.labels.length > config.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.update();
    }
}

// Data Fetching and Processing Class
class DataManager {
    constructor(tileRenderer, configManager) {
        this.tileRenderer = tileRenderer;
        this.configManager = configManager;

        // Device ID mapping for different sensor types
        this.deviceMapping = {
            temperature: 'Device01',
            humidity: 'Device01',
            reed_switch: 'Device01',
            photo_interrupter: 'Device01',
            relay: 'Device01'
        };
    }

    // Fetch data for the sensors, dynamically using the correct device ID
    async fetchMessages(deviceId) {
        const sensorTypes = Object.keys(this.deviceMapping);  // Get all sensor types
        const categorizedData = {};

        try {
            for (const sensorType of sensorTypes) {
                // Get the device ID for the current sensor type
                const deviceForSensor = this.deviceMapping[sensorType];
                const url = `/mqtt/message/${deviceForSensor}/${sensorType}`;

                const response = await fetch(url);
                if (!response.ok) {
                    console.error(`Failed to fetch ${sensorType} data. HTTP Status: ${response.status}`);
                    continue;
                }

                const data = await response.json();
                if (data.error) {
                    console.error(`Error from server for ${sensorType}: ${data.error}`);
                } else {
                    categorizedData[sensorType] = data[sensorType];
                }
            }

            console.log('Fetched data:', categorizedData);
            this.processMessages(categorizedData);

        } catch (error) {
            console.error("Overall fetch error:", error);
        }
    }

    formatDeviceId(deviceId) {
        deviceId = deviceId.toString();
        if (!deviceId.startsWith("Device")) {
            const paddedId = deviceId.padStart(2, "0");
            deviceId = `Device${paddedId}`;
        }
        return deviceId;
    }

    processMessages(data) {
        Object.keys(data).forEach(sensorType => {
            const payload = data[sensorType];
            if (!payload) {
                console.error(`No data available for sensor type: ${sensorType}`);
                return;
            }

            let sensorData = this.extractSensorData(sensorType, payload);
            if (sensorData !== null) {
                const config = this.configManager.getSensorConfig(sensorType);
                this.tileRenderer.updateSensorDisplay(sensorType, sensorData, config);
            }
        });
    }

    extractSensorData(sensorType, payload) {
        let sensorData = null;

        switch(sensorType) {
            case 'temperature':
            case 'humidity':
                // For temperature and humidity, just use the value field
                sensorData = payload.value || payload;
                break;

            case 'reed_switch':
            case 'photo_interrupter':
            case 'relay':
                // For reed_switch, photo_interrupter, and relay, check for state
                sensorData = payload.state || payload;
                break;

            default:
                console.warn(`Unknown sensor type: ${sensorType}`);
                break;
        }

        console.log(`Extracted data for ${sensorType}:`, sensorData); // Log for debugging
        return sensorData;
    }

    async controlRelay(deviceId, relayState) {
        try {
            const formattedDeviceId = this.formatDeviceId(deviceId);
            const response = await fetch(`/relay/${formattedDeviceId}/${relayState}`);
            const data = await response.json();
            if (data.error) {
                console.error(data.error);
            } else {
                console.log(data.message);
            }
        } catch (error) {
            console.error('Error controlling relay:', error);
        }
    }
}

// Main Dashboard Manager Class
class DashboardManager {
    constructor(config = {}) {
        this.pollingInterval = config.pollingInterval || 2000;
        this.configManager = new SensorConfigManager();
        this.container = this.initializeDashboardContainer();
        this.tileRenderer = new TileRenderer(this.configManager, this.container);
        this.dataManager = new DataManager(this.tileRenderer, this.configManager);

        this.initializeDashboard();
        this.startMessagePolling();
        this.setupAddTileFunctionality(); // New method for adding tiles
    }

    initializeDashboardContainer() {
        let container = document.querySelector('.dashboard-grid');
        if (!container) {
            container = document.createElement('div');
            container.classList.add('dashboard-grid');
 const dashboardContainer = document.querySelector('.dashboard-container');
            if (dashboardContainer) {
                dashboardContainer.appendChild(container);
            } else {
                document.body.appendChild(container);
            }
        }
        return container;
    } 

    initializeDashboard() {
        const sensorTypes = Object.keys(this.configManager.sensorTypes);
        this.tileRenderer.createSensorTiles(sensorTypes);
    }

    startMessagePolling() {
        setInterval(() => {
            const deviceId = 'Device01'; // Replace with actual device ID retrieval
            this.dataManager.fetchMessages(deviceId);
        }, this.pollingInterval);
    }

    // New method to set up functionality for adding tiles
    setupAddTileFunctionality() {
        const addTileButton = document.getElementById('addTileButton');
        addTileButton.addEventListener('click', () => {
            const sensorTypeSelect = document.getElementById('sensorTypeSelect');
            const selectedSensorType = sensorTypeSelect.value;
            this.tileRenderer.createSingleTile(selectedSensorType); // Add the selected tile
        });
    }
}

// Initialize Dashboard on DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard is being initialized');
    const dashboard = new DashboardManager();
});