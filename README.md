# Interview Trainer AI 🚀

O **Interview Trainer AI** é uma plataforma SaaS desenvolvida para ajudar profissionais a dominarem entrevistas de emprego através de simulações realistas e feedback inteligente em tempo real.

## 🎯 Objetivo

Transformar o nervosismo da entrevista em confiança. Utilizando inteligência artificial para simular entrevistadores rigorosos, nossa ferramenta analisa não apenas o conteúdo, mas a clareza e o ritmo da comunicação do usuário.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python (Flask)
* **Frontend:** HTML5, CSS3, JavaScript (ES6 Modules)
* **IA & NLP:** OpenAI API (GPT-4o, Whisper)
* **Banco de Dados:** SQLite
* **Análise:** Pandas (Métricas de fala)

## ✨ Funcionalidades Principais

* **Simulação em Tempo Real:** IA que interage como um recrutador sênior.
* **Modo de Pressão:** Entrevistas cronometradas para simular cenários reais.
* **Feedback Estruturado:** Análise de pontos fortes, fracos e sugestões de melhoria.
* **Análise de Comunicação:** Detecção de vícios de linguagem e clareza da fala.
* **Personalização:** Upload de currículo para perguntas baseadas em experiência real.

## 🏗️ Arquitetura do Sistema

O sistema é organizado de forma modular para facilitar a escalabilidade e manutenção:

## 🚀 Como Executar o Projeto

### Pré-requisitos

* Python 3.10+
* [FFmpeg](https://ffmpeg.org/) instalado no sistema (para processamento de áudio).
* Uma chave de API da OpenAI válida.

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/interview-trainer-ai.git
cd interview-trainer-ai

```


2. Instale as dependências:
```bash
pip install -r requirements.txt

```


3. Configure o arquivo `.env` na raiz com suas chaves:
```env
OPENAI_API_KEY=sua_chave_aqui
SECRET_KEY=sua_chave_secreta

```


4. Inicie o servidor:
```bash
python main.py

```



## 📜 Documentação

Para detalhes técnicos, consulte a pasta `/docs`:

* [Arquitetura](https://www.google.com/search?q=docs/architecture.md)
* [API Documentation](https://www.google.com/search?q=docs/api-docs.md)
* [Prompts Engineering](https://www.google.com/search?q=docs/prompts.md)

---

*Desenvolvido com foco em alta performance e experiência do usuário.*

