const config = window.__PROJECT_DATA__;

if (!config || config.schema !== "residential.product5_config.v0.1") {
  throw new Error("Product 5 configuration is missing or incompatible.");
}

if (!config.experience || !Array.isArray(config.experience.chapters)) {
  throw new Error("Product 5 customer experience payload is incomplete.");
}

export const projectProfile = {
  ...config.project,
  valueAnchor: config.value_anchor,
  ...config.experience.brand,
};

export const chapters = config.experience.chapters;
export const cityDestinations = config.experience.city.destinations;
export const cityCopy = config.experience.city.copy;
export const communityStates = config.experience.community.states;
export const communityCopy = config.experience.community.copy;
export const livingStandards = config.experience.living.standards;
export const livingCopy = config.experience.living.copy;
export const advisorQuestions = config.experience.advisor.questions;
export const advisorCopy = config.experience.advisor.copy;
export const generationMessages = config.experience.advisor.generation_messages;
export const routes = Object.fromEntries(
  config.experience.advisor.routes.map((route) => [route.slug, route]),
);
export const defaultRoute =
  routes[config.experience.advisor.default_route] ?? config.experience.advisor.routes[0];

export const sceneAssets = [
  ...new Set([
    ...chapters.map((chapter) => chapter.image),
    ...Object.values(routes).map((route) => route.image),
  ]),
];

export function selectRoute(answers) {
  const concerns = answers.concerns ?? [];

  if (answers.trigger === "价格尚未公布" || concerns.includes("价格与权益")) {
    return routes["price-discipline"] ?? defaultRoute;
  }

  if (
    answers.rhythm === "父母阶段性同住" ||
    answers.rhythm === "居家办公与学习并行" ||
    concerns.includes("家庭边界")
  ) {
    return routes["family-flex"] ?? defaultRoute;
  }

  return routes.commute ?? defaultRoute;
}
