/**
 * @file fn_demo.js
 * @description Example usage of the dynamic color library functions.
 *              Imports functionality from the sibling 'dream.js' file.
 */
import {
    mathUtils,
    hexUtils,
    Hct,
    Contrast,
    TonalPalette,
    CorePalette,
    QuantizerCelebi,
    MaterialDynamicColors,
    Blend,
    themeFromSourceColor,
    themeFromColors,
    dynamicSchemesFromSourceColor,
    extractColorsFromImage,
    applyTheme,
} from './dream.js';

// --- Demo Functions ---

function demoBasicTheme() {
    console.log('\n🎨 DEMO 1: Basic Theme Generation (using CorePalette directly)');

    const sourceColorHex = '#0B57D0'; // Google Blue
    const sourceColor = hexUtils.argbFromHex(sourceColorHex);
    console.log(`Source color: ${sourceColorHex} (ARGB: ${sourceColor.toString(16)})`);

    // Create palette directly
    const palette = CorePalette.of(sourceColor);

    // Access tones directly from the palette for light mode examples
    console.log('\nLight Mode Tones (Direct Palette Access):');
    console.log(`Primary (T40): ${hexUtils.hexFromArgb(palette.a1.tone(40))}`);
    console.log(`On Primary (T100): ${hexUtils.hexFromArgb(palette.a1.tone(100))}`);
    console.log(`Primary Container (T90): ${hexUtils.hexFromArgb(palette.a1.tone(90))}`);
    console.log(`Surface (Neutral T98): ${hexUtils.hexFromArgb(palette.n1.tone(98))}`);
    console.log(`Secondary (T40): ${hexUtils.hexFromArgb(palette.a2.tone(40))}`);
    console.log(`Tertiary (T40): ${hexUtils.hexFromArgb(palette.a3.tone(40))}`);

    // Access tones directly for dark mode examples
    console.log('\nDark Mode Tones (Direct Palette Access):');
    console.log(`Primary (T80): ${hexUtils.hexFromArgb(palette.a1.tone(80))}`);
    console.log(`On Primary (T20): ${hexUtils.hexFromArgb(palette.a1.tone(20))}`);
    console.log(`Primary Container (T30): ${hexUtils.hexFromArgb(palette.a1.tone(30))}`);
    console.log(`Surface (Neutral T6): ${hexUtils.hexFromArgb(palette.n1.tone(6))}`);
    console.log(`Secondary (T80): ${hexUtils.hexFromArgb(palette.a2.tone(80))}`);
    console.log(`Tertiary (T80): ${hexUtils.hexFromArgb(palette.a3.tone(80))}`);
}

function demoMaterialThemeRoles() {
    console.log('\n🎨 DEMO 2: Material Theme Generation (using Roles)');

    const sourceColorHex = '#6750A4'; // Material Default Purple
    const sourceColor = hexUtils.argbFromHex(sourceColorHex);
    console.log(`Source color: ${sourceColorHex} (ARGB: ${sourceColor.toString(16)})`);

    // Generate the full theme structure
    const theme = themeFromSourceColor(sourceColor);

    // Access colors via MaterialDynamicColors roles and the appropriate scheme
    console.log('\nLight Mode Colors (Using Roles):');
    console.log(`Primary: ${hexUtils.hexFromArgb(MaterialDynamicColors.primary.getArgb(theme.schemes.light))}`);
    console.log(`On Primary: ${hexUtils.hexFromArgb(MaterialDynamicColors.onPrimary.getArgb(theme.schemes.light))}`);
    console.log(`Primary Container: ${hexUtils.hexFromArgb(MaterialDynamicColors.primaryContainer.getArgb(theme.schemes.light))}`);
    console.log(`On Primary Container: ${hexUtils.hexFromArgb(MaterialDynamicColors.onPrimaryContainer.getArgb(theme.schemes.light))}`);
    console.log(`Surface: ${hexUtils.hexFromArgb(MaterialDynamicColors.surface.getArgb(theme.schemes.light))}`);
    console.log(`On Surface: ${hexUtils.hexFromArgb(MaterialDynamicColors.onSurface.getArgb(theme.schemes.light))}`);
    console.log(`Outline: ${hexUtils.hexFromArgb(MaterialDynamicColors.outline.getArgb(theme.schemes.light))}`);

    console.log('\nDark Mode Colors (Using Roles):');
    console.log(`Primary: ${hexUtils.hexFromArgb(MaterialDynamicColors.primary.getArgb(theme.schemes.dark))}`);
    console.log(`On Primary: ${hexUtils.hexFromArgb(MaterialDynamicColors.onPrimary.getArgb(theme.schemes.dark))}`);
    console.log(`Primary Container: ${hexUtils.hexFromArgb(MaterialDynamicColors.primaryContainer.getArgb(theme.schemes.dark))}`);
    console.log(`On Primary Container: ${hexUtils.hexFromArgb(MaterialDynamicColors.onPrimaryContainer.getArgb(theme.schemes.dark))}`);
    console.log(`Surface: ${hexUtils.hexFromArgb(MaterialDynamicColors.surface.getArgb(theme.schemes.dark))}`);
    console.log(`On Surface: ${hexUtils.hexFromArgb(MaterialDynamicColors.onSurface.getArgb(theme.schemes.dark))}`);
    console.log(`Outline: ${hexUtils.hexFromArgb(MaterialDynamicColors.outline.getArgb(theme.schemes.dark))}`);
}

function demoMultiSeedTheme() {
    console.log('\n🎨 DEMO 2b: Multi-Seed Theme Generation');

    const seeds = {
        primary: hexUtils.argbFromHex('#006971'),   // Teal
        secondary: hexUtils.argbFromHex('#FF8F00'), // Amber
        tertiary: hexUtils.argbFromHex('#C51162')    // Pink
    };
    console.log(`Seed Colors: Primary=${hexUtils.hexFromArgb(seeds.primary)}, Secondary=${hexUtils.hexFromArgb(seeds.secondary)}, Tertiary=${hexUtils.hexFromArgb(seeds.tertiary)}`);

    // Generate the theme from multiple seeds
    const theme = themeFromColors(seeds);

    // Access colors (they should reflect the individual seed influences)
    console.log('\nLight Mode Colors (Multi-Seed):');
    console.log(`Primary Palette T40: ${hexUtils.hexFromArgb(theme.palettes.primary.tone(40))}`);
    console.log(`Secondary Palette T40: ${hexUtils.hexFromArgb(theme.palettes.secondary.tone(40))}`);
    console.log(`Tertiary Palette T40: ${hexUtils.hexFromArgb(theme.palettes.tertiary.tone(40))}`);
    console.log(`Neutral Palette T40 (from Primary): ${hexUtils.hexFromArgb(theme.palettes.neutral.tone(40))}`);
    console.log(`Primary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.primary.getArgb(theme.schemes.light))}`); // Role still uses T40/T80 etc.
    console.log(`Secondary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.secondary.getArgb(theme.schemes.light))}`);
    console.log(`Tertiary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.tertiary.getArgb(theme.schemes.light))}`);

    console.log('\nDark Mode Colors (Multi-Seed):');
    console.log(`Primary Palette T80: ${hexUtils.hexFromArgb(theme.palettes.primary.tone(80))}`);
    console.log(`Secondary Palette T80: ${hexUtils.hexFromArgb(theme.palettes.secondary.tone(80))}`);
    console.log(`Tertiary Palette T80: ${hexUtils.hexFromArgb(theme.palettes.tertiary.tone(80))}`);
    console.log(`Primary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.primary.getArgb(theme.schemes.dark))}`);
    console.log(`Secondary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.secondary.getArgb(theme.schemes.dark))}`);
    console.log(`Tertiary Role: ${hexUtils.hexFromArgb(MaterialDynamicColors.tertiary.getArgb(theme.schemes.dark))}`);
}


function demoContrastLevels() {
    console.log('\n🔆 DEMO 3: Dynamic Schemes with Contrast Levels');

    const sourceColor = hexUtils.argbFromHex('#006971'); // Teal-ish color
    console.log(`Source color: ${hexUtils.hexFromArgb(sourceColor)}`);

    const contrastLevels = [-0.5, 0.0, 0.5]; // Low, Default, High

    for (const contrast of contrastLevels) {
        console.log(`\n--- Contrast Level: ${contrast.toFixed(1)} ---`);

        // Generate schemes specifically for this contrast level
        const { light: lightScheme, dark: darkScheme } = dynamicSchemesFromSourceColor(sourceColor, contrast);

        // Example: Check contrast between OnSurface and Surface
        const lightOnSurfaceTone = MaterialDynamicColors.onSurface.getTone(lightScheme);
        const lightSurfaceTone = MaterialDynamicColors.surface.getTone(lightScheme);
        const lightTextBgContrast = Contrast.ratioOfTones(lightOnSurfaceTone, lightSurfaceTone);

        const darkOnSurfaceTone = MaterialDynamicColors.onSurface.getTone(darkScheme);
        const darkSurfaceTone = MaterialDynamicColors.surface.getTone(darkScheme);
        const darkTextBgContrast = Contrast.ratioOfTones(darkOnSurfaceTone, darkSurfaceTone);

        console.log(`Light mode:`);
        console.log(`  Surface (T${lightSurfaceTone.toFixed(0)}): ${hexUtils.hexFromArgb(MaterialDynamicColors.surface.getArgb(lightScheme))}`);
        console.log(`  OnSurface (T${lightOnSurfaceTone.toFixed(0)}): ${hexUtils.hexFromArgb(MaterialDynamicColors.onSurface.getArgb(lightScheme))}`);
        console.log(`  Contrast Ratio: ${lightTextBgContrast.toFixed(2)}`);

        console.log(`Dark mode:`);
        console.log(`  Surface (T${darkSurfaceTone.toFixed(0)}): ${hexUtils.hexFromArgb(MaterialDynamicColors.surface.getArgb(darkScheme))}`);
        console.log(`  OnSurface (T${darkOnSurfaceTone.toFixed(0)}): ${hexUtils.hexFromArgb(MaterialDynamicColors.onSurface.getArgb(darkScheme))}`);
        console.log(`  Contrast Ratio: ${darkTextBgContrast.toFixed(2)}`);
    }
}

function demoHctColorSpace() {
    console.log('\n🌈 DEMO 4: HCT Color Space Manipulation');

    const initialHex = '#4CAF50'; // Green
    const initialArgb = hexUtils.argbFromHex(initialHex);
    const hct = Hct.fromInt(initialArgb);
    console.log(`Initial Color: ${initialHex} => HCT(${hct.hue.toFixed(1)}, ${hct.chroma.toFixed(1)}, ${hct.tone.toFixed(1)})`);

    console.log('\nTransforming color in HCT space:');

    // Create a mutable copy
    const hctCopy = Hct.fromInt(hct.toInt());

    // Rotate Hue
    hctCopy.hue = mathUtils.sanitizeDegreesDouble(hctCopy.hue + 120); // Towards blue
    console.log(`-> Rotated Hue +120°: ${hexUtils.hexFromArgb(hctCopy.toInt())} (HCT: ${hctCopy.hue.toFixed(1)}, ${hctCopy.chroma.toFixed(1)}, ${hctCopy.tone.toFixed(1)})`);

    // Increase Chroma (might be limited by gamut)
    hctCopy.chroma = hctCopy.chroma + 30;
    console.log(`-> Increased Chroma +30: ${hexUtils.hexFromArgb(hctCopy.toInt())} (HCT: ${hctCopy.hue.toFixed(1)}, ${hctCopy.chroma.toFixed(1)}, ${hctCopy.tone.toFixed(1)})`);

    // Set Tone
    hctCopy.tone = 85; // Make it lighter
    console.log(`-> Set Tone to 85: ${hexUtils.hexFromArgb(hctCopy.toInt())} (HCT: ${hctCopy.hue.toFixed(1)}, ${hctCopy.chroma.toFixed(1)}, ${hctCopy.tone.toFixed(1)})`);
}

function demoTonalPalettes() {
    console.log('\n🎭 DEMO 5: Tonal Palettes');

    const sourceColor = hexUtils.argbFromHex('#E91E63'); // Pink
    const hct = Hct.fromInt(sourceColor);
    console.log(`Source HCT: H${hct.hue.toFixed(1)}, C${hct.chroma.toFixed(1)}, T${hct.tone.toFixed(1)}`)

    const palette = TonalPalette.fromHct(hct);
    // Or: const palette = TonalPalette.fromHueAndChroma(hct.hue, hct.chroma);

    const tones = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100];

    console.log(`\nTonal Palette colors for Hue ${palette.hue.toFixed(1)}, Chroma ${palette.chroma.toFixed(1)}:`);
    for (const tone of tones) {
        console.log(`  Tone ${String(tone).padStart(3)}: ${hexUtils.hexFromArgb(palette.tone(tone))}`);
    }
}

function demoBlending() {
    console.log('\n🔄 DEMO 6: Color Blending (Harmonization)');

    const designColor = hexUtils.argbFromHex('#FFEB3B'); // Yellow - potentially clashing
    const themeSourceColor = hexUtils.argbFromHex('#3F51B5'); // Indigo - theme color

    console.log(`Design Color: ${hexUtils.hexFromArgb(designColor)}`);
    console.log(`Theme Source: ${hexUtils.hexFromArgb(themeSourceColor)}`);

    const blendAmounts = [0.0, 0.25, 0.5, 0.75, 1.0]; // 0% to 100% towards source

    console.log('\nHarmonizing design color towards theme source:');
    for (const amount of blendAmounts) {
        const blended = Blend.harmonize(designColor, themeSourceColor, amount);
        console.log(`  Blend ${Math.round(amount * 100)}%: ${hexUtils.hexFromArgb(blended)}`);
    }
}

function demoContrastUtils() {
    console.log('\n♿ DEMO 7: Contrast Utilities');

    const backgroundTone = 10; // Dark background
    const midTone = 50;
    const foregroundTone = 95; // Light foreground

    const contrastDarkMid = Contrast.ratioOfTones(backgroundTone, midTone);
    const contrastDarkLight = Contrast.ratioOfTones(backgroundTone, foregroundTone);
    const contrastMidLight = Contrast.ratioOfTones(midTone, foregroundTone);

    console.log(`Contrast between T${backgroundTone} and T${midTone}: ${contrastDarkMid.toFixed(2)}`);
    console.log(`Contrast between T${backgroundTone} and T${foregroundTone}: ${contrastDarkLight.toFixed(2)}`);
    console.log(`Contrast between T${midTone} and T${foregroundTone}: ${contrastMidLight.toFixed(2)}`);

    const targetContrast = 4.5; // WCAG AA for normal text
    console.log(`\nFinding tones for target contrast ${targetContrast} against T${backgroundTone}:`);

    const lighterTarget = Contrast.lighter(backgroundTone, targetContrast);
    if (lighterTarget !== -1.0) {
        console.log(`  Lightest tone >= ${targetContrast}: T${lighterTarget.toFixed(1)} (Actual: ${Contrast.ratioOfTones(backgroundTone, lighterTarget).toFixed(2)})`);
    } else {
        console.log(`  No lighter tone achieves ${targetContrast}.`);
    }

    // Finding darker target (not possible against T10)
    const darkerTarget = Contrast.darker(backgroundTone, targetContrast);
    if (darkerTarget !== -1.0) {
        console.log(`  Darkest tone >= ${targetContrast}: T${darkerTarget.toFixed(1)} (Actual: ${Contrast.ratioOfTones(backgroundTone, darkerTarget).toFixed(2)})`);
    } else {
        console.log(`  No darker tone achieves ${targetContrast}.`);
    }

    // Example using unsafe variants
    const unsafeLight = Contrast.lighterUnsafe(backgroundTone, targetContrast);
    console.log(`  Lighter Unsafe T: ${unsafeLight.toFixed(1)} (Actual: ${Contrast.ratioOfTones(backgroundTone, unsafeLight).toFixed(2)})`);

}

function demoColorExtraction() {
    console.log('\n🖼️ DEMO 8: Color Extraction (Wu + WSMeans)');

    // Create a mock ImageData (e.g., 4x4 pixels with distinct colors)
    // Need ImageData constructor if in browser, otherwise mock object
    let mockImageData;
    const width = 4;
    const height = 4;
    const pixelData = new Uint8ClampedArray([
        // Row 1: Red, Red, Green, Green
        255, 0, 0, 255, 200, 0, 0, 255, 0, 255, 0, 255, 0, 200, 0, 255,
        // Row 2: Red, Red, Green, Green
        255, 0, 0, 255, 180, 0, 0, 255, 0, 255, 0, 255, 0, 180, 0, 255,
        // Row 3: Blue, Blue, Yellow, Yellow
        0, 0, 255, 255, 0, 0, 200, 255, 255, 255, 0, 255, 200, 200, 0, 255,
        // Row 4: Blue, Blue, Yellow, Yellow (with one transparent)
        0, 0, 255, 255, 0, 0, 180, 0, 255, 255, 0, 255, 180, 180, 0, 255,
    ]);

    if (typeof ImageData !== 'undefined') {
        try {
            mockImageData = new ImageData(pixelData, width, height);
        } catch (e) { // Handle potential browser security restrictions or different constructors
            console.warn("Could not create ImageData directly, using mock object.");
            mockImageData = { data: pixelData, width: width, height: height };
        }
    } else {
        mockImageData = { data: pixelData, width: width, height: height };
    }


    // Use async/await for extractColorsFromImage
    async function runExtraction() {
        console.log(`Quantizing mock image data...`);
        try {
            // Extract pixels into ARGB array before passing to quantizer if needed
            // (though current extractColorsFromImage handles ImageData directly)
            const prominentColors = await extractColorsFromImage(mockImageData, { desired: 5 });

            console.log('\nQuantized & Scored Colors:');
            if (prominentColors.length > 0) {
                // Need color counts for population - QuantizerCelebi returns this map
                // Let's modify to show this info
                const pixels = [];
                for (let i = 0; i < mockImageData.data.length; i += 4) {
                    if (mockImageData.data[i + 3] === 255) {
                        pixels.push(
                            (255 << 24) | (mockImageData.data[i] << 16) | (mockImageData.data[i + 1] << 8) | mockImageData.data[i + 2]
                        );
                    }
                }
                const colorCounts = QuantizerCelebi.quantize(pixels, 16); // Run again to get counts map

                prominentColors.forEach((color, index) => {
                    const pop = colorCounts.get(color);
                    console.log(`  ${index + 1}: ${hexUtils.hexFromArgb(color)} (Population: ${pop !== undefined ? pop : 'N/A'})`);
                });
            } else {
                console.log('  No prominent colors found after scoring.');
            }
        } catch (error) {
            console.error("Error during color extraction demo:", error);
        }
    }
    runExtraction(); // Call the async function

}

function demoThemeApplication() {
    console.log('\n💻 DEMO 9: Applying Theme to DOM (Simulated)');

    // Check if running in a browser environment with DOM access
    if (typeof document === 'undefined' || !document.body) {
        console.log('  (Skipping DOM application demo - not in browser environment)');
        return;
    }

    const sourceColor = hexUtils.argbFromHex('#FF9800'); // Orange
    const custom = [{ name: 'my-brand-color', value: 0xFF00BCD4, blend: true }]; // Cyan, blended
    const theme = themeFromSourceColor(sourceColor, custom);

    // --- Apply Light Theme ---
    console.log('\nApplying Light Theme to document.body...');
    applyTheme(theme, { dark: false, target: document.body, brightnessSuffix: false, paletteTones: true }); // Export palette tones too
    // Check a few applied styles (example)
    console.log(`  --md-sys-color-primary: ${document.body.style.getPropertyValue('--md-sys-color-primary')}`);
    console.log(`  --md-custom-color-my-brand-color: ${document.body.style.getPropertyValue('--md-custom-color-my-brand-color')}`);
    console.log(`  --md-ref-palette-primary-tone50: ${document.body.style.getPropertyValue('--md-ref-palette-primary-tone50')}`);


    // --- Apply Dark Theme with Suffix ---
    // Create a dummy element for demonstration
    let dummyElement = document.getElementById('hctjs-dummy-element');
    if (!dummyElement) {
        dummyElement = document.createElement('div');
        dummyElement.id = 'hctjs-dummy-element';
        dummyElement.style.display = 'none'; // Hide it
        document.body.appendChild(dummyElement);
    }
    console.log('\nApplying Dark Theme to dummy element with brightness suffix...');
    applyTheme(theme, { dark: true, target: dummyElement, brightnessSuffix: true });
    console.log(`  --md-sys-color-secondary-dark: ${dummyElement.style.getPropertyValue('--md-sys-color-secondary-dark')}`);
    console.log(`  --md-custom-color-my-brand-color-dark: ${dummyElement.style.getPropertyValue('--md-custom-color-my-brand-color-dark')}`);

    console.log('\n(Inspect document.body and the hidden div#hctjs-dummy-element for applied CSS variables)');
}


function runAllDemos() {
    console.log('===== MATERIAL DYNAMIC COLOR SYSTEM DEMO =====');
    demoBasicTheme();
    demoMaterialThemeRoles();
    demoMultiSeedTheme(); // Added multi-seed demo
    demoContrastLevels();
    demoHctColorSpace();
    demoTonalPalettes();
    demoBlending();
    demoContrastUtils();
    demoColorExtraction(); // Note: This demo is now async
    demoThemeApplication(); // Will skip if not in browser
    // console.log('\n===== DEMO COMPLETE ====='); // Moved inside async check
}

// Automatically run demos when script loads, check for browser environment
// Need to handle the async nature of demoColorExtraction
async function main() {
    if (typeof window !== 'undefined') {
        console.log("Running demos in browser environment...");
        await runAllDemos(); // Await if demos become async
        console.log('\n===== BROWSER DEMO COMPLETE =====');
    } else {
        console.log("Running demos in non-browser environment (DOM application demo will be skipped).");
        await runAllDemos();
        console.log('\n===== NODE DEMO COMPLETE =====');
    }
}

main().catch(console.error);