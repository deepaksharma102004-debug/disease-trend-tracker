function renderSingleChart(canvas, labels, values, forecast, paramName) {
    const forecastLabels = forecast.map((_, i) => `+${i + 1}m`);
    const allLabels      = [...labels, ...forecastLabels];

    const actualData   = [...values, ...forecast.map(() => null)];
    const forecastData = [...values.map(() => null), ...forecast];

    if (values.length > 0 && forecast.length > 0) {
        forecastData[values.length - 1] = values[values.length - 1];
    }

    const accent      = "oklch(0.78 0.12 210)";
    const destructive = "oklch(0.65 0.22 25)";
    const gridColor   = "oklch(0.34 0.03 260)";
    const mutedFg     = "oklch(0.72 0.03 250)";
    const tooltipBg   = "oklch(0.24 0.045 260)";
    const foreground  = "oklch(0.96 0.01 250)";

    new Chart(canvas, {
        type: "line",
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: paramName,
                    data: actualData,
                    borderColor: accent,
                    backgroundColor: "oklch(0.78 0.12 210 / 10%)",
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: accent,
                    pointBorderColor: accent,
                    tension: 0.3,
                    fill: true,
                    spanGaps: false
                },
                {
                    label: "Forecast (next 3 mo)",
                    data: forecastData,
                    borderColor: destructive,
                    borderDash: [6, 4],
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: destructive,
                    pointBorderColor: destructive,
                    tension: 0.3,
                    fill: false,
                    spanGaps: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: tooltipBg,
                    borderColor: gridColor,
                    borderWidth: 1,
                    titleColor: foreground,
                    bodyColor: foreground,
                    padding: 10,
                    cornerRadius: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: mutedFg, font: { size: 11 } }
                },
                y: {
                    beginAtZero: false,
                    grid: { color: gridColor, drawTicks: false },
                    ticks: { color: mutedFg, font: { size: 11 } }
                }
            }
        }
    });
}