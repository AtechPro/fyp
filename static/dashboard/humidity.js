import { createChart, updateChart } from './chart.js';

const humidityData = { labels: [], values: [] };

const humidityCtx = document.getElementById('humidityChart').getContext('2d');
const humidityChart = createChart(humidityCtx, 'Humidity (%)', 'Humidity (%)', 0, 100, 'blue');

export function updateHumidityChart(newHumidity) {
    updateChart(humidityChart, newHumidity, humidityData.labels, humidityData.values, 10);
}
