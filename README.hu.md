# Időkép időjárás Home Assistanthez

Időjárási adatok és előrejelzés az [idokep.hu](https://www.idokep.hu)-ról, magyarországi településekre.

**[English description →](https://github.com/rinyakok/homeassistant_idokep/blob/main/README.md)**

## Mit tud?

- **Weather entitás:** aktuális időjárás, 15 napos napi és 36 órás óránkénti előrejelzés (hőmérséklet, szél, csapadék és csapadékesély)
- **Szenzorok:** hőmérséklet, időjárási állapot (magyarul is), rövid szöveges előrejelzés, napkelte, napnyugta
- **Riasztások:** sárga, narancs és piros időjárási riasztás, valamint figyelmeztető előrejelzés napokra („Sok eső”, „Szeles nap”)
- **Bináris szenzorok:** zivatar a következő órában, kapcsolat az idokep.hu-val
- **Több helyszín:** tetszőleges számú település, mindegyik külön eszközként
- **Magyar és angol felület**

## Telepítés

### HACS-szal (ajánlott)

1. Nyisd meg a HACS-t, és keress rá: **Időkép**.
2. Válaszd az **Időkép Weather Component**-et, majd **Letöltés**.
3. Indítsd újra a Home Assistantet.

![HACS](https://github.com/user-attachments/assets/3d409403-e481-4b48-a9b8-7c2794d578a1)

### Kézzel

Másold a `custom_components/idokep` mappát a Home Assistant `<config>/custom_components` mappájába, majd indítsd újra a Home Assistantet.

## Beállítás

1. **Beállítások → Eszközök és szolgáltatások → Integráció hozzáadása**, majd válaszd az **Időkép**-et.
2. Add meg a település nevét úgy, ahogy az idokep.hu-n szerepel. Például **Pécs** (`https://www.idokep.hu/idojaras/Pécs`).
   - Az ékezet elhagyható: az `erd` is Érdet jelenti. Az integráció az idokep.hu írásmódját menti el.
   - Ha az idokep.hu nem ismeri a nevet, Budapestet mutatja helyette. Ilyenkor a beállítás hibát jelez, így nem kapsz véletlenül budapesti adatokat.
3. További településekhez ismételd meg.

**30 napos előrejelzés:** az integráció bejegyzésénél a **Beállítások** (fogaskerék) pontban választható a 15 napos (alapértelmezett) vagy a 30 napos napi előrejelzés. A 30 naposhoz frissítésenként eggyel több oldalt tölt le az integráció.

**Helyszín módosítása:** az integráció bejegyzésénél válaszd az **Újrakonfigurálás** pontot. Az entitásazonosítók nem változnak, így a vezérlőpultok és az automatizálások tovább működnek.

## Entitások

Egy „Érd” nevű helyszínnél:

| Entitás | Leírás |
|---|---|
| `weather.idokep_erd` | Aktuális időjárás, napi és óránkénti előrejelzés |
| `sensor.idokep_erd_temperature` | Aktuális hőmérséklet (°C) |
| `sensor.idokep_erd_condition` | Aktuális állapot Home Assistant formában (pl. `rainy`, `partlycloudy`) |
| `sensor.idokep_erd_condition_hungarian` | Aktuális állapot úgy, ahogy az idokep.hu írja (pl. „Erősen felhős”) |
| `sensor.idokep_erd_short_forecast` | Rövid szöveges előrejelzés (pl. „Kettősfronti hatás várható”) |
| `sensor.idokep_erd_sunrise`, `sensor.idokep_erd_sunset` | Mai napkelte és napnyugta |
| `binary_sensor.idokep_erd_storm_in_the_next_hour` | Bekapcsol, ha az aktuális vagy a következő órára zivatart jeleznek |
| `binary_sensor.idokep_erd_connection` | Kikapcsol, ha az idokep.hu nem érhető el (diagnosztikai) |
| `binary_sensor.idokep_erd_weather_alert` | Bekapcsol, ha az idokep.hu bármilyen riasztást mutat; a riasztások az attribútumokban |
| `binary_sensor.idokep_erd_yellow_alert`, `..._orange_alert`, `..._red_alert` | Bekapcsol, ha van ilyen szintű riasztás |
| `sensor.idokep_erd_warning_forecast` | A mai figyelmeztetés (pl. „Szeles nap”); az összes nap a `days` attribútumban |

A weather entitásnak további attribútumai is vannak: `short_forecast` (rövid előrejelzés), `precipitation` és `precipitation_probability` (a következő óra csapadéka és csapadékesélye).

### Riasztások

Az idokep.hu kétféle figyelmeztetést mutat:

- **Színes riasztások** (sárga, narancs, piros), például „Sárga riasztás szélre”. Ezeket a `weather_alert` és a szintenkénti szenzorok jelzik. A `weather_alert` attribútumai:
  - `alert_count`: a riasztások száma
  - `yellow_alerts`, `orange_alerts`, `red_alerts`: szintenkénti darabszám
  - `alerts`: lista, elemenként `level` (szint), `type` (típus, pl. `wind`, `thunderstorm`, `freezing_rain`), `description` (az idokep.hu szövege) és `icon_url`
- **Figyelmeztető előrejelzés** a napi előrejelzésben, szín nélkül, például „Sok eső” vagy „Hidegfront erős széllel”. Ezt a `warning_forecast` szenzor mutatja: az állapota a mai figyelmeztetés, a `days` attribútumban pedig az összes nap szerepel (`date`, `description`, `icon_url`).

**Példa** – értesítés narancs vagy piros riasztásnál:

```yaml
automation:
  - alias: "Időjárási riasztás"
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

Az entitásazonosítók a Home Assistant nyelvét követik az entitás létrehozásakor. A fenti példák angol nyelvű Home Assistantre vonatkoznak; magyar nyelvnél például `sensor.idokep_erd_napkelte` lesz.

**Zivatar szenzor példa** – értesítés, ha zivatar jön:

```yaml
automation:
  - alias: "Zivatar érkezik"
    triggers:
      - trigger: state
        entity_id: binary_sensor.idokep_erd_storm_in_the_next_hour
        to: "on"
    actions:
      - action: notify.notify
        data:
          message: "Zivatar várható a következő órában Érden."
```

Az előrejelzést a `weather.get_forecasts` művelettel lehet lekérni (`type: daily` vagy `type: hourly`).

### Időjárási állapotok

Az idokep.hu magyar leírásait az integráció Home Assistant állapotokra fordítja. Néhány példa:

| idokep.hu | Home Assistant |
|---|---|
| derült, napos | `sunny` (éjjel `clear-night`) |
| gyengén / közepesen felhős | `partlycloudy` |
| erősen felhős, borult | `cloudy` |
| gyenge eső, eső, zápor, szitálás | `rainy` |
| erős eső | `pouring` |
| zivatar | `lightning-rainy` |
| köd, ködös, pára | `fog` |
| havazás, hózápor | `snowy` |
| havas eső, ónos eső | `snowy-rainy` |
| porvihar | `exceptional` |

Ha egy leírás még nincs a listában, az állapot ismeretlen lesz, és a naplóban egy figyelmeztetés jelenik meg. Kérlek, jelezd [hibajegyben](https://github.com/rinyakok/homeassistant_idokep/issues), és felvesszük.

## Átállás a HA-Idokep integrációról

A FabianGabor/HA-Idokep és ez az integráció ugyanazt az `idokep` azonosítót használja, ezért egyszerre csak az egyik lehet telepítve. Az átállás:

1. A HACS-ban távolítsd el a **HA-Idokep**-et. Az integráció bejegyzéseit (**Beállítások → Eszközök és szolgáltatások**) **ne töröld**.
2. Ha a HA-Idokep egyéni tárolóként (custom repository) volt felvéve, azt is törölheted a HACS-ból.
3. Telepítsd ezt az integrációt a HACS-ból, majd indítsd újra a Home Assistantet.

A meglévő bejegyzéseket az integráció automatikusan átveszi. A közös entitások (weather, hőmérséklet, állapot) azonosítója nem változik. A HA-Idokep napkelte, napnyugta, rövid előrejelzés, magyar állapot, zivatar és kapcsolat entitásai is megmaradnak. A riasztás entitások (`weather_alert`, `alert_yellow`, `alert_orange`, `alert_red`) is megmaradnak, ugyanazokkal az attribútumokkal.

## Hogyan működik?

Az integráció 20 percenként, településenként két oldalt tölt le az idokep.hu-ról (`/idojaras/` és `/elorejelzes/`), és ezekből olvassa ki az adatokat. Hivatalos API nincs, ezért ha az oldal szerkezete megváltozik, egyes adatok hiányozhatnak. Az integráció ilyenkor a többi adatot tovább frissíti, és a naplóba ír.

## Hibabejelentés

Hibát vagy hiányzó időjárási állapotot a [GitHub hibajegyek](https://github.com/rinyakok/homeassistant_idokep/issues) között jelezhetsz. Hasznos, ha megadod a település nevét és a Home Assistant naplójának idevágó sorait.
