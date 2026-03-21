WITH base AS (
  SELECT
  *
  FROM b_consumidor.consumidor_dia
  WHERE nomeempresa LIKE '%Santander%'
    AND datrefcarga = '20260318'
),

-- 🔹 1. MACROCATEGORIA
macro AS (
  SELECT
    *,
    TRIM(REGEXP_REPLACE(
      LEFT(
        ai_query(
          "databricks-gpt-5-2",
          CONCAT(
"Classifique o relato em apenas UMA das macrocategorias abaixo:

Cobranças e Tarifas
Fraudes e Segurança
Canais Digitais
Atendimento ao Cliente
Cartões
Conta Bancária
Transferências e Pagamentos
Crédito e Financiamento
Investimentos
Transparência e Comunicação
Compliance / Regulatório
Outros

Regras:
- Retorne somente o nome da macrocategoria
- Sem explicação, sem pontuação
- Máximo 4 palavras
- Caso dúvida, retorne Outros

Relato: ", relato)
        ),
        50
      ),
      '[\\n\\r"]',''
    )) AS macro_categoria
  FROM base
),

-- 🔹 2. CATEGORIA
categoria AS (
  SELECT
    *,
    TRIM(REGEXP_REPLACE(
      LEFT(
        ai_query(
          "databricks-gpt-5-2",
          CONCAT(
"Macrocategoria: ", macro_categoria, ".

Classifique em UMA categoria:

Cobrança indevida
Cobrança duplicada
Tarifa não informada
Juros abusivos
Encargos inesperados
Transação não reconhecida
Conta invadida
Golpe / fraude
Cartão clonado
Falha de autenticação
App fora do ar
Erro em transação
Problema de login
Funcionalidade indisponível
Lentidão ou instabilidade
Demora no atendimento
Atendimento ineficiente
Informação incorreta
Falta de retorno
Dificuldade de contato
Cartão bloqueado
Transação recusada
Limite alterado
Problema na fatura
Conta bloqueada
Encerramento indevido
Saldo indisponível
Pix não concluído
Estorno não realizado
Negativa de crédito
Juros não claros
Problemas com contrato
Resgate demorado
Rentabilidade divergente
Contrato confuso
Propaganda enganosa
Descumprimento de prazo
Outros

Regras:
- Retorne apenas a categoria
- Sem explicação
- Coerente com a macrocategoria

Relato: ", relato)
        ),
        60
      ),
      '[\\n\\r"]',''
    )) AS categoria
  FROM macro
),

-- 🔹 3. SUBCATEGORIA
subcategoria AS (
  SELECT
    *,
    TRIM(REGEXP_REPLACE(
      LEFT(
        ai_query(
          "databricks-gpt-5-2",
          CONCAT(
"Macrocategoria: ", macro_categoria, ".
Categoria: ", categoria, ".

Classifique em UMA subcategoria:

Tarifa não reconhecida
Cobrança em duplicidade
Compra não reconhecida
Acesso indevido
Golpe via mensagem
Clonagem de cartão
Falha no Pix
Transferência não processada
Aplicativo indisponível
Erro ao login
Atendimento demorado
Sem resposta
Cartão recusado
Cartão bloqueado
Fatura com erro
Conta bloqueada
Saldo bloqueado
Crédito negado
Resgate não processado
Taxa não informada
Contrato confuso
Falta de transparência
Descumprimento de prazo
Outros

Regras:
- Retorne apenas a subcategoria
- Sem explicação
- Seja específico

Relato: ", relato)
        ),
        80
      ),
      '[\\n\\r"]',''
    )) AS subcategoria
  FROM categoria
),

-- 🔹 4. ROTEAMENTO (REGRA)
roteamento AS (
  SELECT
    *,
    CASE
      WHEN macro_categoria = 'Fraudes e Segurança' THEN 'Prevenção à Fraude'
      WHEN macro_categoria = 'Cobranças e Tarifas' THEN 'Backoffice Financeiro'
      WHEN macro_categoria = 'Cartões' THEN 'Backoffice de Cartões'
      WHEN macro_categoria = 'Conta Bancária' THEN 'Operações de Conta'
      WHEN macro_categoria = 'Crédito e Financiamento' THEN 'Crédito e Cobrança'
      WHEN macro_categoria = 'Investimentos' THEN 'Investimentos'
      WHEN macro_categoria = 'Compliance / Regulatório' THEN 'Jurídico / Compliance'
      WHEN macro_categoria = 'Atendimento ao Cliente' THEN 'SAC'
      ELSE 'SAC'
    END AS canal
  FROM subcategoria
),

prioridade as (
  select *,
  CASE 
    WHEN macro_categoria = 'Fraudes e Segurança' THEN 'Alta'
    WHEN macro_categoria = 'Cobranças e Tarifas' THEN 'Média'
    WHEN macro_categoria = 'Cartões' THEN 'Média'
    WHEN macro_categoria = 'Conta Bancária' THEN 'Média'
    WHEN macro_categoria = 'Crédito e Financiamento' THEN 'Média'
    WHEN macro_categoria = 'Investimentos' THEN 'Média'
    WHEN macro_categoria = 'Compliance / Regulatório' THEN 'Alta'
    WHEN macro_categoria = 'Atendimento ao Cliente' THEN 'Baixa'
  ELSE 'Baixa'
END as prioridade
  FROM roteamento
),

sla as (
  select *,
  CASE 
    WHEN macro_categoria = 'Fraudes e Segurança' THEN '0'
    WHEN macro_categoria = 'Cobranças e Tarifas' THEN '3'
    WHEN macro_categoria = 'Cartões' THEN '3'
    WHEN macro_categoria = 'Conta Bancária' THEN '3'
    WHEN macro_categoria = 'Crédito e Financiamento' THEN '3'
    WHEN macro_categoria = 'Investimentos' THEN '3'
    WHEN macro_categoria = 'Compliance / Regulatório' THEN '0'
    WHEN macro_categoria = 'Atendimento ao Cliente' THEN '5'
  ELSE '5'
END as sla_dias
  FROM prioridade
),

-- 🔹 5. RESPOSTA AUTOMÁTICA
resposta AS (
  SELECT
    *,
    ai_query(
      "databricks-gpt-5-2",
      CONCAT(
"Gere uma resposta ao cliente com base no relato.

Contexto:
Macrocategoria: ", macro_categoria, "
Categoria: ", categoria, "
Subcategoria: ", subcategoria, "

Regras:
- Tom humano e empático
- Não genérico
- Máximo 4 linhas
- Não usar frases padrão como 'estamos analisando'
- Explicar ação que será tomada
- Não inventar informações
- Não usar frases em primeira pessoa

Relato: ", relato)
    ) AS resposta_sugerida
  FROM sla
),

resposta_reanalise AS (
  SELECT
    *,
    CASE 
      WHEN status = 'Não Resolvido' THEN
        ai_query(
          "databricks-meta-llama-3-3-70b-instruct",
          CONCAT(
"O cliente avaliou o atendimento como insatisfatório.

Relato Inicial: ", relato, "
Nota: ", nota, "
Comentário: ", comentario, "

Contexto:
Macrocategoria: ", macro_categoria, "
Categoria: ", categoria, "

Gere uma nova resposta ao cliente.

Regras:
- Tom mais humano e cuidadoso
- Reconhecer explicitamente a insatisfação
- Mostrar que o caso será reavaliado
- Evitar respostas genéricas
- Máximo 5 linhas
- Demonstrar responsabilidade e ação concreta"
          )
        )

      ELSE ''
    END AS resposta_final

  FROM resposta
)

SELECT * FROM resposta_reanalise;