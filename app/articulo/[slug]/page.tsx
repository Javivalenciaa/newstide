import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import ReactMarkdown from 'react-markdown'

export async function generateStaticParams() {
  const { data } = await supabase.from('articles').select('slug')
  return (data || []).map(a => ({ slug: a.slug }))
}

export default async function ArticlePage({ params }: { params: { slug: string } }) {
  const { data: article } = await supabase
    .from('articles')
    .select('*')
    .eq('slug', params.slug)
    .single()

  if (!article) notFound()

  return (
    <main className="article-page">
      <div className="article-hero" style={{background: article.image_gradient}}>
        <div className="article-hero-overlay"/>
        <div className="container">
          <div className="article-header">
            <div className="article-meta-top">
              <span className="badge-article">{article.category}</span>
              <span className="meta-sep">·</span>
              <span>{article.reading_time} min de lectura</span>
              <span className="meta-sep">·</span>
              <span>{new Date(article.published_at).toLocaleDateString('es-ES',{day:'numeric',month:'long',year:'numeric'})}</span>
            </div>
            <h1 className="article-main-title">{article.title}</h1>
            <p className="article-byline">Por <strong>{article.author}</strong></p>
          </div>
        </div>
      </div>
      <div className="container">
        <div className="article-body-wrap">
          <article className="article-content">
            <ReactMarkdown>{article.content}</ReactMarkdown>
          </article>
        </div>
      </div>
    </main>
  )
}
