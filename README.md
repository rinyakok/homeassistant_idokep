# Időkép Weather for Home Assistant

Weather data, forecasts and weather alerts from [idokep.hu](https://www.idokep.hu) for places in Hungary.

> 🇬🇧 English summary below. **The full documentation is in Hungarian: [Magyar dokumentáció ↓](#magyar-dokumentáció)**
>
> 🇭🇺 Lent egy rövid angol összefoglaló található. **A részletes leírás magyarul: [Magyar dokumentáció ↓](#magyar-dokumentáció)**

## English summary

### Features

- Weather entity: current weather, 15-day (optionally 30-day) daily forecast and 36-hour hourly forecast with temperature, wind, precipitation and precipitation chance
- Sensors: temperature, condition (also as the Hungarian text), short text forecast, sunrise, sunset, warning forecast
- Binary sensors: weather alerts (any, yellow, orange, red), thunderstorm in the next hour, connection to idokep.hu
- Any number of places, one device per place
- English and Hungarian user interface

### Installation (HACS)

This integration is in the HACS default list.

1. Open **HACS**, search for **Időkép** and open **Időkép Weather Component**.
2. Select **Download**, then restart Home Assistant.

![HACS](https://github.com/user-attachments/assets/3d409403-e481-4b48-a9b8-7c2794d578a1)

Requires Home Assistant 2024.11 or newer. Manual installation: copy `custom_components/idokep` to `<config>/custom_components` and restart.

### Setup

1. **Settings → Devices & services → Add integration → Időkép**.
2. Type the place name as written on idokep.hu, e.g. **Pécs** (accents are optional: `erd` is saved as `Érd`).
3. Add more places the same way.

- **Options** (gear icon): daily forecast of 15 days (default) or 30 days. 30 days needs one more download per update.
- **Reconfigure** changes the place; entity IDs stay the same.

### Entities (for a place called Érd)

| Entity | Description |
|---|---|
| `weather.idokep_erd` | Current weather; daily and hourly forecast via `weather.get_forecasts` |
| `sensor.idokep_erd_temperature` | Temperature (°C) |
| `sensor.idokep_erd_condition` | Condition, e.g. `rainy` |
| `sensor.idokep_erd_condition_hungarian` | Condition as written on idokep.hu, e.g. "Erősen felhős" |
| `sensor.idokep_erd_short_forecast` | Short text forecast, e.g. "Kettősfronti hatás várható" |
| `sensor.idokep_erd_sunrise`, `sensor.idokep_erd_sunset` | Today's sunrise and sunset |
| `sensor.idokep_erd_warning_forecast` | Today's warning note, e.g. "Szeles nap"; all days in the `days` attribute |
| `binary_sensor.idokep_erd_weather_alert` | Any weather alert; details in the attributes |
| `binary_sensor.idokep_erd_yellow_alert` / `_orange_alert` / `_red_alert` | Alert of that level |
| `binary_sensor.idokep_erd_storm_in_the_next_hour` | Thunderstorm forecast for the current or next hour |
| `binary_sensor.idokep_erd_connection` | Diagnostic: off when idokep.hu can't be reached |

Entity IDs follow the Home Assistant language at the time the entity is created. The examples are for English.

### Switching from FabianGabor/HA-Idokep

Both use the `idokep` domain, so only one can be installed. Remove HA-Idokep in HACS but **keep its integration entries**, install this integration and restart. The entries are taken over and the entity IDs stay the same. [Step-by-step guide (Hungarian)](#átállás-a-ha-idokep-integrációról).

### Limits

idokep.hu has no public API. The integration reads the web pages every 20 minutes, so a change on the website can break parts of it. The rest keeps working, and the problem is logged. Please report problems in the [issue tracker](https://github.com/rinyakok/homeassistant_idokep/issues).

---

## Magyar dokumentáció

Időjárási adatok, előrejelzés és időjárási riasztások az [idokep.hu](https://www.idokep.hu)-ról, magyarországi településekre, Home Assistanthez.

- [Mit tud?](#mit-tud)
- [Telepítés](#telepítés)
- [Beállítás](#beállítás)
- [Entitások](#entitások)
- [Riasztások](#riasztások)
- [Előrejelzés lekérése](#előrejelzés-lekérése)
- [Időjárási állapotok](#időjárási-állapotok)
- [Vezérlőpult példák](#vezérlőpult-példák)
- [Automatizálás példák](#automatizálás-példák)
- [Átállás a HA-Idokep integrációról](#átállás-a-ha-idokep-integrációról)
- [Korlátok](#korlátok)
- [Gyakori kérdések](#gyakori-kérdések)
- [Hibabejelentés](#hibabejelentés)

### Mit tud?

- **Weather entitás:** aktuális időjárás, 15 napos (választhatóan 30 napos) napi és 36 órás óránkénti előrejelzés: hőmérséklet, szél, csapadék és csapadékesély
- **Szenzorok:** hőmérséklet, időjárási állapot (az idokep.hu magyar szövegével is), rövid szöveges előrejelzés, napkelte, napnyugta, figyelmeztető előrejelzés
- **Riasztások:** sárga, narancs és piros időjárási riasztás
- **Zivatar a következő órában**, és egy kapcsolat szenzor, ami jelzi, ha az idokep.hu nem érhető el
- **Több helyszín:** tetszőleges számú település, mindegyik külön eszközként („Időkép Érd”)
- **Magyar és angol felület**

### Telepítés

#### HACS-szal (ajánlott)

Az integráció benne van a HACS alapértelmezett listájában, egyéni tárolót (custom repository) nem kell felvenni.

1. Nyisd meg a **HACS**-t, és keress rá: **Időkép**.
2. Nyisd meg az **Időkép Weather Component**-et, és válaszd a **Letöltés** gombot.
3. Indítsd újra a Home Assistantet.

Legalább Home Assistant 2024.11 szükséges.

#### Kézzel

Másold a `custom_components/idokep` mappát a Home Assistant `<config>/custom_components` mappájába, majd indítsd újra a Home Assistantet.

### Beállítás

1. **Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása**, majd válaszd az **Időkép**-et.
2. Add meg a település nevét úgy, ahogy az idokep.hu-n szerepel. Például **Pécs** (`https://www.idokep.hu/idojaras/Pécs`).
   - Az ékezet elhagyható: az `erd` is Érdet jelenti. Az integráció az idokep.hu írásmódját menti el.
   - Ha az idokep.hu nem ismeri a nevet, Budapestet mutatja helyette. Ilyenkor a beállítás hibát jelez („Ezt a települést az idokep.hu nem ismeri, helyette ezt mutatja: Budapest”), így nem kapsz véletlenül budapesti adatokat.
3. További településekhez ismételd meg.

**Beállítások (fogaskerék):** a napi előrejelzés lehet 15 napos (alapértelmezett) vagy 30 napos. A 30 naposhoz frissítésenként eggyel több oldalt tölt le az integráció.

**Helyszín módosítása:** az integráció bejegyzésénél válaszd az **Újrakonfigurálás** pontot. Az entitásazonosítók nem változnak, így a vezérlőpultok és az automatizálások tovább működnek.

### Entitások

Egy „Érd” nevű helyszínnél, angol nyelvű Home Assistantben:

| Entitás | Leírás |
|---|---|
| `weather.idokep_erd` | Aktuális időjárás, napi és óránkénti előrejelzés |
| `sensor.idokep_erd_temperature` | Aktuális hőmérséklet (°C) |
| `sensor.idokep_erd_condition` | Aktuális állapot Home Assistant formában (pl. `rainy`, `partlycloudy`) |
| `sensor.idokep_erd_condition_hungarian` | Aktuális állapot úgy, ahogy az idokep.hu írja (pl. „Erősen felhős”) |
| `sensor.idokep_erd_short_forecast` | Rövid szöveges előrejelzés (pl. „Kettősfronti hatás várható”) |
| `sensor.idokep_erd_sunrise`, `sensor.idokep_erd_sunset` | Mai napkelte és napnyugta |
| `sensor.idokep_erd_warning_forecast` | A mai figyelmeztetés (pl. „Szeles nap”); az összes nap a `days` attribútumban |
| `binary_sensor.idokep_erd_weather_alert` | Bekapcsol, ha az idokep.hu bármilyen színes riasztást mutat |
| `binary_sensor.idokep_erd_yellow_alert`, `..._orange_alert`, `..._red_alert` | Bekapcsol, ha van ilyen szintű riasztás |
| `binary_sensor.idokep_erd_storm_in_the_next_hour` | Bekapcsol, ha az aktuális vagy a következő órára zivatart jeleznek |
| `binary_sensor.idokep_erd_connection` | Kikapcsol, ha az idokep.hu nem érhető el (diagnosztikai) |

Az entitásazonosítók a Home Assistant nyelvét követik az entitás létrehozásakor. Magyar nyelvnél például `sensor.idokep_erd_napkelte` lesz. A pontos azonosítót az entitás beállításainál látod.

A **weather entitás** további attribútumai: `short_forecast` (rövid előrejelzés), `precipitation` és `precipitation_probability` (a következő óra csapadéka mm-ben és csapadékesélye %-ban).

### Riasztások

Az idokep.hu kétféle figyelmeztetést mutat:

- **Színes riasztások** (sárga, narancs, piros), például „Sárga riasztás szélre”. Ezeket a `weather_alert` és a szintenkénti szenzorok jelzik. A `weather_alert` attribútumai:
  - `alert_count`: a riasztások száma
  - `yellow_alerts`, `orange_alerts`, `red_alerts`: szintenkénti darabszám
  - `alerts`: lista, elemenként `level` (szint), `type` (típus), `description` (az idokep.hu szövege) és `icon_url`

  A szintenkénti szenzorok attribútumai: `alert_count` és `alerts`.

  A `type` értékei: `wind` (szél), `storm` (vihar), `thunderstorm` (zivatar), `rain` (eső), `snow` (hó), `freezing_rain` (ónos eső), `fog` (köd), `heat` (hőség), `cold` (hideg), `frost` (fagy), egyéb esetben `general`.

- **Figyelmeztető előrejelzés** a napi előrejelzésben, szín nélkül, például „Sok eső”, „Szeles nap” vagy „Hidegfront erős széllel”. Ezt a `warning_forecast` szenzor mutatja: az állapota a mai figyelmeztetés (ha nincs, ismeretlen), a `days` attribútumban pedig az összes nap szerepel (`date`, `description`, `icon_url`).

### Előrejelzés lekérése

A Home Assistant az előrejelzést nem attribútumként tárolja, hanem a `weather.get_forecasts` művelettel lehet lekérni:

```yaml
action: weather.get_forecasts
target:
  entity_id: weather.idokep_erd
data:
  type: daily   # vagy: hourly
response_variable: elorejelzes
```

A napi előrejelzés elemei: `datetime`, `condition`, `temperature` (max), `templow` (min), `precipitation` (mm). Az óránkéntiéi: `datetime`, `condition`, `temperature`, `wind_speed` (km/h), `wind_bearing` (fok), `precipitation` (mm), `precipitation_probability` (%).

### Időjárási állapotok

Az idokep.hu magyar leírásait az integráció Home Assistant állapotokra fordítja:

| Home Assistant | idokep.hu |
|---|---|
| `sunny` (éjjel `clear-night`) | napos, derült |
| `partlycloudy` | gyengén felhős, közepesen felhős |
| `cloudy` | erősen felhős, borult |
| `rainy` | gyenge eső, eső, zápor, szitálás, eső viharos széllel |
| `pouring` | erős eső |
| `lightning-rainy` | zivatar |
| `lightning` | villámlás, száraz zivatar |
| `hail` | jégeső |
| `fog` | köd, ködös, ködszitálás, pára, párás |
| `snowy` | havazás, intenzív havazás, hószállingózás, hózápor, hófúvás, hófúvás havazással |
| `snowy-rainy` | havas eső, fagyott eső, ónos eső |
| `windy` | szeles |
| `exceptional` | porvihar |

Ha egy leírás még nincs a listában, az állapot ismeretlen lesz, és a naplóban egyszer megjelenik egy figyelmeztetés („Unknown idokep.hu weather condition …”). Kérlek, jelezd [hibajegyben](https://github.com/rinyakok/homeassistant_idokep/issues), és felvesszük.

### Vezérlőpult példák

**Időjárás kártya** napi és óránkénti előrejelzéssel:

```yaml
type: weather-forecast
entity: weather.idokep_erd
forecast_type: daily
show_forecast: true
```

**Részletek** egy kártyán:

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

**Riasztás kártya**, ami csak riasztáskor látszik:

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

### Automatizálás példák

**Értesítés narancs vagy piros riasztásnál:**

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

**Zivatar érkezik:**

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

**Este 8-kor: lesz-e holnap eső?**

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

### Átállás a HA-Idokep integrációról

A [FabianGabor/HA-Idokep](https://github.com/FabianGabor/HA-Idokep) és ez az integráció ugyanazt az `idokep` azonosítót használja, ezért egyszerre csak az egyik lehet telepítve. Ez az integráció a HA-Idokep bejegyzéseit közvetlenül át tudja venni:

1. A HACS-ban nyisd meg a **HA-Idokep**-et, és válaszd az **Eltávolítás** pontot. Az integráció bejegyzéseit (**Beállítások → Eszközök és szolgáltatások → Időkép**) **ne töröld**.
2. Ha a HA-Idokep egyéni tárolóként (custom repository) volt felvéve, azt is törölheted a HACS **Egyéni tárolók** listájából.
3. Telepítsd ezt az integrációt a HACS-ból (**Időkép Weather Component**), majd indítsd újra a Home Assistantet.

A bejegyzéseket az integráció automatikusan átveszi, az entitásazonosítók nem változnak. Megmarad a weather entitás, a hőmérséklet, az állapot (angolul és magyarul), a rövid előrejelzés, a napkelte és a napnyugta, a zivatar és a kapcsolat szenzor, valamint a riasztás szenzorok (`weather_alert`, `alert_yellow`, `alert_orange`, `alert_red`), ugyanazokkal az attribútumokkal. Új entitásként jelenik meg a figyelmeztető előrejelzés (`warning_forecast`).

Ha valami mégsem jelenik meg, nézd meg a **Beállítások → Rendszer → Naplók** oldalt, és [jelezd a hibát](https://github.com/rinyakok/homeassistant_idokep/issues).

### Korlátok

- **Nincs hivatalos API.** Az integráció az idokep.hu weboldalát olvassa. Ha az oldal szerkezete megváltozik, egyes adatok hiányozhatnak; a többi tovább frissül, és a naplóba kerül egy bejegyzés.
- **Frissítés 20 percenként**, településenként két oldal (30 napos előrejelzésnél három). A zivatar szenzor is ilyenkor frissül.
- **Csak magyarországi települések**, és csak azok, amelyeket az idokep.hu ismer.
- **Páratartalom, légnyomás és aktuális szél** nincs: ezek az idokep.hu előrejelzés oldalain nem szerepelnek. Óránkénti szélsebesség és -irány az előrejelzésben van.
- **A szélsebesség becslés:** az idokep.hu szélerősség-kategóriát mutat (pl. „mérsékelt”), ezt az integráció a kategória közepére (km/h) fordítja.
- **Színes riasztások:** ezeket a riasztási sáv és az óránkénti előrejelzés ikonjai alapján olvassa az integráció. Ha egy riasztás csak a radar oldalon látszik, itt nem jelenik meg.

### Gyakori kérdések

**Budapesti adatokat kapok, pedig más települést adtam meg.**
Az idokep.hu a számára ismeretlen nevekre Budapestet mutatja. Új beállításnál ezt az integráció kiszűri; régebbi bejegyzésnél a naplóban figyelmeztetés jelenik meg. Javítsd a nevet az **Újrakonfigurálás** ponttal.

**Miért `unknown` az állapot?**
Az idokep.hu olyan leírást adott, ami még nincs a fordítási listában. A naplóban látod, melyik az; jelezd hibajegyben.

**Használható egyszerre a HA-Idokep-pel?**
Nem, mert mindkettő ugyanazt az `idokep` azonosítót használja. Lásd: [Átállás a HA-Idokep integrációról](#átállás-a-ha-idokep-integrációról).

**Hol van a napi előrejelzés a weather entitás attribútumai között?**
A Home Assistant 2024 óta nem tárolja attribútumként. A `weather.get_forecasts` művelettel kérhető le, lásd: [Előrejelzés lekérése](#előrejelzés-lekérése).

**Miért nem frissül gyakrabban?**
Az integráció kíméli az idokep.hu-t: 20 percenként, egyértelmű azonosítóval (User-Agent) kér adatot.

### Hibabejelentés

Hibát vagy hiányzó időjárási állapotot a [GitHub hibajegyek](https://github.com/rinyakok/homeassistant_idokep/issues) között jelezhetsz. Hasznos, ha megadod:

- a település nevét,
- a Home Assistant verzióját,
- a napló idevágó sorait (**Beállítások → Rendszer → Naplók**, szűrés: `idokep`).
