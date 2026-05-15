import { createClient } from "@supabase/supabase-js";
import { notFound } from "next/navigation";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default async function ArticuloPage({
  params,
}: {
  params: { slug: string };
}) {
  const { data: article, error } = await supabase
    .from("articles")
    .select("*")
    .eq("slug", params.slug)
    .single();

  if (error || !article) {
    notFound();
  }

  const color: Record<string, string> = {
    IA: "#6ecfca", Startups: "#9b8cef",
    Herramientas: "#e8d5a3", Tutoriales: "#7ecf9b", Noticias: "#ef6c6c",
  };
  const cat = color[article.category] || "#6ecfca";

  return (
    <main style={{ background: "#0a0a0a", minHeight: "100vh", color: "#fff" }}>
      <article style={{ maxWidth: 760, margin: "0 auto", padding: "80px 24px" }}>

        {/* META */}
        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24 }}>
          <span style={{
            padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 600,
            letterSpacing: "0.1em", textTransform: "uppercase",
            background: `${cat}18`, color: cat, border: `1px solid ${cat}30`,
          }}>
            {article.category}
          </span>
          <span style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>
            {article.author} · {article.reading_time} min
          </span>
        </div>

        {/* TÍTULO */}
        <h1 style={{ fontSize: "clamp(2rem, 5vw, 3rem)", fontWeight: 800, lineHeight: 1.15, marginBottom: 20 }}>
          {article.title}
        </h1>

        {/* EXCERPT */}
        <p style={{ fontSize: 18, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, marginBottom: 40 }}>
          {article.excerpt}
        </p>

        {/* SEPARADOR */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", marginBottom: 40 }} />

        {/* CONTENIDO */}
        <div style={{
          fontSize: 17, lineHeight: 1.85, color: "rgba(255,255,255,0.85)",
          whiteSpace: "pre-wrap",
        }}>
          {article.content}
        </div>

      </article>
    </main>
  );
}
