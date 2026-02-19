import sqlite3
import customtkinter as ctk
from tkinter import messagebox

# Grade: 32 a 72 (de 2 em 2) + Especial
GRADE_FIXA = [str(i) for i in range(32, 74, 2)] + ["Especial"]


def init_db():
    conn = sqlite3.connect('sistema_confeccao_v10.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS modelagens (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tecidos
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          id_modelagem
                          INTEGER,
                          nome_tecido
                          TEXT
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS larguras
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          id_tecido
                          INTEGER,
                          valor_largura
                          REAL
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS grades_consumo
    (
        id_largura
        INTEGER,
        tamanho
        TEXT,
        consumo
        REAL,
        PRIMARY
        KEY
                      (
        id_largura,
        tamanho
                      ))''')
    conn.commit()
    conn.close()


class AppCorte(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Corte Profissional - V10")
        self.geometry("1200x900")

        self.tab_control = ctk.CTkTabview(self)
        self.tab_control.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_cadastro = self.tab_control.add("Cadastro de Modelagens")
        self.tab_producao = self.tab_control.add("Ordem de Corte")

        self.id_modelo_atual = None
        self.setup_aba_cadastro()
        self.setup_aba_producao()
        self.carregar_lista_lateral()

    # ================= ABA 1: CADASTRO =================
    def setup_aba_cadastro(self):
        self.tab_cadastro.grid_columnconfigure(1, weight=1)
        self.tab_cadastro.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self.tab_cadastro, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        ctk.CTkButton(self.sidebar, text="+ Novo Molde", fg_color="#2caf5d", command=self.janela_nova_modelagem).pack(
            pady=10, padx=20)

        ctk.CTkLabel(self.sidebar, text="Pesquisar Molde:", font=("Arial", 12)).pack(padx=20, anchor="w")
        self.ent_pesquisa = ctk.CTkEntry(self.sidebar, placeholder_text="Digite o nome...")
        self.ent_pesquisa.pack(pady=5, padx=20, fill="x")
        self.ent_pesquisa.bind("<KeyRelease>", lambda e: self.carregar_lista_lateral())

        self.scroll_modelos = ctk.CTkScrollableFrame(self.sidebar, label_text="Lista Alfabética")
        self.scroll_modelos.pack(expand=True, fill="both", padx=10, pady=5)

        self.btn_excluir_molde = ctk.CTkButton(self.sidebar, text="Excluir Molde Selecionado", fg_color="#e74c3c",
                                               command=self.excluir_modelagem)
        self.btn_excluir_molde.pack(pady=10, padx=20)

        self.main_cad_frame = ctk.CTkFrame(self.tab_cadastro)
        self.main_cad_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.lbl_nome_cad = ctk.CTkLabel(self.main_cad_frame, text="Selecione um molde lateralmente",
                                         font=("Arial", 20, "bold"))
        self.lbl_nome_cad.pack(pady=10)

        self.btn_add_tecido = ctk.CTkButton(self.main_cad_frame, text="+ Adicionar Novo Tecido/Componente",
                                            fg_color="#f39c12", command=self.add_tecido)
        self.tabview_tecidos = None

    def carregar_lista_lateral(self):
        for w in self.scroll_modelos.winfo_children(): w.destroy()
        termo = self.ent_pesquisa.get().lower()
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        query = "SELECT id, nome FROM modelagens WHERE lower(nome) LIKE ? ORDER BY nome ASC"
        modelos = conn.execute(query, (f'%{termo}%',)).fetchall()
        for mid, nome in modelos:
            cor = "#3b8ed0" if mid == self.id_modelo_atual else "transparent"
            btn = ctk.CTkButton(self.scroll_modelos, text=nome, fg_color=cor, anchor="w",
                                command=lambda n=nome, i=mid: self.abrir_modelagem(n, i))
            btn.pack(fill="x", pady=2)
        conn.close()
        self.carregar_combo_moldes_producao()

    def abrir_modelagem(self, nome, mid):
        self.id_modelo_atual = mid
        self.lbl_nome_cad.configure(text=f"Modelagem: {nome}")
        self.btn_add_tecido.pack(pady=5)
        self.carregar_lista_lateral()

        if self.tabview_tecidos: self.tabview_tecidos.destroy()
        self.tabview_tecidos = ctk.CTkTabview(self.main_cad_frame)
        self.tabview_tecidos.pack(expand=True, fill="both", pady=10)

        conn = sqlite3.connect('sistema_confeccao_v10.db')
        tecidos = conn.execute("SELECT id, nome_tecido FROM tecidos WHERE id_modelagem=?", (mid,)).fetchall()
        for tid, tnome in tecidos:
            aba_t = self.tabview_tecidos.add(tnome)
            self.construir_aba_tecido(aba_t, tid)
        conn.close()

    def construir_aba_tecido(self, aba_t, id_tecido):
        f_ctrl = ctk.CTkFrame(aba_t, fg_color="transparent")
        f_ctrl.pack(fill="x", pady=5)
        ctk.CTkButton(f_ctrl, text="+ Add Largura para este Tecido", fg_color="#3498db",
                      command=lambda: self.add_largura(id_tecido)).pack(side="left", padx=5)
        ctk.CTkButton(f_ctrl, text="Excluir Tecido", fg_color="#e74c3c",
                      command=lambda: self.excluir_tecido(id_tecido)).pack(side="right", padx=5)

        tab_larguras = ctk.CTkTabview(aba_t)
        tab_larguras.pack(expand=True, fill="both", pady=5)
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        larguras = conn.execute("SELECT id, valor_largura FROM larguras WHERE id_tecido=? ORDER BY valor_largura ASC",
                                (id_tecido,)).fetchall()
        for lid, lval in larguras:
            aba_l = tab_larguras.add(f"{lval}m")
            self.construir_grade_consumo(aba_l, lid)
        conn.close()

    def construir_grade_consumo(self, frame, lid):
        # Frame de topo para ações da largura
        f_acoes_l = ctk.CTkFrame(frame, fg_color="transparent")
        f_acoes_l.pack(fill="x", pady=5)

        # BOTÃO NOVO: APAGAR LARGURA
        ctk.CTkButton(f_acoes_l, text="Excluir esta Largura", fg_color="#c0392b", hover_color="#962d22",
                      height=24, command=lambda: self.excluir_largura(lid)).pack(side="right", padx=10)

        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(expand=True, fill="both", padx=5, pady=5)
        entradas = {}
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        for i, tam in enumerate(GRADE_FIXA):
            r, c = i // 3, (i % 3) * 2
            ctk.CTkLabel(scroll, text=f"Tam {tam}:").grid(row=r, column=c, padx=5, pady=5, sticky="e")
            ent = ctk.CTkEntry(scroll, width=90)
            ent.grid(row=r, column=c + 1, padx=5, pady=5)
            entradas[tam] = ent
            res = conn.execute("SELECT consumo FROM grades_consumo WHERE id_largura=? AND tamanho=?",
                               (lid, tam)).fetchone()
            if res:
                # Pegar o valor real da tupla (índice 0)
                ent.insert(0, str(res[0]))
        conn.close()

        ctk.CTkButton(frame, text="SALVAR GRADE", fg_color="#2caf5d",
                      command=lambda: self.salvar_grade(lid, entradas)).pack(pady=5)

    def excluir_largura(self, lid):
        if messagebox.askyesno("Excluir Largura",
                               "Tem certeza que deseja apagar esta largura e todos os consumos dela?"):
            conn = sqlite3.connect('sistema_confeccao_v10.db')
            conn.execute("DELETE FROM larguras WHERE id=?", (lid,))
            conn.execute("DELETE FROM grades_consumo WHERE id_largura=?", (lid,))
            conn.commit()
            conn.close()
            # Recarregar interface
            self.abrir_modelagem(self.lbl_nome_cad.cget("text").replace("Modelagem: ", ""), self.id_modelo_atual)

    # ================= ABA 2: PRODUÇÃO =================
    def setup_aba_producao(self):
        self.frame_top_prod = ctk.CTkFrame(self.tab_producao)
        self.frame_top_prod.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(self.frame_top_prod, text="Molde:").grid(row=0, column=0, padx=10)
        self.combo_molde_prod = ctk.CTkComboBox(self.frame_top_prod, values=[], width=250)
        self.combo_molde_prod.grid(row=0, column=1, padx=10)
        ctk.CTkButton(self.frame_top_prod, text="Carregar Grade", command=self.gerar_ordem).grid(row=0, column=2,
                                                                                                 padx=10)

        self.scroll_prod = ctk.CTkScrollableFrame(self.tab_producao, label_text="Dados do Corte")
        self.scroll_prod.pack(expand=True, fill="both", padx=20)
        self.frame_res = ctk.CTkFrame(self.tab_producao)
        self.frame_res.pack(fill="x", padx=20, pady=10)
        self.lbl_res_pecas = ctk.CTkLabel(self.frame_res, text="Total Peças: 0", font=("Arial", 16))
        self.lbl_res_pecas.pack()
        self.lbl_res_metros = ctk.CTkLabel(self.frame_res, text="Consumo: ---", font=("Arial", 18, "bold"),
                                           text_color="#3498db", wraplength=1000)
        self.lbl_res_metros.pack()

    def carregar_combo_moldes_producao(self):
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        modelos = [r[0] for r in conn.execute("SELECT nome FROM modelagens ORDER BY nome ASC").fetchall()]
        self.combo_molde_prod.configure(values=modelos)
        conn.close()

    def gerar_ordem(self):
        for w in self.scroll_prod.winfo_children(): w.destroy()
        nm = self.combo_molde_prod.get()
        if not nm: return
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        mid_row = conn.execute("SELECT id FROM modelagens WHERE nome=?", (nm,)).fetchone()
        if not mid_row: return
        mid = mid_row[0]

        tecidos = conn.execute("SELECT id, nome_tecido FROM tecidos WHERE id_modelagem=?", (mid,)).fetchall()
        self.seletores_largura = {}
        f_seletores = ctk.CTkFrame(self.scroll_prod, fg_color="transparent")
        f_seletores.pack(fill="x", pady=10)
        for tid, tnome in tecidos:
            f_item = ctk.CTkFrame(f_seletores)
            f_item.pack(side="left", padx=10)
            ctk.CTkLabel(f_item, text=f"Largura {tnome}").pack()
            larg_lista = [str(r[0]) for r in
                          conn.execute("SELECT valor_largura FROM larguras WHERE id_tecido=?", (tid,)).fetchall()]
            cb = ctk.CTkComboBox(f_item, values=larg_lista, width=120)
            cb.pack()
            if larg_lista: cb.set(larg_lista[0])
            self.seletores_largura[tid] = (cb, tnome)
        conn.close()

        f_grade = ctk.CTkFrame(self.scroll_prod)
        f_grade.pack(fill="both", expand=True, pady=10)
        self.entradas_qtd = {}
        for i, tam in enumerate(GRADE_FIXA):
            r, c = i // 4, (i % 4) * 2
            ctk.CTkLabel(f_grade, text=f"Tam {tam}:").grid(row=r, column=c, padx=10, pady=8, sticky="e")
            ent = ctk.CTkEntry(f_grade, width=80)
            ent.grid(row=r, column=c + 1, padx=10, pady=8)
            ent.bind("<KeyRelease>", lambda e: self.calc_prod())
            self.entradas_qtd[tam] = ent

    def calc_prod(self):
        total_pecas = 0
        totais_metros = {}
        erros = []
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        for tam, ent in self.entradas_qtd.items():
            val = ent.get().strip()
            if val.isdigit(): total_pecas += int(val)
        for tid, (cb, tnome) in self.seletores_largura.items():
            larg_val = cb.get()
            if not larg_val: continue
            lid_row = conn.execute("SELECT id FROM larguras WHERE id_tecido=? AND valor_largura=?",
                                   (tid, float(larg_val))).fetchone()
            if not lid_row: continue
            lid = lid_row[0]

            cons_map = {t: v for t, v in conn.execute("SELECT tamanho, consumo FROM grades_consumo WHERE id_largura=?",
                                                      (lid,)).fetchall()}
            tot_tec = 0.0
            for tam, ent in self.entradas_qtd.items():
                val = ent.get().strip()
                if val.isdigit() and int(val) > 0:
                    cons_u = cons_map.get(tam, 0)
                    if cons_u == 0:
                        erros.append(f"{tnome}({tam})")
                    else:
                        tot_tec += int(val) * cons_u
            totais_metros[tnome] = tot_tec
        conn.close()
        if erros:
            self.lbl_res_metros.configure(text=f"ERRO: Sem consumo em: {', '.join(set(erros))}", text_color="red")
        else:
            txt = " | ".join([f"{n}: {v:.2f}m" for n, v in totais_metros.items()])
            self.lbl_res_metros.configure(text=f"Consumo: {txt}", text_color="#3498db")
        self.lbl_res_pecas.configure(text=f"Total Peças: {total_pecas}")

    # ================= ACOES DE DADOS =================
    def janela_nova_modelagem(self):
        n = ctk.CTkInputDialog(text="Nome do Molde:", title="Novo").get_input()
        if n:
            conn = sqlite3.connect('sistema_confeccao_v10.db')
            try:
                c = conn.cursor()
                c.execute("INSERT INTO modelagens (nome) VALUES (?)", (n,))
                mid = c.lastrowid
                c.execute("INSERT INTO tecidos (id_modelagem, nome_tecido) VALUES (?, ?)", (mid, "Principal"))
                conn.commit()
                self.carregar_lista_lateral()
            except:
                messagebox.showerror("Erro", "Molde já existe.")
            conn.close()

    def excluir_modelagem(self):
        if not self.id_modelo_atual: return
        if messagebox.askyesno("Excluir", "Deseja apagar este molde?"):
            conn = sqlite3.connect('sistema_confeccao_v10.db')
            conn.execute("DELETE FROM modelagens WHERE id=?", (self.id_modelo_atual,))
            conn.commit()
            conn.close()
            self.id_modelo_atual = None
            self.carregar_lista_lateral()
            if self.tabview_tecidos: self.tabview_tecidos.destroy()

    def add_tecido(self):
        n = ctk.CTkInputDialog(text="Nome do Tecido:", title="Novo").get_input()
        if n and self.id_modelo_atual:
            conn = sqlite3.connect('sistema_confeccao_v10.db')
            conn.execute("INSERT INTO tecidos (id_modelagem, nome_tecido) VALUES (?, ?)", (self.id_modelo_atual, n))
            conn.commit()
            conn.close()
            self.abrir_modelagem(self.lbl_nome_cad.cget("text").replace("Modelagem: ", ""), self.id_modelo_atual)

    def add_largura(self, tid):
        v = ctk.CTkInputDialog(text="Largura (ex: 1.40):", title="Add").get_input()
        if v:
            try:
                conn = sqlite3.connect('sistema_confeccao_v10.db')
                conn.execute("INSERT INTO larguras (id_tecido, valor_largura) VALUES (?, ?)",
                             (tid, float(v.replace(',', '.'))))
                conn.commit()
                conn.close()
                self.abrir_modelagem(self.lbl_nome_cad.cget("text").replace("Modelagem: ", ""), self.id_modelo_atual)
            except:
                messagebox.showerror("Erro", "Valor inválido.")

    def salvar_grade(self, lid, entradas):
        conn = sqlite3.connect('sistema_confeccao_v10.db')
        try:
            for t, e in entradas.items():
                val = e.get().strip().replace(',', '.')
                if val: conn.execute(
                    "INSERT OR REPLACE INTO grades_consumo (id_largura, tamanho, consumo) VALUES (?, ?, ?)",
                    (lid, t, float(val)))
            conn.commit()
            messagebox.showinfo("OK", "Salvo!")
        except:
            messagebox.showerror("Erro", "Valor inválido.")
        conn.close()

    def excluir_tecido(self, tid):
        if messagebox.askyesno("Excluir", "Apagar tecido?"):
            conn = sqlite3.connect('sistema_confeccao_v10.db')
            conn.execute("DELETE FROM tecidos WHERE id=?", (tid,))
            conn.commit()
            conn.close()
            self.abrir_modelagem(self.lbl_nome_cad.cget("text").replace("Modelagem: ", ""), self.id_modelo_atual)


if __name__ == "__main__":
    init_db()
    AppCorte().mainloop()
