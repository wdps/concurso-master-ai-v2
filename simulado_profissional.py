"""
SISTEMA DE SIMULADO PARA CONCURSOS - ARCHITECTURE v2.0
Arquitetura modular e escalável para plataforma de e-learning
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import sqlite3
import random
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class Dificuldade(Enum):
    FACIL = "Fácil"
    MEDIO = "Médio"
    DIFICIL = "Difícil"
    ESPECIALISTA = "Especialista"


class Materia(Enum):
    DIREITO_ADMINISTRATIVO = "Direito Administrativo"
    DIREITO_CONSTITUCIONAL = "Direito Constitucional"
    PORTUGUES = "Língua Portuguesa"
    RACIOCINIO_LOGICO = "Raciocínio Lógico"
    INFORMATICA = "Informática"
    MATEMATICA = "Matemática"
    ATUALIDADES = "Atualidades"


@dataclass
class Questao:
    """Classe que representa uma questão do simulado"""
    id: int
    enunciado: str
    materia: Materia
    alternativa_a: str
    alternativa_b: str
    alternativa_c: str
    alternativa_d: str
    alternativa_e: Optional[str] = None
    resposta_correta: str
    dificuldade: Dificuldade
    justificativa: Optional[str] = None
    tempo_estimado: int = 60  # segundos
    ano_prova: Optional[str] = None
    banca_organizadora: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'enunciado': self.enunciado,
            'materia': self.materia.value,
            'alternativa_a': self.alternativa_a,
            'alternativa_b': self.alternativa_b,
            'alternativa_c': self.alternativa_c,
            'alternativa_d': self.alternativa_d,
            'alternativa_e': self.alternativa_e,
            'resposta_correta': self.resposta_correta,
            'dificuldade': self.dificuldade.value,
            'justificativa': self.justificativa,
            'tempo_estimado': self.tempo_estimado,
            'ano_prova': self.ano_prova,
            'banca_organizadora': self.banca_organizadora
        }


@dataclass
class RespostaUsuario:
    """Classe para gerenciar respostas do usuário"""
    questao_id: int
    alternativa_escolhida: str
    tempo_gasto: int
    acertou: bool
    timestamp: datetime


class BancoQuestoes:
    """Gerenciador profissional do banco de questões"""
    
    def __init__(self, db_path: str = "concurso.db"):
        self.db_path = db_path
        self._criar_tabelas()
    
    def _criar_tabelas(self) -> None:
        """Cria estrutura otimizada do banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela principal de questões
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questões (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disciplina TEXT NOT NULL,
                    assunto TEXT,
                    enunciado TEXT NOT NULL,
                    alt_a TEXT NOT NULL,
                    alt_b TEXT NOT NULL,
                    alt_c TEXT NOT NULL,
                    alt_d TEXT NOT NULL,
                    alt_e TEXT,
                    gabarito TEXT NOT NULL,
                    justificativa TEXT,
                    dificuldade TEXT DEFAULT 'Médio',
                    tempo_estimado INTEGER DEFAULT 60,
                    ano_prova TEXT,
                    banca_organizadora TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de estatísticas de desempenho
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estatisticas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    materia TEXT,
                    total_questoes INTEGER,
                    acertos INTEGER,
                    erros INTEGER,
                    tempo_medio REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def carregar_questoes(self, 
                         materias: Optional[List[Materia]] = None,
                         dificuldade: Optional[Dificuldade] = None,
                         limite: int = 100) -> List[Questao]:
        """Carrega questões com filtros avançados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM questões WHERE 1=1"
                params = []
                
                if materias:
                    materias_str = [m.value for m in materias]
                    placeholders = ','.join(['?'] * len(materias_str))
                    query += f" AND disciplina IN ({placeholders})"
                    params.extend(materias_str)
                
                if dificuldade:
                    query += " AND dificuldade = ?"
                    params.append(dificuldade.value)
                
                query += " ORDER BY RANDOM() LIMIT ?"
                params.append(limite)
                
                cursor.execute(query, params)
                resultados = cursor.fetchall()
                
                questoes = []
                for row in resultados:
                    questao = Questao(
                        id=row['id'],
                        enunciado=row['enunciado'],
                        materia=Materia(row['disciplina']),
                        alternativa_a=row['alt_a'],
                        alternativa_b=row['alt_b'],
                        alternativa_c=row['alt_c'],
                        alternativa_d=row['alt_d'],
                        alternativa_e=row.get('alt_e'),
                        resposta_correta=row['gabarito'],
                        dificuldade=Dificuldade(row.get('dificuldade', 'Médio')),
                        justificativa=row.get('justificativa'),
                        tempo_estimado=row.get('tempo_estimado', 60),
                        ano_prova=row.get('ano_prova'),
                        banca_organizadora=row.get('banca_organizadora')
                    )
                    questoes.append(questao)
                
                return questoes
                
        except Exception as e:
            raise Exception(f"Erro ao carregar questões: {e}")
    
    def obter_estatisticas_materia(self, materia: Materia) -> Dict:
        """Obtém estatísticas detalhadas por matéria"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN dificuldade = 'Fácil' THEN 1 ELSE 0 END) as faceis,
                    SUM(CASE WHEN dificuldade = 'Médio' THEN 1 ELSE 0 END) as medias,
                    SUM(CASE WHEN dificuldade = 'Difícil' THEN 1 ELSE 0 END) as dificeis
                FROM questões 
                WHERE disciplina = ?
            ''', (materia.value,))
            
            resultado = cursor.fetchone()
            
            return {
                'total': resultado[0],
                'faceis': resultado[1],
                'medias': resultado[2],
                'dificeis': resultado[3]
            }


class Cronometro:
    """Gerenciador avançado de tempo para simulados"""
    
    def __init__(self, tempo_total: timedelta):
        self.tempo_total = tempo_total
        self.inicio: Optional[datetime] = None
        self.tempo_restante: timedelta = tempo_total
    
    def iniciar(self) -> None:
        """Inicia o cronômetro"""
        self.inicio = datetime.now()
    
    def tempo_decorrido(self) -> timedelta:
        """Retorna tempo decorrido"""
        if not self.inicio:
            return timedelta(0)
        return datetime.now() - self.inicio
    
    def tempo_restante_formatado(self) -> str:
        """Retorna tempo restante formatado"""
        restante = self.tempo_total - self.tempo_decorrido()
        horas = restante.seconds // 3600
        minutos = (restante.seconds % 3600) // 60
        segundos = restante.seconds % 60
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    
    def tempo_esgotado(self) -> bool:
        """Verifica se o tempo acabou"""
        return self.tempo_decorrido() >= self.tempo_total


class RelatorioDesempenho:
    """Gerador de relatórios detalhados de desempenho"""
    
    def __init__(self, respostas: List[RespostaUsuario], banco_questoes: BancoQuestoes):
        self.respostas = respostas
        self.banco_questoes = banco_questoes
    
    def gerar_relatorio_completo(self) -> Dict:
        """Gera relatório completo de desempenho"""
        total_questoes = len(self.respostas)
        acertos = sum(1 for r in self.respostas if r.acertou)
        percentual_geral = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        
        # Estatísticas por matéria
        estatisticas_materia = {}
        for resposta in self.respostas:
            questao = self._obter_questao_por_id(resposta.questao_id)
            if questao:
                materia = questao.materia.value
                if materia not in estatisticas_materia:
                    estatisticas_materia[materia] = {'total': 0, 'acertos': 0}
                
                estatisticas_materia[materia]['total'] += 1
                if resposta.acertou:
                    estatisticas_materia[materia]['acertos'] += 1
        
        # Calcular percentuais por matéria
        for materia, stats in estatisticas_materia.items():
            stats['percentual'] = (stats['acertos'] / stats['total']) * 100
        
        # Tempo total gasto
        tempo_total = sum(r.tempo_gasto for r in self.respostas)
        
        return {
            'geral': {
                'total_questoes': total_questoes,
                'acertos': acertos,
                'erros': total_questoes - acertos,
                'percentual_geral': round(percentual_geral, 2),
                'tempo_total_minutos': round(tempo_total / 60, 2)
            },
            'por_materia': estatisticas_materia,
            'recomendacoes': self._gerar_recomendacoes(estatisticas_materia)
        }
    
    def _obter_questao_por_id(self, questao_id: int) -> Optional[Questao]:
        """Obtém questão pelo ID"""
        try:
            with sqlite3.connect(self.banco_questoes.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM questões WHERE id = ?", (questao_id,))
                row = cursor.fetchone()
                
                if row:
                    return Questao(
                        id=row['id'],
                        enunciado=row['enunciado'],
                        materia=Materia(row['disciplina']),
                        alternativa_a=row['alt_a'],
                        alternativa_b=row['alt_b'],
                        alternativa_c=row['alt_c'],
                        alternativa_d=row['alt_d'],
                        resposta_correta=row['gabarito'],
                        dificuldade=Dificuldade(row.get('dificuldade', 'Médio')),
                        justificativa=row.get('justificativa')
                    )
                return None
        except:
            return None
    
    def _gerar_recomendacoes(self, estatisticas_materia: Dict) -> List[str]:
        """Gera recomendações de estudo baseadas no desempenho"""
        recomendacoes = []
        
        for materia, stats in estatisticas_materia.items():
            if stats['percentual'] < 70:
                recomendacoes.append(
                    f"📚 Focar em {materia} (acertos: {stats['percentual']}%)"
                )
            elif stats['percentual'] > 90:
                recomendacoes.append(
                    f"✅ Excelente em {materia}! Mantenha o foco para revisão"
                )
        
        if not recomendacoes:
            recomendacoes.append("🎯 Desempenho equilibrado! Continue com estudos diversificados")
        
        return recomendacoes


class Simulado:
    """Classe principal que gerencia a execução do simulado"""
    
    def __init__(self, 
                 banco_questoes: BancoQuestoes,
                 tempo_total: timedelta = timedelta(hours=3),
                 questoes_por_materia: Optional[Dict[Materia, int]] = None):
        
        self.banco_questoes = banco_questoes
        self.cronometro = Cronometro(tempo_total)
        self.questoes: List[Questao] = []
        self.respostas: List[RespostaUsuario] = []
        self.questao_atual_index = 0
        self.finalizado = False
        
        # Configurar distribuição de questões
        self.questoes_por_materia = questoes_por_materia or {
            Materia.DIREITO_ADMINISTRATIVO: 20,
            Materia.DIREITO_CONSTITUCIONAL: 15,
            Materia.PORTUGUES: 15,
            Materia.RACIOCINIO_LOGICO: 10,
            Materia.INFORMATICA: 10,
            Materia.MATEMATICA: 10,
            Materia.ATUALIDADES: 10
        }
    
    def preparar_simulado(self) -> None:
        """Prepara o simulado carregando e embaralhando questões"""
        print("🎯 PREPARANDO SIMULADO...")
        
        todas_questoes = []
        for materia, quantidade in self.questoes_por_materia.items():
            print(f"📚 Carregando {quantidade} questões de {materia.value}...")
            questoes_materia = self.banco_questoes.carregar_questoes(
                materias=[materia], 
                limite=quantidade
            )
            todas_questoes.extend(questoes_materia)
        
        # Embaralhar questões
        random.shuffle(todas_questoes)
        self.questoes = todas_questoes
        
        print(f"✅ Simulado preparado com {len(self.questoes)} questões")
    
    def iniciar(self) -> None:
        """Inicia a execução do simulado"""
        if not self.questoes:
            raise Exception("Simulado não foi preparado. Execute preparar_simulado() primeiro.")
        
        self.cronometro.iniciar()
        print(f"\n⏰ SIMULADO INICIADO! Tempo total: {self.cronometro.tempo_total}")
        print("Pressione Ctrl+C para finalizar antecipadamente\n")
        
        try:
            while (self.questao_atual_index < len(self.questoes) and 
                   not self.cronometro.tempo_esgotado() and 
                   not self.finalizado):
                
                self._apresentar_questao_atual()
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Simulado interrompido pelo usuário")
            self._finalizar_simulado(interrompido=True)
        
        if self.cronometro.tempo_esgotado():
            print("\n⏰ TEMPO ESGOTADO! Finalizando simulado...")
            self._finalizar_simulado()
    
    def _apresentar_questao_atual(self) -> None:
        """Apresenta a questão atual e gerencia a resposta"""
        questao = self.questoes[self.questao_atual_index]
        inicio_tempo = time.time()
        
        print(f"\n{'='*60}")
        print(f"📝 QUESTÃO {self.questao_atual_index + 1}/{len(self.questoes)}")
        print(f"⏰ Tempo restante: {self.cronometro.tempo_restante_formatado()}")
        print(f"📚 Matéria: {questao.materia.value}")
        print(f"🎯 Dificuldade: {questao.dificuldade.value}")
        print(f"{'='*60}")
        print(f"\n{questao.enunciado}\n")
        
        # Apresentar alternativas
        alternativas = [
            ('A', questao.alternativa_a),
            ('B', questao.alternativa_b),
            ('C', questao.alternativa_c),
            ('D', questao.alternativa_d)
        ]
        
        if questao.alternativa_e:
            alternativas.append(('E', questao.alternativa_e))
        
        for letra, texto in alternativas:
            print(f"{letra}) {texto}")
        
        # Obter resposta do usuário
        resposta = self._obter_resposta_valida(alternativas)
        tempo_gasto = int(time.time() - inicio_tempo)
        
        # Verificar resposta
        acertou = resposta.upper() == questao.resposta_correta.upper()
        
        # Armazenar resposta
        resposta_usuario = RespostaUsuario(
            questao_id=questao.id,
            alternativa_escolhida=resposta,
            tempo_gasto=tempo_gasto,
            acertou=acertou,
            timestamp=datetime.now()
        )
        self.respostas.append(resposta_usuario)
        
        # Feedback imediato
        if acertou:
            print("✅ RESPOSTA CORRETA!")
        else:
            print(f"❌ RESPOSTA INCORRETA! A correta era: {questao.resposta_correta}")
        
        print(f"⏱️ Tempo gasto: {tempo_gasto} segundos")
        
        self.questao_atual_index += 1
    
    def _obter_resposta_valida(self, alternativas: List[Tuple[str, str]]) -> str:
        """Obtém uma resposta válida do usuário"""
        opcoes_validas = [letra for letra, _ in alternativas]
        
        while True:
            try:
                resposta = input(f"\nSua resposta ({'/'.join(opcoes_validas)}): ").strip().upper()
                
                if resposta in opcoes_validas:
                    return resposta
                else:
                    print(f"❌ Opção inválida. Use {', '.join(opcoes_validas)}")
                    
            except EOFError:
                print("\n\nSimulado finalizado.")
                self.finalizado = True
                return ""
            except KeyboardInterrupt:
                raise
    
    def _finalizar_simulado(self, interrompido: bool = False) -> None:
        """Finaliza o simulado e gera relatório"""
        self.finalizado = True
        
        if not interrompido and self.respostas:
            relatorio = RelatorioDesempenho(self.respostas, self.banco_questoes)
            dados_relatorio = relatorio.gerar_relatorio_completo()
            
            self._apresentar_relatorio(dados_relatorio)
            self._oferecer_gabarito_comentado()
    
    def _apresentar_relatorio(self, relatorio: Dict) -> None:
        """Apresenta o relatório de desempenho"""
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO DE DESEMPENHO")
        print(f"{'='*60}")
        
        geral = relatorio['geral']
        print(f"\n🎯 DESEMPENHO GERAL:")
        print(f"   • Questões respondidas: {geral['total_questoes']}")
        print(f"   • Acertos: {geral['acertos']}")
        print(f"   • Erros: {geral['erros']}")
        print(f"   • Percentual de acerto: {geral['percentual_geral']}%")
        print(f"   • Tempo total: {geral['tempo_total_minutos']} minutos")
        
        print(f"\n📚 DESEMPENHO POR MATÉRIA:")
        for materia, stats in relatorio['por_materia'].items():
            print(f"   • {materia}: {stats['acertos']}/{stats['total']} "
                  f"({stats['percentual']}%)")
        
        print(f"\n💡 RECOMENDAÇÕES:")
        for recomendacao in relatorio['recomendacoes']:
            print(f"   • {recomendacao}")
    
    def _oferecer_gabarito_comentado(self) -> None:
        """Oferece revisão do gabarito comentado"""
        try:
            opcao = input("\n📖 Deseja revisar o gabarito comentado? (S/N): ").strip().upper()
            
            if opcao == 'S':
                print(f"\n{'='*60}")
                print("📖 GABARITO COMENTADO")
                print(f"{'='*60}")
                
                for i, resposta in enumerate(self.respostas):
                    questao = self._obter_questao_por_id(resposta.questao_id)
                    if questao:
                        print(f"\n{i+1}. {questao.enunciado[:100]}...")
                        print(f"   Sua resposta: {resposta.alternativa_escolhida}")
                        print(f"   Resposta correta: {questao.resposta_correta}")
                        print(f"   Resultado: {'✅ ACERTOU' if resposta.acertou else '❌ ERROU'}")
                        
                        if questao.justificativa:
                            print(f"   💡 Justificativa: {questao.justificativa}")
                        
                        print("   " + "-"*50)
        
        except (KeyboardInterrupt, EOFError):
            print("\nRetornando ao menu principal...")


# 🎯 EXEMPLO DE USO PROFISSIONAL
def main():
    """Função principal com interface profissional"""
    try:
        print("🎓 SISTEMA DE SIMULADO PARA CONCURSOS - v2.0")
        print("=" * 50)
        
        # Inicializar banco de questões
        banco = BancoQuestoes("concurso.db")
        
        # Configurar simulado
        tempo_simulado = timedelta(hours=3)  # 3 horas
        distribuicao_questoes = {
            Materia.DIREITO_ADMINISTRATIVO: 10,
            Materia.DIREITO_CONSTITUCIONAL: 8,
            Materia.PORTUGUES: 8,
            Materia.RACIOCINIO_LOGICO: 5,
            Materia.INFORMATICA: 5,
            Materia.MATEMATICA: 5,
            Materia.ATUALIDADES: 5
        }
        
        simulado = Simulado(
            banco_questoes=banco,
            tempo_total=tempo_simulado,
            questoes_por_materia=distribuicao_questoes
        )
        
        # Preparar simulado
        simulado.preparar_simulado()
        
        # Iniciar simulado
        input("\nPressione ENTER para iniciar o simulado...")
        simulado.iniciar()
        
    except Exception as e:
        print(f"❌ Erro no sistema: {e}")
    finally:
        print("\n🎉 Obrigado por usar o Sistema de Simulado para Concursos!")


if __name__ == "__main__":
    main()
