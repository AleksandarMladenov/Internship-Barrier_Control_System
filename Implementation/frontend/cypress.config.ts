import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:5173",
    video: false,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 8000,

    setupNodeEvents(on, config) {
      // you can add node event listeners here later if needed
      return config;
    },
  },
});
