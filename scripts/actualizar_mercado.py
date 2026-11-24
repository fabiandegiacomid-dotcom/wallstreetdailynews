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

INDICES = [
    ("^GSPC", "S&P 500"),
    ("^IXIC", "Nasdaq Composite"),
    ("^DJI", "Dow Jones"),
]
ADRS = [
    ("MELI", "MercadoLibre", "Argentina · Uruguay"),
    ("NU", "Nu Holdings", "Brasil"),
    ("PBR", "Petrobras", "Brasil"),
    ("VALE", "Vale", "Brasil"),
    ("ITUB", "Itaú Unibanco", "Brasil"),
    ("YPF", "YPF", "Argentina"),
]
MONEDAS = [
    ("BRL=X", "Real brasileño", "USD/BRL"),
    ("ARS=X", "Peso argentino (oficial)", "USD/ARS"),
    ("CLP=X", "Peso chileno", "USD/CLP"),
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
    signo = "+" if x > 0 else ("−" if x < 0 else "")
    return f"{signo}{numero_es(abs(x), 2)}%"


def direccion(x):
    return "up" if x > 0.0001 else ("down" if x < -0.0001 else "flat")


def descargar(simbolo):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(simbolo) + "?range=1mo&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        datos = json.load(r)
    res = datos["chart"]["result"][0]
    meta = res["meta"]
    tz = timedelta(seconds=meta.get("gmtoffset", -18000))
    serie = []
    for ts, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is None:
            continue
        fecha = datetime.fromtimestamp(ts, timezone(tz)).strftime("%Y-%m-%d")
        if serie and serie[-1][0] == fecha:
            serie[-1] = (fecha, c)
        else:
            serie.append((fecha, c))
    if len(serie) < 2:
        raise ValueError("serie demasiado corta")
    fin_sesion = meta.get("currentTradingPeriod", {}).get("regular", {}).get("end", 0)
    cerrado = time.time() >= fin_sesion
    return serie, cerrado


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


def armar(simbolo, nombre, extra, previos, dec=2, con_serie=False, limite=None):
    try:
        serie, cerrado = descargar(simbolo)
    except Exception as e:  # noqa: BLE001
        print(f"AVISO: {simbolo} falló ({e}); se mantiene el valor anterior", file=sys.stderr)
        return previos.get(simbolo), None
    (_, previo), (fecha, ultimo) = serie[-2], serie[-1]
    cambio = (ultimo / previo - 1) * 100
    item = {
        "simbolo": simbolo, "nombre": nombre, "fecha": fecha,
        "valor": round(ultimo, 4), "valor_txt": numero_es(ultimo, dec),
        "cambio_pct": round(cambio, 4), "cambio_txt": pct_es(cambio),
        "dir": direccion(cambio), "cerrado": cerrado,
    }
    if limite is not None and abs(cambio) > limite:
        # Movimiento diario fuera de lo normal: puede ser un dato erróneo de la fuente.
        item["atipico"] = True
        print(f"AVISO: {simbolo} varió {cambio:.2f}% en un día; se marca como dato atípico", file=sys.stderr)
    if extra:
        item["detalle"] = extra
    if con_serie:
        ultimos = serie[-22:]
        item["sparkline"] = sparkline([v for _, v in ultimos])
        item["desde"] = ultimos[0][0]
    return item, (fecha, cerrado)


def main():
    previos = {}
    if SALIDA.exists():
        viejo = json.loads(SALIDA.read_text(encoding="utf-8"))
        for grupo in ("indices", "adrs", "monedas"):
            for it in viejo.get(grupo, []):
                previos[it["simbolo"]] = it

    salida = {"indices": [], "adrs": [], "monedas": []}
    sesion = None
    for s, n in INDICES:
        it, info = armar(s, n, None, previos, con_serie=True)
        if it:
            salida["indices"].append(it)
        if info and sesion is None:
            sesion = info
    if sesion is None:
        print("ERROR: no se pudo descargar ningún índice; no se modifica el archivo", file=sys.stderr)
        sys.exit(1)
    for s, n, pais in ADRS:
        it, _ = armar(s, n, pais, previos)
        if it:
            salida["adrs"].append(it)
    for s, n, par in MONEDAS:
        it, _ = armar(s, n, par, previos, dec=2, limite=3)
        if it:
            salida["monedas"].append(it)

    fecha, cerrado = sesion
    d = datetime.strptime(fecha, "%Y-%m-%d")
    salida["fecha_sesion"] = fecha
    salida["fecha_texto"] = f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"
    salida["estado"] = "Cierre" if cerrado else "En curso"
    salida["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    salida["fuente"] = "Yahoo Finance"

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: sesión {fecha} ({salida['estado']}) · "
          + " · ".join(f"{i['nombre']} {i['valor_txt']} {i['cambio_txt']}" for i in salida["indices"]))


if __name__ == "__main__":
    main()
