
// ===================================
// EARTH DETECTIVE - SEARCH FUNCTION
// ===================================

function searchLocation() {
    const input = document.getElementById("locationInput");
    const result = document.getElementById("result");

    const location = input.value.trim();

    const startTime = document.getElementById("startTime").value;
    const endTime = document.getElementById("endTime").value;

    if (location === "" && !selectedBounds) {
        result.textContent =
            "Please enter a location or select an area on the map.";
        return;
    }

    if (!startTime || !endTime) {
        result.textContent =
            "Please select both a start and end date and time.";
        return;
    }

    if (new Date(endTime) <= new Date(startTime)) {
        result.textContent =
            "The end date and time must be after the start date and time.";
        return;
    }

    const start = new Date(startTime).toLocaleString();
    const end = new Date(endTime).toLocaleString();

    let regionInformation = "";

    if (selectedBounds) {
        regionInformation = `
            <p><strong>North:</strong> ${selectedBounds.north}°</p>
            <p><strong>South:</strong> ${selectedBounds.south}°</p>
            <p><strong>East:</strong> ${selectedBounds.east}°</p>
            <p><strong>West:</strong> ${selectedBounds.west}°</p>
        `;
    }

    result.innerHTML = `
        <h3>EARTH DATA EXPLORATION</h3>

        <p><strong>Location:</strong>
        ${escapeHTML(location || "Custom map selection")}</p>

        ${regionInformation}

        <p><strong>Start:</strong> ${escapeHTML(start)}</p>
        <p><strong>End:</strong> ${escapeHTML(end)}</p>

        <p>Status: Search submitted.</p>
        <p>Environmental data analysis can now be connected.</p>
    `;
}


// ===================================
// HTML SECURITY
// ===================================

function escapeHTML(text) {
    return text.replace(/[&<>"']/g, function(character) {
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
// MAP VARIABLES
// ===================================

let map = null;
let selectionRectangle = null;
let locationMarker = null;
let startPoint = null;
let selectedBounds = null;
let isSelectingRegion = false;
let dragMoved = false;


// ===================================
// HTML ELEMENTS
// ===================================

const regionToggle = document.getElementById("regionToggle");
const mapDropdown = document.getElementById("mapDropdown");
const regionText = document.getElementById("regionText");
const dropdownArrow = document.getElementById("dropdownArrow");
const coordinates = document.getElementById("coordinates");
const clearRegion = document.getElementById("clearRegion");


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
        setTimeout(function() {
            map.invalidateSize();
        }, 150);
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
        dragging: false
    });

    // Add map imagery

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            noWrap: true
        }
    ).addTo(map);


    // ===================================
    // LATITUDE GRIDLINES
    // ===================================

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


    // ===================================
    // LONGITUDE GRIDLINES
    // ===================================

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


    // ===================================
    // CLICK AND DRAG TO SELECT REGION
    // ===================================

    map.on("mousedown", function(e) {

        if (e.originalEvent.button !== 0) return;

        isSelectingRegion = true;
        dragMoved = false;
        startPoint = e.latlng;

        if (selectionRectangle) {
            map.removeLayer(selectionRectangle);
        }

        selectionRectangle = L.rectangle(
            [startPoint, startPoint],
            {
                color: "#f5c400",
                weight: 2,
                fillColor: "#f5c400",
                fillOpacity: 0.2
            }
        ).addTo(map);

    });


    // ===================================
    // UPDATE RECTANGLE WHILE DRAGGING
    // ===================================

    map.on("mousemove", function(e) {

        if (!isSelectingRegion || !startPoint) return;

        if (map.distance(startPoint, e.latlng) > 100) {
            dragMoved = true;
        }

        if (selectionRectangle) {
            selectionRectangle.setBounds(
                L.latLngBounds(startPoint, e.latlng)
            );
        }

    });


    // ===================================
    // FINISH REGION SELECTION
    // ===================================

    map.on("mouseup", function(e) {

        if (!isSelectingRegion || !startPoint) return;

        isSelectingRegion = false;

        if (dragMoved) {

            const bounds = L.latLngBounds(
                startPoint,
                e.latlng
            );

            selectedBounds = {
                north: bounds.getNorth().toFixed(2),
                south: bounds.getSouth().toFixed(2),
                east: bounds.getEast().toFixed(2),
                west: bounds.getWest().toFixed(2)
            };

            coordinates.innerHTML = `
                <strong>SELECTED REGION</strong><br>
                North: ${selectedBounds.north}°<br>
                South: ${selectedBounds.south}°<br>
                East: ${selectedBounds.east}°<br>
                West: ${selectedBounds.west}°
            `;

            regionText.textContent = "Custom Region Selected";

        } else {

            // A click without dragging selects an exact point.

            if (selectionRectangle) {
                map.removeLayer(selectionRectangle);
                selectionRectangle = null;
            }

            selectedBounds = null;

            if (locationMarker) {
                map.removeLayer(locationMarker);
            }

            locationMarker = L.marker(startPoint).addTo(map);

            locationMarker.bindPopup(`
                <strong>SELECTED LOCATION</strong><br>
                Latitude: ${startPoint.lat.toFixed(4)}°<br>
                Longitude: ${startPoint.lng.toFixed(4)}°
            `).openPopup();

            coordinates.innerHTML = `
                <strong>SELECTED POINT</strong><br>
                Latitude: ${startPoint.lat.toFixed(4)}°<br>
                Longitude: ${startPoint.lng.toFixed(4)}°
            `;

            regionText.textContent = "Exact Location Selected";
        }

        startPoint = null;

    });


    // ===================================
    // HANDLE MOUSE RELEASE OUTSIDE MAP
    // ===================================

    document.addEventListener("mouseup", function(e) {

        if (!isSelectingRegion || !startPoint) return;

        if (!map.getContainer().contains(e.target)) {
            isSelectingRegion = false;

            if (selectionRectangle) {
                map.removeLayer(selectionRectangle);
                selectionRectangle = null;
            }

            startPoint = null;
        }

    });

}


// ===================================
// CLEAR REGION AND POINTER
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
    startPoint = null;
    isSelectingRegion = false;
    dragMoved = false;

    coordinates.textContent = "No region selected.";

    regionText.textContent = "Choose a geographical region";

});
