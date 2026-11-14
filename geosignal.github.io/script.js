const form = document.getElementById("dataForm");

const statusMessage = document.getElementById("status");

const resultsSection = document.getElementById("results");

const submitButton = document.getElementById("submitButton");


form.addEventListener("submit", async function(event) {

    // Prevent the page from refreshing
    event.preventDefault();

    // Collect information from the form
    const latitude = Number(
        document.getElementById("latitude").value
    );

    const longitude = Number(
        document.getElementById("longitude").value
    );

    const variable = document.getElementById("variable").value;

    const startYear = Number(
        document.getElementById("startYear").value
    );

    const endYear = Number(
        document.getElementById("endYear").value
    );


    // Create the JSON object
    const requestData = {

        latitude: latitude,
        longitude: longitude,
        start_year: startYear,
        end_year: endYear,
        parameter: variable

    };


    // Show loading message
    statusMessage.textContent = "Retrieving NASA data...";

    resultsSection.hidden = true;

    submitButton.disabled = true;


    try {

        // Send request to FastAPI
        const response = await fetch(
            "http://127.0.0.1:8000/data",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(requestData)
            }
        );


        // Check whether the request succeeded
        if (!response.ok) {

            const error = await response.json();

            throw new Error(
                error.detail || "Something went wrong"
            );

        }


        // Convert response into JavaScript data
        const result = await response.json();


        // Display results
        displayResults(result);

        statusMessage.textContent =
            "NASA data successfully retrieved!";


    } catch (error) {

        statusMessage.textContent =
            "Error: " + error.message;

        console.error(error);

    } finally {

        submitButton.disabled = false;

    }

});


// Function to display NASA data
function displayResults(result) {

    resultsSection.hidden = false;

    document.getElementById(
        "observationCount"
    ).textContent = result.data.length;

    document.getElementById(
        "selectedVariable"
    ).textContent = result.parameter;


    const table = document.getElementById("dataTable");

    table.innerHTML = "";


    // Display the first 30 measurements
    result.data.slice(0, 30).forEach(item => {

        const row = document.createElement("tr");

        const dateCell = document.createElement("td");

        const valueCell = document.createElement("td");


        dateCell.textContent = item.date;

        valueCell.textContent =
            item.value === null ? "Missing" : item.value;


        row.appendChild(dateCell);

        row.appendChild(valueCell);

        table.appendChild(row);

    });

}