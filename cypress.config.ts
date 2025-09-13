import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    supportFile: 'cypress/support/e2e.ts',
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
    baseUrl: 'https://space.bilibili.com',
    viewportWidth: 1920,
    viewportHeight: 1080,
    defaultCommandTimeout: 30000,
    requestTimeout: 30000,
    responseTimeout: 30000,
    video: false,
    screenshotOnRunFailure: false,
    // Disable Chrome security features for cross-origin requests
    chromeWebSecurity: false,
    // Docker-specific optimizations
    experimentalMemoryManagement: true,
    numTestsKeptInMemory: 0,
  },
  env: {
    // Environment variables for Bilibili
    BILIBILI_UID: '322005137',
  },
});
