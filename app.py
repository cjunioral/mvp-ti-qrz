from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = 'estoque.db'

REGIONAIS = ['Natal', 'Mossoró', 'Paraíba']


def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


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
            e.quantidade
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
            JOIN categorias c ON e.categoria_id = c.id
            WHERE c.id = ?
        ''', (categoria_consulta,))
        resultado_consulta = cursor.fetchone()['total']

        cursor.execute('''
            SELECT e.regional, SUM(e.quantidade) AS total
            FROM estoque e
            JOIN categorias c ON e.categoria_id = c.id
            WHERE c.id = ?
            GROUP BY e.regional
            ORDER BY e.regional
        ''', (categoria_consulta,))
        resultado_por_regional = cursor.fetchall()

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
        resultado_por_regional=resultado_por_regional
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

    options = '<option value=''>Selecione a marca</option>'
    for marca in marcas:
        options += f"<option value='{marca['id']}'>{marca['nome']}</option>"

    return options


@app.route('/adicionar_estoque', methods=['POST'])
def adicionar_estoque():
    categoria_id = request.form.get('categoria_id')
    marca_id = request.form.get('marca_id')
    regional = request.form.get('regional')
    quantidade = request.form.get('quantidade')

    if not all([categoria_id, marca_id, regional, quantidade]):
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
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, regional))

    item = cursor.fetchone()

    if item:
        nova_quantidade = item['quantidade'] + quantidade
        cursor.execute('''
            UPDATE estoque
            SET quantidade = ?
            WHERE id = ?
        ''', (nova_quantidade, item['id']))
    else:
        cursor.execute('''
            INSERT INTO estoque (categoria_id, marca_id, regional, quantidade)
            VALUES (?, ?, ?, ?)
        ''', (categoria_id, marca_id, regional, quantidade))

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
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, origem))

    estoque_origem = cursor.fetchone()

    if not estoque_origem or estoque_origem['quantidade'] < quantidade:
        conn.close()
        return redirect(url_for('index'))

    nova_qtd_origem = estoque_origem['quantidade'] - quantidade
    cursor.execute('''
        UPDATE estoque
        SET quantidade = ?
        WHERE id = ?
    ''', (nova_qtd_origem, estoque_origem['id']))

    cursor.execute('''
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, destino))

    estoque_destino = cursor.fetchone()

    if estoque_destino:
        nova_qtd_destino = estoque_destino['quantidade'] + quantidade
        cursor.execute('''
            UPDATE estoque
            SET quantidade = ?
            WHERE id = ?
        ''', (nova_qtd_destino, estoque_destino['id']))
    else:
        cursor.execute('''
            INSERT INTO estoque (categoria_id, marca_id, regional, quantidade)
            VALUES (?, ?, ?, ?)
        ''', (categoria_id, marca_id, destino, quantidade))

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
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    ''', (categoria_id, marca_id, regional))

    item = cursor.fetchone()

    if not item or item['quantidade'] < quantidade:
        conn.close()
        return redirect(url_for('index'))

    nova_quantidade = item['quantidade'] - quantidade

    cursor.execute('''
        UPDATE estoque
        SET quantidade = ?
        WHERE id = ?
    ''', (nova_quantidade, item['id']))

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