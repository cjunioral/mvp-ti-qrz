from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = "estoque.db"

ORIGENS = [
    "Natal",
    "Mossoró",
    "Paraíba"
]

DESTINOS_INTERNOS = [
    "Natal",
    "Mossoró",
    "Paraíba"
]

LOJAS = [
    "001-HQ PATU",
    "002-HQ MACAU",
    "003-HQ CARAU",
    "004-HQ SAO B",
    "005-HQ PATOS",
    "006-HQ N.BET",
    "007-HQ BOA V",
    "008-HQ ASSU",
    "009-HQ A CON",
    "010-QA MOSSO",
    "011-QA ASSU",
    "012-QA JOAO",
    "013-QA SAO G",
    "014-QA CEARA",
    "015-QA PATOS",
    "016-QA PARNA",
    "017-QA CATOL",
    "018-QA MONTE",
    "019-QA ASSU02",
    "020-NOR ATAC PA",
    "021-QA BREJO",
    "022-NOR ATAC",
    "023-QA SAO B",
    "024-QA ITAPO",
    "025-NOR A SO",
    "026-QA VEN E",
    "027-NORD MAC",
    "028-NOR A BA",
    "040-AGIL PAT",
    "041-CQ MOSSO",
    "042-AGIL SG",
    "043-COME J 1",
    "044-POEDMA",
    "045-LV SANTA",
    "046-AGENCIA",
    "047-COME J 2",
    "048-SQ BV",
    "049-SQ CEN",
    "050-SQ ASSU",
    "051-SQ ALT C",
    "052-CQ ASSU",
    "053-CQ BARRO",
    "054-CQ JC",
    "055-CQ S.GON",
    "056-DEPOS CR",
    "057-HQ CATOL",
    "058-ASSU EST"
]


def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marcas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            UNIQUE(nome, categoria_id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            unidade TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            UNIQUE(categoria_id, marca_id, unidade),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entradas_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            unidade TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            observacao TEXT,
            data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            origem TEXT NOT NULL,
            destino TEXT NOT NULL,
            tipo_destino TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            marca_id INTEGER NOT NULL,
            unidade TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            setor TEXT NOT NULL,
            data_entrega TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    """)

    conn.commit()
    conn.close()


def inserir_dados_iniciais():
    conn = conectar()
    cursor = conn.cursor()

    categorias_exemplo = [
        "Teclado",
        "Mouse",
        "Impressora de Cupom",
        "Monitor",
        "Notebook",
        "Cabo HDMI",
        "Cabo VGA",
        "Cabo de Rede",
        "Cabo de Impressora",
        "Pin Pad"
    ]

    for categoria in categorias_exemplo:
        cursor.execute(
            "INSERT OR IGNORE INTO categorias (nome) VALUES (?)",
            (categoria,)
        )

    conn.commit()

    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()
    mapa_categorias = {categoria["nome"]: categoria["id"] for categoria in categorias}

    marcas_exemplo = [
        ("Logitech", mapa_categorias["Teclado"]),
        ("Multilaser", mapa_categorias["Teclado"]),
        ("Genérico", mapa_categorias["Teclado"]),

        ("Logitech", mapa_categorias["Mouse"]),
        ("Multilaser", mapa_categorias["Mouse"]),
        ("HP", mapa_categorias["Mouse"]),
        ("Genérico", mapa_categorias["Mouse"]),

        ("Bematech", mapa_categorias["Impressora de Cupom"]),
        ("Elgin", mapa_categorias["Impressora de Cupom"]),
        ("Epson", mapa_categorias["Impressora de Cupom"]),

        ("LG", mapa_categorias["Monitor"]),
        ("AOC", mapa_categorias["Monitor"]),
        ("Samsung", mapa_categorias["Monitor"]),
        ("Acer", mapa_categorias["Monitor"]),
        ("Genérico", mapa_categorias["Monitor"]),

        ("Dell", mapa_categorias["Notebook"]),
        ("Samsung", mapa_categorias["Notebook"]),
        ("Lenovo", mapa_categorias["Notebook"]),
        ("Acer", mapa_categorias["Notebook"]),

        ("Genérico", mapa_categorias["Cabo HDMI"]),
        ("Genérico", mapa_categorias["Cabo VGA"]),
        ("Genérico", mapa_categorias["Cabo de Rede"]),
        ("Genérico", mapa_categorias["Cabo de Impressora"]),
        ("Genérico", mapa_categorias["Pin Pad"])
    ]

    for nome_marca, categoria_id in marcas_exemplo:
        cursor.execute("""
            INSERT OR IGNORE INTO marcas (nome, categoria_id)
            VALUES (?, ?)
        """, (nome_marca, categoria_id))

    conn.commit()
    conn.close()


criar_tabelas()
inserir_dados_iniciais()


@app.route("/")
def index():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM categorias ORDER BY nome")
    categorias = cursor.fetchall()

    cursor.execute("""
        SELECT
            e.id,
            c.nome AS categoria,
            m.nome AS marca,
            e.unidade,
            e.quantidade
        FROM estoque e
        JOIN categorias c ON e.categoria_id = c.id
        JOIN marcas m ON e.marca_id = m.id
        ORDER BY e.quantidade ASC, c.nome, m.nome, e.unidade
    """)
    estoque = cursor.fetchall()

    cursor.execute("""
        SELECT
            en.id,
            c.nome AS categoria,
            m.nome AS marca,
            en.unidade,
            en.quantidade,
            en.valor_unitario,
            en.valor_total,
            en.observacao,
            en.data_entrada
        FROM entradas_estoque en
        JOIN categorias c ON en.categoria_id = c.id
        JOIN marcas m ON en.marca_id = m.id
        ORDER BY en.id DESC
        LIMIT 50
    """)
    entradas_estoque = cursor.fetchall()

    cursor.execute("""
        SELECT
            mov.id,
            c.nome AS categoria,
            m.nome AS marca,
            mov.origem,
            mov.destino,
            mov.tipo_destino,
            mov.quantidade,
            mov.data_movimentacao
        FROM movimentacoes mov
        JOIN categorias c ON mov.categoria_id = c.id
        JOIN marcas m ON mov.marca_id = m.id
        ORDER BY mov.id DESC
        LIMIT 20
    """)
    movimentacoes = cursor.fetchall()

    cursor.execute("""
        SELECT
            ent.id,
            c.nome AS categoria,
            m.nome AS marca,
            ent.unidade,
            ent.quantidade,
            ent.responsavel,
            ent.setor,
            ent.data_entrega
        FROM entregas ent
        JOIN categorias c ON ent.categoria_id = c.id
        JOIN marcas m ON ent.marca_id = m.id
        ORDER BY ent.id DESC
        LIMIT 20
    """)
    entregas = cursor.fetchall()

    categoria_consulta = request.args.get("categoria_consulta", "").strip()
    resultado_consulta = None
    resultado_por_unidade = []

    if categoria_consulta:
        cursor.execute("""
            SELECT COALESCE(SUM(e.quantidade), 0) AS total
            FROM estoque e
            WHERE e.categoria_id = ?
        """, (categoria_consulta,))
        resultado_consulta = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT e.unidade, SUM(e.quantidade) AS total
            FROM estoque e
            WHERE e.categoria_id = ?
            GROUP BY e.unidade
            ORDER BY e.unidade
        """, (categoria_consulta,))
        resultado_por_unidade = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_registros FROM estoque")
    total_registros = cursor.fetchone()["total_registros"]

    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) AS total_unidades FROM estoque")
    total_unidades = cursor.fetchone()["total_unidades"]

    cursor.execute("SELECT COALESCE(SUM(valor_total), 0) AS total_compras FROM entradas_estoque")
    total_compras = cursor.fetchone()["total_compras"]

    cursor.execute("SELECT COUNT(*) AS total_baixo FROM estoque WHERE quantidade <= 3")
    total_baixo = cursor.fetchone()["total_baixo"]

    cursor.execute("""
        SELECT c.nome AS categoria, COALESCE(SUM(e.quantidade), 0) AS total
        FROM categorias c
        LEFT JOIN estoque e ON e.categoria_id = c.id
        GROUP BY c.id, c.nome
        ORDER BY total ASC, c.nome
    """)
    resumo_categorias = cursor.fetchall()

    cursor.execute("""
        SELECT e.unidade, COALESCE(SUM(e.quantidade), 0) AS total
        FROM estoque e
        WHERE e.unidade IN ('Natal', 'Mossoró', 'Paraíba')
        GROUP BY e.unidade
        ORDER BY total ASC, e.unidade
    """)
    resumo_regionais = cursor.fetchall()

    cursor.execute("""
        SELECT
            c.nome AS categoria,
            m.nome AS marca,
            e.unidade,
            e.quantidade
        FROM estoque e
        JOIN categorias c ON e.categoria_id = c.id
        JOIN marcas m ON e.marca_id = m.id
        WHERE e.quantidade <= 3
        ORDER BY e.quantidade ASC, c.nome, m.nome, e.unidade
        LIMIT 12
    """)
    estoque_baixo = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        categorias=categorias,
        estoque=estoque,
        entradas_estoque=entradas_estoque,
        movimentacoes=movimentacoes,
        entregas=entregas,
        origens=ORIGENS,
        destinos_internos=DESTINOS_INTERNOS,
        lojas=LOJAS,
        categoria_consulta=categoria_consulta,
        resultado_consulta=resultado_consulta,
        resultado_por_unidade=resultado_por_unidade,
        total_registros=total_registros,
        total_unidades=total_unidades,
        total_compras=total_compras,
        total_baixo=total_baixo,
        resumo_categorias=resumo_categorias,
        resumo_regionais=resumo_regionais,
        estoque_baixo=estoque_baixo
    )


@app.route("/marcas/<int:categoria_id>")
def listar_marcas(categoria_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome
        FROM marcas
        WHERE categoria_id = ?
        ORDER BY nome
    """, (categoria_id,))
    marcas = cursor.fetchall()

    conn.close()

    options = "<option value=''>Selecione a marca</option>"
    for marca in marcas:
        options += f"<option value='{marca['id']}'>{marca['nome']}</option>"

    return options


@app.route("/cadastrar_categoria", methods=["POST"])
def cadastrar_categoria():
    nome = request.form.get("nome_categoria", "").strip()

    if not nome:
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/cadastrar_marca", methods=["POST"])
def cadastrar_marca():
    nome = request.form.get("nome_marca", "").strip()
    categoria_id = request.form.get("categoria_id_marca")

    if not nome or not categoria_id:
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO marcas (nome, categoria_id)
        VALUES (?, ?)
    """, (nome, categoria_id))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/adicionar_estoque", methods=["POST"])
def adicionar_estoque():
    categoria_id = request.form.get("categoria_id")
    marca_id = request.form.get("marca_id")
    unidade = request.form.get("unidade")
    quantidade = request.form.get("quantidade")
    valor_total_compra = request.form.get("valor_total_compra")
    observacao = request.form.get("observacao", "").strip()

    if not all([categoria_id, marca_id, unidade, quantidade, valor_total_compra]):
        return redirect(url_for("index"))

    try:
        quantidade = int(quantidade)
        valor_total_compra = float(valor_total_compra)
    except ValueError:
        return redirect(url_for("index"))

    if quantidade <= 0 or valor_total_compra < 0:
        return redirect(url_for("index"))

    valor_unitario = valor_total_compra / quantidade

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND unidade = ?
    """, (categoria_id, marca_id, unidade))

    item = cursor.fetchone()

    if item:
        nova_quantidade = item["quantidade"] + quantidade
        cursor.execute("""
            UPDATE estoque
            SET quantidade = ?
            WHERE id = ?
        """, (nova_quantidade, item["id"]))
    else:
        cursor.execute("""
            INSERT INTO estoque (categoria_id, marca_id, unidade, quantidade)
            VALUES (?, ?, ?, ?)
        """, (categoria_id, marca_id, unidade, quantidade))

    cursor.execute("""
        INSERT INTO entradas_estoque (
            categoria_id, marca_id, unidade, quantidade,
            valor_unitario, valor_total, observacao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        categoria_id,
        marca_id,
        unidade,
        quantidade,
        valor_unitario,
        valor_total_compra,
        observacao
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/transferir", methods=["POST"])
def transferir():
    categoria_id = request.form.get("categoria_id")
    marca_id = request.form.get("marca_id")
    origem = request.form.get("origem")
    tipo_destino = request.form.get("tipo_destino")
    destino_interno = request.form.get("destino_interno")
    destino_loja = request.form.get("destino_loja")
    quantidade = request.form.get("quantidade")

    if tipo_destino == "interno":
        destino = destino_interno
    elif tipo_destino == "loja":
        destino = destino_loja
    else:
        destino = None

    if not all([categoria_id, marca_id, origem, destino, quantidade]):
        return redirect(url_for("index"))

    if origem == destino:
        return redirect(url_for("index"))

    try:
        quantidade = int(quantidade)
    except ValueError:
        return redirect(url_for("index"))

    if quantidade <= 0:
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND unidade = ?
    """, (categoria_id, marca_id, origem))

    estoque_origem = cursor.fetchone()

    if not estoque_origem or estoque_origem["quantidade"] < quantidade:
        conn.close()
        return redirect(url_for("index"))

    nova_qtd_origem = estoque_origem["quantidade"] - quantidade
    cursor.execute("""
        UPDATE estoque
        SET quantidade = ?
        WHERE id = ?
    """, (nova_qtd_origem, estoque_origem["id"]))

    cursor.execute("""
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND unidade = ?
    """, (categoria_id, marca_id, destino))

    estoque_destino = cursor.fetchone()

    if estoque_destino:
        nova_qtd_destino = estoque_destino["quantidade"] + quantidade
        cursor.execute("""
            UPDATE estoque
            SET quantidade = ?
            WHERE id = ?
        """, (nova_qtd_destino, estoque_destino["id"]))
    else:
        cursor.execute("""
            INSERT INTO estoque (categoria_id, marca_id, unidade, quantidade)
            VALUES (?, ?, ?, ?)
        """, (categoria_id, marca_id, destino, quantidade))

    cursor.execute("""
        INSERT INTO movimentacoes (
            categoria_id, marca_id, origem, destino, tipo_destino, quantidade
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (categoria_id, marca_id, origem, destino, tipo_destino, quantidade))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/entregar", methods=["POST"])
def entregar():
    categoria_id = request.form.get("categoria_id")
    marca_id = request.form.get("marca_id")
    unidade = request.form.get("unidade")
    quantidade = request.form.get("quantidade")
    responsavel = request.form.get("responsavel", "").strip()
    setor = request.form.get("setor", "").strip()

    if not all([categoria_id, marca_id, unidade, quantidade, responsavel, setor]):
        return redirect(url_for("index"))

    try:
        quantidade = int(quantidade)
    except ValueError:
        return redirect(url_for("index"))

    if quantidade <= 0:
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quantidade
        FROM estoque
        WHERE categoria_id = ? AND marca_id = ? AND unidade = ?
    """, (categoria_id, marca_id, unidade))

    item = cursor.fetchone()

    if not item or item["quantidade"] < quantidade:
        conn.close()
        return redirect(url_for("index"))

    nova_quantidade = item["quantidade"] - quantidade

    cursor.execute("""
        UPDATE estoque
        SET quantidade = ?
        WHERE id = ?
    """, (nova_quantidade, item["id"]))

    cursor.execute("""
        INSERT INTO entregas (
            categoria_id, marca_id, unidade, quantidade, responsavel, setor
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (categoria_id, marca_id, unidade, quantidade, responsavel, setor))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)