const assert = require("assert");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

const edge =
  process.env.STUDIO_CHROME_PATH ||
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

async function openEdition(browser, edition, keyConfigured = true) {
  const page = await browser.newPage({ viewport: { width: 393, height: 852 } });
  const calls = [];
  let saved = {};
  await page.exposeFunction("nativeMock", (id, action, raw) => {
    const payload = JSON.parse(raw);
    calls.push({ action, payload });
    let result = {};
    if (action === "init")
      result = {
        state: saved,
        keySet: keyConfigured,
        keyProvider: "openai",
        audio: false,
        edition,
        premium: edition === "PREMIUM",
      };
    if (action === "voices") result = { ready: true, voices: [] };
    if (action === "save") saved = payload;
    if (action === "summary") result = { text: "Resumen comprobado" };
    if (action === "settings")
      result = { keySet: !payload.forget, keyProvider: payload.provider };
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
  const html = pathToFileURL(
    path.resolve(__dirname, "../assets/index.html"),
  ).href;
  await page.goto(html);
  await page.waitForFunction(
    () => document.getElementById("editionLabel").textContent !== "Detectando…",
  );
  if (await page.locator("#acceptUsage").count())
    await page.locator("#acceptUsage").click();
  return { page, calls, getSaved: () => saved };
}

(async () => {
  const browser = await chromium.launch({ executablePath: edge, headless: true });
  const premium = await openEdition(browser, "PREMIUM");
  assert.equal(await premium.page.locator("#editionMark").textContent(), "PRO");
  assert.equal(await premium.page.locator("#processing").inputValue(), "auto");
  assert.deepEqual(
    await premium.page
      .locator("#processing option")
      .evaluateAll((options) => options.map((option) => option.value)),
    ["auto", "openai", "server"],
  );
  assert.deepEqual(
    await premium.page
      .locator("#cloudProvider option")
      .evaluateAll((options) => options.map((option) => option.value)),
    ["openai", "google", "groq"],
  );
  await premium.page.locator("#editor").fill("Contenido para resumir.");
  await premium.page.locator("[data-tab=settings]").click();
  await premium.page.locator("#qwenServer").fill("https://ai.example.test");
  await premium.page.locator("#qwenKey").fill("server-secret-not-persisted");
  await premium.page.locator("#consent").check();
  await premium.page.locator("#apiKey").fill("openai-secret-not-persisted");
  await premium.page.locator("#saveSettings").click();
  for (const provider of ["google", "groq", "openai"]) {
    await premium.page.locator("#cloudProvider").selectOption(provider);
    await premium.page.locator("#apiKey").fill(provider + "-temporary-key");
    await premium.page.locator("#saveSettings").click();
    assert.equal(
      premium.calls.filter((call) => call.action === "settings").at(-1).payload
        .provider,
      provider,
    );
  }
  await premium.page.locator("[data-tab=tools]").click();
  await premium.page.locator("#summarize").click();
  await premium.page.waitForFunction(
    () => document.getElementById("modalTitle").textContent === "Resumen",
  );
  const autoCall = premium.calls.find((call) => call.action === "summary");
  assert(autoCall, "Premium summary was not requested");
  assert.equal(autoCall.payload.processing, "auto");
  assert.equal(autoCall.payload.provider, "openai");
  assert.equal(autoCall.payload.server, "https://ai.example.test");
  assert(
    !JSON.stringify(premium.getSaved()).includes("server-secret-not-persisted"),
    "Server token leaked into saved project state",
  );
  assert(
    !JSON.stringify(premium.getSaved()).includes("openai-secret-not-persisted"),
    "OpenAI token leaked into saved project state",
  );
  for (const provider of ["google", "groq", "openai"])
    assert(
      !JSON.stringify(premium.getSaved()).includes(provider + "-temporary-key"),
      provider + " token leaked into saved project state",
    );

  const autoServer = await openEdition(browser, "PREMIUM", false);
  await autoServer.page.locator("#editor").fill("Servidor sin clave personal.");
  await autoServer.page.locator("[data-tab=settings]").click();
  await autoServer.page.locator("#qwenServer").fill("https://ai.example.test");
  await autoServer.page.locator("#qwenKey").fill("server-session-token");
  await autoServer.page.locator("[data-tab=tools]").click();
  await autoServer.page.locator("#summarize").click();
  await autoServer.page.waitForFunction(
    () => document.getElementById("modalTitle").textContent === "Resumen",
  );
  assert(
    autoServer.calls.some(
      (call) =>
        call.action === "summary" &&
        call.payload.processing === "auto" &&
        call.payload.server === "https://ai.example.test",
    ),
    "Automatic mode did not allow an own server without a personal API key",
  );
  await autoServer.page.locator("#closeModal").click();
  await autoServer.page.locator("[data-tab=settings]").click();
  await autoServer.page.locator("#eraseAllData").click();
  await autoServer.page.getByRole("button", { name: "Continuar" }).click();
  await autoServer.page.waitForTimeout(50);
  assert(
    autoServer.calls.some((call) => call.action === "eraseAll"),
    "Local data deletion did not reach the native layer",
  );

  const free = await openEdition(browser, "FREE");
  assert.equal(await free.page.locator("#editionMark").textContent(), "FREE");
  assert(await free.page.locator('#engine option[value="cloud"]').isDisabled());
  assert(await free.page.locator('#engine option[value="qwen"]').isDisabled());
  await free.page.locator("#editor").fill("Texto local de Free.");
  await free.page.locator("[data-tab=tools]").click();
  await free.page.locator("#summarize").click();
  await free.page.waitForFunction(() =>
    document
      .getElementById("statusText")
      .textContent.includes("pertenece a Transcriptor Premium"),
  );
  assert.equal(
    free.calls.filter((call) => call.action === "summary").length,
    0,
    "Free edition reached a Premium native action",
  );
  await free.page.locator("[data-tab=tools]").click();
  await free.page.evaluate(() => {
    for (let i = 1; i <= 3; i++) {
      delete state.currentProjectId;
      document.getElementById("projectName").value = "Proyecto " + i;
      document.getElementById("editor").value = "Texto " + i;
      saveCurrentProject();
    }
  });
  assert.equal(
    await free.page.evaluate(() => state.projects.length),
    3,
    "Free did not retain exactly three projects",
  );
  const fourthProjectError = await free.page.evaluate(() => {
    delete state.currentProjectId;
    document.getElementById("projectName").value = "Proyecto 4";
    document.getElementById("editor").value = "Texto 4";
    try {
      saveCurrentProject();
      return "";
    } catch (error) {
      return error.message;
    }
  });
  assert(fourthProjectError.includes("hasta 3 proyectos"));
  await free.page.evaluate(() => {
    state.history = [];
    for (let i = 0; i < 14; i++) snapshot("Free " + i, "Versión " + i);
  });
  assert.equal(
    await free.page.evaluate(() => state.history.length),
    10,
    "Free history limit was not enforced",
  );

  await browser.close();
  console.log(
    "PASS editions: Free locks Premium AI; Premium exposes automatic, OpenAI/Gemini/Groq BYOK and own-server routes; secrets are not persisted.",
  );
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
