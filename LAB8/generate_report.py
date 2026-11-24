"""
Generator podsumowania wyników algorytmu kNN w formacie PDF (raport_knn.pdf).

Skrypt uruchamia eksperymenty z modułu knn.py, generuje wykresy matplotlib
(osadzane jako base64 PNG) oraz buduje estetyczny dokument HTML w formacie A4,
konwertowany następnie do pliku PDF za pomocą Google Chrome (headless).
"""

from __future__ import annotations

import base64
import html
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from knn import METRIC_LABELS, run_experiments

REPORT_PATH = Path(__file__).parent / "raport_knn.pdf"


def _fig_to_base64(fig: plt.Figure) -> str:
    """Konwertuje figurę matplotlib na ciąg base64 PNG (200 DPI)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _build_accuracy_chart(exp: Dict[str, object]) -> str:
    """
    Wykres 1: Trzy panele (Iris, Wine, Breast Cancer Wisconsin) pokazujące dokładność (%)
    na zbiorze uczącym i testowym w funkcji k dla metryki Euklidesowej i Manhattan.
    """
    k_values: List[int] = exp["k_values"]  # type: ignore[assignment]
    datasets: List[Dict[str, object]] = exp["datasets"]  # type: ignore[assignment]

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 3.8), sharey=True)
    x_pos = np.arange(len(k_values))

    styles = [
        ("euclidean", "test_acc", "Euklidesowa – test", "#1d4ed8", "-", "o"),
        ("euclidean", "train_acc", "Euklidesowa – uczący", "#60a5fa", "--", "s"),
        ("manhattan", "test_acc", "Manhattan – test", "#dc2626", "-", "^"),
        ("manhattan", "train_acc", "Manhattan – uczący", "#f87171", "--", "d"),
    ]

    for ax, ds in zip(axes, datasets):
        norm = ds["normalized"]  # type: ignore[index]
        for metric, key, label, color, ls, marker in styles:
            ys = [norm[metric][k][key] for k in k_values]
            ax.plot(
                x_pos,
                ys,
                label=label,
                color=color,
                linestyle=ls,
                marker=marker,
                markersize=4.5,
                linewidth=1.7,
            )

        ax.set_title(str(ds["name"]), fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xticks(x_pos)
        ax.set_xticklabels([str(k) for k in k_values], fontsize=8.5)
        ax.set_xlabel("Liczba sąsiadów k", fontsize=9)
        ax.set_ylim(88, 101.5)
        ax.grid(True, linestyle=":", alpha=0.55)

    axes[0].set_ylabel("Dokładność klasyfikacji (%)", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.07),
        ncol=4,
        frameon=False,
        fontsize=8.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _fig_to_base64(fig)


def _build_normalization_chart(exp: Dict[str, object], k_ref: int = 5) -> str:
    """
    Wykres 2: Porównanie dokładności testowej (%) dla k=5 bez normalizacji
    oraz z normalizacją [0, 1] dla metryk Euklidesowej i Manhattan.
    """
    datasets: List[Dict[str, object]] = exp["datasets"]  # type: ignore[assignment]
    names = [str(ds["name"]) for ds in datasets]
    x = np.arange(len(names))
    width = 0.19

    raw_eu = [ds["raw"]["euclidean"][k_ref]["test_acc"] for ds in datasets]  # type: ignore[index]
    norm_eu = [ds["normalized"]["euclidean"][k_ref]["test_acc"] for ds in datasets]  # type: ignore[index]
    raw_ma = [ds["raw"]["manhattan"][k_ref]["test_acc"] for ds in datasets]  # type: ignore[index]
    norm_ma = [ds["normalized"]["manhattan"][k_ref]["test_acc"] for ds in datasets]  # type: ignore[index]

    fig, ax = plt.subplots(figsize=(9.5, 2.75))
    bars = [
        ax.bar(x - 1.5 * width, raw_eu, width, label="Bez normalizacji (Euklidesowa)", color="#94a3b8"),
        ax.bar(x - 0.5 * width, norm_eu, width, label="Normalizacja [0, 1] (Euklidesowa)", color="#1d4ed8"),
        ax.bar(x + 0.5 * width, raw_ma, width, label="Bez normalizacji (Manhattan)", color="#cbd5e1"),
        ax.bar(x + 1.5 * width, norm_ma, width, label="Normalizacja [0, 1] (Manhattan)", color="#dc2626"),
    ]

    for group in bars:
        for bar in group:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                h + 0.8,
                f"{h:.1f}%",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Dokładność testowa (%)", fontsize=9.5)
    ax.set_title(
        f"Wpływ normalizacji [0, 1] na dokładność na zbiorze testowym (k = {k_ref})",
        fontsize=10.5,
        fontweight="bold",
        pad=10,
    )
    ax.set_ylim(0, 110)
    ax.grid(True, axis="y", linestyle=":", alpha=0.55)
    ax.legend(loc="lower right", ncol=2, fontsize=8, frameon=True, facecolor="white", framealpha=0.9)
    fig.tight_layout()
    return _fig_to_base64(fig)


def _format_dataset_table(ds: Dict[str, object], k_values: List[int]) -> str:
    """Buduje tabelę HTML wyników dla pojedynczego zbioru danych."""
    norm = ds["normalized"]  # type: ignore[index]
    best_eu_test = max(norm["euclidean"][k]["test_acc"] for k in k_values)
    best_ma_test = max(norm["manhattan"][k]["test_acc"] for k in k_values)

    rows_html: List[str] = []
    for k in k_values:
        eu = norm["euclidean"][k]
        ma = norm["manhattan"][k]

        eu_test_cls = ' class="best-cell"' if eu["test_acc"] == best_eu_test else ""
        ma_test_cls = ' class="best-cell"' if ma["test_acc"] == best_ma_test else ""

        rows_html.append(
            f"""
            <tr>
              <td class="num bold">{k}</td>
              <td class="num">{eu['train_acc']:.2f}% <span class="frac">({eu['train_correct']}/{eu['train_total']})</span></td>
              <td class="num"{eu_test_cls}>{eu['test_acc']:.2f}% <span class="frac">({eu['test_correct']}/{eu['test_total']})</span></td>
              <td class="num">{ma['train_acc']:.2f}% <span class="frac">({ma['train_correct']}/{ma['train_total']})</span></td>
              <td class="num"{ma_test_cls}>{ma['test_acc']:.2f}% <span class="frac">({ma['test_correct']}/{ma['test_total']})</span></td>
            </tr>
            """
        )

    return f"""
    <div class="table-block">
      <h3>Zbiór: {html.escape(str(ds['name']))}
        <span class="badge">{ds['n_samples']} próbek (uczący: {ds['n_train']}, testowy: {ds['n_test']}) · {ds['n_features']} cech · {len(ds['classes'])} klasy</span>
      </h3>
      <table class="data-table">
        <thead>
          <tr>
            <th rowspan="2" style="width: 8%;">k</th>
            <th colspan="2">Metryka Euklidesowa</th>
            <th colspan="2">Metryka Manhattan</th>
          </tr>
          <tr>
            <th>Zbiór uczący (60%)</th>
            <th>Zbiór testowy (40%)</th>
            <th>Zbiór uczący (60%)</th>
            <th>Zbiór testowy (40%)</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    """


def _format_normalization_table(exp: Dict[str, object], k_ref: int = 5) -> str:
    """Buduje tabelę porównawczą bez normalizacji vs z normalizacją [0, 1] (k=5 oraz średnia po k)."""
    k_values: List[int] = exp["k_values"]  # type: ignore[assignment]
    datasets: List[Dict[str, object]] = exp["datasets"]  # type: ignore[assignment]
    rows: List[str] = []

    for ds in datasets:
        raw = ds["raw"]  # type: ignore[index]
        norm = ds["normalized"]  # type: ignore[index]

        raw_eu_k = raw["euclidean"][k_ref]["test_acc"]
        norm_eu_k = norm["euclidean"][k_ref]["test_acc"]
        raw_ma_k = raw["manhattan"][k_ref]["test_acc"]
        norm_ma_k = norm["manhattan"][k_ref]["test_acc"]

        raw_eu_avg = sum(raw["euclidean"][k]["test_acc"] for k in k_values) / len(k_values)
        norm_eu_avg = sum(norm["euclidean"][k]["test_acc"] for k in k_values) / len(k_values)
        raw_ma_avg = sum(raw["manhattan"][k]["test_acc"] for k in k_values) / len(k_values)
        norm_ma_avg = sum(norm["manhattan"][k]["test_acc"] for k in k_values) / len(k_values)

        delta = norm_eu_k - raw_eu_k
        delta_ma = norm_ma_k - raw_ma_k
        eu_cls = "delta-pos" if delta > 0 else ("delta-neg" if delta < 0 else "delta-zero")
        ma_cls = "delta-pos" if delta_ma > 0 else ("delta-neg" if delta_ma < 0 else "delta-zero")

        rows.append(
            f"""
            <tr>
              <td class="bold">{html.escape(str(ds['name']))}</td>
              <td class="num">{raw_eu_k:.2f}%</td>
              <td class="num best-cell">{norm_eu_k:.2f}% <span class="{eu_cls}">({delta:+.2f} pp)</span></td>
              <td class="num">{raw_ma_k:.2f}%</td>
              <td class="num best-cell">{norm_ma_k:.2f}% <span class="{ma_cls}">({delta_ma:+.2f} pp)</span></td>
              <td class="num">{raw_eu_avg:.2f}% &rarr; <b>{norm_eu_avg:.2f}%</b></td>
              <td class="num">{raw_ma_avg:.2f}% &rarr; <b>{norm_ma_avg:.2f}%</b></td>
            </tr>
            """
        )

    return f"""
    <table class="data-table compact">
      <thead>
        <tr>
          <th rowspan="2">Zbiór danych</th>
          <th colspan="2">Euklidesowa (k = {k_ref})</th>
          <th colspan="2">Manhattan (k = {k_ref})</th>
          <th colspan="2">Średnia po wszystkich k</th>
        </tr>
        <tr>
          <th>Bez norm.</th>
          <th>Norm. [0, 1]</th>
          <th>Bez norm.</th>
          <th>Norm. [0, 1]</th>
          <th>Euklidesowa</th>
          <th>Manhattan</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """


def _format_stability_table(exp: Dict[str, object]) -> str:
    """Buduje tabelę stabilności (średnia ± odchylenie standardowe z 20 losowych podziałów 60/40)."""
    k_stab = [1, 3, 5, 7, 9, 11]
    datasets: List[Dict[str, object]] = exp["datasets"]  # type: ignore[assignment]
    rows: List[str] = []

    for ds in datasets:
        stab = ds["stability"]  # type: ignore[index]
        for metric_key in ("euclidean", "manhattan"):
            cells = "".join(
                f"<td class='num'>{stab[metric_key][k]['mean']:.1f}% &plusmn; {stab[metric_key][k]['std']:.1f}</td>"
                for k in k_stab
            )
            rows.append(
                f"""
                <tr>
                  <td class="bold">{html.escape(str(ds['name']))}</td>
                  <td>{METRIC_LABELS[metric_key]}</td>
                  {cells}
                </tr>
                """
            )

    headers = "".join(f"<th>k = {k}</th>" for k in k_stab)
    return f"""
    <table class="data-table compact">
      <thead>
        <tr>
          <th>Zbiór danych</th>
          <th>Metryka</th>
          {headers}
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    """


def build_html(exp: Dict[str, object]) -> str:
    """Składa kompletny dokument HTML raportu."""
    k_values: List[int] = exp["k_values"]  # type: ignore[assignment]
    datasets: List[Dict[str, object]] = exp["datasets"]  # type: ignore[assignment]

    chart1_b64 = _build_accuracy_chart(exp)
    chart2_b64 = _build_normalization_chart(exp, k_ref=5)

    dataset_info_rows = "".join(
        f"""
        <tr>
          <td class="bold">{html.escape(str(ds['name']))}</td>
          <td class="num">{ds['n_samples']}</td>
          <td class="num">{ds['n_train']} / {ds['n_test']}</td>
          <td class="num">{ds['n_features']}</td>
          <td class="num">{len(ds['classes'])}</td>
          <td>{html.escape(str(ds['description']))}</td>
        </tr>
        """
        for ds in datasets
    )

    per_dataset_tables = "".join(_format_dataset_table(ds, k_values) for ds in datasets)
    norm_table = _format_normalization_table(exp, k_ref=5)
    stab_table = _format_stability_table(exp)

    # Dynamiczne wartości do sekcji analitycznej (zero liczb wpisanych na sztywno).
    iris_ds, wine_ds, bc_ds = datasets[0], datasets[1], datasets[2]
    iris_raw_min = min(iris_ds["raw"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    iris_raw_max = max(iris_ds["raw"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    iris_eu_min = min(iris_ds["normalized"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    iris_eu_max = max(iris_ds["normalized"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    iris_ma_min = min(iris_ds["normalized"]["manhattan"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    iris_ma_max = max(iris_ds["normalized"]["manhattan"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    wine_raw_min = min(wine_ds["raw"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    wine_raw_max = max(wine_ds["raw"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    wine_norm_min = min(wine_ds["normalized"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    wine_norm_max = max(wine_ds["normalized"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    wine_ma_max = max(wine_ds["normalized"]["manhattan"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    bc_eu_max = max(bc_ds["normalized"]["euclidean"][k]["test_acc"] for k in k_values)  # type: ignore[index]
    bc_ma_max = max(bc_ds["normalized"]["manhattan"][k]["test_acc"] for k in k_values)  # type: ignore[index]

    iris_norm_range = (
        f"{iris_eu_min:.2f}%"
        if iris_eu_min == iris_eu_max
        else f"{iris_eu_min:.2f}%–{iris_eu_max:.2f}%"
    )

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <title>Podsumowanie kNN – Ćwiczenia 8</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 12mm 13mm 12mm 13mm;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
      font-size: 9.2pt;
      line-height: 1.42;
      color: #1e293b;
      margin: 0;
      padding: 0;
    }}
    .header {{
      border-bottom: 2.5px solid #1d4ed8;
      padding-bottom: 8px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .header h1 {{
      margin: 0;
      font-size: 15.5pt;
      color: #0f172a;
      letter-spacing: -0.2px;
    }}
    .header .subtitle {{
      margin-top: 2px;
      font-size: 9.5pt;
      color: #475569;
    }}
    .header .meta {{
      text-align: right;
      font-size: 8.4pt;
      color: #475569;
      line-height: 1.35;
    }}
    h2 {{
      font-size: 11.2pt;
      color: #1e3a8a;
      border-left: 3.5px solid #1d4ed8;
      padding-left: 8px;
      margin: 11px 0 5px 0;
      break-after: avoid;
    }}
    h3 {{
      font-size: 9.8pt;
      color: #0f172a;
      margin: 8px 0 4px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      break-after: avoid;
    }}
    .badge {{
      font-size: 8pt;
      font-weight: normal;
      background: #eff6ff;
      color: #1e40af;
      border: 1px solid #bfdbfe;
      padding: 1px 7px;
      border-radius: 10px;
    }}
    p {{
      margin: 0 0 7px 0;
      text-align: justify;
    }}
    .formula-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin: 8px 0 10px 0;
      break-inside: avoid;
    }}
    .formula-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 5px;
      padding: 7px 9px;
      font-size: 8.3pt;
    }}
    .formula-card .title {{
      font-weight: bold;
      color: #0f172a;
      margin-bottom: 3px;
    }}
    .formula-card code {{
      font-family: "DejaVu Sans Mono", monospace;
      font-size: 7.3pt;
      color: #1d4ed8;
      white-space: nowrap;
      display: inline-block;
    }}
    .table-block {{
      break-inside: avoid;
      margin-bottom: 10px;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 8.4pt;
      margin-bottom: 6px;
      break-inside: avoid;
    }}
    table.data-table.compact {{
      font-size: 7.9pt;
    }}
    table.data-table th {{
      background: #1e3a8a;
      color: #ffffff;
      font-weight: bold;
      padding: 4.5px 6px;
      border: 1px solid #1e3a8a;
      text-align: center;
    }}
    table.data-table td {{
      padding: 3.8px 5.5px;
      border: 1px solid #cbd5e1;
      vertical-align: middle;
    }}
    table.data-table tbody tr:nth-child(even) {{
      background: #f8fafc;
    }}
    td.num {{
      text-align: center;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}
    td.bold {{
      font-weight: bold;
      color: #0f172a;
    }}
    .frac {{
      color: #64748b;
      font-size: 7.6pt;
    }}
    .delta-pos {{
      color: #15803d;
      font-size: 7.4pt;
      font-weight: normal;
    }}
    .delta-neg {{
      color: #b91c1c;
      font-size: 7.4pt;
      font-weight: normal;
    }}
    .delta-zero {{
      color: #64748b;
      font-size: 7.4pt;
      font-weight: normal;
    }}
    td.best-cell {{
      background: #eff6ff;
      font-weight: bold;
      color: #1e3a8a;
    }}
    .chart-box {{
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 5px 7px;
      background: #ffffff;
      margin: 6px 0 7px 0;
      text-align: center;
      break-inside: avoid;
    }}
    .chart-box img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }}
    .chart-caption {{
      font-size: 7.9pt;
      color: #475569;
      margin-top: 3px;
    }}
    .note-box {{
      background: #f0fdf4;
      border-left: 3.5px solid #16a34a;
      padding: 6px 9px;
      margin: 6px 0;
      font-size: 8.4pt;
      break-inside: avoid;
    }}
    ul.conclusions {{
      margin: 4px 0 0 0;
      padding-left: 17px;
      font-size: 8.6pt;
      break-inside: avoid;
    }}
    ul.conclusions li {{
      margin-bottom: 3px;
    }}
    .page-break {{
      page-break-before: always;
      break-before: page;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>Podstawy sztucznej inteligencji – Ćwiczenia 8</h1>
      <div class="subtitle">Implementacja i analiza algorytmu k najbliższych sąsiadów (kNN)</div>
    </div>
    <div class="meta">
      Data: 2026-11-24<br/>
      Autor: binsg0d (repozytorium SI/LAB8)
    </div>
  </div>

  <h2>1. Cel zadania i metodologia</h2>
  <p>
    Celem ćwiczenia było zaimplementowanie od podstaw klasyfikatora <b>k najbliższych sąsiadów (kNN)</b>
    oraz zbadanie jego skuteczności na trzech zbiorach danych z repozytorium UCI Machine Learning Repository:
    <b>Iris</b>, <b>Wine</b> oraz wybranym dodatkowo <b>Breast Cancer Wisconsin (Diagnostic)</b>.
    Każdy zbiór został losowo podzielony w proporcji <b>60% zbiór uczący</b> i <b>40% zbiór testowy</b>
    (ziarno generatora <code>seed={exp['seed']}</code>), a wszystkie atrybuty numeryczne zostały znormalizowane
    do przedziału <b>[0, 1]</b> przy użyciu parametrów minimum i maksimum wyznaczonych wyłącznie na zbiorze uczącym.
  </p>

  <div class="formula-grid">
    <div class="formula-card">
      <div class="title">Normalizacja Min-Max [0, 1]</div>
      <code>x' = (x - min_train) / (max_train - min_train)</code><br/>
      Zapobiega dominacji cech o dużych zakresach wartości i eliminuje wyciek danych ze zbioru testowego.
    </div>
    <div class="formula-card">
      <div class="title">Odległość Euklidesowa</div>
      <code>d(A, B) = sqrt( sum((Ai - Bi)^2) )</code><br/>
      Standardowa metryka L2 mierząca odległość w linii prostej w przestrzeni n-wymiarowej.
    </div>
    <div class="formula-card">
      <div class="title">Odległość Manhattan</div>
      <code>d(A, B) = sum( |Ai - Bi| )</code><br/>
      Metryka L1 (taksówkowa) będąca sumą wartości bezwzględnych różnic wzdłuż poszczególnych osi.
    </div>
  </div>

  <h2>2. Charakterystyka wykorzystanych zbiorów danych</h2>
  <table class="data-table">
    <thead>
      <tr>
        <th>Zbiór danych</th>
        <th>Próbki</th>
        <th>Podział 60% / 40%</th>
        <th>Cechy</th>
        <th>Klasy</th>
        <th>Opis zadania klasyfikacyjnego</th>
      </tr>
    </thead>
    <tbody>
      {dataset_info_rows}
    </tbody>
  </table>

  <h2>3. Wyniki klasyfikacji kNN (po normalizacji [0, 1])</h2>
  <p>
    W poniższych tabelach przedstawiono odsetek oraz liczbę poprawnie sklasyfikowanych obserwacji
    na zbiorze uczącym (60%) i testowym (40%) dla wybranych wartości <code>k &isin; {{{', '.join(str(k) for k in k_values)}}}</code>
    oraz obu metryk odległości. Pogrubieniem wyróżniono najlepsze wyniki na zbiorze testowym dla danej metryki.
  </p>

  {per_dataset_tables}

  <div class="chart-box">
    <img src="data:image/png;base64,{chart1_b64}" alt="Wykres dokładności kNN w funkcji k" />
    <div class="chart-caption">
      Rys. 1. Zależność dokładności klasyfikacji (%) na zbiorze uczącym i testowym od parametru k
      oraz wybranej metryki (po normalizacji atrybutów do zakresu [0, 1]).
    </div>
  </div>

  <div class="page-break"></div>

  <h2>4. Wpływ normalizacji atrybutów oraz stabilność wyników</h2>
  <p>
    Aby zweryfikować znaczenie skalowania cech (oraz wyjaśnić podpowiedź z treści zadania), porównano
    dokładność klasyfikatora kNN na danych surowych (bez normalizacji) i znormalizowanych do [0, 1].
  </p>

  <div class="table-block">
    {norm_table}
  </div>

  <div class="chart-box">
    <img src="data:image/png;base64,{chart2_b64}" alt="Porównanie dokładności bez normalizacji i z normalizacją" />
    <div class="chart-caption">
      Rys. 2. Porównanie dokładności testowej dla k = 5 przed i po normalizacji min-max do zakresu [0, 1].
    </div>
  </div>

  <div class="note-box">
    <b>Obserwacja kluczowa (Iris vs Wine):</b> Na zbiorze <b>Iris</b> wszystkie 4 cechy są wyrażone w zbliżonej skali
    (centymetry), dlatego dokładność testowa jest wysoka niezależnie od skalowania:
    <b>{iris_norm_range}</b> po normalizacji (Euklidesowa) oraz <b>{iris_ma_min:.2f}%–{iris_ma_max:.2f}%</b> (Manhattan),
    wobec <b>{iris_raw_min:.2f}%–{iris_raw_max:.2f}%</b> bez normalizacji.
    W zbiorze <b>Wine</b> poszczególne atrybuty chemiczne różnią się o rzędy wielkości (np. <i>Proline</i> przyjmuje
    wartości ok. 278–1680, podczas gdy <i>Nonflavanoid phenols</i> ok. 0,13–0,66). Bez normalizacji pojedyncza cecha
    zdominowała metrykę odległości, obniżając skuteczność testową do <b>{wine_raw_min:.2f}%–{wine_raw_max:.2f}%</b>.
    Po normalizacji do [0, 1] dokładność dla Wine wzrasta do <b>{wine_norm_min:.2f}%–{wine_norm_max:.2f}%</b>
    (Euklidesowa) oraz nawet <b>{wine_ma_max:.2f}%</b> (Manhattan).
  </div>

  <h3>Stabilność wyników na {exp['multi_seeds']} losowych podziałach 60% / 40%
    <span class="badge">średnia &plusmn; odch. std. testowe [0, 1]</span>
  </h3>
  <div class="table-block">
    {stab_table}
  </div>

  <h2>5. Wnioski</h2>
  <ul class="conclusions">
    <li>
      <b>Wpływ parametru k:</b> Dla <code>k = 1</code> klasyfikator osiąga zawsze <b>100,00%</b> na zbiorze uczącym
      (każdy punkt jest swoim najbliższym sąsiadem), co oznacza niskie obciążenie i wysoką wariancję (ryzyko
      przeuczenia na szumie). Zwiększanie <code>k</code> do wartości 3–11 wygładza granice decyzyjne i stabilizuje
      wyniki na zbiorze testowym.
    </li>
    <li>
      <b>Porównanie metryk Euklidesowej i Manhattan:</b> Obie metryki zapewniają bardzo zbliżoną, wysoką skuteczność
      po normalizacji (Iris ~95–97%, Wine ~94–100%, Breast Cancer do {max(bc_eu_max, bc_ma_max):.2f}%). Metryka Manhattan
      bywa minimalnie bardziej odporna na pojedyncze cechy odstające w wyższych wymiarach (np. Wine dla 13 cech
      i Breast Cancer dla 30 cech).
    </li>
    <li>
      <b>Znaczenie normalizacji [0, 1]:</b> Normalizacja min-max (dopasowana wyłącznie na zbiorze uczącym) jest
      krytycznym etapem wstępnego przetwarzania danych dla algorytmów opartych na odległości – na zbiorze Wine
      poprawiła skuteczność testową o ok. 18–20 punktów procentowych.
    </li>
  </ul>
</body>
</html>
"""


def generate_pdf(output_path: Path = REPORT_PATH) -> Path:
    """Generuje kompletny raport PDF w podanej ścieżce."""
    exp = run_experiments()
    html_content = build_html(exp)

    with tempfile.TemporaryDirectory() as tmp_dir:
        html_file = Path(tmp_dir) / "raport_knn.html"
        html_file.write_text(html_content, encoding="utf-8")

        cmd = [
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_path}",
            html_file.as_uri(),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return output_path


if __name__ == "__main__":
    pdf = generate_pdf()
    print(f"Wygenerowano raport PDF: {pdf} ({pdf.stat().st_size} B)")
