/**
 * Helpers applied to stored article markdown before it is rendered.
 *
 * These exist because ~385 articles are already in Supabase with content that
 * a later pipeline change would otherwise not reach. Transforming at render
 * keeps the stored rows untouched (no migration, fully reversible) while the
 * pipelines emit the corrected shape for everything published from now on.
 */

/**
 * Remove the standalone stock-photo credit paragraph from article prose.
 *
 * Both pipelines used to append a line of the form
 *   *Photo: [Marija Zaric](https://unsplash.com/@…) on Unsplash*
 *   *Foto: [Marija Zaric](https://unsplash.com/@…) en Unsplash*
 * directly into the indexable body. The photographer's name therefore became
 * rankable article text, and the site started ranking for it: "marija zaric
 * unsplash" was the single highest-clicked query of the 18 Jun – 28 Aug
 * period, i.e. half of all Google clicks, with zero commercial value. It also
 * fed a junk topic straight back into the content pipeline via Search Console.
 *
 * The Unsplash License does not require attribution ("without permission from
 * or attributing the photographer or Unsplash"), so dropping it from prose is
 * permitted. Attribution is preserved out of indexable prose: the pipelines
 * now carry the credit in the markdown image title, which renders as the
 * image's `title` attribute.
 */
export function stripImageCredits(markdown: string): string {
  if (!markdown) return markdown

  return markdown
    // Whole-line credit, italicised, EN and ES, with or without the link.
    .replace(
      /^\s*[*_]\s*(?:Photo|Foto|Image|Imagen)\s*:.*?(?:on|en)\s+Unsplash\s*[*_]\s*$/gim,
      ''
    )
    // Same line without the italic markers.
    .replace(
      /^\s*(?:Photo|Foto|Image|Imagen)\s*:\s*\[[^\]]*\]\([^)]*unsplash[^)]*\)\s*(?:on|en)\s+Unsplash\s*$/gim,
      ''
    )
    // Collapse the blank gap the removal leaves behind.
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/**
 * True for links that should never pass ranking signal: stock-photo profiles
 * and similar third-party credit destinations. Real citations — the external
 * sources that carry E-E-A-T weight — are deliberately NOT matched here and
 * keep their normal followed links.
 */
export function isCreditLink(href: string | undefined): boolean {
  if (!href) return false
  const h = href.toLowerCase()
  return (
    h.includes('unsplash.com') ||
    h.includes('pexels.com') ||
    h.includes('shutterstock.com') ||
    h.includes('istockphoto.com')
  )
}
