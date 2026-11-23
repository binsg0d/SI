"""
Skrypt uruchomieniowy dla zadania Lab 6: Sterownik AEB z logiką rozmytą.

Wykonuje:
1. Przykładową symulację dla reprezentatywnych scenariuszy drogowych (w tym ślad obliczeń).
2. Ilościową analizę wrażliwości na siatce 3D potwierdzającą hierarchię wag cech:
   odległość > prędkość > śliskość.
3. Generację wykresów funkcji przynależności oraz charakterystyk 3D w ciemnym stylu viridis.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib
import numpy as np

from fuzzy_controller import FuzzyController, create_aeb_controller


def configure_dark_3d_axis(ax, xlabel: str, ylabel: str, zlabel: str, title: str) -> None:
    """Konfiguruje ciemny styl wykresu 3D wzorowany na wykresie referencyjnym."""
    ax.set_facecolor("black")
    pane_color = (0.50, 0.50, 0.50, 1.0)
    grid_color = (0.78, 0.78, 0.78, 0.65)

    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color(pane_color)
        axis._axinfo["grid"]["color"] = grid_color
        axis._axinfo["grid"]["linewidth"] = 0.6

    ax.set_xlabel(xlabel, color="white", labelpad=10, fontsize=10)
    ax.set_ylabel(ylabel, color="white", labelpad=10, fontsize=10)
    ax.set_zlabel(zlabel, color="white", labelpad=10, fontsize=10)
    ax.set_title(title, color="white", pad=12, fontsize=11)

    ax.tick_params(axis="x", colors="white", labelsize=8)
    ax.tick_params(axis="y", colors="white", labelsize=8)
    ax.tick_params(axis="z", colors="white", labelsize=8)
    ax.set_zlim(0, 100)
    ax.view_init(elev=28, azim=-55)


def evaluate_surface(
    controller: FuzzyController,
    x_name: str,
    x_vals: np.ndarray,
    y_name: str,
    y_vals: np.ndarray,
    fixed_name: str,
    fixed_val: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Oblicza siatkę wartości sterownika dla dwóch zmiennych wejściowych przy ustalonej trzeciej."""
    xx, yy = np.meshgrid(x_vals, y_vals)
    zz = np.zeros_like(xx, dtype=float)

    for i in range(xx.shape[0]):
        for j in range(xx.shape[1]):
            inputs = {
                x_name: float(xx[i, j]),
                y_name: float(yy[i, j]),
                fixed_name: float(fixed_val),
            }
            zz[i, j] = float(controller.compute(inputs))

    return xx, yy, zz


def plot_membership_functions(controller: FuzzyController, output_dir: Path) -> Path:
    """Rysuje funkcje przynależności wejść (ważone i nieważone) oraz wyjścia."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), facecolor="#111111")
    variables = [
        controller.inputs["odleglosc"],
        controller.inputs["predkosc"],
        controller.inputs["sliskosc"],
        controller.output,
    ]
    palette = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"]

    for ax, var in zip(axes.flat, variables):
        ax.set_facecolor("#1c1c1c")
        for idx, (set_name, fuzzy_set) in enumerate(var.sets.items()):
            color = palette[idx % len(palette)]
            y_unweighted = np.asarray(fuzzy_set.evaluate(var.universe), dtype=float)
            y_weighted = var.weight * y_unweighted

            if var is not controller.output and var.weight < 1.0:
                ax.plot(
                    var.universe,
                    y_unweighted,
                    linestyle="--",
                    linewidth=1.1,
                    color=color,
                    alpha=0.45,
                )
            ax.plot(
                var.universe,
                y_weighted,
                linewidth=2.2,
                color=color,
                label=set_name,
            )

        weight_note = f"waga = {var.weight:.2f}" if var is not controller.output else "zmienna wyjściowa"
        ax.set_title(f"{var.label} ({weight_note})", color="white", fontsize=11, pad=8)
        ax.set_xlabel(f"{var.label} [{var.unit}]", color="white", fontsize=9.5)
        ax.set_ylabel("Przynależność μ", color="white", fontsize=9.5)
        ax.set_ylim(-0.03, 1.08)
        ax.grid(True, color="#444444", linestyle=":", linewidth=0.7)
        ax.tick_params(colors="white", labelsize=8.5)
        for spine in ax.spines.values():
            spine.set_color("#666666")
        legend = ax.legend(loc="upper right", facecolor="#222222", edgecolor="#555555", fontsize=8.5)
        for text in legend.get_texts():
            text.set_color("white")

    fig.suptitle(
        "Funkcje przynależności Gaussa (linia przerywana = bez wagi, ciągła = po przemnożeniu przez wagę)",
        color="white",
        fontsize=12.5,
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = output_dir / "01_funkcje_przynaleznosci.png"
    fig.savefig(out_path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def plot_3d_slices(
    controller: FuzzyController,
    x_name: str,
    y_name: str,
    fixed_name: str,
    fixed_levels: list[tuple[float, str]],
    suptitle: str,
    filename: str,
    output_dir: Path,
    grid_n: int = 40,
) -> Path:
    """Generuje siatkę 1x3 wykresów 3D dla trzech ustalonych poziomów trzeciej cechy."""
    import matplotlib.pyplot as plt

    x_var = controller.inputs[x_name]
    y_var = controller.inputs[y_name]
    x_vals = np.linspace(x_var.universe[0], x_var.universe[-1], grid_n)
    y_vals = np.linspace(y_var.universe[0], y_var.universe[-1], grid_n)

    fig = plt.figure(figsize=(18, 6.2), facecolor="black")
    for idx, (fixed_val, subtitle) in enumerate(fixed_levels, start=1):
        ax = fig.add_subplot(1, 3, idx, projection="3d")
        xx, yy, zz = evaluate_surface(controller, x_name, x_vals, y_name, y_vals, fixed_name, fixed_val)
        ax.plot_surface(
            xx,
            yy,
            zz,
            cmap="viridis",
            vmin=0,
            vmax=100,
            rstride=1,
            cstride=1,
            linewidth=0.15,
            antialiased=True,
        )
        configure_dark_3d_axis(
            ax,
            xlabel=f"{x_var.label} ({x_var.unit})",
            ylabel=f"{y_var.label} ({y_var.unit})",
            zlabel="Siła hamowania (%)",
            title=subtitle,
        )

    fig.suptitle(suptitle, color="white", fontsize=14, y=0.97)
    fig.subplots_adjust(left=0.01, right=0.94, bottom=0.06, top=0.86, wspace=0.16)
    out_path = output_dir / filename
    fig.savefig(out_path, dpi=160, facecolor="black")
    plt.close(fig)
    return out_path


def plot_single_hero_3d(controller: FuzzyController, output_dir: Path, grid_n: int = 45) -> Path:
    """Generuje pojedynczy, czytelny wykres 3D charakterystyki sterownika AEB."""
    import matplotlib.pyplot as plt

    x_var = controller.inputs["odleglosc"]
    y_var = controller.inputs["predkosc"]
    x_vals = np.linspace(x_var.universe[0], x_var.universe[-1], grid_n)
    y_vals = np.linspace(y_var.universe[0], y_var.universe[-1], grid_n)

    xx, yy, zz = evaluate_surface(controller, "odleglosc", x_vals, "predkosc", y_vals, "sliskosc", 50.0)

    fig = plt.figure(figsize=(8.2, 7.6), facecolor="black")
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(
        xx,
        yy,
        zz,
        cmap="viridis",
        vmin=0,
        vmax=100,
        rstride=1,
        cstride=1,
        linewidth=0.15,
        antialiased=True,
    )
    configure_dark_3d_axis(
        ax,
        xlabel="Odległość od przeszkody (m)",
        ylabel="Prędkość pojazdu (km/h)",
        zlabel="Siła hamowania (%)",
        title="Sterowanie hamowaniem awaryjnym AEB (śliskość = 50%)",
    )
    fig.subplots_adjust(left=0.04, right=0.93, bottom=0.06, top=0.92)
    out_path = output_dir / "05_przyklad_3d_glowny.png"
    fig.savefig(out_path, dpi=180, facecolor="black")
    plt.close(fig)
    return out_path


def run_sensitivity_analysis(controller: FuzzyController, n_points: int = 15) -> dict[str, float]:
    """
    Mierzy średni wpływ (rozstęp wyjścia) każdej z cech wejściowych na siatce 3D,
    aby potwierdzić hierarchię wag: odległość > prędkość > śliskość.
    """
    dists = np.linspace(0.0, 100.0, n_points)
    speeds = np.linspace(0.0, 140.0, n_points)
    slips = np.linspace(0.0, 100.0, n_points)

    grid = np.zeros((n_points, n_points, n_points), dtype=float)
    for i, d in enumerate(dists):
        for j, v in enumerate(speeds):
            for k, s in enumerate(slips):
                grid[i, j, k] = float(controller.compute({"odleglosc": d, "predkosc": v, "sliskosc": s}))

    return {
        "odleglosc": float(np.mean(np.ptp(grid, axis=0))),
        "predkosc": float(np.mean(np.ptp(grid, axis=1))),
        "sliskosc": float(np.mean(np.ptp(grid, axis=2))),
    }


def print_demo_scenarios(controller: FuzzyController) -> None:
    """Wypisuje wyniki dla zestawu realistycznych scenariuszy oraz szczegółowy ślad jednego przypadku."""
    scenarios = [
        ("Krytyczne zagrożenie na lodzie", 5.0, 120.0, 90.0),
        ("Nagłe hamowanie w mieście", 12.0, 60.0, 20.0),
        ("Blisko na autostradzie (mokro)", 25.0, 130.0, 55.0),
        ("Korek przy niskiej prędkości", 15.0, 15.0, 10.0),
        ("Średni dystans, duża prędkość", 55.0, 125.0, 40.0),
        ("Średni dystans, lód", 55.0, 70.0, 95.0),
        ("Bezpieczny dystans na autostradzie", 90.0, 130.0, 20.0),
        ("Spokojna jazda (bezpiecznie)", 95.0, 20.0, 10.0),
    ]

    print("=" * 84)
    print(f"{'Scenariusz':<36} | {'Odległ. [m]':>11} | {'Prędk. [km/h]':>13} | {'Ślisk. [%]':>10} | {'Hamow. [%]':>10}")
    print("-" * 84)
    for label, dist, speed, slip in scenarios:
        braking = controller.compute({"odleglosc": dist, "predkosc": speed, "sliskosc": slip})
        print(f"{label:<36} | {dist:11.1f} | {speed:13.1f} | {slip:10.1f} | {braking:10.2f}")
    print("=" * 84)

    sample = {"odleglosc": 28.0, "predkosc": 95.0, "sliskosc": 75.0}
    details = controller.compute(sample, return_details=True)
    print("\nSzczegółowy przebieg dla przypadku testowego:", sample)
    print("  1) Rozmywanie (wartości ważone = waga * mu(x)):")
    for var_name, degrees in details.fuzzified_weighted.items():
        formatted = ", ".join(f"{k}: {v:.3f}" for k, v in degrees.items())
        print(f"     - {var_name} (waga={controller.inputs[var_name].weight:.2f}): {formatted}")
    print("  2) Aktywne reguły (siła odpalenia > 0.05):")
    for rule, strength in details.rule_activations:
        if strength > 0.05:
            ant = " AND ".join(f"{k}={v}" for k, v in rule.antecedents.items())
            print(f"     - [{strength:.3f}] JEŻELI {ant} TO {rule.consequent}")
    print(f"  3) Wyostrzanie (środek ciężkości): {details.crisp_output:.2f} %\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sterownik AEB z logiką rozmytą (Lab 6).")
    parser.add_argument("--show", action="store_true", help="Wyświetl okna wykresów interaktywnie.")
    args = parser.parse_args()

    if not args.show:
        matplotlib.use("Agg")

    controller = create_aeb_controller()
    print_demo_scenarios(controller)

    sensitivity = run_sensitivity_analysis(controller)
    print("Analiza wrażliwości (średni rozstęp siły hamowania przy zmianie pojedynczej cechy):")
    print(f"  - Odległość (waga 1.00): {sensitivity['odleglosc']:.2f} pp")
    print(f"  - Prędkość  (waga 0.65): {sensitivity['predkosc']:.2f} pp")
    print(f"  - Śliskość  (waga 0.35): {sensitivity['sliskosc']:.2f} pp")

    output_dir = Path(__file__).resolve().parent / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = [
        plot_membership_functions(controller, output_dir),
        plot_3d_slices(
            controller,
            x_name="odleglosc",
            y_name="predkosc",
            fixed_name="sliskosc",
            fixed_levels=[
                (10.0, "Śliskość = 10% (suchy asfalt)"),
                (50.0, "Śliskość = 50% (mokra nawierzchnia)"),
                (90.0, "Śliskość = 90% (oblodzenie)"),
            ],
            suptitle="Charakterystyka sterownika AEB dla stałych poziomów śliskości (najmniejsza waga)",
            filename="02_charakterystyka_stala_sliskosc.png",
            output_dir=output_dir,
        ),
        plot_3d_slices(
            controller,
            x_name="odleglosc",
            y_name="sliskosc",
            fixed_name="predkosc",
            fixed_levels=[
                (20.0, "Prędkość = 20 km/h (jazda miejska)"),
                (70.0, "Prędkość = 70 km/h (droga krajowa)"),
                (130.0, "Prędkość = 130 km/h (autostrada)"),
            ],
            suptitle="Charakterystyka sterownika AEB dla stałych poziomów prędkości (średnia waga)",
            filename="03_charakterystyka_stala_predkosc.png",
            output_dir=output_dir,
        ),
        plot_3d_slices(
            controller,
            x_name="predkosc",
            y_name="sliskosc",
            fixed_name="odleglosc",
            fixed_levels=[
                (15.0, "Odległość = 15 m (bliska)"),
                (45.0, "Odległość = 45 m (średnia)"),
                (80.0, "Odległość = 80 m (bezpieczna)"),
            ],
            suptitle="Charakterystyka sterownika AEB dla stałych poziomów odległości (najwyższa waga)",
            filename="04_charakterystyka_stala_odleglosc.png",
            output_dir=output_dir,
        ),
        plot_single_hero_3d(controller, output_dir),
    ]

    print("\nWygenerowane wykresy:")
    for path in generated:
        print(f"  - {path}")

    if args.show:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
