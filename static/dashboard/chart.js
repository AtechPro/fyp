// Export functions for creating and updating charts
export function createChart(context, label, yAxisLabel, minY, maxY, color) {
    return new Chart(context, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: label,
                    data: [],
                    borderColor: color,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Time' } },
                y: {
                    title: { display: true, text: yAxisLabel },
                    min: minY,
                    max: maxY
                }
            }
        }
    });
}

export function updateChart(chart, newValue, labelArray, valueArray, maxPoints) {
    const timestamp = new Date().toLocaleTimeString();
    labelArray.push(timestamp);
    valueArray.push(newValue);

    if (labelArray.length > maxPoints) {
        labelArray.shift();
        valueArray.shift();
    }

    chart.data.labels = labelArray;
    chart.data.datasets[0].data = valueArray;
    chart.update();
}
