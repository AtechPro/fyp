// Global state object to store sensor configurations
let sensorConfigs = {};

// Utility functions for sensor configuration
async function fetchSensorTypes() {
    try {
        const response = await fetch('/dashboard/sensor_types');
        if (!response.ok) {
            throw new Error(`Failed to fetch sensor types. HTTP Status: ${response.status}`);
        }

        const sensorTypes = await response.json();
        console.log('Fetched sensor types:', sensorTypes);

        sensorConfigs = sensorTypes.reduce((acc, sensor) => {
            acc[sensor.type_key] = {
                unit: sensor.unit,
                type: sensor.states ? 'status' : 'chart',
                states: sensor.states,
                color: getDefaultColor(sensor.type_key),
                maxDataPoints: 10,
                min: 0,
                max: getDefaultMaxValue(sensor.type_key),
                controllable: sensor.type_key === 'relay'
            };
            return acc;
        }, {});

        console.log('Processed sensor configs:', sensorConfigs);
        return sensorTypes;
    } catch (error) {
        console.error('Error fetching sensor types:', error);
        return [];
    }
}

function formatSensorName(sensorType) {
    return sensorType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function getDefaultColor(sensorType) {
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

function getDefaultMaxValue(sensorType) {
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

// Chart management functions
const charts = {};

function initializeChart(sensorType, deviceId, sensorId) {
    const ctx = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Chart`);
    if (!ctx) return null;

    const config = sensorConfigs[sensorType];
    const chartColor = config?.color || '#000000';

    charts[`${deviceId}_${sensorId}_${sensorType}`] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: formatSensorName(sensorType),
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
                    min: config?.min || 0,
                    max: config?.max || 100,
                    title: {
                        display: true,
                        text: config?.unit || ''
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

    return charts[`${deviceId}_${sensorId}_${sensorType}`];
}

function updateChart(sensorType, value, deviceId, sensorId) {
    const chart = charts[`${deviceId}_${sensorId}_${sensorType}`];
    const config = sensorConfigs[sensorType];

    if (!chart || typeof value !== 'number') return;

    chart.data.labels.push(new Date().toLocaleTimeString());
    chart.data.datasets[0].data.push(value);

    if (chart.data.labels.length > (config?.maxDataPoints || 10)) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update('none');
}

// Display update functions
function updateSensorDisplay(sensorType, value, deviceId, sensorId) {
    const valueElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Value`);
    const iconElement = document.getElementById(`${deviceId}_${sensorId}_${sensorType}Icon`);
    const config = sensorConfigs[sensorType];

    if (!valueElement || !config) return;

    const numericValue = typeof value === 'string' ? parseFloat(value) : value;

    if (config.type === 'chart') {
        updateChart(sensorType, numericValue, deviceId, sensorId);
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

// Initialize the dashboard
async function initializeDashboard() {
    try {
        await fetchSensorTypes();
        // Additional initialization code can be added here
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

// Event handler setup
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});