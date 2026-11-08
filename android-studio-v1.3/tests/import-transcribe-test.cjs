const assert = require("assert");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

const edge =
  process.env.STUDIO_CHROME_PATH ||
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

(async () => {
  const browser = await chromium.launch({ executablePath: edge, headless: true });
  const page = await browser.newPage({ viewport: { width: 393, height: 852 } });
  const calls = [];
  let transcriptCount = 0;
  await page.exposeFunction("nativeMock", (id, action, raw) => {
    const payload = JSON.parse(raw);
    calls.push({ action, payload });
    let result = {};
    if (action === "init")
      result = {
        state: {},
        keySet: true,
        audio: false,
        edition: "PREMIUM",
        premium: true,
      };
    if (action === "voices") result = { ready: true, voices: [] };
    if (action === "pick") result = { name: "seleccion.wav" };
    if (action === "recordStart") result = { recording: true };
    if (action === "recordStop")
      result = { recording: false, name: "grabacion.m4a", bytes: 4096 };
    if (action === "transcribe") {
      transcriptCount += 1;
      result =
        transcriptCount === 1
          ? { text: "Transcripción comprobada" }
          : { text: "" };
    }
    return { id, result };
  });
  await page.addInitScript(() => {
    window.Native = {
      call: (id, action, raw) =>
        window
          .nativeMock(id, action, raw)
          .then(({ id, result }) => window.nativeResult(id, result, null)),
    };
  });
  await page.goto(
    pathToFileURL(path.resolve(__dirname, "../assets/index.html")).href,
  );
  await page.waitForFunction(
    () => document.getElementById("editionLabel").textContent === "Premium",
  );
  if (await page.locator("#acceptUsage").count())
    await page.locator("#acceptUsage").click();
  await page.locator("[data-tab=settings]").click();
  await page.locator("#processing").selectOption("openai");
  await page.locator("#consent").check();
  await page.locator("[data-tab=text]").click();

  await page.locator("#pick").click();
  await page.waitForFunction(
    () => document.getElementById("fileName").textContent === "seleccion.wav",
  );
  await page.locator("#url").fill("https://example.test/audio.wav");
  await page.locator("#transcribe").click();
  await page.waitForFunction(
    () =>
      document.getElementById("editor").value === "Transcripción comprobada",
  );
  const firstTranscription = calls.find((call) => call.action === "transcribe");
  assert.equal(
    firstTranscription.payload.url,
    "https://example.test/audio.wav",
    "A URL pasted after file selection did not reach the native route",
  );

  await page.locator("#record").click();
  await page.waitForFunction(
    () => document.getElementById("record").textContent.includes("Detener"),
  );
  await page.locator("#record").click();
  await page.waitForFunction(
    () => document.getElementById("fileName").textContent === "grabacion.m4a",
  );
  assert(calls.some((call) => call.action === "recordStart"));
  assert(calls.some((call) => call.action === "recordStop"));

  const preserved = await page.locator("#editor").inputValue();
  await page.locator("#transcribe").click();
  await page
    .locator("#modal")
    .getByRole("button", { name: "Continuar", exact: true })
    .click();
  await page.waitForFunction(() =>
    document
      .getElementById("statusText")
      .textContent.includes("No se detectó voz"),
  );
  assert.equal(
    await page.locator("#editor").inputValue(),
    preserved,
    "An empty transcription erased the editor",
  );

  await browser.close();
  console.log(
    "PASS import/transcribe: file and recording selection, URL priority, successful transcript, and empty-result preservation.",
  );
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
