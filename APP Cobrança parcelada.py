import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import os
import sys
import subprocess
import platform
import shutil  # Biblioteca para copiar arquivos (Backup)

# --- BIBLIOTECAS PDF ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

# --- CONFIGURAÇÕES VISUAIS ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Database:
    def __init__(self, db_name="sistema_jpy_2026.db"):
        self.db_name = db_name
        self.init_db()
        self.migrar_banco()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS clientes
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               nome
                               TEXT
                               NOT
                               NULL,
                               telefone
                               TEXT
                           )
                           """)
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS vendas
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               cliente_id
                               INTEGER,
                               carro
                               TEXT,
                               placa
                               TEXT,
                               ano
                               TEXT,
                               cor
                               TEXT,
                               chassi
                               TEXT,
                               valor_venda
                               REAL,
                               entrada
                               REAL,
                               valor_mensal
                               REAL,
                               data_inicio
                               TEXT,
                               FOREIGN
                               KEY
                           (
                               cliente_id
                           ) REFERENCES clientes
                           (
                               id
                           )
                               )
                           """)
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS pagamentos
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               venda_id
                               INTEGER,
                               valor_pago
                               REAL,
                               data_pagamento
                               TEXT,
                               FOREIGN
                               KEY
                           (
                               venda_id
                           ) REFERENCES vendas
                           (
                               id
                           )
                               )
                           """)
            conn.commit()

    def migrar_banco(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(vendas)")
            colunas = [info[1] for info in cursor.fetchall()]
            novas_cols = ["ano", "cor", "chassi"]
            for col in novas_cols:
                if col not in colunas:
                    cursor.execute(f"ALTER TABLE vendas ADD COLUMN {col} TEXT")
            conn.commit()

    def query(self, sql, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(self, sql, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid


class Utils:
    @staticmethod
    def formatar_moeda(valor):
        try:
            return f"¥ {int(valor):,}"
        except:
            return "¥ 0"

    @staticmethod
    def limpar_moeda(texto):
        nums = "".join(filter(str.isdigit, str(texto)))
        return int(nums) if nums else 0

    @staticmethod
    def validar_data(data_str):
        if re.match(r"\d{2}/\d{2}/\d{4}", data_str):
            try:
                datetime.strptime(data_str, "%d/%m/%Y")
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def formatar_celular_jp(event):
        entry = event.widget
        if event.keysym in ("BackSpace", "Delete", "Left", "Right"): return
        nums = "".join(filter(str.isdigit, entry.get()))[:11]
        novo = ""
        if len(nums) > 0: novo += nums[:3]
        if len(nums) > 3: novo += "-" + nums[3:7]
        if len(nums) > 7: novo += "-" + nums[7:]
        entry.delete(0, "end");
        entry.insert(0, novo)

    @staticmethod
    def abrir_arquivo(path):
        """Abre arquivo ou pasta dependendo do SO"""
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':
            subprocess.call(('open', path))
        else:
            subprocess.call(('xdg-open', path))


class RelatoriosPDF:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.style_titulo = ParagraphStyle('Titulo', parent=self.styles['Heading1'], alignment=1, fontSize=16,
                                           spaceAfter=20)
        self.style_normal = self.styles['Normal']

    def gerar_dossie_venda(self, dados_cliente, dados_venda, pagamentos, totais):
        filename = f"Dossie_{dados_cliente['nome'].replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elementos = []
        elementos.append(Paragraph(f"DOSSIÊ DA VENDA - JPY SYSTEM", self.style_titulo))
        elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['Normal']))
        elementos.append(Spacer(1, 10))
        info_text = f"""
        <b>CLIENTE:</b> {dados_cliente['nome']}<br/>
        <b>TELEFONE:</b> {dados_cliente['telefone']}<br/><br/>
        <b>VEÍCULO:</b> {dados_venda['carro']}<br/>
        <b>DETALHES:</b> {dados_venda['ano']} - {dados_venda['cor']}<br/>
        <b>PLACA:</b> {dados_venda['placa']} | <b>CHASSI:</b> {dados_venda['chassi']}<br/>
        """
        elementos.append(Paragraph(info_text, self.styles['Normal']))
        elementos.append(Spacer(1, 20))
        data_table = [["DATA", "DESCRIÇÃO", "VALOR (¥)", "STATUS"]]
        data_table.append(
            [dados_venda['data_inicio'], "Entrada Inicial", Utils.formatar_moeda(dados_venda['entrada']), "CONFIRMADO"])
        for i, pg in enumerate(pagamentos, 1):
            data_table.append([pg[0], f"Parcela #{i}", Utils.formatar_moeda(pg[1]), "PAGO"])
        t = Table(data_table, colWidths=[3 * cm, 8 * cm, 4 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 20))
        resumo = f"""
        <b>VALOR DA VENDA:</b> {Utils.formatar_moeda(totais['venda'])}<br/>
        <b>TOTAL PAGO (Entrada + Parcelas):</b> {Utils.formatar_moeda(totais['pago'])}<br/>
        <b>SALDO DEVEDOR:</b> <font color='{'red' if totais['saldo'] > 0 else 'green'}'>{Utils.formatar_moeda(totais['saldo'])}</font>
        """
        elementos.append(Paragraph(resumo, self.styles['Normal']))
        if totais['saldo'] <= 0:
            elementos.append(Spacer(1, 20))
            elementos.append(Paragraph("<b>★ VEÍCULO QUITADO ★</b>", self.style_titulo))
        doc.build(elementos)
        Utils.abrir_arquivo(filename)

    def gerar_relatorio_mensal(self, mes_ref, dados_lista):
        filename = f"Relatorio_Mes_{mes_ref.replace('/', '-')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elementos = []
        elementos.append(Paragraph(f"RELATÓRIO GERAL - {mes_ref}", self.style_titulo))
        data = [["CLIENTE", "CARRO", "PARCELA MENSAL", "SITUAÇÃO"]]
        for linha in dados_lista:
            data.append([linha[0], linha[1], linha[2], linha[3]])
        t = Table(data, colWidths=[5 * cm, 7 * cm, 4 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        for i, row in enumerate(data[1:], 1):
            if row[3] == "PENDENTE":
                t.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), colors.red)]))
            else:
                t.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), colors.green)]))
        elementos.append(t)
        doc.build(elementos)
        Utils.abrir_arquivo(filename)

    def gerar_relatorio_devedores_mes(self, mes_ref, dados_lista):
        filename = f"Devedores_{mes_ref.replace('/', '-')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elementos = []
        style_alerta = ParagraphStyle('Alerta', parent=self.styles['Heading1'], alignment=1, fontSize=16, spaceAfter=20,
                                      textColor=colors.red)
        elementos.append(Paragraph(f"DEVEDORES DO MÊS - {mes_ref}", style_alerta))
        elementos.append(Paragraph(f"Lista de clientes com parcela pendente em {mes_ref}.", self.styles['Normal']))
        elementos.append(Spacer(1, 15))
        data = [["CLIENTE", "CARRO", "VALOR PENDENTE", "STATUS"]]
        total_pendente = 0
        for linha in dados_lista:
            data.append([linha[0], linha[1], linha[2], linha[3]])
            val = Utils.limpar_moeda(linha[2])
            total_pendente += val
        t = Table(data, colWidths=[5 * cm, 7 * cm, 4 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 20))
        elementos.append(
            Paragraph(f"<b>TOTAL A RECEBER (MÊS): {Utils.formatar_moeda(total_pendente)}</b>", self.styles['Normal']))
        doc.build(elementos)
        Utils.abrir_arquivo(filename)

    def gerar_relatorio_divida_total(self, dados_lista, total_geral):
        filename = "Relatorio_Divida_Total.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elementos = []
        elementos.append(Paragraph("RELATÓRIO DE DÍVIDAS A RECEBER", self.style_titulo))
        elementos.append(
            Paragraph(f"Total Geral a Receber: <b>{Utils.formatar_moeda(total_geral)}</b>", self.styles['Normal']))
        elementos.append(Spacer(1, 15))
        data = [["CLIENTE", "CARRO", "VALOR VENDA", "JÁ PAGO", "SALDO DEVEDOR"]]
        for linha in dados_lista:
            data.append(linha)
        t = Table(data, colWidths=[5 * cm, 6 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elementos.append(t)
        doc.build(elementos)
        Utils.abrir_arquivo(filename)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.pdf_manager = RelatoriosPDF()
        self.title("Sistema de Gestão Automotiva - JPY 2026")
        self.geometry("1400x850")
        self.minsize(1024, 768)
        self.data_filtro = datetime.now()
        self.setup_ui()
        self.carregar_dados()
        self.verificar_lembrete_backup()  # Verifica se precisa avisar do backup

    def verificar_lembrete_backup(self):
        # Se for um dos primeiros 5 dias do mês, mostra aviso
        dia_hoje = datetime.now().day
        if dia_hoje <= 5:
            # Usar 'after' para garantir que a janela principal carregou antes do popup
            self.after(1000, lambda: messagebox.showinfo("Lembrete Mensal",
                                                         "🔔 INÍCIO DE MÊS DETECTADO!\n\nPor segurança, lembre-se de clicar em\n'BACKUP DE SEGURANÇA' no menu lateral."))

    def realizar_backup(self):
        try:
            # Cria pasta se não existir
            pasta_backup = "backups"
            if not os.path.exists(pasta_backup):
                os.makedirs(pasta_backup)

            # Define nome do arquivo com data/hora
            nome_arquivo = f"backup_sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            caminho_destino = os.path.join(pasta_backup, nome_arquivo)

            # Copia
            shutil.copy(self.db.db_name, caminho_destino)

            messagebox.showinfo("Sucesso", f"Backup realizado com sucesso!\nArquivo: {nome_arquivo}")

            # Abre a pasta de backups
            Utils.abrir_arquivo(os.path.abspath(pasta_backup))

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao realizar backup:\n{e}")

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1);
        self.grid_rowconfigure(0, weight=1)
        self.frame_menu = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.criar_menu_lateral()
        self.frame_main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.criar_area_principal()

    def criar_menu_lateral(self):
        ctk.CTkLabel(self.frame_menu, text="JPY SYSTEM ¥", font=("Arial", 26, "bold")).pack(pady=30)
        btn_configs = [
            ("+ Novo Cliente", self.modal_cliente, "#2ecc71"),
            ("Lista Clientes", self.modal_lista_clientes, "#34495e"),
            ("separator", None, None),
            ("+ Nova Venda", self.modal_venda, "#3498db"),
            ("Lançar Pagamento", self.modal_pagamento, "#27ae60"),
            ("Editar / Excluir", self.modal_gerenciar_registro, "#e67e22"),
            ("separator", None, None),
            ("Dossiê Detalhado", self.janela_dossie, "#8e44ad"),
        ]
        for text, cmd, color in btn_configs:
            if text == "separator":
                ctk.CTkFrame(self.frame_menu, height=2, fg_color="gray50").pack(fill="x", padx=15, pady=10)
            else:
                ctk.CTkButton(self.frame_menu, text=text, command=cmd, fg_color=color, font=("Arial", 14, "bold"),
                              height=40).pack(fill="x", padx=15, pady=5)

        # --- ÁREA DE RELATÓRIOS PDF ---
        ctk.CTkLabel(self.frame_menu, text="Relatórios PDF", text_color="gray").pack(pady=(20, 5))
        ctk.CTkButton(self.frame_menu, text="📄 Do Mês Atual", command=self.imprimir_relatorio_mensal, fg_color="#555",
                      height=30).pack(fill="x", padx=30, pady=2)
        ctk.CTkButton(self.frame_menu, text="📄 Devedores do Mês", command=self.imprimir_relatorio_devedores,
                      fg_color="#c0392b", height=30).pack(fill="x", padx=30, pady=2)
        ctk.CTkButton(self.frame_menu, text="📄 Dívida Total", command=self.imprimir_relatorio_divida, fg_color="#555",
                      height=30).pack(fill="x", padx=30, pady=2)

        # --- ÁREA DO SISTEMA (BACKUP) ---
        ctk.CTkFrame(self.frame_menu, height=2, fg_color="gray50").pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(self.frame_menu, text="💾 Backup de Segurança", command=self.realizar_backup, fg_color="#2c3e50",
                      hover_color="black").pack(fill="x", padx=15)

        self.frame_data = ctk.CTkFrame(self.frame_menu, fg_color="transparent");
        self.frame_data.pack(side="bottom", pady=20)
        ctk.CTkLabel(self.frame_data, text="Mês de Referência:", font=("Arial", 12)).pack()
        f_nav = ctk.CTkFrame(self.frame_data, fg_color="transparent");
        f_nav.pack(pady=5)
        ctk.CTkButton(f_nav, text="<", width=40, command=lambda: self.mudar_mes(-1)).pack(side="left", padx=5)
        self.lbl_data = ctk.CTkLabel(f_nav, text=self.data_filtro.strftime("%m/%Y"), font=("Arial", 20, "bold"));
        self.lbl_data.pack(side="left", padx=10)
        ctk.CTkButton(f_nav, text=">", width=40, command=lambda: self.mudar_mes(1)).pack(side="left", padx=5)

    def criar_area_principal(self):
        top_frame = ctk.CTkFrame(self.frame_main, fg_color="transparent");
        top_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top_frame, text="Painel de Controle", font=("Arial", 24, "bold")).pack(side="left")
        self.entry_busca = ctk.CTkEntry(top_frame, placeholder_text="Buscar Cliente...", width=300);
        self.entry_busca.pack(side="right")
        self.entry_busca.bind("<KeyRelease>", lambda e: self.carregar_dados(filtro_nome=self.entry_busca.get()))

        self.tabview = ctk.CTkTabview(self.frame_main);
        self.tabview.pack(fill="both", expand=True)
        self.tab_ativos = self.tabview.add("Cobranças do Mês")
        self.tab_quitados = self.tabview.add("Veículos Quitados")

        self.tree_ativos = self.criar_treeview(self.tab_ativos,
                                               ["ID", "Cliente", "Carro/Detalhes", "Venda Total", "Saldo Devedor",
                                                "Parcela Mensal", "Progresso", "Status"])
        self.tree_quitados = self.criar_treeview(self.tab_quitados,
                                                 ["ID", "Cliente", "Carro/Detalhes", "Venda Total", "Data Quitação",
                                                  "Status"])

    def criar_treeview(self, parent, cols):
        style = ttk.Style();
        style.theme_use("clam")
        style.configure("Treeview", rowheight=30, font=("Arial", 11))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#2c3e50", foreground="white")
        frame = ctk.CTkFrame(parent, fg_color="transparent");
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview);
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew");
        vsb.grid(row=0, column=1, sticky="ns");
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1);
        frame.grid_columnconfigure(0, weight=1)
        for col in cols:
            width = 50 if col == "ID" else 130
            if col == "Carro/Detalhes": width = 250
            tree.heading(col, text=col);
            tree.column(col, width=width, anchor="center")
        tree.tag_configure('pago', foreground='#27ae60', background='#eafaf1')
        tree.tag_configure('pendente', foreground='#c0392b', background='#fdedec')
        tree.tag_configure('quitado_style', foreground='red', font=("Arial", 11, "bold"))
        return tree

    def mudar_mes(self, delta):
        self.data_filtro += relativedelta(months=delta)
        self.lbl_data.configure(text=self.data_filtro.strftime("%m/%Y"))
        self.carregar_dados()

    def carregar_dados(self, filtro_nome=""):
        for item in self.tree_ativos.get_children(): self.tree_ativos.delete(item)
        for item in self.tree_quitados.get_children(): self.tree_quitados.delete(item)
        mes_ref = self.data_filtro.strftime("%m/%Y")
        sql = """SELECT v.id, \
                        c.nome, \
                        v.carro, \
                        v.placa, \
                        v.ano, \
                        v.cor, \
                        v.valor_venda, \
                        v.entrada, \
                        v.valor_mensal, \
                        v.data_inicio
                 FROM vendas v \
                          JOIN clientes c ON v.cliente_id = c.id \
                 WHERE c.nome LIKE ? \
                 ORDER BY c.nome ASC"""
        for v in self.db.query(sql, (f"%{filtro_nome}%",)):
            vid, nome, carro, placa, ano, cor, total, entrada, mensal, data_ini = v
            ano = ano if ano else "";
            cor = cor if cor else ""
            res_pagos = self.db.query("SELECT SUM(valor_pago), MAX(data_pagamento) FROM pagamentos WHERE venda_id = ?",
                                      (vid,))
            total_pago_extra = res_pagos[0][0] if res_pagos[0][0] else 0
            ultimo_pgto = res_pagos[0][1]
            saldo_devedor = max(0, total - (entrada + total_pago_extra))
            valor_a_financiar = total - entrada
            qtd_parcelas_total = (int(valor_a_financiar / mensal) + (
                1 if valor_a_financiar % mensal > 0 else 0)) if mensal > 0 else 0
            res_qtd_pg = self.db.query("SELECT COUNT(*) FROM pagamentos WHERE venda_id = ?", (vid,))
            qtd_pagas = res_qtd_pg[0][0] if res_qtd_pg else 0

            detalhes = f"{carro}";
            if cor or ano: detalhes += f" ({cor} - {ano})"

            total_fmt = Utils.formatar_moeda(total)
            if saldo_devedor <= 0:
                self.tree_quitados.insert("", "end",
                                          values=(vid, nome, detalhes, total_fmt, ultimo_pgto or data_ini, "QUITADO"),
                                          tags=('quitado_style',))
            else:
                pgto_mes = self.db.query("SELECT id FROM pagamentos WHERE venda_id = ? AND data_pagamento LIKE ?",
                                         (vid, f"%/{mes_ref}"))
                status = "PAGO" if pgto_mes else "PENDENTE"
                self.tree_ativos.insert("", "end",
                                        values=(vid, nome, detalhes, total_fmt, Utils.formatar_moeda(saldo_devedor),
                                                Utils.formatar_moeda(mensal), f"{qtd_pagas}/{qtd_parcelas_total}",
                                                status), tags=('pago' if status == "PAGO" else 'pendente',))

    def _criar_janela(self, titulo, altura=400):
        jan = ctk.CTkToplevel(self);
        jan.title(titulo);
        jan.geometry(f"500x{altura}");
        jan.grab_set();
        jan.resizable(False, False)
        return jan

    def _mask_moeda(self, event):
        entry = event.widget
        if event.keysym in ("BackSpace", "Delete", "Left", "Right"): return
        val = Utils.limpar_moeda(entry.get())
        if val: entry.delete(0, "end"); entry.insert(0, f"{val:,}")

    def _confirmar_exclusao_digitada(self, callback_sucesso):
        jan = self._criar_janela("Confirmação de Segurança", 200)
        ctk.CTkLabel(jan, text="PARA CONFIRMAR A EXCLUSÃO\nDIGITE: EXCLUIR", font=("Arial", 12, "bold"),
                     text_color="red").pack(pady=10)
        entry_conf = ctk.CTkEntry(jan, placeholder_text="excluir")
        entry_conf.pack(pady=10)

        def verificar():
            if entry_conf.get().upper() == "EXCLUIR":
                jan.destroy()
                callback_sucesso()
            else:
                messagebox.showerror("Erro", "Palavra de confirmação incorreta.")

        ctk.CTkButton(jan, text="CONFIRMAR EXCLUSÃO", fg_color="red", command=verificar).pack(pady=10)

    # --- CLIENTES ---
    def modal_cliente(self):
        jan = self._criar_janela("Novo Cliente", 300)
        ctk.CTkLabel(jan, text="Nome:").pack(pady=(10, 0));
        en = ctk.CTkEntry(jan, width=300);
        en.pack()
        ctk.CTkLabel(jan, text="Celular JP (090...):").pack(pady=(10, 0));
        et = ctk.CTkEntry(jan, width=300);
        et.pack();
        et.bind("<KeyRelease>", Utils.formatar_celular_jp)

        def salvar():
            if not en.get(): return messagebox.showerror("Erro", "Nome obrigatório")
            self.db.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (en.get(), et.get()))
            jan.destroy();
            messagebox.showinfo("Ok", "Cliente Salvo")

        ctk.CTkButton(jan, text="Salvar", command=salvar, fg_color="green").pack(pady=20)

    def modal_lista_clientes(self):
        jan = self._criar_janela("Lista de Clientes", 600)
        cols = ("ID", "Nome", "Tel")
        tree_cli = ttk.Treeview(jan, columns=cols, show="headings")
        tree_cli.heading("ID", text="ID");
        tree_cli.column("ID", width=50, anchor="center")
        tree_cli.heading("Nome", text="Nome");
        tree_cli.column("Nome", width=250)
        tree_cli.heading("Tel", text="Telefone");
        tree_cli.column("Tel", width=150, anchor="center")
        tree_cli.pack(fill="both", expand=True, padx=10, pady=10)

        for c in self.db.query("SELECT id, nome, telefone FROM clientes ORDER BY nome"):
            tree_cli.insert("", "end", values=c)

        def abrir_edicao():
            selecionado = tree_cli.selection()
            if not selecionado: return messagebox.showwarning("Aviso", "Selecione um cliente.")
            id_cli = tree_cli.item(selecionado[0])['values'][0]
            jan.destroy();
            self.modal_editar_cliente(id_cli)

        def acao_excluir_cliente():
            selecionado = tree_cli.selection()
            if not selecionado: return messagebox.showwarning("Aviso", "Selecione um cliente.")
            id_cli = tree_cli.item(selecionado[0])['values'][0]
            qtd_vendas = self.db.query("SELECT COUNT(*) FROM vendas WHERE cliente_id = ?", (id_cli,))[0][0]
            if qtd_vendas > 0:
                return messagebox.showerror("Bloqueado",
                                            f"Este cliente possui {qtd_vendas} venda(s) cadastradas.\nApague as vendas primeiro para excluir o cliente.")

            def confirmar_delete():
                self.db.execute("DELETE FROM clientes WHERE id=?", (id_cli,))
                messagebox.showinfo("Sucesso", "Cliente excluído.")
                jan.destroy()
                self.modal_lista_clientes()

            self._confirmar_exclusao_digitada(confirmar_delete)

        f_btns = ctk.CTkFrame(jan, fg_color="transparent")
        f_btns.pack(pady=10, fill="x", padx=20)
        ctk.CTkButton(f_btns, text="Editar Cliente", command=abrir_edicao).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(f_btns, text="Excluir Cliente", command=acao_excluir_cliente, fg_color="#c0392b").pack(
            side="left", expand=True, padx=5)

    def modal_editar_cliente(self, id_cliente):
        dados = self.db.query("SELECT nome, telefone FROM clientes WHERE id=?", (id_cliente,))
        if not dados: return
        nome_atual, tel_atual = dados[0]
        jan = self._criar_janela("Editar Cliente", 300)
        ctk.CTkLabel(jan, text="Nome:").pack(pady=(10, 0));
        en = ctk.CTkEntry(jan, width=300);
        en.insert(0, nome_atual);
        en.pack()
        ctk.CTkLabel(jan, text="Celular JP:").pack(pady=(10, 0));
        et = ctk.CTkEntry(jan, width=300);
        et.insert(0, tel_atual);
        et.pack();
        et.bind("<KeyRelease>", Utils.formatar_celular_jp)

        def salvar_alteracoes():
            novo_nome = en.get();
            novo_tel = et.get()
            if not novo_nome: return messagebox.showerror("Erro", "Nome é obrigatório")
            self.db.execute("UPDATE clientes SET nome=?, telefone=? WHERE id=?", (novo_nome, novo_tel, id_cliente))
            self.carregar_dados();
            jan.destroy();
            messagebox.showinfo("Sucesso", "Dados do cliente atualizados!")

        ctk.CTkButton(jan, text="Salvar Alterações", fg_color="green", command=salvar_alteracoes).pack(pady=20)

    # --- VENDAS ---
    def modal_venda(self):
        clientes = self.db.query("SELECT id, nome FROM clientes ORDER BY nome")
        if not clientes: return messagebox.showwarning("Aviso", "Cadastre clientes!")
        jan = self._criar_janela("Nova Venda", 700)
        mapa = {f"{c[1]} (ID:{c[0]})": c[0] for c in clientes}
        ctk.CTkLabel(jan, text="Cliente:").pack();
        cb = ctk.CTkComboBox(jan, values=list(mapa.keys()), width=300);
        cb.pack()
        ents = {}
        for c in ["Carro", "Ano", "Cor", "Placa", "Chassi"]:
            ctk.CTkLabel(jan, text=c).pack(pady=1);
            e = ctk.CTkEntry(jan, width=300);
            e.pack();
            ents[c] = e
        for c in ["Total", "Entrada", "Mensal"]:
            ctk.CTkLabel(jan, text=f"{c} (¥)").pack(pady=1);
            e = ctk.CTkEntry(jan, width=300);
            e.pack();
            e.bind("<KeyRelease>", self._mask_moeda);
            ents[c] = e
        ctk.CTkLabel(jan, text="Data Início").pack(pady=1);
        ed = ctk.CTkEntry(jan, width=300);
        ed.insert(0, datetime.now().strftime("%d/%m/%Y"));
        ed.pack(pady=5)

        def salvar():
            try:
                if not cb.get() or cb.get() not in mapa: return messagebox.showerror("Erro", "Cliente Inválido")
                self.db.execute(
                    "INSERT INTO vendas (cliente_id, carro, ano, cor, placa, chassi, valor_venda, entrada, valor_mensal, data_inicio) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (mapa[cb.get()], ents["Carro"].get(), ents["Ano"].get(), ents["Cor"].get(), ents["Placa"].get(),
                     ents["Chassi"].get(),
                     Utils.limpar_moeda(ents["Total"].get()), Utils.limpar_moeda(ents["Entrada"].get()),
                     Utils.limpar_moeda(ents["Mensal"].get()), ed.get()))
                self.carregar_dados();
                jan.destroy();
                messagebox.showinfo("Ok", "Venda Salva")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        ctk.CTkButton(jan, text="Salvar Venda", command=salvar, fg_color="#3498db").pack(pady=20)

    def modal_pagamento(self):
        nome_aba = self.tabview.get()
        if nome_aba == "Cobranças do Mês":
            tree = self.tree_ativos
        else:
            tree = self.tree_quitados
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Aviso", f"Selecione uma venda na aba '{nome_aba}'!")
        vid = tree.item(sel[0])['values'][0]
        res = self.db.query("SELECT valor_mensal FROM vendas WHERE id=?", (vid,))
        val = res[0][0] if res else 0
        jan = self._criar_janela("Pagar Parcela", 300)
        e_val = ctk.CTkEntry(jan);
        e_val.insert(0, f"{int(val):,}");
        e_val.pack(pady=10);
        e_val.bind("<KeyRelease>", self._mask_moeda)
        e_dat = ctk.CTkEntry(jan);
        e_dat.insert(0, datetime.now().strftime("%d/%m/%Y"));
        e_dat.pack(pady=10)

        def ok():
            if not Utils.validar_data(e_dat.get()): return messagebox.showerror("Erro", "Data Inválida")
            self.db.execute("INSERT INTO pagamentos (venda_id, valor_pago, data_pagamento) VALUES (?,?,?)",
                            (vid, Utils.limpar_moeda(e_val.get()), e_dat.get()))
            self.carregar_dados();
            jan.destroy();
            messagebox.showinfo("Ok", "Pago!")

        ctk.CTkButton(jan, text="Confirmar", command=ok).pack()

    # --- GERENCIAMENTO ---
    def modal_gerenciar_registro(self):
        nome_aba = self.tabview.get()
        if nome_aba == "Cobranças do Mês":
            tree = self.tree_ativos
        else:
            tree = self.tree_quitados
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Atenção", f"Selecione um registro na aba '{nome_aba}'.")
        venda_id = int(tree.item(sel[0])['values'][0])
        jan = self._criar_janela("Gerenciar", 350)
        ctk.CTkButton(jan, text="EDITAR DADOS DA VENDA", fg_color="#f39c12", font=("Arial", 14, "bold"),
                      command=lambda: [jan.destroy(), self.modal_editar_venda(venda_id)]).pack(pady=10, fill="x",
                                                                                               padx=20)
        ctk.CTkButton(jan, text="GERENCIAR PARCELAS", fg_color="#2980b9", font=("Arial", 14, "bold"),
                      command=lambda: [jan.destroy(), self.modal_listar_pagamentos(venda_id)]).pack(pady=10, fill="x",
                                                                                                    padx=20)

        def callback_excluir_tudo():
            self.db.execute("DELETE FROM pagamentos WHERE venda_id=?", (venda_id,))
            self.db.execute("DELETE FROM vendas WHERE id=?", (venda_id,))
            self.carregar_dados()
            jan.destroy()
            messagebox.showinfo("Info", "Excluído com sucesso.")

        def acao_excluir_tudo():
            self._confirmar_exclusao_digitada(callback_excluir_tudo)

        ctk.CTkButton(jan, text="EXCLUIR TUDO", fg_color="#c0392b", font=("Arial", 14, "bold"),
                      command=acao_excluir_tudo).pack(pady=(30, 5), fill="x", padx=20)

    def modal_editar_venda(self, venda_id):
        dados = self.db.query(
            "SELECT carro, ano, cor, placa, chassi, valor_venda, entrada, valor_mensal, data_inicio FROM vendas WHERE id=?",
            (venda_id,))
        if not dados: return
        carro, ano, cor, placa, chassi, v_total, v_ent, v_men, d_ini = dados[0]
        jan = self._criar_janela("Editar Venda", 650)
        dados_dict = {"Carro": carro, "Ano": ano, "Cor": cor, "Placa": placa, "Chassi": chassi, "Valor Total": v_total,
                      "Entrada": v_ent, "Mensal": v_men}
        entries = {}
        for k, v in dados_dict.items():
            ctk.CTkLabel(jan, text=k).pack(pady=1);
            e = ctk.CTkEntry(jan, width=300)
            val_str = str(v) if v is not None else ""
            if k in ["Valor Total", "Entrada", "Mensal"]:
                e.insert(0, f"{int(v):,}"); e.bind("<KeyRelease>", self._mask_moeda)
            else:
                e.insert(0, val_str)
            e.pack();
            entries[k] = e
        ctk.CTkLabel(jan, text="Data Início").pack(pady=1);
        e_data = ctk.CTkEntry(jan, width=300);
        e_data.insert(0, d_ini);
        e_data.pack()

        def salvar_edicao():
            try:
                self.db.execute(
                    "UPDATE vendas SET carro=?, ano=?, cor=?, placa=?, chassi=?, valor_venda=?, entrada=?, valor_mensal=?, data_inicio=? WHERE id=?",
                    (entries["Carro"].get(), entries["Ano"].get(), entries["Cor"].get(), entries["Placa"].get(),
                     entries["Chassi"].get(),
                     Utils.limpar_moeda(entries["Valor Total"].get()), Utils.limpar_moeda(entries["Entrada"].get()),
                     Utils.limpar_moeda(entries["Mensal"].get()), e_data.get(), venda_id))
                self.carregar_dados();
                jan.destroy();
                messagebox.showinfo("Sucesso", "Atualizado!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        ctk.CTkButton(jan, text="Salvar Alterações", fg_color="green", command=salvar_edicao).pack(pady=20)

    def modal_listar_pagamentos(self, venda_id):
        jan = self._criar_janela("Gerenciar Pagamentos", 600)
        cols = ("ID", "Data", "Valor");
        tree = ttk.Treeview(jan, columns=cols, show="headings", height=15)
        tree.heading("ID", text="ID");
        tree.column("ID", width=50);
        tree.heading("Data", text="Data");
        tree.column("Data", width=150)
        tree.heading("Valor", text="Valor");
        tree.column("Valor", width=150);
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for p in self.db.query(
                "SELECT id, data_pagamento, valor_pago FROM pagamentos WHERE venda_id=? ORDER BY id DESC", (venda_id,)):
            tree.insert("", "end", values=(p[0], p[1], Utils.formatar_moeda(p[2])))

        def editar():
            if not tree.selection(): return messagebox.showwarning("Aviso", "Selecione um pagamento.")
            jan.destroy();
            self.modal_editar_pagamento_unico(tree.item(tree.selection()[0])['values'][0])

        def excluir():
            if not tree.selection(): return messagebox.showwarning("Aviso", "Selecione um pagamento.")
            if messagebox.askyesno("Confirmar", "Excluir este pagamento?"):
                self.db.execute("DELETE FROM pagamentos WHERE id=?", (tree.item(tree.selection()[0])['values'][0],))
                self.carregar_dados();
                jan.destroy();
                messagebox.showinfo("Info", "Excluído.")

        f = ctk.CTkFrame(jan);
        f.pack(pady=10, fill="x", padx=10)
        ctk.CTkButton(f, text="EDITAR", fg_color="#f39c12", command=editar).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(f, text="EXCLUIR", fg_color="#c0392b", command=excluir).pack(side="left", padx=5, expand=True)

    def modal_editar_pagamento_unico(self, pgto_id):
        val, dat = self.db.query("SELECT valor_pago, data_pagamento FROM pagamentos WHERE id=?", (pgto_id,))[0]
        jan = self._criar_janela("Editar Parcela", 250)
        ctk.CTkLabel(jan, text="Valor:").pack(pady=(20, 5));
        e_val = ctk.CTkEntry(jan);
        e_val.insert(0, f"{int(val):,}");
        e_val.pack();
        e_val.bind("<KeyRelease>", self._mask_moeda)
        ctk.CTkLabel(jan, text="Data:").pack(pady=(10, 5));
        e_dat = ctk.CTkEntry(jan);
        e_dat.insert(0, dat);
        e_dat.pack()

        def salvar():
            if not Utils.validar_data(e_dat.get()): return messagebox.showerror("Erro", "Data inválida")
            self.db.execute("UPDATE pagamentos SET valor_pago=?, data_pagamento=? WHERE id=?",
                            (Utils.limpar_moeda(e_val.get()), e_dat.get(), pgto_id))
            self.carregar_dados();
            jan.destroy();
            messagebox.showinfo("Sucesso", "Atualizado.")

        ctk.CTkButton(jan, text="Salvar", fg_color="green", command=salvar).pack(pady=20)

    # --- RELATÓRIOS E VISUALIZAÇÃO ---
    def janela_dossie(self):
        nome_aba = self.tabview.get()
        if nome_aba == "Cobranças do Mês":
            tree = self.tree_ativos
        else:
            tree = self.tree_quitados
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Aviso", f"Selecione uma venda na aba '{nome_aba}'.")
        venda_id = int(tree.item(sel[0])['values'][0])

        dados = self.db.query(
            "SELECT c.nome, c.telefone, v.carro, v.placa, v.ano, v.cor, v.chassi, v.valor_venda, v.entrada, v.data_inicio FROM vendas v JOIN clientes c ON v.cliente_id = c.id WHERE v.id = ?",
            (venda_id,))
        if not dados: return
        nome, tel, car, plac, ano, cor, chas, v_tot, v_ent, d_ini = dados[0]

        jan = ctk.CTkToplevel(self);
        jan.title("Dossiê");
        jan.geometry("800x700")
        txt = f"CLIENTE: {nome} | TEL: {tel}\nVEÍCULO: {car}\nANO: {ano} | COR: {cor} | PLACA: {plac}\nCHASSI: {chas}\n----------------------------------\nVENDA: {Utils.formatar_moeda(v_tot)} | ENTRADA: {Utils.formatar_moeda(v_ent)}"
        ctk.CTkLabel(jan, text=txt, justify="left", font=("Consolas", 14)).pack(pady=10)

        t = ttk.Treeview(jan, columns=("Data", "Descrição", "Valor", "Status"), show="headings");
        t.pack(fill="both", expand=True, padx=10)
        for c in ("Data", "Descrição", "Valor", "Status"): t.heading(c, text=c)
        t.insert("", "end", values=(d_ini, "Entrada", Utils.formatar_moeda(v_ent), "CONFIRMADO"))

        pgtos = self.db.query("SELECT data_pagamento, valor_pago FROM pagamentos WHERE venda_id=? ORDER BY id",
                              (venda_id,))
        tot_pag = v_ent
        lista_pgtos_pdf = []
        for i, p in enumerate(pgtos, 1):
            t.insert("", "end", values=(p[0], f"Parcela #{i}", Utils.formatar_moeda(p[1]), "PAGO"))
            lista_pgtos_pdf.append((p[0], p[1]))
            tot_pag += p[1]

        saldo = max(0, v_tot - tot_pag)
        ctk.CTkLabel(jan, text=f"TOTAL PAGO: {Utils.formatar_moeda(tot_pag)}  |  SALDO: {Utils.formatar_moeda(saldo)}",
                     font=("Arial", 16, "bold"), text_color="#e74c3c" if saldo > 0 else "#2ecc71").pack(pady=10)
        if saldo == 0: ctk.CTkLabel(jan, text="★ VEÍCULO QUITADO ★", font=("Arial", 20, "bold"), text_color="red").pack(
            pady=5)

        def imprimir_pdf():
            cli_dict = {"nome": nome, "telefone": tel}
            venda_dict = {"carro": car, "ano": ano, "cor": cor, "placa": plac, "chassi": chas, "entrada": v_ent,
                          "data_inicio": d_ini}
            totais_dict = {"venda": v_tot, "pago": tot_pag, "saldo": saldo}
            self.pdf_manager.gerar_dossie_venda(cli_dict, venda_dict, lista_pgtos_pdf, totais_dict)

        ctk.CTkButton(jan, text="🖨 IMPRIMIR DOSSIÊ (PDF)", command=imprimir_pdf, fg_color="#8e44ad").pack(pady=20)

    def imprimir_relatorio_mensal(self):
        mes_ref = self.data_filtro.strftime("%m/%Y")
        if not self.tree_ativos.get_children():
            return messagebox.showwarning("Aviso", "Não há dados na tabela para gerar relatório.")
        dados_pdf = []
        for item in self.tree_ativos.get_children():
            valores = self.tree_ativos.item(item)['values']
            dados_pdf.append((valores[1], valores[2].split("\n")[0], valores[5], valores[7]))
        self.pdf_manager.gerar_relatorio_mensal(mes_ref, dados_pdf)

    def imprimir_relatorio_devedores(self):
        mes_ref = self.data_filtro.strftime("%m/%Y")
        if not self.tree_ativos.get_children():
            return messagebox.showwarning("Aviso", "Não há dados na tabela para gerar relatório.")

        dados_pdf = []
        encontrou_pendente = False

        for item in self.tree_ativos.get_children():
            valores = self.tree_ativos.item(item)['values']
            status = valores[7]
            if status == "PENDENTE":
                encontrou_pendente = True
                dados_pdf.append((valores[1], valores[2].split("\n")[0], valores[5], status))

        if not encontrou_pendente:
            return messagebox.showinfo("Parabéns", f"Não há devedores para o mês {mes_ref}!")

        self.pdf_manager.gerar_relatorio_devedores_mes(mes_ref, dados_pdf)

    def imprimir_relatorio_divida(self):
        sql = "SELECT id, cliente_id, carro, valor_venda, entrada FROM vendas"
        vendas = self.db.query(sql)
        dados_relatorio = []
        total_a_receber_geral = 0
        for v in vendas:
            vid, cid, carro, total, entrada = v
            nome = self.db.query("SELECT nome FROM clientes WHERE id=?", (cid,))[0][0]
            res_pagos = self.db.query("SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id=?", (vid,))
            pago_extra = res_pagos[0][0] if res_pagos[0][0] else 0
            total_pago = entrada + pago_extra
            saldo = max(0, total - total_pago)
            if saldo > 0:
                dados_relatorio.append([nome, carro, Utils.formatar_moeda(total), Utils.formatar_moeda(total_pago),
                                        Utils.formatar_moeda(saldo)])
                total_a_receber_geral += saldo
        if not dados_relatorio:
            return messagebox.showinfo("Info", "Nenhuma dívida encontrada.")
        self.pdf_manager.gerar_relatorio_divida_total(dados_relatorio, total_a_receber_geral)


if __name__ == "__main__":
    app = App()
    app.mainloop()