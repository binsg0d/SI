import tkinter as tk
from tkinter import filedialog, messagebox
import math
import heapq
import itertools

class GraphPathfinder:
    def __init__(self, master):
        self.master = master
        self.master.title("Wyszukiwanie Ścieżki - A*, Dijkstra, Best First Search")
        
        # Zmienne stanu przechowujące strukturę grafu i elementy GUI
        self.vertices = {} # Słownik: id_wierzchołka -> (współrzędna_x, współrzędna_y)
        self.edges = {}    # Lista sąsiedztwa: id_wierzchołka -> [lista_id_sąsiadów]
        self.n = 0
        self.canvas_nodes = {} # Referencje do kółek narysowanych na Canvasie (do zmiany kolorów)
        self.canvas_edges = [] # Referencje do linii na Canvasie
        self.generator = None  # Obiekt generatora wyszukiwania, pozwala na asynchroniczne kroki (yield)
        self.running = False   # Flaga blokująca wielokrotne uruchomienie kroków
        
        self.setup_ui()
        
    def setup_ui(self):
        # [Kod UI pozostał bez zmian - układ okien i przycisków]
        control_frame = tk.Frame(self.master, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Button(control_frame, text="Wczytaj plik z grafem", command=self.load_file, width=25).pack(pady=5)
        
        tk.Label(control_frame, text="Algorytm:").pack(pady=(15, 0))
        self.algo_var = tk.StringVar(value="A*")
        tk.Radiobutton(control_frame, text="Best First Search (tylko h)", variable=self.algo_var, value="BFS").pack(anchor=tk.W)
        tk.Radiobutton(control_frame, text="Dijkstra (tylko g)", variable=self.algo_var, value="Dijkstra").pack(anchor=tk.W)
        tk.Radiobutton(control_frame, text="A* (g + h)", variable=self.algo_var, value="A*").pack(anchor=tk.W)
        
        tk.Label(control_frame, text="Węzeł startowy:").pack(pady=(15, 0))
        self.start_entry = tk.Entry(control_frame)
        self.start_entry.pack()
        
        tk.Label(control_frame, text="Węzeł końcowy:").pack(pady=(5, 0))
        self.end_entry = tk.Entry(control_frame)
        self.end_entry.pack()
        
        tk.Label(control_frame, text="Opóźnienie kroku (ms):").pack(pady=(15, 0))
        self.delay_entry = tk.Entry(control_frame)
        self.delay_entry.insert(0, "100")
        self.delay_entry.pack()
        
        tk.Button(control_frame, text="Uruchom algorytm", command=self.start_algorithm, width=25, bg="lightgreen").pack(pady=20)
        tk.Button(control_frame, text="Zresetuj kolory", command=self.reset_colors, width=25).pack(pady=5)
        
        self.result_label = tk.Label(control_frame, text="Koszt ścieżki: -", font=("Helvetica", 10, "bold"))
        self.result_label.pack(pady=20)
        
        self.canvas = tk.Canvas(self.master, width=600, height=600, bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

    def load_file(self):
        # Wybór i wczytanie struktury grafu. Struktura pliku:
        # Linia 1: liczba wierzchołków (n)
        # Linie 2 do n+1: współrzędne x y kolejnych wierzchołków
        # Linie n+2 do 2n+1: lista sąsiedztwa (liczba_sąsiadów sąsiad1 sąsiad2 ...)
        filepath = filedialog.askopenfilename(title="Wybierz plik z grafem", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        
        try:
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            self.n = int(lines[0])
            self.vertices = {}
            self.edges = {}
            
            # Parsowanie współrzędnych geometrycznych (potrzebne do rysowania i liczenia heurystyki)
            for i in range(1, self.n + 1):
                parts = lines[i].split()
                self.vertices[i] = (float(parts[0]), float(parts[1]))
                
            # Parsowanie list sąsiedztwa do słownika
            for i in range(1, self.n + 1):
                parts = lines[i + self.n].split()
                num_neighbors = int(parts[0])
                neighbors = [int(p) for p in parts[1:num_neighbors+1]]
                self.edges[i] = neighbors
                
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, "1")
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, str(self.n))
            
            self.draw_graph()
            messagebox.showinfo("Sukces", f"Pomyślnie wczytano graf ({self.n} wierzchołków).")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać pliku: {e}")

    def draw_graph(self):
        self.canvas.delete("all")
        self.canvas_nodes = {}
        self.canvas_edges = []
        
        if not self.vertices: return
        
        # Wyliczenie skrajnych współrzędnych, aby móc znormalizować (przeskalować) graf 
        # do wymiarów okna (600x600 px) z zachowaniem proporcji (izometrycznie)
        min_x = min(v[0] for v in self.vertices.values())
        max_x = max(v[0] for v in self.vertices.values())
        min_y = min(v[1] for v in self.vertices.values())
        max_y = max(v[1] for v in self.vertices.values())
        
        margin = 40
        width = int(self.canvas['width'])
        height = int(self.canvas['height'])
        
        def scale(x, y):
            range_x = (max_x - min_x) if max_x != min_x else 1
            range_y = (max_y - min_y) if max_y != min_y else 1
            
            # Współczynnik skalowania to minimum z osi X i Y, by graf nie został zdeformowany (rozciągnięty)
            scale_factor = min((width - 2*margin) / range_x, (height - 2*margin) / range_y)
            
            cx = margin + (x - min_x) * scale_factor
            cy = margin + (y - min_y) * scale_factor
            return cx, cy

        # Rysowanie krawędzi (zbiór drawn_edges eliminuje podwójne rysowanie krawędzi nieskierowanych u-v i v-u)
        drawn_edges = set()
        for u in self.edges:
            for v in self.edges[u]:
                if (u, v) not in drawn_edges and (v, u) not in drawn_edges:
                    ux, uy = scale(*self.vertices[u])
                    vx, vy = scale(*self.vertices[v])
                    line = self.canvas.create_line(ux, uy, vx, vy, fill="gray", width=2)
                    self.canvas_edges.append((u, v, line))
                    drawn_edges.add((u, v))
                    
        # Rysowanie węzłów (na wierzchu, aby zakrywały linie krawędzi)
        r = 12
        for u, (x, y) in self.vertices.items():
            cx, cy = scale(x, y)
            circle = self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="white", outline="black", width=2)
            text = self.canvas.create_text(cx, cy, text=str(u), font=("Arial", 8, "bold"))
            self.canvas_nodes[u] = circle

    def reset_colors(self):
        # Przywraca stan wizualny grafu do domyślnego przed nowym wyszukiwaniem
        for circle in self.canvas_nodes.values():
            self.canvas.itemconfig(circle, fill="white")
        for u, v, line in self.canvas_edges:
            self.canvas.itemconfig(line, fill="gray", width=2)
        self.result_label.config(text="Koszt ścieżki: -")

    def dist(self, u, v):
        # Oblicza odległość euklidesową (w linii prostej) za pomocą Twierdzenia Pitagorasa.
        # Pełni podwójną rolę: wagę (koszt) krawędzi oraz heurystykę h(n).
        ux, uy = self.vertices[u]
        vx, vy = self.vertices[v]
        return math.hypot(ux - vx, uy - vy)

    def search_algorithm(self, start, goal, algo):
        # Funkcja-generator obsługująca logikę wybranego algorytmu przeszukiwania
        counter = itertools.count() # Zapewnia unikalne ID dla kopca przy identycznym f(n)
        queue = []
        
        # Inicjalizacja kolejki priorytetowej (Kopca). Format krotki: (Priorytet f(n), licznik, id_wierzchołka)
        heapq.heappush(queue, (0, next(counter), start))
        
        # Słownik do odtwarzania ścieżki powrotnej: węzeł -> skąd do niego przyszliśmy
        came_from = {start: None}
        # Całkowity, faktyczny koszt dotarcia z punktu startowego do danego węzła ( g(n) )
        cost_so_far = {start: 0}
        
        # Zwracamy stan do interfejsu (wizualizacja), funkcja "zamarza" do czasu wywołania next()
        yield ('FRONTIER', start)
        
        while queue:
            # Pobieramy węzeł z najwyższym priorytetem (najmniejszą wartością f(n))
            _, _, current = heapq.heappop(queue)
            
            # Warunek końcowy - cel osiągnięty
            if current == goal:
                # Odtworzenie ścieżki iterując wstecznie przez słownik came_from
                path = []
                curr = goal
                while curr is not None:
                    path.append(curr)
                    curr = came_from[curr]
                path.reverse() # Odwrócenie na kolejność: Start -> Cel
                
                # Zwrócenie ostatecznego stanu
                yield ('PATH', path, cost_so_far[goal])
                return
                
            yield ('VISITING', current)
            
            # Ekspansja (relaksacja) sąsiadów bieżącego węzła
            for neighbor in self.edges[current]:
                # g(neighbor) = g(current) + waga_krawędzi
                new_cost = cost_so_far[current] + self.dist(current, neighbor)
                
                # Jeśli sąsiad jest nowy LUB znaleźliśmy do niego LEPSZĄ (tańszą) drogę
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    
                    # Obliczenie funkcji f(n) determinującej priorytet (kolejność zdejmowania ze stosu)
                    if algo == "BFS":
                        priority = self.dist(neighbor, goal) # Best First Search kieruje się tylko estymatą do celu
                    elif algo == "Dijkstra":
                        priority = new_cost # Dijkstra bada po kolei wg faktycznie przebytej drogi
                    elif algo == "A*":
                        priority = new_cost + self.dist(neighbor, goal) # A* łączy obie metody gwarantując optymalność i mniejszą przestrzeń
                        
                    # Dodanie sąsiada (lub uaktualnienie wagi nowym elementem w kolejce) do kolejki
                    heapq.heappush(queue, (priority, next(counter), neighbor))
                    yield ('FRONTIER', neighbor)

        # Kolejka pusta a celu nie osiągnięto = graf niespójny lub brak ścieżki
        yield ('NOT_FOUND', None, 0)

    def start_algorithm(self):
        # Walidacja danych wejściowych z kontrolek Tkinter przed startem
        if not self.vertices:
            messagebox.showwarning("Uwaga", "Najpierw wczytaj graf!")
            return
            
        try:
            start = int(self.start_entry.get())
            goal = int(self.end_entry.get())
            delay = int(self.delay_entry.get())
        except ValueError:
            messagebox.showerror("Błąd", "Wprowadź poprawne liczby całkowite dla startu, celu i opóźnienia.")
            return
            
        if start not in self.vertices or goal not in self.vertices:
            messagebox.showerror("Błąd", "Podane wierzchołki startowe lub końcowe nie istnieją w grafie.")
            return

        self.reset_colors()
        # Utworzenie i przechwycenie instancji obiektu generatora
        self.generator = self.search_algorithm(start, goal, self.algo_var.get())
        self.running = True
        
        # Uruchomienie "silnika" krokowego
        self.step_algorithm(delay)

    def step_algorithm(self, delay):
        if not self.running: return
        
        try:
            # Wznawia funkcję `search_algorithm`, odbiera od niej status i natychmiast ją znowu zamraża
            state = next(self.generator)
            action = state[0]
            
            # Mapowanie wygenerowanych zdarzeń algorytmu na efekty GUI
            if action == 'FRONTIER':
                node = state[1]
                self.canvas.itemconfig(self.canvas_nodes[node], fill="lightblue") # Węzeł wrzucony do kolejki
            elif action == 'VISITING':
                node = state[1]
                self.canvas.itemconfig(self.canvas_nodes[node], fill="orange") # Węzeł właśnie ściągnięty z kolejki
            elif action == 'PATH':
                path, cost = state[1], state[2]
                
                # Znaleziono optymalną ścieżkę - zaznacz węzły na zielono
                for node in path:
                    self.canvas.itemconfig(self.canvas_nodes[node], fill="lightgreen")
                    
                # Pogrub i pokoloruj na czerwono krawędzie składające się na wynikową ścieżkę
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    for edge_u, edge_v, line in self.canvas_edges:
                        if (edge_u == u and edge_v == v) or (edge_u == v and edge_v == u):
                            self.canvas.itemconfig(line, fill="red", width=4)
                
                self.result_label.config(text=f"Koszt ścieżki: {cost:.2f}")
                self.running = False
                return
            elif action == 'NOT_FOUND':
                self.result_label.config(text="Brak ścieżki do celu!")
                self.running = False
                return
                
            # Delegacja wywołania następnego kroku poprzez pętlę zdarzeń Tkintera po X milisekundach.
            # To sprawia, że interfejs wciąż nasłuchuje zdarzeń systemowych podczas animacji.
            self.master.after(delay, lambda: self.step_algorithm(delay))
            
        except StopIteration:
            # Obsługa błędu - generator w pełni skonsumowany
            self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphPathfinder(root)
    root.mainloop()