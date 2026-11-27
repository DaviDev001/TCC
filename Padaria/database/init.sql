-- Exemplo para o domínio da padaria
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NOT NULL,
    categoria VARCHAR(60),
    preco DECIMAL(10, 2) NOT NULL,
    quantidade_estoque INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_nome VARCHAR(120),
    total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTO'
);

-- Dados iniciais opcionais (evite duplicar se o script rodar mais de uma vez)
INSERT INTO produtos (nome, categoria, preco, quantidade_estoque, ativo)
SELECT 'Pão Francês', 'Pães', 0.80, 200, TRUE
WHERE NOT EXISTS (SELECT 1 FROM produtos WHERE nome = 'Pão Francês');