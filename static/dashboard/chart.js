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
                    tension: 0.4, // Increased from 0.2 for smoother curves
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            animation: {
                duration: 300, // Shorter animation duration
                easing: 'easeInOutQuad' // Smooth easing function
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Time' },
                    grid: {
                        display: true,
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                y: {
                    title: { display: true, text: yAxisLabel },
                    min: minY,
                    max: maxY,
                    grid: {
                        display: true,
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false
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
    
    // Add smooth transition
    chart.update('none'); // Disable animation for immediate data update
    setTimeout(() => {
        chart.update(); // Re-enable animation for smooth visual transition
    }, 0);
}