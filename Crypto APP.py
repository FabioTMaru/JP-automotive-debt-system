import customtkinter as ctk
import requests
import sqlite3
from threading import Thread
from tkinter import messagebox


# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('crypto_vision_2026.db')
    cursor = conn.cursor()
    # Tabela de Usuários
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          login
                          TEXT
                          UNIQUE,
                          senha
                          TEXT
                      )''')
    # Tabela de Carteira
    cursor.execute('''CREATE TABLE IF NOT EXISTS carteira
    (
        user_id
        INTEGER,
        moeda_id
        TEXT,
        quantidade
        REAL
        DEFAULT
        0,
        FOREIGN
        KEY
                      (
        user_id
                      ) REFERENCES usuarios
                      (
                          id
                      ))''')
    conn.commit()
    conn.close()


class CryptoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Crypto Vision v4.0 - 2026")
        self.geometry("1000x650")
        ctk.set_appearance_mode("dark")

        # Estados
        self.user_id = None
        self.user_nome = ""
        self.watchlist = {"bitcoin": "BTC", "ethereum": "ETH"}
        self.price_labels = {}

        # Sua API Key da CoinGecko (Opcional, mas recomendado em 2026)
        # Obtenha em: https://www.coingecko.com
        self.api_key = ""

        init_db()
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    # --- TELAS ---
    def show_login_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, width=350, height=450)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="CRYPTO LOGIN", font=("Roboto", 24, "bold")).pack(pady=30)
        self.entry_user = ctk.CTkEntry(frame, width=250, placeholder_text="Usuário")
        self.entry_user.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(frame, width=250, placeholder_text="Senha", show="*")
        self.entry_pass.pack(pady=10)

        ctk.CTkButton(frame, text="Entrar", width=250, command=self.login).pack(pady=20)
        ctk.CTkButton(frame, text="Criar Conta", width=250, fg_color="transparent", border_width=1,
                      command=self.register_user).pack()

    def show_dashboard(self):
        self.clear_screen()

        # Sidebar
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(sidebar, text=f"Olá, {self.user_nome}", font=("Roboto", 16, "bold")).pack(pady=20)
        ctk.CTkButton(sidebar, text="Dashboard", command=self.show_dashboard).pack(pady=10, padx=10)
        ctk.CTkButton(sidebar, text="Minha Carteira", command=self.show_wallet_screen).pack(pady=10, padx=10)
        ctk.CTkButton(sidebar, text="Sair", fg_color="#aa3333", command=self.show_login_screen).pack(side="bottom",
                                                                                                     pady=20)

        # Main
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.main_frame, text="Mercado em Tempo Real", font=("Roboto", 28, "bold")).pack(anchor="w")

        # Adicionar Moeda
        add_frame = ctk.CTkFrame(self.main_frame)
        add_frame.pack(fill="x", pady=20)
        self.entry_add = ctk.CTkEntry(add_frame, placeholder_text="ID da moeda (ex: solana, cardano, polkadot)")
        self.entry_add.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        ctk.CTkButton(add_frame, text="Adicionar", width=120, command=self.add_crypto).pack(side="right", padx=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Watchlist Ativa")
        self.scroll_frame.pack(fill="both", expand=True)

        self.render_cards()
        self.update_prices_thread()

    def show_wallet_screen(self):
        # Aqui você implementaria a lógica de saldo usando a tabela 'carteira'
        messagebox.showinfo("Carteira", "Módulo de Saldo e Transações em desenvolvimento para v4.1!")

    # --- LÓGICA ---
    def login(self):
        u, s = self.entry_user.get(), self.entry_pass.get()
        conn = sqlite3.connect('crypto_vision_2026.db')
        res = conn.execute("SELECT id, login FROM usuarios WHERE login=? AND senha=?", (u, s)).fetchone()
        conn.close()
        if res:
            self.user_id, self.user_nome = res
            self.show_dashboard()
        else:
            messagebox.showerror("Erro", "Dados inválidos.")

    def register_user(self):
        u, s = self.entry_user.get(), self.entry_pass.get()
        if len(u) < 3: return messagebox.showwarning("Aviso", "Usuário muito curto.")
        try:
            conn = sqlite3.connect('crypto_vision_2026.db')
            conn.execute("INSERT INTO usuarios (login, senha) VALUES (?, ?)", (u, s))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Conta criada! Faça login.")
        except:
            messagebox.showerror("Erro", "Usuário já existe.")

    def add_crypto(self):
        cid = self.entry_add.get().lower().strip()
        if cid and cid not in self.watchlist:
            self.watchlist[cid] = cid.upper()[:4]
            self.render_cards()
            self.entry_add.delete(0, 'end')

    def render_cards(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.price_labels = {}
        for cid, sym in self.watchlist.items():
            f = ctk.CTkFrame(self.scroll_frame)
            f.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(f, text=sym, width=100, font=("bold", 16)).pack(side="left", padx=20, pady=10)
            lbl = ctk.CTkLabel(f, text="Carregando...", font=("Roboto", 16))
            lbl.pack(side="right", padx=30)
            self.price_labels[cid] = lbl

    def update_prices_thread(self):
        def run():
            if not self.user_id: return
            try:
                ids = ",".join(self.watchlist.keys())
                url = f"https://api.coingecko.com{ids}&vs_currencies=usd"
                headers = {"x-cg-demo-api-key": self.api_key} if self.api_key else {}

                resp = requests.get(url, headers=headers, timeout=10)

                if resp.status_code == 429:  # Rate Limit
                    for l in self.price_labels.values(): l.configure(text="Limite atingido (60s)", text_color="orange")
                    self.after(60000, self.update_prices_thread)
                    return

                data = resp.json()
                for cid, label in self.price_labels.items():
                    if cid in data:
                        p = data[cid]['usd']
                        label.configure(text=f"$ {p:,.2f}", text_color="white")
                    else:
                        label.configure(text="Não encontrado", text_color="red")
            except:
                for l in self.price_labels.values(): l.configure(text="Erro Conexão", text_color="red")

            self.after(30000, self.update_prices_thread)

        Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = CryptoApp()
    app.mainloop()
