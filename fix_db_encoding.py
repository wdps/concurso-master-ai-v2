import sqlite3
import traceback
from datetime import datetime

DB_NAME = 'concurso.db'

NOVOS_TEMAS_REDACAO = [
    ("A importância da saúde mental no ambiente de trabalho e o papel das empresas.", "Fácil"),
    ("Os desafios da regulamentação da Inteligência Artificial no Brasil.", "Difícil"),
    ("O impacto das Fake News na democracia brasileira e na saúde pública.", "Médio"),
    ("A crise hídrica e os desafios da gestão de recursos naturais no século XXI.", "Difícil"),
    ("A relevância do Saneamento Básico para a qualidade de vida e o desenvolvimento social.", "Fácil"),
    ("O dilema entre liberdade de expressão e os limites da Cultura do Cancelamento.", "Médio"),
    ("A desigualdade social no acesso à educação de qualidade no Brasil.", "Fácil"),
    ("O aumento da violência nas escolas: causas e propostas de intervenção.", "Difícil"),
    ("Os impactos da Crise Migratória global e o acolhimento de refugiados no país.", "Médio"),
    ("O papel da tecnologia na transformação da segurança pública e o combate ao crime cibernético.", "Difícil"),
    ("Sustentabilidade urbana: desafios para uma mobilidade eficiente nas grandes metrópoles.", "Médio"),
    ("A necessidade de reforma do sistema previdenciário brasileiro e seus reflexos sociais.", "Difícil"),
    ("A influência das redes sociais na formação da opinião pública e o risco da polarização.", "Fácil"),
    ("Os desafios da implementação de políticas de diversidade e inclusão nas instituições públicas.", "Médio"),
    ("O envelhecimento populacional e as demandas por políticas de saúde e assistência ao idoso.", "Fácil"),
    ("A importância da valorização do serviço público para a eficiência do Estado.", "Fácil"),
    ("O combate à corrupção e a transparência na gestão dos recursos públicos.", "Médio"),
    ("A precarização do trabalho na era digital: Uberização e direitos trabalhistas.", "Difícil"),
    ("O combate ao racismo estrutural e a promoção da igualdade racial no Brasil.", "Difícil"),
    ("O acesso à cultura como direito fundamental e ferramenta de transformação social.", "Fácil"),
    ("O desafio da segurança alimentar em um cenário de mudanças climáticas.", "Médio"),
    ("A importância da educação financeira para a estabilidade econômica individual.", "Fácil"),
    ("O uso de agrotóxicos e o debate sobre a saúde do consumidor e o meio ambiente.", "Médio"),
    ("A necessidade de modernização da legislação trabalhista brasileira.", "Difícil"),
    ("O impacto das pandemias na estrutura social e econômica do Brasil.", "Médio"),
    ("Os desafios da mulher no mercado de trabalho e a busca pela igualdade salarial.", "Fácil"),
    ("A crise no sistema carcerário brasileiro: problemas e soluções.", "Difícil"),
    ("A regulamentação do teletrabalho e os desafios para a fiscalização de jornada.", "Médio"),
    ("O papel das micro e pequenas empresas no desenvolvimento econômico local.", "Fácil"),
    ("O desafio de conciliar crescimento econômico e preservação ambiental na Amazônia.", "Difícil"),
    ("A reforma política e a crise de representatividade no Brasil.", "Médio"),
    ("O uso de dados pessoais e o debate sobre privacidade na era da LGPD.", "Fácil"),
    ("A importância da primeira infância e os investimentos em creches e pré-escolas.", "Fácil"),
    ("A importância do voto e a participação cívica na construção da democracia.", "Fácil"),
    ("O crescimento da população em situação de rua nas grandes cidades.", "Médio"),
    ("Os desafios do financiamento da saúde pública e a importância do SUS.", "Médio"),
    ("A regulamentação dos jogos de azar (apostas) no Brasil: prós e contras.", "Difícil"),
    ("O papel das Forças Armadas na garantia da soberania e da lei e ordem.", "Difícil"),
    ("A importância da diplomacia brasileira na integração latino-americana.", "Fácil"),
    ("A violência contra a mulher e as políticas de proteção (Lei Maria da Penha).", "Médio"),
    ("O uso da biotecnologia na agricultura e o debate ético.", "Difícil"),
    ("A inclusão digital e o combate à exclusão social na era da conectividade.", "Fácil"),
    ("Os desafios da segurança no trânsito e a redução de acidentes.", "Médio"),
    ("A crise energética e a busca por fontes renováveis no Brasil.", "Médio"),
    ("A importância da pesquisa científica para o desenvolvimento nacional.", "Fácil"),
    ("A questão indígena: demarcação de terras e o respeito à diversidade cultural.", "Difícil"),
    ("O papel da educação a distância (EAD) no ensino superior brasileiro.", "Fácil"),
    ("Os impactos das mudanças climáticas na agricultura brasileira.", "Médio"),
    ("A influência de grupos de pressão (lobbies) nas decisões do Congresso Nacional.", "Difícil"),
    ("O desafio de manter a estabilidade econômica frente à inflação.", "Médio"),
    ("A importância da vacinação para a saúde coletiva e a luta contra o negacionismo.", "Fácil"),
    ("O mercado de criptomoedas e a necessidade de regulamentação financeira.", "Difícil"),
    ("A poluição dos oceanos e as medidas para a preservação da vida marinha.", "Médio"),
    ("A importância da leitura na formação crítica do cidadão.", "Fácil"),
    ("O assédio moral e sexual no serviço público: prevenção e combate.", "Médio"),
    ("A tecnologia 5G e os desafios de infraestrutura no Brasil.", "Difícil"),
    ("A gestão de resíduos sólidos e o desafio do lixo nas grandes cidades.", "Médio"),
    ("A necessidade de investimentos em ferrovias e a matriz de transportes brasileira.", "Fácil"),
    ("A educação inclusiva para pessoas com deficiência (PcD).", "Fácil"),
    ("O papel do terceiro setor (ONGs) na complementação dos serviços públicos.", "Médio"),
    ("O desmatamento na Mata Atlântica e as ações de recuperação ambiental.", "Difícil"),
    ("A cultura do 'empreendedorismo' e o mito da meritocracia.", "Difícil"),
    ("A importância do jornalismo profissional no combate à desinformação.", "Fácil"),
    ("A reforma tributária e a simplificação do sistema de impostos.", "Médio"),
    ("O impacto da tecnologia na longevidade e na qualidade de vida.", "Fácil"),
    ("O desafio de reduzir o custo Brasil para aumentar a competitividade.", "Médio"),
    ("A evasão escolar no ensino médio e as propostas para permanência.", "Fácil"),
    ("O futuro do trabalho e a automação de tarefas repetitivas.", "Difícil"),
    ("O acesso à justiça e a morosidade do sistema judicial.", "Difícil"),
    ("A importância da proteção à fauna e da luta contra o tráfico de animais.", "Fácil"),
    ("O esporte como ferramenta de inclusão social e desenvolvimento humano.", "Fácil"),
    ("Os riscos da dependência tecnológica na educação e no dia a dia.", "Médio"),
    ("O papel das hidrelétricas na matriz energética e os impactos ambientais.", "Médio"),
    ("A qualidade dos gastos públicos e o combate ao desperdício de recursos.", "Fácil"),
    ("A judicialização da política e os limites de atuação do Poder Judiciário.", "Difícil"),
    ("O desafio da segurança dos dados bancários e o Pix.", "Fácil"),
    ("A política de cotas raciais e sociais nas universidades e concursos.", "Médio"),
    ("A regulação da mineração em áreas de preservação ambiental.", "Difícil"),
    ("A importância da transparência na divulgação de salários no setor público.", "Fácil"),
    ("O papel da mulher na ciência e o combate ao machismo acadêmico.", "Fácil"),
    ("O futuro da União Europeia e as relações com o Mercosul.", "Difícil")
]

def run_db_migration():
    print(f"--- Iniciando varredura e correção em {DB_NAME} ---")
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cursor = conn.cursor()

        # 1. VERIFICA E CORRIGE A ESTRUTURA DA TABELA
        print("🔍 Verificando estrutura da tabela 'temas_redacao'...")
        cursor.execute("PRAGMA table_info(temas_redacao)")
        colunas = cursor.fetchall()
        colunas_nomes = [coluna[1] for coluna in colunas]
        
        # Se a tabela não existe ou não tem as colunas esperadas, recria
        if not colunas_nomes or 'titulo' not in colunas_nomes:
            print("🔄 Recriando tabela 'temas_redacao' com estrutura correta...")
            cursor.execute("DROP TABLE IF EXISTS temas_redacao")
            cursor.execute('''
                CREATE TABLE temas_redacao (
                    id TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    dificuldade TEXT
                )
            ''')
            print("✅ Tabela 'temas_redacao' criada com sucesso.")
        else:
            print("✅ Estrutura da tabela verificada.")

        # 2. EXCLUSÃO TOTAL dos temas antigos
        print("🚨 EXCLUINDO TODOS OS TEMAS DE REDAÇÃO ANTIGOS...")
        cursor.execute("DELETE FROM temas_redacao")
        print("✅ Exclusão da tabela 'temas_redacao' concluída.")
        
        # 3. INSERÇÃO DOS 80 NOVOS TEMAS (com estrutura correta)
        print(f"🚀 INSERINDO {len(NOVOS_TEMAS_REDACAO)} NOVOS TEMAS DE REDAÇÃO...")
        
        for titulo, dificuldade in NOVOS_TEMAS_REDACAO:
            cursor.execute(
                "INSERT INTO temas_redacao (id, titulo, dificuldade) VALUES (?, ?, ?)", 
                (f'tema_{datetime.now().strftime("%Y%m%d%H%M%S")}_{hash(titulo) % 10000}', titulo, dificuldade)
            )

        print(f"✅ Inserção de {len(NOVOS_TEMAS_REDACAO)} temas concluída.")
        
        # 4. Commit e fechar
        conn.commit()
        print("💾 Todas as alterações salvas no banco de dados com sucesso.")

    except sqlite3.Error as e:
        print(f"❌ ERRO SQLITE: {e}")
        print("A migração falhou. Verifique se o arquivo 'concurso.db' existe e não está em uso.")
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
        print("--- Varredura e Inserção concluídas ---")

if __name__ == '__main__':
    run_db_migration()
