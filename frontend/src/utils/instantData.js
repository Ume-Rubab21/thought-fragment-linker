import {
  getDashboardSummary,
  getKnowledgeGraph,
  listAISuggestions,
  listCollections,
  listNotes,
  listTags,
  warmBackend,
} from '../api'
import { writeInstantCache } from './instantCache'

let prefetchPromise = null

export function prefetchCorePages() {
  if (prefetchPromise) return prefetchPromise

  prefetchPromise = Promise.allSettled([
    warmBackend(),
    listNotes().then((data) => writeInstantCache('notes:::', data)),
    listTags().then((data) => writeInstantCache('tags', data)),
    listCollections().then((data) => writeInstantCache('collections', data)),
    listAISuggestions(null).then((data) => writeInstantCache('suggestions:all', data)),
    getDashboardSummary().then((data) => writeInstantCache('dashboard', data)),
    getKnowledgeGraph().then((data) => writeInstantCache('knowledge-graph', data)),
  ]).finally(() => {
    window.setTimeout(() => { prefetchPromise = null }, 30_000)
  })

  return prefetchPromise
}
