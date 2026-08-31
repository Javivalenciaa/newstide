/**
 * Ejecuta un fichero .sql contra la base de datos de Supabase.
 *
 * Existe porque psql no está instalado en la máquina de desarrollo y
 * `supabase db push` no sirve aquí: aplicaría también migraciones antiguas
 * que no son idempotentes.
 *
 * Uso:
 *   set DATABASE_URL=postgresql://...        (PowerShell: $env:DATABASE_URL="...")
 *   node scripts/run-sql.mjs supabase/migrations/<fichero>.sql
 *
 * La connection string está en:
 *   Supabase → Settings → Database → Connection string → URI
 *   (sustituye [YOUR-PASSWORD] por tu contraseña real)
 *
 * Todo el fichero corre dentro de UNA transacción: si algo falla, no se
 * aplica nada.
 */
import { readFileSync } from 'node:fs'
import pg from 'pg'

const file = process.argv[2]
const url = process.env.DATABASE_URL

if (!file) {
  console.error('❌ Falta el fichero .sql\n   node scripts/run-sql.mjs <ruta.sql>')
  process.exit(1)
}
if (!url) {
  console.error('❌ Falta DATABASE_URL en el entorno.')
  console.error('   Supabase → Settings → Database → Connection string → URI')
  process.exit(1)
}

const sql = readFileSync(file, 'utf8')
const client = new pg.Client({
  connectionString: url,
  ssl: { rejectUnauthorized: false },
})

try {
  await client.connect()
  console.log(`🔌 Conectado. Ejecutando ${file}…`)

  await client.query('BEGIN')
  const res = await client.query(sql)
  await client.query('COMMIT')

  const results = Array.isArray(res) ? res : [res]
  results.forEach((r, i) => {
    if (r && typeof r.rowCount === 'number') {
      console.log(`   sentencia ${i + 1}: ${r.rowCount} fila(s) afectada(s)`)
    }
  })
  console.log('✅ Aplicado correctamente.')
} catch (err) {
  try { await client.query('ROLLBACK') } catch { /* la conexión ya puede estar caída */ }
  console.error('❌ Error — se ha hecho ROLLBACK, no se ha cambiado nada:')
  console.error('  ', err.message)
  process.exitCode = 1
} finally {
  await client.end()
}
