import math
import tkinter as tk


class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kółko i Krzyżyk – Minimax")
        self.root.minsize(320, 420)
        self.root.bind("<Configure>", self.on_window_resize)

        # Górny pasek ustawień
        ctrl = tk.Frame(root, padx=10, pady=8)
        ctrl.pack()

        tk.Label(ctrl, text="Rozmiar:").pack(side=tk.LEFT)
        self.size_var = tk.IntVar(value=3)
        tk.Spinbox(
            ctrl,
            from_=3,
            to=6,
            width=3,
            textvariable=self.size_var,
            command=lambda: self.depth_var.set(9 if self.size_var.get() == 3 else 3),
        ).pack(side=tk.LEFT, padx=(2, 10))

        tk.Label(ctrl, text="Głębokość:").pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=9)
        tk.Spinbox(ctrl, from_=1, to=9, width=3, textvariable=self.depth_var).pack(
            side=tk.LEFT, padx=(2, 10)
        )

        tk.Label(ctrl, text="Zaczyna:").pack(side=tk.LEFT)
        self.starter_var = tk.StringVar(value="Użytkownik")
        tk.OptionMenu(ctrl, self.starter_var, "Użytkownik", "Komputer").pack(
            side=tk.LEFT, padx=(2, 10)
        )

        tk.Button(ctrl, text="Nowa gra", command=self.new_game).pack(side=tk.LEFT)
        tk.Button(ctrl, text="Resetuj", command=self.reset_game).pack(side=tk.LEFT)

        self.status = tk.Label(root, text="", font=("Arial", 11, "bold"), pady=4)
        self.status.pack()

        self.board_frame = tk.Frame(root, padx=10, pady=10)
        self.board_frame.pack(fill=tk.BOTH, expand=True)

        self.ai_after_id = None
        self.new_game()
        self.root.after_idle(self.on_window_resize)

    def new_game(self):
        if self.ai_after_id is not None:
            self.root.after_cancel(self.ai_after_id)
            self.ai_after_id = None

        self.N = max(3, self.size_var.get())
        self.max_depth = max(1, self.depth_var.get())
        user_starts = self.starter_var.get() == "Użytkownik"

        self.HUMAN, self.AI = ("X", "O") if user_starts else ("O", "X")
        self.board = [[""] * self.N for _ in range(self.N)]
        self.game_over = False

        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.buttons = []
        for r in range(self.N):
            row_btns = []
            for c in range(self.N):
                btn = tk.Button(
                    self.board_frame,
                    text="",
                    width=4,
                    height=2,
                    font=("Arial", 16, "bold"),
                    command=lambda r=r, c=c: self.on_click(r, c),
                )
                btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                row_btns.append(btn)
            self.buttons.append(row_btns)

        for i in range(self.N):
            self.board_frame.grid_columnconfigure(i, weight=1)
            self.board_frame.grid_rowconfigure(i, weight=1)

        if user_starts:
            self.status.config(text=f"Twój ruch ({self.HUMAN})")
        else:
            self.status.config(text="Komputer myśli...")
            self.ai_after_id = self.root.after(100, self.ai_move)

        self.root.after_idle(self.on_window_resize)

    def on_window_resize(self, event=None):
        if not hasattr(self, "buttons") or not self.buttons:
            return

        n = self.N
        frame_w = max(self.board_frame.winfo_width(), 200)
        frame_h = max(self.board_frame.winfo_height(), 200)

        cell = max(32, min((frame_w - 20) // n, (frame_h - 20) // n))
        font_size = max(12, min(32, int(cell * 0.45)))

        for r in range(n):
            for c in range(n):
                btn = self.buttons[r][c]
                btn.config(
                    width=max(2, cell // 12),
                    height=max(1, cell // 22),
                    font=("Arial", font_size, "bold"),
                )

    def reset_game(self):
        self.new_game()

    def on_click(self, r, c):
        if self.game_over or self.board[r][c] != "":
            return
        self.make_move(r, c, self.HUMAN)
        if not self.game_over:
            self.status.config(text="Komputer myśli...")
            if self.ai_after_id is not None:
                self.root.after_cancel(self.ai_after_id)
            self.ai_after_id = self.root.after(50, self.ai_move)

    def ai_move(self):
        self.ai_after_id = None
        if self.game_over:
            return
        _, move = self.minimax(self.board, 0, True)
        if move:
            self.make_move(move[0], move[1], self.AI)
        if not self.game_over:
            self.status.config(text=f"Twój ruch ({self.HUMAN})")

    def make_move(self, r, c, player):
        self.board[r][c] = player
        self.buttons[r][c].config(
            text=player, fg="#1f77b4" if player == "X" else "#d62728"
        )

        res = self.check_winner(self.board)
        if res:
            self.game_over = True
            messages = {
                "DRAW": "Remis!",
                self.HUMAN: "Wygrałeś!",
                self.AI: "Wygrał komputer!",
            }
            self.status.config(text=messages[res])

    def lines(self, b):
        n = self.N
        return (
            b
            + [[b[r][c] for r in range(n)] for c in range(n)]
            + [[b[i][i] for i in range(n)], [b[i][n - 1 - i] for i in range(n)]]
        )

    def check_winner(self, b):
        for line in self.lines(b):
            if line[0] != "" and len(set(line)) == 1:
                return line[0]
        return "DRAW" if all(cell != "" for row in b for cell in row) else None

    def evaluate(self, b):
        score = 0
        for line in self.lines(b):
            if self.HUMAN not in line and self.AI in line:
                score += 10 ** line.count(self.AI)
            elif self.AI not in line and self.HUMAN in line:
                score -= 10 ** line.count(self.HUMAN)
        return score

    def minimax(self, b, depth, is_max):
        winner = self.check_winner(b)
        if winner == self.AI:
            return 10 ** (self.N + 1) - depth, None
        if winner == self.HUMAN:
            return -(10 ** (self.N + 1)) + depth, None
        if winner == "DRAW":
            return 0, None
        if depth >= self.max_depth:
            return self.evaluate(b), None

        best_score = -math.inf if is_max else math.inf
        best_move = None

        for r in range(self.N):
            for c in range(self.N):
                if b[r][c] == "":
                    b[r][c] = self.AI if is_max else self.HUMAN
                    score, _ = self.minimax(b, depth + 1, not is_max)
                    b[r][c] = ""
                    if (is_max and score > best_score) or (
                        not is_max and score < best_score
                    ):
                        best_score, best_move = score, (r, c)

        return best_score, best_move


if __name__ == "__main__":
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()