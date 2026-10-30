# Uncanny Eyes - ESP32-C3 Super Mini

Animatronic eyes ("Uncanny Eyes") auf zwei runden 1,28" GC9A01-Displays
(240x240) am ESP32-C3 Super Mini. Portiert von
[dalori/ESP32-uncanny-eyes-halloween-skull](https://github.com/dalori/ESP32-uncanny-eyes-halloween-skull)
(Arduino IDE + TFT_eSPI) auf **PlatformIO + LovyanGFX**.

Der Grund für den Port: TFT_eSPI verlangt die Pin-Konfiguration in
`User_Setup.h` innerhalb der Bibliothek. LovyanGFX nimmt alle Pins aus dem
Projekt-Config-File - genau wie im Referenzprojekt
[synex-c21/ESP32-Plane-Radar-metrers](https://github.com/synex-c21/ESP32-Plane-Radar-metrers),
dessen Display-Anschluss hier unverändert übernommen wurde.

Alle Konfiguration: **include/config.h** (Pins, Verhalten) und
**src/eyes/eye_assets.cpp** (Eye-Style).

## Verdrahtung

Beide Displays hängen am selben SPI-Bus, nur CS ist pro Auge einzeln:

| Super Mini (C3) | TFT 1 (linkes Auge) | TFT 2 (rechtes Auge) |
|-----------------|---------------------|----------------------|
| GPIO3           | SDA                 | SDA                  |
| GPIO4           | SCL                 | SCL                  |
| GPIO10          | DC                  | DC                   |
| GPIO0           | RST                 | RST                  |
| GPIO1           | CS                  | -                    |
| GPIO2           | -                   | CS                   |
| 3V3             | VCC                 | VCC                  |
| GND             | GND                 | GND                  |

Pin-Layout identisch zum Radar-Projekt, plus ein zweiter CS (GPIO2).

Optionale Eingänge:

| Super Mini (C3) | Funktion                          |
|-----------------|-----------------------------------|
| GPIO9 (BOOT)    | Blink-Button (beide Augen, nach GND) |
| GPIO6/7/8       | frei für Wink-Buttons pro Auge (config.h) |
| GPIO5           | Kiefer-Servo (config.h aktivieren) |

Servo-Strom nicht vom 3V3-Pin nehmen (Flackern) - siehe Original-README.

## Bauen und Flashen

```bash
pio run                 # kompilieren
pio run -t upload      # flashen
pio device monitor     # Seriell 115200 (FPS-Ausgabe)
```

Onder Visual Studio Code mit der PlatformIO-Erweiterung: Projektordner
öffnen, unten die Umgebung `supermini` wählen, Build/Upload.

## Nur ein Display angeschlossen?

Zum Test mit dem einzelnen Radar-Aufbau in `include/config.h` setzen:

```c
#define EYE_COUNT 1
```

Das Auge laeuft dann auf TFT 1 (CS = GPIO1).

## Eye-Styles

Alle zehn Stile liegen fertig in `data/eyes/`:

| Datei | Stil |
|-------|------|
| `default_large.h` | menschliches Hazel-Auge (nativ 240px, aus dem Originalprojekt) |
| `catEye_240.h` | karikaturenhaftes Katzenauge (flache "2D"-Farben) |
| `doeEye_240.h` | Reh-Auge (Original: ohne Tracking am besten) |
| `dragonEye_240.h` | Drachen-/Dämonenauge mit Schlitzpupille |
| `goatEye_240.h` | Ziegen-/Krampus-Auge mit horizontaler Pupille |
| `naugaEye_240.h` | Nauga-Glotzauge (Original: ohne Tracking am besten) |
| `newtEye_240.h` | Molchauge |
| `noScleraEye_240.h` | grosse Iris, keine Sklera |
| `owlEye_240.h` | Eulenauge (Original: ohne Tracking am besten) |
| `terminatorEye_240.h` | Git to da choppah! |

Aktiviert wird genau ein Include in `src/eyes/eye_assets.cpp` (alle anderen
auskommentiert). Entweder von Hand aendern oder per Skript:

```bash
python scripts/toggle_style.py dragonEye_240   # Stil aktivieren
python scripts/toggle_style.py default_large    # zurueck zum Standard
```

Die `*_240.h`-Dateien sind aus den 128px-Originalen in `data/eyes/128/` mit
`scripts/scale_eye_assets.py` generiert (Faktor 240/128 = 1,875; Sclera,
Iris-Map und Lid-Masks bilinear - die Iris-Map mit zylindrischem Wrap in x,
Polar-Map mit Nearest-Neighbor auf Code-Ebene, IRIS_MIN/MAX mitskaliert).
`scripts/check_asset.py` prueft generierte Header auf Konsistenz. Alle Stile
wurden einzeln kompiliert (erfolgreich, Flash 42-52 % der 2-MB-App-Partition).

Hinweise zum Verhalten:
- Irisgroesse: `kIrisEdgeTrimPx` in include/config.h verkleinert die sichtbare
  Iris-Scheibe pro Kante um N Pixel (der Rand zeigt dann Sklera); 0 = wie im
  Asset. Die Pupillengroesse haengt an IRIS_MIN/IRIS_MAX im Asset-Header
  (groessere Werte = kleinere Pupille).
- Die Lid-Animation steckt in den upper/lower-MAPS je Stil, nicht im Code.
  Beim Menschen-Auge (default_large) folgt das obere Lid dem Blick deutlich
  (19-58 % Bedeckung), das untere ist bewusst zurueckhaltend (22-38 %,
  gekoppelt). Beim Drachen-Auge sind beide Lider fast statisch - das ist
  der Stil (finsterer Schlitzblick), kein Fehler.
- Stile mit "(Original: ohne Tracking)" sehen mit `kPupilTracking = false`
  in include/config.h am besten aus.

## Eigenes Auge aus einem Bild erstellen

`scripts/make_eye_from_image.py` baut aus einem Bild (runder Augapfel auf
dunklem Hintergrund, z.B. `data/eyes/images/eye_test.png`) einen kompletten
Stil: Geometrie, Polar-Map und Lid-Masks entsprechen exakt dem Standard-Auge
(default_large), die Farben stammen komplett aus dem Bild.

```bash
python scripts/make_eye_from_image.py data/eyes/images/eye_test.png data/eyes/eye_test_240.h
python scripts/check_asset.py data/eyes/eye_test_240.h    # Konsistenz
python scripts/simulate_render.py data/eyes/eye_test_240.h  # ASCII/Preview-PNG
python scripts/validate_render.py data/eyes/eye_test_240.h  # Zahlencheck
python scripts/toggle_style.py eye_test_240                  # aktivieren
```

Was das Skript macht: es erkennt Augenmitte, Pupillenradius, Iris-Aussenradius
und Augapfelradius (manuell ueberschreibbar mit --center/--iris-radius/...).
Die Sklera-Textur (375x375) entsteht so, dass die Iris-Kante exakt an der
Polar-Box-Kante (Radius 90px) landet - der Uebergang Overlay/Textur ist nahtlos.
Die Pupille wird als solide Scheibe bis zur maximalen Weitstellung bemalt,
damit bei jeder Pupillengroesse kein Sklera-Ring durchscheint. Die Iris-Map
(489x122) ist die polar-abgewickelte Iris-Ring-Textur des Bildes.
`*_preview.png` neben dem Asset zeigt je drei Pupillengroessen und einen
Lid-Frame zur visuellen Kontrolle vor dem Flashen.

## Architektur / Port-Hinweise

- LovyanGFX 1.2.x kennt keine Multi-Panels. Daher wie im Original: ein
  Bus, CS-Pins werden manuell getoggelt (`src/hardware/display.cpp`,
  `src/eyes/eye_render.cpp`). Das Panel hat `pin_cs = -1`.
- Rendering: Pixel-Loop ueber sclera/iris/polar/lid-Tabellen, RGB565
  Byte-Swap in Software, Push per `writePixelsDMA` mit zwei Ping-Pong-
  Buffern (1024 Pixel).
- Die ~580 KB Asset-Tabellen liegen im Flash; deshalb Partitions-Tabelle
  `no_ota.csv` (2 MB App-Partition).
- Der ESP32-C3 ist einkernig und langsamer als der ESP32 des Originals
  (dort 32 FPS mit zwei Augen). Die FPS-Ausgabe alle 256 Frames zeigt das
  reale Ergebnis; erster Anhaltspunkt zur Optimierung: SPI-Takt in
  config.h (`kDisplaySpiWriteHz`) testweise auf 60-80 MHz erhoeht.
- **Farbreihenfolge:** `kDisplayRgbOrder` muss false sein (config.h, dort
  auch begruendet). Der Eye-Renderer pusht Rohdaten ohne LovyanGFX-
  Farbkonvertierung; die Assets sind Standard-RGB565 (verifizierbar mit
  `scripts/check_color_order.py`). Mit rgb_order=true wuerde das Panel
  Rot und Blau tauschen.
- Nicht portiert (bisher): Joystick-Steuerung und Lichtsensor-Iris
  (`LIGHT_PIN`) - Standard des Originals war ohnehin autonome Bewegung.

## Quellen / Lizenzen

- Augen-Grafiken und Algorithmen: Adafruit "Uncanny Eyes" von Phil Burgess,
  MIT-Lizenz, adaptiert von dalori/ESP32-uncanny-eyes-halloween-skull.
  Originale Sketchdateien: docs/reference/.
- Display-Anbindung orientiert an synex-c21/ESP32-Plane-Radar-metrers.
