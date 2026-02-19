import customtkinter as ctk
import sqlite3
from tkinter import messagebox, ttk, filedialog
import calendar
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# Configurações iniciais
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DATABASE_NAME = 'empresa_gestao_v11.db'
MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
CURRENT_YEAR = 2026
YEARS_FILTER = [str(CURRENT_YEAR + i) for i in range(-5, 6)]
DAYS = [str(i).zfill(2) for i in range(1, 32)]
YEARS_ADMISSION = [str(i) for i in range(CURRENT_YEAR - 40, CURRENT_YEAR + 2)]

# --- Funções de Suporte ---
def f_moeda(valor):
    return f"R$ {valor:.2f}".replace(".", ",")

def limpar_moeda(texto):
    if not texto: return 0.0
    res = str(texto).replace("R$ ", "").replace(",", ".")
    try: return float(res)
    except: return 0.0

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS funcoes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS funcionarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, funcao_id INTEGER NOT NULL, salario_base REAL NOT NULL, data_admissao TEXT, FOREIGN KEY(funcao_id) REFERENCES funcoes(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS custos_mensais (id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario_id INTEGER NOT NULL, mes_num INTEGER NOT NULL, ano INTEGER NOT NULL, salario_pago REAL DEFAULT 0, he REAL DEFAULT 0, decimo_terceiro REAL DEFAULT 0, insal_pf REAL DEFAULT 0, ferias REAL DEFAULT 0, fgts REAL DEFAULT 0, pcmso REAL DEFAULT 0, seguro REAL DEFAULT 0, cafe REAL DEFAULT 0, convenio REAL DEFAULT 0, almoco REAL DEFAULT 0, vt REAL DEFAULT 0, cesta REAL DEFAULT 0, UNIQUE(funcionario_id, mes_num, ano) ON CONFLICT REPLACE)''')
    conn.commit(); conn.close()

def criar_seletor_data(parent, data_string=None):
    frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(pady=5)
    if data_string and "/" in data_string:
        p = data_string.split("/"); d, m, a = p[0], p[1], p[2]
    else:
        d, m, a = "01", MONTHS[datetime.now().month-1], str(CURRENT_YEAR)
    cb_dia = ctk.CTkComboBox(frame, values=DAYS, width=70); cb_dia.set(d); cb_dia.pack(side="left", padx=2)
    cb_mes = ctk.CTkComboBox(frame, values=MONTHS, width=110); cb_mes.set(m); cb_mes.pack(side="left", padx=2)
    cb_ano = ctk.CTkComboBox(frame, values=YEARS_ADMISSION, width=85); cb_ano.set(a); cb_ano.pack(side="left", padx=2)
    return cb_dia, cb_mes, cb_ano

# --- Exportação ---
def export_excel():
    mes, ano = combobox_filtro_mes.get(), combobox_filtro_ano.get()
    data = [tree.item(i)['values'] for i in tree.get_children()]
    if not data: return messagebox.showwarning("Aviso", "Sem dados.")
    cols = ["Nome", "Cargo", "Sal. Base", "HE", "13º", "Insal.", "Férias", "Total Bruto", "FGTS", "PCMSO", "Seguro", "Café", "Conv.", "Almoço", "VT", "Cesta", "Total Desc.", "Líquido"]
    df = pd.DataFrame(data, columns=cols)
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Folha_{mes}_{ano}.xlsx")
    if path: df.to_excel(path, index=False); messagebox.showinfo("Sucesso", "Excel Gerado!")

def export_pdf():
    mes, ano = combobox_filtro_mes.get(), combobox_filtro_ano.get()
    data = [["Nome", "Cargo", "Base", "HE", "13º", "Ins.", "Fer.", "Bruto", "FGTS", "PCM", "Seg.", "Café", "Con.", "Alm.", "VT", "Ces.", "Desc.", "Liq."]]
    for i in tree.get_children(): data.append([str(x).replace("R$ ", "") for x in tree.item(i)['values']])
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Relatorio_{mes}_{ano}.pdf")
    if not path: return
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm)
    styles = getSampleStyleSheet()
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.darkblue),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
    doc.build([Paragraph(f"Gestão RH - {mes}/{ano}", styles['Title']), Spacer(1,12), t])
    messagebox.showinfo("Sucesso", "PDF Gerado!")

# --- Funções de Janela ---
def open_manage_functions_window():
    win = ctk.CTkToplevel(root); win.title("Cargos"); win.geometry("350x450"); win.attributes("-topmost", True)
    ctk.CTkLabel(win, text="Novo Cargo:").pack(pady=10)
    e_n = ctk.CTkEntry(win, width=200); e_n.pack(pady=5)
    def add():
        if e_n.get():
            conn = get_db_connection(); conn.execute("INSERT INTO funcoes (nome) VALUES (?)", (e_n.get(),)); conn.commit(); conn.close(); e_n.delete(0, 'end'); refresh()
    ctk.CTkButton(win, text="Adicionar", command=add).pack(pady=5)
    t = ttk.Treeview(win, columns=("Nome"), show="headings"); t.heading("Nome", text="Nome"); t.pack(padx=10, pady=10, fill="both", expand=True)
    def refresh():
        for i in t.get_children(): t.delete(i)
        conn = get_db_connection()
        for r in conn.execute("SELECT nome FROM funcoes ORDER BY nome"): t.insert("", "end", values=(r['nome'],))
        conn.close()
    refresh()

def open_reg():
    win = ctk.CTkToplevel(root); win.title("Novo Funcionário"); win.geometry("450x550"); win.attributes("-topmost", True)
    ctk.CTkLabel(win, text="Nome:").pack(); e_n = ctk.CTkEntry(win, width=250); e_n.pack()
    dia, mes, ano = criar_seletor_data(win)
    ctk.CTkLabel(win, text="Salário:").pack(); e_s = ctk.CTkEntry(win, width=250); e_s.pack()
    conn = get_db_connection(); cgs = [r['nome'] for r in conn.execute("SELECT nome FROM funcoes ORDER BY nome")]; conn.close()
    cb = ctk.CTkComboBox(win, values=cgs, width=250); cb.pack(pady=10)
    def sv():
        try:
            dt = f"{dia.get()}/{mes.get()}/{ano.get()}"
            conn = get_db_connection(); f_id = conn.execute("SELECT id FROM funcoes WHERE nome=?",(cb.get(),)).fetchone()['id']
            conn.execute("INSERT INTO funcionarios (nome, funcao_id, salario_base, data_admissao) VALUES (?,?,?,?)",(e_n.get(), f_id, float(e_s.get().replace(",", ".")), dt))
            conn.commit(); conn.close(); win.destroy(); refresh_report_table()
        except: messagebox.showerror("Erro", "Dados inválidos.")
    ctk.CTkButton(win, text="Salvar", command=sv).pack(pady=10)

def open_edit_employee_window():
    sel = tree.focus()
    if not sel: return messagebox.showwarning("Aviso", "Selecione um funcionário.")
    nome_f = tree.item(sel, 'values')[0]
    conn = get_db_connection()
    func = conn.execute("SELECT f.*, fu.nome as cargo_nome FROM funcionarios f JOIN funcoes fu ON f.funcao_id = fu.id WHERE f.nome=?", (nome_f,)).fetchone()
    cargos = [r['nome'] for r in conn.execute("SELECT nome FROM funcoes ORDER BY nome").fetchall()]
    conn.close()
    win = ctk.CTkToplevel(root); win.title(f"Editar: {nome_f}"); win.geometry("450x600"); win.attributes("-topmost", True)
    ctk.CTkLabel(win, text="Nome:").pack(); e_n = ctk.CTkEntry(win, width=250); e_n.insert(0, func['nome']); e_n.pack()
    dia, mes, ano = criar_seletor_data(win, func['data_admissao'])
    ctk.CTkLabel(win, text="Salário Base:").pack(); e_s = ctk.CTkEntry(win, width=250); e_s.insert(0, str(func['salario_base'])); e_s.pack()
    cb_c = ctk.CTkComboBox(win, values=cargos, width=250); cb_c.set(func['cargo_nome']); cb_c.pack(pady=15)
    def update():
        conn = get_db_connection(); c_id = conn.execute("SELECT id FROM funcoes WHERE nome=?", (cb_c.get(),)).fetchone()['id']
        conn.execute("UPDATE funcionarios SET nome=?, data_admissao=?, salario_base=?, funcao_id=? WHERE id=?", (e_n.get(), f"{dia.get()}/{mes.get()}/{ano.get()}", float(e_s.get().replace(",",".")), c_id, func['id']))
        conn.commit(); conn.close(); win.destroy(); refresh_report_table()
    ctk.CTkButton(win, text="Atualizar", fg_color="#E67E22", command=update).pack(pady=10)

def open_earnings_window():
    sel = tree.focus()
    if not sel: return
    f_nome = tree.item(sel, 'values')[0]
    mes_n, ano_n = MONTHS.index(combobox_filtro_mes.get()) + 1, int(combobox_filtro_ano.get())
    conn = get_db_connection(); f_d = conn.execute("SELECT id, salario_base FROM funcionarios WHERE nome=?", (f_nome,)).fetchone()
    ex = conn.execute("SELECT * FROM custos_mensais WHERE funcionario_id=? AND mes_num=? AND ano=?", (f_d['id'], mes_n, ano_n)).fetchone(); conn.close()
    sal_mes = ex['salario_pago'] if ex and ex['salario_pago'] > 0 else f_d['salario_base']
    win = ctk.CTkToplevel(root); win.title("Rendimentos"); win.geometry("350x550"); win.attributes("-topmost", True)
    fields = {}
    ctk.CTkLabel(win, text="Salário Base do Mês:").pack(); e_sal = ctk.CTkEntry(win, width=200); e_sal.insert(0, str(sal_mes).replace(".",",")); e_sal.pack()
    for l, k, col in [("Hora Extra","he","he"), ("13º","dec","decimo_terceiro"), ("Insal.","insal","insal_pf"), ("Férias","fer","ferias")]:
        ctk.CTkLabel(win, text=l).pack(); e = ctk.CTkEntry(win, width=200); e.pack(); fields[k] = e
        if ex: e.insert(0, str(ex[col]).replace(".",","))
    def sv():
        conn = get_db_connection(); conn.execute("INSERT INTO custos_mensais (funcionario_id, mes_num, ano, salario_pago, he, decimo_terceiro, insal_pf, ferias) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(funcionario_id, mes_num, ano) DO UPDATE SET salario_pago=excluded.salario_pago, he=excluded.he, decimo_terceiro=excluded.decimo_terceiro, insal_pf=excluded.insal_pf, ferias=excluded.ferias", (f_d['id'], mes_n, ano_n, float(e_sal.get().replace(",",".")), *[float(e.get().replace(",",".") or 0) for e in fields.values()])); conn.commit(); conn.close(); win.destroy(); refresh_report_table()
    ctk.CTkButton(win, text="Salvar", fg_color="green", command=sv).pack(pady=10)

def open_deductions_window():
    sel = tree.focus()
    if not sel: return
    vals = tree.item(sel, 'values'); f_nome = vals[0]; bruto = limpar_moeda(vals[7])
    if bruto <= 0: return messagebox.showwarning("Aviso", "Lance rendimentos primeiro.")
    mes_n, ano_n = MONTHS.index(combobox_filtro_mes.get()) + 1, int(combobox_filtro_ano.get())
    mes_a, ano_a = (12, ano_n-1) if mes_n == 1 else (mes_n-1, ano_n)
    conn = get_db_connection(); f_id = conn.execute("SELECT id FROM funcionarios WHERE nome=?", (f_nome,)).fetchone()['id']
    ex = conn.execute("SELECT * FROM custos_mensais WHERE funcionario_id=? AND mes_num=? AND ano=?", (f_id, mes_n, ano_n)).fetchone()
    ant = conn.execute("SELECT pcmso, seguro, cafe FROM custos_mensais WHERE funcionario_id=? AND mes_num=? AND ano=?", (f_id, mes_a, ano_a)).fetchone(); conn.close()
    win = ctk.CTkToplevel(root); win.title("Descontos"); win.geometry("420x680"); win.attributes("-topmost", True)
    fgts = bruto * 0.08
    f_i = ctk.CTkFrame(win, fg_color="#333"); f_i.pack(pady=10, fill="x", padx=10); ctk.CTkLabel(f_i, text=f"FGTS (8%): {f_moeda(fgts)}", text_color="yellow").pack()
    scroll = ctk.CTkScrollableFrame(win, width=380, height=450); scroll.pack()
    fields = {}
    items = [("FGTS","fgts"), ("PCMSO","pcmso"), ("Seguro","seguro"), ("Café","cafe"), ("Convênio","convenio"), ("Almoço","almoco"), ("VT","vt"), ("Cesta","cesta")]
    for l, k in items:
        ctk.CTkLabel(scroll, text=l).pack(); e = ctk.CTkEntry(scroll, width=200); e.pack(); fields[k] = e
        if ex: e.insert(0, str(ex[k]).replace(".",","))
        elif k == "fgts": e.insert(0, f"{fgts:.2f}".replace(".",","))
        elif k in ["pcmso","seguro","cafe"] and ant: e.insert(0, str(ant[k]).replace(".",","))
    def sv():
        conn = get_db_connection(); conn.execute(f"INSERT INTO custos_mensais (funcionario_id, mes_num, ano, fgts, pcmso, seguro, cafe, convenio, almoco, vt, cesta) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(funcionario_id, mes_num, ano) DO UPDATE SET fgts=excluded.fgts, pcmso=excluded.pcmso, seguro=excluded.seguro, cafe=excluded.cafe, convenio=excluded.convenio, almoco=excluded.almoco, vt=excluded.vt, cesta=excluded.cesta", (f_id, mes_n, ano_n, *[float(e.get().replace(",",".") or 0) for e in fields.values()])); conn.commit(); conn.close(); win.destroy(); refresh_report_table()
    ctk.CTkButton(win, text="Salvar", fg_color="#A83232", command=sv).pack(pady=10)

def refresh_report_table():
    for i in tree.get_children(): tree.delete(i)
    mes_n, ano_n = combobox_filtro_mes.get(), combobox_filtro_ano.get()
    lbl_periodo.configure(text=f"Período: {mes_n} / {ano_n}")
    conn = get_db_connection()
    query = "SELECT f.nome, func.nome as cargo, f.salario_base as sal_cad, cm.* FROM funcionarios f JOIN funcoes func ON f.funcao_id = func.id LEFT JOIN custos_mensais cm ON f.id = cm.funcionario_id AND cm.mes_num = ? AND cm.ano = ? ORDER BY f.nome ASC"
    rows = conn.execute(query, (MONTHS.index(mes_n)+1, int(ano_n))).fetchall(); conn.close()
    tb, td, tl = 0, 0, 0
    for r in rows:
        sal = r['salario_pago'] if (r['salario_pago'] and r['salario_pago'] > 0) else r['sal_cad']
        bruto = sal + (r['he'] or 0) + (r['decimo_terceiro'] or 0) + (r['insal_pf'] or 0) + (r['ferias'] or 0)
        desc = (r['fgts'] or 0) + (r['pcmso'] or 0) + (r['seguro'] or 0) + (r['cafe'] or 0) + (r['convenio'] or 0) + (r['almoco'] or 0) + (r['vt'] or 0) + (r['cesta'] or 0)
        liq = bruto - desc; tb+=bruto; td+=desc; tl+=liq
        tree.insert("", "end", values=(r['nome'], r['cargo'], f_moeda(sal), f_moeda(r['he'] or 0), f_moeda(r['decimo_terceiro'] or 0), f_moeda(r['insal_pf'] or 0), f_moeda(r['ferias'] or 0), f_moeda(bruto), f_moeda(r['fgts'] or 0), f_moeda(r['pcmso'] or 0), f_moeda(r['seguro'] or 0), f_moeda(r['cafe'] or 0), f_moeda(r['convenio'] or 0), f_moeda(r['almoco'] or 0), f_moeda(r['vt'] or 0), f_moeda(r['cesta'] or 0), f_moeda(desc), f_moeda(liq)))
    lbl_bruto.configure(text=f"Total Bruto: {f_moeda(tb)}"); lbl_desc.configure(text=f"Total Descontos: {f_moeda(td)}"); lbl_liq.configure(text=f"Líquido Geral: {f_moeda(tl)}")

# --- UI Principal ---
root = ctk.CTk(); root.title("Divenci CF - Gestão RH 2026"); root.geometry("1550x900"); create_tables()
f_t = ctk.CTkFrame(root); f_t.pack(fill="x", padx=10, pady=10)
combobox_filtro_mes = ctk.CTkComboBox(f_t, values=MONTHS); combobox_filtro_mes.set(MONTHS[datetime.now().month-1]); combobox_filtro_mes.pack(side="left", padx=5)
combobox_filtro_ano = ctk.CTkComboBox(f_t, values=YEARS_FILTER); combobox_filtro_ano.set(str(CURRENT_YEAR)); combobox_filtro_ano.pack(side="left", padx=5)
ctk.CTkButton(f_t, text="Filtrar", width=80, command=refresh_report_table).pack(side="left", padx=5)
ctk.CTkButton(f_t, text="📄 PDF", fg_color="#C0392B", width=80, command=export_pdf).pack(side="left", padx=5)
ctk.CTkButton(f_t, text="📥 Excel", fg_color="#27AE60", width=80, command=export_excel).pack(side="left", padx=5)
lbl_periodo = ctk.CTkLabel(f_t, text="", font=("Roboto", 16, "bold"), text_color="white", fg_color="#C0392B", corner_radius=5, width=200, height=35); lbl_periodo.pack(side="left", expand=True)
ctk.CTkButton(f_t, text="⚙️ Cargos", fg_color="#555", width=100, command=open_manage_functions_window).pack(side="right", padx=5)

cols = ("Nome", "Cargo", "Sal. Base", "HE", "13º", "Insal.", "Férias", "Total Bruto", "FGTS", "PCMSO", "Seguro", "Café", "Conv.", "Almoço", "VT", "Cesta", "Total Desc.", "Líquido")
tree = ttk.Treeview(root, columns=cols, show="headings")
for c in cols: tree.heading(c, text=c); tree.column(c, width=80, anchor="center")
tree.column("Nome", width=150, anchor="w"); tree.pack(expand=True, fill="both", padx=10)

f_res = ctk.CTkFrame(root, fg_color="transparent"); f_res.pack(pady=10, fill="x", padx=10)
lbl_bruto = ctk.CTkLabel(f_res, text="", font=("Roboto", 16, "bold"), fg_color="#90EE90", text_color="black", corner_radius=8, width=320, height=50); lbl_bruto.pack(side="left", padx=20, expand=True)
lbl_desc = ctk.CTkLabel(f_res, text="", font=("Roboto", 16, "bold"), fg_color="#FFB6C1", text_color="black", corner_radius=8, width=320, height=50); lbl_desc.pack(side="left", padx=20, expand=True)
lbl_liq = ctk.CTkLabel(f_res, text="", font=("Roboto", 16, "bold"), fg_color="#2E7D32", text_color="white", corner_radius=8, width=320, height=50); lbl_liq.pack(side="left", padx=20, expand=True)

f_b = ctk.CTkFrame(root); f_b.pack(fill="x", padx=10, pady=10)
ctk.CTkButton(f_b, text="+ Funcionário", command=open_reg, width=180).pack(side="left", padx=5)
ctk.CTkButton(f_b, text="✏️ Editar Cadastro", command=open_edit_employee_window, width=180, fg_color="#E67E22").pack(side="left", padx=5)
ctk.CTkButton(f_b, text="💰 Rendimentos", fg_color="green", command=open_earnings_window, width=180).pack(side="right", padx=5)
ctk.CTkButton(f_b, text="📉 Descontos", fg_color="#A83232", command=open_deductions_window, width=180).pack(side="right", padx=5)

refresh_report_table(); root.mainloop()
