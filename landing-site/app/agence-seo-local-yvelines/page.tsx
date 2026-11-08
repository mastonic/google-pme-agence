import type { Metadata } from 'next'
import { LocalHub } from '../components/LocalHub'
import { hubBySlug } from '../local/hubs'
import { pageMeta } from '../seo/seo'

const hub = hubBySlug('agence-seo-local-yvelines')!

export const metadata: Metadata = { ...pageMeta({ title: hub.title, description: hub.description, path: '/agence-seo-local-yvelines/' }), title: { absolute: hub.title } }

export default function Page() {
  return <LocalHub hub={hub} />
}
