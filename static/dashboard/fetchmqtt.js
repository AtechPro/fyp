import { updateTemperatureChart } from './temp.js';
import { updateHumidityChart } from './humidity.js';

async function fetchMessages() {
    try {
        const response = await fetch('/mqtt/devices');
        const deviceMessages = await response.json();

        // Iterate through each device
        for (const [deviceId, deviceData] of Object.entries(deviceMessages)) {
            // Focus on sensor messages for each device
            const sensorMessages = deviceData.sensors;

            // Process each sensor message
            sensorMessages.forEach(data => {
                // Check if temperature and humidity exist before processing
                if (data.temperature !== undefined && data.humidity !== undefined) {
                    updateTemperatureChart(data.temperature);
                    updateHumidityChart(data.humidity);
                    
                    // Update display elements
                    document.getElementById('temperatureValue').textContent = data.temperature.toFixed(2);
                    document.getElementById('humidityValue').textContent = data.humidity.toFixed(2);
                    
                }
            });
        }
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

// Initial fetch and then periodic updates
setInterval(fetchMessages, 3000);
fetchMessages();