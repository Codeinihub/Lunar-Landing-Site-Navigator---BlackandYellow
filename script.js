
 // ===================================
 // EARTH DETECTIVE - SEARCH FUNCTION
 // ===================================

function searchLocation() {

    const input = document.getElementById("locationInput");
    const result = document.getElementById("result");

    const location = input.value.trim();

    const startTime = document.getElementById("startTime").value;
    const endTime = document.getElementById("endTime").value;

    if (location === "" && !selectedBounds && !locationMarker) {
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

    let pointInformation = "";

    if (locationMarker) {
        const point = locationMarker.getLatLng();

        pointInformation = `
            <p><strong>Latitude:</strong> ${point.lat.toFixed(4)}°</p>
            <p><strong>Longitude:</strong> ${point.lng.toFixed(4)}°</p>
        `;
    }

    result.innerHTML = `
        <h3>EARTH DATA EXPLORATION</h3>

        <p><strong>Location:</strong>
        ${escapeHTML(location || "Custom map selection")}</p>

        ${regionInformation}
        ${pointInformation}

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

let selectedBounds = null;


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

        // Disable normal left-button map dragging
        dragging: false,

        scrollWheelZoom: true,

        doubleClickZoom: true

    });


    // ===================================
    // MAP IMAGERY
    // ===================================

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
    // INTERACTION VARIABLES
    // ===================================

    let interaction = null;

    let moved = false;

    let startPixel = null;

    let startLatLng = null;

    const DRAG_THRESHOLD = 5;


    // ===================================
    // DISABLE RIGHT-CLICK MENU
    // ===================================

    map.getContainer().addEventListener(
        "contextmenu",
        function(e) {

            e.preventDefault();

        }
    );


    // ===================================
    // MOUSE DOWN
    // ===================================

    map.on("mousedown", function(e) {

        // LEFT CLICK: SELECTION MODE

        if (e.originalEvent.button === 0) {

            interaction = "left";

            moved = false;

            startPixel = map.mouseEventToContainerPoint(
                e.originalEvent
            );

            startLatLng = e.latlng;

        }


        // RIGHT CLICK: NAVIGATION MODE

        else if (e.originalEvent.button === 2) {

            interaction = "right";

            moved = false;

            startPixel = map.mouseEventToContainerPoint(
                e.originalEvent
            );

            startLatLng = e.latlng;

        }

    });


    // ===================================
    // MOUSE MOVE
    // ===================================

    map.on("mousemove", function(e) {

        if (!interaction || !startPixel) return;

        const currentPixel = map.mouseEventToContainerPoint(
            e.originalEvent
        );

        const distance = startPixel.distanceTo(currentPixel);

        if (distance > DRAG_THRESHOLD) {

            moved = true;

        }


        // LEFT DRAG: DRAW REGION

        if (interaction === "left" && moved) {

            if (locationMarker) {

                map.removeLayer(locationMarker);

                locationMarker = null;

            }

            if (!selectionRectangle) {

                selectionRectangle = L.rectangle(
                    [startLatLng, e.latlng],
                    {

                        color: "#f5c400",

                        weight: 2,

                        fillColor: "#f5c400",

                        fillOpacity: 0.2

                    }
                ).addTo(map);

            } else {

                selectionRectangle.setBounds(
                    L.latLngBounds(startLatLng, e.latlng)
                );

            }

        }


        // RIGHT DRAG: MOVE MAP

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


    // ===================================
    // FINISH INTERACTION
    // ===================================

    function finishInteraction(e) {

        if (!interaction) return;

        const currentInteraction = interaction;

        const wasMoved = moved;

        const originalPoint = startLatLng;

        const endPoint = map.mouseEventToLatLng(e);

        interaction = null;

        moved = false;

        startPixel = null;

        startLatLng = null;


        // LEFT CLICK: PLACE POINTER

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


        // LEFT DRAG: SELECT REGION ONLY

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


    // ===================================
    // RELEASE MOUSE
    // ===================================

    document.addEventListener("mouseup", function(e) {

        if (!interaction) return;

        const expectedButton =
            interaction === "left" ? 0 : 2;

        if (e.button !== expectedButton) return;

        finishInteraction(e);

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

    coordinates.textContent = "No region selected.";

    regionText.textContent = "Choose a geographical region";

});
