/**
 * charts.js - Chart rendering functions
 * ---------------------------------------
 * All Chart.js visualizations for the NYC Taxi Data Explorer.
 * Depends on: api.js (fetchAPI, formatNumber, formatCurrency, COLORS, CHART_COLORS)
 * Depends on: app.js (chart instance variables declared as globals)
 */

// =========================================
//  Hourly Trip Volume Chart
// =========================================
async function loadHourlyChart() {
    const data = await fetchAPI("/hourly");
    if (!data) return;

    const labels = data.map(d => {
        const h = d.hour;
        return h === 0 ? "12AM" : h < 12 ? h + "AM" : h === 12 ? "12PM" : (h - 12) + "PM";
    });
    const counts = data.map(d => d.trip_count);

    if (hourlyChart) hourlyChart.destroy();
    hourlyChart = new Chart(document.getElementById("hourlyChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Trip Count",
                data: counts,
                backgroundColor: counts.map(c => {
                    const max = Math.max(...counts);
                    const intensity = c / max;
                    return `rgba(247, 201, 72, ${0.3 + intensity * 0.7})`;
                }),
                borderColor: COLORS.yellow,
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.parsed.y.toLocaleString()} trips`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "#1e2e3e" },
                    ticks: { callback: v => formatNumber(v) }
                },
                x: { grid: { display: false } }
            },
        },
    });
}

// =========================================
//  Daily Trip Volume Chart
// =========================================
async function loadDailyChart() {
    const data = await fetchAPI("/daily");
    if (!data) return;

    const labels = data.map(d => d.day_name);
    const counts = data.map(d => d.trip_count);

    if (dailyChart) dailyChart.destroy();
    dailyChart = new Chart(document.getElementById("dailyChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Trip Count",
                data: counts,
                backgroundColor: data.map((d, i) => i >= 5 ? COLORS.orange : COLORS.blue),
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => {
                            return `Avg Fare: ${formatCurrency(data[ctx.dataIndex].avg_fare)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "#1e2e3e" },
                    ticks: { callback: v => formatNumber(v) }
                },
                x: { grid: { display: false } }
            },
        },
    });
}

// =========================================
//  Borough Breakdown Chart
// =========================================
async function loadBoroughChart() {
    const data = await fetchAPI("/boroughs");
    if (!data) return;

    if (boroughChart) boroughChart.destroy();
    boroughChart = new Chart(document.getElementById("boroughChart"), {
        type: "doughnut",
        data: {
            labels: data.map(d => d.borough),
            datasets: [{
                data: data.map(d => d.trip_count),
                backgroundColor: CHART_COLORS.slice(0, data.length),
                borderColor: "#0f1923",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { padding: 15, usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => {
                            const d = data[ctx.dataIndex];
                            return [
                                `Avg Fare: ${formatCurrency(d.avg_fare)}`,
                                `Avg Distance: ${d.avg_distance} mi`,
                                `Revenue: ${formatCurrency(d.total_revenue)}`
                            ];
                        }
                    }
                }
            },
        },
    });
}

// =========================================
//  Payment Types Chart
// =========================================
async function loadPaymentChart() {
    const data = await fetchAPI("/payment-analysis");
    if (!data) return;

    if (paymentChart) paymentChart.destroy();
    paymentChart = new Chart(document.getElementById("paymentChart"), {
        type: "pie",
        data: {
            labels: data.map(d => d.payment_name),
            datasets: [{
                data: data.map(d => d.trip_count),
                backgroundColor: [COLORS.yellow, COLORS.green, COLORS.red, COLORS.purple, COLORS.teal, COLORS.orange],
                borderColor: "#0f1923",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { padding: 15, usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => {
                            const d = data[ctx.dataIndex];
                            return [
                                `Avg Fare: ${formatCurrency(d.avg_fare)}`,
                                `Avg Tip: ${formatCurrency(d.avg_tip)}`
                            ];
                        }
                    }
                }
            },
        },
    });
}

// =========================================
//  Fare Distribution Chart (uses custom bucket sort on backend)
// =========================================
async function loadFareDistribution() {
    const data = await fetchAPI("/fare-distribution");
    if (!data) return;

    if (fareChart) fareChart.destroy();
    fareChart = new Chart(document.getElementById("fareChart"), {
        type: "bar",
        data: {
            labels: data.map(d => d.range),
            datasets: [{
                label: "Number of Trips",
                data: data.map(d => d.count),
                backgroundColor: COLORS.teal,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: ctx => `Avg: ${formatCurrency(data[ctx.dataIndex].avg_fare)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "#1e2e3e" },
                    ticks: { callback: v => formatNumber(v) }
                },
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45 }
                }
            },
        },
    });
}

// =========================================
//  Speed Analysis Chart
// =========================================
async function loadSpeedAnalysis() {
    const data = await fetchAPI("/speed-analysis");
    if (!data) return;

    // Group by borough
    const boroughs = {};
    data.forEach(d => {
        if (!boroughs[d.borough]) boroughs[d.borough] = [];
        boroughs[d.borough].push(d);
    });

    const labels = Array.from({ length: 24 }, (_, h) =>
        h === 0 ? "12AM" : h < 12 ? h + "AM" : h === 12 ? "12PM" : (h - 12) + "PM"
    );

    const datasets = [];
    const colorMap = {
        Manhattan: COLORS.yellow,
        Brooklyn: COLORS.blue,
        Queens: COLORS.green,
        Bronx: COLORS.red,
    };

    Object.keys(boroughs).forEach(borough => {
        const hourData = new Array(24).fill(null);
        boroughs[borough].forEach(d => {
            hourData[d.hour] = d.avg_speed;
        });

        datasets.push({
            label: borough,
            data: hourData,
            borderColor: colorMap[borough] || COLORS.purple,
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 2,
            borderWidth: 2,
        });
    });

    if (speedChart) speedChart.destroy();
    speedChart = new Chart(document.getElementById("speedChart"), {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} mph`
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: "#1e2e3e" },
                    title: { display: true, text: "Speed (mph)", color: "#8899aa" }
                },
                x: { grid: { display: false } }
            },
        },
    });
}

// =========================================
//  Top Pickup Zones Chart
// =========================================
async function loadTopZones() {
    const data = await fetchAPI("/top-zones?limit=15");
    if (!data) return;

    const pickups = data.top_pickup;
    if (topPickupChart) topPickupChart.destroy();
    topPickupChart = new Chart(document.getElementById("topPickupChart"), {
        type: "bar",
        data: {
            labels: pickups.map(d => d.zone_name),
            datasets: [{
                label: "Pickup Count",
                data: pickups.map(d => d.trip_count),
                backgroundColor: pickups.map((d, i) => CHART_COLORS[i % CHART_COLORS.length]),
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: ctx => `Borough: ${pickups[ctx.dataIndex].borough}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "#1e2e3e" },
                    ticks: { callback: v => formatNumber(v) }
                },
                y: { grid: { display: false } }
            },
        },
    });
}

// =========================================
//  Weekday vs Weekend Comparison
// =========================================
async function loadWeekdayWeekend() {
    const data = await fetchAPI("/weekday-vs-weekend");
    if (!data) return;

    const labels = data.map(d => d.period);
    const metrics = ["avg_fare", "avg_distance", "avg_duration", "avg_speed"];
    const metricLabels = ["Avg Fare ($)", "Avg Distance (mi)", "Avg Duration (min)", "Avg Speed (mph)"];
    const metricColors = [COLORS.yellow, COLORS.blue, COLORS.green, COLORS.red];

    if (weekdayWeekendChart) weekdayWeekendChart.destroy();
    weekdayWeekendChart = new Chart(document.getElementById("weekdayWeekendChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: metrics.map((m, i) => ({
                label: metricLabels[i],
                data: data.map(d => Number(d[m]).toFixed(2)),
                backgroundColor: metricColors[i],
                borderRadius: 4,
            })),
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                    labels: { usePointStyle: true }
                }
            },
            scales: {
                y: {
                    grid: { color: "#1e2e3e" },
                    beginAtZero: true
                },
                x: { grid: { display: false } }
            },
        },
    });
}

// =========================================
//  Avg Fare by Hour Chart
// =========================================
async function loadFareHourChart() {
    const data = await fetchAPI("/hourly");
    if (!data) return;

    const labels = data.map(d => {
        const h = d.hour;
        return h === 0 ? "12AM" : h < 12 ? h + "AM" : h === 12 ? "12PM" : (h - 12) + "PM";
    });

    if (fareHourChart) fareHourChart.destroy();
    fareHourChart = new Chart(document.getElementById("fareHourChart"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Avg Fare",
                    data: data.map(d => d.avg_fare),
                    borderColor: COLORS.yellow,
                    backgroundColor: "rgba(247, 201, 72, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                },
                {
                    label: "Avg Tip",
                    data: data.map(d => d.avg_tip),
                    borderColor: COLORS.green,
                    backgroundColor: "rgba(69, 179, 105, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                    labels: { usePointStyle: true }
                }
            },
            scales: {
                y: {
                    grid: { color: "#1e2e3e" },
                    title: { display: true, text: "Amount ($)", color: "#8899aa" }
                },
                x: { grid: { display: false } }
            },
        },
    });
}
