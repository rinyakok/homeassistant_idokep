<div align="center">

<img src="https://raw.githubusercontent.com/rinyakok/homeassistant_idokep/main/custom_components/idokep/idokep.png" alt="Időkép" width="120">

# Időkép Weather for Home Assistant

**Weather, forecasts and weather alerts from [idokep.hu](https://www.idokep.hu) for places in Hungary**

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5?logo=homeassistantcommunitystore&logoColor=white)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/rinyakok/homeassistant_idokep?logo=github)](https://github.com/rinyakok/homeassistant_idokep/releases)
[![CI](https://github.com/rinyakok/homeassistant_idokep/actions/workflows/ci.yml/badge.svg)](https://github.com/rinyakok/homeassistant_idokep/actions/workflows/ci.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.11%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io)
[![License: MIT](https://img.shields.io/github/license/rinyakok/homeassistant_idokep)](LICENSE)

🇬🇧 English summary below &nbsp;·&nbsp; 🇭🇺 **[Részletes magyar leírás lent ↓](#magyar)**

</div>

> [!NOTE]
> 🇬🇧 This page starts with a short English summary. **The full documentation is in Hungarian: [Magyar dokumentáció ↓](#magyar)**
>
> 🇭🇺 Az oldal elején egy rövid angol összefoglaló áll. **A részletes leírás magyarul lent található: [Magyar dokumentáció ↓](#magyar)**

---

## 🇬🇧 English summary

### ✨ Features

| Feature | What you get |
|---|---|
| 🌦️ **Weather entity** | Current weather, 15-day (optionally 30-day) daily and 36-hour hourly forecast: temperature, wind, precipitation and precipitation chance |
| 🌡️ **Sensors** | Temperature, condition (also as the Hungarian text), short text forecast, sunrise, sunset, warning forecast |
| 📍 **Map station sensors** | Add any number of stations as separate entries/devices; each has temperature, 24-hour precipitation, wind speed and gust sensors |
| 🌫️ **Smog sensors** | Add a separate entry and select an available city; its PM10 and PM2.5 station readings appear as sensors |
| 🌱 **Pollen sensors** | Add a separate entry and select an available city; qualitative pollen levels appear as sensors |
| 🌧️ **Radar image and stream** | One global latest radar image and a camera stream cycling through images retained for up to one hour |
| ⚠️ **Weather alerts** | Any alert, plus yellow, orange and red alert sensors with details |
| ⛈️ **Storm warning** | Thunderstorm forecast for the current or next hour |
| 📍 **Many places** | Any number of places, one device per place |
| 🗣️ **Two languages** | English and Hungarian user interface |

### 📦 Installation (HACS)

This integration is in the **HACS default list**, no custom repository needed.

1. Open **HACS**, search for **Időkép** and open **Időkép Weather Component**.
2. Select **Download**, then restart Home Assistant.

![HACS](https://github.com/user-attachments/assets/3d409403-e481-4b48-a9b8-7c2794d578a1)

Requires Home Assistant **2024.1** or newer. HACS cannot select a release based on the HA version, so choose the matching release manually:

| Home Assistant | HACS release tag |
| --- | --- |
| 2024 | `v2.0.0-ha2024` |
| 2026 | `v2.0.0` |

For pre-releases, append `-rc`, or `-dev`, optionally followed by a number (e.g. `v2.0.0-ha2024-rc.1`), and mark the GitHub release as a pre-release. HACS beta versions must be enabled to install it. Manual installation: copy `custom_components/idokep` to `<config>/custom_components` and restart.

### ⚙️ Setup

1. **Settings → Devices & services → Add integration → Időkép**.
2. Choose **Weather location** and type the place name as written on idokep.hu, e.g. **Pécs**. Accents are optional: `erd` is saved as `Érd`.
3. To add map measurements, add Időkép again, choose **Map station sensors**, and enter the station name or ID. Repeat to add more stations.
4. To add smog or pollen readings, add Időkép again, choose **Smog sensors** or **Pollen sensors**, then select a city from the map's available cities. Leaving the city empty cancels the setup.

- 🔧 **Options** (gear icon): daily forecast of 15 days (default) or 30 days.
- Each station entry has its own update interval, configurable from 5 minutes to 1 hour in 5-minute steps (default: 20 minutes).
- Existing location entries that used map station sensors need the station added again as a separate entry; the old location-level station sensors are no longer created.
- ✏️ **Reconfigure** changes the place; entity IDs stay the same.
- 🌧️ The first place automatically creates one separate **Időkép radar** entry with a latest-image entity and a camera stream. The image history fills gradually after startup.

### 🧩 Entities (for a place called Érd)

| Entity | Description |
|---|---|
| 🖼️ `image.idokep_radar_latest_radar_image` | Latest static Időkép radar image, shared by all places |
| 🎞️ `camera.idokep_radar_radar_image_stream` | Cycles through radar images downloaded in the previous hour; history fills for up to an hour after startup |
| 🌦️ `weather.idokep_erd` | Current weather; daily and hourly forecast via `weather.get_forecasts` |
| 🌡️ `sensor.idokep_erd_temperature` | Temperature (°C) |
| ☁️ `sensor.idokep_erd_condition` | Condition, e.g. `rainy` |
| 🇭🇺 `sensor.idokep_erd_condition_hungarian` | Condition as written on idokep.hu, e.g. "Erősen felhős" |
| 📝 `sensor.idokep_erd_short_forecast` | Short text forecast, e.g. "Kettősfronti hatás várható" |
| 🌅 `sensor.idokep_erd_sunrise` / 🌇 `_sunset` | Today's sunrise and sunset |
| 📅 `sensor.idokep_erd_warning_forecast` | Today's warning note, e.g. "Szeles nap"; all days in the `days` attribute |
| 📍 `sensor.idokep_erd_station_temperature` | Temperature (°C) from the separately added Érd station device |
| 🌧️ `sensor.idokep_erd_station_precipitation_24_h` | Station 24-hour precipitation (mm) |
| 💨 `sensor.idokep_erd_station_wind_speed` / `_wind_gust` | Station wind speed and gust (km/h); direction and measurement time are attributes |
| 🌫️ Smog-entry sensors | PM10 and PM2.5 hourly averages for stations in the selected city (µg/m³); station, source and measurement time are attributes |
| 🌱 Pollen-entry sensors | Qualitative level (`nincs`, `alacsony`, `közepes`, etc.) for each pollen type in the selected city |
| ⚠️ `binary_sensor.idokep_erd_weather_alert` | Any weather alert; details in the attributes |
| 🟡 🟠 🔴 `binary_sensor.idokep_erd_yellow_alert` / `_orange_alert` / `_red_alert` | Alert of that level |
| ⛈️ `binary_sensor.idokep_erd_storm_in_the_next_hour` | Thunderstorm in the current or next hour |
| 🔌 `binary_sensor.idokep_erd_connection` | Diagnostic: off when idokep.hu can't be reached |

Entity IDs follow the Home Assistant language at the time the entity is created. The examples are for English.

### 🔄 Switching from FabianGabor/HA-Idokep

Both use the `idokep` domain, so only one can be installed.

- **Home Assistant 2026.11 or newer** (HACS is now the built-in **Marketplace**): the Marketplace removes HA-Idokep only together with its integration entries. Write down your old entity IDs, use **Delete and uninstall** on HA-Idokep, install this integration, restart, add your places again, then rename the new entities to the old entity IDs. History and long-term statistics continue under the old IDs.
- **Older Home Assistant with HACS:** remove HA-Idokep in HACS but **keep its integration entries**, install this integration and restart. The entries are taken over and the entity IDs stay the same.

➡️ [Step-by-step guide (Hungarian)](#atallas)

### 🚧 Limits

idokep.hu has no public API. Weather, smog and pollen data are read every 20 minutes; each map station has an independent, configurable 5-minute-to-1-hour update interval. A change on the website can break parts of the integration. Add map stations as separate entries using their name or ID. Different stations may not provide every measurement, and the page's map formats can change. 🐞 Please report problems in the [issue tracker](https://github.com/rinyakok/homeassistant_idokep/issues).

---

<a id="magyar"></a>

## 🇭🇺 Magyar dokumentáció

Időjárási adatok, előrejelzés és időjárási riasztások az [idokep.hu](https://www.idokep.hu)-ról, magyarországi településekre, Home Assistanthez.

<details open>
<summary><b>📑 Tartalom</b></summary>

- ✨ [Mit tud?](#mit-tud)
- 📦 [Telepítés](#telepites)
- ⚙️ [Beállítás](#beallitas)
- 🧩 [Entitások](#entitasok)
- ⚠️ [Riasztások](#riasztasok)
- 📈 [Előrejelzés lekérése](#elorejelzes)
- ☁️ [Időjárási állapotok](#allapotok)
- 🖼️ [Vezérlőpult példák](#vezerlopult)
- 🤖 [Automatizálás példák](#automatizalas)
- 🔄 [Átállás a HA-Idokep integrációról](#atallas)
- 🚧 [Korlátok](#korlatok)
- ❓ [Gyakori kérdések](#gyik)
- 🐞 [Hibabejelentés](#hibabejelentes)

</details>

<a id="mit-tud"></a>

### ✨ Mit tud?

| Funkció | Mit kapsz |
|---|---|
| 🌦️ **Weather entitás** | Aktuális időjárás, 15 napos (választhatóan 30 napos) napi és 36 órás óránkénti előrejelzés: hőmérséklet, szél, csapadék és csapadékesély |
| 🌡️ **Szenzorok** | Hőmérséklet, időjárási állapot (az idokep.hu magyar szövegével is), rövid szöveges előrejelzés, napkelte, napnyugta, figyelmeztető előrejelzés |
| 📍 **Térképes állomásszenzorok** | Tetszőleges számú, külön bejegyzésként és eszközként felvett állomás hőmérséklet-, 24 órás csapadék-, szélsebesség- és széllökésadatai |
| 🌫️ **Szmogszenzorok** | Külön bejegyzésként vehetők fel; a térképen elérhető település kiválasztása után annak mérőállomásai PM10- és PM2.5-szenzorokat adnak |
| 🌱 **Pollenszenzorok** | Külön bejegyzésként vehetők fel; a térképen elérhető település kiválasztása után annak pollenszintjei szenzorokként jelennek meg |
| 🌧️ **Radarkép és képsorozat** | Egy globális legfrissebb radarkép és egy kamerastream, amely legfeljebb az elmúlt egy óra képeit játssza le |
| ⚠️ **Riasztások** | Bármilyen riasztás, valamint sárga, narancs és piros riasztás szenzor, részletekkel |
| ⛈️ **Zivatar** | Zivatar az aktuális vagy a következő órában |
| 🔌 **Kapcsolat** | Jelzi, ha az idokep.hu nem érhető el |
| 📍 **Több helyszín** | Tetszőleges számú település, mindegyik külön eszközként („Időkép Érd”) |
| 🗣️ **Két nyelv** | Magyar és angol felület |

<a id="telepites"></a>

### 📦 Telepítés

#### HACS-szal (ajánlott)

Az integráció benne van a **HACS alapértelmezett listájában**, egyéni tárolót (custom repository) nem kell felvenni.

1. Nyisd meg a **HACS**-t, és keress rá: **Időkép**.
2. Nyisd meg az **Időkép Weather Component**-et, és válaszd a **Letöltés** gombot.
3. Indítsd újra a Home Assistantet.

> [!IMPORTANT]
> Legalább **Home Assistant 2024.1** szükséges. A HACS nem választ automatikusan HA-verzió alapján, ezért kézzel válaszd ki a megfelelő kiadást:
>
> | Home Assistant | HACS release tag |
> | --- | --- |
> | 2024 | `v2.0.0-ha2024` |
> | 2026 | `v2.0.0` |
>
> Előzetes kiadáshoz a tag végére `-rc`, vagy `-dev` írható, opcionális sorszámmal (például `v2.0.0-ha2024-rc.1`); a GitHub Release-nél jelöld be a **Set as a pre-release** opciót, HACS-ban pedig engedélyezd a béta verziókat.

#### Kézzel

Másold a `custom_components/idokep` mappát a Home Assistant `<config>/custom_components` mappájába, majd indítsd újra a Home Assistantet.

<a id="beallitas"></a>

### ⚙️ Beállítás

1. **Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása**, majd válaszd az **Időkép**-et.
2. Válaszd az **Időjárási helyszín** lehetőséget, majd add meg a település nevét úgy, ahogy az idokep.hu-n szerepel. Például **Pécs** (`https://www.idokep.hu/idojaras/Pécs`).
3. További településekhez ismételd meg. Térképes állomásszenzorokhoz újra add hozzá az Időképet, válaszd a **Térképes állomásszenzorok** lehetőséget, majd add meg az állomás nevét vagy azonosítóját. Több állomás is felvehető.
4. Szmog- vagy pollenszenzorokhoz újra add hozzá az Időképet, válaszd a **Szmogszenzorok** vagy **Pollenszenzorok** lehetőséget, majd válassz egy települést a térképen elérhetők közül. Üres választásnál a beállítás megszakad.

> [!TIP]
> Az ékezet elhagyható: az `erd` is Érdet jelenti. Az integráció az idokep.hu írásmódját menti el.

> [!WARNING]
> Ha az idokep.hu nem ismeri a nevet, **Budapestet mutatja helyette**. Ilyenkor a beállítás hibát jelez („Ezt a települést az idokep.hu nem ismeri, helyette ezt mutatja: Budapest”), így nem kapsz véletlenül budapesti adatokat.

- 🔧 **Beállítások (fogaskerék):** a napi előrejelzés lehet 15 napos (alapértelmezett) vagy 30 napos.
- Minden állomásbejegyzésnél külön állítható a frissítési időköz 5 perc és 1 óra között, 5 perces lépésekben (alapértelmezés: 20 perc).
- Ha korábban a helyszín beállításainál térképes állomásszenzorokat használtál, az állomást külön bejegyzésként újra fel kell venni; a régi helyszínszintű szenzorok már nem jönnek létre.
- ✏️ **Helyszín módosítása:** az integráció bejegyzésénél válaszd az **Újrakonfigurálás** pontot. Az entitásazonosítók nem változnak, így a vezérlőpultok és az automatizálások tovább működnek.
- 🌧️ Az első helyszín hozzáadásakor automatikusan létrejön egy külön **Időkép radar** bejegyzés a legfrissebb kép és a képsorozat entitásával. A képtörténet újraindítás után fokozatosan, legfeljebb egy óra alatt telik fel.

<a id="entitasok"></a>

### 🧩 Entitások

Egy „Érd” nevű helyszínnél, angol nyelvű Home Assistantben:

| Entitás | Leírás |
|---|---|
| 🖼️ `image.idokep_radar_latest_radar_image` | A legfrissebb Időkép-radarkép, minden helyszínnel közös |
| 🎞️ `camera.idokep_radar_radar_image_stream` | Az előző órában letöltött radarképeket ciklikusan megjelenítő kamera; újraindítás után fokozatosan telik fel a képtörténet |
| 🌦️ `weather.idokep_erd` | Aktuális időjárás, napi és óránkénti előrejelzés |
| 🌡️ `sensor.idokep_erd_temperature` | Aktuális hőmérséklet (°C) |
| ☁️ `sensor.idokep_erd_condition` | Aktuális állapot Home Assistant formában (pl. `rainy`, `partlycloudy`) |
| 🇭🇺 `sensor.idokep_erd_condition_hungarian` | Aktuális állapot úgy, ahogy az idokep.hu írja (pl. „Erősen felhős”) |
| 📝 `sensor.idokep_erd_short_forecast` | Rövid szöveges előrejelzés (pl. „Kettősfronti hatás várható”) |
| 🌅 `sensor.idokep_erd_sunrise` / 🌇 `_sunset` | Mai napkelte és napnyugta |
| 📅 `sensor.idokep_erd_warning_forecast` | A mai figyelmeztetés (pl. „Szeles nap”); az összes nap a `days` attribútumban |
| 📍 `sensor.idokep_erd_station_temperature` | A külön felvett Érd állomás hőmérséklete (°C) |
| 🌧️ `sensor.idokep_erd_station_precipitation_24_h` | Az állomás 24 órás csapadéka (mm) |
| 💨 `sensor.idokep_erd_station_wind_speed` / `_wind_gust` | Az állomás szélsebessége és széllökése (km/h); az irány és mérési idő attribútum |
| 🌫️ Szmogbejegyzés szenzorai | A kiválasztott település állomásainak PM10- és PM2.5-órás átlaga (µg/m³); az állomás, forrás és mérési idő attribútum |
| 🌱 Pollenbejegyzés szenzorai | A kiválasztott település pollentípusonkénti szöveges értéke (pl. `nincs`, `alacsony`, `közepes`, `magas`) |
| ⚠️ `binary_sensor.idokep_erd_weather_alert` | Bekapcsol, ha az idokep.hu bármilyen színes riasztást mutat |
| 🟡 🟠 🔴 `binary_sensor.idokep_erd_yellow_alert` / `_orange_alert` / `_red_alert` | Bekapcsol, ha van ilyen szintű riasztás |
| ⛈️ `binary_sensor.idokep_erd_storm_in_the_next_hour` | Bekapcsol, ha az aktuális vagy a következő órára zivatart jeleznek |
| 🔌 `binary_sensor.idokep_erd_connection` | Kikapcsol, ha az idokep.hu nem érhető el (diagnosztikai) |

> [!NOTE]
> Az entitásazonosítók a Home Assistant nyelvét követik az entitás létrehozásakor. Magyar nyelvnél például `sensor.idokep_erd_napkelte` lesz. A pontos azonosítót az entitás beállításainál látod.

A **weather entitás** további attribútumai: `short_forecast` (rövid előrejelzés), `precipitation` és `precipitation_probability` (a következő óra csapadéka mm-ben és csapadékesélye %-ban). Az állomásszenzorok a kiválasztott térképpont mérési idejét, nevét, azonosítóját és adatforrását is megadják. Nem minden állomás szolgáltat minden mérési típust; ilyenkor az adott szenzor értéke ismeretlen.

A pollenadatok az Időkép térképén hetente frissülnek, február 1. és október 31. között; az integráció a kategóriák szöveges szintjét olvassa ki.

<a id="riasztasok"></a>

### ⚠️ Riasztások

Az idokep.hu kétféle figyelmeztetést mutat:

#### 🟡 🟠 🔴 Színes riasztások

Például „Sárga riasztás szélre”. Ezeket a `weather_alert` és a szintenkénti szenzorok jelzik.

| Attribútum (`weather_alert`) | Jelentés |
|---|---|
| `alert_count` | A riasztások száma |
| `yellow_alerts`, `orange_alerts`, `red_alerts` | Szintenkénti darabszám |
| `alerts` | Lista, elemenként `level` (szint), `type` (típus), `description` (az idokep.hu szövege) és `icon_url` |

A szintenkénti szenzorok attribútumai: `alert_count` és `alerts`.

A `type` értékei: 💨 `wind` (szél), 🌪️ `storm` (vihar), ⛈️ `thunderstorm` (zivatar), 🌧️ `rain` (eső), ❄️ `snow` (hó), 🧊 `freezing_rain` (ónos eső), 🌫️ `fog` (köd), 🔥 `heat` (hőség), 🥶 `cold` (hideg), ❄️ `frost` (fagy), egyéb esetben `general`.

#### 📅 Figyelmeztető előrejelzés

A napi előrejelzésben, szín nélkül, például „Sok eső”, „Szeles nap” vagy „Hidegfront erős széllel”. Ezt a `warning_forecast` szenzor mutatja: az állapota a mai figyelmeztetés (ha nincs, ismeretlen), a `days` attribútumban pedig az összes nap szerepel (`date`, `description`, `icon_url`).

<a id="elorejelzes"></a>

### 📈 Előrejelzés lekérése

A Home Assistant az előrejelzést nem attribútumként tárolja, hanem a `weather.get_forecasts` művelettel lehet lekérni:

```yaml
action: weather.get_forecasts
target:
  entity_id: weather.idokep_erd
data:
  type: daily   # vagy: hourly
response_variable: elorejelzes
```

| Előrejelzés | Mezők |
|---|---|
| 📅 Napi | `datetime`, `condition`, `temperature` (max), `templow` (min), `precipitation` (mm) |
| 🕐 Óránkénti | `datetime`, `condition`, `temperature`, `wind_speed` (km/h), `wind_bearing` (fok), `precipitation` (mm), `precipitation_probability` (%) |

<a id="allapotok"></a>

### ☁️ Időjárási állapotok

Az idokep.hu magyar leírásait az integráció Home Assistant állapotokra fordítja:

| | Home Assistant | idokep.hu |
|:---:|---|---|
| ☀️ | `sunny` (éjjel 🌙 `clear-night`) | napos, derült |
| ⛅ | `partlycloudy` | gyengén felhős, közepesen felhős |
| ☁️ | `cloudy` | erősen felhős, borult |
| 🌧️ | `rainy` | gyenge eső, eső, zápor, szitálás, eső viharos széllel |
| 🌊 | `pouring` | erős eső |
| ⛈️ | `lightning-rainy` | zivatar |
| 🌩️ | `lightning` | villámlás, száraz zivatar |
| 🧊 | `hail` | jégeső |
| 🌫️ | `fog` | köd, ködös, ködszitálás, pára, párás |
| ❄️ | `snowy` | havazás, intenzív havazás, hószállingózás, hózápor, hófúvás, hófúvás havazással |
| 🌨️ | `snowy-rainy` | havas eső, fagyott eső, ónos eső |
| 💨 | `windy` | szeles |
| ⚠️ | `exceptional` | porvihar |

> [!TIP]
> Ha egy leírás még nincs a listában, az állapot ismeretlen lesz, és a naplóban egyszer megjelenik egy figyelmeztetés („Unknown idokep.hu weather condition …”). Kérlek, jelezd [hibajegyben](https://github.com/rinyakok/homeassistant_idokep/issues), és felvesszük.

<a id="vezerlopult"></a>

### 🖼️ Vezérlőpult példák

<details>
<summary><b>🌦️ Időjárás kártya</b> – napi előrejelzéssel</summary>

```yaml
type: weather-forecast
entity: weather.idokep_erd
forecast_type: daily
show_forecast: true
```

</details>

<details>
<summary><b>📋 Részletek kártya</b> – előrejelzés, figyelmeztetés, napkelte</summary>

```yaml
type: entities
title: Időkép Érd
entities:
  - entity: sensor.idokep_erd_short_forecast
    name: Előrejelzés
  - entity: sensor.idokep_erd_condition_hungarian
    name: Most
  - entity: sensor.idokep_erd_warning_forecast
    name: Figyelmeztetés
  - entity: sensor.idokep_erd_sunrise
    format: time
  - entity: sensor.idokep_erd_sunset
    format: time
```

</details>

<details>
<summary><b>⚠️ Riasztás kártya</b> – csak riasztáskor látszik</summary>

```yaml
type: conditional
conditions:
  - condition: state
    entity: binary_sensor.idokep_erd_weather_alert
    state: "on"
card:
  type: markdown
  content: >
    {% for a in state_attr('binary_sensor.idokep_erd_weather_alert', 'alerts') %}
    **{{ a.description }}**
    {% endfor %}
```

</details>

<a id="automatizalas"></a>

### 🤖 Automatizálás példák

<details>
<summary><b>🟠 🔴 Értesítés narancs vagy piros riasztásnál</b></summary>

```yaml
alias: Időjárási riasztás
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.idokep_erd_orange_alert
      - binary_sensor.idokep_erd_red_alert
    to: "on"
actions:
  - action: notify.notify
    data:
      message: >
        {{ state_attr(trigger.entity_id, 'alerts')
           | map(attribute='description') | join(', ') }}
```

</details>

<details>
<summary><b>⛈️ Zivatar érkezik</b></summary>

```yaml
alias: Zivatar érkezik
triggers:
  - trigger: state
    entity_id: binary_sensor.idokep_erd_storm_in_the_next_hour
    to: "on"
actions:
  - action: notify.notify
    data:
      message: Zivatar várható a következő órában Érden.
```

</details>

<details>
<summary><b>🌧️ Este 8-kor: lesz-e holnap eső?</b></summary>

```yaml
alias: Holnapi eső
triggers:
  - trigger: time
    at: "20:00:00"
actions:
  - action: weather.get_forecasts
    target:
      entity_id: weather.idokep_erd
    data:
      type: daily
    response_variable: elorejelzes
  - variables:
      holnap: "{{ elorejelzes['weather.idokep_erd'].forecast[1] }}"
  - condition: template
    value_template: "{{ holnap.precipitation | float(0) > 0 }}"
  - action: notify.notify
    data:
      message: "Holnap {{ holnap.precipitation }} mm eső várható."
```

</details>

<a id="atallas"></a>

### 🔄 Átállás a HA-Idokep integrációról

A [FabianGabor/HA-Idokep](https://github.com/FabianGabor/HA-Idokep) és ez az integráció ugyanazt az `idokep` azonosítót használja, ezért egyszerre csak az egyik lehet telepítve. Az átállás attól függ, melyik Home Assistant verziót használod.

#### Home Assistant 2026.11 vagy újabb (Marketplace)

A HACS helyett itt a beépített **Marketplace** van. Ez a HA-Idokep-et csak a bejegyzéseivel együtt engedi eltávolítani, és amíg a HA-Idokep telepítve van, ezt az integrációt nem engedi telepíteni. Ezért a helyszíneket újra fel kell venni, az entitásokat pedig vissza kell nevezni a régi azonosítóra. Az előzmények és a hosszú távú statisztikák így megmaradnak.

1. 📝 Írd fel a régi entitásazonosítókat: **Beállítások → Eszközök és szolgáltatások → Entitások**, keress rá: `idokep`. Jellemzően ilyenek: `weather.idokep_<hely>`, `sensor.idokep_temperature`, `sensor.idokep_weather_condition`, `binary_sensor.idokep_weather_alert`.
2. 🗑️ **Beállítások → Marketplace →** nyisd meg az **Időkép** (FabianGabor) oldalát, a jobb felső **⋮** menüben válaszd az **Uninstall**, majd a **Delete and uninstall** pontot.
3. 📦 Telepítsd ezt az integrációt (**Időkép Weather Component**), majd indítsd újra a Home Assistantet.
4. 📍 **Integráció hozzáadása → Időkép**, és add meg ugyanazt a települést, mint korábban.
5. ✏️ Az új entitásoknál (pl. `sensor.idokep_<hely>_temperature`) az entitás **Beállítások** ablakában írd át az **Entitásazonosítót** a régire (pl. `sensor.idokep_temperature`), majd **Frissítés**.

> [!NOTE]
> Átnevezéskor a naplóban ilyen figyelmeztetés jelenik meg: *„Cannot migrate history … because the new entity_id is already in use”*. Ez rendben van: a régi előzmények megmaradnak, csak az új azonosítón töltött néhány perc nem kerül át.

A `weather` entitás azonosítója általában eleve egyezik, azt nem kell átnevezni. Az automatizálások és a vezérlőpultok a régi azonosítókkal tovább működnek.

#### Régebbi Home Assistant HACS-szal

1. 🗑️ A HACS-ban nyisd meg a **HA-Idokep**-et, és válaszd az **Eltávolítás** pontot.
2. 🧹 Ha a HA-Idokep egyéni tárolóként (custom repository) volt felvéve, azt is törölheted a HACS **Egyéni tárolók** listájából.
3. 📦 Telepítsd ezt az integrációt a HACS-ból (**Időkép Weather Component**), majd indítsd újra a Home Assistantet.

> [!CAUTION]
> Az integráció bejegyzéseit (**Beállítások → Eszközök és szolgáltatások → Időkép**) **ne töröld**, különben az entitások újra létrejönnek, új azonosítóval.

✅ A bejegyzéseket az integráció automatikusan átveszi, az entitásazonosítók nem változnak. Megmarad:

- a weather entitás, a hőmérséklet és az állapot (angolul és magyarul),
- a rövid előrejelzés, a napkelte és a napnyugta,
- a zivatar és a kapcsolat szenzor,
- a riasztás szenzorok (`weather_alert`, `alert_yellow`, `alert_orange`, `alert_red`), ugyanazokkal az attribútumokkal.

🆕 Új entitásként jelenik meg a figyelmeztető előrejelzés (`warning_forecast`).

Ha valami mégsem jelenik meg, nézd meg a **Beállítások → Rendszer → Naplók** oldalt, és [jelezd a hibát](https://github.com/rinyakok/homeassistant_idokep/issues).

<a id="korlatok"></a>

### 🚧 Korlátok

- 🌐 **Nincs hivatalos API.** Az integráció az idokep.hu weboldalát olvassa. Ha az oldal szerkezete megváltozik, egyes adatok hiányozhatnak; a többi tovább frissül, és a naplóba kerül egy bejegyzés.
- ⏱️ **Frissítés 20 percenként**, településenként két oldal (30 napos előrejelzésnél három). A zivatar szenzor is ilyenkor frissül.
- 🇭🇺 **Csak magyarországi települések**, és csak azok, amelyeket az idokep.hu ismer.
- 💧 **Páratartalom, légnyomás és aktuális szél nincs:** ezek az idokep.hu előrejelzés oldalain nem szerepelnek. Óránkénti szélsebesség és -irány az előrejelzésben van.
- 💨 **A szélsebesség becslés:** az idokep.hu szélerősség-kategóriát mutat (pl. „mérsékelt”), ezt az integráció a kategória közepére (km/h) fordítja.
- ⚠️ **Színes riasztások:** ezeket a riasztási sáv és az óránkénti előrejelzés ikonjai alapján olvassa az integráció. Ha egy riasztás csak a radar oldalon látszik, itt nem jelenik meg.

<a id="gyik"></a>

### ❓ Gyakori kérdések

<details>
<summary><b>Budapesti adatokat kapok, pedig más települést adtam meg.</b></summary>

Az idokep.hu a számára ismeretlen nevekre Budapestet mutatja. Új beállításnál ezt az integráció kiszűri; régebbi bejegyzésnél a naplóban figyelmeztetés jelenik meg. Javítsd a nevet az **Újrakonfigurálás** ponttal.

</details>

<details>
<summary><b>Miért <code>unknown</code> az állapot?</b></summary>

Az idokep.hu olyan leírást adott, ami még nincs a fordítási listában. A naplóban látod, melyik az; jelezd hibajegyben.

</details>

<details>
<summary><b>Használható egyszerre a HA-Idokep-pel?</b></summary>

Nem, mert mindkettő ugyanazt az `idokep` azonosítót használja. Lásd: [Átállás a HA-Idokep integrációról](#atallas).

</details>

<details>
<summary><b>Hol van a napi előrejelzés a weather entitás attribútumai között?</b></summary>

A Home Assistant 2024 óta nem tárolja attribútumként. A `weather.get_forecasts` művelettel kérhető le, lásd: [Előrejelzés lekérése](#elorejelzes).

</details>

<details>
<summary><b>Miért nem frissül gyakrabban?</b></summary>

Az integráció kíméli az idokep.hu-t: 20 percenként, egyértelmű azonosítóval (User-Agent) kér adatot.

</details>

<a id="hibabejelentes"></a>

### 🐞 Hibabejelentés

Hibát vagy hiányzó időjárási állapotot a [GitHub hibajegyek](https://github.com/rinyakok/homeassistant_idokep/issues) között jelezhetsz. Hasznos, ha megadod:

- 📍 a település nevét,
- 🏠 a Home Assistant verzióját,
- 📜 a napló idevágó sorait (**Beállítások → Rendszer → Naplók**, szűrés: `idokep`).

---

<div align="center">

Az adatok forrása: [idokep.hu](https://www.idokep.hu) &nbsp;·&nbsp; Data provided by idokep.hu

</div>
