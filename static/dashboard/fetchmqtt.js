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
        });
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

setInterval(fetchMessages, 5000);
fetchMessages();
