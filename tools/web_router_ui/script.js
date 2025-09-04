"use strict";

/**
 * Main entry point for the web UI script.
 * Sets up event listeners for user interaction.
 */
function main() {
    const generateButton = document.getElementById("generate-button");
    const promptInput = document.getElementById("prompt-input");

    generateButton.addEventListener("click", handleGeneration);
    promptInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleGeneration();
        }
    });
}

/**
 * Handles the logic when the generate button is clicked.
 * It reads the prompt, validates it, and initiates the API call.
 */
async function handleGeneration() {
    const promptInput = document.getElementById("prompt-input");
    const prompt = promptInput.value.trim();

    if (!prompt) {
        return;
    }

    toggleLoadingState(true);
    addMessageToUI(prompt, "user");
    promptInput.value = ""; // Clear input after sending

    try {
        const response = await callGenerateApi(prompt);
        addMessageToUI(response.text, "model");
        updateStatus(`Generation complete. (${response.tokens_per_second} TPS)`);
    } catch (error) {
        addMessageToUI(`Error: ${error.message}`, "system");
        updateStatus("Error occurred.");
    } finally {
        toggleLoadingState(false);
    }
}

/**
 * Calls the back-end API to generate text.
 * @param {string} prompt - The user's input prompt.
 * @returns {Promise<Object>} A promise that resolves with the API response.
 */
async function callGenerateApi(prompt) {
    const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            prompt: prompt,
            max_tokens: 1024,
        }),
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * Adds a new message bubble to the chat UI.
 * @param {string} text - The text content of the message.
 * @param {'user' | 'model' | 'system'} role - The role of the message sender.
 */
function addMessageToUI(text, role) {
    const responseArea = document.getElementById("response-area");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}-message`;
    messageDiv.textContent = text;
    responseArea.appendChild(messageDiv);
    responseArea.scrollTop = responseArea.scrollHeight; // Auto-scroll to bottom
}

/**
 * Updates the text content of the status bar.
 * @param {string} text - The new status text to display.
 */
function updateStatus(text) {
    const statusBar = document.getElementById("status-bar");
    statusBar.textContent = `Status: ${text}`;
}

/**
 * Enables or disables the UI controls during API calls.
 * @param {boolean} isLoading - True to disable controls, false to enable them.
 */
function toggleLoadingState(isLoading) {
    const generateButton = document.getElementById("generate-button");
    const promptInput = document.getElementById("prompt-input");

    generateButton.disabled = isLoading;
    promptInput.disabled = isLoading;

    if (isLoading) {
        updateStatus("Generating...");
    } else {
        promptInput.focus();
    }
}

// Initialize the script once the DOM is fully loaded.
document.addEventListener("DOMContentLoaded", main);