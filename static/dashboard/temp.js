import { createChart, updateChart } from './chart.js';

const temperatureData = { labels: [], values: [] };

const tempCtx = document.getElementById('temperatureChart').getContext('2d');
const temperatureChart = createChart(tempCtx, 'Temperature (°C)', 'Temperature (°C)', 0, 50, 'red');

export function updateTemperatureChart(newTemperature) {
    updateChart(temperatureChart, newTemperature, temperatureData.labels, temperatureData.values, 10);
}
