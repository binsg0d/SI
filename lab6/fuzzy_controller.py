"""
Autonomiczny sterownik awaryjnego hamowania pojazdu (AEB) oparty na logice rozmytej.

Moduł implementuje kompletny algorytm wnioskowania rozmytego Mamdaniego od zera
(bez użycia zewnętrznych bibliotek logiki rozmytej):
- funkcje przynależności Gaussa oraz uogólnione funkcje dzwonowe (gbell),
- ważenie cech wejściowych przez przemnożenie funkcji przynależności przez wagę cechy,
- blok rozmywania (fuzzification),
- bazę reguł rozmytych i blok wnioskowania Mamdaniego (T-norma min, implikacja min, agregacja max),
- blok wyostrzania metodą środka ciężkości (centroid / Center of Gravity).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


def gaussian_mf(x: float | np.ndarray, mean: float, sigma: float) -> float | np.ndarray:
    """Gaussowska funkcja przynależności: exp(-((x - mean)^2) / (2 * sigma^2))."""
    if sigma <= 0:
        raise ValueError("Parametr sigma musi być dodatni.")
    return np.exp(-0.5 * ((np.asarray(x, dtype=float) - mean) / sigma) ** 2)


def gbell_mf(x: float | np.ndarray, a: float, b: float, c: float) -> float | np.ndarray:
    """Uogólniona dzwonowa funkcja przynależności: 1 / (1 + |(x - c) / a|^(2b))."""
    if a <= 0 or b <= 0:
        raise ValueError("Parametry a i b muszą być dodatnie.")
    return 1.0 / (1.0 + np.abs((np.asarray(x, dtype=float) - c) / a) ** (2.0 * b))


@dataclass(frozen=True)
class FuzzySet:
    """Pojedynczy zbiór rozmyty opisany nazwą, funkcją przynależności i jej parametrami."""

    name: str
    mf_func: Callable[..., float | np.ndarray]
    params: dict[str, float]

    def evaluate(self, x: float | np.ndarray) -> float | np.ndarray:
        """Oblicza stopień przynależności wartości x do zbioru rozmytego."""
        result = self.mf_func(x, **self.params)
        if np.ndim(result) == 0:
            return float(result)
        return result


@dataclass
class LinguisticVariable:
    """Zmienna lingwistyczna (wejściowa lub wyjściowa) wraz z wagą cechy."""

    name: str
    universe: np.ndarray
    sets: dict[str, FuzzySet]
    weight: float = 1.0
    unit: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        if not 0.0 < self.weight <= 1.0:
            raise ValueError(f"Waga cechy '{self.name}' musi należeć do przedziału (0, 1].")
        if not self.label:
            self.label = self.name

    def fuzzify(self, x: float, apply_weight: bool = True) -> dict[str, float]:
        """
        Blok rozmywania dla pojedynczej zmiennej.

        Wpływ cechy realizowany jest przez przemnożenie wartości funkcji
        przynależności przez wagę cechy: mu_weighted(x) = weight * mu(x).
        """
        factor = self.weight if apply_weight else 1.0
        clipped_x = float(np.clip(x, self.universe[0], self.universe[-1]))
        return {
            set_name: float(factor * fuzzy_set.evaluate(clipped_x))
            for set_name, fuzzy_set in self.sets.items()
        }


@dataclass(frozen=True)
class FuzzyRule:
    """Reguła rozmyta postaci JEŻELI (przesłanki połączone spójnikiem I) TO (wniosek)."""

    antecedents: dict[str, str]
    consequent: str
    description: str = ""


@dataclass
class InferenceDetails:
    """Szczegółowy wynik pojedynczego przebiegu sterownika (do inspekcji i debugowania)."""

    crisp_inputs: dict[str, float]
    fuzzified_unweighted: dict[str, dict[str, float]]
    fuzzified_weighted: dict[str, dict[str, float]]
    rule_activations: list[tuple[FuzzyRule, float]]
    aggregated_output: np.ndarray
    crisp_output: float


class FuzzyController:
    """Sterownik rozmyty typu Mamdaniego z wyostrzaniem metodą środka ciężkości."""

    def __init__(
        self,
        inputs: dict[str, LinguisticVariable],
        output: LinguisticVariable,
        rules: list[FuzzyRule],
    ) -> None:
        self.inputs = inputs
        self.output = output
        self.rules = rules
        self._output_mfs: dict[str, np.ndarray] = {
            set_name: np.asarray(fuzzy_set.evaluate(self.output.universe), dtype=float)
            for set_name, fuzzy_set in self.output.sets.items()
        }
        self._validate_rules()

    def _validate_rules(self) -> None:
        for rule in self.rules:
            for var_name, set_name in rule.antecedents.items():
                if var_name not in self.inputs:
                    raise ValueError(f"Nieznana zmienna wejściowa w regule: {var_name}")
                if set_name not in self.inputs[var_name].sets:
                    raise ValueError(f"Nieznany zbiór '{set_name}' dla zmiennej '{var_name}'")
            if rule.consequent not in self.output.sets:
                raise ValueError(f"Nieznany zbiór wyjściowy w regule: {rule.consequent}")

    def fuzzify(self, crisp_inputs: dict[str, float], apply_weight: bool = True) -> dict[str, dict[str, float]]:
        """Rozmywa wszystkie zmienne wejściowe z uwzględnieniem wag cech."""
        return {
            var_name: var.fuzzify(crisp_inputs[var_name], apply_weight=apply_weight)
            for var_name, var in self.inputs.items()
        }

    def infer(
        self, fuzzified: dict[str, dict[str, float]]
    ) -> tuple[np.ndarray, list[tuple[FuzzyRule, float]]]:
        """
        Blok wnioskowania Mamdaniego:
        - agregacja przesłanek w regule operatorem min (T-norma),
        - implikacja Mamdaniego operatorem min (przycięcie funkcji wyjściowej),
        - agregacja wszystkich reguł operatorem max (S-norma).
        """
        aggregated = np.zeros_like(self.output.universe, dtype=float)
        activations: list[tuple[FuzzyRule, float]] = []

        for rule in self.rules:
            firing_strength = min(
                fuzzified[var_name][set_name]
                for var_name, set_name in rule.antecedents.items()
            )
            activations.append((rule, firing_strength))
            if firing_strength > 0.0:
                implied = np.minimum(firing_strength, self._output_mfs[rule.consequent])
                aggregated = np.maximum(aggregated, implied)

        return aggregated, activations

    def defuzzify(self, aggregated_mf: np.ndarray) -> float:
        """
        Blok wyostrzania metodą środka ciężkości (Centroid / Center of Gravity):
            y* = sum(y * mu(y)) / sum(mu(y))
        """
        denominator = float(np.sum(aggregated_mf))
        if denominator <= 1e-12:
            return 0.0
        numerator = float(np.sum(self.output.universe * aggregated_mf))
        return numerator / denominator

    def compute(
        self, crisp_inputs: dict[str, float], return_details: bool = False
    ) -> float | InferenceDetails:
        """Przeprowadza pełny cykl: rozmywanie -> wnioskowanie -> wyostrzanie."""
        fuzzified_weighted = self.fuzzify(crisp_inputs, apply_weight=True)
        aggregated, activations = self.infer(fuzzified_weighted)
        crisp_output = self.defuzzify(aggregated)

        if not return_details:
            return crisp_output

        fuzzified_unweighted = self.fuzzify(crisp_inputs, apply_weight=False)
        return InferenceDetails(
            crisp_inputs=dict(crisp_inputs),
            fuzzified_unweighted=fuzzified_unweighted,
            fuzzified_weighted=fuzzified_weighted,
            rule_activations=activations,
            aggregated_output=aggregated,
            crisp_output=crisp_output,
        )


def create_aeb_controller() -> FuzzyController:
    """
    Tworzy skonfigurowany sterownik rozmyty autonomicznego hamowania awaryjnego (AEB).

    Wagi cech wejściowych (realizowane przez przemnożenie funkcji przynależności):
    - odleglosc (od przeszkody): waga 1.00 — najwyższa waga
    - predkosc (pojazdu):        waga 0.65 — średnia waga
    - sliskosc (nawierzchni):    waga 0.35 — najmniejsza waga
    """
    odleglosc = LinguisticVariable(
        name="odleglosc",
        label="Odległość od przeszkody",
        unit="m",
        universe=np.linspace(0.0, 100.0, 401),
        weight=1.0,
        sets={
            "krytyczna": FuzzySet("krytyczna", gaussian_mf, {"mean": 0.0, "sigma": 13.0}),
            "bliska": FuzzySet("bliska", gaussian_mf, {"mean": 30.0, "sigma": 13.0}),
            "srednia": FuzzySet("srednia", gaussian_mf, {"mean": 62.0, "sigma": 12.0}),
            "bezpieczna": FuzzySet("bezpieczna", gaussian_mf, {"mean": 100.0, "sigma": 18.0}),
        },
    )

    predkosc = LinguisticVariable(
        name="predkosc",
        label="Prędkość pojazdu",
        unit="km/h",
        universe=np.linspace(0.0, 140.0, 401),
        weight=0.65,
        sets={
            "niska": FuzzySet("niska", gaussian_mf, {"mean": 0.0, "sigma": 28.0}),
            "srednia": FuzzySet("srednia", gaussian_mf, {"mean": 65.0, "sigma": 26.0}),
            "wysoka": FuzzySet("wysoka", gaussian_mf, {"mean": 140.0, "sigma": 32.0}),
        },
    )

    sliskosc = LinguisticVariable(
        name="sliskosc",
        label="Śliskość nawierzchni",
        unit="%",
        universe=np.linspace(0.0, 100.0, 401),
        weight=0.35,
        sets={
            "sucha": FuzzySet("sucha", gaussian_mf, {"mean": 0.0, "sigma": 22.0}),
            "mokra": FuzzySet("mokra", gaussian_mf, {"mean": 50.0, "sigma": 20.0}),
            "sliska": FuzzySet("sliska", gaussian_mf, {"mean": 100.0, "sigma": 22.0}),
        },
    )

    sila_hamowania = LinguisticVariable(
        name="sila_hamowania",
        label="Siła hamowania",
        unit="%",
        universe=np.linspace(0.0, 100.0, 501),
        weight=1.0,
        sets={
            "brak": FuzzySet("brak", gaussian_mf, {"mean": 0.0, "sigma": 6.0}),
            "lekkie": FuzzySet("lekkie", gaussian_mf, {"mean": 25.0, "sigma": 11.0}),
            "umiarkowane": FuzzySet("umiarkowane", gaussian_mf, {"mean": 50.0, "sigma": 11.0}),
            "silne": FuzzySet("silne", gaussian_mf, {"mean": 75.0, "sigma": 11.0}),
            "awaryjne": FuzzySet("awaryjne", gaussian_mf, {"mean": 100.0, "sigma": 6.0}),
        },
    )

    rules = [
        # --- Warstwa 1: reguły dominujące dla odległości (waga 1.0) ---
        FuzzyRule(
            {"odleglosc": "krytyczna"},
            "awaryjne",
            "Krytycznie mała odległość -> natychmiastowe hamowanie awaryjne",
        ),
        FuzzyRule(
            {"odleglosc": "bliska"},
            "silne",
            "Bliska odległość od przeszkody -> silne hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia"},
            "lekkie",
            "Średnia odległość od przeszkody -> lekkie wytracanie prędkości",
        ),
        FuzzyRule(
            {"odleglosc": "bezpieczna"},
            "brak",
            "Bezpieczna odległość od przeszkody -> brak potrzeby hamowania",
        ),
        # --- Warstwa 2: reguły z prędkością pojazdu (waga 0.65 — średnia) ---
        FuzzyRule(
            {"odleglosc": "krytyczna", "predkosc": "wysoka"},
            "awaryjne",
            "Krytyczna odległość i wysoka prędkość -> pełne hamowanie awaryjne",
        ),
        FuzzyRule(
            {"odleglosc": "krytyczna", "predkosc": "niska"},
            "umiarkowane",
            "Krytyczna odległość przy bardzo niskiej prędkości -> umiarkowane hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "bliska", "predkosc": "wysoka"},
            "awaryjne",
            "Bliska odległość i wysoka prędkość -> hamowanie awaryjne",
        ),
        FuzzyRule(
            {"odleglosc": "bliska", "predkosc": "srednia"},
            "silne",
            "Bliska odległość i średnia prędkość -> silne hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "bliska", "predkosc": "niska"},
            "lekkie",
            "Bliska odległość przy niskiej prędkości -> lekkie hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "predkosc": "wysoka"},
            "silne",
            "Średnia odległość przy wysokiej prędkości -> silne hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "predkosc": "srednia"},
            "umiarkowane",
            "Średnia odległość i średnia prędkość -> umiarkowane hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "predkosc": "niska"},
            "brak",
            "Średnia odległość przy niskiej prędkości -> brak hamowania",
        ),
        FuzzyRule(
            {"odleglosc": "bezpieczna", "predkosc": "wysoka"},
            "lekkie",
            "Bezpieczna odległość, ale wysoka prędkość -> lekkie hamowanie profilaktyczne",
        ),
        FuzzyRule(
            {"odleglosc": "bezpieczna", "predkosc": "srednia"},
            "brak",
            "Bezpieczna odległość i średnia prędkość -> brak hamowania",
        ),
        FuzzyRule(
            {"odleglosc": "bezpieczna", "predkosc": "niska"},
            "brak",
            "Bezpieczna odległość i niska prędkość -> brak hamowania",
        ),
        # --- Warstwa 3: reguły korygujące dla śliskości nawierzchni (waga 0.35 — najmniejsza) ---
        FuzzyRule(
            {"odleglosc": "bliska", "sliskosc": "sliska"},
            "awaryjne",
            "Bliska odległość na śliskiej nawierzchni -> wzmocnienie hamowania",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "sliskosc": "sliska"},
            "silne",
            "Średnia odległość na śliskiej nawierzchni -> wcześniejsze silne hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "sliskosc": "mokra"},
            "umiarkowane",
            "Średnia odległość na mokrej nawierzchni -> umiarkowane hamowanie",
        ),
        FuzzyRule(
            {"odleglosc": "srednia", "sliskosc": "sucha"},
            "brak",
            "Średnia odległość na suchej nawierzchni -> łagodniejsze wytracanie prędkości",
        ),
        FuzzyRule(
            {"odleglosc": "bezpieczna", "predkosc": "wysoka", "sliskosc": "sliska"},
            "umiarkowane",
            "Wysoka prędkość na śliskiej drodze nawet przy dużym dystansie -> umiarkowana korekta",
        ),
        FuzzyRule(
            {"odleglosc": "bliska", "predkosc": "niska", "sliskosc": "sucha"},
            "brak",
            "Niska prędkość na suchej drodze -> zmniejszenie agresywności hamowania",
        ),
        FuzzyRule(
            {"predkosc": "wysoka", "sliskosc": "sliska"},
            "silne",
            "Wysoka prędkość na śliskiej nawierzchni -> dodatkowy zapas hamowania",
        ),
        FuzzyRule(
            {"predkosc": "niska", "sliskosc": "sucha"},
            "brak",
            "Niska prędkość na suchej nawierzchni -> minimalizacja niepotrzebnego hamowania",
        ),
    ]

    return FuzzyController(
        inputs={
            "odleglosc": odleglosc,
            "predkosc": predkosc,
            "sliskosc": sliskosc,
        },
        output=sila_hamowania,
        rules=rules,
    )
