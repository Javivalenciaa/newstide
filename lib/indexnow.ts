const KEY = '964bf589528b466cace60749e05cfcb6'
const HOST = 'www.newstide.news'
const KEY_LOCATION = `https://${HOST}/${KEY}.txt`

/**
 * Notify Bing/IndexNow about new or updated URLs.
 * Call this whenever an article is published or updated.
 */
export async function pingIndexNow(urls: string[]): Promise<void> {
  if (!urls.length) return

  try {
    await fetch('https://api.indexnow.org/IndexNow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({
        host: HOST,
        key: KEY,
        keyLocation: KEY_LOCATION,
        urlList: urls,
      }),
    })
  } catch (err) {
    // Non-blocking — never crash the main flow
    console.error('[IndexNow] ping failed:', err)
  }
}
