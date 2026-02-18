/**
 * app.js - Main entry point
 * --------------------------
 * Declares global state, initializes the dashboard on page load,
 * and handles the trip table, pagination, and filter controls.
 * Depends on: api.js, charts.js, map.js
 */

// Chart instances (shared with charts.js via global scope)
let hourlyChart = null;
let dailyChart = null;
let boroughChart = null;
let paymentChart = null;
let fareChart = null;
let speedChart = null;
let topPickupChart = null;
let weekdayWeekendChart = null;
let fareHourChart = null;

// Map instances (shared with map.js via global scope)
let map = null;
let geoLayer = null;

// Pagination state
let currentPage = 1;
let totalPages = 1;

// =========================================
//  Initialize everything on page load
// =========================================
document.addEventListener("DOMContentLoaded", function () {
    // Populate hour filter dropdown
    const hourSelect = document.getElementById("filter-hour");
    for (let h = 0; h < 24; h++) {
        const option = document.createElement("option");
        option.value = h;
        const label = h === 0 ? "12 AM" : h < 12 ? h + " AM" : h === 12 ? "12 PM" : (h - 12) + " PM";
        option.textContent = label;
        hourSelect.appendChild(option);
    }

    // Load stats and all visualizations
    loadStats();
    loadHourlyChart();
    loadDailyChart();
    loadBoroughChart();
    loadPaymentChart();
    loadFareDistribution();
    loadSpeedAnalysis();
    loadTopZones();
    loadWeekdayWeekend();
    loadFareHourChart();
    loadTripsTable();
    loadMap();
});

// =========================================
//  Trip Table with Pagination
// =========================================
async function loadTripsTable(page) {
    if (page === undefined) page = currentPage;

    // Build query params from filters
    const params = new URLSearchParams();
    params.set("page", page);
    params.set("per_page", 50);

    const borough = document.getElementById("filter-borough").value;
    if (borough) params.set("borough", borough);

    const hour = document.getElementById("filter-hour").value;
    if (hour !== "") params.set("hour", hour);

    const day = document.getElementById("filter-day").value;
    if (day !== "") params.set("day", day);

    const payment = document.getElementById("filter-payment").value;
    if (payment) params.set("payment_type", payment);

    const minFare = document.getElementById("filter-min-fare").value;
    if (minFare) params.set("min_fare", minFare);

    const maxFare = document.getElementById("filter-max-fare").value;
    if (maxFare) params.set("max_fare", maxFare);

    const data = await fetchAPI("/trips?" + params.toString());
    if (!data) return;

    currentPage = data.page;
    totalPages = data.total_pages;

    // Update controls
    document.getElementById("table-info").textContent =
        `Showing ${data.trips.length} of ${data.total.toLocaleString()} trips`;
    document.getElementById("page-info").textContent =
        `Page ${currentPage} of ${totalPages}`;
    document.getElementById("btn-prev").disabled = currentPage <= 1;
    document.getElementById("btn-next").disabled = currentPage >= totalPages;

    // Populate table
    const tbody = document.getElementById("trips-body");
    tbody.innerHTML = "";

    data.trips.forEach(trip => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${trip.pickup_datetime}</td>
            <td>${trip.pickup_zone || "N/A"} <small style="color:#6b7b8b">(${trip.pickup_borough || ""})</small></td>
            <td>${trip.dropoff_zone || "N/A"} <small style="color:#6b7b8b">(${trip.dropoff_borough || ""})</small></td>
            <td>${trip.trip_distance}</td>
            <td>${trip.trip_duration_minutes}</td>
            <td>${formatCurrency(trip.fare_amount)}</td>
            <td>${formatCurrency(trip.tip_amount)}</td>
            <td>${formatCurrency(trip.total_amount)}</td>
            <td>${trip.speed_mph}</td>
            <td>${trip.passenger_count}</td>
        `;
        tbody.appendChild(row);
    });
}

