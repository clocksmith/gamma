      const $ = (selector) => document.querySelector(selector);
      const $$ = (selector) => document.querySelectorAll(selector);
      const getEl = (id) => document.getElementById(id);
      const createEl = (tag) => document.createElement(tag);
      const toggleClass = (el, className, force) =>
        el?.classList.toggle(className, force);
      const setAttr = (el, attr, value) => el?.setAttribute(attr, value);
      const removeAttr = (el, attr) => el?.removeAttribute(attr);
      const setText = (el, text) => {
        if (el) el.textContent = text;
      };
      const setHtml = (el, html) => {
        if (el) el.innerHTML = html;
      };
      const disableEl = (el, disabled) => {
        if (el) el.disabled = disabled;
      };
      const hideEl = (el, hide = true) => toggleClass(el, "hidden", hide);

      const config = {
        API_KEY: null,
        GEMINI_MODEL: null,
        GEMINI_MODEL_COLOR_PICKER: null,
        GEMINI_MODEL_COMPONENT_GENERATOR: null,
        USE_M3_TXT_SYS_PROMPT: false,
        ENABLE_IMAGES: true,
        isApiConfigValid: false,
        geminiApiEndpointBase: "",
        geminiApiEndpointColorPicker: "",
        geminiApiEndpointComponentGenerator: "",
        defaultInputSource: "text",
        ENABLE_AUTO_MODES: true,
        MINIMAP_STEP_DELAY: 1000,
        MINIMAP_ANIMATION_DURATION: 400,
      };

      let sessionApiKey = null;
      let apiKeyPromiseResolver = null;

      const state = {
        currentImageFile: null,
        currentInputSource: config.defaultInputSource,
        lastGeneratedTheme: null,
        isDarkMode: false,
        m3ContentCache: null,
        currentMinimapSteps: [],
        minimapUpdateQueue: [],
        isMinimapUpdating: false,
        lastSuggestions: { text: null, image: null },
        selectedSuggestion: { text: null, image: null },
        generationMethod: "material",
        history: [],
        currentPhaseCardId: null,
      };

      const dom = {
        apiKeyModal: getEl("apiKeyModal"),
        apiKeyInput: getEl("apiKeyInput"),
        apiKeyError: getEl("apiKeyError"),
        saveApiKeyBtn: getEl("saveApiKeyBtn"),
        cancelApiKeyBtn: getEl("cancelApiKeyBtn"),
        inputSourceRadios: $$('input[name="inputSource"]'),
        inputSourceSelection: getEl("input-source-selection"),
        textOptionsGroup: getEl("text-options-group"),
        colorOptionsGroup: getEl("color-options-group"),
        imageOptionsGroup: getEl("image-options-group"),
        textPromptInput: getEl("text-prompt-input"),
        textSeedCountSelection: getEl("text-seed-count-selection"),
        textSelectionMethodSelection: getEl("text-selection-method-selection"),
        processTextButton: getEl("process-text-button"),
        textPromptSuggestions: getEl("text-prompt-suggestions"),
        suggestionsList: getEl("suggestions-list"),
        suggestionLoadingIndicator: getEl("suggestion-loading-indicator"),
        useSimulationCheckbox: getEl("use-gemini-simulation"),
        textSelectGeminiMCPInput: getEl("textSelectGeminiMCP"),
        textPromptSimOption: getEl("text-prompt-sim-option"),
        colorSeedCountSelection: getEl("color-seed-count-selection"),
        sourceColorArea: getEl("source-color-area"),
        sourceColorLabel: getEl("source-color-label"),
        sourceColorInputsContainer: getEl("source-color-inputs"),
        multiSourceOptionsArea: getEl("multi-source-options"),
        harmonyStrategySelect: getEl("harmonyStrategy"),
        sourceImageContainer: getEl("sourceImage-container"),
        imageInput: getEl("image-input"),
        dropArea: getEl("drop-area"),
        imagePreview: getEl("image-preview"),
        imageExtractionMethodSelection: getEl(
          "image-extraction-method-selection"
        ),
        imageSeedCountSelection: getEl("image-seed-count-selection"),
        imageMaterialOptions: getEl("image-material-options"),
        imageGeminiOptions: getEl("image-gemini-options"),
        imageSelectGeminiMCPContainer: getEl("imageSelectGeminiMCP-container"),
        imagePromptSuggestions: getEl("image-prompt-suggestions"),
        imageSuggestionsList: getEl("image-suggestions-list"),
        imageSuggestionLoadingIndicator: getEl(
          "image-suggestion-loading-indicator"
        ),
        processImageGeminiButton: getEl("process-image-gemini-button"),
        imageExtractGeminiContainer: getEl("imageExtractGemini-container"),
        numSourcesInput: getEl("numSources"),
        extractQualityInput: getEl("extractQuality"),
        generateButton: getEl("generate-button"),
        generateButtonContainer: getEl("generate-button-container"),
        loadingIndicator: getEl("loading-indicator"),
        errorMessageDiv: getEl("error-message"),
        seedColorsDisplayContainer: getEl("seed-colors-display").querySelector(
          ".swatch-container"
        ),
        paletteDisplay: getEl("palette-display"),
        componentExamplesDiv: getEl("component-examples"),
        generateMwcComponentsButton: getEl("generate-mwc-components-button"),
        generateGeminiComponentsButton: getEl(
          "generate-gemini-components-button"
        ),
        componentStylePromptInput: getEl("component-style-prompt"),
        geminiComponentLoadingIndicator: getEl("gemini-component-loading"),
        mwcComponentPreview: getEl("mwc-component-preview"),
        geminiComponentPreview: getEl("gemini-component-preview"),
        dynamicThemeStyles: getEl("dynamic-theme-styles"),
        bodyElement: document.body,
        themeToggleButton: getEl("theme-toggle"),
        themeToggleIcon: getEl("theme-toggle").querySelector(".material-icons"),
        minimapContent: getEl("minimap-content"),
        useM3GuidanceCheckbox: getEl("use-m3-guidance-checkbox"),
        m3GuidanceOptionContainer: getEl("m3-guidance-option-container"),
        paletteGenerationMethodSelection: getEl(
          "palette-generation-method-selection"
        ),
        backButton: getEl("back-button"),
        backButtonArea: $(".back-button-area"),
        phase1Card: getEl("phase-1-card"),
        phase2Card: getEl("phase-2-card"),
      };

      const placeholders = {
        palette:
          '<p class="placeholder">Configure inputs and click Generate/Process.</p>',
        seeds: '<p class="placeholder">Seeds appear here.</p>',
        noPalettes: '<p class="placeholder error">Invalid theme generated.</p>',
        noSuggestions:
          '<p style="color: var(--md-sys-color-outline-light); font-size: 0.9em;">No valid suggestions generated.</p>',
        noValidSuggestions:
          '<p style="color: var(--md-sys-color-outline-light);">No valid suggestions could be displayed.</p>',
        suggestionsLabelText:
          "<span class='selection-group-label'>Select a suggested color set:</span>",
        suggestionsLabelImage:
          "<span class='selection-group-label'>Select a suggested color set:</span>",
        suggestionsApiError:
          '<p class="error">API not configured or suggestion failed.</p>',
        suggestionsLoadError:
          '<p class="error">Failed to load suggestions.</p>',
        mwcPreview:
          '<h4>MWC Preview</h4><p class="placeholder">Click "Gen Deterministic" to preview.</p>',
        geminiPreview:
          '<h4>Gemini Preview</h4><p class="placeholder">Click "Gen Gemini Comp" to preview.</p>',
        geminiPreviewError:
          '<h4 class="error">Gemini Preview</h4><p class="error">Failed to generate components via Gemini.</p>',
        generating: '<p class="placeholder">Generating theme...</p>',
        paletteError:
          '<p class="placeholder error">Error generating theme.</p>',
        seedUnavailable:
          '<p style="font-size:0.9em;color:var(--md-sys-color-outline-light);">Seed colors unavailable.</p>',
      };

      const workflowSteps = {
        START: {
          id: "start",
          label: "Start",
          type: "start",
          description: "Workflow begins.",
          code: "initializeApp()",
          stepNo: 1,
        },
        SELECT_SOURCE: {
          id: "select_source",
          label: "Select Source",
          type: "human",
          description: "User chooses input source (Text, Color, Image).",
          code: "handleInputSourceChange()",
          stepNo: 2,
        },
        INPUT_TEXT: {
          id: "input_text",
          label: "Input Text",
          type: "human",
          description: "User types a theme description.",
          code: "dom.textPromptInput.value",
          stepNo: 3,
        },
        SELECT_TEXT_SEED_COUNT: {
          id: "select_text_seed",
          label: "Select Text Seed #",
          type: "human",
          description: "User chooses single/multi seed for text.",
          code: "handleOptionChange()",
          stepNo: 4,
        },
        SELECT_TEXT_METHOD: {
          id: "select_text_method",
          label: "Select Text Method",
          type: "human",
          description: "User chooses suggestion/selection method.",
          code: "handleOptionChange()",
          stepNo: 5,
        },
        CLICK_PROCESS_TEXT: {
          id: "click_process_text",
          label: "Process Text",
          type: "human",
          description: "User clicks button to get text suggestions.",
          code: "handleProcessTextClick()",
          stepNo: 6,
        },
        INPUT_COLOR: {
          id: "input_color",
          label: "Input Color(s)",
          type: "human",
          description: "User selects seed color(s) via pickers.",
          code: "dom.sourceColorInputsContainer inputs",
          stepNo: 3,
        },
        SELECT_COLOR_SEED_COUNT: {
          id: "select_color_seed",
          label: "Select Color Seed #",
          type: "human",
          description: "User chooses single/multi color inputs.",
          code: "handleOptionChange()",
          stepNo: 4,
        },
        INPUT_IMAGE: {
          id: "input_image",
          label: "Input Image",
          type: "human",
          description: "User uploads or drops an image file.",
          code: "handleImageFile(file)",
          stepNo: 3,
        },
        SELECT_IMAGE_EXTRACTOR: {
          id: "select_image_extractor",
          label: "Select Img Extractor",
          type: "human",
          description: "User chooses Material Color Utils/Gemini for image.",
          code: "handleOptionChange()",
          stepNo: 4,
        },
        SELECT_IMAGE_SEED_COUNT: {
          id: "select_image_seed",
          label: "Select Img Seed #",
          type: "human",
          description: "User chooses single/multi seed for image.",
          code: "handleOptionChange()",
          stepNo: 5,
        },
        SELECT_IMAGE_METHOD: {
          id: "select_image_method",
          label: "Select Img Method",
          type: "human",
          description:
            "User chooses suggestion/selection method for Gemini image.",
          code: "handleOptionChange()",
          stepNo: 6,
        },
        CLICK_PROCESS_IMAGE: {
          id: "click_process_image",
          label: "Process Image (Gemini)",
          type: "human",
          description: "User clicks button for Gemini image processing.",
          code: "handleProcessImageGeminiClick()",
          stepNo: 7,
        },
        SELECT_PALETTE_GEN_METHOD: {
          id: "select_palette_gen_method",
          label: "Select Gen Method",
          type: "human",
          description: "User selects palette generation method.",
          code: "handleOptionChange()",
          stepNo: 8,
        },
        CLICK_GENERATE: {
          id: "click_generate",
          label: "Generate Theme",
          type: "human",
          description:
            "User clicks button to generate theme from current inputs.",
          code: "handleGenerateClick()",
          stepNo: 9,
        },
        CLICK_GEN_MWC: {
          id: "click_gen_mwc",
          label: "Gen Deterministic",
          type: "human",
          description:
            "User clicks button to render Material Web Components preview.",
          code: "handleGenerateMwcComponents()",
          stepNo: 11,
        },
        CLICK_GEN_GEMINI: {
          id: "click_gen_gemini",
          label: "Gen Gemini Comp",
          type: "human",
          description:
            "User clicks button to generate LLM-styled HTML components.",
          code: "handleGenerateGeminiComponents()",
          stepNo: 12,
        },
        MCP_WRAP_SUGGEST: {
          id: "mcp_wrap_suggest",
          label: "MCP: SuggestColors",
          type: "mcp",
          description: "System wraps LLM request for color suggestions.",
          code: "getGeminiSuggestions(prompt)",
          stepNo: 6.1,
        },
        MCP_WRAP_SELECT: {
          id: "mcp_wrap_select",
          label: "MCP: SelectBest",
          type: "mcp",
          description:
            "System wraps LLM request to select the best suggestion.",
          code: "getGeminiBestSuggestion(suggestions, prompt)",
          stepNo: 7.1,
        },
        MCP_WRAP_GENERATE: {
          id: "mcp_wrap_generate",
          label: "MCP: Prep Theme Gen",
          type: "mcp",
          description:
            "System prepares parameters for the color utility library.",
          code: "Prepare call to generateThemeInternal()",
          stepNo: 9.1,
        },
        MCP_WRAP_IMG_EXTRACT: {
          id: "mcp_wrap_img_extract",
          label: "MCP: Img Extract",
          type: "mcp",
          description: "System wraps LLM request for image color extraction.",
          code: "getGeminiImageSuggestions(image)",
          stepNo: 7.1,
        },
        MCP_INVOKE_TOOL: {
          id: "mcp_invoke_tool",
          label: "MCP: Invoke Tool",
          type: "mcp",
          description: "System (or LLM via MCP) invokes the Material Color Utils tool.",
          code: "generateThemeInternal() or simulateMaterialTheme()",
          stepNo: 9.2,
        },
        MCP_WRAP_GEN_COMP: {
          id: "mcp_wrap_gen_comp",
          label: "MCP: GenerateComponents",
          type: "mcp",
          description: "System wraps LLM request for component generation.",
          code: "getGeminiContent(...)",
          stepNo: 12.1,
        },
        LLM_SUGGEST: {
          id: "llm_suggest",
          label: "LLM: Suggest",
          type: "llm",
          description:
            "LLM processes prompt/image and returns color suggestions.",
          code: "fetch(geminiApiEndpointColorPicker, ...)",
          stepNo: 6.2,
        },
        LLM_SELECT_BEST: {
          id: "llm_select_best",
          label: "LLM: Select Best",
          type: "llm",
          description: "LLM analyzes suggestions and selects the best fit.",
          code: "fetch(geminiApiEndpointColorPicker, ...)",
          stepNo: 7.2,
        },
        LLM_INVOKE_TOOL: {
          id: "llm_invoke_tool",
          label: "LLM: Invoke Tool",
          type: "llm",
          description: "LLM decides to call the generation tool (via MCP).",
          code: "(Function Call -> MCP)",
          stepNo: 9.3,
        },
        LLM_GEN_PALETTE: {
          id: "llm_gen_palette",
          label: "LLM: Generate Palette",
          type: "llm",
          description: "LLM generates the full palette JSON directly.",
          code: "fetch(geminiApiEndpointComponentGenerator, ...)",
          stepNo: 9.5,
        },
        LLM_GEN_COMP: {
          id: "llm_gen_comp",
          label: "LLM: Generate Comp",
          type: "llm",
          description: "LLM generates HTML/CSS components.",
          code: "fetch(geminiApiEndpointComponentGenerator, ...)",
          stepNo: 12.2,
        },
        TOOL_IMAGE_PROC_MATERIAL: {
          id: "tool_image_proc_material",
          label: "Tool: Img Proc (Material)",
          type: "tool",
          description: "Material Color Utils extracts color(s) from image data.",
          code: "sourceColor(s)FromImage(img, ...)",
          stepNo: 7.3,
        },
        TOOL_COLOR_MATH: {
          id: "tool_color_math",
          label: "Tool: Color Math",
          type: "tool",
          description: "Material Color Utils calculates the full theme palette.",
          code: "themeFromSourceColor(s)(...)",
          stepNo: 9.4,
        },
        TOOL_RENDER_MWC: {
          id: "tool_render_mwc",
          label: "Tool: Render MWC",
          type: "tool",
          description: "System renders standard Material Web Components.",
          code: "dom.mwcComponentPreview.innerHTML = ...",
          stepNo: 11.1,
        },
        SELECT_SUGGESTION: {
          id: "select_suggestion",
          label: "Select Suggestion",
          type: "human",
          description: "User clicks on one of the suggested color sets.",
          code: "handleSuggestionSelection()",
          stepNo: 8,
        },
        APPLY_LLM_SELECTION: {
          id: "apply_llm_selection",
          label: "Apply LLM Selection",
          type: "decision",
          description: "System automatically applies the LLM-selected colors.",
          code: "applySuggestionToUI(bestSuggestion)",
          stepNo: 8.1,
        },
        DISPLAY_SUGGESTIONS: {
          id: "display_suggestions",
          label: "Display Suggestions",
          type: "result",
          description: "Color suggestions are rendered for user selection.",
          code: "displaySuggestions(data, type)",
          stepNo: 7.4,
        },
        DISPLAY_THEME: {
          id: "display_theme",
          label: "Display Theme",
          type: "result",
          description: "Generated color palette swatches are displayed.",
          code: "displayTheme(theme)",
          stepNo: 10,
        },
        DISPLAY_COMPONENTS: {
          id: "display_components",
          label: "Display Components",
          type: "result",
          description: "MWC or LLM component previews are displayed.",
          code: "dom.mwcComponentPreview / dom.geminiComponentPreview",
          stepNo: 13,
        },
        ERROR: {
          id: "error",
          label: "Error",
          type: "error",
          description: "An error occurred during the process.",
          code: "showError(message)",
          stepNo: 99,
        },
        GO_BACK: {
          id: "go_back",
          label: "Go Back",
          type: "decision",
          description: "User navigates back to a previous step.",
          code: "handleBackButtonClick()",
          stepNo: 98,
        },
      };

      const audio = {
        context: null,
        mainGain: null,
        isInitialized: false,
        isPlayingIntro: false,
        stepNotes: ["C4", "E4", "G4", "C5", "E5", "G5"],
        errorNote: "C3",
        transitionChord: ["C4", "G4", "C5"],
        noteFrequencies: {
          C3: 130.81,
          D3: 146.83,
          E3: 164.81,
          F3: 174.61,
          G3: 196.0,
          A3: 220.0,
          B3: 246.94,
          C4: 261.63,
          D4: 293.66,
          E4: 329.63,
          F4: 349.23,
          G4: 392.0,
          A4: 440.0,
          B4: 493.88,
          C5: 523.25,
          D5: 587.33,
          E5: 659.25,
          F5: 698.46,
          G5: 783.99,
          A5: 880.0,
          B5: 987.77,
        },
        nextNoteIndex: 0,
        tooltipTimeout: null,
        activeTooltip: null,
        introSequenceIndex: 0,
      };

      const sevSequenceNotes = [
        "E4",
        "G4",
        "E4",
        "C4",
        ["E3", "G3", "C4"],
        "G4",
        "C3",
        "C5",
        ["C4", "E4", "G4"],
        "E5",
      ];

      const sevSequenceEdges = [
        workflowSteps.SELECT_SOURCE,
        workflowSteps.INPUT_TEXT,
        workflowSteps.CLICK_PROCESS_TEXT,
        workflowSteps.MCP_WRAP_SUGGEST,
        workflowSteps.LLM_SUGGEST,
        workflowSteps.DISPLAY_SUGGESTIONS,
        workflowSteps.SELECT_SUGGESTION,
        workflowSteps.CLICK_GENERATE,
        workflowSteps.MCP_WRAP_GENERATE,
        workflowSteps.DISPLAY_THEME,
      ];

      const sevSequenceTypes = [
        "note",
        "note",
        "note",
        "note",
        "chord",
        "note",
        "note",
        "note",
        "chord",
        "note",
      ];

      const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
      const sanitizeHtml = (str) => {
        const temp = createEl("div");
        setText(temp, str);
        return temp.innerHTML;
      };
      const kebabCase = (str) => str.replace(/([A-Z])/g, "-$1").toLowerCase();
      const sanitizeForCssVariable = (str) =>
        (str || "custom")
          .replace(/[^a-zA-Z0-9_-]/g, "-")
          .replace(/-+/g, "-")
          .replace(/^-+|-+$/g, "");
      function hexToArgbInt(hex) {
        if (!hex) return 0;
        hex = hex.replace("#", "");
        if (hex.length === 3)
          hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        if (hex.length !== 6) return 0;
        return (parseInt(`ff${hex}`, 16) | 0) >>> 0;
      }
      function argbIntToHex(argb) {
        if (typeof argb !== "number" || isNaN(argb) || argb < 0)
          argb = argb >>> 0;
        const r = (argb >> 16) & 0xff;
        const g = (argb >> 8) & 0xff;
        const b = argb & 0xff;
        return `#${[r, g, b]
          .map((c) => c.toString(16).padStart(2, "0"))
          .join("")}`;
      }
      function getContrastColor(hex) {
        if (!hex || hex.length < 4) return "#000000";
        hex = hex.replace("#", "");
        if (hex.length === 3)
          hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        if (hex.length !== 6) return "#000000";
        const r = parseInt(hex.substring(0, 2), 16) / 255;
        const g = parseInt(hex.substring(2, 4), 16) / 255;
        const b = parseInt(hex.substring(4, 6), 16) / 255;
        const rLinear =
          r <= 0.03928 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
        const gLinear =
          g <= 0.03928 ? g / 12.92 : Math.pow((g + 0.055) / 1.055, 2.4);
        const bLinear =
          b <= 0.03928 ? b / 12.92 : Math.pow((b + 0.055) / 1.055, 2.4);
        const lum = 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
        const contrastWithWhite = (1 + 0.05) / (lum + 0.05);
        const contrastWithBlack = (lum + 0.05) / (0 + 0.05);
        return contrastWithBlack >= 4.5 || contrastWithBlack > contrastWithWhite
          ? "#000000"
          : "#FFFFFF";
      }
      function createSwatchHtml(name, colorInt, extraClass = "") {
        const hex = argbIntToHex(colorInt);
        const contrast = getContrastColor(hex);
        const safeName = sanitizeHtml(name || "");
        return `<div class="swatch ${extraClass}" style="background-color: ${hex}; color: ${contrast};" title="${safeName} - ${hex}"><span class="swatch-name">${safeName}</span><span class="swatch-hex">${hex}</span></div>`;
      }
      function showError(msg) {
        setText(dom.errorMessageDiv, msg);
        hideEl(dom.errorMessageDiv, false);
        addStepToMinimapQueue(workflowSteps.ERROR, "error");
        toggleBackButton(true);
      }
      function hideError() {
        hideEl(dom.errorMessageDiv, true);
        setText(dom.errorMessageDiv, "");
      }
      function setUILoading(isLoading, source = "") {
        setText(
          dom.loadingIndicator,
          isLoading ? `Generating theme (${source})...` : ""
        );
        hideEl(dom.loadingIndicator, !isLoading);
        disableEl(dom.generateButton, isLoading);
        toggleClass(
          dom.generateButtonContainer,
          "status-active",
          isLoading && !isUserActionRequired(state.currentInputSource)
        );
      }
      function setSuggestionLoading(isLoading, type = "text") {
        const indicator =
          type === "image"
            ? dom.imageSuggestionLoadingIndicator
            : dom.suggestionLoadingIndicator;
        const button =
          type === "image"
            ? dom.processImageGeminiButton
            : dom.processTextButton;
        hideEl(indicator, !isLoading);
        disableEl(button, isLoading);
        if (type === "text") disableEl(dom.textPromptInput, isLoading);
      }
      function setGeminiComponentLoading(isLoading) {
        hideEl(dom.geminiComponentLoadingIndicator, !isLoading);
        disableEl(dom.generateGeminiComponentsButton, isLoading);
        disableEl(dom.generateMwcComponentsButton, isLoading);
      }

      function initializeAudio() {
        if (audio.isInitialized || !window.AudioContext) return;
        try {
          audio.context = new AudioContext();
          audio.mainGain = audio.context.createGain();
          audio.mainGain.gain.setValueAtTime(0.15, audio.context.currentTime);
          audio.mainGain.connect(audio.context.destination);
          audio.isInitialized = true;
        } catch (e) {
          audio.isInitialized = false;
        }
      }
      function getNoteFrequency(note) {
        return audio.noteFrequencies[note] || 440;
      }
      function playNote(note, duration = 0.15, delay = 0) {
        if (
          !audio.isInitialized ||
          !audio.context ||
          audio.context.state === "suspended"
        )
          return;
        const oscillator = audio.context.createOscillator();
        const noteGain = audio.context.createGain();
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(
          getNoteFrequency(note),
          audio.context.currentTime + delay
        );
        noteGain.gain.setValueAtTime(0, audio.context.currentTime + delay);
        noteGain.gain.linearRampToValueAtTime(
          1,
          audio.context.currentTime + delay + 0.01
        );
        noteGain.gain.exponentialRampToValueAtTime(
          0.0001,
          audio.context.currentTime + delay + duration
        );
        oscillator.connect(noteGain);
        noteGain.connect(audio.mainGain);
        oscillator.start(audio.context.currentTime + delay);
        oscillator.stop(audio.context.currentTime + delay + duration);
      }
      function playChord(notes, duration = 0.3, delay = 0, stagger = 0.03) {
        if (!audio.isInitialized) return;
        notes.forEach((note, index) =>
          playNote(note, duration, delay + index * stagger)
        );
      }

      function positionTooltip(targetElement, tooltipElement) {
        if (!targetElement || !tooltipElement) return;
        const targetRect = targetElement.getBoundingClientRect();
        tooltipElement.style.position = "fixed";
        tooltipElement.style.left = `${
          targetRect.left - tooltipElement.offsetWidth - 10
        }px`;
        tooltipElement.style.top = `${
          targetRect.top +
          targetRect.height / 2 -
          tooltipElement.offsetHeight / 2
        }px`;

        const tooltipRect = tooltipElement.getBoundingClientRect();
        if (tooltipRect.left < 0) {
          tooltipElement.style.left = `${targetRect.right + 10}px`;
          tooltipElement.style.top = `${
            targetRect.top +
            targetRect.height / 2 -
            tooltipElement.offsetHeight / 2
          }px`;
        }
        if (tooltipRect.top < 0) {
          tooltipElement.style.top = "5px";
        }
        if (tooltipRect.bottom > window.innerHeight) {
          tooltipElement.style.top = `${
            window.innerHeight - tooltipElement.offsetHeight - 5
          }px`;
        }
      }
      function showTooltip(targetElement) {
        if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
        hideTooltip();
        const tooltip = targetElement.querySelector(".minimap-tooltip");
        if (!tooltip) return;
        audio.activeTooltip = tooltip;
        tooltip.style.visibility = "visible";
        tooltip.style.opacity = "1";
        positionTooltip(targetElement, tooltip);
      }
      function hideTooltip() {
        if (audio.activeTooltip) {
          audio.activeTooltip.style.opacity = "0";
          audio.activeTooltip.style.visibility = "hidden";
          audio.activeTooltip = null;
        }
        if (audio.tooltipTimeout) {
          clearTimeout(audio.tooltipTimeout);
          audio.tooltipTimeout = null;
        }
      }
      function setupTooltipListeners(element) {
        element.addEventListener("mouseenter", (e) => {
          if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
          audio.tooltipTimeout = setTimeout(
            () => showTooltip(e.currentTarget),
            150
          );
        });
        element.addEventListener("mouseleave", () => {
          if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
          audio.tooltipTimeout = setTimeout(hideTooltip, 100);
        });
        element.addEventListener("focus", (e) => {
          if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
          showTooltip(e.currentTarget);
        });
        element.addEventListener("blur", () => {
          if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
          audio.tooltipTimeout = setTimeout(hideTooltip, 100);
        });
        const tooltip = element.querySelector(".minimap-tooltip");
        if (tooltip) {
          tooltip.addEventListener("mouseenter", () => {
            if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
          });
          tooltip.addEventListener("mouseleave", () => {
            if (audio.tooltipTimeout) clearTimeout(audio.tooltipTimeout);
            audio.tooltipTimeout = setTimeout(hideTooltip, 100);
          });
        }
      }

      function addStepToMinimapQueue(step, edgeType = "human") {
        if (!step) return;
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        state.minimapUpdateQueue.push({ step, edgeType });
        if (!state.isMinimapUpdating) {
          processMinimapQueue();
        }
      }

      async function processMinimapQueue() {
        if (state.minimapUpdateQueue.length === 0) {
          state.isMinimapUpdating = false;
          return;
        }
        state.isMinimapUpdating = true;
        const { step, edgeType } = state.minimapUpdateQueue.shift();
        const isNewStep =
          !state.currentMinimapSteps.length ||
          step.id !==
            state.currentMinimapSteps[state.currentMinimapSteps.length - 1].id;

        if (isNewStep) {
          state.currentMinimapSteps.push({
            ...step,
            edge: edgeType || "human",
          });
          playSevSequenceStep();
        } else if (state.currentMinimapSteps.length > 0) {
          state.currentMinimapSteps[state.currentMinimapSteps.length - 1].edge =
            edgeType ||
            state.currentMinimapSteps[state.currentMinimapSteps.length - 1]
              .edge ||
            "human";
        }

        renderMinimap(isNewStep);

        await delay(isNewStep ? config.MINIMAP_STEP_DELAY : 50);
        processMinimapQueue();
      }

      function renderMinimap(stepAdded = false) {
        setHtml(dom.minimapContent, "");
        const fragment = document.createDocumentFragment();

        state.currentMinimapSteps
          .sort((a, b) => a.stepNo - b.stepNo)
          .forEach((step, index) => {
            const isLastNode = index === state.currentMinimapSteps.length - 1;

            const nodeEl = createEl("div");
            nodeEl.className = `minimap-node node-${step.type}`;
            setText(nodeEl, step.label);
            nodeEl.tabIndex = 0;
            if (isLastNode) nodeEl.classList.add("active");

            const tooltipEl = createEl("div");
            tooltipEl.className = "minimap-tooltip";
            let tooltipContent = step.description || `Step: ${step.label}`;
            if (step.code)
              tooltipContent += `<code class="minimap-tooltip-code">${sanitizeHtml(
                step.code
              )}</code>`;
            setHtml(tooltipEl, tooltipContent);
            nodeEl.appendChild(tooltipEl);
            fragment.appendChild(nodeEl);
            setupTooltipListeners(nodeEl);

            if (index < state.currentMinimapSteps.length - 1) {
              const nextStep = state.currentMinimapSteps[index + 1];
              const edgeEl = createEl("div");
              const edgeClass = nextStep.edge || "human";
              edgeEl.className = `minimap-edge edge-${edgeClass}`;
              edgeEl.tabIndex = 0;
              const edgeStep = {
                id: `edge_${step.id}_${nextStep.id}`,
                label: `Transition via ${edgeClass}`,
                type: "edge",
                description:
                  edgeClass === "gemini-bridge"
                    ? `LLM API call (${step.label} -> ${nextStep.label})`
                    : `Transition from ${step.label} to ${nextStep.label} via ${edgeClass}.`,
                code: step.code
                  ? `${step.code} -> ${nextStep.code || "..."}`
                  : `Via: ${edgeClass}`,
              };
              const edgeTooltipEl = createEl("div");
              edgeTooltipEl.className = "minimap-tooltip";
              let edgeTooltipContent = edgeStep.description;
              if (
                edgeStep.code &&
                edgeClass !== "human" &&
                edgeClass !== "result"
              ) {
                edgeTooltipContent += `<code class="minimap-tooltip-code">${sanitizeHtml(
                  edgeStep.code
                )}</code>`;
              }
              setHtml(edgeTooltipEl, edgeTooltipContent);
              edgeEl.appendChild(edgeTooltipEl);
              if (index === state.currentMinimapSteps.length - 2)
                edgeEl.classList.add("active");
              fragment.appendChild(edgeEl);
              setupTooltipListeners(edgeEl);
            }
          });

        dom.minimapContent.appendChild(fragment);

        const elementsToAnimate = Array.from(dom.minimapContent.children);
        if (stepAdded && elementsToAnimate.length > 0) {
          const lastAdded =
            elementsToAnimate.length > 1
              ? [
                  elementsToAnimate[elementsToAnimate.length - 2],
                  elementsToAnimate[elementsToAnimate.length - 1],
                ]
              : [elementsToAnimate[0]];
          lastAdded.forEach((el) => {
            requestAnimationFrame(() => {
              el.style.transition = "none";
              el.style.opacity = "0";
              requestAnimationFrame(() => {
                el.style.transition = `opacity ${config.MINIMAP_ANIMATION_DURATION}ms ease-in-out`;
                el.classList.add("visible");
              });
            });
          });
          elementsToAnimate
            .slice(0, elementsToAnimate.length - lastAdded.length)
            .forEach((el) => el.classList.add("visible"));
        } else {
          elementsToAnimate.forEach((el) => el.classList.add("visible"));
        }

        const lastElement = dom.minimapContent.lastElementChild;
        if (lastElement) {
          lastElement.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }

      function playSevSequenceStep() {
        if (!audio.isInitialized) {
          initializeAudio();
          if (!audio.isInitialized) return;
        }
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        if (audio.introSequenceIndex < sevSequenceNotes.length) {
          const note = sevSequenceNotes[audio.introSequenceIndex];
          const type = sevSequenceTypes[audio.introSequenceIndex] || "note";
          if (type === "note") playNote(note, 0.15);
          else if (type === "chord") playChord(note, 0.3);
          audio.introSequenceIndex++;
        } else {
          audio.introSequenceIndex = 0;
        }
      }

      function resetMinimap(startNode = workflowSteps.START, playSound = true) {
        state.currentMinimapSteps = [];
        state.minimapUpdateQueue = [];
        state.isMinimapUpdating = false;
        setHtml(dom.minimapContent, "");
        addStepToMinimapQueue(startNode);
      }

      function resetMinimapToBase() {
        state.currentMinimapSteps = [workflowSteps.START];
        renderMinimap();
        const currentSource =
          getSelectedValue(dom.inputSourceSelection) ||
          config.defaultInputSource;
        addStepToMinimapQueue(workflowSteps.SELECT_SOURCE);
        updatePhase1UI();
      }

      function loadImageFromSrc(src) {
        return new Promise((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve(img);
          img.onerror = (err) =>
            reject(
              new Error(`Image could not be loaded: ${err.type || "error"}`)
            );
          img.src = src;
          if (img.complete && img.naturalWidth > 0)
            setTimeout(() => resolve(img), 0);
        });
      }
      function validateAndConvertHex(hex, label) {
        const argb = hexToArgbInt(hex);
        if (argb === 0 && !["#000", "#000000"].includes(hex?.toLowerCase()))
          throw new Error(`Invalid hex value for ${label}: ${hex}`);
        return argb;
      }

      function displaySeedColors(seeds, theme) {
        setHtml(dom.seedColorsDisplayContainer, "");
        let displayedSeeds = [];
        if (seeds?.length) {
          displayedSeeds = seeds;
        } else if (theme?.source) {
          const sourceSeed = Array.isArray(theme.source)
            ? theme.source[0]
            : theme.source;
          if (typeof sourceSeed === "number") displayedSeeds = [sourceSeed];
        }
        displayedSeeds.forEach((seed, i) => {
          if (typeof seed === "number")
            dom.seedColorsDisplayContainer.innerHTML += createSwatchHtml(
              `Seed ${i + 1}`,
              seed,
              "seed-swatch"
            );
        });
        if (!dom.seedColorsDisplayContainer.hasChildNodes())
          setHtml(dom.seedColorsDisplayContainer, placeholders.seedUnavailable);
      }
      function loadConfig() {
        try {
          if (typeof APP_CONFIG === "undefined")
            throw new Error("config.js not loaded or APP_CONFIG missing.");
          Object.assign(config, {
            ENABLE_IMAGES: !!APP_CONFIG.ENABLE_IMAGES,
            USE_M3_TXT_SYS_PROMPT: !!APP_CONFIG.USE_M3_TXT_SYS_PROMPT,
            ENABLE_AUTO_MODES: !!APP_CONFIG.ENABLE_AUTO_MODES,
            API_KEY: APP_CONFIG.API_KEY || null,
            GEMINI_MODEL: APP_CONFIG.GEMINI_MODEL || null,
            defaultInputSource: APP_CONFIG.DEFAULT_MODE || "text",
            MINIMAP_STEP_DELAY: APP_CONFIG.MINIMAP_STEP_DELAY ?? 1000,
            MINIMAP_ANIMATION_DURATION:
              APP_CONFIG.MINIMAP_ANIMATION_DURATION ?? 400,
          });
          config.GEMINI_MODEL_COLOR_PICKER =
            APP_CONFIG.GEMINI_MODEL_COLOR_PICKER || config.GEMINI_MODEL;
          config.GEMINI_MODEL_COMPONENT_GENERATOR =
            APP_CONFIG.GEMINI_MODEL_COMPONENT_GENERATOR || config.GEMINI_MODEL;

          document.documentElement.style.setProperty(
            "--minimap-transition-duration",
            `${config.MINIMAP_ANIMATION_DURATION}ms`
          );

          if (
            config.defaultInputSource.startsWith("modeImage") &&
            !config.ENABLE_IMAGES
          )
            config.defaultInputSource = "text";
          else if (config.defaultInputSource.startsWith("mode"))
            config.defaultInputSource = "text";
          state.currentInputSource = config.defaultInputSource;

          if (
            !config.API_KEY ||
            config.API_KEY === "YOUR_API_KEY_HERE" ||
            !config.GEMINI_MODEL
          ) {
            config.isApiConfigValid = false;
            showApiKeyPopup(); // Show the modal instead of showError
          } else {
            const modelIdBase = config.GEMINI_MODEL.startsWith("models/")
              ? config.GEMINI_MODEL
              : `models/${config.GEMINI_MODEL}`;
            const modelIdColorPicker =
              (config.GEMINI_MODEL_COLOR_PICKER &&
                (config.GEMINI_MODEL_COLOR_PICKER.startsWith("models/")
                  ? config.GEMINI_MODEL_COLOR_PICKER
                  : `models/${config.GEMINI_MODEL_COLOR_PICKER}`)) ||
              modelIdBase;
            const modelIdComponentGenerator =
              (config.GEMINI_MODEL_COMPONENT_GENERATOR &&
                (config.GEMINI_MODEL_COMPONENT_GENERATOR.startsWith("models/")
                  ? config.GEMINI_MODEL_COMPONENT_GENERATOR
                  : `models/${config.GEMINI_MODEL_COMPONENT_GENERATOR}`)) ||
              modelIdBase;
            const apiPrefix =
              "https://generativelanguage.googleapis.com/v1beta/";
            config.geminiApiEndpointBase = `${apiPrefix}${modelIdBase}`;
            config.geminiApiEndpointColorPicker = `${apiPrefix}${modelIdColorPicker}`;
            config.geminiApiEndpointComponentGenerator = `${apiPrefix}${modelIdComponentGenerator}`;
            config.isApiConfigValid = true;
          }
        } catch (error) {
          console.error("Error loading config.js:", error);
          showError("Config error. Using simulation, limited features.");
          config.isApiConfigValid = false;
        } finally {
          const defaultRadio = getEl(
            `source${
              config.defaultInputSource.charAt(0).toUpperCase() +
              config.defaultInputSource.slice(1)
            }`
          );
          if (defaultRadio) defaultRadio.checked = true;
          else getEl("sourceText").checked = true;
          state.currentInputSource = $(
            `input[name="inputSource"]:checked`
          ).value;
          setSelectedChip(dom.paletteGenerationMethodSelection, "material");
          state.generationMethod = "material";
        }
      }
      function applyFeatureVisibility() {
        const features = {
          image: config.ENABLE_IMAGES,
          api: config.isApiConfigValid,
          auto: config.ENABLE_AUTO_MODES && config.isApiConfigValid,
        };
        hideEl(dom.sourceImageContainer, !features.image);
        hideEl(getEl("textSelectGeminiMCP").parentNode, !features.auto);
        hideEl(
          dom.imageExtractGeminiContainer,
          !features.api || !features.image
        );
        hideEl(
          dom.imageSelectGeminiMCPContainer,
          !features.auto || !features.image
        );

        const simCheckboxLabel = dom.useSimulationCheckbox?.labels?.[0];
        if (simCheckboxLabel) {
          simCheckboxLabel.style.opacity = features.api ? "1" : "0.6";
          simCheckboxLabel.style.cursor = features.api
            ? "pointer"
            : "not-allowed";
          disableEl(dom.useSimulationCheckbox, !features.api);
          dom.useSimulationCheckbox.checked = !features.api;
        }

        [
          dom.processTextButton,
          dom.processImageGeminiButton,
          dom.generateGeminiComponentsButton,
        ].forEach((btn) => {
          if (btn)
            setAttr(
              btn,
              "title",
              !features.api ? "Gemini API not configured." : ""
            );
        });
        hideEl(dom.generateGeminiComponentsButton, !features.api);
        hideEl(dom.m3GuidanceOptionContainer, !features.api);

        const selectedSourceRadio = $(`input[name="inputSource"]:checked`);
        if (selectedSourceRadio?.value === "image" && !features.image) {
          getEl("sourceText").checked = true;
          state.currentInputSource = "text";
        }
        updatePhase1UI();
      }
      function applyTheme() {
        toggleClass(dom.bodyElement, "dark-theme", state.isDarkMode);
        setText(
          dom.themeToggleIcon,
          state.isDarkMode ? "light_mode" : "dark_mode"
        );
        toggleClass(dom.mwcComponentPreview, "dark-theme", state.isDarkMode);
        toggleClass(dom.geminiComponentPreview, "dark-theme", state.isDarkMode);
        if (state.lastGeneratedTheme)
          applyScopedThemeStyles(state.lastGeneratedTheme);
      }
      function handleThemeToggle() {
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        state.isDarkMode = !state.isDarkMode;
        localStorage.setItem("themeMode", state.isDarkMode ? "dark" : "light");
        applyTheme();
        addStepToMinimapQueue(workflowSteps.SELECT_SOURCE, "human");
      }
      function setupThemeToggle() {
        const storedTheme = localStorage.getItem("themeMode");
        state.isDarkMode = storedTheme === "dark";
        applyTheme();
      }
      function displayTheme(theme) {
        setHtml(dom.paletteDisplay, "");
        state.lastGeneratedTheme = theme;
        if (!theme?.palettes || !theme?.schemes) {
          setHtml(dom.paletteDisplay, placeholders.noPalettes);
          hideEl(dom.componentExamplesDiv, true);
          showError("Invalid theme data received.");
          addStepToMinimapQueue(workflowSteps.ERROR, "error");
          return;
        }
        hideError();
        dom.phase2Card.className = "phase-card output-section phase-local-tool";
        const schemeKeys = [
          "primary",
          "secondary",
          "tertiary",
          "neutral",
          "neutralVariant",
          "error",
        ];
        schemeKeys.forEach((key) => {
          if (!theme.palettes[key]) return;
          const section = createEl("div");
          section.className = "palette-section color-group";
          const title =
            key.charAt(0).toUpperCase() +
            key.slice(1).replace(/([A-Z])/g, " $1");
          setHtml(section, `<h4>${title} Roles</h4>`);
          const swatches = createEl("div");
          swatches.className = "scheme-swatches";
          const capKey = key.charAt(0).toUpperCase() + key.slice(1);
          const roles = [
            { n: `${key}(L)`, k: key, s: "light" },
            { n: `On ${key}(L)`, k: `on${capKey}`, s: "light" },
            { n: `${key} Cont.(L)`, k: `${key}Container`, s: "light" },
            { n: `On ${key} Cont.(L)`, k: `on${capKey}Container`, s: "light" },
            { n: `${key}(D)`, k: key, s: "dark" },
            { n: `On ${key}(D)`, k: `on${capKey}`, s: "dark" },
            { n: `${key} Cont.(D)`, k: `${key}Container`, s: "dark" },
            { n: `On ${key} Cont.(D)`, k: `on${capKey}Container`, s: "dark" },
          ];
          roles.forEach((r) => {
            const scheme = theme.schemes[r.s];
            if (scheme && typeof scheme[r.k] === "number")
              swatches.innerHTML += createSwatchHtml(r.n, scheme[r.k]);
          });
          if (swatches.hasChildNodes()) {
            section.appendChild(swatches);
            dom.paletteDisplay.appendChild(section);
          }
        });

        if (!dom.paletteDisplay.hasChildNodes()) {
          setHtml(dom.paletteDisplay, placeholders.noPalettes);
          hideEl(dom.componentExamplesDiv, true);
        } else {
          hideEl(dom.componentExamplesDiv, false);
          applyScopedThemeStyles(theme);
          setHtml(dom.mwcComponentPreview, placeholders.mwcPreview);
          setHtml(dom.geminiComponentPreview, placeholders.geminiPreview);
          addStepToMinimapQueue(workflowSteps.DISPLAY_THEME, "result");
          state.currentPhaseCardId = "phase-2-card";
          dom.phase2Card.classList.add("phase-local-tool");
        }
      }

      function getSelectedValue(selectionGroup) {
        const selectedRadio = selectionGroup?.querySelector(
          `input[type="radio"]:checked`
        );
        return selectedRadio ? selectedRadio.value : null;
      }

      function isUserActionRequired(source) {
        if (source === "text") {
          return getSelectedValue(dom.textSelectionMethodSelection) === "user";
        } else if (source === "image") {
          const extractionMethod = getSelectedValue(
            dom.imageExtractionMethodSelection
          );
          return (
            extractionMethod === "gemini" &&
            getSelectedValue(dom.imageSelectionMethodSelection) === "user"
          );
        }
        return false;
      }

      function updatePhase1UI() {
        hideError();
        const source =
          getSelectedValue(dom.inputSourceSelection) ??
          state.currentInputSource;
        state.currentInputSource = source;

        hideEl(dom.textOptionsGroup, source !== "text");
        hideEl(dom.colorOptionsGroup, source !== "color");
        hideEl(dom.imageOptionsGroup, source !== "image");

        setHtml(dom.paletteDisplay, placeholders.palette);
        setHtml(dom.seedColorsDisplayContainer, placeholders.seeds);
        hideEl(dom.componentExamplesDiv, true);
        setHtml(dom.mwcComponentPreview, placeholders.mwcPreview);
        setHtml(dom.geminiComponentPreview, placeholders.geminiPreview);
        state.lastSuggestions = { text: null, image: null };
        state.selectedSuggestion = { text: null, image: null };
        toggleBackButton(false);
        dom.phase1Card.className =
          "phase-card input-section phase-human-decision";
        state.currentPhaseCardId = "phase-1-card";

        let stepToAdd = null;
        let needsProcessingButton = false;
        let generateButtonText = "Generate Theme";
        let showGenerateButton = true;

        if (source === "text") {
          const selectionMethod = getSelectedValue(
            dom.textSelectionMethodSelection
          );
          needsProcessingButton = selectionMethod === "user";
          hideEl(dom.textPromptSuggestions, !needsProcessingButton);
          if (
            selectionMethod === "gemini" ||
            selectionMethod === "gemini_mcp"
          ) {
            generateButtonText = "Auto Select & Generate";
            toggleClass(dom.generateButtonContainer, "status-active", true);
          } else {
            toggleClass(dom.generateButtonContainer, "status-active", false);
          }
          hideEl(dom.processTextButton, !needsProcessingButton);
          stepToAdd = workflowSteps.INPUT_TEXT;
        } else if (source === "color") {
          const seedCount = getSelectedValue(dom.colorSeedCountSelection);
          hideEl(dom.multiSourceOptionsArea, seedCount !== "multi");
          updateColorPickers(seedCount);
          toggleClass(dom.generateButtonContainer, "status-active", false);
          stepToAdd = workflowSteps.INPUT_COLOR;
        } else if (source === "image") {
          if (!state.currentImageFile) {
            hideEl(dom.imagePreview, true);
            dom.imagePreview.src = "#";
          }
          const extractionMethod = getSelectedValue(
            dom.imageExtractionMethodSelection
          );
          hideEl(dom.imageMaterialOptions, extractionMethod === "gemini");
          hideEl(dom.imageGeminiOptions, extractionMethod !== "gemini");

          if (extractionMethod === "gemini") {
            const selectionMethod = getSelectedValue(
              dom.imageSelectionMethodSelection
            );
            needsProcessingButton = selectionMethod === "user";
            hideEl(dom.imagePromptSuggestions, !needsProcessingButton);
            if (
              selectionMethod === "gemini" ||
              selectionMethod === "gemini_mcp"
            ) {
              generateButtonText = "Auto Select & Generate";
              toggleClass(dom.generateButtonContainer, "status-active", true);
            } else {
              toggleClass(dom.generateButtonContainer, "status-active", false);
            }
            hideEl(dom.processImageGeminiButton, !needsProcessingButton);
          } else {
            hideEl(dom.processImageGeminiButton, true);
            toggleClass(dom.generateButtonContainer, "status-active", false);
          }
          stepToAdd = workflowSteps.INPUT_IMAGE;
        }

        setText(dom.generateButton, generateButtonText);
        hideEl(dom.generateButtonContainer, !showGenerateButton);

        if (stepToAdd) addStepToMinimapQueue(stepToAdd, "human");
      }

      function updateColorPickers(seedCount) {
        setHtml(dom.sourceColorInputsContainer, "");
        const isMulti = seedCount === "multi";
        if (isMulti) {
          setText(dom.sourceColorLabel, "Source Colors:");
          addSourceColorInput(0, "Primary");
          addSourceColorInput(1, "Secondary");
          addSourceColorInput(2, "Tertiary");
        } else {
          setText(dom.sourceColorLabel, "Source Color:");
          addSourceColorInput(0);
        }
        addStepToMinimapQueue(workflowSteps.SELECT_COLOR_SEED_COUNT, "human");
      }

      function handleInputSourceChange(event) {
        if (event) state.currentInputSource = event.target.value;
        resetMinimapToBase();
        updatePhase1UI();
      }

      function handleOptionChange(event) {
        if (!event || !event.target) return;
        const group = event.target.closest(".chip-selection-group");
        if (!group) return;

        const name = group.dataset.name;
        let step = null;

        switch (name) {
          case "inputSource":
            state.currentInputSource = event.target.value;
            resetMinimapToBase();
            break;
          case "textSeedCount":
            step = workflowSteps.SELECT_TEXT_SEED_COUNT;
            break;
          case "textSelectionMethod":
            step = workflowSteps.SELECT_TEXT_METHOD;
            break;
          case "colorSeedCount":
            step = workflowSteps.SELECT_COLOR_SEED_COUNT;
            break;
          case "imageExtractionMethod":
            step = workflowSteps.SELECT_IMAGE_EXTRACTOR;
            break;
          case "imageSeedCount":
            step = workflowSteps.SELECT_IMAGE_SEED_COUNT;
            break;
          case "imageSelectionMethod":
            step = workflowSteps.SELECT_IMAGE_METHOD;
            break;
          case "paletteGenerationMethod":
            state.generationMethod = event.target.value;
            step = workflowSteps.SELECT_PALETTE_GEN_METHOD;
            break;
        }
        if (step) addStepToMinimapQueue(step, "human");
        updatePhase1UI();
      }

      function addSourceColorInput(index, label = "", disabled = false) {
        const row = createEl("div");
        row.className = "color-input-row";
        const id = `source-color-${index}`;
        const defaults = ["#6750A4", "#625B71", "#7D5260"];
        const safeLabel = sanitizeHtml(label);
        const labelHtml = label
          ? `<label for="${id}">${safeLabel}:</label>`
          : "";
        const inputHtml = `<input type="color" id="${id}" name="${id}" value="${
          defaults[index] || "#808080"
        }" ${disabled ? "disabled" : ""}>`;
        setHtml(row, `${labelHtml}${inputHtml}`);
        dom.sourceColorInputsContainer.appendChild(row);
        row
          .querySelector('input[type="color"]')
          .addEventListener("input", () => {
            addStepToMinimapQueue(workflowSteps.INPUT_COLOR, "human");
          });
      }
      function handleImageFile(file) {
        if (!file?.type.startsWith("image/")) {
          showError("Invalid file type. Please upload an image.");
          return;
        }
        state.currentImageFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
          dom.imagePreview.src = e.target.result;
          hideEl(dom.imagePreview, false);
          hideError();
          addStepToMinimapQueue(workflowSteps.INPUT_IMAGE, "human");
          updatePhase1UI();
        };
        reader.onerror = () => {
          showError("Failed to read image file.");
          hideEl(dom.imagePreview, true);
          dom.imagePreview.src = "#";
          state.currentImageFile = null;
        };
        reader.readAsDataURL(file);
      }
      async function fetchM3Content() {
        if (state.m3ContentCache) return state.m3ContentCache;
        try {
          const response = await fetch("m3.txt");
          if (!response.ok)
            throw new Error(`HTTP error! status: ${response.status}`);
          state.m3ContentCache = await response.text();
          return state.m3ContentCache;
        } catch (error) {
          console.error("Failed to fetch m3.txt:", error);
          showError(
            "Failed to load base component guidelines (m3.txt). Gemini generation might be less accurate."
          );
          return "";
        }
      }
      async function getGeminiContent(
        endpoint,
        systemPrompt = "",
        userPrompt,
        isJsonResponse = false,
        useM3Guidance = false,
        callingStep = workflowSteps.LLM_SUGGEST,
        imageBase64 = null
      ) {
        if (!config.isApiConfigValid)
          throw new Error("Gemini API is not configured in config.js");
        const fullApiUrl = `${endpoint}:generateContent?key=${config.API_KEY}`;
        let effectiveSystemPrompt = systemPrompt;
        if (useM3Guidance && systemPrompt.includes("Material Design 3")) {
          const m3Content = await fetchM3Content();
          if (m3Content)
            effectiveSystemPrompt += `\n\n# Material Design 3 Component Guidelines and Specifications\n\n${m3Content}`;
        }
        const parts = [];
        if (imageBase64)
          parts.push({
            inline_data: {
              mime_type: "image/jpeg",
              data: imageBase64.split(",")[1],
            },
          });
        if (effectiveSystemPrompt && !imageBase64)
          parts.push({ text: effectiveSystemPrompt });
        parts.push({ text: userPrompt });

        const requestBody = {
          contents: [{ role: "user", parts: parts }],
          generationConfig: {
            temperature: 0.6,
            maxOutputTokens: isJsonResponse ? 1024 : 4096,
          },
        };
        if (isJsonResponse)
          requestBody.generationConfig.responseMimeType = "application/json";
        if (effectiveSystemPrompt && imageBase64)
          requestBody.system_instruction = {
            parts: [{ text: effectiveSystemPrompt }],
          };

        try {
          addStepToMinimapQueue(callingStep, "gemini-bridge");
          const response = await fetch(fullApiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
          });
          if (!response.ok) {
            let errorBodyText = await response.text();
            let errorDetails = errorBodyText;
            try {
              errorDetails = JSON.parse(errorBodyText);
            } catch (e) {}
            console.error("Gemini API Error:", response.status, errorDetails);
            throw new Error(
              `API request failed: ${response.status} ${
                response.statusText
              }. Details: ${JSON.stringify(errorDetails)}`
            );
          }
          const data = await response.json();
          if (data.promptFeedback?.blockReason)
            throw new Error(
              `API request blocked: ${
                data.promptFeedback.blockReason
              }. Details: ${JSON.stringify(data.promptFeedback.safetyRatings)}`
            );
          const candidate = data.candidates?.[0];
          if (!candidate) throw new Error("API response missing candidates.");
          if (
            candidate.finishReason &&
            !["STOP", "MAX_TOKENS"].includes(candidate.finishReason)
          ) {
            const safetyInfo = candidate.safetyRatings
              ? `Safety: ${JSON.stringify(candidate.safetyRatings)}`
              : "";
            throw new Error(
              `Generation stopped unexpectedly: ${candidate.finishReason}. ${safetyInfo}`
            );
          }
          const contentText = candidate.content?.parts?.[0]?.text;
          if (typeof contentText !== "string")
            throw new Error("API response missing valid text content.");
          return contentText;
        } catch (error) {
          console.error("Error during Gemini API call:", error);
          addStepToMinimapQueue(workflowSteps.ERROR, "error");
          showError(`Gemini API call failed: ${error.message}`);
          throw error;
        }
      }

      const GEMINI_COLOR_SYSTEM_PROMPT_MULTI = `You are a helpful color palette assistant. Given a text description or an image, suggest exactly 3 DIFFERENT sets of 3 complementary hex color codes suitable for a Material Design 3 theme (Primary, Secondary, Tertiary). Respond ONLY with a valid JSON object containing a single key "suggestions". The value of "suggestions" must be an array containing exactly 3 sub-arrays. Each sub-array must contain exactly 3 valid 6-digit hex color strings (e.g., ["#RRGGBB", "#RRGGBB", "#RRGGBB"]). Example: {"suggestions": [["#6750A4", "#625B71", "#7D5260"], ["#00695C", "#4DB6AC", "#B2DFDB"], ["#B71C1C", "#EF9A9A", "#FFEBEE"]]}. Do not include any other text, explanations, apologies, or markdown formatting. Ensure the hex codes are valid and distinct sets are provided, reflecting the user's prompt or image content.`;
      const GEMINI_COLOR_SYSTEM_PROMPT_SINGLE = `You are a helpful color palette assistant. Given a text description or an image, suggest a SINGLE dominant or representative hex color code suitable as a source color for a Material Design 3 theme. Respond ONLY with a valid JSON object containing a single key "suggestion" whose value is a single valid 6-digit hex color string. Example: {"suggestion": "#6750A4"}. Do not include any other text, explanations, apologies, or markdown formatting.`;

      async function getGeminiSuggestions(
        promptOrImage,
        seedCount = "multi",
        isImage = false
      ) {
        addStepToMinimapQueue(
          isImage
            ? workflowSteps.MCP_WRAP_IMG_EXTRACT
            : workflowSteps.MCP_WRAP_SUGGEST,
          "mcp"
        );
        const systemPrompt =
          seedCount === "single"
            ? GEMINI_COLOR_SYSTEM_PROMPT_SINGLE
            : GEMINI_COLOR_SYSTEM_PROMPT_MULTI;
        const userPrompt = isImage
          ? "Extract color(s) based on the image."
          : promptOrImage;
        const imageBase64 = isImage ? promptOrImage : null;

        try {
          const jsonResponse = await getGeminiContent(
            config.geminiApiEndpointColorPicker,
            systemPrompt,
            userPrompt,
            true,
            false,
            isImage ? workflowSteps.LLM_SUGGEST : workflowSteps.LLM_SUGGEST,
            imageBase64
          );
          try {
            const parsed = JSON.parse(jsonResponse);
            if (seedCount === "single") {
              if (
                !parsed?.suggestion ||
                typeof parsed.suggestion !== "string" ||
                !/^#[0-9A-F]{6}$/i.test(parsed.suggestion)
              ) {
                throw new Error(
                  "Parsed JSON missing 'suggestion' string or invalid hex code."
                );
              }
              return {
                suggestions: [[parsed.suggestion, "#808080", "#A0A0A0"]],
              };
            } else {
              if (
                !parsed?.suggestions ||
                !Array.isArray(parsed.suggestions) ||
                parsed.suggestions.length === 0
              )
                throw new Error(
                  "Parsed JSON missing 'suggestions' array or is empty."
                );
              const validSuggestions = parsed.suggestions.filter(
                (s) =>
                  Array.isArray(s) &&
                  s.length === 3 &&
                  s.every(
                    (c) => typeof c === "string" && /^#[0-9A-F]{6}$/i.test(c)
                  )
              );
              if (validSuggestions.length === 0)
                throw new Error(
                  "No valid suggestions found. Check structure and hex codes."
                );
              return { suggestions: validSuggestions };
            }
          } catch (parseError) {
            console.error(
              "Failed to parse Gemini JSON response:",
              parseError,
              "\nReceived:",
              jsonResponse
            );
            throw new Error(
              `Model returned invalid JSON or structure: ${parseError.message}`
            );
          }
        } catch (apiError) {
          displaySuggestions([], isImage ? "image" : "text");
          throw apiError;
        }
      }
      async function simulateGeminiCall(promptText, seedCount = "multi") {
        addStepToMinimapQueue(workflowSteps.MCP_WRAP_SUGGEST, "mcp");
        await delay(600 + Math.random() * 400);
        const predefinedSets = [
          ["#6750A4", "#625B71", "#7D5260"],
          ["#00695C", "#4DB6AC", "#B2DFDB"],
          ["#B71C1C", "#EF9A9A", "#FFEBEE"],
          ["#0D47A1", "#90CAF9", "#E3F2FD"],
          ["#EF6C00", "#FFCA28", "#FFF9C4"],
          ["#4E342E", "#A1887F", "#D7CCC8"],
          ["#311B92", "#9575CD", "#EDE7F6"],
        ];
        let suggestions = [];
        if (seedCount === "single") {
          const randomIndex = Math.floor(Math.random() * predefinedSets.length);
          suggestions.push([
            predefinedSets[randomIndex][0],
            "#808080",
            "#A0A0A0",
          ]);
        } else {
          const availableIndices = [...Array(predefinedSets.length).keys()];
          while (suggestions.length < 3 && availableIndices.length > 0) {
            const randomIndex = Math.floor(
              Math.random() * availableIndices.length
            );
            const selectedIndex = availableIndices.splice(randomIndex, 1)[0];
            suggestions.push(predefinedSets[selectedIndex]);
          }
        }
        addStepToMinimapQueue(workflowSteps.LLM_SUGGEST, "tool");
        return { suggestions };
      }
      async function simulateGeminiImageCall(imageBase64, seedCount = "multi") {
        addStepToMinimapQueue(workflowSteps.MCP_WRAP_IMG_EXTRACT, "mcp");
        await delay(800 + Math.random() * 500);
        return simulateGeminiCall("Simulated image prompt", seedCount);
      }

      async function getGeminiBestSuggestion(suggestions, promptText) {
        addStepToMinimapQueue(workflowSteps.MCP_WRAP_SELECT, "mcp");
        const GEMINI_SELECT_SYSTEM_PROMPT = `You are a design critic. Given a user prompt/image description and a list of 3 color palettes (each palette has Primary, Secondary, Tertiary hex codes), choose the single BEST palette that matches the user's prompt/image. Respond ONLY with the index number (0, 1, or 2) of the best matching palette. Do not include any other text, explanations, or formatting. Example Response: 1`;
        const userQuery = `User Prompt/Image Context: "${promptText}"\n\nPalettes:\n0: ${JSON.stringify(
          suggestions[0]
        )}\n1: ${JSON.stringify(suggestions[1])}\n2: ${JSON.stringify(
          suggestions[2]
        )}\n\nWhich index (0, 1, or 2) is the best match? Respond with only the index number.`;
        try {
          const responseText = await getGeminiContent(
            config.geminiApiEndpointColorPicker,
            GEMINI_SELECT_SYSTEM_PROMPT,
            userQuery,
            false,
            false,
            workflowSteps.LLM_SELECT_BEST
          );
          try {
            const index = parseInt(responseText.trim(), 10);
            if (isNaN(index) || index < 0 || index >= suggestions.length)
              return suggestions[0];
            return suggestions[index];
          } catch (parseError) {
            console.error("Gemini Best Suggestion Parse Error:", parseError);
            return suggestions[0];
          }
        } catch (apiError) {
          return suggestions[0];
        }
      }
      async function simulateBestSuggestion(suggestions, promptText) {
        addStepToMinimapQueue(workflowSteps.MCP_WRAP_SELECT, "mcp");
        await delay(300 + Math.random() * 200);
        const randomIndex = Math.floor(Math.random() * suggestions.length);
        addStepToMinimapQueue(workflowSteps.LLM_SELECT_BEST, "tool");
        return suggestions[randomIndex];
      }

      function displaySuggestions(suggestionData, type = "text") {
        const container =
          type === "image" ? dom.imageSuggestionsList : dom.suggestionsList;
        const parentDiv =
          type === "image"
            ? dom.imagePromptSuggestions
            : dom.textPromptSuggestions;
        const label =
          type === "image"
            ? placeholders.suggestionsLabelImage
            : placeholders.suggestionsLabelText;
        setHtml(container, "");
        parentDiv.querySelector(".selection-group-label").innerHTML = label;

        if (!suggestionData?.suggestions?.length) {
          setHtml(container, placeholders.noSuggestions);
          hideEl(parentDiv, false);
          addStepToMinimapQueue(workflowSteps.DISPLAY_SUGGESTIONS, "result");
          return;
        }
        const seedCount =
          type === "text"
            ? getSelectedValue(dom.textSeedCountSelection)
            : getSelectedValue(dom.imageSeedCountSelection);
        const isSingleSeed = seedCount === "single";

        suggestionData.suggestions.forEach((colorSet, index) => {
          const displaySet = isSingleSeed ? [colorSet[0]] : colorSet;
          if (
            !Array.isArray(displaySet) ||
            displaySet.length === 0 ||
            !displaySet.every((c) => /^#[0-9A-F]{6}$/i.test(c))
          )
            return;

          const div = createEl("div");
          div.className = "suggestion-option";
          div.dataset.colors = JSON.stringify(colorSet);
          div.dataset.type = type;
          setAttr(div, "role", "button");
          div.tabIndex = 0;
          const swatchesHtml = displaySet
            .map(
              (hex) =>
                `<span class="suggestion-swatch" style="background-color: ${hex};" title="${hex}"></span>`
            )
            .join("");
          const radioId = `${type}_suggestion_${index}`;
          setHtml(
            div,
            ` <input type="radio" name="${type}_suggestion_radio" id="${radioId}" value='${JSON.stringify(
              colorSet
            )}' class="hidden"> <label for="${radioId}">${swatchesHtml}<span>${
              isSingleSeed ? "Color " : "Option "
            }${index + 1}</span></label>`
          );
          div.addEventListener("click", handleSuggestionSelection);
          div.addEventListener("keydown", (e) => {
            if (e.key === " " || e.key === "Enter") {
              handleSuggestionSelection.call(div, e);
              e.preventDefault();
            }
          });
          container.appendChild(div);
        });

        if (container.querySelectorAll(".suggestion-option").length > 0) {
          hideEl(parentDiv, false);
        } else {
          setHtml(container, placeholders.noValidSuggestions);
          hideEl(parentDiv, false);
        }
        addStepToMinimapQueue(workflowSteps.DISPLAY_SUGGESTIONS, "result");
      }

      function applySuggestionToUI(
        colors,
        type = "text",
        markAsSelected = true
      ) {
        if (!Array.isArray(colors) || colors.length === 0)
          throw new Error("Invalid color data provided to apply.");
        const seedCount =
          type === "text"
            ? getSelectedValue(dom.textSeedCountSelection)
            : type === "image"
            ? getSelectedValue(dom.imageSeedCountSelection)
            : "multi";
        const isSingle = seedCount === "single";
        const count = isSingle ? 1 : 3;

        let sourceInputs = dom.sourceColorInputsContainer.querySelectorAll(
          'input[type="color"]'
        );
        if (sourceInputs.length < count) {
          updateColorPickers(seedCount);
          sourceInputs = dom.sourceColorInputsContainer.querySelectorAll(
            'input[type="color"]'
          );
          if (sourceInputs.length < count)
            throw new Error(
              "Failed to create source color inputs for applying suggestion."
            );
        }

        for (let i = 0; i < count; i++) {
          if (sourceInputs[i] && colors[i]) {
            sourceInputs[i].value = colors[i];
            disableEl(sourceInputs[i], false);
            sourceInputs[i].dispatchEvent(
              new Event("input", { bubbles: true })
            );
          }
        }
        for (let i = count; i < sourceInputs.length; i++) {
          disableEl(sourceInputs[i], true);
          sourceInputs[i].closest(".color-input-row").style.opacity = "0.5";
        }

        if (markAsSelected) {
          const container =
            type === "image" ? dom.imageSuggestionsList : dom.suggestionsList;
          container
            .querySelectorAll(".suggestion-option.selected")
            .forEach((el) => el.classList.remove("selected"));
          const matchingSuggestionDiv = Array.from(
            container.querySelectorAll(".suggestion-option")
          ).find((div) => div.dataset.colors === JSON.stringify(colors));
          if (matchingSuggestionDiv) {
            matchingSuggestionDiv.classList.add("selected");
            const radio = matchingSuggestionDiv.querySelector(
              'input[type="radio"]'
            );
            if (radio) radio.checked = true;
          }
        }
        hideError();
      }

      function applyScopedThemeStyles(theme) {
        if (!theme?.schemes) return;
        const lightCSS = [],
          darkCSS = [];
        const previewSelectorBase = `#mwc-component-preview, #gemini-component-preview`;
        for (const [schemeKey, scheme] of Object.entries(theme.schemes)) {
          const isDark = schemeKey === "dark";
          const selector = isDark
            ? `${previewSelectorBase}.dark-theme`
            : `${previewSelectorBase}:not(.dark-theme)`;
          const targetCSS = isDark ? darkCSS : lightCSS;
          targetCSS.push(`${selector} {`);
          for (const [token, value] of Object.entries(scheme)) {
            if (typeof value === "number")
              targetCSS.push(
                `--local-sys-color-${kebabCase(token)}: ${argbIntToHex(value)};`
              );
          }
          targetCSS.push("}");
        }
        setText(
          dom.dynamicThemeStyles,
          `${lightCSS.join("\n")}\n${darkCSS.join("\n")}`
        );
      }
      function handleGenerateMwcComponents() {
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        if (!state.lastGeneratedTheme?.schemes) {
          showError("Please generate a theme first.");
          return;
        }
        addStepToMinimapQueue(workflowSteps.CLICK_GEN_MWC, "human");
        addStepToMinimapQueue(workflowSteps.TOOL_RENDER_MWC, "tool");
        applyScopedThemeStyles(state.lastGeneratedTheme);
        const mwcHTML = ` <div style="display:flex;flex-direction:column;gap:25px;"> <div> <h5>Buttons & FAB</h5> <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;"> <md-filled-button>Filled</md-filled-button> <md-outlined-button>Outlined</md-outlined-button> <md-fab aria-label="Edit"><md-icon slot="icon">edit</md-icon></md-fab> </div> </div> <div> <h5>Chips</h5> <md-chip-set style="display:flex;flex-wrap:wrap;gap:8px;"> <md-assist-chip label="Assist"></md-assist-chip> <md-filter-chip label="Filter" elevated></md-filter-chip> <md-suggestion-chip label="Suggest"></md-suggestion-chip> </md-chip-set> </div> <div> <h5>Slider</h5> <md-slider ticks value="65" style="width: 80%;"></md-slider> </div> <div> <h5>Card</h5> <md-card style="padding:16px;max-width:350px;"> <p style="margin:0; font-weight: 500;">The Music Dance Experience is officially CANCELED.</p> </md-card> </div> </div>`;
        setHtml(dom.mwcComponentPreview, `<h4>MWC Preview</h4> ${mwcHTML}`);
        toggleClass(dom.mwcComponentPreview, "dark-theme", state.isDarkMode);
        addStepToMinimapQueue(workflowSteps.DISPLAY_COMPONENTS, "result");
      }
      const GEMINI_COMPONENT_SYSTEM_PROMPT = `You are an expert web UI designer specializing in Material Design 3. You will be given: 1. A Material Design 3 color theme represented as CSS custom properties starting with '--local-sys-color-...'. Use these variables directly in your CSS. 2. An optional user style prompt. Your task is to: - Create an HTML structure containing ONLY the following components IN THIS ORDER: - Two buttons: one filled (<button class="gemini-filled-button">Filled</button>), one outlined (<button class="gemini-outlined-button">Outlined</button>). - One Floating Action Button (FAB) (<button class="gemini-fab"><span class="material-icons">edit</span></button>). Use standard HTML button and span. - Three chips (<span class="gemini-chip">Assist</span>, <span class="gemini-chip gemini-elevated">Filter</span>, <span class="gemini-chip">Suggest</span>). Use standard HTML spans. - One slider element (<input type="range" class="gemini-slider" value="65">). Use standard HTML range input. - One card (<div class="gemini-card"><p>The Music Dance Experience is officially CANCELED.</p></div>). Use standard HTML divs/paragraphs. - Apply styling using ONLY CSS classes defined within a SINGLE '<style>' tag. Define base styles first, then dark mode overrides using a '.dark-theme' prefix. - **CRITICAL:** Use the provided --local-sys-color-... CSS variables extensively and semantically for ALL colors (backgrounds, text, borders, icons, states like :hover). - Incorporate the user's style prompt subtly. If no prompt, use standard Material Design appearance. - Ensure output is visually coherent, uses appropriate padding/margins. - Respond ONLY with the final combined HTML structure (using specified tags/classes) and the single '<style>' tag. No explanations, markdown, <!DOCTYPE>, <html>, <body>.`;
      async function handleGenerateGeminiComponents() {
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        if (!state.lastGeneratedTheme) {
          showError("Generate a theme first.");
          return;
        }
        if (!config.isApiConfigValid) {
          showError("Gemini API is not configured.");
          return;
        }
        addStepToMinimapQueue(workflowSteps.CLICK_GEN_GEMINI, "human");
        addStepToMinimapQueue(workflowSteps.MCP_WRAP_GEN_COMP, "mcp");
        setGeminiComponentLoading(true);
        setHtml(dom.geminiComponentPreview, "");
        hideError();
        try {
          const stylePrompt = dom.componentStylePromptInput.value.trim();
          let themeVariablesString = ":root {\n";
          if (state.lastGeneratedTheme.schemes.light) {
            for (const [token, value] of Object.entries(
              state.lastGeneratedTheme.schemes.light
            )) {
              if (typeof value === "number")
                themeVariablesString += ` --local-sys-color-${kebabCase(
                  token
                )}: ${argbIntToHex(value)};\n`;
            }
            themeVariablesString += "}";
          }
          const fullPrompt = `MATERIAL DESIGN 3 THEME VARIABLES (Use these in CSS):\n\`\`\`css\n${themeVariablesString}\n\`\`\`\n\nUSER STYLE PROMPT: ${
            stylePrompt || "Default clean Material Design style."
          }\n\nGenerate HTML/CSS using EXACT tags/classes specified. Use --local-sys-color-... variables.`;
          const useM3Guidance = dom.useM3GuidanceCheckbox.checked;
          const generatedHtmlAndCss = await getGeminiContent(
            config.geminiApiEndpointComponentGenerator,
            GEMINI_COMPONENT_SYSTEM_PROMPT,
            fullPrompt,
            false,
            useM3Guidance,
            workflowSteps.LLM_GEN_COMP
          );
          const cleanedHtmlCss = generatedHtmlAndCss
            .replace(/^\s*```(?:html|css|markup|)\s*\n?/im, "")
            .replace(/\n?\s*```\s*$/im, "")
            .trim();
          setHtml(
            dom.geminiComponentPreview,
            `<h4>Gemini Preview</h4> ${cleanedHtmlCss}`
          );
          toggleClass(
            dom.geminiComponentPreview,
            "dark-theme",
            state.isDarkMode
          );
          applyScopedThemeStyles(state.lastGeneratedTheme);
          addStepToMinimapQueue(workflowSteps.DISPLAY_COMPONENTS, "result");
        } catch (error) {
          showError(`Gemini component generation failed: ${error.message}`);
          setHtml(dom.geminiComponentPreview, placeholders.geminiPreviewError);
        } finally {
          setGeminiComponentLoading(false);
        }
      }
      function handleSuggestionSelection(event) {
        if (audio.context && audio.context.state === "suspended")
          audio.context.resume();
        const selectedDiv = event.currentTarget;
        event.preventDefault();
        const colorsJson = selectedDiv.dataset.colors;
        const type = selectedDiv.dataset.type || "text";
        if (!colorsJson) return;
        try {
          const colors = JSON.parse(colorsJson);
          state.selectedSuggestion[type] = colors;
          applySuggestionToUI(colors, type, false);
          const container =
            type === "image" ? dom.imageSuggestionsList : dom.suggestionsList;
          container
            .querySelectorAll(".suggestion-option.selected")
            .forEach((el) => el.classList.remove("selected"));
          selectedDiv.classList.add("selected");
          const radio = selectedDiv.querySelector('input[type="radio"]');
          if (radio) radio.checked = true;
          addStepToMinimapQueue(workflowSteps.SELECT_SUGGESTION, "human");
        } catch (error) {
          showError(`Failed to apply suggestion: ${error.message}`);
        }
      }
      async function generateThemeInternal(seeds, options) {
        if (!seeds || seeds.length === 0)
          throw new Error(
            "No valid seed colors provided for theme generation."
          );
        addStepToMinimapQueue(workflowSteps.TOOL_COLOR_MATH, "tool");
        let theme;
        if (seeds.length === 1) {
          theme = themeFromSourceColor(seeds[0]);
        } else {
          theme = themeFromSourceColors(seeds, options);
        }
        return { theme, seeds };
      }

      async function handleProcessTextClick() {
        const promptText = dom.textPromptInput.value.trim();
        if (!promptText) {
          showError("Please enter a theme description first.");
          return;
        }
        addStepToMinimapQueue(workflowSteps.CLICK_PROCESS_TEXT, "human");
        hideError();
        setSuggestionLoading(true, "text");
        hideEl(dom.textPromptSuggestions, true);
        setHtml(dom.suggestionsList, "");
        state.lastSuggestions.text = null;
        state.selectedSuggestion.text = null;

        try {
          const useSim = dom.useSimulationCheckbox.checked;
          const useApi = !useSim && config.isApiConfigValid;
          const seedCount = getSelectedValue(dom.textSeedCountSelection);
          let data;
          if (useApi) {
            data = await getGeminiSuggestions(promptText, seedCount, false);
          } else if (!config.isApiConfigValid && !useSim) {
            showError(
              "Gemini API not configured. Check simulation box or configure API."
            );
            setHtml(dom.suggestionsList, placeholders.suggestionsApiError);
            hideEl(dom.textPromptSuggestions, false);
            addStepToMinimapQueue(workflowSteps.ERROR, "error");
            return;
          } else {
            data = await simulateGeminiCall(promptText, seedCount);
          }
          state.lastSuggestions.text = data.suggestions;
          displaySuggestions(data, "text");
        } catch (error) {
          showError(`Failed to get text suggestions: ${error.message}`);
          setHtml(dom.suggestionsList, placeholders.suggestionsLoadError);
          hideEl(dom.textPromptSuggestions, false);
        } finally {
          setSuggestionLoading(false, "text");
        }
      }

      async function handleProcessImageGeminiClick() {
        if (!state.currentImageFile) {
          showError("Please upload an image first.");
          return;
        }
        addStepToMinimapQueue(workflowSteps.CLICK_PROCESS_IMAGE, "human");
        hideError();
        setSuggestionLoading(true, "image");
        hideEl(dom.imagePromptSuggestions, true);
        setHtml(dom.imageSuggestionsList, "");
        state.lastSuggestions.image = null;
        state.selectedSuggestion.image = null;

        try {
          const useSim = dom.useSimulationCheckbox.checked;
          const useApi = !useSim && config.isApiConfigValid;
          const seedCount = getSelectedValue(dom.imageSeedCountSelection);
          const imageBase64 = dom.imagePreview.src;
          let data;

          if (useApi) {
            data = await getGeminiSuggestions(imageBase64, seedCount, true);
          } else if (!config.isApiConfigValid && !useSim) {
            showError(
              "Gemini API not configured. Check simulation box or configure API."
            );
            setHtml(dom.imageSuggestionsList, placeholders.suggestionsApiError);
            hideEl(dom.imagePromptSuggestions, false);
            addStepToMinimapQueue(workflowSteps.ERROR, "error");
            return;
          } else {
            data = await simulateGeminiImageCall(imageBase64, seedCount);
          }
          state.lastSuggestions.image = data.suggestions;
          displaySuggestions(data, "image");
        } catch (error) {
          showError(`Failed to get image suggestions: ${error.message}`);
          setHtml(dom.imageSuggestionsList, placeholders.suggestionsLoadError);
          hideEl(dom.imagePromptSuggestions, false);
        } finally {
          setSuggestionLoading(false, "image");
        }
      }

      async function performAutoSelection(
        suggestions,
        contextPrompt,
        useApi,
        type
      ) {
        const wrapStep =
          type === "image"
            ? workflowSteps.MCP_WRAP_IMG_EXTRACT
            : workflowSteps.MCP_WRAP_SUGGEST;
        const selectStep = workflowSteps.MCP_WRAP_SELECT;
        addStepToMinimapQueue(wrapStep, "mcp");
        addStepToMinimapQueue(selectStep, "mcp");
        let bestSuggestion;
        if (useApi) {
          bestSuggestion = await getGeminiBestSuggestion(
            suggestions,
            contextPrompt
          );
        } else {
          bestSuggestion = await simulateBestSuggestion(
            suggestions,
            contextPrompt
          );
        }
        addStepToMinimapQueue(workflowSteps.APPLY_LLM_SELECTION, "decision");
        return bestSuggestion;
      }

      async function handleGenerateClick() {
        addStepToMinimapQueue(workflowSteps.CLICK_GENERATE, "human");
        const source = state.currentInputSource;
        let seeds = [];
        let themeOptions = {};
        let autoInvokedTool = false;
        const useSim = dom.useSimulationCheckbox.checked;
        const useApi = !useSim && config.isApiConfigValid;
        const generationMethod = getSelectedValue(
          dom.paletteGenerationMethodSelection
        );
        state.generationMethod = generationMethod;

        setUILoading(true, source);
        setHtml(dom.paletteDisplay, placeholders.generating);
        setHtml(dom.seedColorsDisplayContainer, "");
        hideError();

        const materialLibExists =
          typeof themeFromSourceColor === "function" &&
          typeof themeFromSourceColors === "function" &&
          (!config.ENABLE_IMAGES ||
            (typeof sourceColorFromImage === "function" &&
              typeof sourceColorsFromImage === "function"));
        if (
          !materialLibExists &&
          (generationMethod === "material" ||
            generationMethod === "gemini_mcp" ||
            generationMethod === "manual_mcp")
        ) {
          showError(
            "Core color generation library (material_color_utils.js) not found for selected method."
          );
          setUILoading(false);
          return;
        }

        try {
          addStepToMinimapQueue(workflowSteps.MCP_WRAP_GENERATE, "mcp");
          let contextPrompt = "";

          if (source === "text") {
            contextPrompt = dom.textPromptInput.value.trim();
            const selectionMethod = getSelectedValue(
              dom.textSelectionMethodSelection
            );
            const seedCount = getSelectedValue(dom.textSeedCountSelection);
            if (
              selectionMethod === "gemini" ||
              selectionMethod === "gemini_mcp"
            ) {
              if (!state.lastSuggestions.text)
                throw new Error(
                  "Please process the text prompt first to get suggestions for auto-selection."
                );
              if (!contextPrompt)
                throw new Error(
                  "Please enter a theme description for auto-selection."
                );
              const bestSuggestion = await performAutoSelection(
                state.lastSuggestions.text,
                contextPrompt,
                useApi,
                "text"
              );
              state.selectedSuggestion.text = bestSuggestion;
              applySuggestionToUI(bestSuggestion, "text", true);
              seeds = bestSuggestion.map((hex, i) =>
                validateAndConvertHex(hex, `LLM Text Color ${i + 1}`)
              );
              if (
                selectionMethod === "gemini_mcp" &&
                (generationMethod === "gemini_mcp" ||
                  generationMethod === "manual_mcp")
              )
                autoInvokedTool = true;
            } else {
              if (!state.selectedSuggestion.text)
                throw new Error("Please select a suggested color set first.");
              seeds = state.selectedSuggestion.text.map((hex, i) =>
                validateAndConvertHex(hex, `Selected Text Color ${i + 1}`)
              );
            }
            themeOptions = {};
          } else if (source === "color") {
            const seedCount = getSelectedValue(dom.colorSeedCountSelection);
            const isMulti = seedCount === "multi";
            const count = isMulti ? 3 : 1;
            const inputs = Array.from(
              dom.sourceColorInputsContainer.querySelectorAll(
                'input[type="color"]'
              )
            ).slice(0, count);
            if (inputs.length < count)
              throw new Error(
                `Expected ${count} color picker(s), found ${inputs.length}.`
              );
            seeds = inputs
              .map((input, idx) => {
                if (input.disabled) return null;
                const label =
                  input.previousElementSibling?.textContent ||
                  `Color ${idx + 1}`;
                return validateAndConvertHex(input.value, label);
              })
              .filter((v) => typeof v === "number");
            if (seeds.length === 0)
              throw new Error("Please provide valid source color(s).");
            if (isMulti)
              themeOptions.harmonyStrategy = dom.harmonyStrategySelect.value;
            contextPrompt = `User selected color(s): ${seeds
              .map(argbIntToHex)
              .join(", ")}`;
          } else if (source === "image") {
            if (
              !state.currentImageFile ||
              !dom.imagePreview.src ||
              dom.imagePreview.src.startsWith("#")
            )
              throw new Error("Please upload an image first.");
            contextPrompt = "Image Analysis Context";
            const extractionMethod = getSelectedValue(
              dom.imageExtractionMethodSelection
            );
            const seedCount = getSelectedValue(dom.imageSeedCountSelection);
            if (extractionMethod === "gemini") {
              const selectionMethod = getSelectedValue(
                dom.imageSelectionMethodSelection
              );
              if (
                selectionMethod === "gemini" ||
                selectionMethod === "gemini_mcp"
              ) {
                if (!state.lastSuggestions.image)
                  throw new Error(
                    "Please process the image with Gemini first to get suggestions."
                  );
                const bestSuggestion = await performAutoSelection(
                  state.lastSuggestions.image,
                  contextPrompt,
                  useApi,
                  "image"
                );
                state.selectedSuggestion.image = bestSuggestion;
                applySuggestionToUI(bestSuggestion, "image", true);
                seeds = bestSuggestion.map((hex, i) =>
                  validateAndConvertHex(hex, `LLM Image Color ${i + 1}`)
                );
                if (
                  selectionMethod === "gemini_mcp" &&
                  (generationMethod === "gemini_mcp" ||
                    generationMethod === "manual_mcp")
                )
                  autoInvokedTool = true;
              } else {
                if (!state.selectedSuggestion.image)
                  throw new Error(
                    "Please select a suggested color set from the image first."
                  );
                seeds = state.selectedSuggestion.image.map((hex, i) =>
                  validateAndConvertHex(hex, `Selected Image Color ${i + 1}`)
                );
              }
              themeOptions = {};
            } else {
              addStepToMinimapQueue(
                workflowSteps.TOOL_IMAGE_PROC_MATERIAL,
                "tool"
              );
              const img = await loadImageFromSrc(dom.imagePreview.src);
              if (seedCount === "single") {
                const srcColor = await sourceColorFromImage(img);
                if (typeof srcColor !== "number")
                  throw new Error(
                    "Failed to extract dominant color from image using Material Color Utils."
                  );
                seeds = [srcColor];
              } else {
                const num = parseInt(dom.numSourcesInput.value, 10) || 3;
                const qual = parseInt(dom.extractQualityInput.value, 10) || 10;
                seeds = await sourceColorsFromImage(img, num, qual);
                if (!seeds?.length)
                  throw new Error(
                    "Failed to extract multiple colors from image using Material Color Utils."
                  );
                themeOptions.harmonyStrategy = "direct";
              }
            }
          } else {
            throw new Error(
              "Invalid or unsupported generation source selected."
            );
          }

          const finalSeeds = seeds.filter((s) => typeof s === "number");
          if (finalSeeds.length === 0) {
            throw new Error(
              "No valid seed colors could be determined for generation."
            );
          }

          let themeResult;
          if (generationMethod === "material") {
            themeResult = await generateThemeInternal(finalSeeds, themeOptions);
          } else if (
            generationMethod === "gemini_mcp" ||
            (autoInvokedTool && generationMethod === "manual_mcp")
          ) {
            addStepToMinimapQueue(workflowSteps.MCP_INVOKE_TOOL, "mcp");
            if (generationMethod === "manual_mcp") {
              themeResult = await simulateMaterialTheme(
                finalSeeds,
                themeOptions
              );
            } else {
              themeResult = await generateThemeInternal(
                finalSeeds,
                themeOptions
              );
            }
          } else if (generationMethod === "manual_mcp") {
            addStepToMinimapQueue(workflowSteps.MCP_INVOKE_TOOL, "mcp");
            themeResult = await simulateMaterialTheme(finalSeeds, themeOptions);
          } else if (generationMethod === "gemini_only") {
            addStepToMinimapQueue(workflowSteps.LLM_GEN_PALETTE, "llm");
            themeResult = await generateGeminiPalette(
              finalSeeds,
              contextPrompt || "Color palette",
              useApi
            );
          } else {
            throw new Error(`Unknown generation method: ${generationMethod}`);
          }

          if (themeResult && themeResult.theme) {
            state.lastGeneratedTheme = themeResult.theme;
            displaySeedColors(finalSeeds, themeResult.seeds || finalSeeds);
            displayTheme(themeResult.theme);
            updatePhaseCardStyle(dom.phase2Card, generationMethod);
          } else {
            showError("Theme generation failed. No theme object was returned.");
          }
        } catch (error) {
          showError(`Generation Error: ${error.message}`);
          setHtml(dom.paletteDisplay, placeholders.paletteError);
        } finally {
          setUILoading(false);
          toggleBackButton(true);
        }
      }

      function updatePhaseCardStyle(cardElement, method) {
        cardElement.classList.remove(
          "phase-local-tool",
          "phase-mcp-tool",
          "phase-llm-decision"
        );
        if (method === "material") cardElement.classList.add("phase-local-tool");
        else if (method === "gemini_mcp" || method === "manual_mcp")
          cardElement.classList.add("phase-mcp-tool");
        else if (method === "gemini_only")
          cardElement.classList.add("phase-llm-decision");
      }

      async function simulateMaterialTheme(seeds, options) {
        addStepToMinimapQueue(workflowSteps.TOOL_COLOR_MATH, "tool");
        await delay(500 + Math.random() * 300);
        if (Math.random() < 0.2)
          throw new Error("Simulated Material Color Utils tool failure.");
        return generateThemeInternal(seeds, options);
      }

      async function generateGeminiPalette(seeds, contextPrompt, useApi) {
        if (!useApi) {
          await delay(400 + Math.random() * 200);
          if (
            typeof themeFromSourceColor === "function" &&
            typeof themeFromSourceColors === "function"
          ) {
            showError(
              "Gemini API not available, falling back to Material Color Utils simulation for palette generation."
            );
            return simulateMaterialTheme(seeds, {});
          } else {
            throw new Error(
              "Gemini API not available and Material Color Utils fallback also failed."
            );
          }
        }
        const seedHexes = seeds.map(argbIntToHex);
        const userQuery = `Generate a Material Design 3 color palette in JSON format based on these seed colors: ${JSON.stringify(
          seedHexes
        )}. Context: ${contextPrompt}. Include light and dark schemes, and palettes for primary, secondary, tertiary, neutral, neutral variant, and error. Ensure the output ONLY contains the valid JSON object with 'palettes' and 'schemes' keys, following the structure used by material-color-utilities.`;
        try {
          const jsonResponse = await getGeminiContent(
            config.geminiApiEndpointComponentGenerator,
            `You are a Material Design 3 color palette generator. Output ONLY valid JSON matching the material-color-utilities theme structure.`,
            userQuery,
            true,
            false,
            workflowSteps.LLM_GEN_PALETTE
          );
          const parsed = JSON.parse(jsonResponse);

          if (
            !parsed ||
            typeof parsed !== "object" ||
            !parsed.schemes ||
            typeof parsed.schemes !== "object" ||
            !parsed.palettes ||
            typeof parsed.palettes !== "object"
          ) {
            throw new Error(
              "Invalid palette JSON response structure from Gemini."
            );
          }
          if (
            !parsed.schemes.light ||
            !parsed.schemes.dark ||
            !parsed.palettes.primary ||
            !parsed.palettes.secondary ||
            !parsed.palettes.tertiary ||
            !parsed.palettes.neutral ||
            !parsed.palettes.neutralVariant ||
            !parsed.palettes.error
          ) {
            console.warn(
              "Gemini palette response missing some standard keys, using what's available.",
              parsed
            );
          }
          const convertScheme = (scheme) =>
            Object.fromEntries(
              Object.entries(scheme).map(([key, value]) => [
                key,
                typeof value === "string" && value.startsWith("#")
                  ? hexToArgbInt(value)
                  : value,
              ])
            );
          const convertPalette = (palette) =>
            Object.fromEntries(
              Object.entries(palette).map(([key, value]) => [
                key,
                typeof value === "string" && value.startsWith("#")
                  ? hexToArgbInt(value)
                  : value,
              ])
            );

          const themeWithInts = {
            source: seeds[0],
            schemes: {
              light: parsed.schemes.light
                ? convertScheme(parsed.schemes.light)
                : {},
              dark: parsed.schemes.dark
                ? convertScheme(parsed.schemes.dark)
                : {},
            },
            palettes: {
              primary: parsed.palettes.primary
                ? convertPalette(parsed.palettes.primary)
                : {},
              secondary: parsed.palettes.secondary
                ? convertPalette(parsed.palettes.secondary)
                : {},
              tertiary: parsed.palettes.tertiary
                ? convertPalette(parsed.palettes.tertiary)
                : {},
              neutral: parsed.palettes.neutral
                ? convertPalette(parsed.palettes.neutral)
                : {},
              neutralVariant: parsed.palettes.neutralVariant
                ? convertPalette(parsed.palettes.neutralVariant)
                : {},
              error: parsed.palettes.error
                ? convertPalette(parsed.palettes.error)
                : {},
            },
            customColors: parsed.customColors || [],
          };

          return { theme: themeWithInts, seeds };
        } catch (apiError) {
          showError(
            `Gemini Palette API Error: ${apiError.message}. Falling back to Material Color Utils simulation.`
          );
          return simulateMaterialTheme(seeds, {});
        }
      }

      function showApiKeyPopup() {
        if (dom.apiKeyModal) {
          dom.apiKeyModal.style.display = "flex";
          if (dom.apiKeyInput) {
            dom.apiKeyInput.value = "";
            dom.apiKeyInput.focus();
          }
          if (dom.apiKeyError) {
            dom.apiKeyError.textContent = "";
          }
        }
      }

      function hideApiKeyPopup() {
        if (dom.apiKeyModal) {
          dom.apiKeyModal.style.display = "none";
        }
      }

      function handleSaveApiKey() {
        const enteredKey = dom.apiKeyInput?.value?.trim();

        if (!enteredKey) {
          if (dom.apiKeyError) {
            dom.apiKeyError.textContent = "Please enter an API key.";
          }
          return;
        }

        // Basic validation - just check if it looks like an API key
        if (enteredKey.length < 20) {
          if (dom.apiKeyError) {
            dom.apiKeyError.textContent = "API key appears to be too short.";
          }
          return;
        }

        // Save the key to session
        sessionApiKey = enteredKey;
        config.API_KEY = enteredKey;

        // Update config with the new key
        const modelIdBase = config.GEMINI_MODEL ?
          (config.GEMINI_MODEL.startsWith("models/") ? config.GEMINI_MODEL : `models/${config.GEMINI_MODEL}`) :
          "models/gemini-1.5-flash";

        const apiPrefix = "https://generativelanguage.googleapis.com/v1beta/";
        config.geminiApiEndpointBase = `${apiPrefix}${modelIdBase}`;
        config.geminiApiEndpointColorPicker = `${apiPrefix}${modelIdBase}`;
        config.geminiApiEndpointComponentGenerator = `${apiPrefix}${modelIdBase}`;
        config.isApiConfigValid = true;

        console.log("API Key saved for this session.");
        hideApiKeyPopup();

        // Update UI to reflect API is now available
        applyFeatureVisibility();
        hideError();

        // Resolve the promise if one is waiting
        if (apiKeyPromiseResolver) {
          apiKeyPromiseResolver.resolve(sessionApiKey);
          apiKeyPromiseResolver = null;
        }
      }

      function handleCancelApiKey() {
        console.log("API Key entry cancelled. Using simulation mode.");
        hideApiKeyPopup();
        config.isApiConfigValid = false; // Explicitly mark as invalid
        config.API_KEY = null; // Clear any potentially partially entered key
        sessionApiKey = null;

        // Ensure simulation checkbox is checked and UI reflects simulation mode
        if (dom.useSimulationCheckbox) {
          dom.useSimulationCheckbox.checked = true;
          disableEl(dom.useSimulationCheckbox, false);
        }
        applyFeatureVisibility();
        showError("API Key not provided. Simulation mode enabled.");

        if (apiKeyPromiseResolver) {
          apiKeyPromiseResolver.reject(
            new Error("API key entry cancelled by user.")
          );
          apiKeyPromiseResolver = null;
        }
      }

      function getApiKey() {
        return new Promise((resolve, reject) => {
          if (sessionApiKey && config.isApiConfigValid) {
            resolve(sessionApiKey);
          } else {
            console.log("API Key not found or invalid, prompting user.");
            apiKeyPromiseResolver = { resolve, reject };
            showApiKeyPopup();
          }
        });
      }

      function handleBackButtonClick() {
        if (state.history.length <= 1) {
          resetMinimapToBase();
          state.history = [];
          toggleBackButton(false);
          return;
        }
        state.history.pop();
        const prevState = state.history[state.history.length - 1];
        if (!prevState) {
          resetMinimapToBase();
          state.history = [];
          toggleBackButton(false);
          return;
        }
        restoreFullState(prevState);
        addStepToMinimapQueue(workflowSteps.GO_BACK, "decision");
        if (state.history.length <= 1) toggleBackButton(false);
      }

      function toggleBackButton(show) {
        hideEl(dom.backButtonArea, !show);
      }

      function saveFullState() {
        const currentState = {
          ...state,
          currentMinimapSteps: [...state.currentMinimapSteps],
          selectedSuggestion: { ...state.selectedSuggestion },
          lastSuggestions: { ...state.lastSuggestions },
          history: undefined,

          inputSourceValue: getSelectedValue(dom.inputSourceSelection),
          textPromptInputValue: dom.textPromptInput.value,
          textSeedCountValue: getSelectedValue(dom.textSeedCountSelection),
          textSelectionMethodValue: getSelectedValue(
            dom.textSelectionMethodSelection
          ),
          colorSeedCountValue: getSelectedValue(dom.colorSeedCountSelection),
          harmonyStrategyValue: dom.harmonyStrategySelect.value,
          imageExtractionMethodValue: getSelectedValue(
            dom.imageExtractionMethodSelection
          ),
          imageSeedCountValue: getSelectedValue(dom.imageSeedCountSelection),
          imageSelectionMethodValue: getSelectedValue(
            dom.imageSelectionMethodSelection
          ),
          numSourcesInputValue: dom.numSourcesInput.value,
          extractQualityInputValue: dom.extractQualityInput.value,
          paletteGenerationMethodValue: getSelectedValue(
            dom.paletteGenerationMethodSelection
          ),
          useSimulationChecked: dom.useSimulationCheckbox.checked,
          componentStylePromptValue: dom.componentStylePromptInput.value,
          useM3GuidanceChecked: dom.useM3GuidanceCheckbox.checked,

          suggestionsListHTML: dom.suggestionsList.innerHTML,
          imageSuggestionsListHTML: dom.imageSuggestionsList.innerHTML,
          sourceColorInputsHTML: dom.sourceColorInputsContainer.innerHTML,
          seedColorsDisplayHTML: dom.seedColorsDisplayContainer.innerHTML,
          paletteDisplayHTML: dom.paletteDisplay.innerHTML,
          mwcComponentPreviewHTML: dom.mwcComponentPreview.innerHTML,
          geminiComponentPreviewHTML: dom.geminiComponentPreview.innerHTML,

          textOptionsGroupHidden:
            dom.textOptionsGroup.classList.contains("hidden"),
          colorOptionsGroupHidden:
            dom.colorOptionsGroup.classList.contains("hidden"),
          imageOptionsGroupHidden:
            dom.imageOptionsGroup.classList.contains("hidden"),
          textPromptSuggestionsHidden:
            dom.textPromptSuggestions.classList.contains("hidden"),
          imagePromptSuggestionsHidden:
            dom.imagePromptSuggestions.classList.contains("hidden"),
          imagePreviewHidden: dom.imagePreview.classList.contains("hidden"),
          componentExamplesHidden:
            dom.componentExamplesDiv.classList.contains("hidden"),
          errorMessageHidden: dom.errorMessageDiv.classList.contains("hidden"),
          errorMessageText: dom.errorMessageDiv.textContent,
        };
        state.history.push(currentState);
      }

      function restoreFullState(prevState) {
        state.currentImageFile = prevState.currentImageFile;
        state.currentInputSource = prevState.currentInputSource;
        state.lastGeneratedTheme = prevState.lastGeneratedTheme;
        state.isDarkMode = prevState.isDarkMode;
        state.m3ContentCache = prevState.m3ContentCache;
        state.currentMinimapSteps = [...prevState.currentMinimapSteps];
        state.selectedSuggestion = { ...prevState.selectedSuggestion };
        state.lastSuggestions = { ...prevState.lastSuggestions };
        state.generationMethod = prevState.generationMethod;
        state.currentPhaseCardId = prevState.currentPhaseCardId;

        setSelectedChip(dom.inputSourceSelection, prevState.inputSourceValue);
        dom.textPromptInput.value = prevState.textPromptInputValue;
        setSelectedChip(
          dom.textSeedCountSelection,
          prevState.textSeedCountValue
        );
        setSelectedChip(
          dom.textSelectionMethodSelection,
          prevState.textSelectionMethodValue
        );
        setSelectedChip(
          dom.colorSeedCountSelection,
          prevState.colorSeedCountValue
        );
        dom.harmonyStrategySelect.value = prevState.harmonyStrategyValue;
        setSelectedChip(
          dom.imageExtractionMethodSelection,
          prevState.imageExtractionMethodValue
        );
        setSelectedChip(
          dom.imageSeedCountSelection,
          prevState.imageSeedCountValue
        );
        setSelectedChip(
          dom.imageSelectionMethodSelection,
          prevState.imageSelectionMethodValue
        );
        dom.numSourcesInput.value = prevState.numSourcesInputValue;
        dom.extractQualityInput.value = prevState.extractQualityInputValue;
        setSelectedChip(
          dom.paletteGenerationMethodSelection,
          prevState.paletteGenerationMethodValue
        );
        dom.useSimulationCheckbox.checked = prevState.useSimulationChecked;
        dom.componentStylePromptInput.value =
          prevState.componentStylePromptValue;
        dom.useM3GuidanceCheckbox.checked = prevState.useM3GuidanceChecked;

        // Restore HTML Content
        setHtml(dom.suggestionsList, prevState.suggestionsListHTML);
        setHtml(dom.imageSuggestionsList, prevState.imageSuggestionsListHTML);
        setHtml(
          dom.sourceColorInputsContainer,
          prevState.sourceColorInputsHTML
        );
        setHtml(
          dom.seedColorsDisplayContainer,
          prevState.seedColorsDisplayHTML
        );
        setHtml(dom.paletteDisplay, prevState.paletteDisplayHTML);
        setHtml(dom.mwcComponentPreview, prevState.mwcComponentPreviewHTML);
        setHtml(
          dom.geminiComponentPreview,
          prevState.geminiComponentPreviewHTML
        );

        hideEl(dom.textOptionsGroup, prevState.textOptionsGroupHidden);
        hideEl(dom.colorOptionsGroup, prevState.colorOptionsGroupHidden);
        hideEl(dom.imageOptionsGroup, prevState.imageOptionsGroupHidden);
        hideEl(
          dom.textPromptSuggestions,
          prevState.textPromptSuggestionsHidden
        );
        hideEl(
          dom.imagePromptSuggestions,
          prevState.imagePromptSuggestionsHidden
        );
        hideEl(dom.imagePreview, prevState.imagePreviewHidden);
        hideEl(dom.componentExamplesDiv, prevState.componentExamplesHidden);
        hideEl(dom.errorMessageDiv, prevState.errorMessageHidden);
        setText(dom.errorMessageDiv, prevState.errorMessageText);

        if (state.lastGeneratedTheme)
          applyScopedThemeStyles(state.lastGeneratedTheme);
        renderMinimap();
        attachSuggestionListeners(dom.suggestionsList);
        attachSuggestionListeners(dom.imageSuggestionsList);
        if (state.currentPhaseCardId) {
          const card = getEl(state.currentPhaseCardId);
          if (card) updatePhaseCardStyle(card, state.generationMethod);
        }
        updatePhase1UI();
      }

      function setSelectedChip(chipGroup, value) {
        if (!chipGroup || !value) return;
        chipGroup.querySelectorAll('input[type="radio"]').forEach((radio) => {
          radio.checked = radio.value === value;
        });
      }

      function attachSuggestionListeners(container) {
        container?.querySelectorAll(".suggestion-option").forEach((div) => {
          div.removeEventListener("click", handleSuggestionSelection);
          div.removeEventListener("keydown", handleSuggestionKeydown);
          div.addEventListener("click", handleSuggestionSelection);
          div.addEventListener("keydown", handleSuggestionKeydown);
        });
      }

      function handleSuggestionKeydown(e) {
        if (e.key === " " || e.key === "Enter") {
          handleSuggestionSelection.call(this, e);
          e.preventDefault();
        }
      }

      function setupEventListeners() {
        dom.inputSourceSelection.addEventListener(
          "change",
          handleInputSourceChange
        );

        $$(".chip-selection-group").forEach((group) => {
          group.addEventListener("change", handleOptionChange);
        });

        dom.dropArea.addEventListener("click", () => dom.imageInput.click());
        dom.dropArea.addEventListener("dragover", (e) => {
          e.preventDefault();
          dom.dropArea.classList.add("drag-over");
        });
        dom.dropArea.addEventListener("dragleave", () =>
          dom.dropArea.classList.remove("drag-over")
        );
        dom.dropArea.addEventListener("drop", (e) => {
          e.preventDefault();
          dom.dropArea.classList.remove("drag-over");
          if (e.dataTransfer.files.length)
            handleImageFile(e.dataTransfer.files[0]);
        });
        dom.imageInput.addEventListener("change", (e) => {
          if (e.target.files.length) handleImageFile(e.target.files[0]);
        });

        dom.processTextButton.addEventListener("click", () => {
          saveFullState();
          handleProcessTextClick();
        });
        dom.processImageGeminiButton.addEventListener("click", () => {
          saveFullState();
          handleProcessImageGeminiClick();
        });
        dom.generateButton.addEventListener("click", () => {
          saveFullState();
          handleGenerateClick();
        });
        dom.generateMwcComponentsButton.addEventListener(
          "click",
          handleGenerateMwcComponents
        );
        dom.generateGeminiComponentsButton.addEventListener(
          "click",
          handleGenerateGeminiComponents
        );

        dom.themeToggleButton.addEventListener("click", handleThemeToggle);

        dom.backButton.addEventListener("click", handleBackButtonClick);

        if (dom.saveApiKeyBtn) {
          dom.saveApiKeyBtn.addEventListener("click", handleSaveApiKey);
        } else {
          console.warn("Save API Key button not found");
        }
        if (dom.cancelApiKeyBtn) {
          dom.cancelApiKeyBtn.addEventListener("click", handleCancelApiKey);
        } else {
          console.warn("Cancel API Key button not found");
        }

        if (dom.apiKeyInput) {
          dom.apiKeyInput.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              handleSaveApiKey();
            }
          });
        }

        if (dom.apiKeyModal) {
          dom.apiKeyModal.addEventListener("click", (event) => {
            if (event.target === dom.apiKeyModal) {
              handleCancelApiKey();
            }
          });
        }

        attachSuggestionListeners(dom.suggestionsList);
        attachSuggestionListeners(dom.imageSuggestionsList);
      }

      function initializeApp() {
        loadConfig();
        setupThemeToggle();
        applyFeatureVisibility();
        setupEventListeners();
        document.body.addEventListener("click", initializeAudio, {
          once: true,
        });
        resetMinimapToBase();
        saveFullState();
        toggleBackButton(false);
      }

      document.addEventListener("DOMContentLoaded", (event) => {
        initializeApp();
      });
