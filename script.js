

const API_URL = "https://earthdetective-blackandyellow.onrender.com";


let map = null;
let resultsMap = null;

let selectionRectangle = null;
let locationMarker = null;
let selectedBounds = null;

let chartInstances = {};

let lastSearch = null;

const regionToggle = document.getElementById("regionToggle");
const mapDropdown = document.getElementById("mapDropdown");
const regionText = document.getElementById("regionText");
const dropdownArrow = document.getElementById("dropdownArrow");
const coordinates = document.getElementById("coordinates");
const clearRegion = document.getElementById("clearRegion");


// ===================================
// SEARCH AND BACKEND CONNECTION
// ===================================

async function searchLocation() {

    const result = document.getElementById("result");
    const searchButton = document.getElementById("searchButton");

    const locationName =
        document.getElementById("locationInput").value.trim();

    const startDate =
        document.getElementById("startTime").value;

    const endDate =
        document.getElementById("endTime").value;

    const parameter =
        document.getElementById("parameterSelect").value;

    const temporalResolution =
        document.getElementById("resolutionSelect").value;


    result.classList.remove("error");

    // DATE VALIDATION

    if (!startDate || !endDate) {
        showError("Please select both a start date and an end date.");
        return;
    }

    if (endDate < startDate) {
        showError("The end date must be after the start date.");
        return;
    }

    const startYear = Number(startDate.slice(0, 4));
    const endYear = Number(endDate.slice(0, 4));

    if (startYear < 1981) {
        showError("NASA POWER analysis requires a start year of 1981 or later.");
        return;
    }

    if (endYear - startYear < 2) {
        showError("Please select a date range covering at least three calendar years for trend analysis.");
        return;
    }

    // LOCATION VALIDATION

    if (!locationMarker && !selectedBounds) {
        showError("Please select a point or region on the map.");
        return;
    }

    // GET COORDINATES

    let latitude;
    let longitude;

    if (selectedBounds) {
        latitude =
            (Number(selectedBounds.north) +
             Number(selectedBounds.south)) / 2;

        longitude =
            (Number(selectedBounds.east) +
             Number(selectedBounds.west)) / 2;
    } else {
        const point = locationMarker.getLatLng();

        latitude = point.lat;
        longitude = point.lng;
    }

    // BUILD BACKEND REQUEST

    const requestData = {
        temporal_resolution: temporalResolution,
        parameter: [parameter],
        latitude: latitude,
        longitude: longitude,
        start_year: startYear,
        end_year: endYear,
        min_completeness: 90,
        alpha: 0.05
    };

    lastSearch = {
        requestData,
        locationName,
        startDate,
        endDate,
        selectedBounds: selectedBounds
            ? { ...selectedBounds }
            : null,
        point: {
            latitude,
            longitude
        }
    };

    searchButton.disabled = true;
    searchButton.textContent = "ANALYZING...";

    result.textContent =
        "Connecting to NASA POWER through our backend. Please wait...";

    try {

        const response = await fetch(
            `${API_URL}/analysis/trends`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(requestData)
            }
        );

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(
                responseData.detail ||
                "The backend could not complete the analysis."
            );
        }

        displayDashboard(responseData, lastSearch);

    } catch (error) {

        console.error("Analysis error:", error);

        showError(
            error.message.includes("Failed to fetch")
                ? "Could not connect to the backend. Make sure FastAPI is running at " + API_URL
                : error.message
        );

    } finally {

        searchButton.disabled = false;
        searchButton.textContent = "SEARCH";

    }


    function showError(message) {
        result.classList.add("error");
        result.textContent = message;
    }

}


// ===================================
// DISPLAY DASHBOARD
// ===================================

function displayDashboard(data, search) {

    const parameterName =
        search.requestData.parameter[0];

    const parameterData =
        data.parameters[parameterName];

    if (!parameterData) {
        alert("The backend did not return the selected parameter.");
        return;
    }

    const analysis =
        parameterData.trend_analysis;

    const methods = analysis.methods;

    const linear = methods.linear_regression;
    const sens = methods.sens_slope;
    const mannKendall = methods.mann_kendall;

    // SWITCH PAGES

    document.getElementById("homePage").classList.add("hidden");
    document.getElementById("resultsPage").classList.remove("hidden");

    window.scrollTo(0, 0);

    // DATE RANGE

    document.getElementById("dashboardDateRange").textContent =
        `${search.startDate} → ${search.endDate}`;

    // SUMMARY

    const parameterLabels = {
        T2M: "Temperature",
        T2M_MAX: "Maximum Temperature",
        T2M_MIN: "Minimum Temperature",
        PRECTOTCORR: "Rainfall",
        RH2M: "Relative Humidity",
        WS10M: "Wind Speed",
        ALLSKY_SFC_SW_DWN: "Solar Radiation"
    };

    document.getElementById("summaryParameter").textContent =
        parameterLabels[parameterName] || parameterName;

    document.getElementById("summaryResolution").textContent =
        search.requestData.temporal_resolution.toUpperCase();

    document.getElementById("summaryCoordinates").textContent =
        `${search.point.latitude.toFixed(3)}, ${search.point.longitude.toFixed(3)}`;

    document.getElementById("summaryDirection").textContent =
        formatDirection(analysis.summary.observed_direction);

    document.getElementById("summaryPValue").textContent =
        Number(mannKendall.p_value).toFixed(5);

    document.getElementById("summaryCompleteness").textContent =
        `${parameterData.quality.completeness_percent}%`;

    const significanceStatus =
        document.getElementById("significanceStatus");

    significanceStatus.textContent =
        mannKendall.is_significant
            ? "A statistically significant trend was detected at the selected significance level."
            : "No statistically significant trend was detected at the selected significance level.";

    // LOCATION LABEL

    document.getElementById("mapLocationLabel").textContent =
        search.locationName || "Selected map location";

    // DRAW MAP

    initializeResultsMap(search);

    // DRAW GRAPHS

    drawMannKendallChart(mannKendall);
    drawLinearChart(linear);
    drawSensChart(sens);

    // GRAPH DETAILS

    document.getElementById("mannKendallDetails").innerHTML = `
        <p><strong>Observed direction:</strong>
        ${escapeHTML(formatDirection(mannKendall.observed_direction))}</p>

        <p><strong>Trend result:</strong>
        ${escapeHTML(formatDirection(mannKendall.trend_direction))}</p>

        <p><strong>S statistic:</strong>
        ${Number(mannKendall.s_statistic).toFixed(2)}</p>

        <p><strong>Z statistic:</strong>
        ${Number(mannKendall.z_statistic).toFixed(4)}</p>

        <p><strong>P-value:</strong>
        ${Number(mannKendall.p_value).toFixed(5)}</p>

        <p><strong>Significant:</strong>
        ${mannKendall.is_significant ? "Yes" : "No"}</p>
    `;

    document.getElementById("linearDetails").innerHTML = `
        <p><strong>Direction:</strong>
        ${escapeHTML(formatDirection(linear.trend_direction))}</p>

        <p><strong>Slope per year:</strong>
        ${Number(linear.slope_per_year).toFixed(5)}</p>

        <p><strong>R-squared:</strong>
        ${Number(linear.r_squared).toFixed(5)}</p>

        <p><strong>Reference year:</strong>
        ${linear.reference_year}</p>
    `;

    document.getElementById("sensDetails").innerHTML = `
        <p><strong>Direction:</strong>
        ${escapeHTML(formatDirection(sens.trend_direction))}</p>

        <p><strong>Sen's slope per year:</strong>
        ${Number(sens.slope_per_year).toFixed(5)}</p>

        <p><strong>Reference year:</strong>
        ${sens.reference_year}</p>
    `;

    // ANNUAL DATA TABLE

    populateAnnualTable(parameterData.annual_data);

}


// ===================================
// FORMAT TREND DIRECTION
// ===================================

function formatDirection(direction) {

    if (!direction) return "Unavailable";

    return String(direction)
        .replaceAll("_", " ")
        .replace(/\b\w/g, character => character.toUpperCase());

}


// ===================================
// CHART HELPER
// ===================================

function createLineChart(canvasId, labels, datasets) {

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const canvas = document.getElementById(canvasId);

    chartInstances[canvasId] = new Chart(canvas, {

        type: "line",

        data: {
            labels: labels,
            datasets: datasets
        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {

                legend: {
                    labels: {
                        color: "#ddd"
                    }
                },

                tooltip: {
                    enabled: true
                }

            },

            scales: {

                x: {
                    title: {
                        display: true,
                        text: "Year",
                        color: "#f5c400"
                    },

                    ticks: {
                        color: "#aaa"
                    },

                    grid: {
                        color: "#292929"
                    }
                },

                y: {
                    title: {
                        display: true,
                        text: "Annual Average",
                        color: "#f5c400"
                    },

                    ticks: {
                        color: "#aaa"
                    },

                    grid: {
                        color: "#292929"
                    }
                }

            }

        }

    });

}


// ===================================
// MANN-KENDALL GRAPH
// ===================================

function drawMannKendallChart(result) {

    const labels = result.years_analyzed;

    const values = result.observed_values;

    createLineChart(
        "mannKendallChart",
        labels,
        [
            {
                label: "Annual observations",
                data: values,
                borderColor: "#f5c400",
                backgroundColor: "#f5c400",
                tension: 0.2,
                pointRadius: 4
            }
        ]
    );

}


// ===================================
// LINEAR REGRESSION GRAPH
// ===================================

function drawLinearChart(result) {

    createLineChart(
        "linearChart",
        result.years_analyzed,
        [
            {
                label: "Observed values",
                data: result.observed_values,
                borderColor: "#f5c400",
                backgroundColor: "#f5c400",
                tension: 0.2,
                pointRadius: 4
            },
            {
                label: "Linear regression",
                data: result.fitted_values,
                borderColor: "#45a6ff",
                backgroundColor: "#45a6ff",
                borderDash: [6, 5],
                pointRadius: 0,
                tension: 0
            }
        ]
    );

}


// ===================================
// SEN'S SLOPE GRAPH
// ===================================

function drawSensChart(result) {

    createLineChart(
        "sensChart",
        result.years_analyzed,
        [
            {
                label: "Observed values",
                data: result.observed_values,
                borderColor: "#f5c400",
                backgroundColor: "#f5c400",
                tension: 0.2,
                pointRadius: 4
            },
            {
                label: "Sen's slope",
                data: result.fitted_values,
                borderColor: "#4dd599",
                backgroundColor: "#4dd599",
                borderDash: [6, 5],
                pointRadius: 0,
                tension: 0
            }
        ]
    );

}


// ===================================
// ANNUAL DATA TABLE
// ===================================

function populateAnnualTable(data) {

    const table = document.getElementById("annualDataTable");

    table.innerHTML = "";

    data.forEach(row => {

        const tr = document.createElement("tr");

        const values = [
            row.year,
            row.annual_average === null
                ? "Unavailable"
                : Number(row.annual_average).toFixed(3),
            row.valid_observations,
            `${row.completeness_percent}%`,
            row.eligible_for_trend ? "Yes" : "No"
        ];

        values.forEach(value => {

            const td = document.createElement("td");

            td.textContent = value;

            tr.appendChild(td);

        });

        table.appendChild(tr);

    });

}


// ===================================
// RESULTS MAP
// ===================================

function initializeResultsMap(search) {

    if (resultsMap) {
        resultsMap.remove();
        resultsMap = null;
    }

    resultsMap = L.map("resultsMap").setView(
        [
            search.point.latitude,
            search.point.longitude
        ],
        5
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(resultsMap);

    if (search.selectedBounds) {

        L.rectangle(
            [
                [
                    Number(search.selectedBounds.south),
                    Number(search.selectedBounds.west)
                ],
                [
                    Number(search.selectedBounds.north),
                    Number(search.selectedBounds.east)
                ]
            ],
            {
                color: "#f5c400",
                weight: 3,
                fillColor: "#f5c400",
                fillOpacity: 0.15
            }
        ).addTo(resultsMap);

        L.marker([
            search.point.latitude,
            search.point.longitude
        ]).addTo(resultsMap)
            .bindPopup("Centre point used for NASA POWER analysis")
            .openPopup();

    } else {

        L.marker([
            search.point.latitude,
            search.point.longitude
        ]).addTo(resultsMap)
            .bindPopup("Selected analysis location")
            .openPopup();

    }

    setTimeout(() => {
        resultsMap.invalidateSize();
    }, 200);

}


// ===================================
// BACK TO SEARCH
// ===================================

document.getElementById("backButton").addEventListener(
    "click",
    function() {

        document.getElementById("resultsPage").classList.add("hidden");

        document.getElementById("homePage").classList.remove("hidden");

        window.scrollTo(0, 0);

        if (resultsMap) {
            resultsMap.remove();
            resultsMap = null;
        }

    }
);


// ===================================
// HTML SECURITY
// ===================================

function escapeHTML(text) {

    return String(text).replace(/[&<>"']/g, function(character) {

        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];

    });

}


// ===================================
// OPEN AND CLOSE MAP
// ===================================

regionToggle.addEventListener("click", function() {

    const isOpen = mapDropdown.classList.toggle("active");

    regionToggle.setAttribute("aria-expanded", isOpen);

    dropdownArrow.textContent = isOpen ? "▲" : "▼";

    if (isOpen && !map) {
        initializeMap();
    }

    if (isOpen && map) {
        setTimeout(() => map.invalidateSize(), 150);
    }

});


// ===================================
// INITIALIZE WORLD MAP
// ===================================

function initializeMap() {

    map = L.map("worldMap", {

        center: [20, 0],
        zoom: 2,
        minZoom: 2,
        maxZoom: 7,
        maxBounds: [[-85, -180], [85, 180]],
        maxBoundsViscosity: 1,
        dragging: false,
        scrollWheelZoom: true,
        doubleClickZoom: true

    });

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            noWrap: true
        }
    ).addTo(map);

    // GRIDLINES

    for (let lat = -75; lat <= 75; lat += 15) {

        L.polyline(
            [[lat, -180], [lat, 180]],
            {
                color: "#eab308",
                weight: 0.7,
                opacity: 0.7,
                interactive: false
            }
        ).addTo(map);

    }

    for (let lng = -180; lng <= 180; lng += 15) {

        L.polyline(
            [[-85, lng], [85, lng]],
            {
                color: "#eab308",
                weight: 0.7,
                opacity: 0.7,
                interactive: false
            }
        ).addTo(map);

    }

    // MAP INTERACTION

    let interaction = null;
    let moved = false;
    let startPixel = null;
    let startLatLng = null;

    const DRAG_THRESHOLD = 5;

    map.getContainer().addEventListener(
        "contextmenu",
        event => event.preventDefault()
    );

    map.on("mousedown", function(e) {

        if (e.originalEvent.button === 0) {

            interaction = "left";
            moved = false;

            startPixel = map.mouseEventToContainerPoint(
                e.originalEvent
            );

            startLatLng = e.latlng;

        } else if (e.originalEvent.button === 2) {

            interaction = "right";
            moved = false;

            startPixel = map.mouseEventToContainerPoint(
                e.originalEvent
            );

            startLatLng = e.latlng;

        }

    });

    map.on("mousemove", function(e) {

        if (!interaction || !startPixel) return;

        const currentPixel = map.mouseEventToContainerPoint(
            e.originalEvent
        );

        const distance = startPixel.distanceTo(currentPixel);

        if (distance > DRAG_THRESHOLD) {
            moved = true;
        }

        // LEFT DRAG: DRAW RECTANGLE

        if (interaction === "left" && moved) {

            if (locationMarker) {
                map.removeLayer(locationMarker);
                locationMarker = null;
            }

            const bounds = L.latLngBounds(
                startLatLng,
                e.latlng
            );

            if (!selectionRectangle) {

                selectionRectangle = L.rectangle(
                    bounds,
                    {
                        color: "#f5c400",
                        weight: 2,
                        fillColor: "#f5c400",
                        fillOpacity: 0.2
                    }
                ).addTo(map);

            } else {

                selectionRectangle.setBounds(bounds);

            }

        }

        // RIGHT DRAG: PAN MAP

        if (interaction === "right" && moved) {

            const dx = currentPixel.x - startPixel.x;
            const dy = currentPixel.y - startPixel.y;

            map.panBy(
                [-dx, -dy],
                { animate: false }
            );

            startPixel = currentPixel;

        }

    });

    // FINISH INTERACTION

    function finishInteraction(event) {

        if (!interaction) return;

        const currentInteraction = interaction;
        const wasMoved = moved;
        const originalPoint = startLatLng;

        const pixel = map.mouseEventToContainerPoint(event);
        const endPoint = map.containerPointToLatLng(pixel);

        interaction = null;
        moved = false;
        startPixel = null;
        startLatLng = null;

        // LEFT CLICK: SELECT POINT

        if (currentInteraction === "left" && !wasMoved) {

            if (selectionRectangle) {
                map.removeLayer(selectionRectangle);
                selectionRectangle = null;
            }

            if (locationMarker) {
                map.removeLayer(locationMarker);
            }

            selectedBounds = null;

            locationMarker = L.marker(originalPoint).addTo(map);

            locationMarker.bindPopup(`
                <strong>SELECTED LOCATION</strong><br>
                Latitude: ${originalPoint.lat.toFixed(4)}°<br>
                Longitude: ${originalPoint.lng.toFixed(4)}°
            `).openPopup();

            coordinates.innerHTML = `
                <strong>SELECTED POINT</strong><br>
                Latitude: ${originalPoint.lat.toFixed(4)}°<br>
                Longitude: ${originalPoint.lng.toFixed(4)}°
            `;

            regionText.textContent = "Exact Location Selected";

        }

        // LEFT DRAG: SELECT RECTANGLE

        else if (currentInteraction === "left" && wasMoved) {

            const bounds = L.latLngBounds(
                originalPoint,
                endPoint
            );

            selectedBounds = {
                north: bounds.getNorth().toFixed(2),
                south: bounds.getSouth().toFixed(2),
                east: bounds.getEast().toFixed(2),
                west: bounds.getWest().toFixed(2)
            };

            if (locationMarker) {
                map.removeLayer(locationMarker);
                locationMarker = null;
            }

            coordinates.innerHTML = `
                <strong>SELECTED REGION</strong><br>
                North: ${selectedBounds.north}°<br>
                South: ${selectedBounds.south}°<br>
                East: ${selectedBounds.east}°<br>
                West: ${selectedBounds.west}°
            `;

            regionText.textContent = "Custom Region Selected";

        }

    }

    document.addEventListener("mouseup", function(event) {

        if (!interaction) return;

        const expectedButton =
            interaction === "left" ? 0 : 2;

        if (event.button !== expectedButton) return;

        finishInteraction(event);

    });

}


// ===================================
// CLEAR SELECTION
// ===================================

clearRegion.addEventListener("click", function() {

    if (selectionRectangle && map) {
        map.removeLayer(selectionRectangle);
        selectionRectangle = null;
    }

    if (locationMarker && map) {
        map.removeLayer(locationMarker);
        locationMarker = null;
    }

    selectedBounds = null;

    coordinates.textContent = "No region selected.";

    regionText.textContent = "Choose a geographical region";

});
