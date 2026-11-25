#!/usr/bin/env python3
"""Descarga los cierres del día y escribe _data/mercado.json.

Lo ejecuta GitHub Actions de lunes a viernes después del cierre de Nueva York.
No necesita clave de API: usa el endpoint público de gráficos de Yahoo Finance.
Si un símbolo falla, conserva el último valor guardado de ese símbolo.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "_data" / "mercado.json"

# Índices de Wall Street (con gráfico del último mes).
INDICES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq Composite"),
    ("^DJI", "Dow Jones"),
]

# Grupos de acciones. "referencia" es el índice o ETF que resume al grupo.
GRUPOS = [
    {
        "id": "magnificas",
        "titulo": "Las 7 Magníficas",
        "nota": "Las siete tecnológicas que más pesan en el S&P 500 y el Nasdaq. Precios en US$.",
        "referencia": None,
        "acciones": [
            ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("GOOGL", "Alphabet (Google)"),
            ("AMZN", "Amazon"), ("NVDA", "Nvidia"), ("META", "Meta"), ("TSLA", "Tesla"),
        ],
    },
    {
        "id": "chile",
        "titulo": "Chile · IPSA",
        "nota": "Empresas del IPSA que cotizan en Nueva York, en US$. Referencia: ETF iShares MSCI Chile.",
        "referencia": ("ECH", "iShares MSCI Chile (ETF)", 2),
        "acciones": [
            ("SQM", "SQM"), ("BCH", "Banco de Chile"), ("BSAC", "Banco Santander Chile"),
            ("LTM", "LATAM Airlines"), ("ENIC", "Enel Chile"), ("CCU", "CCU"),
            ("AKO-B", "Embotelladora Andina"),
        ],
    },
    {
        "id": "brasil",
        "titulo": "Brasil · B3",
        "nota": "Empresas brasileñas que cotizan en Nueva York, en US$. Referencia: Ibovespa, en puntos.",
        "referencia": ("^BVSP", "Ibovespa", 0),
        "acciones": [
            ("PBR", "Petrobras"), ("VALE", "Vale"), ("ITUB", "Itaú Unibanco"),
            ("NU", "Nu Holdings"), ("BBD", "Bradesco"), ("ABEV", "Ambev"),
        ],
    },
    {
        "id": "argentina",
        "titulo": "Argentina",
        "nota": "ADR argentinos en Nueva York, en US$. Referencia: ETF Global X MSCI Argentina.",
        "referencia": ("ARGT", "Global X MSCI Argentina (ETF)", 2),
        "acciones": [
            ("MELI", "MercadoLibre"), ("YPF", "YPF"), ("GGAL", "Grupo Galicia"),
            ("BMA", "Banco Macro"), ("PAM", "Pampa Energía"), ("TGS", "TGS"),
        ],
    },
]

MONEDAS = [
    ("CLP=X", "Peso chileno", "USD/CLP"),
    ("BRL=X", "Real brasileño", "USD/BRL"),
    ("ARS=X", "Peso argentino (oficial)", "USD/ARS"),
    ("COP=X", "Peso colombiano", "USD/COP"),
    ("PEN=X", "Sol peruano", "USD/PEN"),
]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def numero_es(x, dec=2):
    """7201.09 -> '7.201,09'"""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct_es(x):
    signo = "+" if x > 0.004 else ("−" if x < -0.004 else "")
    return f"{signo}{numero_es(abs(x), 2)}%"


def direccion(x):
    return "up" if x > 0.004 else ("down" if x < -0.004 else "flat")


def descargar(simbolo):
    """Devuelve (serie, fecha, precio, previo, cerrado).

    El precio sale de regularMarketPrice: la barra diaria del día en curso puede
    venir vacía aunque el mercado ya haya cerrado. El cierre previo es el último
    cierre con fecha anterior a la de la sesión.
    """
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(simbolo) + "?range=1mo&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                datos = json.load(r)
            break
        except Exception:  # noqa: BLE001
            if intento == 2:
                raise
            time.sleep(5 * (intento + 1))
    res = datos["chart"]["result"][0]
    meta = res["meta"]
    tz = timezone(timedelta(seconds=meta.get("gmtoffset", -18000)))

    def dia(ts):
        return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d")

    serie = {}
    for ts, c in zip(res.get("timestamp", []), res["indicators"]["quote"][0].get("close", [])):
        if c is not None:
            serie[dia(ts)] = c

    precio = meta.get("regularMarketPrice")
    t = meta.get("regularMarketTime")
    if precio is not None and t:
        fecha = dia(t)
    elif serie:
        fecha = max(serie)
        precio = serie[fecha]
    else:
        raise ValueError("sin datos")

    anteriores = sorted((d, c) for d, c in serie.items() if d < fecha)
    if not anteriores:
        raise ValueError("sin cierre previo")
    previo = anteriores[-1][1]
    fin_sesion = meta.get("currentTradingPeriod", {}).get("regular", {}).get("end", 0)
    cerrado = time.time() >= fin_sesion
    return anteriores + [(fecha, precio)], fecha, precio, previo, cerrado


def sparkline(valores, ancho=120, alto=32):
    """Puntos SVG de la serie, escalados al mínimo y máximo del período."""
    lo, hi = min(valores), max(valores)
    rango = (hi - lo) or 1
    n = len(valores) - 1
    pts = []
    for i, v in enumerate(valores):
        x = i * ancho / n
        y = alto - 2 - (v - lo) / rango * (alto - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    ultimo = pts[-1].split(",")
    return {
        "linea": " ".join(pts),
        "area": f"0,{alto} " + " ".join(pts) + f" {ancho},{alto}",
        "x": ultimo[0], "y": ultimo[1],
        "min_txt": numero_es(lo), "max_txt": numero_es(hi),
    }


def armar(simbolo, nombre, previos, extra=None, dec=2, con_serie=False, limite=None):
    try:
        serie, fecha, precio, previo, cerrado = descargar(simbolo)
    except Exception as e:  # noqa: BLE001
        print(f"AVISO: {simbolo} falló ({e}); se mantiene el valor anterior", file=sys.stderr)
        return previos.get(simbolo), None
    cambio = (precio / previo - 1) * 100
    item = {
        "simbolo": simbolo, "nombre": nombre, "fecha": fecha,
        "valor": round(precio, 4), "valor_txt": numero_es(precio, dec),
        "cambio_pct": round(cambio, 4), "cambio_txt": pct_es(cambio),
        "dir": direccion(cambio), "cerrado": cerrado,
    }
    if extra:
        item["detalle"] = extra
    if limite is not None and abs(cambio) > limite:
        # Movimiento diario fuera de lo normal: puede ser un dato erróneo de la fuente.
        item["atipico"] = True
        print(f"AVISO: {simbolo} varió {cambio:.2f}% en un día; se marca como dato atípico", file=sys.stderr)
    if con_serie:
        ultimos = serie[-22:]
        item["sparkline"] = sparkline([v for _, v in ultimos])
        item["desde"] = ultimos[0][0]
    return item, (fecha, cerrado)


def main():
    previos = {}
    viejo = {}
    if SALIDA.exists():
        viejo = json.loads(SALIDA.read_text(encoding="utf-8"))
        items = viejo.get("indices", []) + viejo.get("monedas", [])
        for g in viejo.get("grupos", []):
            items += g.get("acciones", []) + ([g["referencia"]] if g.get("referencia") else [])
        for it in items:
            previos[it["simbolo"]] = it

    salida = {"indices": [], "grupos": [], "monedas": []}
    sesion = None
    for s, n in INDICES:
        it, info = armar(s, n, previos, con_serie=True)
        if it:
            salida["indices"].append(it)
        if info and sesion is None:
            sesion = info
    if sesion is None:
        print("ERROR: no se pudo descargar ningún índice; no se modifica el archivo", file=sys.stderr)
        sys.exit(1)

    for g in GRUPOS:
        grupo = {"id": g["id"], "titulo": g["titulo"], "nota": g["nota"], "acciones": []}
        if g["referencia"]:
            s, n, dec = g["referencia"]
            ref, _ = armar(s, n, previos, dec=dec)
            if ref:
                grupo["referencia"] = ref
        for s, n in g["acciones"]:
            it, _ = armar(s, n, previos)
            if it:
                grupo["acciones"].append(it)
        salida["grupos"].append(grupo)

    for s, n, par in MONEDAS:
        it, _ = armar(s, n, previos, extra=par, limite=3)
        if it:
            salida["monedas"].append(it)

    fecha, cerrado = sesion
    d = datetime.strptime(fecha, "%Y-%m-%d")
    salida["fecha_sesion"] = fecha
    salida["fecha_texto"] = f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"
    salida["estado"] = "Cierre" if cerrado else "En curso"
    salida["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    salida["fuente"] = "Yahoo Finance"

    # Si los precios no cambiaron (feriado o ejecución de respaldo), no se toca el archivo.
    sin_hora = lambda d: {k: v for k, v in d.items() if k != "actualizado"}  # noqa: E731
    if viejo and sin_hora(viejo) == sin_hora(salida):
        print(f"Sin cambios: los datos de la sesión {salida['fecha_sesion']} ya estaban guardados")
        return

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: sesión {fecha} ({salida['estado']}) · "
          + " · ".join(f"{i['nombre']} {i['valor_txt']} {i['cambio_txt']}" for i in salida["indices"]))


if __name__ == "__main__":
    main()
