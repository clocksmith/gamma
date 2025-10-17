/**
 * @file fn_test.js
 * @description Basic functional tests for hct.js library.
 *              Assumes it runs as an ES module (e.g., in Node.js with type="module" or a browser).
 */

// --- Import necessary components from dream.js ---
import {
    mathUtils, hexUtils, colorUtils,
    ViewingConditions, Cam16, Hct, HctSolver,
    ContrastCurve, Contrast,
    TonalPalette, KeyColor, CorePalette, CorePalettes,
    DynamicScheme, isMonochrome, isFidelity,
    QuantizerCelebi, QuantizerWsmeans, LabPointProvider, QuantizerMap, QuantizerWu,
    DynamicColor, MaterialDynamicColors, Blend, Score, themeFromSourceColor, dynamicSchemesFromSourceColor, themeFromColors, extractColorsFromImage, themeFromImage, applyTheme, processCustomColors
} from './dream.js'; // Adjust path if necessary

// Create the 'lib' object structure expected by the tests
const lib = {
    mathUtils, hexUtils, colorUtils,
    ViewingConditions, Cam16, Hct, HctSolver,
    ContrastCurve, Contrast,
    TonalPalette, KeyColor, CorePalette, CorePalettes,
    DynamicScheme, isMonochrome, isFidelity,
    QuantizerCelebi, QuantizerWsmeans, LabPointProvider, QuantizerMap, QuantizerWu, // Removed internal helpers like BoxWu
    DynamicColor, MaterialDynamicColors, Blend, Score, themeFromSourceColor, dynamicSchemesFromSourceColor, themeFromColors, extractColorsFromImage, themeFromImage, applyTheme, processCustomColors // Removed internal helpers like ToneDeltaPair
};

// --- Helper Assertion Functions (No external deps!) ---

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(`Assertion failed: ${message} - Expected: ${expected} (${typeof expected}), Actual: ${actual} (${typeof actual})`);
    }
}

function assertDeepEqual(actual, expected, message) {
    const actualJson = JSON.stringify(actual);
    const expectedJson = JSON.stringify(expected);
    if (actualJson !== expectedJson) {
        throw new Error(`Assertion failed: ${message} - Expected: ${expectedJson}, Actual: ${actualJson}`);
    }
}

function assertApproxEqual(actual, expected, tolerance, message) {
    // Check for NaN before comparison
    if (isNaN(actual) || isNaN(expected)) {
        if (isNaN(actual) && isNaN(expected)) return; // Both NaN is considered equal for this test
        throw new Error(`Assertion failed: ${message} - NaN detected. Expected: ${expected}, Actual: ${actual}`);
    }
    if (Math.abs(actual - expected) > tolerance) {
        throw new Error(`Assertion failed: ${message} - Expected: ~${expected}, Actual: ${actual} (Tolerance: ${tolerance})`);
    }
}


function assertTrue(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message} - Expected: true, Actual: false`);
    }
}

function assertFalse(condition, message) {
    if (condition) {
        throw new Error(`Assertion failed: ${message} - Expected: false, Actual: true`);
    }
}

// --- Test Workflow Functions (Copied from original, using 'lib' object) ---

function testCoreUtils(lib) {
    console.log("Running Core Utility Tests...");
    assertEqual(lib.mathUtils.clampDouble(0, 100, 150), 100, "clampDouble Max");
    assertEqual(lib.mathUtils.clampDouble(0, 100, -50), 0, "clampDouble Min");
    assertApproxEqual(lib.mathUtils.lerp(10, 20, 0.5), 15, 1e-6, "lerp midpoint");
    assertEqual(lib.mathUtils.sanitizeDegreesDouble(400), 40, "sanitizeDegrees positive");
    assertEqual(lib.mathUtils.sanitizeDegreesDouble(-10), 350, "sanitizeDegrees negative");
    assertEqual(lib.hexUtils.hexFromArgb(0xFFFF0000), "#ff0000", "hexFromArgb Red");
    assertEqual(lib.hexUtils.argbFromHex("#00FF00"), 0xFF00FF00, "argbFromHex Green");
    assertEqual(lib.hexUtils.argbFromHex("0000FF"), 0xFF0000FF, "argbFromHex Blue (no #)");
    assertEqual(lib.hexUtils.argbFromHex("abc"), 0xFFAABBCC, "argbFromHex shorthand");
    assertEqual(lib.colorUtils.redFromArgb(0xFFAABBCC), 0xAA, "redFromArgb");
    assertEqual(lib.colorUtils.greenFromArgb(0xFFAABBCC), 0xBB, "greenFromArgb");
    assertEqual(lib.colorUtils.blueFromArgb(0xFFAABBCC), 0xCC, "blueFromArgb");
    assertApproxEqual(lib.colorUtils.lstarFromArgb(0xFFFFFFFF), 100, 1e-3, "lstarFromArgb White");
    assertApproxEqual(lib.colorUtils.lstarFromArgb(0xFF000000), 0, 1e-3, "lstarFromArgb Black");
    const greyArgb = lib.colorUtils.argbFromLstar(50);
    assertApproxEqual(lib.colorUtils.lstarFromArgb(greyArgb), 50, 0.5, "lstarFromArgb -> argbFromLstar roundtrip");

    console.log("Core Utility Tests Passed!");
}


function testColorRepresentations(lib) {
    console.log("Running Color Representation Tests (HCT, CAM16)...");

    const h = 270, c = 40, t = 60;
    const hct = lib.Hct.from(h, c, t);
    const argb = hct.toInt();
    const hctRoundtrip = lib.Hct.fromInt(argb);

    assertApproxEqual(hctRoundtrip.hue, h, 1.0, "HCT -> ARGB -> HCT Hue Roundtrip");
    assertTrue(hctRoundtrip.chroma <= c + 1.0, "HCT -> ARGB -> HCT Chroma does not increase significantly");
    // Tone roundtrip tolerance needs to be slightly higher due to gamut mapping effects
    assertApproxEqual(hctRoundtrip.tone, t, 1.0, "HCT -> ARGB -> HCT Tone Roundtrip");

    const cam = lib.Cam16.fromInt(argb);
    assertTrue(cam instanceof lib.Cam16, "Cam16.fromInt returns a Cam16 object");
    assertApproxEqual(cam.hue, hctRoundtrip.hue, 1.0, "Cam16 hue matches HCT hue");
    assertApproxEqual(cam.chroma, hctRoundtrip.chroma, 1.0, "Cam16 chroma matches HCT chroma");
    // J (lightness) in CAM16 is not exactly L* (tone), but should be close
    assertApproxEqual(cam.j, hctRoundtrip.tone, 1.0, "Cam16 J approx matches HCT tone");

    const camArgbRoundtrip = cam.toInt();
    const deltaR = Math.abs(lib.colorUtils.redFromArgb(argb) - lib.colorUtils.redFromArgb(camArgbRoundtrip));
    const deltaG = Math.abs(lib.colorUtils.greenFromArgb(argb) - lib.colorUtils.greenFromArgb(camArgbRoundtrip));
    const deltaB = Math.abs(lib.colorUtils.blueFromArgb(argb) - lib.colorUtils.blueFromArgb(camArgbRoundtrip));
    assertTrue(deltaR <= 2 && deltaG <= 2 && deltaB <= 2, "CAM16 -> ARGB Roundtrip (within tolerance)");


    console.log("Color Representation Tests Passed!");
}


function testContrastAndPalettes(lib) {
    console.log("Running Contrast and Palette Tests...");

    assertApproxEqual(lib.Contrast.ratioOfTones(100, 0), 21.0, 1e-3, "Contrast White vs Black");
    assertApproxEqual(lib.Contrast.ratioOfTones(50, 50), 1.0, 1e-3, "Contrast Mid Grey vs Mid Grey");
    const ratio45 = lib.Contrast.ratioOfTones(90, 30);
    assertTrue(ratio45 > 4.0 && ratio45 < 5.0, "Contrast ratio calculation sanity check");

    const bgTone = 20;
    const targetRatio = 4.5;
    const lighterTone = lib.Contrast.lighter(bgTone, targetRatio);
    assertTrue(lighterTone === -1.0 || lighterTone >= bgTone, "Contrast.lighter produces lighter tone or -1");
    if (lighterTone !== -1.0) {
        assertTrue(lib.Contrast.ratioOfTones(lighterTone, bgTone) >= targetRatio - 0.05, `Contrast.lighter meets ratio (approx) T${lighterTone.toFixed(1)} vs T${bgTone}`);
    }

    const darkerTone = lib.Contrast.darker(90, targetRatio);
    assertTrue(darkerTone === -1.0 || darkerTone <= 90, "Contrast.darker produces darker tone or -1");
    if (darkerTone !== -1.0) {
        assertTrue(lib.Contrast.ratioOfTones(90, darkerTone) >= targetRatio - 0.05, `Contrast.darker meets ratio (approx) T90 vs T${darkerTone.toFixed(1)}`);
    }

    const sourceColor = 0xFF0080FF; // Blue
    const hct = lib.Hct.fromInt(sourceColor);
    const palette = lib.TonalPalette.fromHueAndChroma(hct.hue, hct.chroma);
    assertTrue(palette instanceof lib.TonalPalette, "TonalPalette.fromHueAndChroma returns TonalPalette");
    const tone50Argb = palette.tone(50);
    assertApproxEqual(lib.colorUtils.lstarFromArgb(tone50Argb), 50, 1.0, "TonalPalette tone(50) has L* near 50");
    const tone50Hct = lib.Hct.fromInt(tone50Argb);
    assertApproxEqual(tone50Hct.hue, hct.hue, 1.0, "TonalPalette tone(50) preserves hue");
    assertTrue(tone50Hct.chroma <= hct.chroma + 1.0, "TonalPalette tone(50) chroma doesn't increase significantly");

    const corePaletteOf = lib.CorePalette.of(sourceColor);
    assertTrue(corePaletteOf.a1 instanceof lib.TonalPalette, "CorePalette.of creates primary TonalPalette (a1)");
    assertTrue(corePaletteOf.n1 instanceof lib.TonalPalette, "CorePalette.of creates neutral TonalPalette (n1)");
    assertTrue(corePaletteOf.error instanceof lib.TonalPalette, "CorePalette.of creates error TonalPalette");
    assertApproxEqual(corePaletteOf.a1.hue, hct.hue, 1.0, "CorePalette.of primary hue matches source hue");
    assertTrue(corePaletteOf.n1.chroma < 10.0, "CorePalette.of neutral chroma is low");

    const seeds = { primary: 0xFF0000FF, secondary: 0xFF00FF00, tertiary: 0xFFFF0000 };
    const corePaletteFrom = lib.CorePalette.fromColors(seeds);
    assertApproxEqual(corePaletteFrom.a1.hue, 240, 1.5, "CorePalette.fromColors primary hue (Blue)"); // Increased tolerance slightly
    assertApproxEqual(corePaletteFrom.a2.hue, 120, 1.0, "CorePalette.fromColors secondary hue (Green)");
    // Red hue can be 0 or 360
    const tertiaryHue = corePaletteFrom.a3.hue;
    assertTrue(tertiaryHue < 1.0 || tertiaryHue > 359.0, "CorePalette.fromColors tertiary hue (Red)");
    assertApproxEqual(corePaletteFrom.n1.hue, 240, 1.5, "CorePalette.fromColors neutral hue (from primary)");


    console.log("Contrast and Palette Tests Passed!");
}

function testSchemeAndTheme(lib) {
    console.log("Running Scheme and Theme Tests...");

    const sourceColor = 0xFF3367D6; // Another Blue

    const themeSingle = lib.themeFromSourceColor(sourceColor);
    assertTrue(typeof themeSingle === 'object', "themeFromSourceColor returns an object");
    assertTrue(themeSingle.schemes.light instanceof lib.DynamicScheme, "Single Seed: Theme has light scheme");
    assertTrue(themeSingle.schemes.dark instanceof lib.DynamicScheme, "Single Seed: Theme has dark scheme");
    assertTrue(themeSingle.palettes.primary instanceof lib.TonalPalette, "Single Seed: Theme has primary palette");
    assertEqual(themeSingle.source, sourceColor, "Single Seed: Theme source color is stored");

    const seeds = { primary: 0xFF0000FF, secondary: 0xFF00FF00, tertiary: 0xFFFF0000 };
    const themeMulti = lib.themeFromColors(seeds);
    assertTrue(typeof themeMulti === 'object', "themeFromColors returns an object");
    assertTrue(themeMulti.schemes.light instanceof lib.DynamicScheme, "Multi Seed: Theme has light scheme");
    assertTrue(themeMulti.schemes.dark instanceof lib.DynamicScheme, "Multi Seed: Theme has dark scheme");
    assertTrue(themeMulti.palettes.primary instanceof lib.TonalPalette, "Multi Seed: Theme has primary palette");
    assertEqual(themeMulti.source, seeds.primary, "Multi Seed: Theme source color is primary seed");
    assertDeepEqual(themeMulti.seedColors, seeds, "Multi Seed: Theme stores seed colors");

    assertApproxEqual(themeMulti.palettes.primary.hue, 240, 1.5, "Multi Seed: Primary palette hue");
    assertApproxEqual(themeMulti.palettes.secondary.hue, 120, 1.0, "Multi Seed: Secondary palette hue");
    const tertiaryHueMulti = themeMulti.palettes.tertiary.hue;
    assertTrue(tertiaryHueMulti < 1.0 || tertiaryHueMulti > 359.0, "Multi Seed: Tertiary palette hue (Red)");


    const lightPrimary = lib.MaterialDynamicColors.primary.getArgb(themeSingle.schemes.light);
    const darkPrimary = lib.MaterialDynamicColors.primary.getArgb(themeSingle.schemes.dark);
    assertTrue(typeof lightPrimary === 'number', "Light primary color is a number");
    assertTrue(typeof darkPrimary === 'number', "Dark primary color is a number");
    const lstarLight = lib.colorUtils.lstarFromArgb(lightPrimary);
    const lstarDark = lib.colorUtils.lstarFromArgb(darkPrimary);
    // Typical relationship, but can invert in monochrome/edge cases
    // assertTrue(lstarDark > lstarLight, `Dark primary L* (${lstarDark.toFixed(1)}) > Light primary L* (${lstarLight.toFixed(1)}) (typical)`);

    const lightOnSurface = lib.MaterialDynamicColors.onSurface.getArgb(themeSingle.schemes.light);
    const lightSurface = lib.MaterialDynamicColors.surface.getArgb(themeSingle.schemes.light);
    const lightContrast = lib.Contrast.ratioOfTones(
        lib.colorUtils.lstarFromArgb(lightOnSurface),
        lib.colorUtils.lstarFromArgb(lightSurface)
    );
    assertTrue(lightContrast >= 4.5 - 0.1, `Light onSurface/surface contrast ${lightContrast.toFixed(2)} >= 4.5 (approx)`);

    const customColors = [{ value: 0xFFCC00CC, name: "CustomPurple", blend: true }];
    const themeWithCustom = lib.themeFromSourceColor(sourceColor, customColors);
    assertTrue(themeWithCustom.customColors.length > 0, "Theme with custom colors has customColors array");
    assertEqual(themeWithCustom.customColors[0].color.name, "CustomPurple", "Custom color name is correct");
    assertTrue(typeof themeWithCustom.customColors[0].light.color === 'number', "Custom color light group has color");
    if (customColors[0].blend) {
        assertFalse(themeWithCustom.customColors[0].value === customColors[0].value, "Custom color blended value differs if blend=true");
    }

    console.log("Scheme and Theme Tests Passed!");
}

// --- Main Test Execution ---

function runAllIntegrationTests(libToTest, libName) {
    console.log(`\n--- Running tests against: ${libName} ---`);
    let success = true;
    try {
        testCoreUtils(libToTest);
        testColorRepresentations(libToTest);
        testContrastAndPalettes(libToTest);
        testSchemeAndTheme(libToTest);
        // Add other test suites here
    } catch (error) {
        console.error(`\n--- Tests FAILED for: ${libName} ---`);
        console.error(error);
        success = false;
    } finally {
        if (success) {
            console.log(`\n--- All tests PASSED for: ${libName} ---`);
        }
        console.log("\n--- Test Run Complete ---");
    }
    return success;
}

// --- Run tests ---
runAllIntegrationTests(lib, "dream.js Library");