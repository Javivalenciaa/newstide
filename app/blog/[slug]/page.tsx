import { createSupabaseClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";

export default async function BlogPostPage({
  params,
}: {
  params: { slug: string };
}) {
  const supabase = createSupabaseClient();

  const { data: article, error } = await supabase
    .from("articles")
    .select("*")
    .eq("slug", params.slug)
    .single();

  if (error || !article) {
    notFound();
  }

  return (
    <article className="mx-auto max-w-3xl p-6">
      <p className="text-sm text-gray-400">
        {article.category} · {article.author}
      </p>
      <h1 className="mt-2 text-4xl font-bold">{article.title}</h1>
      <p className="mt-4 text-gray-500">{article.excerpt}</p>

      <div className="mt-8 whitespace-pre-wrap leading-7">
        {article.content}
      </div>
    </article>
  );
}