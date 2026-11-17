import random

ITEMS = [
    ("Laptop", 3.0, 2000),
    ("Namiot", 4.0, 1000),
    ("Kamera", 1.0, 1500),
    ("Apteczka", 0.5, 300),
    ("Buty", 1.5, 500),
    ("Jedzenie", 2.0, 600),
    ("Latarka", 0.3, 150),
    ("Powerbank", 0.7, 250),
    ("Kurtka", 1.0, 400),
    ("Scyzoryk", 0.2, 200),
    ("Woda", 2.0, 100),
    ("Mapa", 0.1, 50),
    ("Książka", 0.5, 300),
    ("Czapka", 0.2, 100),
    ("Rękawiczki", 0.3, 150),
]

N = len(ITEMS)
CAPACITY = 6.0
MAX_TOTAL_VALUE = sum(value for _, _, value in ITEMS)

POP_SIZE = 100
MAX_ITER = 1000
CROSSOVER_RATIO = 0.80
MUTATION_RATIO = 0.20


def fitness(individual):
    weight = sum(items[1] * gene for items, gene in zip(ITEMS, individual))
    value = sum(items[2] * gene for items, gene in zip(ITEMS, individual))

    if weight > CAPACITY:
        return 999_999 + weight

    return MAX_TOTAL_VALUE - value


def generate_population(size):
    return [[random.randint(0, 1) for _ in range(N)] for _ in range(size)]


def crossover(parent_a, parent_b):
    cut = random.randint(1, N - 1)
    child_a = parent_a[:cut] + parent_b[cut:]
    child_b = parent_b[:cut] + parent_a[cut:]
    return child_a, child_b


def mutate(individual):
    mutated = individual.copy()
    idx = random.randint(0, N - 1)
    mutated[idx] = random.randint(0, 1)
    return mutated


population = generate_population(POP_SIZE)

for _ in range(MAX_ITER):
    new_generation = []

    for _ in range(int(POP_SIZE * CROSSOVER_RATIO / 2)):
        parent_a, parent_b = random.sample(population, 2)
        new_generation.extend(crossover(parent_a, parent_b))

    for _ in range(int(POP_SIZE * MUTATION_RATIO)):
        new_generation.append(mutate(random.choice(population)))

    population.extend(new_generation)
    population.sort(key=fitness)
    population = population[:POP_SIZE]

    if fitness(population[0]) == 0:
        break

best = population[0]
final_weight = sum(item[1] * gene for item, gene in zip(ITEMS, best))
final_value = sum(item[2] * gene for item, gene in zip(ITEMS, best))

print(f"Algorytm zakończył po {MAX_ITER} iteracjach.")
print(f"Najlepszy wektor: {best}")
print(f"Waga: {final_weight} / {CAPACITY}")
print(f"Wartość: {final_value}")
print("Spakowane przedmioty:")

for index, (_, weight, value) in enumerate(ITEMS):
    if best[index]:
        print(f" - {ITEMS[index][0]} (waga: {weight}, wartość: {value})")