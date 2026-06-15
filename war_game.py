import pygame
import random
import sys

# ==========================================
# CONFIGURAÇÕES GLOBAIS E INICIALIZAÇÃO
# ==========================================
pygame.init()
pygame.font.init()

LARGURA, ALTURA = 1280, 860
tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("War of Israely")
relogio = pygame.time.Clock()

MAPA = pygame.image.load("mapa_mundi.png")
MAPA = pygame.transform.scale(MAPA, (1280, 860))

# ==========================================
# PALETA DE CORES PALPÁVEL (DESIGN MODERNO)
# ==========================================
BG_DARK      = (18, 22, 28)
PANEL_BG     = (28, 35, 46)
PANEL_BORDER = (45, 55, 72)
TEXT_WHITE   = (240, 244, 248)
TEXT_MUTED   = (148, 163, 184)
GOLD         = (245, 158, 11)
CRIMSON      = (225, 29, 72)

# Cores dos Continentes (Identificação Visual do Tabuleiro)
COR_AM_NORTE = (239, 68, 68)    # Vermelho Vivo
COR_AM_SUL   = (34, 197, 94)    # Verde
COR_EUROPA   = (59, 130, 246)   # Azul
COR_AFRICA   = (168, 85, 247)   # Roxo
COR_ASIA     = (234, 179, 8)    # Amarelo Ouro
COR_OCEANIA  = (6, 182, 212)    # Ciano

# Cores das Tropas dos Jogadores (Pinos/Exércitos)
P_VERMELHO = (255, 50, 50)
P_AZUL     = (50, 150, 255)
P_VERDE    = (50, 255, 150)
P_AMARELO  = (255, 230, 50)
CORES_JOGADORES = [P_VERMELHO, P_AZUL, P_VERDE, P_AMARELO]

# ==========================================
# SISTEMA DE MISSÕES (ESTILO WAR ORIGINAL)
# ==========================================
MISSOES_POOL = [
    {
        "descricao": "Dominar a ÁSIA e a OCEANIA",
        "tipo": "continentes",
        "alvos": ["Ásia", "Oceania"],
    },
    {
        "descricao": "Dominar a ÁSIA e a AFRICA",
        "tipo": "continentes",
        "alvos": ["Ásia", "África"],
    },
    {
        "descricao": "Dominar a EUROPA e a AMERICA DO SUL",
        "tipo": "continentes",
        "alvos": ["Europa", "Am. Sul"],
    },
    {
        "descricao": "Dominar a AMERICA DO NORTE e a AFRICA",
        "tipo": "continentes",
        "alvos": ["Am. Norte", "África"],
    },
    {
        "descricao": "Dominar a EUROPE, a OCEANIA e mais 5 territórios quaisquer",
        "tipo": "continentes_mais",
        "alvos": ["Europa", "Oceania"],
        "bonus_territorios": 5,
    },
    {
        "descricao": "Dominar a AMERICA DO NORTE e a OCEANIA",
        "tipo": "continentes",
        "alvos": ["Am. Norte", "Oceania"],
    },
    {
        "descricao": "Conquistar 18 territórios e ocupá-los com pelo menos 2 exércitos cada",
        "tipo": "territorios_com_exercitos",
        "qtd_territorios": 18,
        "min_exercitos": 2,
    },
    {
        "descricao": "Conquistar 24 territórios quaisquer",
        "tipo": "territorios_simples",
        "qtd_territorios": 24,
    },
    {
        "descricao": "Eliminar completamente as tropas do Vermelho (J1)",
        "tipo": "eliminar_jogador",
        "alvo_jogador_idx": 0,
    },
    {
        "descricao": "Eliminar completamente as tropas do Azul (J2)",
        "tipo": "eliminar_jogador",
        "alvo_jogador_idx": 1,
    },
    {
        "descricao": "Eliminar completamente as tropas do Verde (J3)",
        "tipo": "eliminar_jogador",
        "alvo_jogador_idx": 2,
    },
    {
        "descricao": "Eliminar completamente as tropas do Amarelo (J4)",
        "tipo": "eliminar_jogador",
        "alvo_jogador_idx": 3,
    },
]

def verificar_missao(engine, jogador_idx):
    """Retorna True se o jogador_idx cumpriu sua missão."""
    missao = engine.missoes_jogadores.get(jogador_idx)
    if not missao:
        return False
    tipo = missao["tipo"]
    territorios_do_jogador = [t for t in engine.territorios.values() if t.dono == jogador_idx]
    continentes_dominados = set()
    for cont in ["Am. Norte", "Am. Sul", "Europa", "África", "Ásia", "Oceania"]:
        ids_cont = [t.id for t in engine.territorios.values() if t.continente == cont]
        if all(engine.territorios[tid].dono == jogador_idx for tid in ids_cont):
            continentes_dominados.add(cont)

    if tipo == "continentes":
        return all(c in continentes_dominados for c in missao["alvos"])
    elif tipo == "continentes_mais":
        domina_cont = all(c in continentes_dominados for c in missao["alvos"])
        extra = sum(1 for t in engine.territorios.values()
                    if t.dono == jogador_idx and t.continente not in missao["alvos"])
        return domina_cont and extra >= missao["bonus_territorios"]
    elif tipo == "territorios_simples":
        return len(territorios_do_jogador) >= missao["qtd_territorios"]
    elif tipo == "territorios_com_exercitos":
        qtd = sum(1 for t in territorios_do_jogador if t.exercitos >= missao["min_exercitos"])
        return qtd >= missao["qtd_territorios"]
    elif tipo == "eliminar_jogador":
        alvo = missao["alvo_jogador_idx"]
        # Se o próprio jogador É o alvo, a missão vira "conquistar 24 territórios"
        if alvo == jogador_idx:
            return len(territorios_do_jogador) >= 24
        return not any(t.dono == alvo for t in engine.territorios.values())
    return False

def desenhar_tela_missao(engine):
    """Overlay exibido ao iniciar o jogo mostrando a missão secreta de cada jogador."""
    import math
    tela.fill(BG_DARK)
    idx = engine.missao_reveal_jogador
    if idx >= engine.qtd_jogadores:
        engine.estado = "JOGANDO"
        engine.missao_reveal_jogador = 0
        return None

    cor_j = CORES_JOGADORES[idx]
    nome_j = engine.nomes_jogadores[idx]
    missao = engine.missoes_jogadores[idx]

    # Fundo animado
    agora = pygame.time.get_ticks()
    for x in range(0, LARGURA, 60):
        pygame.draw.line(tela, (20, 28, 40), (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, 60):
        pygame.draw.line(tela, (20, 28, 40), (0, y), (LARGURA, y))

    # Painel central
    painel = pygame.Rect(200, 140, 880, 500)
    pygame.draw.rect(tela, PANEL_BG, painel, border_radius=18)
    pygame.draw.rect(tela, cor_j, painel, 3, border_radius=18)

    # Cabeçalho
    txt_ordem = FONTE_G.render(f"MISSÃO SECRETA — {nome_j.upper()}", True, cor_j)
    tela.blit(txt_ordem, (LARGURA//2 - txt_ordem.get_width()//2, 175))

    pygame.draw.line(tela, cor_j, (220, 230), (LARGURA - 220, 230), 1)

    txt_instrucao = FONTE_M.render("Sua missão confidencial de campanha:", True, TEXT_MUTED)
    tela.blit(txt_instrucao, (LARGURA//2 - txt_instrucao.get_width()//2, 265))

    # Quebra automática da descrição em linhas de até 55 chars
    descricao = missao["descricao"]
    palavras = descricao.split()
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        if len(linha_atual) + len(palavra) + 1 <= 55:
            linha_atual += (" " if linha_atual else "") + palavra
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)

    y_desc = 320
    for linha in linhas:
        txt_linha = FONTE_G.render(linha, True, GOLD)
        tela.blit(txt_linha, (LARGURA//2 - txt_linha.get_width()//2, y_desc))
        y_desc += 46

    txt_aviso = FONTE_M.render("Não revele sua missão aos adversários!", True, CRIMSON)
    tela.blit(txt_aviso, (LARGURA//2 - txt_aviso.get_width()//2, 530))

    # Indicadores de jogadores (bolinhas na base)
    for i in range(engine.qtd_jogadores):
        cor_indicador = CORES_JOGADORES[i] if i == idx else PANEL_BORDER
        pygame.draw.circle(tela, cor_indicador, (LARGURA//2 - (engine.qtd_jogadores - 1)*20 + i*40, 580), 9)
        pygame.draw.circle(tela, TEXT_WHITE, (LARGURA//2 - (engine.qtd_jogadores - 1)*20 + i*40, 580), 9, 2)

    # Botão
    texto_btn = "PRÓXIMA MISSÃO ▶" if idx < engine.qtd_jogadores - 1 else "⚔ INICIAR GUERRA"
    btn = pygame.Rect(LARGURA//2 - 200, 600, 400, 56)
    mx, my = pygame.mouse.get_pos()
    hover = btn.collidepoint(mx, my)
    cor_btn = (22, 210, 150) if hover else (16, 185, 129)
    pygame.draw.rect(tela, cor_btn, btn, border_radius=12)
    pygame.draw.rect(tela, GOLD if hover else PANEL_BORDER, btn, 2, border_radius=12)
    txt_btn = FONTE_G.render(texto_btn, True, TEXT_WHITE)
    tela.blit(txt_btn, (btn.centerx - txt_btn.get_width()//2, btn.centery - txt_btn.get_height()//2))

    return btn

# Fontes Elegantes
FONTE_P = pygame.font.SysFont("Segoe UI", 13, bold=True)
FONTE_M = pygame.font.SysFont("Segoe UI", 18, bold=True)
FONTE_G = pygame.font.SysFont("Segoe UI", 28, bold=True)
FONTE_TG = pygame.font.SysFont("Segoe UI", 56, bold=True)

# ==========================================
# CLASSES DE DADOS E ENGENHARIA MAPA
# ==========================================
class Territorio:
    def __init__(self, id_t, nome, continente, cor_continente, x, y, conexoes):
        self.id = id_t
        self.nome = nome
        self.continente = continente
        self.cor_continente = cor_continente
        self.x = x
        self.y = y
        self.conexoes = conexoes  
        self.dono = None
        self.exercitos = 1
        self.rect = pygame.Rect(x - 40, y - 20, 80, 40)
        self.selecionado = False

    def desenhar(self, superficie, turno_jogador_cor, atacante_sel, alvo_possivel):
        cx, cy = self.x, self.y

        # --- Anel externo: cor do continente (ou feedback tático) ---
        raio_ext = 20
        cor_anel = self.cor_continente
        espessura_anel = 3
        if self.selecionado:
            cor_anel = GOLD
            espessura_anel = 4
        elif alvo_possivel:
            cor_anel = TEXT_WHITE
            espessura_anel = 3

        # Sombra sutil
        pygame.draw.circle(superficie, (0, 0, 0, 120), (cx + 2, cy + 2), raio_ext)

        # Círculo de fundo (cor do continente, semiescuro)
        cor_fundo = (
            int(self.cor_continente[0] * 0.25),
            int(self.cor_continente[1] * 0.25),
            int(self.cor_continente[2] * 0.25),
        )
        pygame.draw.circle(superficie, cor_fundo, (cx, cy), raio_ext)

        # Anel colorido (continente ou estado tático)
        pygame.draw.circle(superficie, cor_anel, (cx, cy), raio_ext, espessura_anel)

        # --- Pino do dono (círculo menor centralizado) ---
        cor_pino = CORES_JOGADORES[self.dono] if self.dono is not None else PANEL_BORDER
        raio_pino = 11
        pygame.draw.circle(superficie, cor_pino, (cx, cy), raio_pino)
        pygame.draw.circle(superficie, BG_DARK, (cx, cy), raio_pino, 2)

        # Número de tropas dentro do pino
        txt_qtd = FONTE_P.render(str(self.exercitos), True, BG_DARK if self.dono is not None else TEXT_WHITE)
        superficie.blit(txt_qtd, (cx - txt_qtd.get_width() // 2, cy - txt_qtd.get_height() // 2 + 1))

        # --- Nome do país flutuando acima do marcador ---
        txt_nome = FONTE_P.render(self.nome, True, TEXT_WHITE)
        nx = cx - txt_nome.get_width() // 2
        ny = cy - raio_ext - txt_nome.get_height() - 2
        # Fundo semitransparente para legibilidade
        bg_surf = pygame.Surface((txt_nome.get_width() + 6, txt_nome.get_height() + 2), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 140))
        superficie.blit(bg_surf, (nx - 3, ny - 1))
        superficie.blit(txt_nome, (nx, ny))

class Carta:
    def __init__(self, territorio_id, simbolo):
        self.territorio_id = territorio_id
        self.simbolo = simbolo # Quadrado, Triângulo, Círculo

# ==========================================
# MOTOR LOGÍSTICO DO JOGO
# ==========================================
class WarEngine:
    def __init__(self):
        self.estado = "MENU"
        self.qtd_jogadores = 3
        self.jogadores = []
        self.turno_atual = 0
        self.fase_atual = "DISTRIBUICAO"
        
        self.territorios = {}
        self.cartas_baralho = []
        self.cartas_jogadores = {}
        
        self.territorio_selecionado = None
        self.exercitos_para_distribuir = 0
        self.conquistou_neste_turno = False
        self.trocas_realizadas = 0
        self.logs = ["Aguardando início de campanha militar..."]
        self.missoes_jogadores = {}       # idx -> missao dict
        self.missao_reveal_jogador = 0    # qual jogador está vendo sua missao agora
        self.vencedor_missao = None       # idx do vencedor por missão

        # Nomes dos comandantes
        self.nomes_jogadores = ["Comandante 1", "Comandante 2", "Comandante 3", "Comandante 4"]
        self.input_ativo = -1   # índice do campo de texto ativo
        self.input_textos = ["", "", "", ""]  # buffer de digitação

        # ── Animação de batalha ──
        self.animacao_batalha = False
        self.anim_inicio_ms = 0
        self.anim_duracao_ms = 3800
        self.anim_atacante = None
        self.anim_defensor = None
        self.anim_dados_atk = []
        self.anim_dados_def = []
        self.anim_cor_atk = (255, 255, 255)
        self.anim_cor_def = (255, 255, 255)
        self.anim_angulos = [0.0] * 6
        self.anim_faces_rolando = [1] * 6
        self.anim_nome_atk = ""
        self.anim_nome_def = ""
        self.anim_resultado_pendente = None  # guarda kwargs para resolver após animação
        self.anim_aguardando_enter = False   # True quando os dados já pararam e esperam ENTER

        self.gerar_tabuleiro_completo()

    def gerar_tabuleiro_completo(self):
        # 32 Países Mapeados Vetorialmente por Coordenadas Estratégicas
        dados = [
    # AMÉRICA DO NORTE
    (1, "Alaska",      "Am. Norte", COR_AM_NORTE,  70, 140, [2,3,24]),
    (2, "Calgary",     "Am. Norte", COR_AM_NORTE, 190, 160, [1,3,4]),
    (3, "Groenlândia", "Am. Norte", COR_AM_NORTE, 460, 110, [1,2,5,11]),
    (4, "Califórnia",  "Am. Norte", COR_AM_NORTE, 160, 300, [2,5,6]),
    (5, "Nova York",   "Am. Norte", COR_AM_NORTE, 310, 250, [2,3,4,6]),
    (6, "México",      "Am. Norte", COR_AM_NORTE, 250, 390, [4,5,7]),

    # AMÉRICA DO SUL
    (7, "Venezuela",   "Am. Sul", COR_AM_SUL, 320, 430, [6,8,9]),
    (8, "Brasil",      "Am. Sul", COR_AM_SUL, 390, 500, [7,9,10,14]),
    (9, "Peru",        "Am. Sul", COR_AM_SUL, 290, 490, [7,8,10]),
    (10,"Argentina",   "Am. Sul", COR_AM_SUL, 330, 600, [8,9]),

    # EUROPA
    (11,"Islândia",    "Europa", COR_EUROPA, 620, 90, [3,12,13]),
    (12,"Reino Unido", "Europa", COR_EUROPA, 545, 195, [11,13,14]),
    (13,"Alemanha",    "Europa", COR_EUROPA, 700, 215, [11,12,14,15]),
    (14,"França",      "Europa", COR_EUROPA, 625, 270, [8,12,13,15]),
    (15,"Itália",      "Europa", COR_EUROPA, 710, 310, [13,14,16]),

    # ÁFRICA
    (16,"Argélia",     "África", COR_AFRICA, 580, 400, [15,17,18]),
    (17,"Egito",       "África", COR_AFRICA, 695, 395, [16,18,19,21]),
    (18,"Congo",       "África", COR_AFRICA, 645, 495, [16,17,20]),
    (19,"Oriente Médio","África",COR_AFRICA, 800, 385, [17,21,22]),
    (20,"África do Sul","África",COR_AFRICA, 650, 550, [18,30]),

    # ÁSIA
    (21,"Moscou",      "Ásia", COR_ASIA, 820, 180, [17,22,23,24]),
    (22,"Aral",        "Ásia", COR_ASIA, 900, 255, [19,21,23,25]),
    (23,"Sibéria",     "Ásia", COR_ASIA,1000, 130, [21,22,24,26]),
    (24,"Vladivostok", "Ásia", COR_ASIA,1135, 170, [1,21,23,27]),
    (25,"Índia",       "Ásia", COR_ASIA, 955, 395, [22,26,28]),
    (26,"China",       "Ásia", COR_ASIA,1065, 310, [23,25,27,28]),
    (27,"Japão",       "Ásia", COR_ASIA,1165, 245, [24,26]),
    (28,"Vietnã",      "Ásia", COR_ASIA,1055, 430, [25,26,29]),

    # OCEANIA
    (29,"Indonésia",   "Oceania", COR_OCEANIA,1075, 480, [28,30,31]),
    (30,"Austrália",   "Oceania", COR_OCEANIA,1085, 555, [20,29,32]),
    (31,"Nova Guiné",  "Oceania", COR_OCEANIA,1155, 440, [29,32]),
    (32,"Nova Zelândia","Oceania",COR_OCEANIA,1200, 615, [30,31]),
]
        
        for dt in dados:
            self.territorios[dt[0]] = Territorio(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6])
            
        simbolos = ["Quadrado", "Triângulo", "Círculo"]
        for idx, t_id in enumerate(self.territorios.keys()):
            self.cartas_baralho.append(Carta(t_id, simbolos[idx % 3]))

    def adicionar_log(self, texto):
        self.logs.append(texto)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def iniciar_jogo(self):
        # Salva nomes dos campos de input (se preenchidos)
        for i in range(self.qtd_jogadores):
            txt = self.input_textos[i].strip()
            if txt:
                self.nomes_jogadores[i] = txt
            else:
                self.nomes_jogadores[i] = f"Comandante {i+1}"

        self.jogadores = list(range(self.qtd_jogadores))
        self.cartas_jogadores = {j: [] for j in self.jogadores}
        self.turno_atual = 0
        self.trocas_realizadas = 0
        
        ids_embaralhados = list(self.territorios.keys())
        random.shuffle(ids_embaralhados)
        
        for idx, t_id in enumerate(ids_embaralhados):
            dono = self.jogadores[idx % self.qtd_jogadores]
            self.territorios[t_id].dono = dono
            self.territorios[t_id].exercitos = random.randint(2, 4)
            
        self.calcular_exercitos_ganhos()
        self.sortear_missoes()
        self.estado = "MISSAO_REVEAL"
        self.missao_reveal_jogador = 0
        self.vencedor_missao = None
        self.fase_atual = "DISTRIBUICAO"
        self.adicionar_log("Guerra Global Declarada! Alavanque suas tropas defensoras.")

    def sortear_missoes(self):
        """Sorteia missões únicas para cada jogador, garantindo que eliminar-jogador não aponte para si mesmo ou para jogador inexistente."""
        pool_embaralhada = list(MISSOES_POOL)
        random.shuffle(pool_embaralhada)
        self.missoes_jogadores = {}
        for j in self.jogadores:
            for missao in pool_embaralhada:
                # Pula missões de eliminar jogador inválidas (jogador não existe no jogo)
                if missao["tipo"] == "eliminar_jogador":
                    alvo = missao["alvo_jogador_idx"]
                    if alvo >= self.qtd_jogadores:
                        continue
                # Garante que cada jogador receba missão diferente se possível
                ja_usada = missao in self.missoes_jogadores.values()
                if not ja_usada:
                    self.missoes_jogadores[j] = missao
                    break
            else:
                # Fallback: missão genérica de 24 territórios
                self.missoes_jogadores[j] = {
                    "descricao": "Conquistar 24 territórios quaisquer",
                    "tipo": "territorios_simples",
                    "qtd_territorios": 24,
                }

    def calcular_exercitos_ganhos(self):
        total_territorios = sum(1 for t in self.territorios.values() if t.dono == self.turno_atual)
        self.exercitos_para_distribuir = max(3, total_territorios // 2)
        self.conquistou_neste_turno = False

    def avancar_fase(self):
        if self.fase_atual == "DISTRIBUICAO":
            if self.exercitos_para_distribuir > 0:
                self.adicionar_log("Aviso: Você possui tropas pendentes na reserva!")
                return
            self.fase_atual = "ATAQUE"
            self.adicionar_log("Ordem de Ataque emitida. Escolha uma base armada.")
        elif self.fase_atual == "ATAQUE":
            self.fase_atual = "REMANEJAMENTO"
            self.adicionar_log("Fase de Remanejamento: Movimentação de comboios de defesa.")
        elif self.fase_atual == "REMANEJAMENTO":
            if self.conquistou_neste_turno and self.cartas_baralho:
                carta_ganha = self.cartas_baralho.pop(random.randint(0, len(self.cartas_baralho)-1))
                self.cartas_jogadores[self.turno_atual].append(carta_ganha)
                self.adicionar_log(f"Espionagem obteve carta territorial: {self.territorios[carta_ganha.territorio_id].nome}!")

            # Avança o turno para o próximo vivo
            loop_seguranca = 0
            while loop_seguranca < 10:
                self.turno_atual = (self.turno_atual + 1) % self.qtd_jogadores
                if any(t.dono == self.turno_atual for t in self.territorios.values()):
                    break
                loop_seguranca += 1
            
            self.fase_atual = "DISTRIBUICAO"
            self.calcular_exercitos_ganhos()
            self.adicionar_log(f"Nova Rodada! Vez de {self.nomes_jogadores[self.turno_atual]}")
            # Verificar vitória por missão de qualquer jogador ativo
            for j in self.jogadores:
                if any(t.dono == j for t in self.territorios.values()):
                    if verificar_missao(self, j):
                        self.vencedor_missao = j
                        self.estado = "VITORIA_MISSAO"
                        return
            
        if self.territorio_selecionado:
            self.territorio_selecionado.selecionado = False
            self.territorio_selecionado = None

    def calcular_max_dados(self, qtd_soldados):
        """
        Define o número MÁXIMO de dados que um exército pode lançar com
        base no seu tamanho. Exércitos maiores ganham acesso a mais dados,
        representando sua superioridade numérica, enquanto exércitos
        pequenos ficam restritos a poucos dados. O teto absoluto é 3 dados.
        """
        if qtd_soldados <= 2:
            return 1
        elif qtd_soldados <= 5:
            return 2
        else:
            return 3

    def calcular_dados_disponiveis(self, atacante, defensor):
        """
        Verifica o número de soldados de cada lado e define quantos dados
        cada exército poderá lançar no confronto. O lado com mais soldados
        recebe um teto de dados maior (vantagem estratégica pela superioridade
        numérica), mas o resultado de cada dado permanece aleatório (sorte).
        """
        # O atacante precisa manter ao menos 1 soldado de guarnição no território
        soldados_disponiveis_atk = atacante.exercitos - 1
        soldados_disponiveis_def = defensor.exercitos

        teto_atk = self.calcular_max_dados(atacante.exercitos)
        teto_def = self.calcular_max_dados(defensor.exercitos)

        n_dados_atk = max(0, min(soldados_disponiveis_atk, teto_atk))
        n_dados_def = max(0, min(soldados_disponiveis_def, teto_def))

        return n_dados_atk, n_dados_def

    def realizar_ataque(self, atacante, defensor):
        if atacante.exercitos <= 1: return

        n_dados_atk, n_dados_def = self.calcular_dados_disponiveis(atacante, defensor)
        if n_dados_atk <= 0 or n_dados_def <= 0:
            return

        dados_atk = sorted([random.randint(1, 6) for _ in range(n_dados_atk)], reverse=True)
        dados_def = sorted([random.randint(1, 6) for _ in range(n_dados_def)], reverse=True)

        # ── Iniciar animação de batalha ──
        self.animacao_batalha = True
        self.anim_aguardando_enter = False
        self.anim_inicio_ms = pygame.time.get_ticks()
        self.anim_atacante = atacante
        self.anim_defensor = defensor
        self.anim_dados_atk = dados_atk
        self.anim_dados_def = dados_def
        self.anim_cor_atk = CORES_JOGADORES[atacante.dono]
        self.anim_cor_def = CORES_JOGADORES[defensor.dono] if defensor.dono is not None else TEXT_MUTED
        total_dados = n_dados_atk + n_dados_def
        self.anim_angulos = [random.uniform(0, 360) for _ in range(total_dados)]
        self.anim_faces_rolando = [random.randint(1, 6) for _ in range(total_dados)]
        self.anim_nome_atk = self.nomes_jogadores[atacante.dono]
        self.anim_nome_def = self.nomes_jogadores[defensor.dono] if defensor.dono is not None else defensor.nome
        # Guarda resultado para aplicar após animação
        self.anim_resultado_pendente = {
            "atacante": atacante, "defensor": defensor,
            "dados_atk": dados_atk, "dados_def": dados_def,
            "n_dados_atk": n_dados_atk
        }

    def resolver_ataque_apos_animacao(self):
        """Aplica o resultado do ataque após a animação terminar."""
        r = self.anim_resultado_pendente
        if not r: return
        atacante = r["atacante"]
        defensor = r["defensor"]
        dados_atk = r["dados_atk"]
        dados_def = r["dados_def"]
        n_dados_atk = r["n_dados_atk"]

        perdas_atk = 0
        perdas_def = 0
        for i in range(min(len(dados_atk), len(dados_def))):
            if dados_atk[i] > dados_def[i]: perdas_def += 1
            else: perdas_atk += 1

        atacante.exercitos -= perdas_atk
        defensor.exercitos -= perdas_def
        self.adicionar_log(f"Conflito: ATK {dados_atk} vs DEF {dados_def}")

        if defensor.exercitos <= 0:
            self.adicionar_log(f"Sucesso! Fronteira de {defensor.nome} foi anexada.")
            defensor.dono = atacante.dono
            defensor.exercitos = n_dados_atk - perdas_atk
            atacante.exercitos -= (n_dados_atk - perdas_atk)
            self.conquistou_neste_turno = True
            atacante.selecionado = False
            self.territorio_selecionado = None

        self.animacao_batalha = False
        self.anim_aguardando_enter = False
        self.anim_resultado_pendente = None

    def tentar_troca_cartas(self):
        cartas = self.cartas_jogadores[self.turno_atual]
        if len(cartas) < 3: return
        contagem = {"Quadrado": 0, "Triângulo": 0, "Círculo": 0}
        for c in cartas: contagem[c.simbolo] += 1
        
        troca_valida = False
        cartas_para_remover = []
        for simb, qtd in contagem.items():
            if qtd >= 3:
                troca_valida = True
                cartas_para_remover = [c for c in cartas if c.simbolo == simb][:3]
                break
        if not troca_valida and contagem["Quadrado"] >= 1 and contagem["Triângulo"] >= 1 and contagem["Círculo"] >= 1:
            troca_valida = True
            for simb in ["Quadrado", "Triângulo", "Círculo"]:
                for c in cartas:
                    if c.simbolo == simb:
                        cartas_para_remover.append(c)
                        break
        if troca_valida:
            for c in cartas_para_remover:
                self.cartas_jogadores[self.turno_atual].remove(c)
                self.cartas_baralho.append(c)
            self.trocas_realizadas += 1
            bonus = 4 + (self.trocas_realizadas * 2)
            self.exercitos_para_distribuir += bonus
            self.adicionar_log(f"Suprimentos Recebidos! Bônus de +{bonus} exércitos na reserva.")

    def tratar_clique_mapa(self, pos):
        territorio_clicado = None
        melhor_dist = 22  # raio de detecção de clique (px)
        for t in self.territorios.values():
            dx = pos[0] - t.x
            dy = pos[1] - t.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < melhor_dist:
                melhor_dist = dist
                territorio_clicado = t
        if not territorio_clicado: return

        if self.fase_atual == "DISTRIBUICAO":
            if territorio_clicado.dono == self.turno_atual and self.exercitos_para_distribuir > 0:
                territorio_clicado.exercitos += 1
                self.exercitos_para_distribuir -= 1
        elif self.fase_atual == "ATAQUE":
            if self.territorio_selecionado is None:
                if territorio_clicado.dono == self.turno_atual and territorio_clicado.exercitos > 1:
                    self.territorio_selecionado = territorio_clicado
                    territorio_clicado.selecionado = True
            else:
                if territorio_clicado == self.territorio_selecionado:
                    self.territorio_selecionado.selecionado = False
                    self.territorio_selecionado = None
                elif territorio_clicado.id in self.territorio_selecionado.conexoes and territorio_clicado.dono != self.turno_atual:
                    self.realizar_ataque(self.territorio_selecionado, territorio_clicado)
                else:
                    self.territorio_selecionado.selecionado = False
                    self.territorio_selecionado = None
        elif self.fase_atual == "REMANEJAMENTO":
            if self.territorio_selecionado is None:
                if territorio_clicado.dono == self.turno_atual and territorio_clicado.exercitos > 1:
                    self.territorio_selecionado = territorio_clicado
                    territorio_clicado.selecionado = True
            else:
                if territorio_clicado == self.territorio_selecionado:
                    self.territorio_selecionado.selecionado = False
                    self.territorio_selecionado = None
                elif territorio_clicado.id in self.territorio_selecionado.conexoes and territorio_clicado.dono == self.turno_atual:
                    if self.territorio_selecionado.exercitos > 1:
                        self.territorio_selecionado.exercitos -= 1
                        territorio_clicado.exercitos += 1

# ==========================================
# ANIMAÇÃO DO DADO
# ==========================================
DADO_FACES = [
    # Cada face: lista de círculos (cx_rel, cy_rel) em fração 0..1 dentro do cubo
    [(0.5, 0.5)],                                                    # 1
    [(0.25, 0.25), (0.75, 0.75)],                                    # 2
    [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],                       # 3
    [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],       # 4
    [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],  # 5
    [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],  # 6
]

# ==========================================
# ANIMAÇÃO DE BATALHA (OVERLAY DE ATAQUE)
# ==========================================
def desenhar_animacao_batalha(engine):
    """Renderiza o overlay de animação de dados durante o ataque."""
    import math
    agora = pygame.time.get_ticks()

    if engine.anim_aguardando_enter:
        # Dados já pararam: mantém o resultado final congelado na tela
        progresso = 1.0
        rolando = False
    else:
        elapsed = agora - engine.anim_inicio_ms
        progresso = min(1.0, elapsed / engine.anim_duracao_ms)
        # Fase: 0..0.7 = dados girando, 0.7..1.0 = desacelerando e revelando a face final
        rolando = progresso < 0.7

    # Overlay escurecido semitransparente sobre o mapa
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay_alpha = int(200 * min(1.0, progresso * 4))
    overlay.fill((8, 10, 16, overlay_alpha))
    tela.blit(overlay, (0, 0))

    # Painel central da batalha
    pw, ph = 860, 420
    px = LARGURA // 2 - pw // 2
    py = ALTURA // 2 - ph // 2
    painel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(painel, (20, 26, 38, 230), pygame.Rect(0, 0, pw, ph), border_radius=20)
    pygame.draw.rect(painel, (60, 70, 90, 255), pygame.Rect(0, 0, pw, ph), 2, border_radius=20)
    tela.blit(painel, (px, py))

    # Título da batalha (pisca no início)
    titulo_alpha = 255 if progresso > 0.1 else int(255 * progresso * 10)
    txt_batalha = FONTE_G.render("⚔  BATALHA DECLARADA  ⚔", True, CRIMSON)
    ts = pygame.Surface((txt_batalha.get_width(), txt_batalha.get_height()), pygame.SRCALPHA)
    ts.blit(txt_batalha, (0, 0))
    ts.set_alpha(titulo_alpha)
    tela.blit(ts, (LARGURA // 2 - txt_batalha.get_width() // 2, py + 18))

    # Nomes dos comandantes
    nome_atk_surf = FONTE_M.render(f"⚔ {engine.anim_nome_atk.upper()}", True, engine.anim_cor_atk)
    nome_def_surf = FONTE_M.render(f"🛡 {engine.anim_nome_def.upper()}", True, engine.anim_cor_def)
    tela.blit(nome_atk_surf, (px + 40, py + 65))
    tela.blit(nome_def_surf, (px + pw - nome_def_surf.get_width() - 40, py + 65))

    vs_surf = FONTE_G.render("VS", True, GOLD)
    tela.blit(vs_surf, (LARGURA // 2 - vs_surf.get_width() // 2, py + 60))

    # Linha divisória
    pygame.draw.line(tela, PANEL_BORDER, (px + 20, py + 100), (px + pw - 20, py + 100), 1)

    # ── Velocidade de rotação: suave no início, desacelera bem no final ──
    vel_base = 7.0
    if not engine.anim_aguardando_enter:
        if rolando:
            vel = vel_base
        else:
            t_desacel = (progresso - 0.7) / 0.3  # 0..1
            vel = vel_base * (1.0 - t_desacel) ** 2

        for i in range(len(engine.anim_angulos)):
            engine.anim_angulos[i] = (engine.anim_angulos[i] + vel * (1 + i * 0.12)) % 360

        # Troca de face aleatória durante a rolagem (ritmo mais calmo)
        if rolando and (agora // 130) % 2 == 0:
            engine.anim_faces_rolando = [random.randint(1, 6) for _ in range(len(engine.anim_faces_rolando))]

    n_atk = len(engine.anim_dados_atk)
    n_def = len(engine.anim_dados_def)

    gap = 20
    # Largura disponível para cada lado do painel de batalha (com margem central)
    largura_disponivel_lado = 350
    maior_lado = max(n_atk, n_def, 1)
    dado_size = min(90, (largura_disponivel_lado - (maior_lado - 1) * gap) // maior_lado)
    dado_size = max(40, dado_size)

    # ── DADOS DO ATACANTE (esquerda) ──
    total_w_atk = n_atk * dado_size + (n_atk - 1) * gap
    x_atk_start = LARGURA // 2 - 80 - total_w_atk
    y_dados = ALTURA // 2 + 10

    label_atk = FONTE_P.render("ATAQUE", True, engine.anim_cor_atk)
    tela.blit(label_atk, (x_atk_start + total_w_atk // 2 - label_atk.get_width() // 2, y_dados - 55))

    for i, face_final in enumerate(engine.anim_dados_atk):
        cx = x_atk_start + i * (dado_size + gap) + dado_size // 2
        cy = y_dados + dado_size // 2
        face_exibida = engine.anim_faces_rolando[i] if rolando else face_final
        angulo_exibido = engine.anim_angulos[i] if rolando else 0
        desenhar_dado_batalha(tela, cx, cy, dado_size, face_exibida, angulo_exibido, engine.anim_cor_atk, rolando)

    # ── DADOS DO DEFENSOR (direita) ──
    total_w_def = n_def * dado_size + (n_def - 1) * gap
    x_def_start = LARGURA // 2 + 80
    y_dados_def = ALTURA // 2 + 10

    label_def = FONTE_P.render("DEFESA", True, engine.anim_cor_def)
    tela.blit(label_def, (x_def_start + total_w_def // 2 - label_def.get_width() // 2, y_dados_def - 55))

    for i, face_final in enumerate(engine.anim_dados_def):
        cx = x_def_start + i * (dado_size + gap) + dado_size // 2
        cy = y_dados_def + dado_size // 2
        face_exibida = engine.anim_faces_rolando[n_atk + i] if rolando else face_final
        angulo_exibido = engine.anim_angulos[n_atk + i] if rolando else 0
        desenhar_dado_batalha(tela, cx, cy, dado_size, face_exibida, angulo_exibido, engine.anim_cor_def, rolando)

    # ── Barra de progresso da animação ──
    barra_w = pw - 80
    pygame.draw.rect(tela, PANEL_BORDER, pygame.Rect(px + 40, py + ph - 46, barra_w, 10), border_radius=5)
    fill_w = int(barra_w * progresso)
    if fill_w > 0:
        cor_barra = GOLD if not rolando else CRIMSON
        pygame.draw.rect(tela, cor_barra, pygame.Rect(px + 40, py + ph - 46, fill_w, 10), border_radius=5)

    if engine.anim_aguardando_enter:
        # Texto pulsante convidando a continuar
        pulso = 0.55 + 0.45 * abs(math.sin(agora / 250))
        st = FONTE_M.render("Resultado revelado!  Pressione ENTER para continuar", True, GOLD)
        ts2 = pygame.Surface(st.get_size(), pygame.SRCALPHA)
        ts2.blit(st, (0, 0))
        ts2.set_alpha(int(140 + 115 * pulso))
        tela.blit(ts2, (LARGURA // 2 - st.get_width() // 2, py + ph - 34))
    else:
        status_txt = "Dados rolando..." if rolando else "Revelando resultado..."
        st = FONTE_P.render(status_txt, True, GOLD if not rolando else TEXT_MUTED)
        tela.blit(st, (LARGURA // 2 - st.get_width() // 2, py + ph - 30))

    # Terminou a rolagem → aguarda confirmação manual (ENTER) antes de resolver
    if progresso >= 1.0:
        engine.anim_aguardando_enter = True


def desenhar_dado_batalha(superficie, cx, cy, tamanho, face, angulo, cor_comandante, rolando):
    """Dado de batalha colorido com a cor do comandante, com giro 3D suave."""
    import math
    face = max(1, min(6, face))
    pontos = DADO_FACES[face - 1]

    # ── Desenha a face do dado numa superfície quadrada própria ──
    base = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)

    # Corpo do dado com tom derivado da cor do comandante
    r_bg = min(255, 35 + cor_comandante[0] // 4)
    g_bg = min(255, 35 + cor_comandante[1] // 4)
    b_bg = min(255, 35 + cor_comandante[2] // 4)
    corpo_rect = pygame.Rect(0, 0, tamanho, tamanho)
    pygame.draw.rect(base, (r_bg, g_bg, b_bg), corpo_rect, border_radius=18)

    # Borda na cor do comandante
    pygame.draw.rect(base, cor_comandante, corpo_rect, 4, border_radius=18)

    # Pontos (pips) com sombra sutil para profundidade
    ponto_cor = (245, 245, 250) if not rolando else (220, 220, 230)
    for (fx, fy) in pontos:
        px_p = int(fx * tamanho)
        py_p = int(fy * tamanho)
        r_pip = max(4, int(tamanho * 0.09))
        pygame.draw.circle(base, (12, 16, 24), (px_p + 1, py_p + 2), r_pip)
        pygame.draw.circle(base, ponto_cor, (px_p, py_p), r_pip)

    # Brilho diagonal no topo (sensação de superfície polida)
    brilho = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    pygame.draw.polygon(brilho, (255, 255, 255, 35),
                         [(0, 0), (tamanho, 0), (tamanho * 0.55, tamanho * 0.4), (0, tamanho * 0.25)])
    base.blit(brilho, (0, 0))

    # ── Giro 3D: rotação + leve oscilação de escala (efeito de tumbling) ──
    if rolando:
        escala = 0.78 + 0.22 * abs(math.sin(math.radians(angulo * 1.4)))
        dado_final = pygame.transform.rotozoom(base, angulo, escala)
    else:
        dado_final = base

    fw, fh = dado_final.get_size()

    # Sombra projetada (acompanha o tamanho atual do dado)
    sombra = pygame.Surface((fw + 14, fh + 14), pygame.SRCALPHA)
    sombra_cor = (*[c // 3 for c in cor_comandante], 90)
    pygame.draw.ellipse(sombra, sombra_cor, pygame.Rect(7, fh - 8, fw, 18))
    superficie.blit(sombra, (cx - (fw + 14) // 2, cy - (fh + 14) // 2 + 6))

    # Leve brilho externo quando o resultado é revelado
    if not rolando:
        halo = pygame.Surface((fw + 16, fh + 16), pygame.SRCALPHA)
        pygame.draw.rect(halo, (*cor_comandante, 60), pygame.Rect(0, 0, fw + 16, fh + 16), border_radius=22)
        superficie.blit(halo, (cx - (fw + 16) // 2, cy - (fh + 16) // 2))

    superficie.blit(dado_final, (cx - fw // 2, cy - fh // 2))

# ==========================================
# MOTOR GRÁFICO (INTERFACE POLIDA)
# ==========================================
def desenhar_menu(tick):
    import math

    tela.fill(BG_DARK)
    
    # ── Grade hexagonal de fundo ──
    HEX_COR = (24, 30, 42)
    h_gap = 60
    v_gap = 52
    for row in range(ALTURA // v_gap + 2):
        for col in range(LARGURA // h_gap + 2):
            ox = (col * h_gap) + (30 if row % 2 else 0)
            oy = row * v_gap
            pts = [(ox + 25*math.cos(math.radians(60*i)), oy + 25*math.sin(math.radians(60*i))) for i in range(6)]
            pygame.draw.polygon(tela, HEX_COR, pts, 1)

    # ── Gradiente lateral esquerdo (barra decorativa) ──
    barra = pygame.Surface((8, ALTURA), pygame.SRCALPHA)
    for i in range(ALTURA):
        a = int(255 * abs(math.sin(math.pi * i / ALTURA)))
        pygame.draw.line(barra, (*GOLD, a), (0, i), (7, i))
    tela.blit(barra, (0, 0))
    tela.blit(barra, (LARGURA - 8, 0))

    # ── Título ──
    sombra_t = FONTE_TG.render("WAR OF ISRAELY", True, (0,0,0))
    tela.blit(sombra_t, (LARGURA//2 - sombra_t.get_width()//2 + 3, 113))
    txt = FONTE_TG.render("WAR OF ISRAELY", True, GOLD)
    tela.blit(txt, (LARGURA//2 - txt.get_width()//2, 110))

    subsubtxt = FONTE_M.render("EEEP Jeová Costa Lima - Informática 1", True, TEXT_MUTED)
    anotxt = FONTE_M.render("2026", True, TEXT_MUTED)
    subtxt = FONTE_M.render("Por: Vitor Medeiros, Pedro Segundo, Ramon Nogueira, Ravir Sousa e Miguel Alves", True, TEXT_MUTED)
    tela.blit(subtxt, (LARGURA//2 - subtxt.get_width()//2, 180))
    tela.blit(subsubtxt, (LARGURA//2 - subsubtxt.get_width()//2, 220))
    tela.blit(anotxt, (LARGURA//2 - anotxt.get_width()//2, 240))

    # ── Linha divisória ──
    pygame.draw.line(tela, PANEL_BORDER, (LARGURA//2 - 200, 215), (LARGURA//2 + 200, 215), 1)

    # ── Botões modernos ──
    botoes_dados = []
    configs_botoes = [
        ("INICIAR CONQUISTA", (16, 185, 129), "▶"),
        ("MANUAL TÁTICO",     PANEL_BG,       "📖"),
        ("SAIR DO CAMPO",     (60, 30, 40),   "✕"),
    ]
    y_base = 290
    for i, (label, cor, icone) in enumerate(configs_botoes):
        b = pygame.Rect(LARGURA//2 - 190, y_base + i*76, 380, 56)
        botoes_dados.append(b)
        
        # Brilho de hover
        mx, my = pygame.mouse.get_pos()
        hover = b.collidepoint(mx, my)
        
        sombra_b = pygame.Surface((b.width + 6, b.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(sombra_b, (0,0,0,80), pygame.Rect(3,3,b.width,b.height), border_radius=12)
        tela.blit(sombra_b, (b.x-3, b.y+3))
        
        cor_btn = tuple(min(255, c + 25) for c in cor) if hover else cor
        pygame.draw.rect(tela, cor_btn, b, border_radius=12)
        
        # Borda dourada apenas no botão de hover
        borda_cor = GOLD if hover else PANEL_BORDER
        pygame.draw.rect(tela, borda_cor, b, 2, border_radius=12)
        
        tx = FONTE_M.render(label, True, TEXT_WHITE)
        tela.blit(tx, (b.centerx - tx.get_width()//2, b.centery - tx.get_height()//2))

    return botoes_dados[0], botoes_dados[1], botoes_dados[2]

def desenhar_manual():
    tela.fill(BG_DARK)
    pygame.draw.rect(tela, PANEL_BG, pygame.Rect(50, 50, LARGURA-100, ALTURA-100), border_radius=12)
    
    txt_t = FONTE_G.render("MANUAL OPERACIONAL DE CAMPANHA", True, GOLD)
    tela.blit(txt_t, (80, 80))
    
    regras = [
        "1. DISTRIBUIÇÃO E REFORÇO DA GUARDA: No início de cada rodada, você receberá guarnições equivalentes",
        "   à metade dos territórios conquistados. Aloque-os de forma astuta clicando em suas posições.",
        "2. CAMPANHA OFENSIVA (ATAQUE): Escolha um território sob sua jurisdição com mais de 2 exércitos.",
        "   Em seguida, escolha uma nação inimiga conectada pelas malhas de comunicação terrestres/marítimas.",
        "3. LOGÍSTICA DE COMBATE: Os dados são lançados no centro de inteligência. A Defesa detém a vantagem",
        "   estratégica, vencendo batalhas individuais em caso de empates numéricos nos valores.",
        "4. REMANEJAMENTO TÁTICO: Envie tropas excedentes entre países aliados conectados para assegurar proteção.",
        "5. INTELIGÊNCIA CARTOGRÁFICA: Dominar um território garante uma carta. Combine trios para ganhar bônus robustos."
    ]
    y = 170
    for r in regras:
        tela.blit(FONTE_M.render(r, True, TEXT_MUTED), (80, y))
        y += 48
        
    b_v = pygame.Rect(80, 630, 200, 50)
    pygame.draw.rect(tela, CRIMSON, b_v, border_radius=8)
    tx = FONTE_M.render("RETORNAR", True, TEXT_WHITE)
    tela.blit(tx, (b_v.centerx - tx.get_width()//2, b_v.centery - tx.get_height()//2))
    return b_v

def desenhar_config(engine):
    import math
    tela.fill(BG_DARK)
    
    # Fundo decorativo
    for x in range(0, LARGURA, 40):
        pygame.draw.line(tela, (22, 28, 38), (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, 40):
        pygame.draw.line(tela, (22, 28, 38), (0, y), (LARGURA, y))

    # Painel central
    painel = pygame.Rect(260, 60, 760, 740)
    pygame.draw.rect(tela, PANEL_BG, painel, border_radius=18)
    pygame.draw.rect(tela, GOLD, painel, 2, border_radius=18)

    # Título
    txt = FONTE_G.render("DISPOSIÇÃO DOS IMPÉRIOS", True, GOLD)
    tela.blit(txt, (LARGURA//2 - txt.get_width()//2, 90))

    sub = FONTE_M.render("Configure o número de comandantes e seus nomes", True, TEXT_MUTED)
    tela.blit(sub, (LARGURA//2 - sub.get_width()//2, 133))

    # Seletor de quantidade
    txt_q = FONTE_G.render(f"{engine.qtd_jogadores} Comandantes", True, TEXT_WHITE)
    tela.blit(txt_q, (LARGURA//2 - txt_q.get_width()//2, 168))

    bm = pygame.Rect(LARGURA//2 - 155, 165, 44, 44)
    bp = pygame.Rect(LARGURA//2 + 111, 165, 44, 44)
    for b, sym in [(bm, "−"), (bp, "+")]:
        pygame.draw.rect(tela, PANEL_BORDER, b, border_radius=8)
        pygame.draw.rect(tela, GOLD, b, 1, border_radius=8)
        ts = FONTE_G.render(sym, True, GOLD)
        tela.blit(ts, (b.centerx - ts.get_width()//2, b.centery - ts.get_height()//2 - 2))

    # Campos de nome por jogador
    PLAYER_LABELS = ["COMANDANTE I", "COMANDANTE II", "COMANDANTE III", "COMANDANTE IV"]
    input_rects = []
    y0 = 240
    row_h = 86
    for i in range(engine.qtd_jogadores):
        cor_j = CORES_JOGADORES[i]
        
        # Label
        lbl = FONTE_P.render(PLAYER_LABELS[i], True, cor_j)
        tela.blit(lbl, (310, y0 + i*row_h))
        
        # Caixa de input
        r = pygame.Rect(310, y0 + i*row_h + 20, 620, 40)
        input_rects.append(r)
        
        ativo = (engine.input_ativo == i)
        cor_borda = GOLD if ativo else PANEL_BORDER
        pygame.draw.rect(tela, BG_DARK, r, border_radius=8)
        pygame.draw.rect(tela, cor_borda, r, 2, border_radius=8)
        
        # Indicador colorido de jogador
        pygame.draw.circle(tela, cor_j, (r.x + 18, r.centery), 7)
        
        # Texto digitado ou placeholder
        texto_exibido = engine.input_textos[i]
        if not texto_exibido:
            txt_in = FONTE_M.render(f"Nome do Comandante {i+1}...", True, (60, 75, 95))
        else:
            cursor = "|" if ativo and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            txt_in = FONTE_M.render(texto_exibido + cursor, True, TEXT_WHITE)
        tela.blit(txt_in, (r.x + 34, r.centery - txt_in.get_height()//2))

    # Botão Lançar
    bc = pygame.Rect(LARGURA//2 - 200, 590, 400, 56)
    mx, my = pygame.mouse.get_pos()
    hover_bc = bc.collidepoint(mx, my)
    cor_bc = (22, 210, 150) if hover_bc else (16, 185, 129)
    pygame.draw.rect(tela, cor_bc, bc, border_radius=12)
    pygame.draw.rect(tela, GOLD if hover_bc else (0,0,0,0), bc, 2, border_radius=12)
    tx = FONTE_G.render("⚔  LANÇAR ESTRATÉGIA", True, TEXT_WHITE)
    tela.blit(tx, (bc.centerx - tx.get_width()//2, bc.centery - tx.get_height()//2))

    return bm, bp, bc, input_rects

def desenhar_hud_centralizado(engine):
    # Header do Turno Atual
    header_rect = pygame.Rect(20, 20, 1240, 50)
    pygame.draw.rect(tela, PANEL_BG, header_rect, border_radius=8)
    pygame.draw.rect(tela, PANEL_BORDER, header_rect, 1, border_radius=8)

    # Botão Voltar ao Menu
    btn_menu = pygame.Rect(30, 28, 90, 34)
    mx, my = pygame.mouse.get_pos()
    hover_menu = btn_menu.collidepoint(mx, my)
    cor_menu = (60, 70, 90) if hover_menu else PANEL_BORDER
    pygame.draw.rect(tela, cor_menu, btn_menu, border_radius=6)
    pygame.draw.rect(tela, GOLD if hover_menu else PANEL_BORDER, btn_menu, 1, border_radius=6)
    txt_menu = FONTE_P.render("MENU", True, TEXT_WHITE)
    tela.blit(txt_menu, (btn_menu.centerx - txt_menu.get_width()//2, btn_menu.centery - txt_menu.get_height()//2))

    txt_j = FONTE_M.render(f"IMPÉRIO DA VEZ: {engine.nomes_jogadores[engine.turno_atual].upper()}", True, CORES_JOGADORES[engine.turno_atual])
    txt_f = FONTE_M.render(f"FASE DO EXÉRCITO: {engine.fase_atual}", True, GOLD)
    tela.blit(txt_j, (135, 33))
    tela.blit(txt_f, (520, 33))

    if engine.fase_atual == "DISTRIBUICAO":
        txt_d = FONTE_M.render(f"Reservas: {engine.exercitos_para_distribuir}", True, TEXT_WHITE)
        tela.blit(txt_d, (920, 33))

    # Painel de Missão do Jogador Atual (canto superior direito)
    missao_panel = pygame.Rect(810, 60, 450, 48)
    pygame.draw.rect(tela, PANEL_BG, missao_panel, border_radius=8)
    pygame.draw.rect(tela, GOLD, missao_panel, 1, border_radius=8)
    missao_atual = engine.missoes_jogadores.get(engine.turno_atual, {})
    descricao_missao = missao_atual.get("descricao", "")
    # Trunca para caber no painel
    if len(descricao_missao) > 42:
        descricao_missao = descricao_missao[:40] + "…"
    tela.blit(FONTE_P.render("🎯 MISSÃO:", True, GOLD), (820, 65))
    tela.blit(FONTE_P.render(descricao_missao, True, TEXT_WHITE), (820, 83))

    # Botão Concluir Fase
    btn_av = pygame.Rect(1080, 28, 160, 34)
    pygame.draw.rect(tela, CRIMSON, btn_av, border_radius=6)
    tela.blit(FONTE_P.render("CONCLUIR FASE", True, TEXT_WHITE), (1110, 37))

    # Painel Inferior de Terminal Log (Histórico de Batalhas)
    log_panel = pygame.Rect(20, 710, 780, 130)
    pygame.draw.rect(tela, PANEL_BG, log_panel, border_radius=10)
    pygame.draw.rect(tela, PANEL_BORDER, log_panel, 1, border_radius=10)
    
    y_l = 720
    for log in engine.logs:
        tela.blit(FONTE_P.render(f">> {log}", True, TEXT_MUTED), (40, y_l))
        y_l += 17

    # Painel Inferior de Cartas Armazenadas
    cards_panel = pygame.Rect(820, 710, 440, 130)
    pygame.draw.rect(tela, PANEL_BG, cards_panel, border_radius=10)
    pygame.draw.rect(tela, PANEL_BORDER, cards_panel, 1, border_radius=10)
    
    tela.blit(FONTE_P.render("RESERVA TÁTICA DE CARTAS:", True, GOLD), (840, 720))
    cartas = engine.cartas_jogadores.get(engine.turno_atual, [])
    x_c = 840
    for c in cartas[:3]: # Exibe até 3 cartas na tela de forma limpa
        nome_c = engine.territorios[c.territorio_id].nome
        pygame.draw.rect(tela, BG_DARK, pygame.Rect(x_c, 745, 110, 46), border_radius=6)
        tela.blit(FONTE_P.render(c.simbolo, True, GOLD), (x_c + 8, 750))
        tela.blit(FONTE_P.render(nome_c[:12], True, TEXT_WHITE), (x_c + 8, 770))
        x_c += 120

    btn_tr = pygame.Rect(840, 800, 400, 30)
    if len(cartas) >= 3:
        pygame.draw.rect(tela, (139, 92, 246), btn_tr, border_radius=6)
        tela.blit(FONTE_P.render("SOLICITAR REFORÇO EXTRA POR TROCA", True, TEXT_WHITE), (930, 708))

    return btn_av, btn_tr, btn_menu

def desenhar_rotas_globais(engine):
    for t in engine.territorios.values():
        for cid in t.conexoes:
            v = engine.territorios[cid]
            # Desenha cabos táticos translúcidos e estilizados
            if abs(t.x - v.x) < 400: # Evita poluição visual em loops de bordas
                pygame.draw.line(tela, (40, 50, 65), (t.x, t.y), (v.x, v.y), 2)
            else:
                # Desenha pequenos indicadores de saída do mapa para o Alaska/Vladivostok
                pygame.draw.line(tela, (150, 50, 50), (t.x, t.y), (t.x + (40 if t.x < 500 else -40), t.y), 2)

def desenhar_vitoria_missao(engine):
    """Tela de vitória quando um jogador cumpre sua missão."""
    import math
    tela.fill(BG_DARK)
    agora = pygame.time.get_ticks()
    idx = engine.vencedor_missao if engine.vencedor_missao is not None else 0
    cor_j = CORES_JOGADORES[idx]
    nome_j = engine.nomes_jogadores[idx]
    missao = engine.missoes_jogadores.get(idx, {})

    # Brilho pulsante de fundo
    pulso = 0.4 + 0.6 * abs(math.sin(agora / 600))
    brilho_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    brilho_surf.fill((*cor_j, int(18 * pulso)))
    tela.blit(brilho_surf, (0, 0))

    # Grade decorativa
    for x in range(0, LARGURA, 60):
        pygame.draw.line(tela, (22, 30, 44), (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, 60):
        pygame.draw.line(tela, (22, 30, 44), (0, y), (LARGURA, y))

    painel = pygame.Rect(160, 100, 960, 580)
    pygame.draw.rect(tela, PANEL_BG, painel, border_radius=20)
    pygame.draw.rect(tela, cor_j, painel, 4, border_radius=20)

    txt_vitoria = FONTE_TG.render("VITÓRIA!", True, GOLD)
    tela.blit(txt_vitoria, (LARGURA//2 - txt_vitoria.get_width()//2, 130))

    txt_nome = FONTE_G.render(f"{nome_j.upper()} cumpriu sua missão!", True, cor_j)
    tela.blit(txt_nome, (LARGURA//2 - txt_nome.get_width()//2, 230))

    pygame.draw.line(tela, PANEL_BORDER, (200, 295), (LARGURA - 200, 295), 1)

    txt_label = FONTE_M.render("Missão cumprida:", True, TEXT_MUTED)
    tela.blit(txt_label, (LARGURA//2 - txt_label.get_width()//2, 315))

    descricao = missao.get("descricao", "Dominação Total")
    palavras = descricao.split()
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        if len(linha_atual) + len(palavra) + 1 <= 52:
            linha_atual += (" " if linha_atual else "") + palavra
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)

    y_desc = 360
    for linha in linhas:
        txt_linha = FONTE_G.render(linha, True, GOLD)
        tela.blit(txt_linha, (LARGURA//2 - txt_linha.get_width()//2, y_desc))
        y_desc += 46

    btn = pygame.Rect(LARGURA//2 - 200, 650, 400, 56)
    mx, my = pygame.mouse.get_pos()
    hover = btn.collidepoint(mx, my)
    cor_btn = (60, 80, 110) if hover else PANEL_BORDER
    pygame.draw.rect(tela, cor_btn, btn, border_radius=12)
    pygame.draw.rect(tela, GOLD if hover else PANEL_BORDER, btn, 2, border_radius=12)
    txt_btn = FONTE_G.render("VOLTAR AO MENU", True, TEXT_WHITE)
    tela.blit(txt_btn, (btn.centerx - txt_btn.get_width()//2, btn.centery - txt_btn.get_height()//2))
    return btn

# ==========================================
# LAÇO INFINITO OPERACIONAL
# ==========================================
def main():
    engine = WarEngine()
    b1 = b2 = b3 = bv = bm = bp = bc = b_av = b_tr = b_menu = None
    btn_missao = None
    btn_vitoria = None
    input_rects_config = []
    tick = 0

    while True:
        tick += 1
        pos_mouse = pygame.mouse.get_pos()
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Alternar tela cheia / janela com F11 ──
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()

            # ── Teclado: digitar nomes na tela CONFIG ──
            if engine.estado == "CONFIG" and evento.type == pygame.KEYDOWN:
                idx = engine.input_ativo
                if idx >= 0:
                    if evento.key == pygame.K_BACKSPACE:
                        engine.input_textos[idx] = engine.input_textos[idx][:-1]
                    elif evento.key in (pygame.K_RETURN, pygame.K_TAB):
                        engine.input_ativo = (idx + 1) % engine.qtd_jogadores
                    elif evento.key == pygame.K_ESCAPE:
                        engine.input_ativo = -1
                    elif len(engine.input_textos[idx]) < 20:
                        engine.input_textos[idx] += evento.unicode

            # ── Teclado: confirmar resultado dos dados de batalha com ENTER ──
            if (engine.estado == "JOGANDO" and evento.type == pygame.KEYDOWN
                    and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                    and engine.animacao_batalha and engine.anim_aguardando_enter):
                engine.resolver_ataque_apos_animacao()

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if engine.estado == "MENU":
                    if b1 and b1.collidepoint(pos_mouse): engine.estado = "CONFIG"
                    elif b2 and b2.collidepoint(pos_mouse): engine.estado = "MANUAL"
                    elif b3 and b3.collidepoint(pos_mouse): pygame.quit(); sys.exit()
                elif engine.estado == "MANUAL":
                    if bv and bv.collidepoint(pos_mouse): engine.estado = "MENU"
                elif engine.estado == "CONFIG":
                    if bm and bm.collidepoint(pos_mouse):
                        engine.qtd_jogadores = max(2, engine.qtd_jogadores - 1)
                    elif bp and bp.collidepoint(pos_mouse):
                        engine.qtd_jogadores = min(4, engine.qtd_jogadores + 1)
                    elif bc and bc.collidepoint(pos_mouse):
                        engine.iniciar_jogo()
                    else:
                        # Verificar clique em campo de texto
                        engine.input_ativo = -1
                        for i, r in enumerate(input_rects_config):
                            if i < engine.qtd_jogadores and r.collidepoint(pos_mouse):
                                engine.input_ativo = i
                                break
                elif engine.estado == "MISSAO_REVEAL":
                    if btn_missao and btn_missao.collidepoint(pos_mouse):
                        engine.missao_reveal_jogador += 1
                        if engine.missao_reveal_jogador >= engine.qtd_jogadores:
                            engine.estado = "JOGANDO"
                            engine.missao_reveal_jogador = 0
                elif engine.estado == "VITORIA_MISSAO":
                    if btn_vitoria and btn_vitoria.collidepoint(pos_mouse):
                        engine.estado = "MENU"
                elif engine.estado == "JOGANDO" and not engine.animacao_batalha:
                    if b_menu and b_menu.collidepoint(pos_mouse): engine.estado = "MENU"
                    elif b_av and b_av.collidepoint(pos_mouse): engine.avancar_fase()
                    elif b_tr and b_tr.collidepoint(pos_mouse): engine.tentar_troca_cartas()
                    elif pos_mouse[1] > 80 and pos_mouse[1] < 700:
                        engine.tratar_clique_mapa(pos_mouse)

        # RENDERIZAÇÃO DE ESTADOS
        if engine.estado == "MENU":
            b1, b2, b3 = desenhar_menu(tick)
        elif engine.estado == "MANUAL":
            bv = desenhar_manual()
        elif engine.estado == "CONFIG":
            bm, bp, bc, input_rects_config = desenhar_config(engine)
        elif engine.estado == "MISSAO_REVEAL":
            btn_missao = desenhar_tela_missao(engine)
        elif engine.estado == "VITORIA_MISSAO":
            btn_vitoria = desenhar_vitoria_missao(engine)
        elif engine.estado == "JOGANDO":
            tela.blit(MAPA, (0, 0))
            desenhar_rotas_globais(engine)

            # Destacar alvos válidos em tempo real baseado no país ativo
            for t in engine.territorios.values():
                is_sel = (engine.territorio_selecionado == t)
                is_alvo = False
                if engine.territorio_selecionado:
                    if engine.fase_atual == "ATAQUE" and t.id in engine.territorio_selecionado.conexoes and t.dono != engine.turno_atual:
                        is_alvo = True
                    elif engine.fase_atual == "REMANEJAMENTO" and t.id in engine.territorio_selecionado.conexoes and t.dono == engine.turno_atual:
                        is_alvo = True
                t.desenhar(tela, CORES_JOGADORES[engine.turno_atual], is_sel, is_alvo)

            b_av, b_tr, b_menu = desenhar_hud_centralizado(engine)

            # ── Overlay de animação de batalha (sobrepõe tudo) ──
            if engine.animacao_batalha:
                desenhar_animacao_batalha(engine)

            # Validação de Fim de Jogo: dominação total ou missão cumprida
            primeiro = engine.territorios[1].dono
            if all(t.dono == primeiro for t in engine.territorios.values()):
                engine.vencedor_missao = primeiro
                engine.estado = "VITORIA_MISSAO"

        pygame.display.flip()
        relogio.tick(60)

if __name__ == "__main__":
    main()