import { createSupabaseClient } from "@/lib/supabase/server";
import Link from "next/link";

export default async function BlogPage() {
  const supabase = createSupabaseClient();

  const { data: articles, error } = await supabase
    .from("articles")
    .select("id, title, excerpt, slug, category, author, created_at")
    .order("created_at", { ascending: false });

  if (error) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <p>Error cargando artículos.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6 space-y-6">
      <h1 className="text-3xl font-bold">Blog</h1>

      <div className="grid gap-4">
        {articles?.map((article) => (
          <Link
            key={article.id}
            href={`/blog/${article.slug}`}
            className="block rounded-xl border p-5 shadow-sm hover:shadow-md transition"
          >
            <h2 className="text-2xl font-semibold">{article.title}</h2>
            <p className="mt-2 text-gray-600">{article.excerpt}</p>
            <div className="mt-3 text-sm text-gray-400 flex gap-3">
              <span>{article.category}</span>
              <span>·</span>
              <span>{article.author}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}