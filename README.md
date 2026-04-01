# PM Discovery Tool

Transforme reviews do Google Play em oportunidades de produto usando IA Gemini. Construído para Product Managers que querem descoberta estruturada mais rápida.

## 🚀 Visão Geral

O PM Discovery Tool é uma aplicação web que automatiza o processo de análise de feedback de usuários. Usando inteligência artificial (Google Gemini), a ferramenta extrai insights estruturados de reviews do Google Play, identifica problemas, oportunidades e prioriza melhorias de produto.

### ✨ Funcionalidades Principais

- **📱 Busca de Reviews**: Coleta reviews do Google Play com filtros por rating e ordenação
- **🤖 Análise com IA**: Usa Gemini para extrair insights estruturados de cada review
- **✅ Validação de Oportunidades**: Verifica se as oportunidades são viáveis e dentro do escopo
- **📊 Agrupamento por Temas**: Organiza oportunidades similares por categorias
- **🎯 Backlog Priorizado**: Cria lista de prioridades baseada em frequência e viabilidade
- **📋 Resumo Executivo**: Gera relatório executivo das principais oportunidades
- **💾 Exportação**: Salva resultados em JSON e CSV

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Streamlit** - Interface web
- **Google Play Scraper** - Coleta de reviews
- **Google Gemini AI** - Análise de texto
- **Pandas** - Manipulação de dados
- **python-dotenv** - Gerenciamento de variáveis de ambiente

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Conta Google Cloud com API Gemini habilitada
- Chave de API do Gemini

### Passos de Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/dustiinthewind1-del/pmdiscoverytool.git
   cd pmdiscoverytool
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   ```
   
   Edite o arquivo `.env` e adicione sua chave da API Gemini:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   ```

## 🚀 Como Usar

### Execução da Aplicação

```bash
streamlit run main.py
```

A aplicação será aberta no seu navegador em `http://localhost:8501`.

### Fluxo de Uso

1. **Digite o nome da app** (ex: `com.strava`, `com.goodreads.app`)
2. **Configure os filtros:**
   - Tipo de ordenação (Mais relevantes, Mais recentes)
   - Número de reviews (5-100)
   - Ratings desejados (1-5 estrelas)
3. **Clique em "Analyse"**
4. **Aguarde a análise** - a ferramenta irá:
   - Buscar reviews
   - Analisar cada review com IA
   - Validar oportunidades
   - Apresentar resultados em tabela

### Exemplo de Uso

Para analisar reviews do Strava:
- App name: `com.strava`
- Reviews: 20
- Ratings: 1, 2, 3 estrelas
- Ordenação: Mais relevantes

## 📁 Estrutura do Projeto

```
pmdiscoverytool/
├── main.py                 # Aplicação principal Streamlit
├── export_report.py        # Gerador de relatórios (CLI)
├── requirements.txt        # Dependências Python
├── .env.example           # Exemplo de configuração
├── .gitignore             # Arquivos ignorados pelo Git
├── README.md              # Este arquivo
└── strava_*               # Arquivos de exemplo (CSV, JSON, XLSX)
```

## 🔧 Funcionalidades Detalhadas

### Análise de Reviews

Cada review é analisada pelo Gemini com o prompt estruturado que extrai:
- **Tema**: Categoria do problema (2-3 palavras)
- **Declaração do Problema**: O que está quebrado da perspectiva do usuário
- **Insight**: Razão mais profunda por trás da reclamação
- **Oportunidade**: Solução específica e construível
- **Critérios de Aceitação**: Como saber se foi implementado
- **Sinal de Prioridade**: Alto/Médio/Baixo impacto
- **Confiança**: Alto/Médio/Baixo na clareza do insight

### Validação de Oportunidades

Cada oportunidade é validada quanto a:
- **Viabilidade Técnica**: Pode ser construída?
- **Escopo**: Está dentro do escopo atual da app?
- **Novidade**: Já existe como feature?

### Agrupamento por Temas

As oportunidades são agrupadas automaticamente por temas similares usando IA.

### Backlog Priorizado

Cria uma lista priorizada baseada em:
- Frequência de menção
- Viabilidade das oportunidades
- Pontuação ponderada

## 📊 Saídas da Análise

### Arquivos Gerados
- `{app_name}_insights.json` - Insights estruturados
- `{app_name}_insights.csv` - Dados em formato tabular
- `{app_name}_backlog.csv` - Backlog priorizado

### Formatos de Saída
- **JSON**: Dados estruturados para processamento
- **CSV**: Planilhas para análise manual
- **Interface Web**: Visualização interativa no Streamlit

## 🔐 Configuração da API

### Obtendo Chave do Gemini

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova chave de API
3. Copie a chave para o arquivo `.env`

### Segurança
- Nunca commite a chave real no Git
- Use sempre variáveis de ambiente
- O `.gitignore` já está configurado para ignorar `.env`

## 🐛 Troubleshooting

### Problemas Comuns

**Erro de API Key:**
- Verifique se a chave está correta no `.env`
- Confirme se a API Gemini está habilitada

**Reviews não encontradas:**
- Verifique o package name da app
- Tente reduzir o número de reviews
- Mude os filtros de rating

**Erro de dependências:**
- Certifique-se de usar Python 3.8+
- Reinstale as dependências: `pip install -r requirements.txt`

### Debug Mode

Para mais detalhes durante a execução, observe o terminal onde o Streamlit está rodando.

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Áreas de Melhoria
- Suporte a mais stores (App Store, etc.)
- Análise de sentimento mais avançada
- Dashboard de métricas
- Integração com ferramentas de PM (Jira, Linear, etc.)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

- Google Gemini por fornecer a IA
- Google Play Scraper pela coleta de dados
- Streamlit pela interface web
- Comunidade Python pelos pacotes incríveis

---

**Desenvolvido com ❤️ para Product Managers que querem acelerar sua descoberta de produto.**
