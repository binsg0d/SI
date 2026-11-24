"""
Implementacja algorytmu k najbliższych sąsiadów (kNN) od podstaw
dla zbiorów danych Iris, Wine oraz Breast Cancer Wisconsin (UCI ML Repository).

Zawiera:
- ładowanie i parsowanie zbiorów danych z katalogu data/ (z opcją pobrania z UCI),
- losowy podział na zbiór uczący (60%) i testowy (40%),
- normalizację min-max atrybutów do zakresu [0, 1] dopasowaną na zbiorze uczącym,
- metryki odległości: Euklidesową oraz Manhattan,
- klasyfikator KNNClassifier z deterministycznym rozstrzyganiem remisów,
- moduł eksperymentów (porównanie k, metryk, wpływu normalizacji i stabilności).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
import urllib.request

import numpy as np

DATA_DIR = Path(__file__).parent / "data"

DATASET_URLS: Dict[str, str] = {
    "iris.data": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
    "wine.data": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
    "wdbc.data": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data",
}

METRIC_LABELS: Dict[str, str] = {
    "euclidean": "Euklidesowa",
    "manhattan": "Manhattan",
}


def _ensure_dataset_file(filename: str) -> Path:
    """Sprawdza obecność pliku zbioru danych w data/, a w razie braku pobiera go z UCI."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    if not path.exists():
        url = DATASET_URLS[filename]
        urllib.request.urlretrieve(url, path)
    return path


def _read_nonempty_lines(path: Path) -> List[str]:
    """Wczytuje niepuste wiersze z pliku tekstowego."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_iris() -> Dict[str, object]:
    """Ładuje zbiór danych Iris (150 próbek, 4 cechy, 3 klasy)."""
    path = _ensure_dataset_file("iris.data")
    features: List[List[float]] = []
    labels: List[str] = []

    for line in _read_nonempty_lines(path):
        parts = line.split(",")
        features.append([float(v) for v in parts[:4]])
        labels.append(parts[4])

    X = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=str)
    return {
        "name": "Iris",
        "X": X,
        "y": y,
        "classes": sorted(set(labels)),
        "source_url": "https://archive.ics.uci.edu/dataset/53/iris",
        "description": "Klasyfikacja 3 gatunków kosaćca (Setosa, Versicolor, Virginica) na podstawie 4 wymiarów kwiatu.",
    }


def load_wine() -> Dict[str, object]:
    """Ładuje zbiór danych Wine (178 próbek, 13 cech, 3 klasy)."""
    path = _ensure_dataset_file("wine.data")
    features: List[List[float]] = []
    labels: List[str] = []

    for line in _read_nonempty_lines(path):
        parts = line.split(",")
        # Kolumna 0 to etykieta klasy (1, 2 lub 3), kolumny 1..13 to atrybuty chemiczne.
        labels.append(f"Klasa {parts[0]}")
        features.append([float(v) for v in parts[1:]])

    X = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=str)
    return {
        "name": "Wine",
        "X": X,
        "y": y,
        "classes": sorted(set(labels)),
        "source_url": "https://archive.ics.uci.edu/dataset/109/wine",
        "description": "Rozpoznawanie 3 szczepów win włoskich na podstawie 13 parametrów analizy chemicznej.",
    }


def load_breast_cancer() -> Dict[str, object]:
    """Ładuje zbiór Breast Cancer Wisconsin Diagnostic (569 próbek, 30 cech, 2 klasy)."""
    path = _ensure_dataset_file("wdbc.data")
    features: List[List[float]] = []
    labels: List[str] = []

    for line in _read_nonempty_lines(path):
        parts = line.split(",")
        # Kolumna 0 to ID pacjenta (pomijana), kolumna 1 to diagnoza (M/B), kolumny 2..31 to 30 cech.
        labels.append(parts[1])
        features.append([float(v) for v in parts[2:]])

    X = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=str)
    return {
        "name": "Breast Cancer Wisconsin",
        "X": X,
        "y": y,
        "classes": sorted(set(labels)),
        "source_url": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "description": "Klasyfikacja binarna zmian nowotworowych piersi (M – złośliwy, B – łagodny) na podstawie 30 cech.",
    }


def load_all_datasets() -> List[Dict[str, object]]:
    """Zwraca listę wszystkich trzech zbiorów danych używanych w zadaniu."""
    return [load_iris(), load_wine(), load_breast_cancer()]


def train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    train_ratio: float = 0.6,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Losowo dzieli dane na zbiór uczący (domyślnie 60%) i testowy (40%).
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("Parametr train_ratio musi należeć do przedziału (0, 1).")

    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(X))
    split_idx = int(round(len(X) * train_ratio))

    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    return X[train_idx], y[train_idx], X[test_idx], y[test_idx]


def normalize_minmax(
    X_train: np.ndarray,
    X_test: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Normalizuje atrybuty do zakresu [0, 1] metodą min-max.
    Parametry min i max wyznaczane są wyłącznie na zbiorze uczącym,
    aby uniknąć wycieku informacji ze zbioru testowego.
    """
    min_v = X_train.min(axis=0)
    max_v = X_train.max(axis=0)
    span = np.where(max_v - min_v == 0.0, 1.0, max_v - min_v)

    X_train_norm = (X_train - min_v) / span
    X_test_norm = (X_test - min_v) / span
    return X_train_norm, X_test_norm


def euclidean_distances(X_train: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Oblicza odległość Euklidesową między punktem x a każdym wierszem X_train."""
    return np.sqrt(np.sum((X_train - x) ** 2, axis=1))


def manhattan_distances(X_train: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Oblicza odległość Manhattan między punktem x a każdym wierszem X_train."""
    return np.sum(np.abs(X_train - x), axis=1)


class KNNClassifier:
    """
    Klasyfikator k najbliższych sąsiadów (kNN) z obsługą metryki Euklidesowej i Manhattan.
    """

    def __init__(self, k: int, metric: str = "euclidean") -> None:
        if k < 1:
            raise ValueError("Liczba sąsiadów k musi być >= 1.")
        if metric not in ("euclidean", "manhattan"):
            raise ValueError(f"Nieznana metryka: {metric}. Dozwolone: 'euclidean', 'manhattan'.")
        self.k = k
        self.metric = metric
        self.X_train_: np.ndarray | None = None
        self.y_train_: np.ndarray | None = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "KNNClassifier":
        """Zapamiętuje zbiór uczący (leniwe uczenie algorytmu kNN)."""
        if len(X_train) != len(y_train):
            raise ValueError("Liczba próbek X_train i etykiet y_train musi być równa.")
        if self.k > len(X_train):
            raise ValueError("Liczba sąsiadów k nie może przekraczać rozmiaru zbioru uczącego.")
        self.X_train_ = np.asarray(X_train, dtype=np.float64)
        self.y_train_ = np.asarray(y_train)
        return self

    def _compute_distances(self, x: np.ndarray) -> np.ndarray:
        assert self.X_train_ is not None
        if self.metric == "euclidean":
            return euclidean_distances(self.X_train_, x)
        return manhattan_distances(self.X_train_, x)

    def predict_one(self, x: np.ndarray) -> str:
        """Przewiduje klasę pojedynczego punktu x na podstawie k najbliższych sąsiadów."""
        if self.X_train_ is None or self.y_train_ is None:
            raise RuntimeError("Klasyfikator musi zostać najpierw dopasowany metodą fit().")

        distances = self._compute_distances(x)
        # argpartition/argsort z mergesort gwarantuje stabilne, deterministyczne sortowanie.
        nearest_idx = np.argsort(distances, kind="mergesort")[: self.k]

        counts: Dict[str, int] = defaultdict(int)
        dist_sums: Dict[str, float] = defaultdict(float)
        for idx in nearest_idx:
            label = str(self.y_train_[idx])
            counts[label] += 1
            dist_sums[label] += float(distances[idx])

        # Najwięcej głosów; przy remisie mniejsza suma odległości, potem porządek leksykograficzny.
        best_label = min(
            counts.keys(),
            key=lambda lbl: (-counts[lbl], dist_sums[lbl], lbl),
        )
        return best_label

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Przewiduje klasy dla wszystkich wierszy macierzy X."""
        return np.asarray([self.predict_one(row) for row in X], dtype=str)

    def score(self, X: np.ndarray, y: np.ndarray) -> Tuple[float, Tuple[int, int]]:
        """
        Zwraca dokładność klasyfikacji w procentach oraz krotkę (poprawne, wszystkie).
        """
        preds = self.predict(X)
        correct = int(np.sum(preds == y))
        total = int(len(y))
        accuracy_pct = 100.0 * correct / total
        return accuracy_pct, (correct, total)


def _evaluate_split(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    k_values: Sequence[int],
    metrics: Sequence[str] = ("euclidean", "manhattan"),
) -> Dict[str, Dict[int, Dict[str, object]]]:
    """Oblicza dokładność uczącą i testową dla podanych wartości k i metryk."""
    results: Dict[str, Dict[int, Dict[str, object]]] = {m: {} for m in metrics}
    for metric in metrics:
        for k in k_values:
            clf = KNNClassifier(k=k, metric=metric).fit(X_train, y_train)
            train_acc, train_counts = clf.score(X_train, y_train)
            test_acc, test_counts = clf.score(X_test, y_test)
            results[metric][k] = {
                "train_acc": train_acc,
                "train_correct": train_counts[0],
                "train_total": train_counts[1],
                "test_acc": test_acc,
                "test_correct": test_counts[0],
                "test_total": test_counts[1],
            }
    return results


def run_experiments(
    k_values: Iterable[int] = (1, 3, 5, 7, 9, 11, 15),
    seed: int = 42,
    multi_seeds: int = 20,
) -> Dict[str, object]:
    """
    Przeprowadza komplet eksperymentów kNN na wszystkich 3 zbiorach danych:
    1. Podział 60%/40% (seed) z normalizacją [0, 1] dla obu metryk i listy k.
    2. Porównanie bez normalizacji vs z normalizacją [0, 1].
    3. Ocena stabilności na multi_seeds losowych podziałach 60%/40%.
    """
    k_list = tuple(k_values)
    metrics = ("euclidean", "manhattan")
    datasets = load_all_datasets()
    dataset_results: List[Dict[str, object]] = []

    for ds in datasets:
        X: np.ndarray = ds["X"]  # type: ignore[assignment]
        y: np.ndarray = ds["y"]  # type: ignore[assignment]

        X_train, y_train, X_test, y_test = train_test_split(X, y, train_ratio=0.6, seed=seed)
        X_train_norm, X_test_norm = normalize_minmax(X_train, X_test)

        normalized_eval = _evaluate_split(
            X_train_norm, y_train, X_test_norm, y_test, k_list, metrics
        )
        raw_eval = _evaluate_split(
            X_train, y_train, X_test, y_test, k_list, metrics
        )

        # Stabilność na wielu losowych podziałach (z normalizacją [0, 1])
        stability: Dict[str, Dict[int, Dict[str, float]]] = {m: {} for m in metrics}
        per_seed_acc: Dict[str, Dict[int, List[float]]] = {
            m: {k: [] for k in k_list} for m in metrics
        }
        for s in range(multi_seeds):
            Xt, yt, Xv, yv = train_test_split(X, y, train_ratio=0.6, seed=s)
            Xt_n, Xv_n = normalize_minmax(Xt, Xv)
            for metric in metrics:
                for k in k_list:
                    clf = KNNClassifier(k=k, metric=metric).fit(Xt_n, yt)
                    acc, _ = clf.score(Xv_n, yv)
                    per_seed_acc[metric][k].append(acc)

        for metric in metrics:
            for k in k_list:
                vals = np.asarray(per_seed_acc[metric][k], dtype=np.float64)
                stability[metric][k] = {
                    "mean": float(vals.mean()),
                    "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                    "min": float(vals.min()),
                    "max": float(vals.max()),
                }

        dataset_results.append(
            {
                "name": ds["name"],
                "source_url": ds["source_url"],
                "description": ds["description"],
                "classes": ds["classes"],
                "n_samples": int(len(X)),
                "n_features": int(X.shape[1]),
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
                "train_norm_min": float(X_train_norm.min()),
                "train_norm_max": float(X_train_norm.max()),
                "normalized": normalized_eval,
                "raw": raw_eval,
                "stability": stability,
            }
        )

    return {
        "k_values": list(k_list),
        "seed": seed,
        "multi_seeds": multi_seeds,
        "train_ratio": 0.6,
        "datasets": dataset_results,
    }


def _print_summary(exp: Dict[str, object]) -> None:
    """Wypisuje czytelne tabele wyników w terminalu."""
    k_values: List[int] = exp["k_values"]  # type: ignore[assignment]
    print(f"Eksperyment kNN | Podział 60%/40% (seed={exp['seed']}) | Powtórzenia stabilności={exp['multi_seeds']}")
    print("=" * 96)

    for ds in exp["datasets"]:  # type: ignore[attr-defined]
        print(
            f"\nZbiór: {ds['name']} | Próbki: {ds['n_samples']} "
            f"(uczący={ds['n_train']}, testowy={ds['n_test']}) | Cechy: {ds['n_features']} | "
            f"Zakres train po norm.: [{ds['train_norm_min']:.1f}, {ds['train_norm_max']:.1f}]"
        )
        print("-" * 96)
        header = (
            f"{'k':>3} | {'Eukl. Ucz. (%)':>16} | {'Eukl. Test (%)':>16} | "
            f"{'Manh. Ucz. (%)':>16} | {'Manh. Test (%)':>16} | {'Raw Eukl Test':>14}"
        )
        print(header)
        print("-" * 96)
        norm = ds["normalized"]
        raw = ds["raw"]
        for k in k_values:
            eu = norm["euclidean"][k]
            ma = norm["manhattan"][k]
            re = raw["euclidean"][k]
            print(
                f"{k:>3} | "
                f"{eu['train_acc']:6.2f}% ({eu['train_correct']:>3}/{eu['train_total']:<3}) | "
                f"{eu['test_acc']:6.2f}% ({eu['test_correct']:>3}/{eu['test_total']:<3}) | "
                f"{ma['train_acc']:6.2f}% ({ma['train_correct']:>3}/{ma['train_total']:<3}) | "
                f"{ma['test_acc']:6.2f}% ({ma['test_correct']:>3}/{ma['test_total']:<3}) | "
                f"{re['test_acc']:6.2f}%"
            )


if __name__ == "__main__":
    summary = run_experiments()
    _print_summary(summary)
