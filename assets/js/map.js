document.addEventListener("DOMContentLoaded", function () {
  // --- Safety Check ---
  if (typeof L === "undefined") {
    console.error("Leaflet (L) is not defined. Map cannot initialize.");
    const mapEl = document.getElementById("map");
    if (mapEl) {
      mapEl.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted p-4 text-center">
          <i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i>
          <p>Failed to load the map library. Please check your internet connection or try refreshing the page.</p>
        </div>
      `;
    }
    return;
  }

  // --- Map Initialization ---
  // --- Map Initialization ---

  // 1. Define Base Layers
  const standardLayer = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }
  );

  const satelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution:
        "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
    }
  );

  const satelliteLabels = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    {
      attribution: "",
    }
  );

  // Group Satellite + Labels
  const satelliteHybrid = L.layerGroup([satelliteLayer, satelliteLabels]);

  // 2. Define Weather Overlay Layers (Using secure proxy)
  const cloudsLayer = L.tileLayer('/api/proxy/tiles/clouds_new/{z}/{x}/{y}', {
    opacity: 0.8,
    maxZoom: 18
  });

  const precipLayer = L.tileLayer('/api/proxy/tiles/precipitation_new/{z}/{x}/{y}', {
    opacity: 0.7,
    maxZoom: 18
  });

  const tempLayer = L.tileLayer('/api/proxy/tiles/temp_new/{z}/{x}/{y}', {
    opacity: 0.6,
    maxZoom: 18
  });
  
  const windLayer = L.tileLayer('/api/proxy/tiles/wind_new/{z}/{x}/{y}', {
    opacity: 0.6,
    maxZoom: 18
  });
  
  const pressureLayer = L.tileLayer('/api/proxy/tiles/pressure_new/{z}/{x}/{y}', {
    opacity: 0.6,
    maxZoom: 18
  });


  // 3. Initialize Map with Default Layer
  const map = L.map("map", {
    center: [33.6844, 73.0479],
    zoom: 5,
    layers: [satelliteHybrid], // Default to Satellite
    attributionControl: false,
  });

  // 4. Add Layer Control
  const baseMaps = {
    "Standard": standardLayer,
    "Satellite": satelliteHybrid,
  };

  const overlayMaps = {
    "Clouds": cloudsLayer,
    "Precipitation": precipLayer,
    "Temperature": tempLayer,
    "Wind Speed": windLayer,
    "Pressure": pressureLayer
  };

  const layerControl = L.control.layers(baseMaps, overlayMaps, {
    position: "bottomleft",
  });

  // Override _initLayout (Same as before)
  const originalInitLayout = layerControl._initLayout;
  layerControl._initLayout = function () {
    originalInitLayout.call(this);
    L.DomEvent.off(this._container, "mouseenter", this.expand, this);
    L.DomEvent.off(this._container, "mouseleave", this.collapse, this);
  };

  layerControl.addTo(map);
  
  setTimeout(() => {
    map.invalidateSize();
  }, 100);

  const container = layerControl.getContainer();
  L.DomEvent.disableClickPropagation(container);
  L.DomEvent.disableScrollPropagation(container);

  container.addEventListener("mouseenter", function () {
    layerControl.expand();
  });

  container.addEventListener("click", function (e) {
    if (
      e.target.tagName === "INPUT" ||
      e.target.tagName === "LABEL" ||
      e.target.tagName === "SPAN"
    ) {
      return;
    }
    if (container.classList.contains("leaflet-control-layers-expanded")) {
      layerControl.collapse();
    } else {
      layerControl.expand();
    }
  });

  map.on("click", function () {
    layerControl.collapse();
  });

  // Custom Purple Marker Icon
  const purpleMarker = L.divIcon({
    className: "custom-div-icon",
    html: `<div style='background-color: #2f2f2f; width: 30px; height: 30px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'><div style='width: 10px; height: 10px; background: white; border-radius: 50%; position: absolute; top: 10px; left: 10px;'></div></div>`,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
  });

  let marker = L.marker([33.6844, 73.0479], { icon: purpleMarker }).addTo(map);

  // --- Favorites / Bookmarks Functionality ---
  
  // 1. Favorites State Helpers
  function getFavorites() {
    return JSON.parse(localStorage.getItem('synocast_favorites') || '[]');
  }

  function saveFavorite(name, lat, lon) {
    const favs = getFavorites();
    if (favs.some(f => f.name === name)) {
        ToastUtils.show("Already Saved", `${name} is already in your favorites.`, "info");
        return;
    }
    favs.push({ name, lat, lon });
    localStorage.setItem('synocast_favorites', JSON.stringify(favs));
    ToastUtils.show("Saved", `${name} added to favorites!`, "success");
    
    updateFavoriteIcon(name);
  }

  function removeFavorite(name) {
    let favs = getFavorites();
    favs = favs.filter(f => f.name !== name);
    localStorage.setItem('synocast_favorites', JSON.stringify(favs));
    
    // Refresh list if open
    const dropdown = document.querySelector('.favorites-list-dropdown');
    if (dropdown && !dropdown.classList.contains('d-none')) {
        renderFavoritesList(dropdown); // Re-render logic needed
    }
    
    const currentCity = document.getElementById("map-city")?.textContent;
    updateFavoriteIcon(currentCity);
  }

  // 2. Add Buttons to .map-controls (Grouping Bookmarks with Favorites)
  const mapControlsDiv = document.querySelector('.map-controls');
  if (mapControlsDiv) {
      
      // Wrapper for alignment
      const btnGroup = document.createElement('div');
      btnGroup.className = 'd-flex ms-2 position-relative';
      
      // A. "Add to Favorites" Button (Heart)
      const addFavBtn = document.createElement('button');
      addFavBtn.className = 'btn btn-white shadow-sm border rounded-circle d-flex align-items-center justify-content-center';
      addFavBtn.style.width = '42px';
      addFavBtn.style.height = '42px';
      addFavBtn.title = "Save this location";
      addFavBtn.innerHTML = '<i class="far fa-heart text-danger"></i>';
      addFavBtn.onclick = () => saveCurrentLocation();
      
      // B. "View Favorites" Button (Star) -> Replaces top-right control
      const viewFavBtn = document.createElement('button');
      viewFavBtn.className = 'btn btn-white shadow-sm border rounded-circle ms-2 d-flex align-items-center justify-content-center';
      viewFavBtn.style.width = '42px';
      viewFavBtn.style.height = '42px';
      viewFavBtn.title = "View Saved Locations";
      viewFavBtn.innerHTML = '<i class="fas fa-star text-warning"></i>';
      
      // Favorites Dropdown (Attached to View Button)
      const dropdown = document.createElement('div');
      dropdown.className = 'favorites-list-dropdown shadow-lg bg-white rounded-3 p-2 d-none';
      dropdown.style.position = 'absolute';
      dropdown.style.top = '100%'; // Render below the button
      dropdown.style.marginTop = '10px';
      dropdown.style.left = '0'; // Align left edge
      dropdown.style.width = '240px';
      dropdown.style.maxHeight = '300px';
      dropdown.style.overflowY = 'auto';
      dropdown.style.zIndex = '2000'; // Higher z-index to ensure visibility

      viewFavBtn.onclick = (e) => {
          e.stopPropagation();
          dropdown.classList.toggle('d-none');
          if (!dropdown.classList.contains('d-none')) {
              renderFavoritesList(dropdown);
          }
      };

      // Close dropdown when clicking outside
      document.addEventListener('click', (e) => {
          if (!viewFavBtn.contains(e.target) && !dropdown.contains(e.target)) {
              dropdown.classList.add('d-none');
          }
      });

      // Append everything
      btnGroup.appendChild(addFavBtn);
      btnGroup.appendChild(viewFavBtn);
      btnGroup.appendChild(dropdown);
      mapControlsDiv.appendChild(btnGroup);
      
      // Store ref for icon updates
      addFavBtn.id = 'map-add-fav-btn';
  }

  function renderFavoritesList(container) {
    const favs = getFavorites();
    container.innerHTML = '';
    
    if (favs.length === 0) {
        container.innerHTML = '<div class="text-muted small text-center py-2">No saved locations</div>';
        return;
    }

    const title = document.createElement('div');
    title.className = 'fw-bold mb-2 small text-secondary px-2 pt-1';
    title.textContent = 'MY PLACES';
    container.appendChild(title);

    favs.forEach(f => {
        const item = document.createElement('div');
        item.className = 'd-flex justify-content-between align-items-center p-2 rounded hover-bg-light cursor-pointer mb-1';
        item.innerHTML = `
            <span class="small fw-bold text-dark text-truncate" style="max-width: 140px;">${f.name}</span>
            <i class="fas fa-times text-muted small favorites-item-remove hover-text-danger p-1"></i>
        `;
        
        // Interaction
        item.addEventListener('click', (e) => {
             if (e.target.classList.contains('favorites-item-remove')) {
                 e.stopPropagation();
                 removeFavorite(f.name);
             } else {
                 map.setView([f.lat, f.lon], 16);
                 marker.setLatLng([f.lat, f.lon]);
                 updateWeather(f.lat, f.lon);
                 container.classList.add('d-none');
             }
        });
        
        container.appendChild(item);
    });
  }

  function saveCurrentLocation() {
      const cityEl = document.getElementById("map-city");
      const currentCity = cityEl ? cityEl.textContent : "Unknown Location";
      const center = map.getCenter();
      
      if (currentCity === "Loading..." || currentCity === "Unknown Location") {
          ToastUtils.show("Wait", "Please wait for location to load.", "warning");
          return;
      }
      saveFavorite(currentCity, center.lat, center.lng);
  }

  function updateFavoriteIcon(cityName) {
      if (!cityName) return;
      const favs = getFavorites();
      const isFav = favs.some(f => f.name === cityName);
      const btnIcon = document.querySelector('#map-add-fav-btn i');
      
      if(btnIcon) {
          if(isFav) {
              btnIcon.className = 'fas fa-heart text-danger';
          } else {
              btnIcon.className = 'far fa-heart text-danger';
          }
      }
  }

  // --- Location Handling integration with location_handler.js ---

  function setMapLocation(lat, lon, isCached) {
    map.setView([lat, lon], 16);
    marker.setLatLng([lat, lon]);
    updateWeather(lat, lon);
  }

  // 1. Listen for global location grant
  window.addEventListener("synocast_location_granted", (e) => {
    const { lat, lon, isCached } = e.detail;
    setMapLocation(lat, lon, isCached);
  });

  // 2. Immediate check if already granted/cached
  if (window.synocast_current_loc) {
    const { lat, lon, isCached } = window.synocast_current_loc;
    setMapLocation(lat, lon, isCached);
  } else {
    // Default View until location is resolved
    updateWeather(33.6844, 73.0479);
  }

  // --- Map Controls ---

  // Debounce helper
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  const debouncedUpdateWeather = debounce((lat, lon) => {
    updateWeather(lat, lon);
  }, 500);

  // Update weather on map move
  map.on("moveend", function () {
    const center = map.getCenter();
    marker.setLatLng(center); // Move marker to center
    debouncedUpdateWeather(center.lat, center.lng);
  });

  // --- Map Controls ---

  // Search Functionality
  const searchInput = document.getElementById('location-search'); // FIXED ID
  const searchResults = document.getElementById("location-search-results");
  if (searchInput && searchResults) {
    AutocompleteUtils.initAutocomplete(searchInput, searchResults, (city) => {
      const lat = parseFloat(city.lat);
      const lon = parseFloat(city.lon);
      map.setView([lat, lon], 16); // Zoom in on result
      marker.setLatLng([lat, lon]);
      updateWeather(lat, lon);
    });
  }

  // Locate Me Functionality
  document.getElementById("locate-btn").addEventListener("click", function () {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          map.setView([lat, lon], 16);
          marker.setLatLng([lat, lon]);
          updateWeather(lat, lon);
        },
        () => {
          ToastUtils.show("Location Error", "Unable to retrieve your location.", "error");
        }
      );
    } else {
      ToastUtils.show("Not Supported", "Geolocation is not supported by your browser.", "warning");
    }
  });

  async function updateWeather(lat, lon) {
    const weatherUrl = `/api/weather?lat=${lat}&lon=${lon}`;
    const geocodeUrl = `/api/geocode/reverse?lat=${lat}&lon=${lon}`;

    // Show loading state
    const overlay = document.getElementById("weather-overlay");
    if (overlay) overlay.classList.add("loading");

    const mapCityEl = document.getElementById("map-city");
    if (mapCityEl) mapCityEl.textContent = "Loading...";

    try {
      // Fetch Weather
      const weatherRes = await fetch(weatherUrl);
      const weatherData = await weatherRes.json();

      // Fetch City Name (Reverse Geocoding)
      // We can still use this for better location details if OWM name is too generic
      const geoRes = await fetch(geocodeUrl);
      const geoData = await geoRes.json();

      // Update UI
      if (weatherData.current) {
        // OpenWeatherMap returns temp in Celsius (metric units requested in backend)
        const mapTempEl = document.getElementById("map-temp");
        if (mapTempEl)
          mapTempEl.textContent = Math.round(weatherData.current.main.temp);

        const mapWindEl = document.getElementById("map-wind");
        if (mapWindEl)
          mapWindEl.textContent = WeatherUtils.formatWind(
            weatherData.current.wind.speed
          );

        const mapHumEl = document.getElementById("map-humidity");
        if (mapHumEl)
          mapHumEl.textContent = `${weatherData.current.main.humidity}%`;

        // Update Icon
        const w = weatherData.current.weather[0];
        const iconClass = WeatherUtils.getIconClass(w.id, w.icon);

        const iconContainer = document.getElementById("map-icon");
        if (iconContainer) {
          iconContainer.innerHTML = `<i class="fas ${iconClass}"></i>`;
        }
      }

      let locationName = "Unknown Location";
      if (geoData.address) {
        locationName =
          geoData.address.city ||
          geoData.address.town ||
          geoData.address.village ||
          geoData.address.county ||
          "Unknown Location";
      } else if (weatherData.current && weatherData.current.name) {
        locationName = weatherData.current.name;
      }
      if (mapCityEl) {
          mapCityEl.textContent = locationName;
          updateFavoriteIcon(locationName); // Update icon state
      }
    } catch (error) {
      const mapCityEl = document.getElementById("map-city");
      if (mapCityEl) mapCityEl.textContent = "Error loading data";
    } finally {
      if (overlay) overlay.classList.remove("loading");
    }
  }
});
