import { defineConfig, devices } from "@playwright/test";

const external = process.env.BASE_URL; // e.g. https://jhs512.github.io/practical-exam-500/
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  retries: 0,
  workers: 4,
  reporter: [["list"], ["json", { outputFile: "reports/e2e-results.json" }]],
  use: {
    baseURL: external || "http://localhost:4573/practical-exam-500/",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "mobile", use: { ...devices["Pixel 7"] } },
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 860 } } },
  ],
  webServer: external ? undefined : { command: "node tests/serve.mjs", url: "http://localhost:4573/practical-exam-500/", reuseExistingServer: false },
});
