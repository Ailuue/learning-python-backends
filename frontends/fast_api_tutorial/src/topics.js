import GROUPS from './groups.json' with { type: 'json' }

// This pattern is to allow hot reloading of the groups.json file, which is useful during development.
// In production, this will be optimized by the bundler.
export { GROUPS }
export const BASE_URL = 'http://localhost:8000'
export const ALL_TOPICS = GROUPS.flatMap((g) => g.topics)
