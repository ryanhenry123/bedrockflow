const fs = require("fs");
const path = require("path");

const DASHBOARD_SCRIPT = fs.readFileSync(
  path.join(__dirname, "../../src/ui/static/dashboard.js"),
  "utf8",
);

function buildDashboardDom({ live = "false", withPipeline = true } = {}) {
  const pipeline = withPipeline
    ? `
      <section
        class="pipeline-run status-completed"
        data-run-id="run-abc12345"
        data-started="2026-06-28T12:00:00.000Z"
        data-finished="2026-06-28T12:00:05.000Z"
      >
        <header class="pipeline-head">
          <div>
            <h2>daily_report</h2>
            <p class="meta">
              <code>abc12345</code>
              <span class="badge completed run-badge">completed</span>
              <span class="run-duration" data-run-duration></span>
            </p>
          </div>
        </header>
        <div class="wave-rail" aria-label="Execution loops">
          <button type="button" class="wave-chip status-completed" data-wave="0">
            <span class="wave-label">Loop 1</span>
            <span class="wave-steps">fetch · report</span>
          </button>
        </div>
        <div class="stages-track">
          <div class="stage-column">
            <article
              class="stage-node status-completed"
              data-step="fetch"
              data-run-id="run-abc12345"
              data-depends-on=""
              tabindex="0"
            >
              <div class="stage-node-head">
                <div class="stage-copy">
                  <h3>fetch</h3>
                  <p class="stage-caller">tasks.fetch_data</p>
                </div>
                <span class="badge completed step-badge">completed</span>
              </div>
              <template class="stage-details">
                <p class="meta">Upstream: none</p>
                <div class="notify-block">
                  <h4>Events</h4>
                  <p class="meta">Waiting for events.</p>
                </div>
              </template>
            </article>
            <article
              class="stage-node status-completed"
              data-step="report"
              data-run-id="run-abc12345"
              data-depends-on="fetch"
              tabindex="0"
            >
              <div class="stage-node-head">
                <div class="stage-copy">
                  <h3>report</h3>
                  <p class="stage-caller">tasks.build_report</p>
                </div>
                <span class="badge completed step-badge">completed</span>
              </div>
              <template class="stage-details">
                <p class="meta">Upstream: fetch</p>
                <div class="notify-block">
                  <h4>Events</h4>
                  <p class="meta">Waiting for events.</p>
                </div>
              </template>
            </article>
          </div>
        </div>
      </section>
    `
    : `
      <section class="empty-state">
        <h2>No pipelines yet</h2>
      </section>
    `;

  document.body.innerHTML = `
    <div class="app">
      <header class="topbar">
        <button type="button" class="ghost-btn" id="fit-view">Fit</button>
        <span class="live-badge" id="live-badge">idle</span>
      </header>
      <div class="workspace">
        <div class="viewport" id="viewport">
          <div class="canvas" id="canvas">
            <svg class="pipeline-edges" id="pipeline-edges" aria-hidden="true"></svg>
            ${pipeline}
          </div>
        </div>
        <aside class="inspector" id="inspector">
          <h2 id="inspector-title">Select a stage</h2>
          <p class="inspector-meta" id="inspector-meta">Click a stage</p>
          <div id="inspector-body"></div>
        </aside>
      </div>
    </div>
  `;
  document.body.dataset.live = live;
}

function loadDashboard() {
  eval(DASHBOARD_SCRIPT);
}

describe("dashboard.js", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    global.fetch = jest.fn().mockResolvedValue({ ok: false });
    Element.prototype.scrollIntoView = jest.fn();
    buildDashboardDom();
    loadDashboard();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllTimers();
  });

  test("exits early when viewport or canvas is missing", () => {
    document.body.innerHTML = "<div></div>";
    expect(() => loadDashboard()).not.toThrow();
    expect(document.querySelector(".stage-node.selected")).toBeNull();
  });

  test("selects the first stage node on load", () => {
    const selected = document.querySelector(".stage-node.selected");
    expect(selected).not.toBeNull();
    expect(selected.dataset.step).toBe("fetch");
    expect(document.getElementById("inspector-title").textContent).toBe("fetch");
  });

  test("updates inspector when another stage is clicked", () => {
    const reportNode = document.querySelector('.stage-node[data-step="report"]');
    reportNode.click();

    expect(reportNode.classList.contains("selected")).toBe(true);
    expect(document.getElementById("inspector-title").textContent).toBe("report");
    expect(document.getElementById("inspector-meta").textContent).toContain(
      "tasks.build_report",
    );
  });

  test("moves selection with arrow keys", () => {
    const reportNode = document.querySelector('.stage-node[data-step="report"]');
    document.body.dispatchEvent(
      new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
    );
    expect(reportNode.classList.contains("selected")).toBe(true);

    document.body.dispatchEvent(
      new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }),
    );
    const fetchNode = document.querySelector('.stage-node[data-step="fetch"]');
    expect(fetchNode.classList.contains("selected")).toBe(true);
  });

  test("renders run duration labels from dataset timestamps", () => {
    const duration = document.querySelector("[data-run-duration]");
    expect(duration.textContent).toMatch(/· 5s/);
  });

  test("highlights a wave when its chip is clicked", () => {
    const chip = document.querySelector(".wave-chip");
    chip.click();

    expect(document.querySelector(".stage-node.wave-highlight")).not.toBeNull();
    expect(chip.classList.contains("selected")).toBe(true);

    chip.click();
    expect(document.querySelector(".stage-node.wave-highlight")).toBeNull();
  });

  test("draws dependency edges into the svg layer", () => {
    jest.runOnlyPendingTimers();
    const edges = document.querySelectorAll("#pipeline-edges path");
    expect(edges.length).toBeGreaterThan(0);
  });

  test("polls the runs api only when live mode is enabled", async () => {
    jest.clearAllMocks();
    document.body.dataset.live = "true";
    buildDashboardDom({ live: "true" });
    loadDashboard();

    await Promise.resolve();
    expect(global.fetch).toHaveBeenCalledWith("/api/runs");

    jest.advanceTimersByTime(1500);
    await Promise.resolve();
    expect(global.fetch.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
