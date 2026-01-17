from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.routes import router as api_router
from app.core.config import load_settings


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="Funnel API", version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix="/api")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(_INDEX_HTML)

    return app


app = create_app()


_INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Funnel</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; }
      textarea { width: 100%; height: 90px; }
      .row { margin: 12px 0; }
      .facet { border: 1px solid #ddd; padding: 8px; margin: 8px 0; }
      .muted { color: #666; font-size: 12px; }
      button { margin-right: 8px; }
      pre { white-space: pre-wrap; background: #f7f7f7; padding: 12px; }
    </style>
  </head>
  <body>
    <h2>Funnel</h2>
    <div class="row">
      <label>Query</label>
      <textarea id="query" placeholder="Ask a question..."></textarea>
    </div>
    <div class="row" id="baseFacets">
      <div class="row">
        <strong>Audience</strong>
        <label><input type="radio" name="audience" value="beginner" /> Beginner</label>
        <label><input type="radio" name="audience" value="intermediate" /> Intermediate</label>
        <label><input type="radio" name="audience" value="expert" /> Expert</label>
        <label><input type="radio" name="audience" value="executive" /> Executive</label>
      </div>
      <div class="row">
        <strong>Format</strong>
        <label><input type="radio" name="format" value="bullets" /> Bullets</label>
        <label><input type="radio" name="format" value="steps" /> Steps</label>
        <label><input type="radio" name="format" value="table" /> Table</label>
        <label><input type="radio" name="format" value="paragraphs" /> Paragraphs</label>
      </div>
      <div class="row">
        <strong>Length</strong>
        <label><input type="radio" name="length" value="300 words" /> 300 words</label>
        <label><input type="radio" name="length" value="600 words" /> 600 words</label>
        <label><input type="radio" name="length" value="900 words" /> 900 words</label>
        <label><input type="radio" name="length" value="1200 words" /> 1200 words</label>
      </div>
    </div>
    <div class="row">
      <label>Domain hint (optional)</label>
      <input id="domainHint" placeholder="finance, legal, universal" />
    </div>
    <div class="row">
      <button id="discoverBtn">Discover facets</button>
      <button id="refineBtn" disabled>Narrow further</button>
      <button id="answerBtn" disabled>Proceed</button>
    </div>
    <div id="facets"></div>
    <div class="row">
      <h3>Answer</h3>
      <pre id="answer"></pre>
    </div>
    <div class="row">
      <h3>Trace</h3>
      <pre id="trace"></pre>
    </div>
    <script>
      const state = { requestId: null, facets: [] };

      const facetsEl = document.getElementById("facets");
      const answerEl = document.getElementById("answer");
      const traceEl = document.getElementById("trace");
      const refineBtn = document.getElementById("refineBtn");
      const answerBtn = document.getElementById("answerBtn");

      function renderFacets(facets, mode = "replace") {
        if (mode === "replace") {
          facetsEl.innerHTML = "";
        }
        facets.forEach((facet, idx) => {
          const div = document.createElement("div");
          div.className = "facet";
          const options = (facet.suggested_values || [])
            .map((val) => {
              return `
                <label>
                  <input type="checkbox" data-suggest="${facet.id}" data-value="${val}" />
                  ${val}
                </label>
              `;
            })
            .join(" ");
          div.innerHTML = `
            <label>
              <input type="checkbox" data-id="${facet.id}" />
              <strong>${facet.title}</strong>
            </label>
            <div>${facet.question}</div>
            <div class="muted">${facet.reason}</div>
            <div class="row">
              <input data-value-for="${facet.id}" placeholder="custom value (optional)" />
            </div>
            <div class="row">${options || ""}</div>
          `;
          facetsEl.appendChild(div);
        });

        document.querySelectorAll('input[type="checkbox"][data-suggest]').forEach((box) => {
          box.onchange = () => {
            const id = box.getAttribute("data-suggest");
            const value = box.getAttribute("data-value");
            const facetBox = document.querySelector(`input[type="checkbox"][data-id="${id}"]`);
            if (facetBox && box.checked) facetBox.checked = true;

            if (value === "all options" && box.checked) {
              document
                .querySelectorAll(`input[type="checkbox"][data-suggest="${id}"]`)
                .forEach((other) => {
                  if (other !== box) other.checked = false;
                });
            }

            if (value !== "all options" && box.checked) {
              const allBox = document.querySelector(
                `input[type="checkbox"][data-suggest="${id}"][data-value="all options"]`
              );
              if (allBox) allBox.checked = false;
            }
          };
        });
      }

      function gatherSelections() {
        const selections = [];
        const baseIds = ["audience", "format", "length"];
        baseIds.forEach((id) => {
          const selected = document.querySelector(`input[name="${id}"]:checked`);
          if (selected) {
            selections.push({ id, value: selected.value });
          }
        });

        document.querySelectorAll('input[type="checkbox"][data-id]').forEach((checkbox) => {
          const id = checkbox.getAttribute("data-id");
          const valueInput = document.querySelector(`input[data-value-for="${id}"]`);
          const customValue = valueInput && valueInput.value ? valueInput.value.trim() : "";
          const selectedValues = [];

          document
            .querySelectorAll(`input[type="checkbox"][data-suggest="${id}"]`)
            .forEach((optionBox) => {
              if (optionBox.checked) {
                selectedValues.push(optionBox.getAttribute("data-value"));
              }
            });

          if (customValue) {
            selectedValues.push(customValue);
          }

          const value = selectedValues.length ? selectedValues.join(", ") : null;
          if (checkbox.checked || value) {
            selections.push({ id, value });
          }
        });
        return selections;
      }

      document.getElementById("discoverBtn").onclick = async () => {
        answerEl.textContent = "";
        traceEl.textContent = "";
        const raw_query = document.getElementById("query").value.trim();
        const domain_hint = document.getElementById("domainHint").value.trim();
        const res = await fetch("/api/discover", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ raw_query, domain_hint: domain_hint || null })
        });
        const data = await res.json();
        state.requestId = data.request_id;
        state.facets = data.facet_candidates || [];
        renderFacets(state.facets);
        refineBtn.disabled = false;
        answerBtn.disabled = false;
      };

      refineBtn.onclick = async () => {
        const res = await fetch("/api/refine", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: state.requestId,
            facet_selections: gatherSelections(),
            refine_round: 2
          })
        });
        const data = await res.json();
        const nextFacets = data.facet_candidates || [];
        if (!nextFacets.length) {
          facetsEl.insertAdjacentHTML(
            "beforeend",
            `<div class="muted">No additional facets found.</div>`
          );
          return;
        }
        state.facets = state.facets.concat(nextFacets);
        renderFacets(nextFacets, "append");
      };

      answerBtn.onclick = async () => {
        const res = await fetch("/api/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: state.requestId,
            facet_selections: gatherSelections()
          })
        });
        const data = await res.json();
        answerEl.textContent = data.answer || "";
        traceEl.textContent = JSON.stringify(data.trace || [], null, 2);
      };
    </script>
  </body>
</html>
"""
