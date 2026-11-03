import random
import time


class NQueensGA:
    def __init__(self, n=8, pop_size=100, max_generations=10000, 
                 crossover_rate=0.8, mutation_rate=0.2):
        self.n = n
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def create_individual(self):
        """Tworzy losową konfigurację hetmanów."""
        return [random.randint(0, self.n - 1) for _ in range(self.n)]

    def count_conflicts(self, individual):
        """Liczba par hetmanów atakujących się nawzajem."""
        conflicts = 0
        n = self.n
        for i in range(n):
            for j in range(i + 1, n):
                # Konflikt w kolumnie
                if individual[i] == individual[j]:
                    conflicts += 1
                # Konflikt na przekątnej
                elif abs(individual[i] - individual[j]) == abs(i - j):
                    conflicts += 1
        return conflicts

    def crossover(self, parent1, parent2):
        """Krzyżowanie jednopunktowe tworzące dwójkę potomków."""
        point = random.randint(1, self.n - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def mutate(self, individual):
        """Mutacja: zmiana kolumny w losowym wierszu."""
        mutated = list(individual)
        row_idx = random.randint(0, self.n - 1)
        mutated[row_idx] = random.randint(0, self.n - 1)
        return mutated

    def solve(self):
        """Główna pętla algorytmu genetycznego."""
        # 1. Inicjalizacja populacji
        population = [self.create_individual() for _ in range(self.pop_size)]
        
        start_time = time.time()
        
        for generation in range(1, self.max_generations + 1):
            # 2. Ocena przystosowania
            scored_pop = [(ind, self.count_conflicts(ind)) for ind in population]
            scored_pop.sort(key=lambda x: x[1])
            
            best_ind, best_conflicts = scored_pop[0]
            
            # Warunek stopu – znalezienie rozwiązania
            if best_conflicts == 0:
                execution_time = time.time() - start_time
                return best_ind, generation, execution_time

            # 3. Tworzenie potomstwa (krzyżowanie i mutacja)
            children = []
            
            # Krzyżowanie
            num_crossovers = int(self.pop_size * self.crossover_rate) // 2
            for _ in range(num_crossovers):
                p1 = random.choice(population)
                p2 = random.choice(population)
                c1, c2 = self.crossover(p1, p2)
                children.extend([c1, c2])
                
            # Mutacja
            num_mutations = int(self.pop_size * self.mutation_rate)
            for _ in range(num_mutations):
                p = random.choice(population)
                children.append(self.mutate(p))
                
            # 4. Połączenie populacji i selekcja (elitarna)
            combined = population + children
            scored_combined = [(ind, self.count_conflicts(ind)) for ind in combined]
            scored_combined.sort(key=lambda x: x[1])
            
            # Zachowanie stałego rozmiaru populacji
            population = [ind for ind, _ in scored_combined[:self.pop_size]]

        execution_time = time.time() - start_time
        return scored_pop[0][0], self.max_generations, execution_time

    def print_board(self, individual):
        """Formatowanie i wyświetlanie szachownicy."""
        cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:self.n]
        print("   " + cols)
        for r in range(self.n):
            row_str = f"{r + 1:2d} "
            for c in range(self.n):
                if individual[r] == c:
                    row_str += "X"
                else:
                    row_str += "."
            print(row_str)


# Example execution
if __name__ == "__main__":
    for n in [4, 8, 16]:
        print(f"\n--- Problem N-hetmanów dla N = {n} ---")
        ga = NQueensGA(n=n, pop_size=150, max_generations=20000, 
                       crossover_rate=0.8, mutation_rate=0.3)
        solution, gen, elapsed = ga.solve()
        
        conflicts = ga.count_conflicts(solution)
        print(f"Wynik: {solution}")
        print(f"Liczba konfliktów: {conflicts}")
        print(f"Liczba generacji: {gen}")
        print(f"Czas wykonania: {elapsed:.4f} s\n")
        ga.print_board(solution)