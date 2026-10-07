const API_BASE = "https://avalanche-prediction-8w-api.onrender.com";
async function getMountainRisk(mountainId) {

    try {

        const response = await fetch(
            `${API_BASE}/api/peaks/${mountainId}/risk`
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        return await response.json();

    } catch (error) {

        console.error(
            "Risk API error:",
            error
        );

        return null;
    }
}
/* =========================================================
   8W MOUNTAIN RISK INTELLIGENCE
   Frontend V2
========================================================= */


/* =========================================================
   GLOBAL STATE
========================================================= */

let selectedPeak = peaks[0];


/* =========================================================
   DOM ELEMENTS
========================================================= */

const peakGrid = document.getElementById("peakGrid");

const detailName = document.getElementById("detailName");
const detailLocation = document.getElementById("detailLocation");
const detailElevation = document.getElementById("detailElevation");
const detailRange = document.getElementById("detailRange");
const detailRegion = document.getElementById("detailRegion");
const detailAscent = document.getElementById("detailAscent");

const temperature = document.getElementById("temperature");
const wind = document.getElementById("wind");
const snowfall = document.getElementById("snowfall");
const visibility = document.getElementById("visibility");

const weatherLoading = document.getElementById("weatherLoading");

const riskValue = document.getElementById("riskValue");
const riskScore = document.getElementById("riskScore");
const riskBar = document.getElementById("riskBar");

const riskFactors = document.getElementById("riskFactors");
const snowDepth =
    document.getElementById("snowDepth");

const windGust =
    document.getElementById("windGust");

const riskAssessment =
    document.getElementById("riskAssessment");

const riskConfidence =
    document.getElementById("riskConfidence");


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    renderPeaks();
});

/* =========================================================
   RENDER PEAK CARDS
========================================================= */

function renderPeaks() {

    peakGrid.innerHTML = "";

    peaks.forEach((peak, index) => {

        const card = document.createElement("button");

        card.className = "peak-card";

        card.dataset.id = peak.id;

        card.innerHTML = `

            <div class="peak-number">
                ${String(index + 1).padStart(2, "0")}
            </div>

            <div class="peak-info">

                <h3>
                    ${peak.shortName}
                </h3>

                <p>
                    ${peak.elevation.toLocaleString()} m
                </p>

            </div>

            <div class="peak-arrow">
                →
            </div>

        `;

       card.addEventListener("click", () => {
    const mountainId = peak.dbId ?? peak.id;

    window.location.href = `mountain.html?id=${mountainId}`;
});
        peakGrid.appendChild(card);

    });

}


/* =========================================================
   SELECT PEAK
========================================================= */

function selectPeak(peak) {

    selectedPeak = peak;

    updateActiveCard(peak.id);

    updatePeakDetails(peak);

    resetWeather();

    fetchWeather(peak);

}


/* =========================================================
   ACTIVE CARD
========================================================= */

function updateActiveCard(id) {

    document.querySelectorAll(".peak-card").forEach(card => {

        card.classList.remove("active");

    });

    const activeCard = document.querySelector(
        `.peak-card[data-id="${id}"]`
    );

    if (activeCard) {

        activeCard.classList.add("active");

    }

}


/* =========================================================
   UPDATE DETAILS
========================================================= */

function updatePeakDetails(peak) {

    detailName.textContent = peak.name;

    detailLocation.textContent = peak.country;

    detailElevation.textContent =
        `${peak.elevation.toLocaleString()} m`;

    detailRange.textContent = peak.range;

    detailRegion.textContent = peak.region;

    detailAscent.textContent =
        peak.firstAscent;

}


/* =========================================================
   RESET WEATHER
========================================================= */
function resetWeather() {

    weatherLoading.style.display = "block";

    temperature.textContent = "--";
    wind.textContent = "--";
    snowfall.textContent = "--";
    visibility.textContent = "--";

    if (snowDepth) snowDepth.textContent = "--";
    if (windGust) windGust.textContent = "--";

    riskValue.textContent = "ANALYZING";
    riskScore.textContent = "--";
    riskBar.style.width = "0%";

    if (riskAssessment) {
        riskAssessment.textContent = "WAITING FOR DATA";
    }

    if (riskConfidence) {
        riskConfidence.textContent = "--";
    }

    riskFactors.innerHTML = "";
}


/* =========================================================
   FETCH WEATHER
========================================================= */
async function fetchWeather(peak) {

    // =========================
    // LIVE WEATHER
    // =========================
    try {

        // Get mountain coordinates from our backend
        const peakResponse = await fetch(
            `https://avalanche-prediction-8w-api.onrender.com/api/peaks/${peak.dbId}`
        );

        if (!peakResponse.ok) {
            throw new Error(`Peak HTTP ${peakResponse.status}`);
        }

        const peakData = await peakResponse.json();

        const latitude = peakData.lat;
        const longitude = peakData.lon;

        // Ask Open-Meteo directly for current weather
        const weatherUrl =
            `https://api.open-meteo.com/v1/forecast` +
            `?latitude=${latitude}` +
            `&longitude=${longitude}` +
            `&current=` +
            `temperature_2m,` +
            `relative_humidity_2m,` +
            `precipitation,` +
            `snowfall,` +
            `snow_depth,` +
            `visibility,` +
            `wind_speed_80m,` +
            `wind_direction_10m,` +
            `wind_gusts_10m` +
            `&timezone=UTC`;

        const weatherResponse = await fetch(weatherUrl);

        if (!weatherResponse.ok) {
            throw new Error(`Weather HTTP ${weatherResponse.status}`);
        }

        const weatherResult = await weatherResponse.json();

        displayWeather(weatherResult);

        weatherLoading.style.display = "none";

    } catch (error) {

        console.error("Live weather error:", error);

        weatherLoading.textContent =
            "LIVE WEATHER TEMPORARILY UNAVAILABLE";

    }


    // =========================
    // RISK
    // =========================
    try {

        const riskResponse = await fetch(
            `https://avalanche-prediction-8w-api.onrender.com/api/peaks/${peak.dbId}/risk`
        );

        if (!riskResponse.ok) {
            throw new Error(`Risk HTTP ${riskResponse.status}`);
        }

        const riskResult = await riskResponse.json();

        displayBackendRisk(riskResult.risk);

    } catch (error) {

        console.error("Risk API error:", error);

        riskValue.textContent = "DATA UNAVAILABLE";
        riskScore.textContent = "--";
        riskBar.style.width = "0%";

    }

}
function displayBackendRisk(risk) {

    // ---------------------------------------------------------
    // Backend Risk Engine V2 values
    // ---------------------------------------------------------

    const score = Number(
        risk.risk_index ?? 0
    );

    const category =
        risk.risk_level ?? "UNKNOWN";

    const confidence = Number(
        risk.confidence ?? 0
    );

    const dataQuality = Number(
        risk.data_quality ?? 0
    );

    const weatherScore = Number(
        risk.weather_score ?? 0
    );

    const terrainScore = Number(
        risk.terrain_score ?? 0
    );

    const terrainAvailable =
        risk.terrain_available === true;

    const contributors =
        Array.isArray(risk.contributors)
            ? risk.contributors
            : [];


    // ---------------------------------------------------------
    // Main risk display
    // ---------------------------------------------------------

  riskScore.textContent =
    score.toFixed(1);

if (riskConfidence) {
    riskConfidence.textContent = `${confidence}%`;
}

riskValue.textContent =
    category;

if (riskAssessment) {
    riskAssessment.textContent = category;
}
    riskBar.style.width =
        `${Math.max(
            0,
            Math.min(score, 100)
        )}%`;

        /* =========================================================
   RISK VISUAL STATE
   ========================================================= */

const riskClassMap = {
    "LOW": "risk-low",
    "GUARDED": "risk-guarded",
    "MODERATE": "risk-moderate",
    "HIGH": "risk-high",
    "VERY HIGH": "risk-very-high"
};

const riskClass =
    riskClassMap[category] || "risk-guarded";


/* Remove previous state */

[
    "risk-low",
    "risk-guarded",
    "risk-moderate",
    "risk-high",
    "risk-very-high"
].forEach(className => {

    riskValue.classList.remove(className);
    riskScore.classList.remove(className);
    riskBar.classList.remove(className);

    if (riskAssessment) {
        riskAssessment.classList.remove(className);
    }

});


/* Apply current state */

riskValue.classList.add(riskClass);
riskScore.classList.add(riskClass);
riskBar.classList.add(riskClass);

if (riskAssessment) {
    riskAssessment.classList.add(riskClass);
}


    // ---------------------------------------------------------
    // Clear old contributors
    // ---------------------------------------------------------

    riskFactors.innerHTML = "";


    // ---------------------------------------------------------
    // Risk engine breakdown
    // ---------------------------------------------------------

    const breakdown = document.createElement(
        "div"
    );

    breakdown.className =
        "risk-factor";

    breakdown.innerHTML = `
        <span>WEATHER COMPONENT</span>
        <strong>${weatherScore.toFixed(1)} / 100</strong>
    `;

    riskFactors.appendChild(
        breakdown
    );


    const terrain = document.createElement(
        "div"
    );

    terrain.className =
        "risk-factor";

    terrain.innerHTML = `
        <span>TERRAIN COMPONENT</span>
        <strong>${terrainScore.toFixed(1)} / 100</strong>
    `;

    riskFactors.appendChild(
        terrain
    );


    // ---------------------------------------------------------
    // Confidence
    // ---------------------------------------------------------

    const confidenceItem =
        document.createElement("div");

    confidenceItem.className =
        "risk-factor";

    confidenceItem.innerHTML = `
        <span>CONFIDENCE</span>
        <strong>${confidence}%</strong>
    `;

    riskFactors.appendChild(
        confidenceItem
    );


    // ---------------------------------------------------------
    // Data quality
    // ---------------------------------------------------------

    const qualityItem =
        document.createElement("div");

    qualityItem.className =
        "risk-factor";

    qualityItem.innerHTML = `
        <span>DATA QUALITY</span>
        <strong>${dataQuality}%</strong>
    `;

    riskFactors.appendChild(
        qualityItem
    );


    // ---------------------------------------------------------
    // Terrain availability
    // ---------------------------------------------------------

    const terrainItem =
        document.createElement("div");

    terrainItem.className =
        "risk-factor";

    terrainItem.innerHTML = `
        <span>TERRAIN DATA</span>
        <strong>
            ${terrainAvailable
                ? "AVAILABLE"
                : "UNAVAILABLE"}
        </strong>
    `;

    riskFactors.appendChild(
        terrainItem
    );


    // ---------------------------------------------------------
    // Risk contributors
    // ---------------------------------------------------------

    if (contributors.length === 0) {

        const item =
            document.createElement("div");

        item.className =
            "risk-factor";

        item.innerHTML = `
            <span>DATA STATUS</span>
            <strong>
                No contributors available
            </strong>
        `;

        riskFactors.appendChild(item);

    } else {

        contributors.forEach(
            factor => {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "risk-factor";

                const name =
                    factor.factor ??
                    "Unknown factor";

                const value =
                    factor.value ??
                    "--";

                const severity =
                    factor.severity ??
                    "UNKNOWN";

                item.innerHTML = `
                    <span>${name}</span>
                    <strong>
                        ${value}
                        <small>
                            ${severity}
                        </small>
                    </strong>
                `;

                riskFactors.appendChild(
                    item
                );
            }
        );
    }


    // ---------------------------------------------------------
    // Debug information
    // ---------------------------------------------------------

    console.log(
        "8W Risk Engine V2:",
        {
            score,
            category,
            weatherScore,
            terrainScore,
            confidence,
            dataQuality,
            terrainAvailable,
            contributors
        }
    );
}

/* =========================================================
   DISPLAY WEATHER
========================================================= */
function displayWeather(data) {

    weatherLoading.style.display = "none";

    const current = data.current;

    if (!current) {
        return;
    }

    /* Temperature */
    temperature.textContent =
    current.temperature_2m != null
        ? `${Number(current.temperature_2m).toFixed(1)}°C`
        : "--";

    /* Wind */
    wind.textContent =
    current.wind_speed_80m != null
        ? `${Number(current.wind_speed_80m).toFixed(1)} km/h`
        : "--";

    /* Snowfall */
    snowfall.textContent =
        `${current.snowfall ?? 0} cm`;

    /* Visibility */
    const visibilityKm =
        current.visibility
            ? current.visibility / 1000
            : null;

    visibility.textContent =
        visibilityKm !== null
            ? `${visibilityKm.toFixed(1)} km`
            : "--";

    /* Snow depth */
    if (snowDepth) {
        snowDepth.textContent =
            current.snow_depth != null
                ? `${Number(current.snow_depth).toFixed(2)} m`
                : "--";
    }

    /* Wind gust */
    if (windGust) {
        windGust.textContent =
            current.wind_gusts_10m != null
                ? `${Number(current.wind_gusts_10m).toFixed(1)} km/h`
                : "--";
    }
}


/* =========================================================
   EXPERIMENTAL RISK ENGINE
========================================================= */

function calculateRisk(data) {

    const current = data.current;

    if (!current) {

        return;

    }


    let score = 0;

    const factors = [];


    /* -----------------------------------------
       SNOWFALL
    ----------------------------------------- */

    const snow =
        Number(current.snowfall || 0);

    if (snow >= 10) {

        score += 30;

        factors.push({
            name: "Snowfall",
            value: "HIGH"
        });

    }

    else if (snow >= 3) {

        score += 15;

        factors.push({
            name: "Snowfall",
            value: "MODERATE"
        });

    }

    else {

        score += 3;

        factors.push({
            name: "Snowfall",
            value: "LOW"
        });

    }


    /* -----------------------------------------
       WIND
    ----------------------------------------- */

    const windSpeed =
        Number(current.wind_speed_10m || 0);

    const gust =
        Number(current.wind_gusts_10m || 0);


    if (windSpeed >= 60 || gust >= 80) {

        score += 30;

        factors.push({
            name: "Wind",
            value: "HIGH"
        });

    }

    else if (windSpeed >= 35 || gust >= 50) {

        score += 18;

        factors.push({
            name: "Wind",
            value: "MODERATE"
        });

    }

    else {

        score += 5;

        factors.push({
            name: "Wind",
            value: "LOW"
        });

    }


    /* -----------------------------------------
       TEMPERATURE
    ----------------------------------------- */

    const temp =
        Number(current.temperature_2m);


    if (temp > 2) {

        score += 20;

        factors.push({
            name: "Temperature",
            value: "WARM"
        });

    }

    else if (temp > -5) {

        score += 10;

        factors.push({
            name: "Temperature",
            value: "MODERATE"
        });

    }

    else {

        score += 5;

        factors.push({
            name: "Temperature",
            value: "COLD"
        });

    }


    /* -----------------------------------------
       VISIBILITY
    ----------------------------------------- */

    const visibilityMeters =
        Number(current.visibility || 0);


    if (
        visibilityMeters > 0 &&
        visibilityMeters < 2000
    ) {

        score += 15;

    }

    else {

        score += 3;

    }


    score = Math.min(score, 100);


    displayRisk(score, factors);

}


/* =========================================================
   DISPLAY RISK
========================================================= */

function displayRisk(score, factors) {

    riskScore.textContent =
        `${score}`;

    riskBar.style.width =
        `${score}%`;


    let status;


    if (score >= 70) {

        status = "ELEVATED";

    }

    else if (score >= 40) {

        status = "MODERATE";

    }

    else {

        status = "LOW SIGNAL";

    }


    riskValue.textContent = status;


    riskFactors.innerHTML = "";


    factors.forEach(factor => {

        const item =
            document.createElement("div");

        item.innerHTML = `

            <span>
                ${factor.name}
            </span>

            <b>
                ${factor.value}
            </b>

        `;

        riskFactors.appendChild(item);

    });

}


/* =========================================================
   NAVBAR SCROLL
========================================================= */

window.addEventListener("scroll", () => {

    const navbar =
        document.querySelector(".navbar");

    if (window.scrollY > 40) {

        navbar.classList.add("scrolled");

    }

    else {

        navbar.classList.remove("scrolled");

    }

});
