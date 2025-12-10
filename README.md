# Monitor de BID do Fortaleza

Este projeto monitora o BID (Boletim Informativo Diário) da CBF em busca de novos contratos relacionados ao **Fortaleza Esporte Clube**. Ele utiliza o **Google Gemini** para resolver captchas e gerar postagens criativas para redes sociais, e a **API do Twitter** para publicar automaticamente as novidades.

## Funcionalidades

- **Coleta Automatizada**: Busca e resolve captchas do site do BID da CBF.
- **Integração de Busca**: Pesquisa especificamente por contratos do Fortaleza EC.
- **Persistência de Dados**: Salva dados únicos de contratos no MongoDB para evitar duplicatas.
- **Mídias Sociais com IA**: Usa o Gemini para gerar tweets engajadores sobre novos jogadores/contratos.
- **Bot do Twitter**: Publica atualizações automaticamente no Twitter (X).
- **Arquitetura MVC**: Estrutura de código modular para melhor manutenção.

## Estrutura do Projeto

```
/
├── app/
│   ├── config.py          # Configuração e Variáveis de Ambiente
│   ├── controllers/       # Lógica de Negócio (BidController)
│   ├── models/            # Interação com Banco de Dados (ContractRepository)
│   ├── services/          # Serviços Externos (CBF, Gemini, Twitter)
│   └── __init__.py
├── main.py                # Ponto de Entrada da Aplicação
├── Dockerfile             # Configuração do Docker
├── docker-compose.yml     # Orquestração de Containers (App + Mongo + Mongo Express)
└── requirements.txt       # Dependências Python
```

## Pré-requisitos

- **Docker** e **Docker Compose** instalados.
- **Chave de API do Google Cloud** (Gemini).
- **Credenciais da API do Twitter** (Opcional, para postagem automática).

## Configuração

1.  **Clone o repositório**:
    ```bash
    git clone <url-do-repositorio>
    cd fortaleza-bid
    ```

2.  **Configure o Ambiente**:
    Copie o arquivo de exemplo e atualize com suas chaves.
    ```bash
    cp .env.example .env
    ```
    
    Edite o arquivo `.env`:
    ```env
    # Banco de Dados
    MONGO_URI=mongodb://mongo:27017/ 

    # IA
    GOOGLE_API_KEY=sua_chave_gemini_aqui

    # Twitter (Opcional - deixe em branco para modo "Dry Run")
    TWITTER_API_KEY=
    TWITTER_API_SECRET=
    TWITTER_ACCESS_TOKEN=
    TWITTER_ACCESS_TOKEN_SECRET=
    ```

## Executando com Docker Compose

A melhor maneira de rodar o projeto é utilizando o Docker Compose, que subirá a aplicação, o banco de dados MongoDB e a interface administrativa Mongo Express.

1.  **Subir os serviços**:
    ```bash
    docker-compose up --build
    ```

2.  **Acessando os Serviços**:
    - **Aplicação**: Acompanhe os logs no terminal para ver o processo de busca e publicação.
    - **Mongo Express**: Acesse `http://localhost:8081` para visualizar os dados salvos no banco de dados.

## Como Funciona

1.  **Inicialização**: Visita o site da CBF para obter cookies de sessão e tokens CSRF.
2.  **Captcha**: Baixa a imagem do captcha e a envia para o Gemini extrair o texto.
3.  **Busca**: Envia o captcha resolvido para buscar contratos do "Fortaleza" (ID 63238).
4.  **Filtragem e Salvamento**: Verifica no MongoDB se existem contratos. Novos contratos são salvos.
5.  **Publicação**: Se novos contratos forem encontrados, o Gemini gera um tweet e a aplicação o publica no Twitter.
