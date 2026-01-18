import psycopg2
from psycopg2 import sql, pool
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import date
import logging
import os
import datetime
import time
import pandas as pd
from urllib.parse import quote
import sys

logar_query = False

def resource_path(rel_path):
    """Resolve o caminho do recurso quando empacotado com PyInstaller"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.abspath(rel_path)

load_dotenv(dotenv_path=resource_path(".env"))

DB_CONFIG = {
    'dbname':   os.getenv('DB_NAME'),
    'user':     os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host':     os.getenv('DB_HOST'),
    'port':     os.getenv('DB_PORT')
}
def get_connection():
    """Abre uma nova conexão ao banco de dados utilizando as configurações do .env."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erro ao obter conexão: {e}")
        return None
    
def get_connection_alchemy():
    """Retorna uma engine SQLAlchemy para conexão com o banco."""
    try:
        password_encoded = quote(DB_CONFIG['password'])  # Evita erro com caracteres especiais
        url = f"postgresql://{DB_CONFIG['user']}:{password_encoded}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        engine = create_engine(url, pool_size=10, max_overflow=20)
        return engine
    except Exception as e:
        print(f"❌ Erro ao criar engine SQLAlchemy: {e}")
        return None

def salvar_consulta(texto, nome_base="consulta"):
    # Define o diretório onde os arquivos serão salvos
    diretorio = os.path.join(os.getcwd(), "consultas")
    
    # Cria a pasta se ela não existir
    os.makedirs(diretorio, exist_ok=True)
    
    # Formata a data e hora para o nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define o nome do arquivo
    nome_arquivo = f"{nome_base}_{timestamp}.sql"
    
    # Caminho completo do arquivo
    caminho_arquivo = os.path.join(diretorio, nome_arquivo)
    
    # Salva o texto no arquivo
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(texto)
    
    print(f"Consulta salva em: {caminho_arquivo}")
    return caminho_arquivo

def execute_query(query, params=None):
    if logar_query:
        print(f"Executando query: {query}")
        print(f"Parâmetros: {params}")
    conn = get_connection()
    if not conn:
        raise Exception("Não foi possível conectar ao banco de dados")
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                # Se for uma query com RETURNING, retorna os resultados
                if cursor.description and 'RETURNING' in query.upper():
                    result = cursor.fetchall()
                    print(f"Resultado da query: {result}")
                    return {
                        'data': result,
                        'rowcount': cursor.rowcount
                    }
                # Para outras queries, retorna o número de linhas afetadas
                else:
                    conn.commit()
                    return cursor
    except Exception as e:
        print(f"Erro ao executar query: {e}")
        raise e
    finally:
        conn.close()

def open_query(query, params=None):
    if logar_query:
        print(f"Executando query: {query}")
        print(f"Parâmetros: {params}")
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None
    finally:
        conn.close()

def select(tabela, filtros=None):
    """
    Seleciona registros da tabela com base nos filtros fornecidos.

    :param tabela: Nome da tabela para selecionar os dados.
    :param filtros: Dicionário contendo os filtros para a cláusula WHERE.
    :return: Lista de registros que correspondem aos filtros.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Construção da cláusula WHERE dinâmica
            where_clause = sql.SQL('')
            valores = []
            if filtros:
                conditions = []
                for coluna, valor in filtros.items():
                    conditions.append(sql.SQL("{} = {}").format(sql.Identifier(coluna), sql.Placeholder()))
                    valores.append(valor)
                where_clause = sql.SQL(' WHERE ').join(conditions)

            # Montagem da query
            query = sql.SQL("SELECT * FROM {}{}").format(
                sql.Identifier(tabela),
                where_clause
            )
            cursor.execute(query, valores)
            resultados = cursor.fetchall()
            return resultados

    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return []
    finally:
        conn.close()

def update(tabela, valores_atualizar, filtros=None):
    """
    Atualiza registros na tabela com base nos filtros fornecidos.

    :param tabela: Nome da tabela onde os dados serão atualizados.
    :param valores_atualizar: Dicionário contendo as colunas e seus novos valores.
    :param filtros: Dicionário contendo os filtros para a cláusula WHERE.
    """
    try:
        conn = psycopg2.connect(dbname="seubanco", user="seuusuario", password="suasenha", host="localhost")
        with conn.cursor() as cursor:

            # Construção da cláusula SET dinâmica
            set_clause = []
            valores = []
            for coluna, valor in valores_atualizar.items():
                set_clause.append(sql.SQL("{} = {}").format(sql.Identifier(coluna), sql.Placeholder()))
                valores.append(valor)
            set_clause = sql.SQL(', ').join(set_clause)

            # Construção da cláusula WHERE dinâmica
            where_clause = sql.SQL('')
            if filtros:
                conditions = []
                for coluna, valor in filtros.items():
                    conditions.append(sql.SQL("{} = {}").format(sql.Identifier(coluna), sql.Placeholder()))
                    valores.append(valor)
                where_clause = sql.SQL(' WHERE ').join(conditions)

            # Montagem da query
            query = sql.SQL("UPDATE {} SET {}{}").format(
                sql.Identifier(tabela),
                set_clause,
                where_clause
            )

            cursor.execute(query, valores)
            conn.commit()

    except Exception as e:
        print(f"Erro ao executar a atualização: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def insert(objeto, tabela):
    """
    Insere dinamicamente os dados do dicionário 'objeto' na tabela especificada.

    :param objeto: Dicionário contendo os dados a serem inseridos.
    :param tabela: Nome da tabela onde os dados serão inseridos.
    """
    # Obtém as colunas e valores do objeto
    colunas = objeto.keys()
    valores = [objeto.get(col, None) for col in colunas]

    # Monta a query dinâmica
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(tabela),
        sql.SQL(', ').join(map(sql.Identifier, colunas)),
        sql.SQL(', ').join(sql.Placeholder() * len(valores))
    )

    # Executa a query
    execute_query(query, valores)
#endregion

# region Funções de Receita
def obtem_receitas():
    sql = f'SELECT id, nome, tempo_preparo, modo_preparo, rendimento FROM public.receita where deleted_at is null;'

    resultados = open_query(sql)
    produtos = []
    
    for resultado in resultados:
        produtos.append({
            'id': resultado[0],
            'nome': resultado[1],
            'tempo_preparo': resultado[2],
            'modo_preparo': resultado[3],
            'rendimento': resultado[4]
        })
    
    return produtos



def inserir_receita(dados):
    sql = '''
    INSERT INTO public.receita 
        (nome, rendimento, tempo_preparo, modo_preparo, data_criacao)
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    RETURNING id;
    '''
    params = (
        dados.get('nome', 'Não informado'),       # Se não existir, usa 'Não informado'
        dados.get('rendimento', 'Não informado'),
        dados.get('tempo_preparo', 'Não informado'),
        dados.get('modo_preparo', 'Não informado')
    )
    retorno = execute_query(sql, params)
    id = retorno['data'][0][0]
    return id

def atualizar_receita(dados):
    sql = '''
    UPDATE public.receita
        SET nome = %s,
            rendimento = %s,
            tempo_preparo = %s,
            modo_preparo = %s,
            data_criacao = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    '''
    params = (
        dados.get('nome', 'Não informado'),      
        dados.get('rendimento', 'Não informado'),
        dados.get('tempo_preparo', 'Não informado'),
        dados.get('modo_preparo', 'Não informado'),
        dados.get('id',0)
    )
    execute_query(sql, params)

def excluir_receita(id):
    sql = '''
    update public.receita 
    set deleted_at = CURRENT_TIMESTAMP
    where id = %s
    '''
    params = (id,)
    execute_query(sql, params)

#endregion

# region Funções Itens Receita
def listar_receita(dados):
    sql = '''
    SELECT id, receita_id, produto_id, quantidade_utilizada, observacao
      FROM public.item_receita;
     where receita_id = %s
    '''
    params = (dados.id)
    return open_query(sql, params=params)

def obtem_itens_receita(id):
    sql = '''
    select ir.id
         , p.descricao
         , ir.quantidade_utilizada
         , p.quantificacao
         , ir.observacao 
      from item_receita ir 
     inner
      join produtos p 
        on p.id  = ir.produto_id
       and p.deleted_at is null 
     where ir.deleted_at is null
       and receita_id = %s
    '''    
    param = (id,)

    dados = open_query(sql, param)

    produtos = []
    
    for resultado in dados:
        produtos.append({
            'id': resultado[0],
            'descricao': resultado[1],
            'quantidade_utilizada':  float(resultado[2]) if resultado[2] else 0,
            'quantificacao': resultado[3],
            'observacao':resultado[4], 
        })
    
    return produtos

def inserir_item_receita(dados):
    # Primeiro tenta o update
    sql_update = '''
    UPDATE public.item_receita
    SET quantidade_utilizada = %s,
        observacao = %s
    WHERE receita_id = %s AND produto_id = %s;
    '''
    params_update = (
        dados.get('quantidade_utilizada'),
        dados.get('observacao'),
        dados.get('receita_id'),
        dados.get('produto_id')
    )
    rows_affected = execute_query(sql_update, params_update).rowcount

    # Se não atualizou nada, insere
    if rows_affected == 0:
        sql_insert = '''
        INSERT INTO public.item_receita
            (receita_id, produto_id, quantidade_utilizada, observacao)
        VALUES (%s, %s, %s, %s);
        '''
        params_insert = (
            dados.get('receita_id'),
            dados.get('produto_id'),
            dados.get('quantidade_utilizada'),
            dados.get('observacao')
        )
        execute_query(sql_insert, params_insert)
    
def excluir_item_receita(id):
    sql = '''
    update public.item_receita 
    set deleted_at = CURRENT_TIMESTAMP
    where id = %s
    '''
    params = (id,)
    execute_query(sql, params)

#endregion

# region Funções Podutos

def obtem_produtos():
    sql = '''
    SELECT id
         , descricao
         , quantidade
         , quantificacao
         , valor_unitario
         , ean
      FROM public.produtos
     where deleted_at is null 
     order by id desc;
    '''
    
    resultados = open_query(sql)
    produtos = []
    
    for resultado in resultados:
        produtos.append({
            'id': resultado[0],
            'descricao': resultado[1],
            'quantidade': float(resultado[2]) if resultado[2] else 0,
            'quantificacao': resultado[3],
            'valor_unitario': float(resultado[4]) if resultado[4] else 0,
            'ean': resultado[5] if resultado[5] else ''
        })
    
    return produtos

def obtem_produtos_selecao():
    sql = '''
    SELECT id, descricao, quantidade, quantificacao, valor_unitario, deleted_at
      FROM public.produtos
     where deleted_at is null 
     order by id desc;
    '''
    
    resultados = open_query(sql)
    produtos = []
    
    for resultado in resultados:
        produtos.append({
            'id': resultado[0],
            'descricao': resultado[1],
            'quantidade': float(resultado[2]) if resultado[2] else 0,
            'quantificacao': resultado[3],
            'valor_unitario': float(resultado[4]) if resultado[4] else 0,
            'selecionado': '',
            'quantidade_utilizada': 0.0
        })
    
    return produtos

def inserir_produto(dados):
    sql = '''
    INSERT INTO public.produtos
        (descricao, quantidade, quantificacao, valor_unitario)
    VALUES
        (%s, %s, %s, %s)
    RETURNING id;
    ''' 
    params = (
        dados['descricao'],
        dados['quantidade'],
        dados['quantificacao'],
        dados['valor_unitario']
    )
    result = execute_query(sql, params)['data']
    if not result:
        raise Exception("Erro ao inserir produto")
    return result[0][0]

def atualizar_produto(id, dados):
    sql = '''
    UPDATE public.produtos 
    SET descricao = %s,
        quantidade = %s,
        quantificacao = %s,
        valor_unitario = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s AND deleted_at IS NULL
    RETURNING id
    '''
    params = (
        dados['descricao'],
        dados['quantidade'],
        dados['quantificacao'],
        dados['valor_unitario'],
        id
    )
    print(f"Executando query com parâmetros: {params}")
    result = execute_query(sql, params)['data']
    print(f"Resultado da query: {result}")
    if not result or not result[0]:
        raise Exception(f"Produto {id} não encontrado ou já foi excluído")
    return result[0][0]

def excluir_produto(id):
    sql = '''
    UPDATE public.produtos 
    SET deleted_at = CURRENT_TIMESTAMP
    WHERE id = %s
    '''
    params = (id,)
    execute_query(sql, params=params)

def criar_tabela_produtos():
    # Primeiro, verifica se a tabela existe
    check_sql = '''
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'produtos'
    );
    '''
    result = open_query(check_sql)
    tabela_existe = result[0][0]

    if not tabela_existe:
        # Se a tabela não existe, cria com a nova estrutura
        sql = '''
        CREATE TABLE public.produtos (
            id SERIAL PRIMARY KEY,
            descricao VARCHAR(255) NOT NULL,
            quantidade DECIMAL(10,3) NOT NULL,
            quantificacao VARCHAR(50) NOT NULL,
            valor_unitario DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP
        );
        '''
        execute_query(sql)
    else:
        # Se a tabela existe, renomeia as colunas
        try:
            sql_updates = [
                'ALTER TABLE public.produtos RENAME COLUMN nome TO descricao;',
                'ALTER TABLE public.produtos RENAME COLUMN unidade TO quantidade;',
                'ALTER TABLE public.produtos RENAME COLUMN preco TO valor_unitario;',
                'ALTER TABLE public.produtos ALTER COLUMN quantidade TYPE DECIMAL(10,3);'
            ]
            for sql in sql_updates:
                try:
                    execute_query(sql)
                except Exception as e:
                    # Ignora erros de coluna não existente ou já renomeada
                    if 'does not exist' not in str(e):
                        raise e
        except Exception as e:
            logging.error(f'Erro ao atualizar estrutura da tabela: {e}')
    logging.info('Tabela de produtos verificada/criada com sucesso')

# region Funções Orçamento

def obtem_orcamento():
    sql = f'SELECT id, nome, percentual FROM public.orcamento where deleted_at is null ;'
    resultados = open_query(sql)
    orcamentos = []
    
    for resultado in resultados:
        orcamentos.append({
            'id': resultado[0],
            'nome': resultado[1],
            'percentual': float(resultado[2]) if resultado[2] else 0.0,
        })
    
    return orcamentos

def inserir_orcamento(dados):
    sql = '''
    INSERT 
      INTO public.orcamento
         ( nome, percentual, created_at)
    VALUES
         ( %s, %s, CURRENT_TIMESTAMP)
    RETURNING id;    
    '''
    params = (dados.get('nome'), dados.get('percentual',0))
    orcamento = execute_query(sql, params)['data']
    return orcamento[0][0]

def update_orcamento(dados):
    sql = '''
    UPDATE public.orcamento
       SET nome = %s
         , percentual = %s
         , created_at = CURRENT_TIMESTAMP
     where id = %s
    RETURNING id;    
    '''
    params = (dados.get('nome'), dados.get('percentual',0) , dados.get('id'))
    orcamento = execute_query(sql, params)
    return orcamento['data'][0][0]

def excluir_orcamento(id):
    sql = '''
    update public.orcamento 
    set deleted_at = CURRENT_TIMESTAMP
    where id = %s
    '''
    params = (id,)
    execute_query(sql, params)

#endregion

def obtem_itens_orcamento(orcamento_id):
    sql = '''
    select io.id
         , r.nome
         , io.quantidade  
      from item_orcamento io
     inner 
      join orcamento o 
        on o.id = io.orcamento_id
       and o.deleted_at is null
     inner
      join receita r 
        on r.id = io.receita_id	
       and r.deleted_at is null  
     where io.deleted_at is null 
       and o.id = %s -- param
    '''
    param = (orcamento_id,)
    resultados = open_query(sql, param)
    itens = []

    for resultado in resultados:
            itens.append({
                'id': resultado[0],
                'nome': resultado[1],
                'quantidade': float(resultado[2]) if resultado[2] else 0.0,
            })
        
    return itens

def inserir_item_orcamento(dados):
    # Primeiro tentamos atualizar se existir o par (receita_id, produto_id)
    sql_update = '''
    UPDATE public.item_orcamento
       SET orcamento_id = %s,
           quantidade = %s
     WHERE deleted_at is null 
       and receita_id = %s
       AND orcamento_id = %s
    RETURNING id;
    '''
    
    params_update = (
        dados.get('orcamento_id'),
        dados.get('quantidade'),
        dados.get('receita_id'),
        dados.get('orcamento_id')
    )
    
    # Executa o UPDATE e verifica se alguma linha foi afetada
    result = execute_query(sql_update, params_update)
    
    # Se o UPDATE afetou alguma linha (rowcount > 0), retorna o ID
    if result['rowcount'] > 0:
        return result['data'][0][0]  # Retorna o ID do registro atualizado
    
    # Se não houve UPDATE, faz o INSERT
    sql_insert = '''
    INSERT INTO public.item_orcamento
        (orcamento_id, receita_id, quantidade)
    VALUES
        (%s, %s, %s)
    RETURNING id;
    '''
    
    params_insert = (
        dados.get('orcamento_id'),
        dados.get('receita_id'),
        dados.get('quantidade')
    )
    
    result_insert = execute_query(sql_insert, params_insert)
    return result_insert['data'][0][0]  # Retorna o ID do novo registro

def excluir_item_orcamento(id):
    sql = '''
    update public.item_orcamento 
    set deleted_at = CURRENT_TIMESTAMP
    where id = %s
    '''
    params = (id,)
    execute_query(sql, params)

def obtem_totais_orcamento(id):
    sql = '''
        WITH ingredientes_bolo AS (
             SELECT ir.receita_id
                  , ir.produto_id
                  , ir.quantidade_utilizada
                  , p.descricao, p.quantidade AS quantidade_produto
                  , p.quantificacao, p.valor_unitario
                  , io.quantidade
                  , ((ir.quantidade_utilizada / p.quantidade) * p.valor_unitario) * io.quantidade AS custo_ingrediente
                  , (((ir.quantidade_utilizada / p.quantidade) * p.valor_unitario) * (1 + (o.percentual / 100.0))) * io.quantidade AS valor_com_acrescimo
              FROM orcamento o 
             INNER JOIN item_orcamento io 
                ON io.deleted_at IS NULL
               AND io.orcamento_id = o.id 
             INNER JOIN receita r
                ON r.deleted_at IS NULL
               AND r.id = io.receita_id
             INNER JOIN item_receita ir 
                ON ir.deleted_at IS NULL 
               AND ir.receita_id = r.id
             INNER JOIN produtos p 
                ON p.deleted_at IS NULL
               AND p.id = ir.produto_id
              WHERE o.deleted_at IS NULL 
               AND o.id = %s
        )

        SELECT 
            r.nome AS tipo,
            ROUND(SUM(ib.custo_ingrediente), 2) AS valor,
            ROUND(SUM(ib.valor_com_acrescimo), 2) AS valor_acrescimo,
            quantidade 
        FROM ingredientes_bolo ib
        INNER JOIN receita r ON ib.receita_id = r.id
        GROUP BY r.nome, receita_id, quantidade
    '''

    params = (id,)
    resultados = open_query(sql, params)
    orcamentos = []
    total_custo = 0.0
    total_valor_acrescimo = 0.0
    
    for resultado in resultados:
        custo = float(resultado[1]) if resultado[1] else 0.0
        valor_acrescimo = float(resultado[2]) if resultado[2] else 0.0
        
        item = {
            'tipo': resultado[0],
            'custo': custo,
            'adicional': valor_acrescimo,
            'quantidade': float(resultado[3]) if resultado[3] else 0.0
        }
        
        # Acumula totais apenas para itens que não sejam o total geral
        if resultado[0] != 'TOTAL DO ORCAMENTO':
            total_custo += custo
            total_valor_acrescimo += valor_acrescimo
            
        orcamentos.append(item)
    
    # Retorna um dicionário com os itens e os totais separadamente
    return {
        'itens': orcamentos,
        'totais': {
            'total_custo': round(total_custo, 2),
            'total_valor_final': round(total_valor_acrescimo, 2),
            'diferenca_acrescimo': round(total_valor_acrescimo - total_custo, 2)
        }
    }

def obtem_itens_orcamentos_receita(orcamento_id):
    if not orcamento_id:
        orcamento_id = 'o.id'
    sql = '''
    select r.id
         , r.nome
         , r.rendimento 
         , CASE 
           WHEN io.quantidade IS NULL THEN 0.0 
           ELSE io.quantidade 
            END AS quantidade
         , io.id orcamento_id
      from receita r
     inner 
      join orcamento o 
        on o.id = %s 
     inner
      join item_orcamento io
        on io.deleted_at is null 
       and io.receita_id = r.id
       and io.orcamento_id = o.id
       and o.deleted_at is null 
     where r.deleted_at is null
       and io.deleted_at is null 
     order by r.id asc 
    '''
    param = (orcamento_id,)
    resultados = open_query(sql, param)
    itens = []

    for resultado in resultados:
            itens.append({
                'id': resultado[0],
                'nome': resultado[1],
                'rendimento': resultado[2],
                'quantidade': float(resultado[3]) if resultado[3] else 0.0,
                'orcamento_id':int(resultado[4]) if resultado[4] else 0, 
                'selecionado': '',
            })
    return itens


if __name__ == '__main__':
    criar_tabela_produtos()

