from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = 'estoque.db'

REGIONAIS = ['Natal', 'Mossoró', 'Paraíba']


def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def coluna_existe(nome_tabela, nome_coluna):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({nome_tabela})")
    colunas = cursor.fetchall()
    conn.close()
    return any(coluna["name"] == nome_coluna for coluna in colunas)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            UNIQUE(nome, categoria_id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            regional TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            valor_unitario REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            UNIQUE(categoria_id, marca_id, regional),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            origem TEXT NOT NULL,
            destino TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            regional TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            setor TEXT NOT NULL,
            data_entrega TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    ''')

    conn.commit()
    conn.close()


def atualizar_schema():
    conn = conectar()
    cursor = conn.cursor()

    if not coluna_existe("estoque", "valor_unitario"):
        cursor.execute("ALTER TABLE estoque ADD COLUMN valor_unitario REAL DEFAULT 0")

    if not coluna_existe("estoque", "valor_total"):
        cursor.execute("ALTER TABLE estoque ADD COLUMN valor_total REAL DEFAULT 0")

    conn.commit()
    conn.close()


def inserir_dados_iniciais():
    conn = conectar()
    cursor = conn.cursor()

    categorias_exemplo = [
        'Teclado',
        'Mouse',
        'Impressora de Cupom',
        'Monitor',
        'Notebook',
        'Cabo HDMI',
        'Cabo VGA',
        'Cabo de Impressora',
        'Pin Pad'
    ]

    for categoria in categorias_exemplo:
        cursor.execute(
            'INSERT OR IGNORE INTO categorias (nome) VALUES (?)',
            (categoria,)
        )

    conn.commit()

    cursor.execute('SELECT id, nome FROM categorias')
    categorias = cursor.fetchall()
    mapa_categorias = {categoria['nome']: categoria['id'] for categoria in categorias}

    marcas_exemplo = [
        ('Logitech', mapa_categorias['Teclado']),
        ('Multilaser', mapa_categorias['Teclado']),
        ('Genérico', mapa_categorias['Teclado']),

        ('Logitech', mapa_categorias['Mouse']),
        ('Multilaser', mapa_categorias['Mouse']),
        ('HP', mapa_categorias['Mouse']),
        ('Genérico', mapa_categorias['Mouse']),

        ('Bematech', mapa_categorias['Impressora de Cupom']),
        ('Elgin', mapa_categorias['Impressora de Cupom']),
        ('Epson', mapa_categorias['Impressora de Cupom']),

        ('LG', mapa_categorias['Monitor']),
        ('AOC', mapa_categorias['Monitor']),
        ('Samsung', mapa_categorias['Monitor']),
        ('Acer', mapa_categorias['Monitor']),
        ('Genérico', mapa_categorias['Monitor']),

        ('Dell', mapa_categorias['Notebook']),
        ('Samsung', mapa_categorias['Notebook']),
        ('Lenovo', mapa_categorias['Notebook']),
        ('Acer', mapa_categorias['Notebook']),

        ('Genérico', mapa_categorias['Cabo HDMI']),
        ('Genérico', mapa_categorias['Cabo VGA']),
        ('Genérico', mapa_categorias['Cabo de Impressora']),
        ('Genérico', mapa_categorias['Pin Pad'])
    ]

    for nome_marca, categoria_id in marcas_exemplo:
        cursor.execute('''
            INSERT OR IGNORE INTO marcas (nome, categoria_id)
            VALUES (?, ?)
        ''', (nome_marca, categoria_id))

    conn.commit()
    conn.close()


criar_tabelas()
atualizar_schema()
inserir_dados_iniciais()


@app.route('/')
def index():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM categorias ORDER BY nome')
    categorias = cursor.fetchall()

    cursor.execute('''
        SELECT
            e.id,
            c.nome AS categoria,
            m.nome AS marca,
            e.regional,
            e.quantidade,
            e.valor_unitario,
            e.valor_total
        FROM estoque e
        JOIN categorias c ON e.categoria_id = c.id
        JOIN marcas m ON e.marca_id = m.id
        ORDER BY c.nome, m.nome, e.regional
    ''')
    estoque = cursor.fetchall()

    cursor.execute('''
        SELECT
            mov.id,
            c.nome AS categoria,
            m.nome AS marca,
            mov.origem,
            mov.destino,
            mov.quantidade,
            mov.data_movimentacao
        FROM movimentacoes mov
        JOIN categorias c ON mov.categoria_id = c.id
        JOIN marcas m ON mov.marca_id = m.id
        ORDER BY mov.id DESC
        LIMIT 10
    ''')
    movimentacoes = cursor.fetchall()

    cursor.execute('''
        SELECT
            ent.id,
            c.nome AS categoria,
            m.nome AS marca,
            ent.regional,
            ent.quantidade,
            ent.responsavel,
            ent.setor,
            ent.data_entrega
        FROM entregas ent
        JOIN categorias c ON ent.categoria_id = c.id
        JOIN marcas m ON ent.marca_id = m.id
        ORDER BY ent.id DESC
        LIMIT 10
    ''')
    entregas = cursor.fetchall()

    categoria_consulta = request.args.get('categoria_consulta', '').strip()
    resultado_consulta = None
    resultado_por_regional = []

    if categoria_consulta:
        cursor.execute('''
            SELECT COALESCE(SUM(e.quantidade), 0) AS total
            FROM estoque e
            WHERE e.categoria_id = ?
        ''', (categoria_consulta,))
        resultado_consulta = cursor.fetchone()['total']

        cursor.execute('''
            SELECT e.regional, SUM(e.quantidade) AS total
            FROM estoque e
            WHERE e.categoria_id = ?
            GROUP BY e.regional
            ORDER BY e.regional
        ''', (categoria_consulta,))
        resultado_por_regional = cursor.fetchall()

    # KPIs / BI
    cursor.execute('SELECT COUNT(*) AS total_registros FROM estoque')
    total_registros = cursor.fetchone()['total_registros']

    cursor.execute('SELECT COALESCE(SUM(quantidade), 0) AS total_unidades FROM estoque')
    total_unidades = cursor.fetchone()['total_unidades']

    cursor.execute('SELECT COALESCE(SUM(valor_total), 0) AS valor_estoque FROM estoque')
    valor_estoque = cursor.fetchone()['valor_estoque']

    cursor.execute('''
        SELECT c.nome AS categoria, COALESCE(SUM(e.quantidade), 0) AS total
        FROM categorias c
        LEFT JOIN estoque e ON e.categoria_id = c.id
        GROUP BY c.id, c.nome
        ORDER BY total DESC, c.nome
    ''')
    resumo_categorias = cursor.fetchall()

    conn.close()

    return render_template(
        'index.html',
        categorias=categorias,
        estoque=estoque,
        movimentacoes=movimentacoes,
        entregas=entregas,
        regionais=REGIONAIS,
        categoria_consulta=categoria_consulta,
        resultado_consulta=resultado_consulta,
        resultado_por_regional=resultado_por_regional,
        total_registros=total_registros,
        total_unidades=total_unidades,
        valor_estoque=valor_estoque,
        resumo_categorias=resumo_categorias
    )


@app.route('/marcas/<int:categoria_id>')
def listar_marcas(categoria_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, nome
        FROM marcas
        WHERE categoria_id = ?
        ORDER BY nome
    ''', (categoria_id,))
    marcas = cursor.fetchall()

    conn.close()

    options = "<option value=''>Selecione a marca</option>"
    for marca in marcas:
        options += f"<option value='{marca['id']}'>{marca['nome']}</option>"

    return options


@app.route('/cadastrar_categoria', methods=['POST'])
def cadastrar_categoria():
    nome = request.form.get('nome_categoria', '').strip()

    if not nome:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO categorias (nome) VALUES (?)', (nome,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/cadastrar_marca', methods=['POST'])
def cadastrar_marca():
    nome = request.form.get('nome_marca', '').strip()
    categoria_id = request.form.get('categoria_id_marca')

    if not nome or not categoria_id:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO marcas (nome, categoria_id)
        VALUES (?, ?)
    ''', (nome, categoria_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/adicionar_estoque', methods=['POST'])
def adicionar_estoque():
    categoria_id = request.form.get('categoria_id')
    marca_id = request.form.get('marca_id')
    regional = request.form.get('regional')
    quantidade = request.form.get('quantidade')
    valor_total_compra = request.form.get('valor_total_compra')

    if not all([categoria_id, marca_id, regional, quantidade, valor_total_compra]):
        return redirect(url_for('index'))

    try:
        quantidade = int(quantidade)
        valor_total_compra = float(valor_total_compra)
    except ValueError:
        return redirect(url_for('index'))

    if quantidade <= 0 or valor_total_compra < 0:
        return redirect(url_for('index'))

    valor_unitario = valor_total_compra / quantidade if quantidade > 0 else 0

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, quantidade, valor_total
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, regional))

    item = cursor.fetchone()

    if item:
        nova_quantidade = item['quantidade'] + quantidade
        novo_valor_total = (item['valor_total'] or 0) + valor_total_compra
        novo_valor_unitario = novo_valor_total / nova_quantidade if nova_quantidade > 0 else 0

        cursor.execute('''
            UPDATE estoque
            SET quantidade = ?, valor_unitario = ?, valor_total = ?
            WHERE id = ?
        ''', (nova_quantidade, novo_valor_unitario, novo_valor_total, item['id']))
    else:
        cursor.execute('''
            INSERT INTO estoque (
                categoria_id, marca_id, regional, quantidade, valor_unitario, valor_total
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (categoria_id, marca_id, regional, quantidade, valor_unitario, valor_total_compra))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/transferir', methods=['POST'])
def transferir():
    categoria_id = request.form.get('categoria_id')
    marca_id = request.form.get('marca_id')
    origem = request.form.get('origem')
    destino = request.form.get('destino')
    quantidade = request.form.get('quantidade')

    if not all([categoria_id, marca_id, origem, destino, quantidade]):
        return redirect(url_for('index'))

    if origem == destino:
        return redirect(url_for('index'))

    try:
        quantidade = int(quantidade)
    except ValueError:
        return redirect(url_for('index'))

    if quantidade <= 0:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, quantidade, valor_unitario, valor_total
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, origem))

    estoque_origem = cursor.fetchone()

    if not estoque_origem or estoque_origem['quantidade'] < quantidade:
        conn.close()
        return redirect(url_for('index'))

    valor_unitario_origem = estoque_origem['valor_unitario'] or 0
    nova_qtd_origem = estoque_origem['quantidade'] - quantidade
    novo_valor_total_origem = nova_qtd_origem * valor_unitario_origem

    cursor.execute('''
        UPDATE estoque
        SET quantidade = ?, valor_total = ?
        WHERE id = ?
    ''', (nova_qtd_origem, novo_valor_total_origem, estoque_origem['id']))

    cursor.execute('''
        SELECT id, quantidade, valor_unitario, valor_total
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, destino))

    estoque_destino = cursor.fetchone()
    valor_transferido = quantidade * valor_unitario_origem

    if estoque_destino:
        nova_qtd_destino = estoque_destino['quantidade'] + quantidade
        novo_valor_total_destino = (estoque_destino['valor_total'] or 0) + valor_transferido
        novo_valor_unitario_destino = novo_valor_total_destino / nova_qtd_destino if nova_qtd_destino > 0 else 0

        cursor.execute('''
            UPDATE estoque
            SET quantidade = ?, valor_unitario = ?, valor_total = ?
            WHERE id = ?
        ''', (nova_qtd_destino, novo_valor_unitario_destino, novo_valor_total_destino, estoque_destino['id']))
    else:
        cursor.execute('''
            INSERT INTO estoque (
                categoria_id, marca_id, regional, quantidade, valor_unitario, valor_total
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (categoria_id, marca_id, destino, quantidade, valor_unitario_origem, valor_transferido))

    cursor.execute('''
        INSERT INTO movimentacoes (categoria_id, marca_id, origem, destino, quantidade)
        VALUES (?, ?, ?, ?, ?)
    ''', (categoria_id, marca_id, origem, destino, quantidade))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/entregar', methods=['POST'])
def entregar():
    categoria_id = request.form.get('categoria_id')
    marca_id = request.form.get('marca_id')
    regional = request.form.get('regional')
    quantidade = request.form.get('quantidade')
    responsavel = request.form.get('responsavel', '').strip()
    setor = request.form.get('setor', '').strip()

    if not all([categoria_id, marca_id, regional, quantidade, responsavel, setor]):
        return redirect(url_for('index'))

    try:
        quantidade = int(quantidade)
    except ValueError:
        return redirect(url_for('index'))

    if quantidade <= 0:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, quantidade, valor_unitario
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, regional))

    item = cursor.fetchone()

    if not item or item['quantidade'] < quantidade:
        conn.close()
        return redirect(url_for('index'))

    nova_quantidade = item['quantidade'] - quantidade
    novo_valor_total = nova_quantidade * (item['valor_unitario'] or 0)

    cursor.execute('''
        UPDATE estoque
        SET quantidade = ?, valor_total = ?
        WHERE id = ?
    ''', (nova_quantidade, novo_valor_total, item['id']))

    cursor.execute('''
        INSERT INTO entregas (
            categoria_id, marca_id, regional, quantidade, responsavel, setor
        )
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (categoria_id, marca_id, regional, quantidade, responsavel, setor))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)