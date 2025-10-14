const APP_CONFIG = {
  API_KEY: "YOUR_API_KEY_HERE", // Your Google Cloud API Key
  PROJECT_ID: "YOUR_GCP_PROJECT_ID_HERE", // Your Google Cloud Project ID
  GEMINI_MODEL: "gemini-2.0-flash", // The default Gemini model you want to use
  GEMINI_MODEL_COLOR_PICKER: "gemini-2.0-flash", // The specific Gemini model you want to use for color extraction / picking
  GEMINI_MODEL_COMPONENT_GENERATION: "gemini-2.0-flash-thinking-exp-01-21", // The specific Gemini model you want to use for coding components
  ENABLE_CUSTOM_COLORS: false, // Whether to enable custom color input in the UI
  ENABLE_IMAGES: false, // Whether to enable image input in the UI
  USE_M3_TXT_SYS_PROMPT: true, // Whether to use m3.txt in system prompt
};

if (
  APP_CONFIG.API_KEY === "YOUR_API_KEY_HERE" ||
  APP_CONFIG.PROJECT_ID === "YOUR_GCP_PROJECT_ID_HERE"
) {
  console.warn(
    "Configuration Warning: Please update 'config.js' with your actual Gemini API Key and Project ID. Add 'config.js' to your .gitignore file."
  );
}
