
function searchLocation() {
    const input = document.getElementById("locationInput");
    const result = document.getElementById("result");

    const location = input.value.trim();

    if (location === "") {
        result.textContent = "Please enter a lunar location.";
        return;
    }

    result.innerHTML = `
        <h3>EXPLORATION TARGET</h3>
        <p>Selected location: ${escapeHTML(location)}</p>
        <p>Status: Search submitted.</p>
        <p>Further geographical analysis is required.</p>
    `;
}

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
