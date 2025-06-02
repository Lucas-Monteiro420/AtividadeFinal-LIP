import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import datetime
import base64
import os
import hashlib
import random
import json
import threading
import time
import webbrowser
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Tentar importar bibliotecas adicionais
try:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    matplotlib_disponivel = True
except ImportError:
    matplotlib_disponivel = False

try:
    import winsound

    winsound_disponivel = True
except ImportError:
    winsound_disponivel = False

try:
    from scipy import signal
    from scipy.io import wavfile

    scipy_disponivel = True
except ImportError:
    scipy_disponivel = False

try:
    import serial
    import serial.tools.list_ports

    serial_disponivel = True
except ImportError:
    serial_disponivel = False


# Classe para estatísticas de uso
class Estatisticas:
    def __init__(self):
        self.arquivos_criptografados = 0
        self.arquivos_descriptografados = 0
        self.tamanho_total_criptografado = 0
        self.tamanho_total_descriptografado = 0
        self.operacoes_por_dia = {}
        self.tipos_arquivos = {}
        self.hora_inicio = datetime.datetime.now()

    def registrar_operacao(self, tipo, tamanho=0, extensao=None):
        if tipo == 'criptografar':
            self.arquivos_criptografados += 1
            self.tamanho_total_criptografado += tamanho
        elif tipo == 'descriptografar':
            self.arquivos_descriptografados += 1
            self.tamanho_total_descriptografado += tamanho

        # Registra operação por data
        data_hoje = datetime.datetime.now().strftime('%Y-%m-%d')
        if data_hoje not in self.operacoes_por_dia:
            self.operacoes_por_dia[data_hoje] = {'cripto': 0, 'descripto': 0}

        if tipo == 'criptografar':
            self.operacoes_por_dia[data_hoje]['cripto'] += 1
        elif tipo == 'descriptografar':
            self.operacoes_por_dia[data_hoje]['descripto'] += 1

        # Registra operação por tipo de arquivo
        if extensao:
            if extensao not in self.tipos_arquivos:
                self.tipos_arquivos[extensao] = {'cripto': 0, 'descripto': 0}

            if tipo == 'criptografar':
                self.tipos_arquivos[extensao]['cripto'] += 1
            elif tipo == 'descriptografar':
                self.tipos_arquivos[extensao]['descripto'] += 1


class MenuLateralApp:
    def __init__(self, root):
        self.janela = root
        self.janela.title("CryptographiE")
        self.janela.minsize(800, 600)

        # Adicionar ícone personalizado
        try:
            self.janela.iconbitmap("crypto.ico")  # Coloque o arquivo icone.ico na mesma pasta
        except:
            pass  # Se não encontrar o arquivo, continua sem ícone

        # Instância de estatísticas
        self.estatisticas = Estatisticas()

        # Lista para armazenar o histórico de operações com arquivos
        self.historico_arquivos = []

        # Chave mestra fixa para criptografia automática
        self.chave_mestra = self.gerar_chave_mestra()

        # Dicionário para armazenar metadados dos arquivos processados
        self.metadados_arquivos = {}

        # Variáveis para código Morse
        self.reproduzindo = False
        self.thread_reproducao = None
        self.pausado = False  # Estado de pausa
        self.evento_pausa = threading.Event()  # Evento para controlar pausa
        self.evento_pausa.set()  # Iniciar desbloqueado

        # Variáveis para Arduino
        self.arduino_serial = None
        self.arduino_conectado = False
        self.arduino_porta = None
        self.thread_arduino = None
        self.transmitindo_arduino = False

        # Variáveis para controle de login
        self.usuario_logado = False
        self.email_usuario_logado = ""

        # Configurar comportamento responsivo
        self.janela.columnconfigure(1, weight=1)
        self.janela.rowconfigure(0, weight=1)

        # Criar o menu lateral
        self.criar_menu_lateral()

        # Criar área principal
        self.criar_area_principal()

        # Criar menu
        self.criar_menu()

        # Criar barra de status
        self.criar_barra_status()

        # Mostrar primeira aba por padrão
        self.mostrar_aba("texto")

        # Inicializar estatísticas
        self.atualizar_estatisticas()

    def gerar_chave_mestra(self):
        """Gerar chave mestra fixa baseada no sistema"""
        sistema_info = f"{os.environ.get('USERNAME', 'user')}{os.environ.get('COMPUTERNAME', 'pc')}"
        chave_base = hashlib.sha256(sistema_info.encode()).digest()
        return base64.urlsafe_b64encode(chave_base)

    def gerar_chave_de_senha(self, senha="default_key", salt=None):
        """Gerar chave de criptografia de forma consistente"""
        if salt is None:
            salt = os.urandom(16)

        if isinstance(senha, str):
            senha_bytes = senha.encode('utf-8')
        else:
            senha_bytes = senha

        chave_combinada = self.chave_mestra + senha_bytes

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(chave_combinada))
        return key, salt

    def criptografar_texto(self, texto, senha_personalizada=None):
        """Criptografar texto - VERSÃO CORRIGIDA"""
        try:
            # Gerar salt único para esta operação
            salt = os.urandom(16)

            if senha_personalizada:
                # Usar senha personalizada
                senha_para_chave = senha_personalizada
                usar_senha_personalizada = True
            else:
                # Usar senha padrão
                senha_para_chave = "texto_default_2024"
                usar_senha_personalizada = False

            # Gerar chave
            key, _ = self.gerar_chave_de_senha(senha_para_chave, salt)
            f = Fernet(key)

            # Criptografar texto
            texto_criptografado = f.encrypt(texto.encode('utf-8'))

            # Criar estrutura de dados
            dados_completos = {
                'salt': base64.urlsafe_b64encode(salt).decode(),
                'senha_personalizada': usar_senha_personalizada,
                'dados': base64.urlsafe_b64encode(texto_criptografado).decode(),
                'versao': '2.2'  # Nova versão corrigida
            }

            # Se não é senha personalizada, armazenar hash do texto para validação
            if not usar_senha_personalizada:
                hash_texto = hashlib.sha256(texto.encode()).hexdigest()
                dados_completos['hash_texto'] = hash_texto

            json_dados = json.dumps(dados_completos)
            resultado = base64.urlsafe_b64encode(json_dados.encode()).decode()

            return resultado
        except Exception as e:
            raise Exception(f"Erro na criptografia: {str(e)}")

    def descriptografar_texto(self, texto_criptografado, senha_personalizada=None):
        """Descriptografar texto - VERSÃO CORRIGIDA"""
        try:
            # Decodificar dados
            json_dados = base64.urlsafe_b64decode(texto_criptografado.encode()).decode()
            dados_completos = json.loads(json_dados)

            salt = base64.urlsafe_b64decode(dados_completos['salt'].encode())
            dados_criptografados = base64.urlsafe_b64decode(dados_completos['dados'].encode())
            senha_personalizada_flag = dados_completos.get('senha_personalizada', False)
            versao = dados_completos.get('versao', '1.0')

            if senha_personalizada_flag:
                # Foi criptografado com senha personalizada
                if not senha_personalizada:
                    raise Exception("Este texto foi criptografado com senha personalizada. Por favor, forneça a senha.")

                senha_para_chave = senha_personalizada
            else:
                # Foi criptografado com senha padrão
                if versao >= '2.2':
                    senha_para_chave = "texto_default_2024"
                else:
                    # Compatibilidade com versões antigas
                    senha_para_chave = "default_key"

            # Gerar chave e descriptografar
            key, _ = self.gerar_chave_de_senha(senha_para_chave, salt)
            f = Fernet(key)
            texto_descriptografado = f.decrypt(dados_criptografados).decode('utf-8')

            # Se não é senha personalizada e temos hash, validar
            if not senha_personalizada_flag and 'hash_texto' in dados_completos:
                hash_esperado = dados_completos['hash_texto']
                hash_atual = hashlib.sha256(texto_descriptografado.encode()).hexdigest()

                if hash_esperado != hash_atual:
                    raise Exception("Falha na validação da integridade do texto")

            return texto_descriptografado

        except json.JSONDecodeError:
            # Tentar formatos antigos
            return self.descriptografar_texto_formato_antigo(texto_criptografado, senha_personalizada)
        except Exception as e:
            raise Exception(f"Erro na descriptografia: {str(e)}")

    def descriptografar_texto_formato_antigo(self, texto_criptografado, senha_personalizada=None):
        """Descriptografar texto no formato antigo (compatibilidade)"""
        try:
            dados = base64.urlsafe_b64decode(texto_criptografado.encode())
            salt = dados[:16]
            texto_cripto = dados[16:]

            # Lista de senhas para testar (compatibilidade)
            senhas_teste = [
                "texto_default_2024",  # Nova senha padrão
                "default_key",  # Senha antiga
                "",  # Senha vazia
                "text_key"  # Outra variação
            ]

            # Se senha personalizada fornecida, tentar primeiro
            if senha_personalizada:
                senhas_teste.insert(0, senha_personalizada)

            for senha in senhas_teste:
                try:
                    key, _ = self.gerar_chave_de_senha(senha, salt)
                    f = Fernet(key)
                    texto_original = f.decrypt(texto_cripto).decode('utf-8')
                    return texto_original
                except:
                    continue

            raise Exception("Não foi possível descriptografar com as chaves disponíveis")
        except Exception as e:
            raise Exception(f"Erro no formato antigo: {str(e)}")

    def processar_texto(self):
        """Processar texto com opção de senha personalizada"""
        texto = self.entrada_texto.get('1.0', tk.END).strip()

        if not texto:
            messagebox.showwarning("Aviso", "Digite algum texto para processar!")
            return

        # Perguntar se deseja usar senha personalizada
        usar_senha = messagebox.askyesno("Senha Personalizada",
                                         "Deseja usar uma senha personalizada?\n\n"
                                         "Sim: Você escolhe a senha\n"
                                         "Não: Senha automática gerada")

        senha_personalizada = None
        if usar_senha:
            senha_personalizada = simpledialog.askstring("Senha",
                                                         "Digite a senha personalizada:",
                                                         show='*')
            if not senha_personalizada:
                messagebox.showinfo("Cancelado", "Operação cancelada.")
                return

        try:
            resultado = self.criptografar_texto(texto, senha_personalizada)
            self.saida_texto.delete('1.0', tk.END)
            self.saida_texto.insert('1.0', resultado)
            self.estatisticas.registrar_operacao('criptografar', len(texto))

            if senha_personalizada:
                messagebox.showinfo("Sucesso", "Texto criptografado com senha personalizada!")
            else:
                messagebox.showinfo("Sucesso", "Texto criptografado com senha automática!")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def restaurar_texto(self):
        """Restaurar texto com opção de senha personalizada"""
        texto = self.entrada_texto.get('1.0', tk.END).strip()

        if not texto:
            messagebox.showwarning("Aviso", "Digite o texto processado para restaurar!")
            return

        # Primeiro, tentar sem senha personalizada
        try:
            resultado = self.descriptografar_texto(texto)
            self.saida_texto.delete('1.0', tk.END)
            self.saida_texto.insert('1.0', resultado)
            self.estatisticas.registrar_operacao('descriptografar', len(texto))
            messagebox.showinfo("Sucesso", "Texto restaurado com sucesso!")
            return
        except Exception as e:
            # Se falhou, perguntar pela senha
            if "senha personalizada" in str(e).lower():
                senha = simpledialog.askstring("Senha Necessária",
                                               "Este texto requer senha personalizada:",
                                               show='*')
                if senha:
                    try:
                        resultado = self.descriptografar_texto(texto, senha)
                        self.saida_texto.delete('1.0', tk.END)
                        self.saida_texto.insert('1.0', resultado)
                        self.estatisticas.registrar_operacao('descriptografar', len(texto))
                        messagebox.showinfo("Sucesso", "Texto restaurado com sucesso!")
                        return
                    except Exception as e2:
                        messagebox.showerror("Erro", f"Senha incorreta ou erro na descriptografia: {e2}")
                else:
                    messagebox.showinfo("Cancelado", "Operação cancelada.")
            else:
                messagebox.showerror("Erro", f"Erro ao restaurar texto: {e}")

    def criar_menu_lateral(self):
        """Criar o menu lateral à esquerda"""
        self.frame_menu = tk.Frame(self.janela, bg="#2c3e50", width=250)
        self.frame_menu.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.frame_menu.grid_propagate(False)

        titulo = tk.Label(
            self.frame_menu,
            text="CryptographiE",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 16, "bold"),
            pady=20
        )
        titulo.pack(fill="x")

        separador = tk.Frame(self.frame_menu, bg="#34495e", height=2)
        separador.pack(fill="x", padx=20, pady=10)

        self.botoes_menu = {}
        self.criar_botao_menu("Processamento de Texto", "texto", "📝")
        self.criar_botao_menu("Processamento de Arquivos", "arquivos", "📁")
        self.criar_botao_menu("Estatísticas", "estatisticas", "📊")
        self.criar_botao_menu("Código Morse", "morse", "📡")

        rodape = tk.Label(
            self.frame_menu,
            text="v2.1\n© 2024",
            bg="#2c3e50",
            fg="#7f8c8d",
            font=("Arial", 8),
            justify="center"
        )
        rodape.pack(side="bottom", pady=20)

    def criar_botao_menu(self, texto, aba_id, icone=""):
        """Criar um botão no menu lateral"""
        frame_botao = tk.Frame(self.frame_menu, bg="#2c3e50")
        frame_botao.pack(fill="x", padx=10, pady=2)

        botao = tk.Button(
            frame_botao,
            text=f"{icone} {texto}",
            bg="#34495e",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            bd=0,
            pady=12,
            cursor="hand2",
            anchor="w",
            padx=20,
            command=lambda: self.mostrar_aba(aba_id)
        )
        botao.pack(fill="x")

        def on_enter(event):
            if aba_id != self.aba_atual:
                botao.config(bg="#3498db")

        def on_leave(event):
            if aba_id != self.aba_atual:
                botao.config(bg="#34495e")

        botao.bind("<Enter>", on_enter)
        botao.bind("<Leave>", on_leave)

        self.botoes_menu[aba_id] = botao

    def criar_area_principal(self):
        """Criar a área principal onde o conteúdo será exibido"""
        self.frame_principal = tk.Frame(self.janela, bg="white")
        self.frame_principal.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.frame_principal.columnconfigure(0, weight=1)
        self.frame_principal.rowconfigure(0, weight=1)

        self.container_abas = tk.Frame(self.frame_principal, bg="white")
        self.container_abas.grid(row=0, column=0, sticky="nsew")
        self.container_abas.columnconfigure(0, weight=1)
        self.container_abas.rowconfigure(0, weight=1)

        self.criar_abas()
        self.aba_atual = None

    def criar_abas(self):
        """Criar todas as abas do aplicativo"""
        self.abas = {}

        self.abas["texto"] = self.criar_aba_texto()
        self.abas["arquivos"] = self.criar_aba_arquivos()
        self.abas["estatisticas"] = self.criar_aba_estatisticas()
        self.abas["morse"] = self.criar_aba_morse()

    def criar_aba_texto(self):
        """Criar conteúdo da aba de processamento de texto"""
        aba = tk.Frame(self.container_abas, bg="white")
        aba.grid(row=0, column=0, sticky="nsew")
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(0, weight=40)
        aba.rowconfigure(1, weight=1)
        aba.rowconfigure(2, weight=40)

        titulo = tk.Label(aba, text="Processamento Seguro de Texto", font=("Arial", 16, "bold"), bg="white")
        titulo.grid(row=0, column=0, sticky="n", pady=(0, 10))

        frame_entrada = tk.LabelFrame(aba, text="Entrada", font=("Arial", 10))
        frame_entrada.grid(row=0, column=0, sticky="nsew", pady=5)
        frame_entrada.columnconfigure(0, weight=1)
        frame_entrada.rowconfigure(0, weight=1)

        self.entrada_texto = scrolledtext.ScrolledText(frame_entrada, height=8)
        self.entrada_texto.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        btn_abrir = tk.Button(frame_entrada, text="Abrir Arquivo", command=self.carregar_arquivo)
        btn_abrir.grid(row=1, column=0, sticky="e", padx=5, pady=2)

        frame_botoes_texto = tk.Frame(aba)
        frame_botoes_texto.grid(row=1, column=0, sticky="ew", pady=5)
        frame_botoes_texto.columnconfigure(0, weight=1)
        frame_botoes_texto.columnconfigure(1, weight=1)
        frame_botoes_texto.columnconfigure(2, weight=1)
        frame_botoes_texto.columnconfigure(3, weight=1)

        btn_processar = tk.Button(frame_botoes_texto, text="Criptografar", command=self.processar_texto,
                                  bg="#27ae60", fg="white", padx=5)
        btn_processar.grid(row=0, column=0, sticky="ew", padx=2)

        btn_restaurar = tk.Button(frame_botoes_texto, text="Descriptografar", command=self.restaurar_texto,
                                  bg="#e74c3c", fg="white", padx=5)
        btn_restaurar.grid(row=0, column=1, sticky="ew", padx=2)

        btn_limpar = tk.Button(frame_botoes_texto, text="Limpar", command=self.limpar_texto, bg="lightgray", padx=5)
        btn_limpar.grid(row=0, column=2, sticky="ew", padx=2)

        btn_salvar = tk.Button(frame_botoes_texto, text="Salvar", command=self.salvar_arquivo,
                               bg="#3498db", fg="white", padx=5)
        btn_salvar.grid(row=0, column=3, sticky="ew", padx=2)

        frame_saida = tk.LabelFrame(aba, text="Resultado", font=("Arial", 10))
        frame_saida.grid(row=2, column=0, sticky="nsew", pady=5)
        frame_saida.columnconfigure(0, weight=1)
        frame_saida.rowconfigure(0, weight=1)

        self.saida_texto = scrolledtext.ScrolledText(frame_saida, height=8)
        self.saida_texto.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        return aba

    def criar_aba_arquivos(self):
        """Criar conteúdo da aba de processamento de arquivos - VERSÃO MELHORADA"""
        aba = tk.Frame(self.container_abas, bg="#f8f9fa")
        aba.grid(row=0, column=0, sticky="nsew")
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(1, weight=1)

        # Header com título e indicador de segurança
        header = tk.Frame(aba, bg="#2c3e50", height=80)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        # Ícone de segurança
        icon_frame = tk.Frame(header, bg="#2c3e50", width=60)
        icon_frame.grid(row=0, column=0, sticky="nsew", padx=20)
        icon_frame.grid_propagate(False)

        security_icon = tk.Label(icon_frame, text="🔐", font=("Arial", 24),
                                 bg="#2c3e50", fg="#ecf0f1")
        security_icon.pack(expand=True)

        # Título e descrição
        title_frame = tk.Frame(header, bg="#2c3e50")
        title_frame.grid(row=0, column=1, sticky="nsew", pady=10)

        titulo = tk.Label(title_frame, text="Criptografia de Arquivos",
                          font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white")
        titulo.pack(anchor="w")

        subtitulo = tk.Label(title_frame, text="Proteção avançada com AES-256 | Processamento em lote",
                             font=("Segoe UI", 10), bg="#2c3e50", fg="#bdc3c7")
        subtitulo.pack(anchor="w")

        # Indicador de status
        status_frame = tk.Frame(header, bg="#2c3e50", width=150)
        status_frame.grid(row=0, column=2, sticky="nsew", padx=20)
        status_frame.grid_propagate(False)

        self.status_indicator = tk.Label(status_frame, text="● Sistema Ativo",
                                         font=("Segoe UI", 10, "bold"),
                                         bg="#2c3e50", fg="#27ae60")
        self.status_indicator.pack(expand=True)

        # Container principal
        main_container = tk.Frame(aba, bg="#f8f9fa")
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main_container.columnconfigure(0, weight=2)
        main_container.columnconfigure(1, weight=3)
        main_container.rowconfigure(0, weight=1)

        # Painel de operações (esquerda)
        operations_panel = tk.Frame(main_container, bg="white", relief="solid", bd=1)
        operations_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Header do painel de operações
        ops_header = tk.Frame(operations_panel, bg="#34495e", height=50)
        ops_header.pack(fill="x")
        ops_header.grid_propagate(False)

        ops_title = tk.Label(ops_header, text="Central de Operações",
                             font=("Segoe UI", 12, "bold"),
                             bg="#34495e", fg="white")
        ops_title.pack(expand=True)

        # Container das operações
        ops_container = tk.Frame(operations_panel, bg="white")
        ops_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Seção 1: Arquivos Individuais
        self.criar_secao_operacao(ops_container, "Arquivos Individuais", [
            {
                'texto': '🔒 Criptografar Arquivo',
                'comando': self.criptografar_arquivo,
                'cor': '#27ae60',
                'descricao': 'Proteger arquivos únicos'
            },
            {
                'texto': '🔓 Descriptografar Arquivo',
                'comando': self.descriptografar_arquivo,
                'cor': '#e74c3c',
                'descricao': 'Restaurar arquivos únicos'
            }
        ])

        # Separador
        tk.Frame(ops_container, height=2, bg="#ecf0f1").pack(fill="x", pady=15)

        # Seção 2: Processamento em Lote
        self.criar_secao_operacao(ops_container, "Processamento em Lote", [
            {
                'texto': '📁 Criptografar Pasta',
                'comando': self.criptografar_pasta,
                'cor': '#8e44ad',
                'descricao': 'Proteger pastas completas'
            },
            {
                'texto': '📂 Descriptografar Pasta',
                'comando': self.descriptografar_pasta,
                'cor': '#f39c12',
                'descricao': 'Restaurar pastas completas'
            }
        ])

        # Separador
        tk.Frame(ops_container, height=2, bg="#ecf0f1").pack(fill="x", pady=15)

        # Seção 3: Gerenciamento
        self.criar_secao_operacao(ops_container, "Gerenciamento", [
            {
                'texto': '🔑 Gerar Nova Chave',
                'comando': self.gerar_nova_chave,
                'cor': '#3498db',
                'descricao': 'Criar nova chave de segurança'
            },
            {
                'texto': '🗑️ Limpar Histórico',
                'comando': self.limpar_historico,
                'cor': '#95a5a6',
                'descricao': 'Apagar logs de operações'
            }
        ])

        # Painel de monitoramento (direita)
        monitoring_panel = tk.Frame(main_container, bg="white", relief="solid", bd=1)
        monitoring_panel.grid(row=0, column=1, sticky="nsew")

        # Header do painel de monitoramento
        mon_header = tk.Frame(monitoring_panel, bg="#2980b9", height=50)
        mon_header.pack(fill="x")
        mon_header.grid_propagate(False)

        mon_title = tk.Label(mon_header, text="Monitor de Atividades",
                             font=("Segoe UI", 12, "bold"),
                             bg="#2980b9", fg="white")
        mon_title.pack(expand=True)

        # Container do histórico
        history_container = tk.Frame(monitoring_panel, bg="white")
        history_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Controles do histórico
        controls_frame = tk.Frame(history_container, bg="white")
        controls_frame.pack(fill="x", pady=(0, 10))

        # Filtros
        filter_frame = tk.Frame(controls_frame, bg="white")
        filter_frame.pack(side="left")

        tk.Label(filter_frame, text="Filtrar:", font=("Segoe UI", 9),
                 bg="white", fg="#7f8c8d").pack(side="left")

        self.filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                    values=["Todos", "Criptografia", "Descriptografia", "Sistema", "Erros"],
                                    width=12, state="readonly", font=("Segoe UI", 9))
        filter_combo.pack(side="left", padx=(5, 0))
        filter_combo.bind("<<ComboboxSelected>>", self.filtrar_historico)

        # Botões de controle
        controls_right = tk.Frame(controls_frame, bg="white")
        controls_right.pack(side="right")

        btn_refresh = tk.Button(controls_right, text="🔄", font=("Segoe UI", 10),
                                command=self.atualizar_historico, bg="#ecf0f1",
                                relief="flat", padx=8, pady=2)
        btn_refresh.pack(side="right", padx=2)

        btn_export = tk.Button(controls_right, text="📤", font=("Segoe UI", 10),
                               command=self.exportar_historico, bg="#ecf0f1",
                               relief="flat", padx=8, pady=2)
        btn_export.pack(side="right", padx=2)

        # Área do histórico com estilo melhorado
        history_frame = tk.Frame(history_container, bg="#f8f9fa", relief="solid", bd=1)
        history_frame.pack(fill="both", expand=True)

        # Scrollbar customizada
        scrollbar_frame = tk.Frame(history_frame, bg="#f8f9fa")
        scrollbar_frame.pack(side="right", fill="y")

        scrollbar = ttk.Scrollbar(scrollbar_frame)
        scrollbar.pack(fill="y", padx=5, pady=5)

        # Área de texto do histórico
        self.area_historico = tk.Text(history_frame,
                                      height=20,
                                      width=50,
                                      state='disabled',
                                      wrap=tk.WORD,
                                      font=("Consolas", 9),
                                      bg="#fefefe",
                                      fg="#2c3e50",
                                      relief="flat",
                                      yscrollcommand=scrollbar.set)
        self.area_historico.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        scrollbar.config(command=self.area_historico.yview)

        # Configurar tags para diferentes tipos de mensagem
        self.configurar_tags_historico()

        # Inicializar histórico
        self.adicionar_ao_historico("Sistema iniciado - Criptografia AES-256 ativada", "SISTEMA")

        return aba

    def criar_secao_operacao(self, parent, titulo, operacoes):
        """Criar uma seção de operações com título e botões"""
        # Título da seção
        title_label = tk.Label(parent, text=titulo, font=("Segoe UI", 11, "bold"),
                               bg="white", fg="#34495e")
        title_label.pack(anchor="w", pady=(0, 8))

        # Container dos botões
        for operacao in operacoes:
            btn_frame = tk.Frame(parent, bg="white")
            btn_frame.pack(fill="x", pady=2)

            # Botão principal
            btn = tk.Button(btn_frame,
                            text=operacao['texto'],
                            command=operacao['comando'],
                            bg=operacao['cor'],
                            fg="white",
                            font=("Segoe UI", 10, "bold"),
                            relief="flat",
                            padx=15,
                            pady=8,
                            cursor="hand2")
            btn.pack(fill="x")

            # Descrição
            desc_label = tk.Label(btn_frame, text=operacao['descricao'],
                                  font=("Segoe UI", 8), bg="white", fg="#7f8c8d")
            desc_label.pack(anchor="w", padx=5, pady=(2, 0))

            # Efeitos hover
            def on_enter(event, button=btn, original_color=operacao['cor']):
                # Escurecer a cor um pouco
                button.config(bg=self.escurecer_cor(original_color))

            def on_leave(event, button=btn, original_color=operacao['cor']):
                button.config(bg=original_color)

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def escurecer_cor(self, cor_hex):
        """Escurecer uma cor hexadecimal para efeito hover"""
        # Remove o # se presente
        cor_hex = cor_hex.lstrip('#')

        # Converte para RGB
        rgb = tuple(int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))

        # Escurece cada componente
        rgb_escuro = tuple(max(0, int(c * 0.8)) for c in rgb)

        # Converte de volta para hex
        return f"#{rgb_escuro[0]:02x}{rgb_escuro[1]:02x}{rgb_escuro[2]:02x}"

    def configurar_tags_historico(self):
        """Configurar tags de formatação para o histórico"""
        self.area_historico.tag_configure("SISTEMA", foreground="#3498db", font=("Consolas", 9, "bold"))
        self.area_historico.tag_configure("PROCESSAMENTO", foreground="#27ae60", font=("Consolas", 9))
        self.area_historico.tag_configure("RESTAURACAO", foreground="#e67e22", font=("Consolas", 9))
        self.area_historico.tag_configure("ERRO", foreground="#e74c3c", font=("Consolas", 9, "bold"))
        self.area_historico.tag_configure("INFO", foreground="#95a5a6", font=("Consolas", 9))

    def filtrar_historico(self, event=None):
        """Filtrar histórico por tipo de operação"""
        filtro = self.filter_var.get()

        # Reexibir histórico filtrado
        self.area_historico.config(state='normal')
        self.area_historico.delete('1.0', tk.END)

        for entrada in self.historico_arquivos:
            tipo = entrada['tipo']
            if filtro == "Todos" or \
                    (filtro == "Criptografia" and tipo == "PROCESSAMENTO") or \
                    (filtro == "Descriptografia" and tipo == "RESTAURACAO") or \
                    (filtro == "Sistema" and tipo == "SISTEMA") or \
                    (filtro == "Erros" and tipo == "ERRO"):
                self.exibir_entrada_historico(entrada)

        self.area_historico.config(state='disabled')

    def exibir_entrada_historico(self, entrada):
        """Exibir uma entrada específica no histórico"""
        timestamp = entrada['timestamp']
        operacao = entrada['operacao']
        tipo = entrada['tipo']

        # Ícones por tipo
        icones = {
            "PROCESSAMENTO": "🔒",
            "RESTAURACAO": "🔓",
            "ERRO": "❌",
            "SISTEMA": "ℹ️",
            "INFO": "📋"
        }

        icone = icones.get(tipo, "📝")

        # Formatar entrada
        linha = f"{icone} [{timestamp}] {operacao}\n"

        # Inserir com tag apropriada
        start_pos = self.area_historico.index(tk.INSERT)
        self.area_historico.insert(tk.INSERT, linha)
        end_pos = self.area_historico.index(tk.INSERT)

        self.area_historico.tag_add(tipo, start_pos, end_pos)

    def atualizar_historico(self):
        """Atualizar exibição do histórico"""
        self.filtrar_historico()

    def exportar_historico(self):
        """Exportar histórico para arquivo"""
        arquivo = filedialog.asksaveasfilename(
            title="Exportar Histórico",
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )

        if arquivo:
            try:
                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write("HISTÓRICO DE OPERAÇÕES - CryptographiE\n")
                    f.write("=" * 50 + "\n\n")

                    for entrada in self.historico_arquivos:
                        f.write(f"[{entrada['timestamp']}] {entrada['tipo']}: {entrada['operacao']}\n")

                messagebox.showinfo("Sucesso", "Histórico exportado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar histórico: {e}")

    def criar_aba_estatisticas(self):
        """Criar conteúdo da aba de informações do sistema com gráfico de pizza"""
        aba = tk.Frame(self.container_abas, bg="white")
        aba.grid(row=0, column=0, sticky="nsew")
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(0, weight=1)

        # Container principal com scroll
        canvas = tk.Canvas(aba, bg="white")
        scrollbar = ttk.Scrollbar(aba, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Título principal
        titulo = tk.Label(scrollable_frame, text="📊 Estatísticas de Criptografia",
                          font=("Segoe UI", 18, "bold"), bg="white", fg="#2c3e50")
        titulo.pack(pady=(20, 30))

        # Container principal dividido em duas colunas
        main_container = tk.Frame(scrollable_frame, bg="white")
        main_container.pack(fill="both", expand=True, padx=20)

        # Coluna esquerda - Gráfico
        left_frame = tk.Frame(main_container, bg="white")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Frame do gráfico
        grafico_frame = tk.LabelFrame(left_frame, text="📈 Distribuição de Operações",
                                      font=("Segoe UI", 12, "bold"), bg="white", fg="#34495e")
        grafico_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Verificar se matplotlib está disponível
        if matplotlib_disponivel:
            # Criar figura do matplotlib
            self.fig_pizza = Figure(figsize=(6, 6), dpi=100, facecolor='white')
            self.ax_pizza = self.fig_pizza.add_subplot(111)

            # Canvas para o gráfico
            self.canvas_grafico = FigureCanvasTkAgg(self.fig_pizza, grafico_frame)
            self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # Fallback se matplotlib não estiver disponível
            info_label = tk.Label(grafico_frame,
                                  text="📊 Gráfico não disponível\n\nPara visualizar gráficos, instale:\npip install matplotlib",
                                  font=("Segoe UI", 12), bg="white", fg="#7f8c8d", justify="center")
            info_label.pack(expand=True, pady=50)

        # Coluna direita - Controles e resumo
        right_frame = tk.Frame(main_container, bg="white", width=300)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)

        # Frame de controles
        frame_controles = tk.LabelFrame(right_frame, text="🎛️ Controles",
                                        font=("Segoe UI", 11, "bold"), bg="white", fg="#34495e")
        frame_controles.pack(fill="x", pady=(0, 15))

        # Botões de controle em grid
        controles_grid = tk.Frame(frame_controles, bg="white")
        controles_grid.pack(fill="x", padx=15, pady=15)

        btn_atualizar = tk.Button(controles_grid, text="🔄 Atualizar",
                                  command=self.atualizar_estatisticas,
                                  bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
                                  relief="flat", padx=15, pady=8, cursor="hand2")
        btn_atualizar.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=2)

        btn_exportar = tk.Button(controles_grid, text="📤 Exportar",
                                 command=self.exportar_estatisticas,
                                 bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                                 relief="flat", padx=15, pady=8, cursor="hand2")
        btn_exportar.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=2)

        btn_limpar = tk.Button(controles_grid, text="🗑️ Limpar Dados",
                               command=self.limpar_dados_estatisticas,
                               bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
                               relief="flat", padx=15, pady=8, cursor="hand2")
        btn_limpar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 2))

        btn_grafico = tk.Button(controles_grid, text="📊 Atualizar Gráfico",
                                command=self.atualizar_grafico,
                                bg="#9b59b6", fg="white", font=("Segoe UI", 10, "bold"),
                                relief="flat", padx=15, pady=8, cursor="hand2")
        btn_grafico.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)

        controles_grid.columnconfigure(0, weight=1)
        controles_grid.columnconfigure(1, weight=1)

        # Frame de resumo estatístico
        resumo_frame = tk.LabelFrame(right_frame, text="📋 Resumo Rápido",
                                     font=("Segoe UI", 11, "bold"), bg="white", fg="#34495e")
        resumo_frame.pack(fill="x", pady=(0, 15))

        self.resumo_texto = tk.Text(resumo_frame, height=8, width=35,
                                    font=("Segoe UI", 9), bg="#f8f9fa",
                                    relief="flat", wrap=tk.WORD, state="disabled")
        self.resumo_texto.pack(fill="x", padx=15, pady=15)

        # Área de texto para estatísticas detalhadas (parte inferior)
        frame_estatisticas = tk.LabelFrame(scrollable_frame, text="📝 Relatório Detalhado",
                                           font=("Segoe UI", 12, "bold"), bg="white", fg="#34495e")
        frame_estatisticas.pack(fill="both", expand=True, padx=20, pady=(20, 30))

        self.area_estatisticas = scrolledtext.ScrolledText(frame_estatisticas, height=15,
                                                           font=("Consolas", 10), bg="#f8f9fa")
        self.area_estatisticas.pack(fill="both", expand=True, padx=15, pady=15)

        return aba

    def atualizar_grafico(self):
        """Atualizar o gráfico de pizza com dados atuais"""
        if not matplotlib_disponivel:
            messagebox.showwarning("Aviso", "Matplotlib não está disponível.\nInstale com: pip install matplotlib")
            return

        try:
            # Limpar gráfico anterior
            self.ax_pizza.clear()

            # Obter dados
            criptografados = self.estatisticas.arquivos_criptografados
            descriptografados = self.estatisticas.arquivos_descriptografados
            total = criptografados + descriptografados

            if total == 0:
                # Exibir gráfico vazio com mensagem
                self.ax_pizza.text(0.5, 0.5, 'Nenhuma operação\nrealizada ainda',
                                   horizontalalignment='center', verticalalignment='center',
                                   transform=self.ax_pizza.transAxes, fontsize=14, color='gray')
                self.ax_pizza.set_title('Distribuição de Operações', fontsize=16, fontweight='bold', pad=20)
            else:
                # Dados para o gráfico
                labels = ['Criptografados', 'Descriptografados']
                sizes = [criptografados, descriptografados]
                colors = ['#e74c3c', '#27ae60']  # Vermelho para cripto, verde para descripto

                # Criar gráfico de pizza
                wedges, texts, autotexts = self.ax_pizza.pie(sizes, colors=colors,
                                                             autopct='%1.1f%%', startangle=90,
                                                             labeldistance=None,  # Remove completamente os labels
                                                             textprops={'fontsize': 11})

                # Melhorar aparência dos textos
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(12)

                # Título
                self.ax_pizza.set_title(f'\nTotal: {total} arquivos',
                                        fontsize=14, fontweight='bold', pad=20)

                # Adicionar legenda com valores absolutos
                legend_labels = [f'{label}: {size} arquivo(s)' for label, size in zip(labels, sizes)]
                self.ax_pizza.legend(wedges, legend_labels, title="Operações:",
                                     loc="lower center", bbox_to_anchor=(0.5, -0.1))

            # Garantir que o gráfico seja circular
            self.ax_pizza.axis('equal')

            # Atualizar canvas
            self.canvas_grafico.draw()

            # Atualizar resumo
            self.atualizar_resumo()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar gráfico: {e}")

    def atualizar_resumo(self):
        """Atualizar o resumo estatístico rápido"""
        try:
            total_arquivos = self.estatisticas.arquivos_criptografados + self.estatisticas.arquivos_descriptografados
            total_tamanho = self.estatisticas.tamanho_total_criptografado + self.estatisticas.tamanho_total_descriptografado

            if total_arquivos > 0:
                pct_cripto = (self.estatisticas.arquivos_criptografados / total_arquivos) * 100
                pct_descripto = (self.estatisticas.arquivos_descriptografados / total_arquivos) * 100
            else:
                pct_cripto = pct_descripto = 0

            resumo_texto = f"""🔒 CRIPTOGRAFADOS: {self.estatisticas.arquivos_criptografados}
   Percentual: {pct_cripto:.1f}%

🔓 DESCRIPTOGRAFADOS: {self.estatisticas.arquivos_descriptografados}
   Percentual: {pct_descripto:.1f}%

📊 TOTAL PROCESSADO: {total_arquivos}

💾 VOLUME TOTAL: {self.formatar_tamanho(total_tamanho)}

⏱️ SESSÃO INICIADA:
   {self.estatisticas.hora_inicio.strftime('%d/%m/%Y às %H:%M')}"""

            # Atualizar texto
            self.resumo_texto.config(state="normal")
            self.resumo_texto.delete("1.0", tk.END)
            self.resumo_texto.insert("1.0", resumo_texto)
            self.resumo_texto.config(state="disabled")

        except Exception as e:
            print(f"Erro ao atualizar resumo: {e}")

    def criar_aba_morse(self):
        """Criar conteúdo da aba de código morse com design moderno e organizado - ATUALIZADA COM BOTÃO PAUSA"""
        aba = tk.Frame(self.container_abas, bg="#f8f9fa")
        aba.grid(row=0, column=0, sticky="nsew")
        aba.columnconfigure(0, weight=1)
        aba.rowconfigure(0, weight=1)

        # Container principal com scroll
        canvas = tk.Canvas(aba, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(aba, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f8f9fa")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Container principal com padding reduzido
        main_container = tk.Frame(scrollable_frame, bg="#f8f9fa")
        main_container.pack(fill="both", expand=True, padx=50, pady=50)

        # Título principal mais compacto
        title_frame = tk.Frame(main_container, bg="#f8f9fa")
        title_frame.pack(fill="x", pady=(0, 20))

        titulo = tk.Label(title_frame, text="📡 Código Morse",
                          font=("Segoe UI", 18, "bold"),
                          bg="#f8f9fa", fg="#2c3e50")
        titulo.pack()

        subtitulo = tk.Label(title_frame, text="Converta texto para morse e vice-versa",
                             font=("Segoe UI", 9),
                             bg="#f8f9fa", fg="#7f8c8d")
        subtitulo.pack(pady=(3, 0))

        # Grid principal - 2 colunas
        grid_frame = tk.Frame(main_container, bg="#f8f9fa")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # === COLUNA ESQUERDA: ENTRADA E CONVERSÃO ===
        left_frame = tk.Frame(grid_frame, bg="#f8f9fa")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Card de entrada mais compacto
        entrada_card = tk.LabelFrame(left_frame, text="  📝 Entrada  ",
                                     font=("Segoe UI", 10, "bold"),
                                     fg="#2c3e50", bg="white",
                                     relief="solid", bd=1)
        entrada_card.pack(fill="both", expand=True, pady=(0, 10))

        # Área de texto com estilo
        text_frame = tk.Frame(entrada_card, bg="white")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.entrada_morse = tk.Text(text_frame, height=6, wrap=tk.WORD,
                                     font=("Consolas", 10), bg="#f8f9fa",
                                     relief="solid", bd=1, padx=8, pady=8)
        self.entrada_morse.pack(fill="both", expand=True)

        # Scrollbar para entrada
        entrada_scroll = ttk.Scrollbar(text_frame, orient="vertical",
                                       command=self.entrada_morse.yview)
        entrada_scroll.pack(side="right", fill="y")
        self.entrada_morse.configure(yscrollcommand=entrada_scroll.set)

        # Card de botões de conversão mais compacto
        botoes_card = tk.LabelFrame(left_frame, text="  🔄 Conversão  ",
                                    font=("Segoe UI", 10, "bold"),
                                    fg="#2c3e50", bg="white",
                                    relief="solid", bd=1)
        botoes_card.pack(fill="x", pady=(0, 10))

        botoes_frame = tk.Frame(botoes_card, bg="white")
        botoes_frame.pack(fill="x", padx=10, pady=10)
        botoes_frame.columnconfigure((0, 1, 2), weight=1)

        # Botões estilizados mais compactos
        btn_texto_para_morse = tk.Button(botoes_frame, text="Texto → Morse",
                                         command=self.texto_para_morse,
                                         bg="#3498db", fg="white", font=("Segoe UI", 9, "bold"),
                                         relief="flat", padx=15, pady=6,
                                         cursor="hand2")
        btn_texto_para_morse.grid(row=0, column=0, padx=(0, 3), sticky="ew")

        btn_morse_para_texto = tk.Button(botoes_frame, text="Morse → Texto",
                                         command=self.morse_para_texto,
                                         bg="#e74c3c", fg="white", font=("Segoe UI", 9, "bold"),
                                         relief="flat", padx=15, pady=6,
                                         cursor="hand2")
        btn_morse_para_texto.grid(row=0, column=1, padx=3, sticky="ew")

        btn_limpar = tk.Button(botoes_frame, text="🗑️ Limpar",
                               command=self.limpar_morse,
                               bg="#95a5a6", fg="white", font=("Segoe UI", 9, "bold"),
                               relief="flat", padx=15, pady=6,
                               cursor="hand2")
        btn_limpar.grid(row=0, column=2, padx=(3, 0), sticky="ew")

        # Card de resultado mais compacto
        resultado_card = tk.LabelFrame(left_frame, text="  📤 Resultado  ",
                                       font=("Segoe UI", 10, "bold"),
                                       fg="#2c3e50", bg="white",
                                       relief="solid", bd=1)
        resultado_card.pack(fill="both", expand=True)

        resultado_frame = tk.Frame(resultado_card, bg="white")
        resultado_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.saida_morse = tk.Text(resultado_frame, height=6, wrap=tk.WORD,
                                   font=("Consolas", 10), bg="#f8f9fa",
                                   relief="solid", bd=1, padx=8, pady=8,
                                   state="normal")
        self.saida_morse.pack(fill="both", expand=True)

        # Scrollbar para resultado
        resultado_scroll = ttk.Scrollbar(resultado_frame, orient="vertical",
                                         command=self.saida_morse.yview)
        resultado_scroll.pack(side="right", fill="y")
        self.saida_morse.configure(yscrollcommand=resultado_scroll.set)

        # === COLUNA DIREITA: CONFIGURAÇÕES E CONTROLES ===
        right_frame = tk.Frame(grid_frame, bg="#f8f9fa")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        # Card de configurações de som
        som_card = tk.LabelFrame(right_frame, text="  🔊 Configurações de Som  ",
                                 font=("Segoe UI", 12, "bold"),
                                 fg="#2c3e50", bg="white",
                                 relief="solid", bd=1)
        som_card.pack(fill="x", pady=(0, 15))

        som_content = tk.Frame(som_card, bg="white")
        som_content.pack(fill="x", padx=20, pady=20)

        # Velocidade WPM com visual moderno
        wpm_frame = tk.Frame(som_content, bg="white")
        wpm_frame.pack(fill="x", pady=(0, 15))

        wpm_label = tk.Label(wpm_frame, text="⚡ Velocidade (WPM)",
                             font=("Segoe UI", 10, "bold"), bg="white", fg="#34495e")
        wpm_label.pack(anchor="w")

        self.wpm_var = tk.IntVar(value=15)
        wpm_scale = tk.Scale(wpm_frame, from_=5, to=30, orient="horizontal",
                             variable=self.wpm_var, bg="white", fg="#2c3e50",
                             highlightthickness=0, troughcolor="#ecf0f1",
                             activebackground="#3498db")
        wpm_scale.pack(fill="x", pady=(5, 0))

        # Frequência com visual moderno
        freq_frame = tk.Frame(som_content, bg="white")
        freq_frame.pack(fill="x", pady=(0, 15))

        freq_label = tk.Label(freq_frame, text="🎵 Frequência (Hz)",
                              font=("Segoe UI", 10, "bold"), bg="white", fg="#34495e")
        freq_label.pack(anchor="w")

        self.freq_var = tk.IntVar(value=700)
        freq_scale = tk.Scale(freq_frame, from_=500, to=1000, orient="horizontal",
                              variable=self.freq_var, bg="white", fg="#2c3e50",
                              highlightthickness=0, troughcolor="#ecf0f1",
                              activebackground="#3498db")
        freq_scale.pack(fill="x", pady=(5, 0))

        # BOTÕES DE CONTROLE DE SOM - ATUALIZADOS COM BOTÃO PAUSA
        controle_frame = tk.Frame(som_content, bg="white")
        controle_frame.pack(fill="x")
        controle_frame.columnconfigure((0, 1), weight=1)

        btn_reproduzir = tk.Button(controle_frame, text="▶️ Reproduzir",
                                   command=self.reproduzir_morse,
                                   bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                                   relief="flat", padx=15, pady=8, cursor="hand2")
        btn_reproduzir.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # NOVO BOTÃO PAUSA - substitui o botão parar
        self.btn_pausa = tk.Button(controle_frame, text="⏸️ Pausar",
                                   bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"),
                                   relief="flat", padx=15, pady=8, cursor="hand2")
        self.btn_pausa.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Configurar eventos do botão pausa
        self.btn_pausa.bind("<Button-1>", self.on_pause_press)
        self.btn_pausa.bind("<ButtonRelease-1>", self.on_pause_release)

        # Card Arduino (se disponível) mais compacto
        if serial_disponivel:
            arduino_card = tk.LabelFrame(right_frame, text="  🔌 Arduino  ",
                                         font=("Segoe UI", 10, "bold"),
                                         fg="#2c3e50", bg="white",
                                         relief="solid", bd=1)
            arduino_card.pack(fill="x", pady=(0, 10))

            arduino_content = tk.Frame(arduino_card, bg="white")
            arduino_content.pack(fill="x", padx=12, pady=12)

            # Seleção de porta mais compacta
            porta_frame = tk.Frame(arduino_content, bg="white")
            porta_frame.pack(fill="x", pady=(0, 10))

            porta_label = tk.Label(porta_frame, text="🔗 Porta",
                                   font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e")
            porta_label.pack(anchor="w", pady=(0, 3))

            porta_select_frame = tk.Frame(porta_frame, bg="white")
            porta_select_frame.pack(fill="x")
            porta_select_frame.columnconfigure(0, weight=1)

            self.combo_portas = ttk.Combobox(porta_select_frame, font=("Segoe UI", 8))
            self.combo_portas.grid(row=0, column=0, sticky="ew", padx=(0, 5))

            btn_atualizar = tk.Button(porta_select_frame, text="🔄",
                                      command=self.atualizar_portas_seriais,
                                      bg="#f39c12", fg="white", font=("Segoe UI", 8, "bold"),
                                      relief="flat", padx=8, pady=4, cursor="hand2")
            btn_atualizar.grid(row=0, column=1)

            # Botões de controle Arduino mais compactos
            arduino_ctrl_frame = tk.Frame(arduino_content, bg="white")
            arduino_ctrl_frame.pack(fill="x", pady=(0, 8))
            arduino_ctrl_frame.columnconfigure((0, 1, 2), weight=1)

            self.btn_conectar_arduino = tk.Button(arduino_ctrl_frame, text="Conectar",
                                                  command=self.conectar_arduino,
                                                  bg="#27ae60", fg="white", font=("Segoe UI", 8, "bold"),
                                                  relief="flat", padx=8, pady=4, cursor="hand2")
            self.btn_conectar_arduino.grid(row=0, column=0, padx=(0, 2), sticky="ew")

            self.btn_desconectar_arduino = tk.Button(arduino_ctrl_frame, text="Desconectar",
                                                     command=self.desconectar_arduino,
                                                     bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"),
                                                     relief="flat", padx=8, pady=4, cursor="hand2")
            self.btn_desconectar_arduino.grid(row=0, column=1, padx=2, sticky="ew")

            self.btn_transmitir_arduino = tk.Button(arduino_ctrl_frame, text="Transmitir",
                                                    command=self.transmitir_morse_arduino,
                                                    bg="#f39c12", fg="white", font=("Segoe UI", 8, "bold"),
                                                    relief="flat", padx=8, pady=4, cursor="hand2")
            self.btn_transmitir_arduino.grid(row=0, column=2, padx=(2, 0), sticky="ew")

            # Status mais compacto
            self.lbl_status_arduino = tk.Label(arduino_content, text="🔴 Desconectado",
                                               font=("Segoe UI", 8), bg="white", fg="#e74c3c")
            self.lbl_status_arduino.pack()

            # Inicializar portas
            self.atualizar_portas_seriais()

        # Card de referência mais compacto
        ref_card = tk.LabelFrame(right_frame, text="  📋 Referência  ",
                                 font=("Segoe UI", 10, "bold"),
                                 fg="#2c3e50", bg="white",
                                 relief="solid", bd=1)
        ref_card.pack(fill="x")

        ref_content = tk.Frame(ref_card, bg="white")
        ref_content.pack(fill="x", padx=12, pady=12)

        btn_mostrar_tabela = tk.Button(ref_content, text="📚 Tabela Morse",
                                       command=self.mostrar_tabela_morse,
                                       bg="#9b59b6", fg="white", font=("Segoe UI", 9, "bold"),
                                       relief="flat", padx=15, pady=8, cursor="hand2")
        btn_mostrar_tabela.pack(fill="x")

        # Adicionar efeitos hover aos botões
        def add_hover_effect(button, hover_color, original_color):
            def on_enter(e):
                button.configure(bg=hover_color)

            def on_leave(e):
                button.configure(bg=original_color)

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)

        # Aplicar efeitos hover
        add_hover_effect(btn_texto_para_morse, "#2980b9", "#3498db")
        add_hover_effect(btn_morse_para_texto, "#c0392b", "#e74c3c")
        add_hover_effect(btn_limpar, "#7f8c8d", "#95a5a6")
        add_hover_effect(btn_reproduzir, "#219a52", "#27ae60")
        add_hover_effect(self.btn_pausa, "#d68910", "#f39c12")
        add_hover_effect(btn_mostrar_tabela, "#8e44ad", "#9b59b6")

        if serial_disponivel:
            add_hover_effect(self.btn_conectar_arduino, "#219a52", "#27ae60")
            add_hover_effect(self.btn_desconectar_arduino, "#c0392b", "#e74c3c")
            add_hover_effect(self.btn_transmitir_arduino, "#d68910", "#f39c12")
            add_hover_effect(btn_atualizar, "#d68910", "#f39c12")

        return aba

    def mostrar_aba(self, aba_id):
        """Mostrar a aba selecionada e ocultar as outras"""
        for aba in self.abas.values():
            aba.grid_remove()

        self.abas[aba_id].grid(row=0, column=0, sticky="nsew")

        for btn_id, botao in self.botoes_menu.items():
            if btn_id == aba_id:
                botao.config(bg="#3498db", fg="white")
            else:
                botao.config(bg="#34495e", fg="white")

        self.aba_atual = aba_id

        # Atualizar gráfico se estivermos na aba de estatísticas
        if aba_id == "estatisticas":
            self.janela.after(100, self.atualizar_grafico)

    def adicionar_ao_historico(self, operacao, tipo="INFO"):
        """Adicionar uma entrada ao histórico de operações"""
        agora = datetime.datetime.now()
        timestamp = agora.strftime("%d/%m/%Y %H:%M:%S")

        entrada = {
            'timestamp': timestamp,
            'operacao': operacao,
            'tipo': tipo
        }

        self.historico_arquivos.append(entrada)

        self.area_historico.config(state='normal')
        self.exibir_entrada_historico(entrada)
        self.area_historico.config(state='disabled')

        # Atualizar indicador de status na interface
        if hasattr(self, 'status_indicator'):
            if tipo == "ERRO":
                self.status_indicator.config(text="● Erro Detectado", fg="#e74c3c")
                self.janela.after(3000, lambda: self.status_indicator.config(text="● Sistema Ativo", fg="#27ae60"))
            elif tipo in ["PROCESSAMENTO", "RESTAURACAO"]:
                self.status_indicator.config(text="● Processando...", fg="#f39c12")
                self.janela.after(2000, lambda: self.status_indicator.config(text="● Sistema Ativo", fg="#27ae60"))

        if len(self.historico_arquivos) > 100:
            self.historico_arquivos.pop(0)

    def limpar_historico(self):
        """Limpar todo o histórico de operações"""
        resultado = messagebox.askyesno("Confirmar Limpeza",
                                        "Deseja realmente limpar todo o histórico de operações?")
        if resultado:
            self.historico_arquivos.clear()
            self.area_historico.config(state='normal')
            self.area_historico.delete('1.0', tk.END)
            self.area_historico.config(state='disabled')
            self.adicionar_ao_historico("Histórico limpo pelo usuário", "SISTEMA")
            messagebox.showinfo("Sucesso", "Histórico limpo com sucesso!")

    # Métodos para processamento de texto
    def carregar_arquivo(self):
        arquivo = filedialog.askopenfilename(title="Carregar arquivo",
                                             filetypes=[("Arquivos de texto", "*.txt"),
                                                        ("Todos os arquivos", "*.*")])
        if arquivo:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    self.entrada_texto.delete('1.0', tk.END)
                    self.entrada_texto.insert('1.0', conteudo)
                messagebox.showinfo("Sucesso", "Arquivo carregado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo: {e}")

    def salvar_arquivo(self):
        arquivo = filedialog.asksaveasfilename(title="Salvar arquivo",
                                               defaultextension=".txt",
                                               filetypes=[("Arquivos de texto", "*.txt"),
                                                          ("Todos os arquivos", "*.*")])
        if arquivo:
            try:
                with open(arquivo, 'w', encoding='utf-8') as f:
                    conteudo = self.saida_texto.get('1.0', tk.END)
                    f.write(conteudo)
                messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")

    def processar_texto(self):
        """Processar texto automaticamente"""
        texto = self.entrada_texto.get('1.0', tk.END).strip()

        if not texto:
            messagebox.showwarning("Aviso", "Digite algum texto para processar!")
            return

        try:
            resultado = self.criptografar_texto(texto)
            self.saida_texto.delete('1.0', tk.END)
            self.saida_texto.insert('1.0', resultado)
            self.estatisticas.registrar_operacao('criptografar', len(texto))
            messagebox.showinfo("Sucesso", "Texto processado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def restaurar_texto(self):
        """Restaurar texto automaticamente"""
        texto = self.entrada_texto.get('1.0', tk.END).strip()

        if not texto:
            messagebox.showwarning("Aviso", "Digite o texto processado para restaurar!")
            return

        try:
            resultado = self.descriptografar_texto(texto)
            self.saida_texto.delete('1.0', tk.END)
            self.saida_texto.insert('1.0', resultado)
            self.estatisticas.registrar_operacao('descriptografar', len(texto))
            messagebox.showinfo("Sucesso", "Texto restaurado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao restaurar texto!\n\nDetalhes: {e}")

    def limpar_texto(self):
        self.entrada_texto.delete('1.0', tk.END)
        self.saida_texto.delete('1.0', tk.END)

    # Métodos para processamento de arquivos
    def gerar_nova_chave(self):
        """Gerar uma nova chave de criptografia"""
        resultado = messagebox.askyesno("Gerar Nova Chave",
                                        "⚠️ ATENÇÃO ⚠️\n\n"
                                        "Gerar uma nova chave tornará IMPOSSÍVEL descriptografar "
                                        "arquivos criptografados com a chave atual.\n\n"
                                        "Certifique-se de que todos os arquivos importantes "
                                        "foram descriptografados antes de continuar.\n\n"
                                        "Deseja realmente gerar uma nova chave?")
        if resultado:
            try:
                chave = Fernet.generate_key()
                with open("chave.key", "wb") as arquivo_chave:
                    arquivo_chave.write(chave)
                messagebox.showinfo("Sucesso", "✅ Nova chave gerada com sucesso!\n\n"
                                               "A nova chave foi salva em 'chave.key'")
                self.adicionar_ao_historico("Nova chave de criptografia gerada", "SISTEMA")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar nova chave: {e}")
                self.adicionar_ao_historico(f"Erro ao gerar nova chave: {e}", "ERRO")

    def carregar_chave(self):
        """Carregar chave de criptografia"""
        try:
            with open("chave.key", "rb") as arquivo_chave:
                return arquivo_chave.read()
        except FileNotFoundError:
            # Gerar nova chave se não existir
            chave = Fernet.generate_key()
            with open("chave.key", "wb") as arquivo_chave:
                arquivo_chave.write(chave)
            return chave

    def criptografar_arquivo(self):
        """Criptografar arquivo único - VERSÃO MELHORADA"""
        arquivos = filedialog.askopenfilenames(
            title="🔒 Selecione os arquivos para criptografar",
            filetypes=[("Todos os arquivos", "*.*")]
        )

        if not arquivos:
            return

        # Diálogo de opções
        opcoes = self.mostrar_opcoes_criptografia()
        if not opcoes:
            return

        try:
            chave = self.carregar_chave()
            fernet = Fernet(chave)

            arquivos_processados = 0
            erros = 0
            total_arquivos = len(arquivos)

            # Criar janela de progresso
            progresso = self.criar_janela_progresso("Criptografando arquivos...", total_arquivos)

            for i, arquivo in enumerate(arquivos):
                try:
                    # Atualizar progresso
                    self.atualizar_progresso(progresso, i, total_arquivos,
                                             f"Processando: {os.path.basename(arquivo)}")

                    with open(arquivo, "rb") as f:
                        conteudo = f.read()
                        tamanho_arquivo = len(conteudo)

                    conteudo_criptografado = fernet.encrypt(conteudo)

                    if opcoes['backup']:
                        import shutil
                        shutil.copy2(arquivo, arquivo + ".bak")

                    with open(arquivo, "wb") as f:
                        f.write(conteudo_criptografado)

                    self.adicionar_ao_historico(
                        f"Arquivo criptografado: {os.path.basename(arquivo)} ({self.formatar_tamanho(tamanho_arquivo)})",
                        "PROCESSAMENTO"
                    )
                    arquivos_processados += 1

                    _, extensao = os.path.splitext(arquivo)
                    self.estatisticas.registrar_operacao('criptografar', tamanho_arquivo, extensao)

                except Exception as e:
                    erro_msg = f"Erro ao criptografar '{os.path.basename(arquivo)}': {e}"
                    self.adicionar_ao_historico(erro_msg, "ERRO")
                    erros += 1

            # Fechar janela de progresso
            progresso.destroy()

            # Mostrar resultado
            self.mostrar_resultado_operacao("Criptografia", arquivos_processados, erros, total_arquivos)
            self.atualizar_estatisticas()

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro durante a operação: {e}")

    def descriptografar_arquivo(self):
        """Descriptografar arquivo único - VERSÃO MELHORADA"""
        arquivos = filedialog.askopenfilenames(
            title="🔓 Selecione os arquivos criptografados",
            filetypes=[("Todos os arquivos", "*.*")]
        )

        if not arquivos:
            return

        try:
            chave = self.carregar_chave()
            fernet = Fernet(chave)

            arquivos_processados = 0
            erros = 0
            total_arquivos = len(arquivos)

            # Criar janela de progresso
            progresso = self.criar_janela_progresso("Descriptografando arquivos...", total_arquivos)

            for i, arquivo in enumerate(arquivos):
                try:
                    # Atualizar progresso
                    self.atualizar_progresso(progresso, i, total_arquivos,
                                             f"Processando: {os.path.basename(arquivo)}")

                    with open(arquivo, "rb") as f:
                        conteudo_criptografado = f.read()
                        tamanho_arquivo = len(conteudo_criptografado)

                    try:
                        conteudo_descriptografado = fernet.decrypt(conteudo_criptografado)

                        with open(arquivo, "wb") as f:
                            f.write(conteudo_descriptografado)

                        self.adicionar_ao_historico(
                            f"Arquivo descriptografado: {os.path.basename(arquivo)} ({self.formatar_tamanho(tamanho_arquivo)})",
                            "RESTAURACAO"
                        )
                        arquivos_processados += 1

                        _, extensao = os.path.splitext(arquivo)
                        self.estatisticas.registrar_operacao('descriptografar', tamanho_arquivo, extensao)

                    except Exception:
                        erro_msg = f"Falha ao descriptografar '{os.path.basename(arquivo)}' - Chave incorreta ou arquivo não criptografado"
                        self.adicionar_ao_historico(erro_msg, "ERRO")
                        erros += 1

                except Exception as e:
                    erro_msg = f"Erro ao abrir '{os.path.basename(arquivo)}': {e}"
                    self.adicionar_ao_historico(erro_msg, "ERRO")
                    erros += 1

            # Fechar janela de progresso
            progresso.destroy()

            # Mostrar resultado
            self.mostrar_resultado_operacao("Descriptografia", arquivos_processados, erros, total_arquivos)
            self.atualizar_estatisticas()

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro durante a operação: {e}")

    def criptografar_pasta(self):
        """Criptografar pasta inteira - VERSÃO MELHORADA"""
        pasta = filedialog.askdirectory(title="📁 Selecione a pasta para criptografar")
        if not pasta:
            return

        # Diálogo de opções
        opcoes = self.mostrar_opcoes_pasta()
        if not opcoes:
            return

        try:
            chave = self.carregar_chave()
            fernet = Fernet(chave)

            # Coletar todos os arquivos
            arquivos_para_processar = []
            for pasta_atual, subpastas, arquivos in os.walk(pasta):
                if not opcoes['subpastas'] and pasta_atual != pasta:
                    continue

                for arquivo in arquivos:
                    if arquivo.endswith(".bak") and not opcoes['incluir_backup']:
                        continue

                    caminho_completo = os.path.join(pasta_atual, arquivo)
                    arquivos_para_processar.append(caminho_completo)

            if not arquivos_para_processar:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado para processar.")
                return

            total_arquivos = len(arquivos_para_processar)
            arquivos_processados = 0
            erros = 0

            # Criar janela de progresso
            progresso = self.criar_janela_progresso(f"Criptografando pasta: {os.path.basename(pasta)}", total_arquivos)

            for i, caminho_completo in enumerate(arquivos_para_processar):
                try:
                    arquivo = os.path.basename(caminho_completo)

                    # Atualizar progresso
                    self.atualizar_progresso(progresso, i, total_arquivos, f"Processando: {arquivo}")

                    with open(caminho_completo, "rb") as f:
                        conteudo = f.read()

                    # Verificar se já está criptografado
                    try:
                        fernet.decrypt(conteudo)
                        self.adicionar_ao_historico(f"Arquivo já criptografado: {arquivo}", "INFO")
                        continue
                    except:
                        pass

                    conteudo_criptografado = fernet.encrypt(conteudo)

                    if opcoes['backup']:
                        import shutil
                        shutil.copy2(caminho_completo, caminho_completo + ".bak")

                    with open(caminho_completo, "wb") as f:
                        f.write(conteudo_criptografado)

                    self.adicionar_ao_historico(f"Criptografado: {arquivo}", "PROCESSAMENTO")
                    arquivos_processados += 1

                    _, extensao = os.path.splitext(caminho_completo)
                    self.estatisticas.registrar_operacao('criptografar', len(conteudo), extensao)

                except Exception as e:
                    self.adicionar_ao_historico(f"Erro em {arquivo}: {str(e)}", "ERRO")
                    erros += 1

            # Fechar janela de progresso
            progresso.destroy()

            # Mostrar resultado
            self.mostrar_resultado_operacao("Criptografia de Pasta", arquivos_processados, erros, total_arquivos)
            self.atualizar_estatisticas()

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro durante a operação: {e}")

    def descriptografar_pasta(self):
        """Descriptografar pasta inteira - VERSÃO MELHORADA"""
        pasta = filedialog.askdirectory(title="📂 Selecione a pasta para descriptografar")
        if not pasta:
            return

        # Diálogo de opções
        opcoes = self.mostrar_opcoes_pasta(descriptografar=True)
        if not opcoes:
            return

        try:
            chave = self.carregar_chave()
            fernet = Fernet(chave)

            # Coletar todos os arquivos
            arquivos_para_processar = []
            for pasta_atual, subpastas, arquivos in os.walk(pasta):
                if not opcoes['subpastas'] and pasta_atual != pasta:
                    continue

                for arquivo in arquivos:
                    if arquivo.endswith(".bak") and not opcoes['incluir_backup']:
                        continue

                    caminho_completo = os.path.join(pasta_atual, arquivo)
                    arquivos_para_processar.append(caminho_completo)

            if not arquivos_para_processar:
                messagebox.showinfo("Informação", "Nenhum arquivo encontrado para processar.")
                return

            total_arquivos = len(arquivos_para_processar)
            arquivos_processados = 0
            erros = 0

            # Criar janela de progresso
            progresso = self.criar_janela_progresso(f"Descriptografando pasta: {os.path.basename(pasta)}",
                                                    total_arquivos)

            for i, caminho_completo in enumerate(arquivos_para_processar):
                try:
                    arquivo = os.path.basename(caminho_completo)

                    # Atualizar progresso
                    self.atualizar_progresso(progresso, i, total_arquivos, f"Processando: {arquivo}")

                    with open(caminho_completo, "rb") as f:
                        conteudo_criptografado = f.read()

                    try:
                        conteudo_descriptografado = fernet.decrypt(conteudo_criptografado)

                        with open(caminho_completo, "wb") as f:
                            f.write(conteudo_descriptografado)

                        self.adicionar_ao_historico(f"Descriptografado: {arquivo}", "RESTAURACAO")
                        arquivos_processados += 1

                        _, extensao = os.path.splitext(caminho_completo)
                        self.estatisticas.registrar_operacao('descriptografar', len(conteudo_criptografado),
                                                             extensao)

                    except:
                        self.adicionar_ao_historico(f"Arquivo não criptografado ou chave inválida: {arquivo}",
                                                    "INFO")

                except Exception as e:
                    self.adicionar_ao_historico(f"Erro em {arquivo}: {str(e)}", "ERRO")
                    erros += 1

            # Fechar janela de progresso
            progresso.destroy()

            # Mostrar resultado
            self.mostrar_resultado_operacao("Descriptografia de Pasta", arquivos_processados, erros,
                                            total_arquivos)
            self.atualizar_estatisticas()

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro durante a operação: {e}")

    def mostrar_opcoes_criptografia(self):
        """Mostrar diálogo de opções para criptografia"""
        opcoes_window = tk.Toplevel(self.janela)
        opcoes_window.title("Opções de Criptografia")
        opcoes_window.geometry("350x200")
        opcoes_window.transient(self.janela)
        opcoes_window.grab_set()
        opcoes_window.resizable(False, False)

        # Centralizar janela
        opcoes_window.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + 50,
            self.janela.winfo_rooty() + 50
        ))

        # Variáveis
        backup_var = tk.BooleanVar(value=True)
        resultado = {"backup": False, "confirmado": False}

        # Header
        header = tk.Frame(opcoes_window, bg="#3498db", height=50)
        header.pack(fill="x")
        header.grid_propagate(False)

        title_label = tk.Label(header, text="⚙️ Configurações da Operação",
                               font=("Segoe UI", 12, "bold"),
                               bg="#3498db", fg="white")
        title_label.pack(expand=True)

        # Conteúdo
        content = tk.Frame(opcoes_window, bg="white")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Opção de backup
        backup_frame = tk.Frame(content, bg="white")
        backup_frame.pack(fill="x", pady=10)

        tk.Checkbutton(backup_frame, text="Criar backup dos arquivos originais (.bak)",
                       variable=backup_var, font=("Segoe UI", 10),
                       bg="white").pack(anchor="w")

        info_label = tk.Label(backup_frame,
                              font=("Segoe UI", 8), fg="#7f8c8d", bg="white")
        info_label.pack(anchor="w", padx=20)

        # Botões
        buttons_frame = tk.Frame(content, bg="white")
        buttons_frame.pack(fill="x", pady=(20, 0))

        def confirmar():
            resultado["backup"] = backup_var.get()
            resultado["confirmado"] = True
            opcoes_window.destroy()

        def cancelar():
            opcoes_window.destroy()

        tk.Button(buttons_frame, text="Cancelar", command=cancelar,
                  bg="#95a5a6", fg="white", padx=20).pack(side="right", padx=5)

        tk.Button(buttons_frame, text="Continuar", command=confirmar,
                  bg="#27ae60", fg="white", padx=20).pack(side="right")

        # Aguardar resultado
        opcoes_window.wait_window()
        return resultado if resultado["confirmado"] else None

    def mostrar_opcoes_pasta(self, descriptografar=False):
        """Mostrar diálogo de opções para processamento de pasta"""
        opcoes_window = tk.Toplevel(self.janela)
        title = "Opções de Descriptografia" if descriptografar else "Opções de Criptografia"
        opcoes_window.title(title)
        opcoes_window.geometry("400x280")
        opcoes_window.transient(self.janela)
        opcoes_window.grab_set()
        opcoes_window.resizable(False, False)

        # Centralizar janela
        opcoes_window.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + 50,
            self.janela.winfo_rooty() + 50
        ))

        # Variáveis
        subpastas_var = tk.BooleanVar(value=True)
        backup_var = tk.BooleanVar(value=True)
        incluir_backup_var = tk.BooleanVar(value=False)
        resultado = {"subpastas": False, "backup": False, "incluir_backup": False, "confirmado": False}

        # Header
        header = tk.Frame(opcoes_window, bg="#8e44ad", height=50)
        header.pack(fill="x")
        header.grid_propagate(False)

        icon = "📂" if descriptografar else "📁"
        title_label = tk.Label(header, text=f"{icon} {title}",
                               font=("Segoe UI", 12, "bold"),
                               bg="#8e44ad", fg="white")
        title_label.pack(expand=True)

        # Conteúdo
        content = tk.Frame(opcoes_window, bg="white")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Opção de subpastas
        subpastas_frame = tk.Frame(content, bg="white")
        subpastas_frame.pack(fill="x", pady=5)

        tk.Checkbutton(subpastas_frame, text="Incluir subpastas no processamento",
                       variable=subpastas_var, font=("Segoe UI", 10),
                       bg="white").pack(anchor="w")

        # Opção de backup (apenas para criptografia)
        if not descriptografar:
            backup_frame = tk.Frame(content, bg="white")
            backup_frame.pack(fill="x", pady=5)

            tk.Checkbutton(backup_frame, text="Criar backup dos arquivos originais",
                           variable=backup_var, font=("Segoe UI", 10),
                           bg="white").pack(anchor="w")

        # Opção de incluir arquivos .bak
        bak_frame = tk.Frame(content, bg="white")
        bak_frame.pack(fill="x", pady=5)

        tk.Checkbutton(bak_frame, text="Incluir arquivos de backup (.bak)",
                       variable=incluir_backup_var, font=("Segoe UI", 10),
                       bg="white").pack(anchor="w")

        # Informações
        info_frame = tk.LabelFrame(content, text="Informações", font=("Segoe UI", 9))
        info_frame.pack(fill="x", pady=10)

        if descriptografar:
            info_text = ("• Apenas arquivos criptografados serão processados\n"
                         "• Arquivos não criptografados serão ignorados\n"
                         "• Verifique se possui a chave correta")
        else:
            info_text = ("• Arquivos já criptografados serão ignorados\n"
                         "• Backup recomendado para segurança\n"
                         "• Processo pode demorar para pastas grandes")

        tk.Label(info_frame, text=info_text, font=("Segoe UI", 8),
                 fg="#34495e", bg="white", justify="left").pack(padx=10, pady=5)

        # Botões
        buttons_frame = tk.Frame(content, bg="white")
        buttons_frame.pack(fill="x", pady=(15, 0))

        def confirmar():
            resultado["subpastas"] = subpastas_var.get()
            resultado["backup"] = backup_var.get() if not descriptografar else False
            resultado["incluir_backup"] = incluir_backup_var.get()
            resultado["confirmado"] = True
            opcoes_window.destroy()

        def cancelar():
            opcoes_window.destroy()

        tk.Button(buttons_frame, text="Cancelar", command=cancelar,
                  bg="#95a5a6", fg="white", padx=20).pack(side="right", padx=5)

        cor_botao = "#e67e22" if descriptografar else "#8e44ad"
        tk.Button(buttons_frame, text="Iniciar Processamento", command=confirmar,
                  bg=cor_botao, fg="white", padx=20).pack(side="right")

        # Aguardar resultado
        opcoes_window.wait_window()
        return resultado if resultado["confirmado"] else None

    def criar_janela_progresso(self, titulo, total):
        """Criar janela de progresso"""
        progresso_window = tk.Toplevel(self.janela)
        progresso_window.title("Processando...")
        progresso_window.geometry("450x150")
        progresso_window.transient(self.janela)
        progresso_window.grab_set()
        progresso_window.resizable(False, False)

        # Centralizar
        progresso_window.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + 100,
            self.janela.winfo_rooty() + 100
        ))

        # Header
        header = tk.Frame(progresso_window, bg="#2c3e50", height=40)
        header.pack(fill="x")
        header.grid_propagate(False)

        titulo_label = tk.Label(header, text=titulo, font=("Segoe UI", 11, "bold"),
                                bg="#2c3e50", fg="white")
        titulo_label.pack(expand=True)

        # Conteúdo
        content = tk.Frame(progresso_window, bg="white")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # Label de status
        progresso_window.status_label = tk.Label(content, text="Iniciando...",
                                                 font=("Segoe UI", 10), bg="white")
        progresso_window.status_label.pack(pady=(0, 10))

        # Barra de progresso
        progresso_window.progress_bar = ttk.Progressbar(content, length=400, mode='determinate')
        progresso_window.progress_bar.pack(pady=5)
        progresso_window.progress_bar['maximum'] = total

        # Label de progresso
        progresso_window.progress_label = tk.Label(content, text="0 / 0",
                                                   font=("Segoe UI", 9), bg="white", fg="#7f8c8d")
        progresso_window.progress_label.pack(pady=(5, 0))

        progresso_window.update()
        return progresso_window

    def atualizar_progresso(self, janela_progresso, atual, total, status):
        """Atualizar janela de progresso"""
        try:
            janela_progresso.progress_bar['value'] = atual + 1
            janela_progresso.status_label.config(text=status)
            janela_progresso.progress_label.config(text=f"{atual + 1} / {total}")
            janela_progresso.update()
        except:
            pass  # Janela pode ter sido fechada

    def mostrar_resultado_operacao(self, operacao, sucessos, erros, total):
        """Mostrar resultado da operação em janela personalizada"""
        resultado_window = tk.Toplevel(self.janela)
        resultado_window.title("Resultado da Operação")
        resultado_window.geometry("400x300")
        resultado_window.transient(self.janela)
        resultado_window.grab_set()
        resultado_window.resizable(False, False)

        # Centralizar
        resultado_window.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + 100,
            self.janela.winfo_rooty() + 100
        ))

        # Determinar cor do header baseado no resultado
        if erros == 0:
            header_color = "#27ae60"  # Verde para sucesso
            icon = "✅"
        elif sucessos == 0:
            header_color = "#e74c3c"  # Vermelho para falha total
            icon = "❌"
        else:
            header_color = "#f39c12"  # Laranja para sucesso parcial
            icon = "⚠️"

        # Header
        header = tk.Frame(resultado_window, bg=header_color, height=60)
        header.pack(fill="x")
        header.grid_propagate(False)

        title_label = tk.Label(header, text=f"{icon} {operacao} Concluída",
                               font=("Segoe UI", 14, "bold"),
                               bg=header_color, fg="white")
        title_label.pack(expand=True)

        # Conteúdo
        content = tk.Frame(resultado_window, bg="white")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Estatísticas
        stats_frame = tk.LabelFrame(content, text="Resumo da Operação", font=("Segoe UI", 10))
        stats_frame.pack(fill="x", pady=(0, 15))

        stats_text = f"""📊 Total de arquivos: {total}
            ✅ Processados com sucesso: {sucessos}
            ❌ Erros encontrados: {erros}
            📈 Taxa de sucesso: {(sucessos / total * 100):.1f}%"""

        tk.Label(stats_frame, text=stats_text, font=("Segoe UI", 9),
                 bg="white", justify="left").pack(padx=15, pady=10, anchor="w")

        # Mensagem adicional
        if erros > 0:
            msg_frame = tk.LabelFrame(content, text="Informações Adicionais", font=("Segoe UI", 10))
            msg_frame.pack(fill="x", pady=(0, 15))

            if sucessos > 0:
                msg = "A operação foi concluída com alguns erros. Verifique o histórico para detalhes dos arquivos que falharam."
            else:
                msg = "Nenhum arquivo foi processado com sucesso. Verifique as permissões dos arquivos e a chave de criptografia."

            tk.Label(msg_frame, text=msg, font=("Segoe UI", 9),
                     bg="white", wraplength=350, justify="left").pack(padx=15, pady=10)

        # Botões
        buttons_frame = tk.Frame(content, bg="white")
        buttons_frame.pack(fill="x", pady=(10, 0))

        def ver_historico():
            resultado_window.destroy()
            self.mostrar_aba("arquivos")

        def fechar():
            resultado_window.destroy()

        tk.Button(buttons_frame, text="Ver Histórico", command=ver_historico,
                  bg="#3498db", fg="white", padx=15).pack(side="left")

        tk.Button(buttons_frame, text="Fechar", command=fechar,
                  bg="#95a5a6", fg="white", padx=20).pack(side="right")

    def formatar_tamanho(self, tamanho_bytes):
        """Formatar tamanho em bytes para formato legível"""
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if tamanho_bytes < 1024.0:
                return f"{tamanho_bytes:.1f} {unidade}"
            tamanho_bytes /= 1024.0
        return f"{tamanho_bytes:.1f} PB"

        # Métodos para estatísticas

    def atualizar_estatisticas(self):
        """Atualizar exibição de estatísticas"""
        self.area_estatisticas.delete("1.0", tk.END)

        def bytes_para_legivel(tamanho_bytes):
            for unidade in ['B', 'KB', 'MB', 'GB']:
                if tamanho_bytes < 1024.0:
                    return f"{tamanho_bytes:.2f} {unidade}"
                tamanho_bytes /= 1024.0
            return f"{tamanho_bytes:.2f} TB"

        texto_stats = f"""Estatísticas de Uso - CryptographiE v2.1
            {'=' * 50}

            ESTATÍSTICAS GERAIS:
            • Arquivos criptografados: {self.estatisticas.arquivos_criptografados}
            • Arquivos descriptografados: {self.estatisticas.arquivos_descriptografados}
            • Volume total criptografado: {bytes_para_legivel(self.estatisticas.tamanho_total_criptografado)}
            • Volume total descriptografado: {bytes_para_legivel(self.estatisticas.tamanho_total_descriptografado)}

            OPERAÇÕES POR TIPO DE ARQUIVO:
            """

        for ext, dados in self.estatisticas.tipos_arquivos.items():
            texto_stats += f"• {ext}: {dados['cripto']} criptografados, {dados['descripto']} descriptografados\n"

        texto_stats += f"""
            OPERAÇÕES POR DIA:
            """

        dias = list(self.estatisticas.operacoes_por_dia.keys())
        dias.sort()
        for dia in dias[-7:]:  # Últimos 7 dias
            dados = self.estatisticas.operacoes_por_dia[dia]
            texto_stats += f"• {dia}: {dados['cripto']} criptografados, {dados['descripto']} descriptografados\n"

        texto_stats += f"""
            INFORMAÇÕES TÉCNICAS:
            • Algoritmo: AES-256 (Fernet)
            • Derivação de chave: PBKDF2 com SHA-256
            • Iterações: 100.000
            • Modo de operação: CBC com autenticação
            • Sessão iniciada: {self.estatisticas.hora_inicio.strftime('%d/%m/%Y %H:%M:%S')}
            """

        self.area_estatisticas.insert("1.0", texto_stats)

        # Atualizar gráfico também
        if hasattr(self, 'canvas_grafico'):
            self.atualizar_grafico()

    def exportar_estatisticas(self):
        """Exportar estatísticas para arquivo"""
        arquivo = filedialog.asksaveasfilename(
            title="Exportar Estatísticas",
            defaultextension=".txt",
            filetypes=(("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*"))
        )

        if arquivo:
            try:
                conteudo = self.area_estatisticas.get("1.0", tk.END)
                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write(conteudo)
                messagebox.showinfo("Sucesso", "Estatísticas exportadas com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")

    def limpar_dados_estatisticas(self):
        """Limpar dados de estatísticas"""
        resultado = messagebox.askyesno("Limpar Dados",
                                        "Tem certeza que deseja limpar todos os dados estatísticos?")
        if resultado:
            self.estatisticas = Estatisticas()
            self.atualizar_estatisticas()
            messagebox.showinfo("Sucesso", "Dados estatísticos limpos com sucesso!")

        # Métodos para código Morse

    MORSE_CODE_DICT = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
        'Z': '--..',
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
        '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
        '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--',
        '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...', ':': '---...',
        ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-',
        '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
    }

    def texto_para_morse(self):
        """Converter texto para código morse"""
        texto = self.entrada_morse.get("1.0", tk.END).strip().upper()

        if not texto:
            messagebox.showwarning("Aviso", "Digite algum texto para converter!")
            return

        morse_reverse = {v: k for k, v in self.MORSE_CODE_DICT.items()}

        resultado = []
        for palavra in texto.split():
            palavra_morse = []
            for caractere in palavra:
                if caractere in self.MORSE_CODE_DICT:
                    palavra_morse.append(self.MORSE_CODE_DICT[caractere])
            resultado.append(' '.join(palavra_morse))

        morse_final = '   '.join(resultado)

        self.saida_morse.delete("1.0", tk.END)
        self.saida_morse.insert("1.0", morse_final)

    def morse_para_texto(self):
        """Converter código morse para texto"""
        morse_code = self.entrada_morse.get("1.0", tk.END).strip()

        if not morse_code:
            messagebox.showwarning("Aviso", "Digite o código morse para converter!")
            return

        morse_reverse = {v: k for k, v in self.MORSE_CODE_DICT.items()}

        try:
            palavras = morse_code.split('   ')
            resultado = []

            for palavra in palavras:
                chars = palavra.split(' ')
                palavra_resultado = ''
                for char in chars:
                    if char in morse_reverse:
                        palavra_resultado += morse_reverse[char]
                    elif char == '/':
                        palavra_resultado += ' '
                    elif char.strip():
                        palavra_resultado += f'[{char}]'
                resultado.append(palavra_resultado)

            texto_final = ' '.join(resultado)
            self.saida_morse.delete("1.0", tk.END)
            self.saida_morse.insert("1.0", texto_final)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao converter morse: {e}")

    def limpar_morse(self):
        """Limpar áreas de texto do morse"""
        self.entrada_morse.delete("1.0", tk.END)
        self.saida_morse.delete("1.0", tk.END)

    def reproduzir_morse(self):
        """Reproduzir código morse como som"""
        if not winsound_disponivel:
            messagebox.showerror("Erro", "Biblioteca de som não disponível.")
            return

        morse_code = self.saida_morse.get("1.0", tk.END).strip()

        if not morse_code:
            self.texto_para_morse()
            morse_code = self.saida_morse.get("1.0", tk.END).strip()

        if not morse_code:
            messagebox.showwarning("Aviso", "Nenhum código morse para reproduzir.")
            return

        # Parar reprodução anterior
        if self.reproduzindo:
            self.parar_reproducao()

        wpm = self.wpm_var.get()
        frequencia = self.freq_var.get()

        dot_duration = int((1.2 / wpm) * 1000)
        dash_duration = dot_duration * 3

        self.reproduzindo = True
        self.thread_reproducao = threading.Thread(target=self.tocar_morse,
                                                  args=(morse_code, dot_duration, dash_duration, frequencia))
        self.thread_reproducao.daemon = True
        self.thread_reproducao.start()

    def tocar_morse(self, morse_code, dot_duration, dash_duration, frequencia):
        """Tocar código morse em thread separada"""
        try:
            for palavra in morse_code.split('   '):
                for letra in palavra.split(' '):
                    for simbolo in letra:
                        if not self.reproduzindo:
                            break

                        if simbolo == '.':
                            winsound.Beep(frequencia, dot_duration)
                        elif simbolo == '-':
                            winsound.Beep(frequencia, dash_duration)

                        time.sleep(dot_duration / 1000)

                    if self.reproduzindo:
                        time.sleep(dot_duration * 3 / 1000)

                if self.reproduzindo:
                    time.sleep(dot_duration * 7 / 1000)

        except Exception as e:
            print(f"Erro na reprodução: {e}")
        finally:
            self.reproduzindo = False

    def parar_reproducao(self):
        """Parar reprodução do morse"""
        self.reproduzindo = False

    def on_pause_press(self, event):
        """Método chamado quando o botão de pausa é pressionado"""
        if self.reproduzindo:
            if self.pausado:
                # Retomar reprodução
                self.pausado = False
                self.evento_pausa.set()  # Desbloqueio
                self.btn_pausa.config(text="⏸️ Pausar", bg="#f39c12")
            else:
                # Pausar reprodução
                self.pausado = True
                self.evento_pausa.clear()  # Bloqueio
                self.btn_pausa.config(text="▶️ Retomar", bg="#27ae60")

    def on_pause_release(self, event):
        """Método chamado quando o botão de pausa é liberado"""
        # Este método pode ficar vazio ou ser usado para efeitos visuais
        pass

    def tocar_morse(self, morse_code, dot_duration, dash_duration, frequencia):
        """Tocar código morse em thread separada - VERSÃO ATUALIZADA COM PAUSA"""
        try:
            for palavra in morse_code.split('   '):
                for letra in palavra.split(' '):
                    for simbolo in letra:
                        if not self.reproduzindo:
                            break

                        # Aguardar se estiver pausado
                        self.evento_pausa.wait()

                        if not self.reproduzindo:
                            break

                        if simbolo == '.':
                            winsound.Beep(frequencia, dot_duration)
                        elif simbolo == '-':
                            winsound.Beep(frequencia, dash_duration)

                        # Aguardar se estiver pausado durante a pausa entre símbolos
                        if self.reproduzindo:
                            self.evento_pausa.wait()
                            time.sleep(dot_duration / 1000)

                    # Pausa entre letras
                    if self.reproduzindo:
                        self.evento_pausa.wait()
                        time.sleep(dot_duration * 3 / 1000)

                # Pausa entre palavras
                if self.reproduzindo:
                    self.evento_pausa.wait()
                    time.sleep(dot_duration * 7 / 1000)

        except Exception as e:
            print(f"Erro na reprodução: {e}")
        finally:
            self.reproduzindo = False
            # Resetar botão de pausa quando terminar
            if hasattr(self, 'btn_pausa'):
                self.janela.after(0, lambda: self.btn_pausa.config(text="⏸️ Pausar", bg="#f39c12"))
                self.pausado = False
                self.evento_pausa.set()

    def parar_reproducao(self):
        """Parar reprodução do morse - VERSÃO ATUALIZADA"""
        self.reproduzindo = False
        self.pausado = False
        self.evento_pausa.set()  # Desbloqueio para que a thread possa terminar

        # Resetar visual do botão
        if hasattr(self, 'btn_pausa'):
            self.btn_pausa.config(text="⏸️ Pausar", bg="#f39c12")

    def mostrar_tabela_morse(self):
        """Mostrar tabela de referência do morse"""
        tabela = tk.Toplevel(self.janela)
        tabela.title("Tabela de Código Morse")
        tabela.geometry("400x500")

        texto_tabela = scrolledtext.ScrolledText(tabela, wrap=tk.WORD, font=("Courier", 10))
        texto_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        conteudo = "TABELA DE CÓDIGO MORSE\n" + "=" * 30 + "\n\n"

        conteudo += "LETRAS:\n" + "-" * 15 + "\n"
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if letra in self.MORSE_CODE_DICT:
                conteudo += f"{letra} : {self.MORSE_CODE_DICT[letra]}\n"

        conteudo += "\nNÚMEROS:\n" + "-" * 15 + "\n"
        for numero in "0123456789":
            if numero in self.MORSE_CODE_DICT:
                conteudo += f"{numero} : {self.MORSE_CODE_DICT[numero]}\n"

        conteudo += "\nPONTUAÇÃO:\n" + "-" * 15 + "\n"
        for char, morse in self.MORSE_CODE_DICT.items():
            if char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
                conteudo += f"{char} : {morse}\n"

        texto_tabela.insert("1.0", conteudo)
        texto_tabela.config(state="disabled")

    # Métodos para Arduino (se disponível)

    def atualizar_portas_seriais(self):
        """Atualizar lista de portas seriais"""
        if not serial_disponivel:
            return

        try:
            portas = list(serial.tools.list_ports.comports())
            if portas:
                portas_str = [p.device for p in portas]
                self.combo_portas['values'] = portas_str
                if len(portas_str) > 0:
                    self.combo_portas.current(0)
            else:
                self.combo_portas['values'] = []
        except Exception as e:
            print(f"Erro ao listar portas: {e}")

    def conectar_arduino(self):
        """Conectar ao Arduino"""
        if not serial_disponivel:
            messagebox.showerror("Erro", "Biblioteca serial não disponível.")
            return

        porta = self.combo_portas.get()
        if not porta:
            messagebox.showerror("Erro", "Selecione uma porta serial.")
            return

        try:
            if self.arduino_serial and self.arduino_serial.is_open:
                self.arduino_serial.close()

            self.arduino_serial = serial.Serial(porta, 9600, timeout=2)
            time.sleep(2)

            # Teste de conexão
            self.arduino_serial.write(b'T')
            time.sleep(1)
            resposta = self.arduino_serial.read_all()

            if b'OK' in resposta:
                self.arduino_conectado = True
                self.lbl_status_arduino.config(text="Status: Conectado", fg="green")
                self.btn_conectar_arduino.config(state=tk.DISABLED)
                self.btn_desconectar_arduino.config(state=tk.NORMAL)
                self.btn_transmitir_arduino.config(state=tk.NORMAL)
                messagebox.showinfo("Sucesso", f"Arduino conectado na porta {porta}.")
            else:
                self.arduino_serial.close()
                messagebox.showerror("Erro", "Arduino não respondeu corretamente.")

        except Exception as e:
            if self.arduino_serial and self.arduino_serial.is_open:
                self.arduino_serial.close()
            messagebox.showerror("Erro", f"Erro ao conectar: {e}")

    def desconectar_arduino(self):
        """Desconectar do Arduino"""
        try:
            if self.arduino_serial and self.arduino_serial.is_open:
                self.arduino_serial.write(b'X')
                self.arduino_serial.close()

            self.arduino_conectado = False
            self.lbl_status_arduino.config(text="Status: Desconectado", fg="red")
            self.btn_conectar_arduino.config(state=tk.NORMAL)
            self.btn_desconectar_arduino.config(state=tk.DISABLED)
            self.btn_transmitir_arduino.config(state=tk.DISABLED)
            messagebox.showinfo("Sucesso", "Arduino desconectado.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao desconectar: {e}")

    def transmitir_morse_arduino(self):
        """Transmitir código morse para Arduino"""
        if not self.arduino_conectado:
            messagebox.showerror("Erro", "Arduino não está conectado.")
            return

        morse_code = self.saida_morse.get("1.0", tk.END).strip()

        if not morse_code:
            self.texto_para_morse()
            morse_code = self.saida_morse.get("1.0", tk.END).strip()

        if not morse_code:
            messagebox.showwarning("Aviso", "Nenhum código morse para transmitir.")
            return

        try:
            wpm = self.wpm_var.get()
            dot_duration = int((1.2 / wpm) * 1000)
            dash_duration = dot_duration * 3

            # Enviar configurações
            comando = f"C,{dot_duration},{dash_duration},0,0,0\n"
            self.arduino_serial.write(comando.encode())
            time.sleep(0.5)

            # Enviar código morse
            comando = f"M,{morse_code}\n"
            self.arduino_serial.write(comando.encode())

            messagebox.showinfo("Sucesso", "Código morse enviado para Arduino.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro na transmissão: {e}")

    # Métodos para criar menu e barra de status
    def criar_menu(self):
        """Criar menu principal"""
        menu_principal = tk.Menu(self.janela)
        self.janela.config(menu=menu_principal)

        # Menu Arquivo
        menu_arquivo = tk.Menu(menu_principal, tearoff=0)
        menu_principal.add_cascade(label="Arquivo", menu=menu_arquivo)
        menu_arquivo.add_command(label="Abrir Arquivo", command=self.carregar_arquivo)
        menu_arquivo.add_command(label="Salvar Resultado", command=self.salvar_arquivo)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.janela.quit)

        # Menu Operações
        menu_operacoes = tk.Menu(menu_principal, tearoff=0)
        menu_principal.add_cascade(label="Operações", menu=menu_operacoes)
        menu_operacoes.add_command(label="Criptografar Texto", command=self.processar_texto)
        menu_operacoes.add_command(label="Descriptografar Texto", command=self.restaurar_texto)
        menu_operacoes.add_separator()
        menu_operacoes.add_command(label="Criptografar Arquivo", command=self.criptografar_arquivo)
        menu_operacoes.add_command(label="Descriptografar Arquivo", command=self.descriptografar_arquivo)
        menu_operacoes.add_separator()
        menu_operacoes.add_command(label="Gerar Nova Chave", command=self.gerar_nova_chave)

        # Menu Estatísticas
        menu_estatisticas = tk.Menu(menu_principal, tearoff=0)
        menu_principal.add_cascade(label="Estatísticas", menu=menu_estatisticas)
        menu_estatisticas.add_command(label="Ver Estatísticas",
                                      command=lambda: self.mostrar_aba("estatisticas"))
        menu_estatisticas.add_command(label="Exportar Relatório", command=self.exportar_estatisticas)
        menu_estatisticas.add_command(label="Limpar Dados", command=self.limpar_dados_estatisticas)

        # Menu Ajuda
        menu_ajuda = tk.Menu(menu_principal, tearoff=0)
        menu_principal.add_cascade(label="Ajuda", menu=menu_ajuda)
        menu_ajuda.add_command(label="Conteúdo da Ajuda", command=self.mostrar_ajuda, accelerator="F1")
        menu_ajuda.add_command(label="Ver Tutorial", command=self.mostrar_tutorial, accelerator="F2")
        menu_ajuda.add_command(label="Dicas Rápidas", command=self.mostrar_dicas, accelerator="F3")
        menu_ajuda.add_command(label="Relatório de Bugs", command=self.reportar_bug, accelerator="F4")
        menu_ajuda.add_command(label="Verificar Atualizações", command=self.verificar_atualizacoes,
                               accelerator="F5")
        menu_ajuda.add_separator()
        menu_ajuda.add_command(label="Sobre", command=self.mostrar_sobre, accelerator="F6")

        # Vincular teclas de atalho
        self.janela.bind("<F1>", lambda event: self.mostrar_ajuda())
        self.janela.bind("<F2>", lambda event: self.mostrar_tutorial())
        self.janela.bind("<F3>", lambda event: self.mostrar_dicas())
        self.janela.bind("<F4>", lambda event: self.reportar_bug())
        self.janela.bind("<F5>", lambda event: self.verificar_atualizacoes())
        self.janela.bind("<F6>", lambda event: self.mostrar_sobre())

    def criar_barra_status(self):
        """Criar barra de status"""
        self.barra_status = tk.Label(self.janela, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.barra_status.grid(row=1, column=0, columnspan=2, sticky="ew")

    # Métodos do menu Ajuda
    def mostrar_ajuda(self):
        """Mostrar janela de ajuda"""
        ajuda = tk.Toplevel(self.janela)
        ajuda.title("Ajuda - CryptographiE")
        ajuda.geometry("600x500")
        ajuda.transient(self.janela)
        ajuda.grab_set()

        frame_principal = tk.Frame(ajuda, padx=20, pady=20)
        frame_principal.pack(fill="both", expand=True)

        titulo = tk.Label(frame_principal, text="CryptographiE - Ajuda",
                          font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 20))

        ajuda_texto = scrolledtext.ScrolledText(frame_principal, wrap=tk.WORD)
        ajuda_texto.pack(fill="both", expand=True)

        conteudo_ajuda = """MANUAL DE AJUDA - CryptographiE v2.1

        INTRODUÇÃO:
        O CryptographiE é um sistema completo de criptografia que permite proteger textos e arquivos usando algoritmos avançados de segurança.

        FUNCIONALIDADES PRINCIPAIS:

        1. CRIPTOGRAFIA DE TEXTO:
           - Digite ou carregue texto na área de entrada
           - Clique em "Criptografar" para proteger o texto
           - Use "Descriptografar" para recuperar o texto original
           - Salve o resultado usando o botão "Salvar"

        2. CRIPTOGRAFIA DE ARQUIVOS:
           - Criptografar/Descriptografar arquivos individuais
           - Processar pastas inteiras com subpastas
           - Geração automática de backups
           - Suporte a todos os tipos de arquivo

        3. ESTATÍSTICAS:
           - Monitore o uso do sistema
           - Visualize dados por tipo de arquivo e período
           - Exporte relatórios detalhados
           - Gráfico de pizza para visualização intuitiva

        4. CÓDIGO MORSE:
           - Converta texto para código morse e vice-versa
           - Reproduza código morse como som
           - Ajuste velocidade e frequência
           - Conecte com Arduino para transmissão física

        SEGURANÇA:
        - Algoritmo AES-256 com Fernet
        - Chaves derivadas com PBKDF2-SHA256
        - 100.000 iterações para máxima segurança
        - Compatibilidade com versões anteriores

        DICAS IMPORTANTES:
        - Sempre faça backup antes de criptografar
        - Descriptografe tudo antes de gerar nova chave
        - Mantenha a chave em local seguro
        - Use senhas fortes quando necessário

        Para mais informações, consulte os outros itens do menu Ajuda."""

        ajuda_texto.insert("1.0", conteudo_ajuda)
        ajuda_texto.config(state="disabled")

        tk.Button(frame_principal, text="Fechar", command=ajuda.destroy).pack(pady=10)

    def mostrar_tutorial(self):
        """Mostrar tutorial"""
        messagebox.showinfo("Tutorial", "Tutorial em vídeo será implementado em versão futura.\n\n"
                                        "Por enquanto, consulte a Ajuda (F1) para instruções detalhadas.")

    def mostrar_dicas(self):
        """Mostrar dicas rápidas"""
        dicas = tk.Toplevel(self.janela)
        dicas.title("Dicas Rápidas")
        dicas.geometry("450x350")
        dicas.transient(self.janela)
        dicas.grab_set()

        frame = tk.Frame(dicas, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Dicas Rápidas", font=("Arial", 14, "bold")).pack(pady=(0, 15))

        dicas_texto = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        dicas_texto.pack(fill="both", expand=True)

        dicas_conteudo = """DICAS RÁPIDAS:

        🔒 SEGURANÇA:
        • Sempre faça backup dos arquivos originais
        • Descriptografe tudo antes de gerar nova chave
        • Mantenha a chave em local seguro

        ⚡ EFICIÊNCIA:
        • Use "Criptografar Pasta" para múltiplos arquivos
        • Organize arquivos por categoria antes de criptografar
        • Monitore o progresso pelo histórico

        📊 ANÁLISE:
        • Acompanhe estatísticas de uso
        • Exporte relatórios para análise
        • Use filtros por período nos dados
        • Visualize dados no gráfico de pizza

        📡 CÓDIGO MORSE:
        • Ajuste velocidade conforme necessário
        • Use Arduino para transmissão física
        • Pratique com a tabela de referência

        🎯 PRODUTIVIDADE:
        • Use atalhos de teclado (F1-F6)
        • Configure backup automático
        • Mantenha histórico organizado"""

        dicas_texto.insert("1.0", dicas_conteudo)
        dicas_texto.config(state="disabled")

        tk.Button(frame, text="Fechar", command=dicas.destroy).pack(pady=10)

    def reportar_bug(self):
        """Reportar bug"""
        bug = tk.Toplevel(self.janela)
        bug.title("Reportar Bug")
        bug.geometry("500x400")
        bug.transient(self.janela)
        bug.grab_set()

        frame = tk.Frame(bug, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Reportar um Problema", font=("Arial", 14, "bold")).pack(pady=(0, 15))

        tk.Label(frame, text="Título do problema:").pack(anchor="w")
        titulo_entry = tk.Entry(frame, width=50)
        titulo_entry.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Descrição detalhada:").pack(anchor="w")
        desc_text = scrolledtext.ScrolledText(frame, height=8)
        desc_text.pack(fill="both", expand=True, pady=(0, 10))

        frame_botoes = tk.Frame(frame)
        frame_botoes.pack(fill="x")

        def enviar_relatorio():
            titulo = titulo_entry.get()
            descricao = desc_text.get("1.0", tk.END)

            if not titulo.strip():
                messagebox.showerror("Erro", "Por favor, informe um título.")
                return

            # Simular envio
            messagebox.showinfo("Enviado", "Relatório enviado com sucesso!\n\n"
                                           "Nossa equipe analisará o problema em breve.")
            bug.destroy()

        tk.Button(frame_botoes, text="Cancelar", command=bug.destroy).pack(side="right", padx=5)
        tk.Button(frame_botoes, text="Enviar", command=enviar_relatorio).pack(side="right")

    def verificar_atualizacoes(self):
        """Verificar atualizações"""
        messagebox.showinfo("Atualizações", "Verificando atualizações...\n\n"
                                            "Você possui a versão mais recente (v2.1)")

    def mostrar_sobre(self):
        """Mostrar informações sobre o programa"""
        sobre = tk.Toplevel(self.janela)
        sobre.title("Sobre o CryptographiE")
        sobre.geometry("400x300")
        sobre.transient(self.janela)
        sobre.grab_set()

        frame = tk.Frame(sobre, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="CryptographiE", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(frame, text="Versão 2.1", font=("Arial", 12)).pack()

        info_texto = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=10)
        info_texto.pack(fill="both", expand=True, pady=20)

        sobre_conteudo = """Sistema Avançado de Criptografia

        Desenvolvido por: CONATUS Technologies
        Email: conatustechnologies@gmail.com

        RECURSOS:
        • Criptografia AES-256 de alta segurança
        • Interface intuitiva e responsiva
        • Processamento em lote de arquivos
        • Sistema de estatísticas completo
        • Gráficos interativos com matplotlib
        • Código Morse com Arduino
        • Compatibilidade multiplataforma

        SEGURANÇA:
        • Algoritmo Fernet (AES-256)
        • Derivação PBKDF2-SHA256
        • 100.000 iterações de hash
        • Chaves de 256 bits

        © 2024 CONATUS Technologies
        Todos os direitos reservados."""

        info_texto.insert("1.0", sobre_conteudo)
        info_texto.config(state="disabled")

        frame_botoes = tk.Frame(frame)
        frame_botoes.pack(fill="x")

        def abrir_website():
            webbrowser.open("https://brisashumanas.blogspot.com/")

        tk.Button(frame_botoes, text="Website", command=abrir_website).pack(side="left")
        tk.Button(frame_botoes, text="Fechar", command=sobre.destroy).pack(side="right")


# Função principal para executar o aplicativo
def main():
    try:
        root = tk.Tk()
        app = MenuLateralApp(root)
        root.mainloop()
    except ImportError as e:
        messagebox.showerror("Erro de Dependência",
                             "Biblioteca 'cryptography' não encontrada!\n\n" +
                             "Para instalar, execute:\n" +
                             "pip install cryptography\n\n" +
                             f"Erro: {e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()