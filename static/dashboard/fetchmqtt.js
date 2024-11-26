import { updateTemperatureChart } from './temp.js';
import { updateHumidityChart } from './humidity.js';

async function fetchMessages() {
    try {
        const response = await fetch('/mqtt/messages');
        const messages = await response.json();

        messages.forEach(msg => {
            const data = JSON.parse(msg.payload);

            updateTemperatureChart(data.temperature);
            updateHumidityChart(data.humidity);
            document.getElementById('temperatureValue').textContent = data.temperature.toFixed(2);  // Display temperature with 2 decimal places
            document.getElementById('humidityValue').textContent = data.humidity.toFixed(2);  // Display humidity with 2 decimal places

        });
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

setInterval(fetchMessages, 3000);
fetchMessages();
