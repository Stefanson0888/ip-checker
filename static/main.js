document.addEventListener("DOMContentLoaded", () => {
    fetch("https://ipapi.co/json/")
        .then(response => response.json())
        .then(data => {
            document.getElementById("ip").textContent = data.ip;
            document.getElementById("city").textContent = data.city;
            document.getElementById("country").textContent = data.country_name;
            document.getElementById("org").textContent = data.org;

            const map = L.map("map").setView([data.latitude, data.longitude], 10);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: '&copy; OpenStreetMap'
            }).addTo(map);
            L.marker([data.latitude, data.longitude]).addTo(map)
                .bindPopup(`Ваше розташування<br>${data.city}, ${data.country_name}`)
                .openPopup();
        })
        .catch(error => {
            document.getElementById("ip").textContent = "Не вдалося отримати дані";
            console.error(error);
        });
});

function toggleDetails() {
    const info = document.getElementById("additional-info");
    if (info.style.display === "none" || info.style.display === "") {
        info.style.display = "block";
    } else {
        info.style.display = "none";
    }
}
