/**
 * api.js - API utilities, shared constants, and data fetching
 * ------------------------------------------------------------
 * Provides fetchAPI helper, number formatters, color palettes,
 * Chart.js global defaults, and the stats card loader.
 */

const API_BASE = "http://localhost:8080/api";

// Color palette (NYC taxi themed)
const COLORS = {
    yellow: "#f7c948",
    blue: "#4a90d9",
    green: "#45b369",
    red: "#e74c3c",
    purple: "#9b59b6",
    orange: "#f39c12",
    teal: "#1abc9c",
    pink: "#e84393",
};

const CHART_COLORS = [
    "#f7c948", "#4a90d9", "#45b369", "#e74c3c",
    "#9b59b6", "#f39c12", "#1abc9c", "#e84393",
    "#3498db", "#2ecc71", "#e67e22", "#1abc9c",
    "#8e44ad", "#d35400", "#16a085",
];

// Chart.js default styling for dark theme
Chart.defaults.color = "#8899aa";
Chart.defaults.borderColor = "#2a3a4a";
Chart.defaults.font.family = "'Segoe UI', sans-serif";

// =========================================
//  Helper: Fetch JSON from API
// =========================================
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(API_BASE + endpoint);
        if (!response.ok) throw new Error("API error: " + response.status);
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch " + endpoint, error);
        return null;
    }
}

// =========================================
//  Format numbers nicely
// =========================================
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toLocaleString();
}

function formatCurrency(num) {
    return "$" + Number(num).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

