// =====================================================
// 8W MOUNTAIN DETAILS
// =====================================================


// =====================================================
// API
// =====================================================

const API_BASE =
    "https://avalanche-prediction-8w-api.onrender.com";


// =====================================================
// GET MOUNTAIN ID
// =====================================================

const params =
    new URLSearchParams(window.location.search);

const rawId =
    params.get("id");


// VS CODE LIVE PREVIEW CAN SOMETIMES PRODUCE:
// ?id=1vscode-livepreview=true
//
// Extract only the number.

const match =
    rawId
        ? rawId.match(/^\d+/)
        : null;

const mountainId =
    match
        ? match[0]
        : null;


console.log(
    "8W Mountain ID:",
    mountainId
);


// =====================================================
// ELEMENTS
// =====================================================

const mountainName =
    document.getElementById("mountainName");

const mountainElevation =
    document.getElementById("mountainElevation");

const mountainRange =
    document.getElementById("mountainRange");

const mountainCountry =
    document.getElementById("mountainCountry");


const temperature =
    document.getElementById("temperature");

const wind =
    document.getElementById("wind");

const snowfall =
    document.getElementById("snowfall");

const snowDepth =
    document.getElementById("snowDepth");

const windGust =
    document.getElementById("windGust");

const visibility =
    document.getElementById("visibility");


const riskLevel =
    document.getElementById("riskLevel");

const riskScore =
    document.getElementById("riskScore");

const riskBar =
    document.getElementById("riskBar");

const confidence =
    document.getElementById("confidence");


const weatherScore =
    document.getElementById("weatherScore");

const terrainScore =
    document.getElementById("terrainScore");

const dataQuality =
    document.getElementById("dataQuality");


const contributors =
    document.getElementById("contributors");


// =====================================================
// LOAD MOUNTAIN
// =====================================================

async function loadMountain() {

    if (!mountainId) {

        mountainName.textContent =
            "MOUNTAIN NOT FOUND";

        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE}/api/peaks/${mountainId}`
            );


        if (!response.ok) {

            throw new Error(
                `Mountain API error: ${response.status}`
            );

        }


        const mountain =
            await response.json();


        console.log(
            "Mountain data:",
            mountain
        );


        // ---------------------------------------------
        // MOUNTAIN INFORMATION
        // ---------------------------------------------

        mountainName.textContent =
            mountain.name || "--";


        mountainElevation.textContent =
            mountain.elevation
                ? `${Number(
                    mountain.elevation
                ).toLocaleString()} m`
                : "--";


        mountainRange.textContent =
            mountain.range || "--";


        mountainCountry.textContent =
            mountain.country || "--";


        // ---------------------------------------------
        // LOAD WEATHER
        // ---------------------------------------------

        loadWeather(mountain);


        // -e--------------------------------------------
        // LOAD RISK
        // ---------------------------------------------

        loadRisk();

    }


    catch (error) {

        console.error(
            "Mountain loading error:",
            error
        );


        mountainName.textContent =
            "DATA UNAVAILABLE";

    }

}



// =====================================================
// WEATHER
// =====================================================

async function loadWeather(mountain) {

    try {

        const weatherURL =
            `https://api.open-meteo.com/v1/forecast` +
            `?latitude=${mountain.lat}` +
            `&longitude=${mountain.lon}` +
            `&elevation=${mountain.elevation}` +
            `&current=` +
            `temperature_2m,` +
            `relative_humidity_2m,` +
            `precipitation,` +
            `snowfall,` +
            `snow_depth,` +
            `wind_speed_80m,` +
            `wind_direction_80m,` +
            `wind_gusts_10m,` +
            `visibility` +
            `&timezone=UTC`;

        const response =
            await fetch(weatherURL);

        if (!response.ok) {

            throw new Error(
                `Weather API error: ${response.status}`
            );

        }

        const data =
            await response.json();

        const current =
            data.current;

        if (!current) {

            throw new Error(
                "No current weather data"
            );

        }

        // ---------------------------------------------
        // TEMPERATURE
        // ---------------------------------------------

        temperature.textContent =
            current.temperature_2m !== null &&
            current.temperature_2m !== undefined

                ? `${Number(
                    current.temperature_2m
                  ).toFixed(1)}°C`

                : "--";


        // ---------------------------------------------
        // WIND - 80 m
        // ---------------------------------------------

        wind.textContent =
            current.wind_speed_80m !== null &&
            current.wind_speed_80m !== undefined

                ? `${Number(
                    current.wind_speed_80m
                  ).toFixed(1)} km/h`

                : "--";


        // ---------------------------------------------
        // SNOWFALL
        // ---------------------------------------------

        snowfall.textContent =
            current.snowfall !== null &&
            current.snowfall !== undefined

                ? `${Number(
                    current.snowfall
                  ).toFixed(1)} cm`

                : "--";


        // ---------------------------------------------
        // SNOW DEPTH
        // ---------------------------------------------

        snowDepth.textContent =
            current.snow_depth !== null &&
            current.snow_depth !== undefined

                ? `${Number(
                    current.snow_depth
                  ).toFixed(2)} m`

                : "--";


        // ---------------------------------------------
        // WIND GUST
        // ---------------------------------------------

        windGust.textContent =
            current.wind_gusts_10m !== null &&
            current.wind_gusts_10m !== undefined

                ? `${Number(
                    current.wind_gusts_10m
                  ).toFixed(1)} km/h`

                : "--";


        // ---------------------------------------------
        // VISIBILITY
        // ---------------------------------------------

        if (
            current.visibility !== null &&
            current.visibility !== undefined
        ) {

            visibility.textContent =
                `${(
                    Number(current.visibility) / 1000
                ).toFixed(1)} km`;

        } else {

            visibility.textContent = "--";

        }

        console.log(
            "8W WEATHER:",
            current
        );

        console.log(
            "8W VISIBILITY:",
            current.visibility
        );

    }

    catch (error) {

        console.error(
            "Weather error:",
            error
        );

    }

}



// =====================================================
// RISK
// =====================================================

async function loadRisk() {

    try {


        const response =
            await fetch(
                `${API_BASE}/api/peaks/${mountainId}/risk`
            );


        if (!response.ok) {

            throw new Error(
                `Risk API error: ${response.status}`
            );

        }


        const result =
            await response.json();


        console.log(
            "Risk data:",
            result
        );


        const risk =
            result.risk;


        if (!risk) {

            throw new Error(
                "Risk object missing"
            );

        }


        // ---------------------------------------------
        // RISK LEVEL
        // ---------------------------------------------

        riskLevel.textContent =
            risk.risk_level || "--";



        // ---------------------------------------------
        // RISK SCORE
        // ---------------------------------------------

        if (
            risk.risk_index !== undefined &&
            risk.risk_index !== null
        ) {

            const score =
                Number(risk.risk_index);


            riskScore.textContent =
                score.toFixed(1);


            // Risk bar
            const safeScore =
                Math.max(
                    0,
                    Math.min(
                        100,
                        score
                    )
                );


            riskBar.style.width =
                `${safeScore}%`;

        }


        else {

            riskScore.textContent =
                "--";

        }



        // ---------------------------------------------
        // CONFIDENCE
        // ---------------------------------------------

        confidence.textContent =
            risk.confidence !== undefined &&
            risk.confidence !== null

                ? `${risk.confidence}%`

                : "--%";



        // ---------------------------------------------
        // WEATHER SCORE
        // ---------------------------------------------

        weatherScore.textContent =
            risk.weather_score !== undefined &&
            risk.weather_score !== null

                ? Number(
                    risk.weather_score
                ).toFixed(1)

                : "--";



        // ---------------------------------------------
        // TERRAIN SCORE
        // ---------------------------------------------

        terrainScore.textContent =
            risk.terrain_score !== undefined &&
            risk.terrain_score !== null

                ? Number(
                    risk.terrain_score
                ).toFixed(1)

                : "--";



        // ---------------------------------------------
        // DATA QUALITY
        // ---------------------------------------------

        dataQuality.textContent =
            risk.data_quality !== undefined &&
            risk.data_quality !== null

                ? `${risk.data_quality}%`

                : "--%";



        // ---------------------------------------------
        // CONTRIBUTORS
        // ---------------------------------------------

        displayContributors(
            risk.contributors
        );

    }


    catch (error) {

        console.error(
            "Risk error:",
            error
        );


        riskLevel.textContent =
            "DATA UNAVAILABLE";


        riskScore.textContent =
            "--";


        confidence.textContent =
            "--%";


        contributors.innerHTML =
            `<div class="contributor-empty">
                Risk data unavailable.
            </div>`;

    }

}



// =====================================================
// RISK CONTRIBUTORS
// =====================================================

function displayContributors(items) {


    contributors.innerHTML =
        "";


    if (
        !items ||
        items.length === 0
    ) {

        contributors.innerHTML =
            `<div class="contributor-empty">
                No significant contributors.
            </div>`;

        return;

    }



    items.forEach((item) => {


        const div =
            document.createElement("div");


        div.className =
            "contributor-item";



        // =================================================
        // BACKEND RETURNS STRING
        // =================================================

        if (
            typeof item === "string"
        ) {

            div.innerHTML = `
                <span class="contributor-dot">
                    ●
                </span>

                <span class="contributor-text">
                    ${item}
                </span>
            `;

        }



        // =================================================
        // BACKEND RETURNS OBJECT
        // =================================================

        else if (
            typeof item === "object"
        ) {


            const label =
                item.label ||
                item.factor ||
                item.name ||
                item.metric ||
                item.category ||
                "RISK FACTOR";


            const value =
                item.value ??
                item.current ??
                item.amount ??
                "";


            const severity =
                item.severity ||
                item.status ||
                "";



            div.innerHTML = `

                <span class="contributor-dot">
                    ●
                </span>

                <div class="contributor-content">

                    <strong>
                        ${label}
                    </strong>

                    ${
                        value !== ""
                            ? `<span>
                                ${value}
                               </span>`
                            : ""
                    }

                </div>

                ${
                    severity !== ""
                        ? `<small>
                            ${severity}
                           </small>`
                        : ""
                }

            `;

        }



        contributors.appendChild(
            div
        );

    });

}



// =====================================================
// START
// =====================================================

loadMountain();