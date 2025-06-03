function toggleDetails() {
    const el = document.getElementById("additional-info");
    el.style.display = el.style.display === "none" ? "block" : "none";
}

function initMap(latitude, longitude) {
    const map = L.map('map').setView([latitude, longitude], 10);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    L.marker([latitude, longitude]).addTo(map)
        .bindPopup("Ти тут!")
        .openPopup();
}
