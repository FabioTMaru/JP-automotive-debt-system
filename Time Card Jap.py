import customtkinter as ctk
import sqlite3
from tkinter import messagebox, ttk
import calendar
from datetime import datetime

# Configurações iniciais
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DATABASE_NAME = 'empresa_gestao_v7.db'
MONTHS = [calendar.month_name[i] for i in range(1, 13)]
CURRENT_YEAR = datetime.now().year
YEARS = [str(CURRENT_YEAR + i) for i in range(-5, 6)]


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS funcoes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE)')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS funcionarios
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       nome
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       funcao_id
                       INTEGER
                       NOT
                       NULL,
                       salario_base
                       REAL
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       funcao_id
                   ) REFERENCES funcoes
                   (
                       id
                   )
                       )
                   ''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS custos_mensais
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       funcionario_id
                       INTEGER
                       NOT
                       NULL,
                       mes_num
                       INTEGER
                       NOT
                       NULL,
                       ano
                       INTEGER
                       NOT
                       NULL,
                       he
                       REAL
                       NOT
                       NULL
                       DEFAULT
                       0.0,
                       decimo_terceiro
                       REAL
                       NOT
                       NULL
                       DEFAULT
                       0.0,
                       insal_pf
                       REAL
                       NOT
                       NULL
                       DEFAULT
                       0.0,
                       ferias
                       REAL
                       NOT
                       NULL
                       DEFAULT
                       0.0,
                       custo_total
                       REAL
                       NOT
                       NULL,
                       UNIQUE
                   (
                       funcionario_id,
                       mes_num,
                       ano
                   ) ON CONFLICT REPLACE
                       )
                   ''')
    conn.commit()
    conn.close()


# --- Funções de Gestão de Cargos ---
def open_manage_functions_window():
    win = ctk.CTkToplevel(root)
    win.title("Gerenciar Funções/Cargos")
    win.geometry("300x400")
    win.attributes("-topmost", True)

    ctk.CTkLabel(win, text="Novo Cargo:").pack(pady=5)
    e_nome = ctk.CTkEntry(win)
    e_nome.pack(pady=5)

    def add_func():
        nome = e_nome.get().strip()
        if nome:
            try:
                conn = get_db_connection()
                conn.execute("INSERT INTO funcoes (nome) VALUES (?)", (nome,))
                conn.commit()
                conn.close()
                refresh_list()
                e_nome.delete(0, ctk.END)
            except:
                messagebox.showerror("Erro", "Cargo já existe.")

    ctk.CTkButton(win, text="Adicionar", command=add_func).pack(pady=5)
    listbox = ttk.Treeview(win, columns=("ID", "Nome"), show="headings")
    listbox.heading("ID", text="ID");
    listbox.heading("Nome", text="Nome")
    listbox.pack(expand=True, fill="both", padx=10, pady=10)

    def refresh_list():
        for i in listbox.get_children(): listbox.delete(i)
        conn = get_db_connection()
        for row in conn.execute("SELECT * FROM funcoes"): listbox.insert("", "end", values=(row[0], row[1]))
        conn.close()

    refresh_list()


# --- Cadastro de Funcionários ---
def open_register_employee_window():
    win = ctk.CTkToplevel(root)
    win.title("Novo Funcionário")
    win.geometry("400x400")
    win.attributes("-topmost", True)

    ctk.CTkLabel(win, text="Nome Completo:").pack(pady=5)
    e_nome = ctk.CTkEntry(win, width=250)
    e_nome.pack()

    ctk.CTkLabel(win, text="Cargo:").pack(pady=5)
    conn = get_db_connection()
    cargos = [r['nome'] for r in conn.execute("SELECT nome FROM funcoes").fetchall()]
    conn.close()
    cb_cargo = ctk.CTkComboBox(win, values=cargos, width=250)
    cb_cargo.pack()

    ctk.CTkLabel(win, text="Salário Base (R$):").pack(pady=5)
    e_salario = ctk.CTkEntry(win, width=250)
    e_salario.pack()

    def salvar():
        try:
            nome, cargo, sal = e_nome.get(), cb_cargo.get(), float(e_salario.get())
            conn = get_db_connection()
            f_id = conn.execute("SELECT id FROM funcoes WHERE nome=?", (cargo,)).fetchone()[0]
            conn.execute("INSERT INTO funcionarios (nome, funcao_id, salario_base) VALUES (?,?,?)", (nome, f_id, sal))
            conn.commit()
            conn.close()
            win.destroy()
            refresh_report_table(tree, label_total_geral, combobox_filtro_mes.get(), combobox_filtro_ano.get())
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    ctk.CTkButton(win, text="Salvar", command=salvar).pack(pady=20)


# --- Lançamento Mensal ---
def open_monthly_cost_window():
    sel = tree.focus()
    if not sel: return messagebox.showwarning("Aviso", "Selecione um funcionário.")

    val = tree.item(sel, 'values')
    f_id, f_nome = val[0], val[1]
    sal_base = float(val[3].replace("R$ ", "").replace(".", "").replace(",", "."))
    mes, ano = combobox_filtro_mes.get(), combobox_filtro_ano.get()

    win = ctk.CTkToplevel(root)
    win.title(f"Custos: {f_nome}")
    win.geometry("350x450")
    win.attributes("-topmost", True)

    fields = {}
    for label in ["Hora Extra (R$)", "13º Salário (R$)", "Insalubridade/PF (R$)"]:
        ctk.CTkLabel(win, text=label).pack(pady=2)
        e = ctk.CTkEntry(win, width=250)
        e.pack(pady=5)
        fields[label] = e

    def salvar_custo():
        try:
            he = float(fields["Hora Extra (R$)"].get() or 0)
            dec = float(fields["13º Salário (R$)"].get() or 0)
            insal = float(fields["Insalubridade/PF (R$)"].get() or 0)
            ferias = (sal_base + he) / 12
            total = sal_base + he + dec + insal + ferias

            conn = get_db_connection()
            conn.execute(
                """INSERT INTO custos_mensais (funcionario_id, mes_num, ano, he, decimo_terceiro, insal_pf, ferias,
                                               custo_total)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                         (f_id, MONTHS.index(mes)+1, int(ano), he, dec, insal, ferias, total))
            conn.commit()
            conn.close()
            win.destroy()
            refresh_report_table(tree, label_total_geral, mes, ano)
        except: messagebox.showerror("Erro", "Valores inválidos.")

    ctk.CTkButton(win, text="Salvar", command=salvar_custo).pack(pady=20)

def refresh_report_table(tree, label_total_geral, mes_nome, ano_str):
    for item in tree.get_children(): tree.delete(item)
    mes_num = MONTHS.index(mes_nome) + 1

    conn = get_db_connection()
    query = """
            SELECT f.id, f.nome, func.nome as cargo, f.salario_base, cm.he, cm.decimo_terceiro, cm.insal_pf, cm.ferias
            FROM funcionarios f
                     JOIN funcoes func ON f.funcao_id = func.id
                     LEFT JOIN custos_mensais cm ON f.id = cm.funcionario_id AND cm.mes_num = ? AND cm.ano = ? \
            """
    rows = conn.execute(query, (mes_num, int(ano_str))).fetchall()
    conn.close()

    total_geral = 0
    for r in rows:
        he, dec, insal, fer = r[4] or 0, r[5] or 0, r[6] or 0, r[7] or 0
        total_func = r[3] + he + dec + insal + fer
        total_geral += total_func
        tree.insert("", "end", values=(r[0], r[1], r[2], f"R$ {r[3]:,.2f}", f"R$ {he:,.2f}", f"R$ {dec:,.2f}", f"R$ {insal:,.2f}", f"R$ {fer:,.2f}", f"R$ {total_func:,.2f}"))

    label_total_geral.configure(text=f"Total da Folha: R$ {total_geral:,.2f}")

# --- Janela Principal ---
root = ctk.CTk()
root.title("Sistema Gestão de Custos - Divenci CF")
root.geometry("1100x600")

create_tables()

# Barra Superior de Filtros
frame_topo = ctk.CTkFrame(root)
frame_topo.pack(fill="x", padx=10, pady=10)

combobox_filtro_mes = ctk.CTkComboBox(frame_topo, values=MONTHS)
combobox_filtro_mes.set(MONTHS[datetime.now().month-1])
combobox_filtro_mes.pack(side="left", padx=5)

combobox_filtro_ano = ctk.CTkComboBox(frame_topo, values=YEARS)
combobox_filtro_ano.set(str(CURRENT_YEAR))
combobox_filtro_ano.pack(side="left", padx=5)

ctk.CTkButton(frame_topo, text="Atualizar", command=lambda: refresh_report_table(tree, label_total_geral, combobox_filtro_mes.get(), combobox_filtro_ano.get())).pack(side="left", padx=5)

# Tabela principal
cols = ("ID", "Nome", "Cargo", "Base", "HE", "13º", "Insal.", "Férias", "Total")
tree = ttk.Treeview(root, columns=cols, show="headings")
for col in cols: tree.heading(col, text=col); tree.column(col, width=100)
tree.pack(expand=True, fill="both", padx=10)

label_total_geral = ctk.CTkLabel(root, text="Total da Folha: R$ 0,00", font=("Roboto", 16, "bold"))
label_total_geral.pack(pady=10)

# Botões de Ação
frame_btns = ctk.CTkFrame(root)
frame_btns.pack(fill="x", padx=10, pady=10)

ctk.CTkButton(frame_btns, text="Gerenciar Cargos", command=open_manage_functions_window).pack(side="left", padx=5)
ctk.CTkButton(frame_btns, text="Cadastrar Funcionário", command=open_register_employee_window).pack(side="left", padx=5)
ctk.CTkButton(frame_btns, text="Lançar Custos Mensais", command=open_monthly_cost_window, fg_color="green").pack(side="left", padx=5)

root.mainloop()
