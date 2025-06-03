document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("toggle-map-btn");
    const mapContainer = document.getElementById("map-container");
  
    // Прочитай координати з елементів, переданих з бекенду
    const latitude = parseFloat(document.getElementById("latitude").textContent);
    const longitude = parseFloat(document.getElementById("longitude").textContent);
  
    let mapInitialized = false;
    let map;
  
    toggleButton.addEventListener("click", function () {
      if (mapContainer.style.display === "none") {
        mapContainer.style.display = "block";
  
        if (!mapInitialized) {
          map = L.map('map').setView([latitude, longitude], 10);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
          }).addTo(map);
          L.marker([latitude, longitude]).addTo(map)
            .bindPopup("You are here!")
            .openPopup();
  
          mapInitialized = true;
        } else {
          map.invalidateSize();
        }
      } else {
        mapContainer.style.display = "none";
      }
    });
  });
  