<div align="center">
  <img src="docs/media/brand/nighty-banner.png" width="750" alt="Nighty Android Banner" />
  <h1>Nighty Alpha</h1>
  <p><strong>Ultra-Fast Native Ahead-of-Time Rust Client for Minecraft Java Edition 26.3</strong></p>
  <p><em>Nighty Alpha · purple liquid glass · Direct Vulkan Pipeline · Zero JVM Overhead · Sub-1.5s Cold Boots · WebAssembly Mods</em></p>
  <br>
  <p>
    <a href="https://github.com/redglitchx-xd/nighty/releases">Download APK</a> ·
    <a href="docs/">Documentation</a> ·
    <a href="docs/security.md">Security &amp; privacy</a>
  </p>
</div>

---

### Unofficial Project & Collaboration Notice

Nighty Alpha is an unofficial ARM64 launcher; upstream engine attribution is preserved in `LICENSE` and `THIRD_PARTY_NOTICES.md`. Nighty Alpha is not affiliated with, endorsed by, or connected to Mojang Studios, Microsoft Corporation, Starling or Zalith, or any of their subsidiaries. Minecraft is a registered trademark of Mojang Synergies AB. Starling and Zalith are mentioned only as UI inspiration; no code is copied from them.

- **Android Port:** Maintained and optimized for ARM64 mobile hardware by [RedGlitchX (@tubers9999)](https://github.com/tubers9999).
- *Apex Android is developed independently for mobile devices.*
- *No Mojang game files are bundled; settings stay local, and in-app downloads come only from sources you choose. See [security and privacy](docs/security.md).*

---

## Nighty UI: deeper purple, liquid glass

The Nighty Alpha build (`vNighty-Alpha`, `versionName Nighty Alpha`) continues the Nighty rebuild: deeper purple tones, frosted translucent panels with subtle wave and sheen bands, the `docs/media/brand/nighty.png` mark, and theme choices saved on the device. The launcher and Nighty overlays use this look; the game's vanilla screens stay unchanged where parity matters. The design direction is documented in [docs/design-system.md](docs/design-system.md), and the Android packaging details in [docs/android-publication.md](docs/android-publication.md).

---

## Core Characteristics

| Dimension | Nighty Android | Traditional JVM Wrapper |
| :--- | :--- | :--- |
| **Execution Architecture** | Native Rust (Ahead-of-Time) | OpenJDK HotSpot JVM |
| **RAM Footprint** | **~140–220 MB** | 1,200–2,500 MB |
| **Cold Startup Duration** | **&lt; 1.5 seconds** | 15–35 seconds |
| **Graphics Pipeline** | **Vulkan 1.1 (Naga WGSL)** | OpenGL via GL4ES |
| **Modding Sandbox** | **WebAssembly (`.hmod` via Wasmtime)** | Bytecode injection (Forge/Fabric unsupported) |
| **Garbage Collection** | **Deterministic RAII (0ms GC pause)** | Stop-the-world JVM GC cycles |
| **Touch Controls** | **Pojav & Bedrock + Polygon Outlines** | Virtual Java keyboard |

### Native Rust Ahead-of-Time Engine
Chunk meshing and terrain streaming run on native threads without intermediate Java object allocation, eliminating Garbage Collection spikes during chunk generation.

### Direct Vulkan 1.1 Pipeline
Custom WGSL shaders compiled with Naga communicate directly with Qualcomm Adreno and ARM Mali GPU drivers, bypassing OpenGL translation layers.

### WebAssembly Sandboxed Modding (.hmod)
Mod extensions compile to WebAssembly (`.hmod`) and run in a deterministic, memory-safe Wasmtime sandbox with strict capability boundaries.

### Zero-Latency PvP Feedback & Overlays
- **Visual PvP Hitmarker:** Accent-coloured hit feedback synchronized with landed hits, following the active Nighty theme.
- **Keystrokes & CPS Visualizer:** Live WASD and Space overlay with a 1,000ms sliding-window frequency tracker for Left and Right click speeds.
- **Hardware Performance Optimization:** 1-tap entity and cave occlusion culling tuned for mobile chipsets.

---

## Gameplay & Mobile Screenshots

Authentic captures from the native Android port across touch navigation, world generation, and multiplayer:

| Joystick Navigation & Crosshair Targeting | D-Pad Controls & Gesture Touch Aiming |
| :---: | :---: |
| ![Joystick Controls](docs/media/android/joystick-fox.png) | ![D-pad Controls](docs/media/android/dpad-river.png) |

| Multiplayer Network Play (Hypixel Arcade) | Native Chunk Meshing & World Generation |
| :---: | :---: |
| ![Hypixel Arcade](docs/media/android/hypixel-arcade.png) | ![Snowy Landscape](docs/media/android/snow-landscape.png) |

| Vulkan Atmospheric Lighting & Desert Terrain | Third-Person Perspective & Dynamic FOV |
| :---: | :---: |
| ![Desert Panorama](docs/media/android/desert-panorama.png) | ![Third Person](docs/media/android/third-person-desert.png) |

---

## Supported Version Matrix

Nighty targets an exact engine specification verified against upstream test suites.

| Target | Architecture | Supported | Status |
| :--- | :--- | :--- | :--- |
| **Minecraft Java 26.3** | ARM64-v8a | Yes | Verified cryptographically against `research-lock.json` |
| **Minecraft Java 26.2** | Any | No | Unsupported |
| **Minecraft Java 1.20.x** | Any | No | Unsupported |
| **Forge / Fabric / NeoForge** | Any | No | Bytecode mods unsupported; use native `.hmod` |

---

## Legitimate Setup & Preparation

Apex does not download or redistribute copyrighted Mojang assets. To build or run Apex, you must provide your own legally purchased copy of Minecraft Java Edition 26.3.

1. **Verify Ownership**  
   Ensure you have an active Microsoft account with a legally purchased copy of Minecraft Java Edition 26.3.

2. **Prepare Inputs**  
   Run the prepare tool to extract official client assets and verify their SHA-1 signatures against `research-lock.json`:
   ```bash
   python3 tools/android_prepare.py --java-home "$JAVA_HOME"
   ```

3. **Install ARM64 Package**  
   Install the release package onto your ARM64 Android device:
   ```bash
   adb install -r dist/nighty-arm64.apk
   ```

---

<details>
<summary><strong>Versiunea în limba română (Romanian version)</strong></summary>

<br>

<div align="center">
  <img src="docs/media/brand/nighty.png" width="96" height="96" alt="Nighty Android Logo" />
  <h1>Nighty Alpha</h1>
  <p><strong>Client nativ Ahead-of-Time în Rust pentru Minecraft Java Edition 26.3</strong></p>
  <p><em>Nighty Alpha · Pipeline Vulkan direct · Fără overhead JVM · Pornire în sub 1.5 secunde · Moduri WebAssembly</em></p>
</div>

### Notă privind caracterul neoficial și colaborarea

Nighty Alpha este un launcher neoficial ARM64; atribuirea motorului upstream este păstrată în `LICENSE` și `THIRD_PARTY_NOTICES.md`. Nighty Alpha nu este afiliat, aprobat sau asociat cu Mojang Studios, Microsoft Corporation, Starling sau Zalith, sau cu oricare dintre filialele acestora. Minecraft este o marcă înregistrată a Mojang Synergies AB. Starling și Zalith sunt menționate doar ca inspirație vizuală; nu a fost copiat cod din ele.

- **Portarea Android:** Menținută și optimizată pentru dispozitive mobile ARM64 de [RedGlitchX (@tubers9999)](https://github.com/tubers9999).
- Apex Android este dezvoltat independent pentru dispozitive mobile.
- Interfața Nighty: violet mai adânc, panouri translucide cu valuri și reflexii subtile, sigla nouă, iar setările temei se salvează local. Detalii: [securitate și confidențialitate](security.md).

### Caracteristici de bază

- **Execuție nativă în Rust:** Fără dependențe de mașina virtuală Java, eliminând ciclurile de pauză Garbage Collector.
- **Consum redus de memorie:** Rulează stabil într-o amprentă de ~140–220 MB RAM.
- **Randare prin Vulkan 1.1:** Pipeline direct WGSL/Naga optimizat pentru GPU-urile mobile Qualcomm Adreno și ARM Mali.
- **Moduri sigure în WebAssembly (`.hmod`):** Extensii izolate într-un sandbox Wasmtime cu memorie deterministă. Modurile clasice Forge/Fabric nu sunt suportate.
- **Feedback PvP & Keystrokes:** Hitmarker vizual colorat cu accentul temei la loviturile PvP, afișaj Keystrokes WASD și contor CPS.
- **Comenzi tactile avansate:** Presets Pojav și Bedrock, butoane poligonale configurabile și mouse virtual.

### Compatibilitate

Doar **Minecraft Java Edition 26.3** este suportat și implementat conform specificațiilor din `research-lock.json`. Versiunile mai vechi și modurile Java nu sunt compatibile.

### Pregătire și cerință de deținere legală

Apex nu redistribuie resurse originale Mojang. Pentru a compila și rula clientul, este necesară propria copie licențiată de Minecraft Java Edition 26.3, verificată cu scriptul `tools/android_prepare.py`.

</details>

---

Copyright (c) 2026 RedGlitchX. All rights reserved.
Licensed under the MIT License. See [LICENSE](LICENSE).
