# Cómo publicar en Puente Bursátil

Guía para el equipo interno. No hace falta saber programar.

Cada vez que guardás una noticia o un paper, el sitio se vuelve a publicar solo. Tarda entre 1 y 3 minutos.

Las cotizaciones (S&P 500, Nasdaq, Dow, ADR y monedas) se actualizan solas de lunes a viernes después del cierre de Nueva York. No tenés que hacer nada con ellas.

---

## Opción A: desde el panel (recomendada)

1. Entrá a **https://app.pagescms.org** e iniciá sesión con tu cuenta de GitHub.
2. Elegí el repositorio **puente-bursatil**.
3. En el menú de la izquierda vas a ver **Noticias** y **Papers**.
4. Tocá **Add an entry**, completá el formulario y tocá **Save**.

Campos de una noticia:

| Campo | Qué poner |
|---|---|
| Título | El titular. Corto y concreto. |
| Fecha de publicación | Día y hora. Si ponés una fecha futura, la nota no aparece hasta ese día (en la siguiente actualización del sitio). |
| Autor | Tu nombre o "Redacción Puente Bursátil". |
| Categoría | Wall Street, Nasdaq, Sudamérica, Empresas, Economía o Monedas. |
| Resumen | Una o dos oraciones. Aparece en la portada, en la lista y al compartir el enlace. |
| Imagen principal | Opcional. JPG o PNG de menos de 1 MB. |
| Contenido | El texto completo. Podés usar títulos, negritas, listas, citas y tablas. |

Para un **paper con PDF**: en **Papers**, completá el formulario y subí el archivo en el campo **Archivo PDF**. El sitio muestra un botón "Descargar PDF".

La noticia más reciente aparece siempre como **nota principal** en la portada y en la página de enlaces de Instagram.

---

## Opción B: desde GitHub (sin panel)

### Publicar una noticia

1. Abrí el repositorio en github.com y entrá a la carpeta `_posts`.
2. Tocá **Add file → Create new file**.
3. Poné un nombre con este formato: `AAAA-MM-DD-titulo-corto.md`
   Ejemplo: `2026-11-25-la-fed-y-el-dato-de-inflacion.md`
4. Pegá esta plantilla y completala:

```
---
title: "Título de la noticia"
date: 2026-11-25 19:00:00 -0300
autor: Tu nombre
categoria: Wall Street
resumen: "Una o dos oraciones que resumen la nota."
---

Primer párrafo de la nota.

## Un subtítulo

Más texto. **Negrita** para lo importante.

- Un punto de una lista
- Otro punto
```

5. Tocá **Commit changes**.

### Publicar un paper con PDF

1. Entrá a la carpeta `archivos`, tocá **Add file → Upload files** y subí el PDF. Usá un nombre sin espacios ni tildes, por ejemplo `fed-diciembre-2026.pdf`.
2. Entrá a la carpeta `_papers` y creá un archivo `AAAA-MM-titulo-corto.md` con esta plantilla:

```
---
title: "Título del paper"
date: 2026-11-25
autor: Equipo de análisis
categoria: Economía
resumen: "De qué trata el paper, en una o dos oraciones."
pdf: /archivos/fed-diciembre-2026.pdf
---

Resumen o texto completo del paper.
```

### Editar o borrar

Abrí el archivo en GitHub y tocá el lápiz para editar, o los tres puntos y **Delete file** para borrar.

---

## Si algo no aparece

- Entrá a la pestaña **Actions** del repositorio. Si la última ejecución tiene una cruz roja, abrila: el error suele indicar el archivo y la línea con el problema. El más común es un título con comillas sin cerrar.
- Revisá que la fecha no sea futura.
- Para actualizar las cotizaciones a mano: **Actions → Actualizar datos y publicar el sitio → Run workflow**.
