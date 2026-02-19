import customtkinter as ctk
from tkinter import messagebox
import pandas as pd
import calendar
import os
from datetime import datetime, timedelta

# Bibliotecas para o PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- REGISTRO DE FONTE JAPONESA ---
try:
    font_path = "C:/Windows/Fonts/msgothic.ttc"
    pdfmetrics.registerFont(TTFont('MS-Gothic', font_path))
    FONT_NAME = 'MS-Gothic'
except:
    FONT_NAME = 'Helvetica'

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO_DB = "dados_ponto_jp_final.csv"
ARQUIVO_FUNC = "funcionarios_jp_final.csv"


class AppPonto(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("勤怠管理システム (Sistema de Ponto)")
        self.geometry("1250x850")
        self.configurar_banco()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- サイドバー (Menu Lateral 300px) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="デジタル点呼", font=("Arial", 22, "bold")).pack(pady=30)

        ctk.CTkLabel(self.sidebar, text="従業員名 (Nome):").pack(pady=(10, 0))
        self.combo_func = ctk.CTkComboBox(self.sidebar, values=self.get_lista_func(), command=self.mudar_usuario,
                                          width=260)
        self.combo_func.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="年度 (Ano):").pack(pady=(10, 0))
        self.combo_ano = ctk.CTkComboBox(self.sidebar, values=[str(a) for a in range(2023, 2031)],
                                         command=self.mudar_usuario, width=260)
        self.combo_ano.set(datetime.now().strftime('%Y'))
        self.combo_ano.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="月 (Mês):").pack(pady=(10, 0))
        self.combo_mes = ctk.CTkComboBox(self.sidebar, values=[str(i).zfill(2) for i in range(1, 13)],
                                         command=self.mudar_usuario, width=260)
        self.combo_mes.set(datetime.now().strftime('%m'))
        self.combo_mes.pack(pady=10)

        self.btn_pdf = ctk.CTkButton(self.sidebar, text="📄 PDFレポート作成", fg_color="#2c3e50", command=self.gerar_pdf,
                                     width=260)
        self.btn_pdf.pack(pady=20)

        self.btn_cadastrar = ctk.CTkButton(self.sidebar, text="+ 新規登録 (Novo)", fg_color="transparent",
                                           border_width=1, command=self.janela_cadastro, width=260)
        self.btn_cadastrar.pack(pady=10)

        # --- メインエリア ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.lista_dias_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="月間勤務表")
        self.lista_dias_frame.pack(fill="both", expand=True)

        # --- フッター (Rodapé) ---
        self.footer = ctk.CTkFrame(self, height=140)
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.lbl_totais = ctk.CTkLabel(self.footer, text="従業員を選択してください", font=("Arial", 14, "bold"),
                                       justify="left")
        self.lbl_totais.pack(side="left", padx=30)

        ctk.CTkButton(self.footer, text="全月入力 (夜勤)", fg_color="#5c2d91",
                      command=lambda: self.preencher_mes_completo("夜勤"), width=150).pack(side="right", padx=10)
        ctk.CTkButton(self.footer, text="全月入力 (日勤)", fg_color="#1f538d",
                      command=lambda: self.preencher_mes_completo("日勤"), width=150).pack(side="right", padx=10)

    def configurar_banco(self):
        colunas = ['Data', 'Funcionario', 'Turno', 'Entrada', 'Saida', 'Horas', 'Extra', 'Ad_Noturno']
        if not os.path.exists(ARQUIVO_DB): pd.DataFrame(columns=colunas).to_csv(ARQUIVO_DB, index=False)
        if not os.path.exists(ARQUIVO_FUNC): pd.DataFrame(columns=['Nome']).to_csv(ARQUIVO_FUNC, index=False)

    def get_lista_func(self):
        if os.path.exists(ARQUIVO_FUNC):
            lista = pd.read_csv(ARQUIVO_FUNC)['Nome'].tolist()
            return lista if lista else ["登録なし"]
        return ["登録なし"]

    def mudar_usuario(self, _=None):
        self.atualizar_lista_dias()

    def gerar_pdf(self):
        func = self.combo_func.get()
        mes, ano = self.combo_mes.get(), self.combo_ano.get()
        if func == "登録なし": return
        df = pd.read_csv(ARQUIVO_DB)
        df['Data_dt'] = pd.to_datetime(df['Data'])
        df_mes = df[(df['Funcionario'] == func) & (df['Data_dt'].dt.month == int(mes)) & (
                    df['Data_dt'].dt.year == int(ano))].sort_values('Data')

        nome_arquivo = f"Report_{func}_{ano}_{mes}.pdf"
        doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
        styles = getSampleStyleSheet()
        styles['Title'].fontName = styles['Normal'].fontName = FONT_NAME
        elements = [Paragraph(f"{ano}年{mes}月 勤務報告書", styles['Title']),
                    Paragraph(f"氏名: {func}", styles['Normal']), Spacer(1, 12)]

        dados_tabela = [["日付", "出勤", "退勤", "勤務", "残業", "深夜"]]
        for _, row in df_mes.iterrows():
            dados_tabela.append([
                datetime.strptime(row['Data'], '%Y-%m-%d').strftime('%m/%d'),
                row['Entrada'], row['Saida'],
                f"{row['Horas']:.2f}", f"{row['Extra']:.2f}", f"{row['Ad_Noturno']:.2f}"
            ])

        # LARGURAS DAS COLUNAS (Corrigido)
        larguras = [80, 80, 80, 80, 80, 80]
        t = Table(dados_tabela, colWidths=larguras)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ]))
        elements.append(t);
        elements.append(Spacer(1, 20))

        resumo = f"合計勤務: {df_mes['Horas'].sum():.2f}h | 合計残業: {df_mes['Extra'].sum():.2f}h | 深夜合計: {df_mes['Ad_Noturno'].sum():.2f}h"
        elements.append(Paragraph(resumo, styles['Normal']))
        doc.build(elements);
        os.startfile(nome_arquivo)

    def atualizar_lista_dias(self):
        for widget in self.lista_dias_frame.winfo_children(): widget.destroy()
        func = self.combo_func.get()
        if func == "登録なし": return
        mes, ano = int(self.combo_mes.get()), int(self.combo_ano.get())
        _, num_dias = calendar.monthrange(ano, mes)
        df = pd.read_csv(ARQUIVO_DB)
        dias_jp = ["月", "火", "水", "木", "金", "土", "日"]
        for dia in range(1, num_dias + 1):
            data_dt = datetime(ano, mes, dia);
            data_str = data_dt.strftime('%Y-%m-%d')
            reg = df[(df['Data'] == data_str) & (df['Funcionario'] == func)];
            ja_tem = not reg.empty
            cor = "#333333"
            if ja_tem: cor = "#7a1a1a" if reg.iloc[0]['Turno'] == "休日" else "#1b2e1b"
            row = ctk.CTkFrame(self.lista_dias_frame, fg_color=cor);
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"{dia:02d} ({dias_jp[data_dt.weekday()]})", width=100,
                         font=("Arial", 12, "bold")).pack(side="left", padx=10)
            if not ja_tem:
                ctk.CTkButton(row, text="休日", width=70, height=22, fg_color="#a12525",
                              command=lambda d=data_dt: self.salvar_ponto(d, "休日", "--", "--", 0, 0, 0)).pack(
                    side="right", padx=5)
                ctk.CTkButton(row, text="修正", width=70, height=22, fg_color="#d68a00",
                              command=lambda d=data_dt: self.abrir_janela_especial(d)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="夜勤", width=70, height=22, fg_color="#5c2d91",
                              command=lambda d=data_dt: self.salvar_ponto(d, "夜勤", "16:45", "01:45", 8.0, 0,
                                                                          3.75)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="日勤", width=70, height=22,
                              command=lambda d=data_dt: self.salvar_ponto(d, "日勤", "08:00", "17:00")).pack(
                    side="right", padx=5)
            else:
                info = reg.iloc[0]
                txt = "休 日 (Folga)" if info[
                                             'Turno'] == "休日" else f"{info['Entrada']}-{info['Saida']} | {info['Horas']:.2f}h | 残:{info['Extra']:.2f}h | 深夜:{info['Ad_Noturno']:.2f}h"
                ctk.CTkLabel(row, text=txt, text_color="#A5D6A7").pack(side="left", padx=20)
                ctk.CTkButton(row, text="編集", width=50, height=20, fg_color="gray",
                              command=lambda d=data_dt, r=info: self.abrir_janela_especial(d, r)).pack(side="right",
                                                                                                       padx=10)

        df_mes = df[(df['Funcionario'] == func) & (pd.to_datetime(df['Data']).dt.month == mes) & (
                    pd.to_datetime(df['Data']).dt.year == ano)]
        d_trab = len(df_mes[df_mes['Turno'] != "休日"])
        d_folga = len(df_mes[df_mes['Turno'] == "休日"])
        self.lbl_totais.configure(
            text=f"【月間報告】 出勤: {d_trab}日 | 休日: {d_folga}日\n合計勤務: {df_mes['Horas'].sum():.2f}h | 合計残業: {df_mes['Extra'].sum():.2f}h | 深夜合計: {df_mes['Ad_Noturno'].sum():.2f}h")

    def abrir_janela_especial(self, data_ref, registro_existente=None):
        janela = ctk.CTkToplevel(self)
        janela.title("勤務入力")
        janela.geometry("350x450")
        janela.attributes("-topmost", True)

        horas_list = [f"{i:02d}" for i in range(24)]
        min_list = [f"{i:02d}" for i in range(0, 60, 5)]

        e_h, e_m, s_h, s_m = "08", "00", "17", "00"
        if registro_existente is not None and registro_existente['Turno'] != "休日":
            try:
                e_h, e_m = registro_existente['Entrada'].split(":")
                s_h, s_m = registro_existente['Saida'].split(":")
            except:
                pass

        ctk.CTkLabel(janela, text="出勤 (Entrada):").pack(pady=10)
        f1 = ctk.CTkFrame(janela, fg_color="transparent");
        f1.pack()
        cb_eh = ctk.CTkComboBox(f1, values=horas_list, width=70);
        cb_eh.set(e_h);
        cb_eh.pack(side="left", padx=2)
        cb_em = ctk.CTkComboBox(f1, values=min_list, width=70);
        cb_em.set(e_m);
        cb_em.pack(side="left", padx=2)

        ctk.CTkLabel(janela, text="退勤 (Saída):").pack(pady=10)
        f2 = ctk.CTkFrame(janela, fg_color="transparent");
        f2.pack()
        cb_sh = ctk.CTkComboBox(f2, values=horas_list, width=70);
        cb_sh.set(s_h);
        cb_sh.pack(side="left", padx=2)
        cb_sm = ctk.CTkComboBox(f2, values=min_list, width=70);
        cb_sm.set(s_m);
        cb_sm.pack(side="left", padx=2)

        def confirmar():
            e, s = f"{cb_eh.get()}:{cb_em.get()}", f"{cb_sh.get()}:{cb_sm.get()}"
            t1, t2 = datetime.strptime(e, "%H:%M"), datetime.strptime(s, "%H:%M")
            if t2 < t1: t2 += timedelta(days=1)
            h_ef = max(0, ((t2 - t1).total_seconds() / 3600) - 1.0)
            noturno = 0;
            check = t1
            while check < t2:
                if check.hour >= 22 or check.hour < 5: noturno += 1 / 60
                check += timedelta(minutes=1)
            self.remover_registro(data_ref)
            self.salvar_ponto(data_ref, "修正", e, s, round(min(8, h_ef), 2), round(max(0, h_ef - 8), 2),
                              round(noturno, 2))
            janela.destroy()

        ctk.CTkButton(janela, text="保存 (Salvar)", fg_color="green", command=confirmar).pack(pady=30)
        ctk.CTkButton(janela, text="休日 (Folga)", fg_color="#a12525", command=lambda: [self.remover_registro(data_ref),
                                                                                        self.salvar_ponto(data_ref,
                                                                                                          "休日", "--",
                                                                                                          "--", 0, 0,
                                                                                                          0),
                                                                                        janela.destroy()]).pack()

    def remover_registro(self, data_ref):
        df = pd.read_csv(ARQUIVO_DB)
        df = df.drop(
            df[(df['Data'] == data_ref.strftime('%Y-%m-%d')) & (df['Funcionario'] == self.combo_func.get())].index)
        df.to_csv(ARQUIVO_DB, index=False)

    def salvar_ponto(self, data_ref, turno, ent, sai, h, ext, notur):
        df = pd.read_csv(ARQUIVO_DB)
        nova = {'Data': data_ref.strftime('%Y-%m-%d'), 'Funcionario': self.combo_func.get(), 'Turno': turno,
                'Entrada': ent, 'Saida': sai, 'Horas': h, 'Extra': ext, 'Ad_Noturno': notur}
        pd.concat([df, pd.DataFrame([nova])], ignore_index=True).to_csv(ARQUIVO_DB, index=False)
        self.atualizar_lista_dias()

    def preencher_mes_completo(self, tipo):
        func = self.combo_func.get()
        if func == "登録なし": return
        df = pd.read_csv(ARQUIVO_DB)
        mes, ano = int(self.combo_mes.get()), int(self.combo_ano.get())
        _, num_dias = calendar.monthrange(ano, mes)
        novos = []
        for dia in range(1, num_dias + 1):
            dt = datetime(ano, mes, dia);
            dt_str = dt.strftime('%Y-%m-%d')
            if not df[(df['Data'] == dt_str) & (df['Funcionario'] == func)].empty: continue
            if dt.weekday() >= 5:
                novos.append(
                    {'Data': dt_str, 'Funcionario': func, 'Turno': '休日', 'Entrada': '--', 'Saida': '--', 'Horas': 0,
                     'Extra': 0, 'Ad_Noturno': 0})
            else:
                h, n = (8, 0) if tipo == "日勤" else (8, 3.75)
                e, s = ("08:00", "17:00") if tipo == "日勤" else ("16:45", "01:45")
                novos.append({'Data': dt_str, 'Funcionario': func, 'Turno': tipo, 'Entrada': e, 'Saida': s, 'Horas': h,
                              'Extra': 0, 'Ad_Noturno': n})
        if novos: pd.concat([df, pd.DataFrame(novos)], ignore_index=True).to_csv(ARQUIVO_DB,
                                                                                 index=False); self.atualizar_lista_dias()

    def janela_cadastro(self):
        dialog = ctk.CTkInputDialog(text="氏名を入力:", title="登録")
        nome = dialog.get_input()
        if nome:
            df = pd.read_csv(ARQUIVO_FUNC)
            pd.concat([df, pd.DataFrame({'Nome': [nome]})], ignore_index=True).to_csv(ARQUIVO_FUNC, index=False)
            self.combo_func.configure(values=self.get_lista_func())


if __name__ == "__main__":
    AppPonto().mainloop()
