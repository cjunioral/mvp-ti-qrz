from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = "estoque.db"

REGIONAIS = ["Natal", "Mossoró", "Paraíba"]


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
            regional TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            UNIQUE(categoria_id, marca_id, regional),
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
            quantidade INTEGER NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (marca_id) REFERENCES marcas(id)
        )
    """)

    conn.commit()
    conn.close()


def inserir_dados_iniciais():
    conn = conectar()
    cursor = conn.cursor()

    categorias_exemplo = ["Teclado", "Mouse", "Impressora Fiscal"]

    for categoria in categorias_exemplo:
        cursor.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (categoria,))

    conn.commit()

    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()
    mapa_categorias = {categoria["nome"]: categoria["id"] for categoria in categorias}

    marcas_exemplo = [
        ("Logitech", mapa_categorias["Teclado"]),
        ("Multilaser", mapa_categorias["Teclado"]),
        ("Redragon", mapa_categorias["Teclado"]),
        ("Logitech", mapa_categorias["Mouse"]),
        ("Multilaser", mapa_categorias["Mouse"]),
        ("HP", mapa_categorias["Mouse"]),
        ("Bematech", mapa_categorias["Impressora Fiscal"]),
        ("Elgin", mapa_categorias["Impressora Fiscal"]),
        ("Epson", mapa_categorias["Impressora Fiscal"]),
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
            e.regional,
            e.quantidade
        FROM estoque e
        JOIN categorias c ON e.categoria_id = c.id
        JOIN marcas m ON e.marca_id = m.id
        ORDER BY c.nome, m.nome, e.regional
    """)
    estoque = cursor.fetchall()

    cursor.execute("""
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
    """)
    movimentacoes = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        categorias=categorias,
        estoque=estoque,
        movimentacoes=movimentacoes,
        regionais=REGIONAIS
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

    options = '<option value="">Selecione a marca</option>'
    for marca in marcas:
        options += f'<option value="{marca["id"]}">{marca["nome"]}</option>'

    return options


@app.route("/adicionar_estoque", methods=["POST"])
def adicionar_estoque():
    categoria_id = request.form.get("categoria_id")
    marca_id = request.form.get("marca_id")
    regional = request.form.get("regional")
    quantidade = request.form.get("quantidade")

    if not all([categoria_id, marca_id, regional, quantidade]):
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
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
    """, (categoria_id, marca_id, regional))

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
            INSERT INTO estoque (categoria_id, marca_id, regional, quantidade)
            VALUES (?, ?, ?, ?)
        """, (categoria_id, marca_id, regional, quantidade))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/transferir", methods=["POST"])
def transferir():
    categoria_id = request.form.get("categoria_id")
    marca_id = request.form.get("marca_id")
    origem = request.form.get("origem")
    destino = request.form.get("destino")
    quantidade = request.form.get("quantidade")

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
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
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
        WHERE categoria_id = ? AND marca_id = ? AND regional = ?
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
            INSERT INTO estoque (categoria_id, marca_id, regional, quantidade)
            VALUES (?, ?, ?, ?)
        """, (categoria_id, marca_id, destino, quantidade))

    cursor.execute("""
        INSERT INTO movimentacoes (categoria_id, marca_id, origem, destino, quantidade)
        VALUES (?, ?, ?, ?, ?)
    """, (categoria_id, marca_id, origem, destino, quantidade))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)