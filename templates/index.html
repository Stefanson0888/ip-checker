<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IP Checker</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 30px; }
        .flag { margin-top: 20px; }
        #map { height: 400px; width: 80%; margin: 0 auto; margin-top: 20px; }
        .info-block { margin: 10px 0; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css" />
</head>
<body>
    <h1>Твоя IP-адреса: {{ ip }}</h1>

    <div class="info-block"><strong>Тип IP:</strong> {{ type }}</div>
    <div class="info-block"><strong>Провайдер (ISP):</strong> {{ isp }}</div>
    <div class="info-block"><strong>ASN:</strong> {{ asn }}</div>
    <div class="info-block"><strong>Хост-нейм:</strong> {{ hostname }}</div>

    <div class="info-block"><strong>Проксі:</strong> {{ "Так" if is_proxy else "Ні" }}</div>
    <div class="info-block"><strong>VPN:</strong> {{ "Так" if is_vpn else "Ні" }}</div>
    <div class="info-block"><strong>Tor:</strong> {{ "Так" if is_tor else "Ні" }}</div>

    <div class="info-block"><strong>Браузер:</strong> {{ browser }}</div>
    <div class="info-block"><strong>Операційна система:</strong> {{ os }}</div>
    <div class="info-block"><strong>User-Agent:</strong> {{ user_agent }}</div>

    <div class="info-block"><strong>Місто:</strong> {{ city }}</div>
    <div class="info-block"><strong>Регіон:</strong> {{ region }}</div>
    <div class="info-block"><strong>Країна:</strong> {{ country }}</div>
    <div class="info-block"><strong>Код країни:</strong> {{ country_code }}</div>
    <div class="info-block"><strong>Часовий пояс:</strong> {{ timezone }}</div>
    <div class="info-block"><strong>Поштовий індекс (ZIP):</strong> {{ zip }}</div>
    <div class="info-block"><strong>Валюта:</strong> {{ currency }}</div>

    <div class="info-block"><strong>Мови:</strong> 
        {% if languages %}
            {{ ", ".join(languages) }}
        {% else %}
            Невідомо
        {% endif %}
    </div>

    {% if flag_url %}
        <img src="{{ flag_url }}" alt="Country flag" width="100" class="flag">
    {% else %}
        <p>Прапор не знайдено</p>
    {% endif %}

    {% if latitude and longitude %}
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([{{ latitude }}, {{ longitude }}], 10);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            L.marker([{{ latitude }}, {{ longitude }}]).addTo(map)
                .bindPopup("Ти тут!")
                .openPopup();
        </script>
    {% endif %}
</body>
</html>
