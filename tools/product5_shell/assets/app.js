(() => {
  "use strict";

  const data = window.__PROJECT_DATA__;
  if (!data || data.schema !== "residential.product5_config.v0.1") {
    document.body.textContent = "Product 5 configuration is unavailable or invalid.";
    return;
  }

  const text = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value || "";
  };

  const renderGaps = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;
    for (const gap of data.evidence_gaps) {
      const item = document.createElement("li");
      item.textContent = `${gap.topic}：${gap.impact}`;
      container.appendChild(item);
    }
  };

  if (document.body.dataset.view === "mobile") {
    text("mobile-project-name", data.project.name);
    text("mobile-notice", data.project.fixture_notice);
    const route = data.family_routes[0];
    const container = document.getElementById("family-route");
    if (container && route) {
      const heading = document.createElement("h2");
      heading.textContent = route.visible_name;
      container.appendChild(heading);
      route.scenes.forEach((scene, index) => {
        const article = document.createElement("article");
        article.className = "route-step";
        const number = document.createElement("span");
        number.className = "route-index";
        number.textContent = String(index + 1);
        const title = document.createElement("h3");
        title.textContent = scene.visible_title;
        const content = document.createElement("p");
        content.textContent = scene.content;
        article.append(number, title, content);
        container.appendChild(article);
      });
    }
    renderGaps("mobile-gap-list");
    return;
  }

  text("project-name", data.project.name);
  text("project-location", `${data.project.city} · ${data.project.district}`);
  text("fixture-notice", data.project.fixture_notice);
  text("value-anchor", data.value_anchor);

  const nav = document.getElementById("primary-nav");
  if (nav) {
    data.navigation.forEach((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "nav-item";
      button.textContent = item.label;
      button.dataset.target = item.id;
      if (index === 0) button.setAttribute("aria-current", "page");
      button.addEventListener("click", () => {
        nav.querySelectorAll(".nav-item").forEach((node) => node.removeAttribute("aria-current"));
        button.setAttribute("aria-current", "page");
      });
      nav.appendChild(button);
    });
  }

  const cards = document.getElementById("competitiveness-cards");
  if (cards) {
    for (const item of data.super_competitiveness) {
      const article = document.createElement("article");
      article.className = "competitiveness-card";
      const id = document.createElement("span");
      id.className = "card-id";
      id.textContent = item.id;
      const title = document.createElement("h3");
      title.textContent = item.title;
      const gain = document.createElement("p");
      gain.textContent = item.customer_gain;
      article.append(id, title, gain);
      cards.appendChild(article);
    }
  }
  renderGaps("gap-list");
})();

