# WallStreetDailyNews.cl

Sitio de reportes de Wall Street y el Nasdaq para Sudamérica.

- **Portada** (`/`): índices con gráfico del último mes, nota principal, ADR sudamericanos, el dólar en la región, papers y horario local.
- **Noticias** (`/noticias/`) y **Papers** (`/papers/`): las escribe el equipo. Ver [COMO-PUBLICAR.md](COMO-PUBLICAR.md).
- **Enlaces** (`/links/`): página para la bio de Instagram.

## Cómo funciona

- Jekyll, publicado con GitHub Pages.
- `.github/workflows/sitio.yml` corre de lunes a viernes a las 21:45 UTC. Ejecuta `scripts/actualizar_mercado.py`, que descarga los cierres de Yahoo Finance (sin clave de API), guarda `_data/mercado.json` y vuelve a publicar el sitio.
- Cada push a `main` (una noticia o un paper nuevo) también vuelve a publicar el sitio.
- Para cambiar las acciones (`GRUPOS`) o las monedas (`MONEDAS`), editá las listas al principio de `scripts/actualizar_mercado.py`.
- Si una moneda varía más de 3% en un día, se muestra como "dato atípico" en lugar de publicar la variación.

## Puesta en marcha

1. Creá un repositorio público llamado `wallstreetdailynews` en GitHub y subí estos archivos.
2. En `_config.yml` están el usuario de GitHub (`url`), la ruta (`baseurl`) y la cuenta de Instagram.
3. **Settings → Pages → Source: GitHub Actions**.
4. **Actions → Actualizar datos y publicar el sitio → Run workflow**.

El sitio queda en `https://fabiandegiacomid-dotcom.github.io/wallstreetdailynews/` y el enlace para Instagram en `https://fabiandegiacomid-dotcom.github.io/wallstreetdailynews/links/`.
