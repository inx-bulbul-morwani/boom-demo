const state = { advisor: "all", priority: "flagged", q: "" };

function matchesPriority(priority) {
  if (state.priority === "all") {
    return true;
  }
  if (state.priority === "flagged") {
    return priority !== "Clear";
  }
  return priority === state.priority;
}

function applyFilters() {
  const query = state.q.trim().toLowerCase();
  const showAll = state.priority === "all";
  const roster = document.getElementById("roster");
  if (roster) {
    roster.hidden = !showAll;
  }
  let visibleRoster = 0;
  document.querySelectorAll("[data-roster-item]").forEach((element) => {
    const advisorOk = state.advisor === "all" || element.dataset.advisor === state.advisor;
    const searchOk = !query || (element.dataset.search || "").includes(query);
    const visible = showAll && advisorOk && searchOk;
    element.hidden = !visible;
    if (visible) {
      visibleRoster += 1;
    }
  });
  const rosterCount = document.getElementById("roster-count");
  if (rosterCount) {
    rosterCount.textContent = `Showing ${visibleRoster} students`;
  }
  if (showAll) {
    const top = document.getElementById("top");
    if (top) {
      top.hidden = true;
    }
    document.querySelectorAll("[data-advisor-section]").forEach((section) => {
      section.hidden = true;
    });
    const empty = document.getElementById("empty");
    if (empty) {
      empty.hidden = visibleRoster !== 0;
    }
    return;
  }

  document.querySelectorAll("[data-student]").forEach((element) => {
    const advisorOk = state.advisor === "all" || element.dataset.advisor === state.advisor;
    const priorityOk = matchesPriority(element.dataset.priority);
    const searchOk = !query || (element.dataset.search || "").includes(query);
    element.hidden = !(advisorOk && priorityOk && searchOk);
  });

  document.querySelectorAll("[data-clear]").forEach((details) => {
    const visible = details.querySelectorAll("[data-clear-item]:not([hidden])").length;
    details.hidden = visible === 0;
    if (visible > 0 && (state.priority === "all" || query)) {
      details.open = true;
    }
  });

  document.querySelectorAll("[data-advisor-section]").forEach((section) => {
    const cards = section.querySelectorAll("[data-card]:not([hidden])").length;
    const clear = section.querySelectorAll("[data-clear-item]:not([hidden])").length;
    section.hidden = cards === 0 && clear === 0;
  });

  const top = document.getElementById("top");
  if (top) {
    top.hidden = top.querySelectorAll("[data-student]:not([hidden])").length === 0;
  }

  const visibleCards = document.querySelectorAll("[data-card]:not([hidden])").length;
  const visibleClear = document.querySelectorAll("[data-clear-item]:not([hidden])").length;
  const empty = document.getElementById("empty");
  if (empty) {
    empty.hidden = visibleCards + visibleClear !== 0;
  }
}

function setPressed(group, value) {
  document.querySelectorAll(`[data-filter-group="${group}"]`).forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.value === value ? "true" : "false");
  });
}

document.querySelectorAll("[data-filter-group]").forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.dataset.filterGroup;
    state[group] = button.dataset.value;
    setPressed(group, button.dataset.value);
    applyFilters();
    if (button.dataset.value === "all") {
      document.getElementById("roster")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

const search = document.getElementById("search");
if (search) {
  search.addEventListener("input", () => {
    state.q = search.value;
    applyFilters();
  });
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const box = document.getElementById(`msg-${button.dataset.copy}`);
    if (!box) {
      return;
    }
    try {
      await navigator.clipboard.writeText(box.value);
    } catch (_error) {
      box.focus();
      box.select();
    }
    const original = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1400);
  });
});

document.querySelectorAll("[data-mailto]").forEach((button) => {
  button.addEventListener("click", () => {
    const box = document.getElementById(`msg-${button.dataset.mailto}`);
    if (!box) {
      return;
    }
    const href = `mailto:${button.dataset.email}?subject=${encodeURIComponent(button.dataset.subject)}&body=${encodeURIComponent(box.value)}`;
    window.location.href = href;
  });
});

document.querySelectorAll("[data-jump]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.jump);
    if (target) {
      target.hidden = false;
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

applyFilters();
