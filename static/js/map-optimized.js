// 🗺️ Оптимізована карта - винесений JavaScript
// Performance-optimized map loading for checkip.app

// 🚀 Оптимізована ініціалізація карти
function initializeOptimizedMap() {
    if (!window.mapConfig?.hasCoordinates) {
      console.log('❌ No coordinates for map');
      return;
    }
    
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
      console.log('❌ Map container not found');
      return;
    }
    
    console.log('🗺️ Starting optimized map initialization...');
    
    // 🎨 Створюємо красивий placeholder
    createOptimizedPlaceholder(mapContainer);
    
    // 📱 Мобільна оптимізація
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
      // Мобільні: тільки по кліку
      setupClickToLoad(mapContainer);
    } else {
      // Десктоп: lazy load + fallback
      setupIntersectionObserver(mapContainer);
    }
  }
  
  // 🎨 Оптимізований placeholder
  function createOptimizedPlaceholder(container) {
    const isMobile = window.innerWidth <= 768;
    const height = isMobile ? '250px' : '400px';
    const mapCity = window.mapConfig.city || 'Unknown';
    const mapCountry = window.mapConfig.country || 'Unknown';
    
    container.innerHTML = `
      <div class="map-placeholder-optimized" style="
        width: 100%; 
        height: ${height}; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 12px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        cursor: pointer;
        border: 2px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
      ">
        <div style="
          text-align: center; 
          color: white; 
          z-index: 2; 
          position: relative;
          user-select: none;
        ">
          <div style="
            font-size: 3rem; 
            margin-bottom: 15px; 
            animation: mapBounce 2s infinite ease-in-out;
          ">🗺️</div>
          <div style="
            font-size: 1.2rem; 
            font-weight: 700; 
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
          ">
            ${isMobile ? 'Натисніть' : 'Клікніть'} для карти
          </div>
          <div style="
            font-size: 0.9rem; 
            opacity: 0.9;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
          ">
            📍 ${mapCity}, ${mapCountry}
          </div>
        </div>
        
        <!-- Анімовані елементи -->
        <div style="
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle, rgba(255,255,255,0.1) 2px, transparent 2px);
          background-size: 40px 40px;
          animation: mapRotate 30s linear infinite;
          opacity: 0.5;
        "></div>
      </div>
    `;
    
    // hover ефекти
    const placeholder = container.querySelector('.map-placeholder-optimized');
    
    placeholder.addEventListener('mouseenter', () => {
      placeholder.style.transform = 'scale(1.02) translateY(-4px)';
      placeholder.style.boxShadow = '0 12px 48px rgba(102, 126, 234, 0.4)';
    });
    
    placeholder.addEventListener('mouseleave', () => {
      placeholder.style.transform = 'scale(1) translateY(0)';
      placeholder.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.3)';
    });
    
    console.log('✅ Optimized placeholder created');
  }
  
  // 🖱️ Click to load для мобільних
  function setupClickToLoad(container) {
    const placeholder = container.querySelector('.map-placeholder-optimized');
    
    placeholder.addEventListener('click', () => {
      console.log('📱 Mobile click - loading map...');
      loadOptimizedMap(container);
    }, { once: true });
  }
  
  // 👁️ Intersection Observer для десктопу
  function setupIntersectionObserver(container) {
    if (!('IntersectionObserver' in window)) {
      // Fallback для старих браузерів
      setTimeout(() => setupClickToLoad(container), 1000);
      return;
    }
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          console.log('👁️ Map in viewport - loading...');
          
          // Затримка для кращого UX
          setTimeout(() => {
            loadOptimizedMap(container);
          }, 800);
          
          observer.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      rootMargin: '100px',
      threshold: 0.2
    });
    
    observer.observe(container);
    
    // Fallback click
    setupClickToLoad(container);
    
    console.log('✅ Intersection observer setup');
  }
  
  // 🗺️ Завантаження оптимізованої карти
  function loadOptimizedMap(container) {
    console.log('🚀 Loading optimized Leaflet map...');
    
    // Loading стан
    const placeholder = container.querySelector('.map-placeholder-optimized');
    placeholder.style.background = 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)';
    placeholder.innerHTML = `
      <div style="text-align: center; color: white;">
        <div style="font-size: 3rem; margin-bottom: 15px; animation: mapSpin 1s linear infinite;">⏳</div>
        <div style="font-size: 1.1rem; font-weight: 600;">Завантаження карти...</div>
      </div>
    `;
    
    // ⚡ Lazy load Leaflet resources
    loadLeafletResources().then(() => {
      createLeafletMap(container);
    }).catch(error => {
      console.error('❌ Map loading failed:', error);
      showMapError(container);
    });
  }
  
  // 📦 Lazy loading Leaflet ресурсів
  function loadLeafletResources() {
    return new Promise((resolve, reject) => {
      // Перевіряємо чи Leaflet вже завантажений
      if (window.L) {
        resolve();
        return;
      }
      
      console.log('📦 Loading Leaflet resources...');
      
      // Завантажуємо CSS
      const css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = 'https://unpkg.com/leaflet@1.9.3/dist/leaflet.css';
      css.crossOrigin = '';
      document.head.appendChild(css);
      
      // Завантажуємо JS
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.3/dist/leaflet.js';
      script.async = true;
      script.crossOrigin = '';
      
      script.onload = () => {
        console.log('✅ Leaflet loaded successfully');
        resolve();
      };
      
      script.onerror = () => {
        console.error('❌ Failed to load Leaflet');
        reject(new Error('Leaflet loading failed'));
      };
      
      document.head.appendChild(script);
    });
  }
  
  // 🗺️ Створення Leaflet карти
  function createLeafletMap(container) {
    try {
      console.log('🗺️ Creating Leaflet map instance...');
      
      const mapCoords = window.mapConfig.coords;
      const mapZoom = window.mapConfig.zoom || 12;
      const mapCity = window.mapConfig.city || 'Unknown';
      const mapCountry = window.mapConfig.country || 'Unknown';
      
      // Очищуємо container
      container.innerHTML = '';
      
      // Створюємо карту з оптимізованими налаштуваннями
      const map = L.map(container, {
        center: mapCoords,
        zoom: mapZoom,
        zoomControl: false,
        attributionControl: false,
        preferCanvas: true,
        renderer: L.canvas(),
        // Performance налаштування
        wheelPxPerZoomLevel: 120,
        zoomAnimationThreshold: 4
      });
      
      // ⚡ Optimized tile layer
      const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 18,
        crossOrigin: true,
        // Performance оптимізації
        updateWhenIdle: true,
        updateWhenZooming: false,
        keepBuffer: 2,
        // Faster loading
        subdomains: ['a', 'b', 'c']
      });
      
      tileLayer.addTo(map);
      
      // 📍 Оптимізований маркер
      const markerIcon = L.divIcon({
        className: 'custom-marker-optimized',
        html: `
          <div style="
            background: #ef4444; 
            width: 20px; 
            height: 20px; 
            border-radius: 50%; 
            border: 3px solid white; 
            box-shadow: 0 3px 12px rgba(239, 68, 68, 0.4);
            position: relative;
          ">
            <div style="
              position: absolute;
              top: -5px;
              left: -5px;
              width: 30px;
              height: 30px;
              border-radius: 50%;
              background: rgba(239, 68, 68, 0.3);
              animation: markerPulse 2s infinite;
            "></div>
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });
      
      // Додаємо маркер
      const marker = L.marker(mapCoords, { 
        icon: markerIcon,
        riseOnHover: true
      }).addTo(map);
      
      // 💬 Popup - міжнародний текст
      const youAreHereText = getLocalizedText('you_are_here');
      
      marker.bindPopup(`
        <div style="text-align: center; padding: 8px; min-width: 150px;">
          <div style="font-weight: 700; color: #1f2937; margin-bottom: 4px;">
            📍 ${youAreHereText}
          </div>
          <div style="color: #6b7280; font-size: 0.9rem;">
            ${mapCity}, ${mapCountry}
          </div>
        </div>
      `, {
        offset: L.point(0, -10),
        closeButton: false,
        autoClose: false,
        closeOnClick: false,
        className: 'custom-popup'
      }).openPopup();
      
      // Додаємо контроли через секунду
      setTimeout(() => {
        L.control.zoom({ 
          position: 'topright',
          zoomInTitle: 'Збільшити',
          zoomOutTitle: 'Зменшити'
        }).addTo(map);
        
        L.control.attribution({ 
          position: 'bottomright',
          prefix: ''
        }).addTo(map);
      }, 1000);
      
      console.log('✅ Map created successfully');
      
      // Analytics
      if (window.queueAnalytics) {
        queueAnalytics({
          'event': 'map_loaded_optimized',
          'event_category': 'engagement',
          'event_label': 'leaflet_optimized'
        });
      }
      
    } catch (error) {
      console.error('❌ Map creation error:', error);
      showMapError(container);
    }
  }
  
  // 🌐 Локалізація тексту
  function getLocalizedText(key) {
    const translations = {
      'you_are_here': {
        'en': 'You are here',
        'de': 'Sie sind hier',
        'pl': 'Jesteś tutaj',
        'hi': 'आप यहाँ हैं',
        'uk': 'Ви тут',
        'ru': 'Вы здесь'
      }
    };
    
    const lang = window.mapConfig?.lang || 'en';
    return translations[key]?.[lang] || translations[key]?.['en'] || 'You are here';
  }
  
  // 🚨 Error state
  function showMapError(container) {
    container.innerHTML = `
      <div style="
        width: 100%; 
        height: 300px; 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
        border-radius: 12px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        color: white;
        text-align: center;
      ">
        <div>
          <div style="font-size: 3rem; margin-bottom: 15px;">❌</div>
          <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">
            Помилка завантаження карти
          </div>
          <div style="font-size: 0.9rem; opacity: 0.9;">
            Перевірте інтернет-з'єднання
          </div>
        </div>
      </div>
    `;
  }
  
  // 🚀 Ініціалізація при завантаженні сторінки
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeOptimizedMap);
  } else {
    setTimeout(initializeOptimizedMap, 200);
  }