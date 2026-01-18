from flask import jsonify, request, render_template
from . import pg  
import pandas as pd

def setup_routes(app):
    @app.route('/')
    def index():
        return render_template("index.html")  # arquivo templates/index.html

    @app.route('/produtos', methods=['GET'])
    def listar_produto():
        try:
            produtos = pg.obtem_produtos()

            return jsonify({
                "status": "sucesso",
                "produtos": produtos                    
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500
        
    @app.route('/produtos_selecao', methods=['GET'])
    def listar_produto_selecao():
        try:
            produtos = pg.obtem_produtos_selecao()

            return jsonify({
                "status": "sucesso",
                "produtos": produtos                    
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/produtos', methods=['POST'])
    def inserir_produto():
        try:
            dados = request.get_json()
            campos_obrigatorios = ['descricao', 'quantidade', 'quantificacao', 'valor_unitario']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            id = pg.inserir_produto(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Produto inserido com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/produtos/<int:id>', methods=['PUT'])
    def atualizar_produto(id):
        try:
            dados = request.get_json()
            print(f"Dados recebidos: {dados}")
            
            campos_obrigatorios = ['descricao', 'quantidade', 'quantificacao', 'valor_unitario']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            print(f"Atualizando produto {id} com dados: {dados}")
            pg.atualizar_produto(id, dados)
            print("Produto atualizado com sucesso")

            return jsonify({
                "status": "sucesso",
                "mensagem": "Produto atualizado com sucesso!"
            })
        except Exception as e:
            print(f"Erro ao atualizar produto: {str(e)}")
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/produtos/<int:id>', methods=['DELETE'])
    def excluir_produto(id):
        try:
            pg.excluir_produto(id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Produto excluído com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas', methods=['GET'])
    def listar_receita():
        try:
            receitas = pg.obtem_receitas()

            return jsonify({
                "status": "sucesso",
                "receitas": receitas
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas', methods=['POST'])
    def inserir_receita():
        try:
            dados = request.get_json()
            print(dados)
            campos_obrigatorios = ['nome']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            id = pg.inserir_receita(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Receita inserida com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas', methods=['PUT'])
    def inserir_receita_update():
        try:
            dados = request.get_json()
            campos_obrigatorios = ['id' ,'nome']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            pg.atualizar_receita(dados)

            return jsonify({
                "status": "sucesso",
                "mensagem": "Receita atualizada com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas/<int:id>', methods=['DELETE'])
    def excluir_receita(id):
        try:
            pg.excluir_receita(id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Receita excluída com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas/<int:receita_id>/itens', methods=['GET'])
    def listar_item_receita(receita_id):
        try:
            itens = pg.obtem_itens_receita(receita_id)

            return jsonify({
                "status": "sucesso",
                "itens": itens
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas/<int:receita_id>/itens', methods=['POST'])
    def inserir_item_receita(receita_id):
        try:
            dados = request.get_json()
            print(dados)
            campos_obrigatorios = ['produto_id', 'quantidade_utilizada']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            dados['receita_id'] = receita_id
            id = pg.inserir_item_receita(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Item inserido com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/receitas/itens/<int:item_id>', methods=['DELETE'])
    def excluir_item_receita(item_id):
        try:
            pg.excluir_item_receita(item_id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Item excluído com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500



    @app.route('/orcamento', methods=['GET'])
    def listar_orcamento():
        try:
            orcamento = pg.obtem_orcamento()

            return jsonify({
                "status": "sucesso",
                "orcamento": orcamento
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/orcamento', methods=['POST'])
    def inserir_orcamento():
        try:
            dados = request.get_json()
            print(dados)
            campos_obrigatorios = ['nome']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            id = pg.inserir_orcamento(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Orçamento inserido com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500
        
    @app.route('/orcamento', methods=['PUT'])
    def update_orcamento():
        try:
            dados = request.get_json()
            print(dados)
            campos_obrigatorios = ['nome']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            id = pg.update_orcamento(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Orçamento atualizado com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/orcamento/<int:id>', methods=['DELETE'])
    def excluir_orcamento(id):
        try:
            pg.excluir_orcamento(id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Receita excluída com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500
        
    @app.route('/orcamento/<int:orcamento_id>/total', methods=['GET'])
    def obtem_totais_orcamento(orcamento_id):
        try:
            totais = pg.obtem_totais_orcamento(orcamento_id)

            return jsonify({
                "status": "sucesso",
                "data": totais
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500
        
    @app.route('/orcamento/<int:orcamento_id>/itens', methods=['GET'])
    def listar_item_orcamento(orcamento_id):
        try:
            itens = pg.obtem_itens_orcamento(orcamento_id)

            return jsonify({
                "status": "sucesso",
                "itens": itens
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/orcamento/<int:orcamento_id>/itens', methods=['POST'])
    def inserir_item_orcamento(orcamento_id):
        try:
            dados = request.get_json()
            campos_obrigatorios = ['orcamento_id', 'receita_id', 'quantidade']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            id = pg.inserir_item_orcamento(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Item inserido com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/orcamento/itens/<int:item_id>', methods=['DELETE'])
    def excluir_item_orcamento(item_id):
        try:
            pg.excluir_item_orcamento(item_id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Item excluído com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500
        
    @app.route('/orcamento/<int:orcamento_id>/receitas', methods=['GET'])
    def obtem_itens_orcamentos_receita(orcamento_id):
        try:
            itens = pg.obtem_itens_orcamentos_receita(orcamento_id)

            return jsonify({
                "status": "sucesso",
                "itens": itens
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    # region Endpoints de Estoque
    @app.route('/estoque/movimentacoes', methods=['GET'])
    def listar_movimentacoes_estoque():
        try:
            produto_id = request.args.get('produto_id', type=int)
            movimentacoes = pg.obtem_movimentacoes_estoque(produto_id if produto_id else None)

            return jsonify({
                "status": "sucesso",
                "movimentacoes": movimentacoes
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/estoque/saldo', methods=['GET'])
    def listar_saldo_estoque():
        try:
            produto_id = request.args.get('produto_id', type=int)
            saldos = pg.obtem_saldo_estoque(produto_id if produto_id else None)

            return jsonify({
                "status": "sucesso",
                "saldos": saldos
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/estoque/movimentacoes', methods=['POST'])
    def inserir_movimentacao_estoque():
        try:
            dados = request.get_json()
            campos_obrigatorios = ['produto_id', 'tipo_movimentacao', 'quantidade']
            
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")

            # Validações adicionais
            if dados['tipo_movimentacao'] not in ['ENTRADA', 'SAIDA']:
                raise ValueError("tipo_movimentacao deve ser 'ENTRADA' ou 'SAIDA'")
            
            if dados['tipo_movimentacao'] == 'ENTRADA' and 'tipo_entrada' in dados:
                if dados['tipo_entrada'] not in ['MANUAL', 'COMPRA']:
                    raise ValueError("tipo_entrada deve ser 'MANUAL' ou 'COMPRA'")

            id = pg.inserir_movimentacao_estoque(dados)

            return jsonify({
                "status": "sucesso",
                "id": id,
                "mensagem": "Movimentação de estoque registrada com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    @app.route('/estoque/movimentacoes/<int:id>', methods=['DELETE'])
    def excluir_movimentacao_estoque(id):
        try:
            pg.excluir_movimentacao_estoque(id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Movimentação de estoque excluída com sucesso!"
            })
        except Exception as e:
            return jsonify({
                "status": "erro",
                "mensagem": str(e)
            }), 500

    #endregion