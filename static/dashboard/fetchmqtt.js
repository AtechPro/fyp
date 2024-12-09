// Utility Class for Sensor Configuration
class SensorConfigManager {
    constructor() {
        this.sensorTypes = {
            temperature: { 
                unit: '°C', 
                type: 'chart', 
                color: 'rgb(255, 99, 132)', 
                maxDataPoints: 10,
                min: 0,
                max: 50
            },
            humidity: { 
                unit: '%', 
                type: 'chart', 
                color: 'rgb(54, 162, 235)', 
                maxDataPoints: 10,
                min: 0,
                max: 100
            },
            reed_switch: { 
                type: 'status', 
                states: { 
                    'OPEN': { color: 'red', label: 'Open', icon: '🚪' }, 
                    'CLOSED': { color: 'green', label: 'Closed', icon: '🔒' } 
                } 
            },
            photo_interrupter: { 
                type: 'status', 
                states: { 
                    'CLEAR': { color: 'green', label: 'Clear', icon: '✅' }, 
                    'BLOCKED': { color: 'red', label: 'Blocked', icon: '⛔' } 
                } 
            },
            relay: { 
                type: 'status', 
                states: { 
                    'ON': { color: 'green', label: 'Active', icon: '🟢' }, 
                    'OFF': { color: 'red', label: 'Inactive', icon: '🔴' } 
                },
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

    createSensorTiles(sensorTypes) {
        sensorTypes.forEach(sensorType => this.createSingleTile(sensorType));
    }

    createSingleTile(sensorType) {
        const config = this.configManager.getSensorConfig(sensorType);
        if (!config) {
            console.warn(`No configuration found for sensor type: ${sensorType}`);
            return null;
        }

        const tileId = `${sensorType}Tile`;
        
        // Prevent duplicate tiles
        if (this.tiles[tileId]) {
            console.warn(`Tile for ${sensorType} already exists`);
            return this.tiles[tileId];
        }

        const tile = document.createElement('div');
        tile.classList.add('dashboard-tile', `tile-${sensorType}`);
        tile.id = tileId;
        tile.dataset.sensorType = sensorType;

        tile.innerHTML = this.generateTileContent(sensorType, config);
        this.container.appendChild(tile);

        // Add control button for controllable sensors
        if (config.controllable) {
            this.addControlButton(tile, sensorType);
        }

        // Initialize chart if needed
        if (config.type === 'chart') {
            this.initializeChart(sensorType, config);
        }

        this.tiles[tileId] = tile;
        return tile;
    }

    generateTileContent(sensorType, config) {
        const formattedName = this.configManager.formatSensorName(sensorType);
        const valueId = `${sensorType}Value`;
        const iconId = `${sensorType}Icon`;

        if (config.type === 'chart') {
            return `
                <div class="tile-header">
                    <h3>${formattedName}</h3>
                </div>
                <div class="tile-content">
                    <canvas id="${sensorType}Chart"></canvas>
                    <div class="tile-value-container">
                        <span id="${iconId}"></span>
                        <p>Current: <span id="${valueId}">N/A</span>${config.unit}</p>
                    </div>
                </div>
            `;
        }

        return `
            <div class="tile-header">
                <h3>${formattedName}</h3>
            </div>
            <div class="tile-content">
                <span id="${iconId}" class="tile-icon"></span>
                <p>${formattedName}: <span id="${valueId}">N/A</span></p>
            </div>
        `;
    }

    addControlButton(tile, sensorType) {
        const controlContainer = document.createElement('div');
        controlContainer.classList.add('tile-controls');
        
        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Toggle';
        toggleButton.classList.add('btn', 'btn-secondary');
        toggleButton.addEventListener('click', () => {
            const currentTile = document.getElementById(`${sensorType}Tile`);
            const currentValue = document.getElementById(`${sensorType}Value`).textContent;
            const newState = currentValue === 'Active' ? 'OFF' : 'ON';
            
            // Dispatch custom event for relay control
            const event = new CustomEvent('relay-control', {
                detail: { 
                    sensorType, 
                    state: newState 
                }
            });
            document.dispatchEvent(event);
        });

        controlContainer.appendChild(toggleButton);
        tile.appendChild(controlContainer);
    }

    initializeChart(sensorType, config) {
        const ctx = document.getElementById(`${sensorType}Chart`);
        if (!ctx) return null;
    
        const chartColor = config.color || '#000000'; // Default to black if no color provided
    
        this.charts[sensorType] = new Chart(ctx, {
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
    
        return this.charts[sensorType];
    }
    
    
    hexToRgba(hex, opacity = 1) {
        if (!/^#([0-9A-Fa-f]{3}){1,2}$/.test(hex)) {
            console.warn(`Invalid hex color: ${hex}`);
            return `rgba(0, 0, 0, ${opacity})`; // Default to black on invalid input
        }
    
        let r, g, b;
        if (hex.length === 4) {
            // Convert shorthand hex (#RGB) to full format (#RRGGBB)
            r = parseInt(hex[1] + hex[1], 16);
            g = parseInt(hex[2] + hex[2], 16);
            b = parseInt(hex[3] + hex[3], 16);
        } else {
            r = parseInt(hex.slice(1, 3), 16);
            g = parseInt(hex.slice(3, 5), 16);
            b = parseInt(hex.slice(5, 7), 16);
        }
    
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    

    updateSensorDisplay(sensorType, value, config) {
        const valueElement = document.getElementById(`${sensorType}Value`);
        const iconElement = document.getElementById(`${sensorType}Icon`);
        
        if (!valueElement) return;

        if (config.type === 'chart') {
            this.updateChart(sensorType, value);
            valueElement.textContent = value.toFixed(1);
        } else if (config.type === 'status') {
            const state = config.states[value];
            if (state) {
                valueElement.textContent = state.label;
                valueElement.style.color = state.color;
                iconElement.textContent = state.icon;
            } else {
                valueElement.textContent = 'Unknown';
                valueElement.style.color = 'gray';
                iconElement.textContent = '❓';
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

        chart.update('none');  // Update without animation
    }

    // Utility method to convert hex to rgba for chart background
    hexToRgba(hex, opacity = 1) {
        const [r, g, b] = hex.match(/\w\w/g).map(x => parseInt(x, 16));
        return `rgba(${r},${g},${b},${opacity})`;
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

        // Setup relay control event listener
        document.addEventListener('relay-control', this.handleRelayControl.bind(this));
    }

    async fetchMessages() {
        const sensorTypes = this.configManager.getAllSensorTypes();
        const categorizedData = {};

        try {
            for (const sensorType of sensorTypes) {
                const deviceForSensor = this.deviceMapping[sensorType];
                const url = `/dashboard/message/${deviceForSensor}/${sensorType}`;

                try {
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
                } catch (fetchError) {
                    console.error(`Fetch error for ${sensorType}:`, fetchError);
                }
            }

            this.processMessages(categorizedData);
        } catch (error) {
            console.error("Overall fetch error:", error);
        }
    }

    processMessages(data) {
        Object.keys(data).forEach(sensorType => {
            const payload = data[sensorType];
            if (!payload) {
                console.warn(`No data available for sensor type: ${sensorType}`);
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
        switch(sensorType) {
            case 'temperature':
            case 'humidity':
                return payload.value ?? payload;
            case 'reed_switch':
            case 'photo_interrupter':
            case 'relay':
                return payload.state ?? payload;
            default:
                console.warn(`Unknown sensor type: ${sensorType}`);
                return null;
        }
    }

    async handleRelayControl(event) {
        const { sensorType, state } = event.detail;
        
        try {
            const deviceId = this.deviceMapping[sensorType];
            const response = await fetch(`/relay/${deviceId}/${state}`);
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
        this.startMessagePolling();
        this.setupDynamicTileAddition();
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

    initializeDashboard() {
        const sensorTypes = this.configManager.getAllSensorTypes();
        this.tileRenderer.createSensorTiles(sensorTypes);
    }

    startMessagePolling() {
        // Initial fetch
        this.dataManager.fetchMessages();

        // Start periodic polling
        setInterval(() => {
            this.dataManager.fetchMessages();
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