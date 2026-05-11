import GROUPS from './groups.json' with { type: 'json' }

export { GROUPS }
export const BASE_URL = 'http://localhost:8001'
export const WS_BASE_URL = 'ws://localhost:8001'
export const ALL_TOPICS = GROUPS.flatMap(g => g.topics)
