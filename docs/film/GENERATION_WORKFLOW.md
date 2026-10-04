# Ablauf zur Erzeugung eines GS-DOE-Films

Diese Anleitung beschreibt den vollständigen Arbeitsablauf mit `GDoeSII_Film_GS_Batch.exe` – vom Ausgangsbild bzw. den Zielbildern bis zu den 16-Bit-DOE-Dateien, Simulationen, Helligkeitsdaten und dem Ringlayout.

Der Filmgenerator ist bewusst auf **Arbitrary Image / Gerchberg-Saxton (GS)** beschränkt. Lens, Grating, Fresnel Zone Plate und Vortex gehören zum separaten Einzel-DOE-Generator.

## 1. Film-GUI starten

Windows-Artefakt bzw. lokale EXE starten:

```text
GDoeSII_Film_GS_Batch.exe
```

Die Oberfläche ist scrollbar. Das Mausrad scrollt vertikal, `Shift + Mausrad` horizontal.

## 2. Eingangsmodus wählen

Es gibt zwei Wege.

### A. Vorhandene Zielbilder verwenden

`Input mode`:

```text
Use existing frame directory
```

Dann unter `Target frame directory` den Ordner mit den Einzelbildern auswählen.

Unterstützte Formate:

```text
.png .tif .tiff .jpg .jpeg .bmp
```

Die Dateien werden nach Dateinamen sortiert. Für eine 48-Frame-Sequenz empfiehlt sich daher:

```text
frame_000.png
frame_001.png
...
frame_047.png
```

### B. Rotationsframes aus einem Ausgangsbild erzeugen

`Input mode`:

```text
Generate 360-degree yaw frames from source image
```

Dann `Source image` auswählen und die Frame-Erzeugung einstellen.

Typische Werte für eine 48-Frame-Umdrehung:

```text
Frame count:          48
Frame canvas:       1024 px
Front image width:   600 px
Perspective distance: 4.0
```

Bei 48 Frames beträgt der nominelle Winkelschritt:

```text
360 deg / 48 = 7.5 deg
```

Für die Intensitätsumsetzung stehen nur allgemeine Graustufenmodi zur Verfügung:

```text
grayscale as intensity
invert grayscale
```

`grayscale as intensity` bedeutet: helle Bildbereiche werden zu hoher Sollintensität.

`invert grayscale` bedeutet: dunkle Bildbereiche werden zu hoher Sollintensität. Dieser Modus ist beispielsweise für dunkle Logos auf weißem Hintergrund geeignet.

Die erzeugten Zielbilder werden nach

```text
frames_raw/
```

geschrieben. Zusätzlich enthält `frames_raw/frames.json` die Framewinkel, die verwendete Frontbreite und die Projektionsgeometrie der erzeugten Frames.

Bei exakt 90 und 270 Grad wäre die projektive Transformation mathematisch singulär. Diese beiden Ansichten werden deshalb intern mit einem sehr kleinen Winkelversatz von 0.15 Grad gerendert; der nominelle Winkel bleibt in den Metadaten 90 bzw. 270 Grad.

## 3. Ausgabeordner festlegen

Unter `Output directory` einen neuen bzw. leeren Projektordner auswählen, zum Beispiel:

```text
D:\DOE_Film\POF_48frames\
```

Alle Batch-Ergebnisse werden darunter strukturiert abgelegt.

## 4. GS- und Optikparameter einstellen

Für den vorgesehenen physikalischen Projektionsbetrieb ist `Physical projection` der Standard.

Referenzwerte für das bisherige Filmkonzept:

```text
DOE width:          4096 px
DOE height:         4096 px
DOE pixel size:      500 nm
Wavelength:          532 nm
Target z:            300 mm
Target width:         50 mm
Propagation mode:    Physical projection
GS iterations:        50
GS seed:               0
```

### Physical projection

Der Modus verwendet unterschiedliche Abtastungen in DOE- und Zielebene. Die Zielrasterweite wird aus

```text
dx_target = lambda * z / (N * dx_DOE)
```

berechnet.

Für

```text
N       = 4096
lambda  = 532 nm
z       = 300 mm
dx_DOE  = 500 nm
```

ergibt sich:

```text
Target pitch:  77.9296875 um/px
Target field:  319.2 x 319.2 mm
```

Eine 50-mm-Zielbreite entspricht damit ungefähr:

```text
641.6 Zielpixeln
```

Die GUI zeigt diese abgeleiteten Werte direkt unter den Optikparametern an.

Bei automatisch erzeugten Yaw-Frames bezieht sich `Target width` auf die in `frames.json` gespeicherte frontale Bildbreite, nicht auf den kompletten dunklen Frame-Rand. Bei beispielsweise 600 px Frontbreite in einem 1024-px-Canvas bleibt das frontal sichtbare Motiv daher 50 mm breit; die dunkle Umgebung wird zusätzlich mitgeführt.

### Same sampling

`Same sampling` ist für Kompatibilität, kleine Zielfelder und den derzeitigen Pan/Tilt-GS-Pfad gedacht. Für große reale Projektionsflächen wie 50 mm bei 300 mm sollte `Physical projection` verwendet werden.

## 5. Zielposition einstellen

Für die normale Filmgeometrie:

```text
Target X:    0 mm
Target Y:    0 mm
Target pan:  0 deg
Target tilt: 0 deg
```

X/Y verschiebt die Zielrichtung relativ zur optischen Achse.

Wichtig: `Physical projection` unterstützt derzeit nur eine parallele Zielfläche:

```text
pan  = 0 deg
tilt = 0 deg
```

Pan/Tilt steht weiterhin im `Same sampling`-Modus zur Verfügung. Eine Kombination aus skaliertem Physical Projection und geneigter Zielfläche wird derzeit bewusst nicht approximiert.

## 6. Helligkeitsanalyse einstellen

`Active threshold` definiert, welche Bereiche des Zielbildes zur aktiven Sollfläche gehören. Ein Startwert ist:

```text
0.05
```

Für `Brightness analysis / Mode` stehen zur Verfügung:

```text
constant reconstructed brightness
preserve geometric brightness
analysis only
```

### Constant reconstructed brightness

Nach der GS-Berechnung wird pro Frame der Anteil der rekonstruierten Leistung im gewünschten Zielbereich bestimmt. Der ineffizienteste Frame dient als Referenz. Für effizientere Frames wird ein Dämpfungsfaktor `0 ... 1` berechnet.

Der Wert steht in:

```text
statistics/brightness_statistics.csv
```

als

```text
recommended_laser_or_duty_factor
```

Dieser Faktor ist für eine externe synchronisierte Laserleistungs- bzw. Duty-Cycle-Regelung gedacht. Er wird nicht automatisch in das reine Phasen-DOE eingebaut.

### Preserve geometric brightness

Zusätzlich zur Effizienzkorrektur wird die geometrische Helligkeitsänderung einer rotierenden Fläche berücksichtigt:

```text
abs(cos(frame_angle)) ** gamma
```

`Geometric gamma = 0.5` ist ein sinnvoller Ausgangswert.

### Analysis only

Es werden nur die Messgrößen ausgegeben; es wird keine Helligkeitskorrektur empfohlen.

Bei einer rein passiven Scheibe mit konstantem, nicht synchronisiertem Laser können die berechneten Dämpfungsfaktoren nicht aktiv umgesetzt werden. Sie dienen dann zunächst zur Bewertung der zu erwartenden Frame-zu-Frame-Schwankungen.

## 7. Ringlayout einstellen

Typische Werte:

```text
Ring pitch:             2.5 mm
Ring radius:              0 mm   # auto
DOE orientation: tangential
```

Bei `Ring radius = 0` wird automatisch gerechnet:

```text
R = frame_count * pitch / (2*pi)
```

Für 48 Frames und 2.5 mm Pitch:

```text
R = 19.0986 mm
```

Die möglichen Orientierungen sind:

```text
tangential
radial
fixed
```

Das Ringlayout beeinflusst nicht die GS-Berechnung. Jedes DOE wird zunächst in seinem lokalen Koordinatensystem berechnet; Position und Drehung auf der Scheibe werden erst als Layoutdaten ausgegeben.

## 8. Vorabtest durchführen

Vor einem vollständigen 4096-x-4096-Lauf sollte die Pipeline zuerst mit kleiner Auflösung geprüft werden, zum Beispiel:

```text
DOE:          512 x 512 px
GS iterations: 10 ... 20
Frames:         2 ... 8
```

Dabei prüfen:

- werden die gewünschten Frames eingelesen bzw. erzeugt,
- stimmt die Reihenfolge,
- ist die Intensitätsinvertierung korrekt,
- sieht die Rekonstruktion in `simulation/` plausibel aus,
- enthält `brightness_statistics.csv` sinnvolle Werte,
- stimmt das Ringlayout.

Dieser Test vermeidet einen langen 4096-x-4096-Batch mit falschen Einstellungen.

## 9. Frames optional vorab analysieren

Mit

```text
Analyze frames
```

wird nur die Eingangssequenz analysiert. Es werden noch keine DOEs berechnet.

Ergebnis:

```text
statistics/frame_source_statistics.csv
```

Darin stehen unter anderem:

- Summe und Mittelwert der normierten Intensität,
- Anzahl und Anteil aktiver Pixel,
- aktive Bounding-Box,
- Framewinkel.

Dieser Schritt ist optional. `Run GS batch` führt die Analyse ebenfalls im vollständigen Prozess aus.

## 10. GS-Batch starten

Mit

```text
Run GS batch
```

startet die eigentliche Erzeugung.

Für jedes Frame läuft unabhängig:

```text
Zielbild laden
    -> Zielbild auf physikalisches Zielraster setzen
    -> zufälliges Startphasenfeld mit definiertem Seed
    -> GS Vorwärtspropagation
    -> Sollamplitude im Ziel einsetzen
    -> GS Rückpropagation
    -> Phasenbedingung in DOE-Ebene anwenden
    -> Iterationen wiederholen
    -> finale DOE-Phase erzeugen
    -> Zielrekonstruktion simulieren
    -> Leistungs-/Helligkeitswerte bestimmen
    -> 16-Bit-DOE und Metadaten speichern
```

Die Frames werden sequentiell verarbeitet. Dadurch bleibt der Speicherbedarf begrenzt und fertige Ergebnisse liegen bereits vor, bevor der gesamte Batch abgeschlossen ist.

## 11. Ergebnisse prüfen

Nach erfolgreichem Batch entsteht beispielsweise:

```text
film_batch_output/
├── film_config.json
├── summary.json
├── frames_raw/                 # nur bei interner Frame-Erzeugung
│   ├── frame_000.png
│   ├── ...
│   └── frames.json
├── doe/
│   ├── DOE_000.png
│   ├── DOE_000.json
│   ├── DOE_001.png
│   └── ...
├── simulation/
│   ├── sim_000.png
│   ├── sim_001.png
│   └── ...
├── statistics/
│   ├── frame_source_statistics.csv
│   └── brightness_statistics.csv
└── layout/
    └── DOE_ring_layout.csv
```

### `film_config.json`

Enthält die vollständigen Batch-Einstellungen. Diese Datei ist wichtig für die Reproduzierbarkeit.

### `summary.json`

Enthält eine Zusammenfassung des Laufs und bei Physical Projection die abgeleitete physikalische Zielabtastung.

### `doe/DOE_NNN.png`

Das eigentliche 16-Bit-Phasen-DOE für Frame `NNN`.

### `doe/DOE_NNN.json`

Metadaten des einzelnen DOE, einschließlich Optik-, Ziel- und Propagationsparametern.

### `simulation/sim_NNN.png`

Normierte Simulation der rekonstruierten Zielintensität. Diese Dateien sollten vor der Fertigung visuell kontrolliert werden.

### `statistics/frame_source_statistics.csv`

Statistik der Eingangsbilder.

### `statistics/brightness_statistics.csv`

Rekonstruktionsleistung und Helligkeitsvergleich der Frames. Besonders relevant sind:

```text
target_power_fraction
recommended_laser_or_duty_factor
```

### `layout/DOE_ring_layout.csv`

Enthält für jedes DOE:

```text
Frameindex
Dateiname
X/Y-Mittelpunkt auf der Scheibe
Sektorwinkel
DOE-Rotationswinkel
Ringradius
Pitch
```

Diese Datei gehört zur späteren Anordnung der einzelnen DOE-Felder auf dem Substrat.

## 12. Finalen Film rechnen

Erst nach erfolgreichem Testlauf auf die endgültigen Parameter wechseln, zum Beispiel:

```text
Frames:             48
DOE raster:         4096 x 4096
DOE pitch:          500 nm
Wavelength:         532 nm
Target z:           300 mm
Target width:        50 mm
Propagation:        Physical projection
GS iterations:       50
Pan / Tilt:           0 / 0 deg
Ring pitch:           2.5 mm
Ring orientation: tangential
```

Ein 48-Frame-Batch mit 4096 x 4096 Pixeln und vielen GS-Iterationen ist rechenintensiv. Deshalb sollte die finale Rechnung erst nach erfolgreicher Prüfung eines kleinen Batches gestartet werden.

## 13. Vor der Fertigung

Vor Verwendung der DOE-Dateien für die Lithographie mindestens prüfen:

1. alle 48 DOE-Dateien und Metadaten sind vorhanden,
2. die Simulationen zeigen die richtige Frame-Reihenfolge und Orientierung,
3. die physikalische Zielbreite und Zielabtastung in `summary.json` sind korrekt,
4. Helligkeitsausreißer in `brightness_statistics.csv` sind bekannt,
5. Ringradius, Pitch und DOE-Rotationen in `DOE_ring_layout.csv` passen zum mechanischen Design,
6. die 16-Bit-Phasendaten werden anschließend mit der passenden Material-/GrayScribe-Kalibrierung in die Fertigung überführt.

## Weiterführende Dokumentation

- [`README.md`](README.md) – Überblick über den GS-Filmgenerator
- [`BATCH_MODE.md`](BATCH_MODE.md) – technische Batch-Funktion
- [`PHYSICAL_PROJECTION.md`](PHYSICAL_PROJECTION.md) – skalierte Fresnel-Propagation
- [`BRIGHTNESS.md`](BRIGHTNESS.md) – Helligkeitsanalyse und Ausgleich
- [`RING_LAYOUT.md`](RING_LAYOUT.md) – Scheibenlayout
