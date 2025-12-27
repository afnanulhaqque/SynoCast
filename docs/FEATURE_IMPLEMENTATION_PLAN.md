# SynoCast Feature Implementation Plan

## Overview

This document outlines the comprehensive implementation strategy for expanding SynoCast's capabilities across 12 key feature categories. The plan leverages the existing Flask + SQLite architecture while introducing necessary enhancements for scalability and interactivity.

---

## 1. 🌡️ Weather Alerts & Notifications

### Implementation Profile

- **Priority:** High
- **Complexity:** Complex
- **Estimated Timeline:** 2 Weeks

### Technical Requirements

- **Backend:** Enhanced background worker (Celery or robust threading) for reliable polling.
- **Database:** Expand `user_preferences` for granular alert settings (e.g., specific thresholds).
- **APIs:** OpenWeatherMap One Call API (alerts endpoint).
- **Services:** Resend (Email), Web Push API (Browser Notifications), Twilio (optional for SMS).

### Implementation Details

1.  **Backend Logic:** Refactor the existing `check_weather_alerts` thread in `app.py` into a robust scheduler.
2.  **User Preferences:** Add UI in `subscribe.html` to let users define "Severity Levels" and specific event types (e.g., "Only Tornado Warnings").
3.  **Push Notifications:** Implement Service Worker (`sw.js`) push event listeners and a subscription endpoint for VAPID keys.

### key Challenges

- **Rate Limiting:** Polling OWM for every user is inefficient. **Solution:** Cache alerts by geohash or region to minimize API calls.
- **Delivery Reliability:** Email delivery can be delayed. **Solution:** Prioritize Browser Push/SMS for critical life-safety warnings.

---

## 2. 📊 Advanced Weather Analytics

### Implementation Profile

- **Priority:** Medium
- **Complexity:** Moderate
- **Estimated Timeline:** 1.5 Weeks

### Technical Requirements

- **Frontend:** Chart.js or Recharts for visualization.
- **Backend:** Aggregation logic in `app.py`.
- **API:** OWM 5 Day / 3 Hour Forecast (mostly sufficient for near-term analytics).

### Implementation Details

1.  **Data Processing:** Create a utility to process 5-day forecast data into daily aggregates (Min/Max Temp, Total Precip).
2.  **Visualization:** Create a "Analytics" tab in `weather.html` rendering:
    - Temperature trend line graph.
    - Precipitation probability bar chart.
    - UV Index gauge.

### Key Challenges

- **Mobile Responsiveness:** Complex charts can break on small screens. **Solution:** Use responsive Chart.js containers and simplified views for mobile.

---

## 3. 🗺️ Enhanced Interactive Map Features

### Implementation Profile

- **Priority:** High
- **Complexity:** Complex
- **Estimated Timeline:** 3 Weeks

### Technical Requirements

- **Frontend library:** Leaflet.js (already likely in use, need verification) or Mapbox GL JS.
- **Data Layers:** OWM Tile Layers (Precipitation, Clouds, Temp, Wind).

### Implementation Details

1.  **Layer Control:** Add a layer switcher control to the map (Precipitation, Temp, Wind).
2.  **Animation:** Implement a time-slider to animate forecast tiles (requires pre-fetching next 3-6 hours of tile frames).
3.  **Comparisons:** Create a "Split View" mode where two map instances run side-by-side synchronized by zoom/center but showing different locations.

### Key Challenges

- **Performance:** Animating raster tiles can be heavy. **Solution:** Preload images in JS constraints and limit animation to 6-frame loops.

---

## 4. 👥 Social & Community Features

### Implementation Profile

- **Priority:** Low
- **Complexity:** Moderate
- **Estimated Timeline:** 2 Weeks

### Technical Requirements

- **Database:** New `community_reports` table (extends existing `weather_reports`).
- **Media Storage:** Cloudinary or AWS S3 for user photos.
- **Auth:** Need lightweight user accounts (beyond just email param).

### Implementation Details

1.  **Crowdsourcing:** "Confirm Weather" button on the main dashboard ("Is it raining? Yes/No").
2.  **Photo Feed:** Community stream in `home.html` filtered by radius.
3.  **Sharing:** Generate OG Images dynamically for "Share this Forecast" using an internal API or library like `html2canvas`.

### Key Challenges

- **Moderation:** User uploads require policing. **Solution:** Use Google Gemini Vision API to auto-flag inappropriate images before publishing.

---

## 5. 🎯 Personalization

### Implementation Profile

- **Priority:** Medium
- **Complexity:** Simple
- **Estimated Timeline:** 1 Week

### Technical Requirements

- **Storage:** LocalStorage for anonymous guests; `user_preferences` DB table for subscribers.

### Implementation Details

1.  **Dashboard Config:** Allow users to toggle visibility of widgets (News, Map, Hourly). Save JSON blob to DB.
2.  **Hobbies:** "Weather for..." selector (Photography, Running, Gardening).
    - _Photography:_ Highlights Golden Hour/Blue Hour.
    - _Running:_ Highlights Dew Point & Wind.

### Key Challenges

- **Synchronization:** Keeping LocalStorage in sync with DB when a user logs in. **Solution:** "Merge" strategy on login.

---

## 6. 🌤️ Extended Forecasting

### Implementation Profile

- **Priority:** Medium
- **Complexity:** Moderate
- **Estimated Timeline:** 1 Week

### Technical Requirements

- **API:** OWM "One Call" API (essential for daily 7-14 day data).
- **Astronomy:** `suncalc` library (JS) or OWM Astro data.

### Implementation Details

1.  **UI Layout:** Horizontal scroll card list for 10-day forecast.
2.  **Detail View:** Clicking a day expands to show "Morning/Afternoon/Evening/Night" breakdown.
3.  **Astro Widget:** Visual arc showing sun position, moon phase icon.

### Key Challenges

- **Data Accuracy:** 14-day forecasts are notoriously inaccurate. **Solution:** Visually fade confidence level or explicitly label "Long Range" for days 8+.

---

## 7. 🏠 Smart Home Integration

### Implementation Profile

- **Priority:** Low
- **Complexity:** Moderate
- **Estimated Timeline:** 2 Weeks

### Technical Requirements

- **API:** Create RESTful JSON endpoints protected by API Tokens.
- **Format:** JSON response optimized for automation (e.g., `{"rain_expected": true, "temp": 22}`).

### Implementation Details

1.  **Token Management:** Generate API keys for users in `/profile`.
2.  **Endpoints:**
    - `GET /api/v1/smart/current` (Simplified current state).
    - `GET /api/v1/smart/trigger` (Boolean flags for automations).
3.  **IFTTT:** Create a Webhook reception endpoint for external triggers.

### Key Challenges

- **Security:** API keys can be leaked. **Solution:** Rate limiting (already implemented in `app.py`) and read-only scopes.

---

## 8. 📈 Historical Data & Trends

### Implementation Profile

- **Priority:** Low
- **Complexity:** Simple (if using simulated data) / High (if real API).
- **Estimated Timeline:** 1 Week

### Technical Requirements

- **API:** OWM History API (Paid) or accumulate own data over time.

### Implementation Details

1.  **"On This Day":** Since the DB is new, use OWM History API or a free alternative (e.g., Open-Meteo) to fetch last year's data for the same date.
2.  **Climate Context:** Show "3°C warmer than average" badge using static climate average data files for major cities.

### Key Challenges

- **Data Cost:** Historical APIs are expensive. **Solution:** Use Open-Meteo (free for non-commercial) for historical comparisons.

---

## 9. 🎨 Enhanced UI/UX

### Implementation Profile

- **Priority:** High
- **Complexity:** Moderate
- **Estimated Timeline:** Continuous

### Technical Requirements

- **CSS:** CSS Variables for theming.
- **Assets:** Lottie Files (JSON animations) for weather icons.
- **Video:** HTML5 Background Video loops.

### Implementation Details

1.  **Lottie Integration:** Replace static FontAwesome icons with animated Lottie JSONs for forecast states.
2.  **Dynamic Backgrounds:** Map weather conditions (`Rain`, `Clear`) to a video filename map.
3.  **Themes:** "OLED Dark", "High Contrast", "Sunset" themes using CSS variable swapping.

### Key Challenges

- **Performance:** Heavy animations drain battery. **Solution:** Use IntersectionObserver to pause animations when off-screen.

---

## 10. 🤖 AI Enhancements

### Implementation Profile

- **Priority:** High (Core Differentiator)
- **Complexity:** Moderate
- **Estimated Timeline:** 2 Weeks

### Technical Requirements

- **Engine:** Google Gemini (Existing integration).
- **Context:** Inject user location context (already done in `api_ai_chat`).

### Implementation Details

1.  **Outfit & Recipe:** Add specific prompt templates for "What to wear" and "Comfort food for this weather".
2.  **Natural Language Search:** "Weather in Paris next Tuesday" -> Parse intent -> Call API.
3.  **Impact Prediction:** "Pollen is high, traffic might be slow due to fog." (Requires Air Quality API).

### Key Challenges

- **Latency:** AI responses are slow. **Solution:** Stream responses or show "Thinking..." skeleton states.

---

## 11. 📱 Mobile App Features (PWA)

### Implementation Profile

- **Priority:** Medium
- **Complexity:** Moderate
- **Estimated Timeline:** 1 Week

### Technical Requirements

- **PWA:** Manifest v3, Service Workers.

### Implementation Details

1.  **Installability:** Custom "Install SynoCast" prompt logic in JS.
2.  **Offline Support:** Cache the last known forecast JSON in `localStorage` or Service Worker Cache Storage to show "stale" data instead of a dinosaur.
3.  **Share Target:** Allow users to share text/links _to_ the app (feature expansion).

### Key Challenges

- **iOS Limitations:** Limited PWA push support on older iOS. **Solution:** In-app fallback notifications.

---

## 12. 🌍 Global Features

### Implementation Profile

- **Priority:** Low
- **Complexity:** Moderate
- **Estimated Timeline:** 2 Weeks

### Technical Requirements

- **Library:** `i18next` or Flask-Babel.
- **Data:** Translation JSON files.

### Implementation Details

1.  **Currency:** "Travel Mode" showing exchange rates for the searched city's country (requires Currency API).
2.  **Localization:** Translate static UI strings. Weather conditions come translated from OWM (`lang` param).

### Key Challenges

- **Maintenance:** Keeping 10+ language files in sync. **Solution:** Automate translation updates using Gemini.
