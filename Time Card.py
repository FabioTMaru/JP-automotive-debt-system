import customtkinter as ctk
from tkinter import messagebox
import pandas as pd
import calendar
import os
from datetime import datetime, timedelta

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO_DB = "dados_ponto_v12.csv"
ARQUIVO_FUNC = "funcionarios_v12.csv"


class AppPonto(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Ponto Pro")
        self.geometry("1250x850")
        self.configurar_banco()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL (300px) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="PONTO DIGITAL", font=("Arial", 22, "bold")).pack(pady=30)

        ctk.CTkLabel(self.sidebar, text="Funcionário:").pack(pady=(10, 0))
        self.combo_func = ctk.CTkComboBox(self.sidebar, values=self.get_lista_func(), command=self.mudar_usuario,
                                          width=260)
        self.combo_func.pack(pady=10)

        # Seleção de Ano para registro correto
        ctk.CTkLabel(self.sidebar, text="Ano do Exercício:").pack(pady=(10, 0))
        self.combo_ano = ctk.CTkComboBox(self.sidebar, values=[str(a) for a in range(2023, 2031)],
                                         command=self.mudar_usuario, width=260)
        self.combo_ano.set(datetime.now().strftime('%Y'))
        self.combo_ano.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="Mês de Referência:").pack(pady=(10, 0))
        self.combo_mes = ctk.CTkComboBox(self.sidebar, values=[str(i).zfill(2) for i in range(1, 13)],
                                         command=self.mudar_usuario, width=260)
        self.combo_mes.set(datetime.now().strftime('%m'))
        self.combo_mes.pack(pady=10)

        ctk.CTkButton(self.sidebar, text="+ Novo Funcionário", fg_color="transparent", border_width=1,
                      command=self.janela_cadastro, width=260).pack(pady=30)

        # --- ÁREA CENTRAL ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.lista_dias_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Frequência Mensal")
        self.lista_dias_frame.pack(fill="both", expand=True)

        # --- RODAPÉ (Relatório Detalhado) ---
        self.footer = ctk.CTkFrame(self, height=120)
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))

        self.lbl_totais = ctk.CTkLabel(self.footer, text="Selecione um funcionário", font=("Arial", 14, "bold"),
                                       justify="left")
        self.lbl_totais.pack(side="left", padx=30)

        ctk.CTkButton(self.footer, text="Mês Todo (Noturno)", fg_color="#5c2d91",
                      command=lambda: self.preencher_mes_completo("Noturno"), width=170).pack(side="right", padx=10)
        ctk.CTkButton(self.footer, text="Mês Todo (Diurno)", fg_color="#1f538d",
                      command=lambda: self.preencher_mes_completo("Diurno"), width=170).pack(side="right", padx=10)

    def configurar_banco(self):
        colunas = ['Data', 'Funcionario', 'Turno', 'Entrada', 'Saida', 'Horas', 'Extra', 'Ad_Noturno']
        if not os.path.exists(ARQUIVO_DB): pd.DataFrame(columns=colunas).to_csv(ARQUIVO_DB, index=False)
        if not os.path.exists(ARQUIVO_FUNC): pd.DataFrame(columns=['Nome']).to_csv(ARQUIVO_FUNC, index=False)

    def get_lista_func(self):
        if os.path.exists(ARQUIVO_FUNC):
            lista = pd.read_csv(ARQUIVO_FUNC)['Nome'].tolist()
            return lista if lista else ["Nenhum"]
        return ["Nenhum"]

    def mudar_usuario(self, _=None):
        self.atualizar_lista_dias()

    def atualizar_lista_dias(self):
        for widget in self.lista_dias_frame.winfo_children(): widget.destroy()
        func = self.combo_func.get()
        if func == "Nenhum": return

        mes = int(self.combo_mes.get())
        ano = int(self.combo_ano.get())
        _, num_dias = calendar.monthrange(ano, mes)

        df = pd.read_csv(ARQUIVO_DB)
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

        for dia in range(1, num_dias + 1):
            data_dt = datetime(ano, mes, dia)
            data_str = data_dt.strftime('%Y-%m-%d')
            reg = df[(df['Data'] == data_str) & (df['Funcionario'] == func)]
            ja_tem = not reg.empty

            cor_fundo = "#333333"
            if ja_tem:
                cor_fundo = "#7a1a1a" if reg.iloc[0]['Turno'] == "Folga" else "#1b2e1b"

            row = ctk.CTkFrame(self.lista_dias_frame, fg_color=cor_fundo)
            row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(row, text=f"{dia:02d}/{mes:02d} ({dias_semana[data_dt.weekday()][:3]})", width=120,
                         font=("Arial", 12, "bold")).pack(side="left", padx=10)

            if not ja_tem:
                ctk.CTkButton(row, text="Folga", width=70, height=22, fg_color="#a12525",
                              command=lambda d=data_dt: self.salvar_ponto(d, "Folga", "--", "--", 0, 0, 0)).pack(
                    side="right", padx=5)
                ctk.CTkButton(row, text="Manual", width=70, height=22, fg_color="#d68a00",
                              command=lambda d=data_dt: self.abrir_janela_especial(d)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="Noturno", width=70, height=22, fg_color="#5c2d91",
                              command=lambda d=data_dt: self.salvar_ponto(d, "Noturno", "16:45", "01:45", 8.0, 0.0,
                                                                          3.75)).pack(side="right", padx=5)
                ctk.CTkButton(row, text="Diurno", width=70, height=22,
                              command=lambda d=data_dt: self.salvar_ponto(d, "Diurno", "08:00", "17:00")).pack(
                    side="right", padx=5)
            else:
                info = reg.iloc[0]
                if info['Turno'] == "Folga":
                    ctk.CTkLabel(row, text="[ FOLGA ]", text_color="#ff8080", font=("Arial", 12, "bold")).pack(
                        side="left", padx=20)
                else:
                    txt = f"{info['Entrada']}-{info['Saida']} | Trab: {info['Horas']:.2f}h | Extra: {info['Extra']:.2f}h | Not: {info['Ad_Noturno']:.2f}h"
                    ctk.CTkLabel(row, text=txt, text_color="#A5D6A7", font=("Consolas", 12)).pack(side="left", padx=20)

                ctk.CTkButton(row, text="Editar", width=60, height=20, fg_color="gray",
                              command=lambda d=data_dt, r=info: self.abrir_janela_especial(d, r)).pack(side="right",
                                                                                                       padx=10)

        # Atualização do Relatório Inferior
        df_mes = df[(df['Funcionario'] == func) & (pd.to_datetime(df['Data']).dt.month == mes) & (
                    pd.to_datetime(df['Data']).dt.year == ano)]

        dias_trab = len(df_mes[df_mes['Turno'] != "Folga"])
        dias_folga = len(df_mes[df_mes['Turno'] == "Folga"])
        total_h = df_mes['Horas'].sum()
        total_e = df_mes['Extra'].sum()
        total_n = df_mes['Ad_Noturno'].sum()

        resumo = (f"RELATÓRIO MENSAL ({mes:02d}/{ano})\n"
                  f"Dias Trabalhados: {dias_trab} | Dias de Folga: {dias_folga}\n"
                  f"Horas: {total_h:.2f}h | Extras: {total_e:.2f}h | Noturno: {total_n:.2f}h")
        self.lbl_totais.configure(text=resumo)

    def abrir_janela_especial(self, data_ref, registro_existente=None):
        janela = ctk.CTkToplevel(self)
        janela.title(f"Registro - {data_ref.strftime('%d/%m')}")
        janela.geometry("300x420")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Entrada (HH:MM):").pack(pady=10)
        ent_in = ctk.CTkEntry(janela)
        val_e = registro_existente['Entrada'] if (
                    registro_existente is not None and registro_existente['Turno'] != "Folga") else "08:00"
        ent_in.insert(0, val_e);
        ent_in.pack()

        ctk.CTkLabel(janela, text="Saída (HH:MM):").pack(pady=10)
        ent_out = ctk.CTkEntry(janela)
        val_s = registro_existente['Saida'] if (
                    registro_existente is not None and registro_existente['Turno'] != "Folga") else "17:00"
        ent_out.insert(0, val_s);
        ent_out.pack()

        def confirmar():
            try:
                e, s = ent_in.get(), ent_out.get()
                t1 = datetime.strptime(e, "%H:%M")
                t2 = datetime.strptime(s, "%H:%M")
                if t2 < t1: t2 += timedelta(days=1)
                h_efetiva = max(0, ((t2 - t1).total_seconds() / 3600) - 1.0)
                h_normais = min(8.0, h_efetiva)
                h_extras = max(0, h_efetiva - 8.0)

                noturno = 0;
                check = t1
                while check < t2:
                    if check.hour >= 22 or check.hour < 5: noturno += 1 / 60
                    check += timedelta(minutes=1)

                self.remover_registro(data_ref)
                self.salvar_ponto(data_ref, "Manual", e, s, round(h_normais, 2), round(h_extras, 2), round(noturno, 2))
                janela.destroy()
            except:
                messagebox.showerror("Erro", "Use HH:MM")

        ctk.CTkButton(janela, text="Salvar", fg_color="green", command=confirmar).pack(pady=10)
        ctk.CTkButton(janela, text="Folga", fg_color="#a12525", command=lambda: [self.remover_registro(data_ref),
                                                                                 self.salvar_ponto(data_ref, "Folga",
                                                                                                   "--", "--", 0, 0, 0),
                                                                                 janela.destroy()]).pack(pady=5)
        if registro_existente is not None:
            ctk.CTkButton(janela, text="Limpar", fg_color="gray",
                          command=lambda: [self.remover_registro(data_ref), self.atualizar_lista_dias(),
                                           janela.destroy()]).pack(pady=5)

    def remover_registro(self, data_ref):
        df = pd.read_csv(ARQUIVO_DB)
        df = df.drop(
            df[(df['Data'] == data_ref.strftime('%Y-%m-%d')) & (df['Funcionario'] == self.combo_func.get())].index)
        df.to_csv(ARQUIVO_DB, index=False)

    def salvar_ponto(self, data_ref, turno, ent, sai, h=8.0, ext=0.0, notur=0.0):
        df = pd.read_csv(ARQUIVO_DB)
        nova = {'Data': data_ref.strftime('%Y-%m-%d'), 'Funcionario': self.combo_func.get(), 'Turno': turno,
                'Entrada': ent, 'Saida': sai, 'Horas': h, 'Extra': ext, 'Ad_Noturno': notur}
        pd.concat([df, pd.DataFrame([nova])], ignore_index=True).to_csv(ARQUIVO_DB, index=False)
        self.atualizar_lista_dias()

    def preencher_mes_completo(self, tipo):
        func = self.combo_func.get()
        if func == "Nenhum": return
        df = pd.read_csv(ARQUIVO_DB)
        mes = int(self.combo_mes.get())
        ano = int(self.combo_ano.get())
        _, num_dias = calendar.monthrange(ano, mes)
        novos = []
        for dia in range(1, num_dias + 1):
            dt_str = datetime(ano, mes, dia).strftime('%Y-%m-%d')
            if not df[(df['Data'] == dt_str) & (df['Funcionario'] == func)].empty: continue
            if datetime(ano, mes, dia).weekday() >= 5:
                novos.append({'Data': dt_str, 'Funcionario': func, 'Turno': 'Folga', 'Entrada': '--', 'Saida': '--',
                              'Horas': 0.0, 'Extra': 0.0, 'Ad_Noturno': 0.0})
            else:
                if tipo == "Diurno":
                    novos.append(
                        {'Data': dt_str, 'Funcionario': func, 'Turno': 'Diurno', 'Entrada': '08:00', 'Saida': '17:00',
                         'Horas': 8.0, 'Extra': 0.0, 'Ad_Noturno': 0.0})
                else:
                    novos.append(
                        {'Data': dt_str, 'Funcionario': func, 'Turno': 'Noturno', 'Entrada': '16:45', 'Saida': '01:45',
                         'Horas': 8.0, 'Extra': 0.0, 'Ad_Noturno': 3.75})
        if novos: pd.concat([df, pd.DataFrame(novos)], ignore_index=True).to_csv(ARQUIVO_DB,
                                                                                 index=False); self.atualizar_lista_dias()

    def janela_cadastro(self):
        dialog = ctk.CTkInputDialog(text="Nome do Funcionário:", title="Cadastro")
        nome = dialog.get_input()
        if nome:
            df = pd.read_csv(ARQUIVO_FUNC)
            pd.concat([df, pd.DataFrame({'Nome': [nome]})], ignore_index=True).to_csv(ARQUIVO_FUNC, index=False)
            self.combo_func.configure(values=self.get_lista_func())


if __name__ == "__main__":
    AppPonto().mainloop()
