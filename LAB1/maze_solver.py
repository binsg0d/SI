import sys
import time
import os
from collections import deque

# Słownik definiujący dostępne ruchy dla każdego znaku
# Reprezentacja: (dy, dx) gdzie y to wiersz, a x to kolumna
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

MOVES = {
    '┼': (UP, DOWN, LEFT, RIGHT),
    '┐': (DOWN, LEFT),
    '┤': (UP, DOWN, LEFT),
    '╵': (UP,),
    '│': (UP, DOWN),
    '┘': (UP, LEFT),
    '┴': (UP, LEFT, RIGHT),
    '╷': (DOWN,),
    '─': (LEFT, RIGHT),
    '└': (UP, RIGHT),
    '├': (UP, DOWN, RIGHT),
    '╴': (LEFT,),
    ' ': (),
    '┌': (DOWN, RIGHT),
    '┬': (DOWN, LEFT, RIGHT),
    '╶': (RIGHT,)
}

# Kolory dla terminala
C_RED = '\033[1;31m'
C_GREEN = '\033[1;32m'
C_YELLOW = '\033[1;33m'
C_BLUE = '\033[1;34m'
C_DEFAULT = '\033[0m'

def load_map(filepath):
    """Wczytuje mapę, uzupełnia spacjami krótsze linie i zwraca siatkę 2D."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\r\n') for line in f]
    
    if not lines:
        print("Mapa jest pusta.")
        sys.exit(1)
        
    width = max(len(line) for line in lines)
    grid = [line.ljust(width, ' ') for line in lines]
    return grid, width, len(grid)

def render_map(grid, start, end, visited, frontier_set):
    """Odrysowuje mapę w terminalu z odpowiednimi kolorami."""
    # Przesunięcie kursora na początek terminala (zapobiega migotaniu)
    sys.stdout.write('\033[H')
    
    for y, row in enumerate(grid):
        line_out = []
        for x, char in enumerate(row):
            pos = (y, x)
            if pos == start:
                color = C_RED
            elif pos == end:
                color = C_BLUE
            elif pos in visited:
                color = C_GREEN
            elif pos in frontier_set:
                color = C_YELLOW
            else:
                color = C_DEFAULT
            
            line_out.append(f"{color}{char}{C_DEFAULT}")
        sys.stdout.write("".join(line_out) + "\n")
    sys.stdout.flush()

def search_path(grid, width, height, start, end, algo):
    """Przeszukuje labirynt algorytmem BFS (FIFO) lub DFS (LIFO)."""
    frontier = deque([start])
    frontier_set = {start}
    visited = set()
    steps = 0
    found = False

    # Czyszczenie ekranu przed animacją
    os.system('cls' if os.name == 'nt' else 'clear')

    while frontier:
        render_map(grid, start, end, visited, frontier_set)
        time.sleep(0.1)  # Czas trwania jednej klatki (100 ms)

        # BFS używa kolejki FIFO (popleft), DFS stosu LIFO (pop)
        current = frontier.popleft() if algo == 'BFS' else frontier.pop()
        frontier_set.remove(current)
        steps += 1

        if current == end:
            found = True
            visited.add(current)
            render_map(grid, start, end, visited, frontier_set)
            break

        visited.add(current)
        cy, cx = current
        current_char = grid[cy][cx]

        # Sprawdzanie dostępnych kierunków z obecnego pola
        for dy, dx in MOVES.get(current_char, ()):
            ny, nx = cy + dy, cx + dx

            # Sprawdzenie, czy nie wychodzimy poza mapę
            if 0 <= ny < height and 0 <= nx < width:
                # Sprawdzenie, czy pole do którego wchodzimy, pozwala na ruch "powrotny"
                # (np. idąc w dół, nowe pole musi pozwalać na ruch w górę)
                opposite_move = (-dy, -dx)
                next_char = grid[ny][nx]
                
                if opposite_move in MOVES.get(next_char, ()):
                    neighbor = (ny, nx)
                    if neighbor not in visited and neighbor not in frontier_set:
                        frontier.append(neighbor)
                        frontier_set.add(neighbor)

    return found, steps

def main():
    # Aktywacja kodów ANSI na starszych Windowsach
    if os.name == 'nt':
        os.system('')

    if len(sys.argv) < 2:
        print("Użycie: python maze_solver.py <ścieżka_do_mapy>")
        sys.exit(1)

    filepath = sys.argv[1]
    try:
        grid, width, height = load_map(filepath)
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {filepath}")
        sys.exit(1)

    # Wyświetlanie wstępnej mapy
    for row in grid:
        print(row)
        
    print(f"\nWykryto mapę o rozmiarze: {width}x{height} (kolumny x wiersze)")
    print("Współrzędne podajemy od 0.")
    
    try:
        sx = int(input(f"Start X (kolumna 0-{width-1}): "))
        sy = int(input(f"Start Y (wiersz 0-{height-1}): "))
        ex = int(input(f"Koniec X (kolumna 0-{width-1}): "))
        ey = int(input(f"Koniec Y (wiersz 0-{height-1}): "))
    except ValueError:
        print("Błąd: Współrzędne muszą być liczbami całkowitymi.")
        sys.exit(1)

    algo = input("Wybierz algorytm (BFS / DFS): ").strip().upper()
    if algo not in ['BFS', 'DFS']:
        print("Błąd: Nieznany algorytm. Wybierz 'BFS' lub 'DFS'.")
        sys.exit(1)

    start = (sy, sx)
    end = (ey, ex)

    # Zabezpieczenie przed polem pustym na starcie/końcu
    if grid[sy][sx] == ' ' or grid[ey][ex] == ' ':
        print("Uwaga: Wybrano puste pole jako start lub koniec. Może to natychmiast przerwać wyszukiwanie.")
        time.sleep(2)

    found, steps = search_path(grid, width, height, start, end, algo)

    print("\n" + "="*30)
    if found:
        print(f"Sukces! Znaleziono ścieżkę algorytmem {algo}.")
    else:
        print(f"Brak przejścia! Algorytm {algo} nie odnalazł ścieżki.")
    print(f"Ilość wykonanych kroków (odwiedzonych węzłów): {steps}")
    print("="*30)

if __name__ == "__main__":
    main()