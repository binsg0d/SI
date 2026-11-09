import random

# --- DANE WEJŚCIOWE PROBLEMU ---
# Lista przedmiotów: (Nazwa, Waga, Wartość)
ITEMS = [
    ("Laptop", 3.0, 2000),
    ("Namiot", 4.0, 1000),
    ("Kamera", 1.0, 1500),
    ("Apteczka", 0.5, 300),
    ("Buty górskie", 1.5, 500),
    ("Zapas jedzenia", 2.0, 600),
    ("Latarka", 0.3, 150),
    ("Powerbank", 0.7, 250),
    ("Kurtka", 1.0, 400),
    ("Scyzoryk", 0.2, 200)
]
KNAPSACK_CAPACITY = 7.0   # Maksymalny udźwig plecaka

# --- PARAMETRY ALGORYTMU GENETYCZNEGO ---
POP_SIZE = 50             # Rozmiar populacji
MAX_ITER = 200            # Limit iteracji
CROSSOVER_RATE = 0.8      # Prawdopodobieństwo krzyżowania
MUTATION_RATE = 0.1       # Prawdopodobieństwo mutacji pojedynczego genu

# --- FUNKCJE POMOCNICZE ---

def create_individual():
    """Tworzy losowego osobnika (wektor 0 i 1)."""
    return [random.choice([0, 1]) for _ in range(len(ITEMS))]

def fitness(individual):
    """Zwraca łączną wartość przedmiotów, jeśli waga mieści się w plecaku. Inaczej 0."""
    total_weight = 0
    total_value = 0
    
    for i, is_selected in enumerate(individual):
        if is_selected:
            total_weight += ITEMS[i][1]
            total_value += ITEMS[i][2]
            
    # Jeżeli waga przekracza pojemność, osobnik jest 'martwy' (wartość 0)
    if total_weight > KNAPSACK_CAPACITY:
        return 0
    return total_value

def print_solution(individual):
    """Wypisuje spakowane przedmioty i ich parametry."""
    total_w = 0
    total_v = 0
    print("Spakowane przedmioty:")
    for i, is_selected in enumerate(individual):
        if is_selected:
            name, weight, value = ITEMS[i]
            print(f" - {name} (Waga: {weight}, Wartość: {value})")
            total_w += weight
            total_v += value
    print(f"\nŁączna waga: {total_w} / {KNAPSACK_CAPACITY}")
    print(f"Łączna wartość: {total_v}")

# --- GŁÓWNA PĘTLA ALGORYTMU ---

def genetic_algorithm():
    # 1. Inicjalizacja populacji
    population = [create_individual() for _ in range(POP_SIZE)]
    
    for iteration in range(MAX_ITER):
        # 2. Ocena i sortowanie (tym razem malejąco, bo szukamy maksimum wartości)
        population.sort(key=fitness, reverse=True)
        
        # 3. Selekcja i rozród (tworzymy nowe pokolenie)
        children = []
        num_crossovers = int((CROSSOVER_RATE * POP_SIZE) / 2)
        
        for _ in range(num_crossovers):
            # Wybieramy rodziców z lepszej połowy populacji (selekcja turniejowa uproszczona)
            parent1 = random.choice(population[:POP_SIZE//2])
            parent2 = random.choice(population[:POP_SIZE//2])
            
            # Krzyżowanie jednopunktowe
            cross_point = random.randint(1, len(ITEMS) - 1)
            child1 = parent1[:cross_point] + parent2[cross_point:]
            child2 = parent2[:cross_point] + parent1[cross_point:]
            children.extend([child1, child2])
            
        population.extend(children)
        
        # 4. Mutacja (Bit-flip - zamiana 0 na 1 lub 1 na 0)
        for i in range(len(population)):
            for j in range(len(ITEMS)):
                if random.random() < MUTATION_RATE:
                    population[i][j] = 1 - population[i][j] # Odwrócenie bitu
                    
        # 5. Odcięcie najsłabszych osobników (przywrócenie rozmiaru POP_SIZE)
        population.sort(key=fitness, reverse=True)
        population = population[:POP_SIZE]

    # Zwracamy najlepszego osobnika z ostatniej iteracji
    return population[0]

# --- URUCHOMIENIE ---
best_individual = genetic_algorithm()
print_solution(best_individual)