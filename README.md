# SISTEMA-WEB

> Projeto para construir, evoluir e operar uma aplicação web real, alojada no servidor Ubuntu do projeto, acessível por navegador e versionada no GitHub.

## 1. Visão do projeto

O **SISTEMA-WEB** será a base de uma aplicação web própria. O objetivo é sair de uma ideia/documentação inicial para um sistema funcional, com implantação controlada no servidor Ubuntu, acesso pela rede e evolução rastreável por meio deste repositório.

O GitHub será a fonte de verdade do código e da documentação. O servidor Ubuntu será o ambiente de execução da aplicação. Essas responsabilidades devem permanecer separadas: o repositório guarda o estado versionado; o servidor executa uma versão implantada.

## 2. Objetivos

- Desenvolver uma aplicação web organizada, modular e sustentável.
- Disponibilizar a interface através de um navegador, em computadores e dispositivos móveis.
- Hospedar a aplicação no servidor Ubuntu já utilizado no laboratório.
- Manter código, configuração de exemplo e documentação sob controlo de versão.
- Automatizar, progressivamente, validações, testes e implantação.
- Integrar a aplicação aos serviços de infraestrutura do laboratório apenas quando existir uma necessidade técnica definida.
- Priorizar segurança, rastreabilidade, disponibilidade e facilidade de manutenção.

## 3. Contexto de infraestrutura

O ambiente de referência é o servidor Ubuntu do laboratório do projeto, que também serve de base a iniciativas de infraestrutura e monitorização.

**Diretrizes de arquitetura:**

1. **Servidor Ubuntu:** ambiente de execução e alojamento.
2. **Aplicação web:** serviço independente, com responsabilidades e dependências documentadas.
3. **Acesso HTTP/HTTPS:** publicação através de um servidor web ou proxy reverso, com TLS quando o serviço for exposto.
4. **Persistência:** escolher a tecnologia de base de dados somente após definir os dados, o modelo de domínio e os requisitos de consistência.
5. **GitHub:** histórico de código, documentação, revisão de alterações e eventual pipeline CI/CD.
6. **Monitorização:** integrar métricas, logs e alertas com a infraestrutura de monitorização existente quando os endpoints e os indicadores estiverem definidos.

> Os itens acima representam diretrizes e decisões de arquitetura. Não significam que esses componentes já estejam instalados, configurados ou operacionais para esta aplicação.

## 4. Arquitetura lógica de referência

```text
                    UTILIZADOR
                        |
                  Navegador Web
                        |
                   HTTPS / TLS
                        |
                Proxy reverso / Web
                        |
                 Aplicação SISTEMA-WEB
                        |
              +---------+---------+
              |                   |
          Persistência       Serviços externos
          (a definir)        (quando necessários)

                        |
                 Logs e métricas
                        |
              Monitorização (futura
                integração validada)

DESENVOLVIMENTO E ENTREGA
        Repositório GitHub
                |
       Revisão + validação
                |
       Pipeline CI/CD (fase futura)
                |
        Implantação controlada
                |
          Servidor Ubuntu
```

A arquitetura é intencionalmente lógica e agnóstica quanto à stack. A escolha de framework, linguagem, base de dados e método de implantação deve ocorrer após requisitos funcionais e não funcionais mínimos.

## 5. Princípios técnicos

- **Separação de responsabilidades:** aplicação, proxy, dados, monitorização e entrega não devem ser acoplados sem necessidade.
- **Configuração externa:** credenciais, tokens e parâmetros por ambiente não devem ser incorporados ao código.
- **Segredos protegidos:** nunca versionar ficheiros reais de ambiente, chaves privadas, palavras-passe ou tokens.
- **Reprodutibilidade:** documentar versões, dependências, comandos e pré-requisitos de instalação.
- **Segurança por padrão:** princípio do menor privilégio, atualizações controladas, validação de entradas e exposição mínima de portas.
- **Observabilidade:** prever logs estruturados, health checks e métricas úteis, sem expor dados sensíveis.
- **Alterações reversíveis:** toda implantação deve permitir identificar a versão publicada e definir um procedimento de rollback.
- **Documentação sincronizada:** alterações relevantes na arquitetura ou operação devem refletir-se neste repositório.

## 6. Organização inicial recomendada

A estrutura será criada progressivamente, conforme os componentes reais forem implementados.

```text
SISTEMA-WEB/
├── README.md
├── LICENSE
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── INSTALLATION.md
│   └── OPERATIONS.md
├── src/
├── tests/
├── deploy/
├── scripts/
├── .github/
│   └── workflows/
└── .gitignore
```

Não criar diretórios vazios apenas para reproduzir este desenho. Cada pasta deve corresponder a código, documentação ou automação efetivamente existente.

## 7. Segurança e gestão de configuração

- Manter um ficheiro de exemplo, como `.env.example`, apenas com nomes de variáveis e valores fictícios.
- Manter `.env`, credenciais, certificados privados, dumps de bases de dados e ficheiros locais fora do Git.
- Definir utilizador de sistema próprio para executar a aplicação, sem privilégios administrativos.
- Restringir portas e acessos de rede ao estritamente necessário.
- Usar HTTPS em qualquer publicação que transporte autenticação ou dados sensíveis.
- Registar alterações operacionais e manter cópias de segurança testáveis.
- Não assumir que uma aplicação está segura apenas porque está atrás de um proxy reverso.

## 8. Fluxo de desenvolvimento e implantação

1. Definir requisitos e critérios de aceitação.
2. Selecionar a stack com base nos requisitos, capacidade do servidor e manutenção a longo prazo.
3. Implementar localmente e versionar alterações em commits pequenos e descritivos.
4. Executar testes e validações antes da integração na branch principal.
5. Preparar configuração específica do ambiente Ubuntu sem incluir segredos no repositório.
6. Implantar uma versão identificável e verificar saúde, logs e acesso.
7. Documentar o resultado, limitações conhecidas e procedimento de reversão.

A implantação inicial deve ser manual e controlada. A automação CI/CD será introduzida depois de existirem testes, estratégia de configuração e procedimento de rollback confiáveis.

## 9. Roadmap inicial

| Fase | Entrega | Critério de conclusão |
|---|---|---|
| 0 — Reconhecimento | Inventário do servidor e decisões iniciais | Recursos, rede, domínio e restrições documentados |
| 1 — Requisitos | Escopo funcional e não funcional | Requisitos e critérios de aceitação aprovados |
| 2 — Fundação | Stack, estrutura do projeto e ambiente de desenvolvimento | Aplicação mínima executável e versionada |
| 3 — Primeiro deploy | Publicação no Ubuntu | Acesso validado, logs disponíveis e rollback documentado |
| 4 — Qualidade | Testes, segurança e observabilidade | Verificações automatizadas e health checks funcionais |
| 5 — Evolução | CI/CD e integrações | Pipeline validado e integrações documentadas |

As fases não devem ser consideradas concluídas apenas pela criação de documentação. Cada conclusão exige evidência verificável.

## 10. Estado atual do repositório

Na data desta atualização, o reconhecimento do repositório identificou:

- Repositório público: `carlos-andrade/SISTEMA-WEB`.
- Branch principal: `main`.
- Licença identificada: MIT.
- Conteúdo inicial: `README.md` e `LICENSE`.
- Aplicação, stack, base de dados, pipeline e implantação: **ainda não comprovadas neste repositório**.

Este estado é a linha de base documental. O README deverá ser atualizado à medida que os componentes forem efetivamente implementados e validados.

## 11. Próximas ações técnicas

1. Inventariar o servidor Ubuntu: versão, CPU, RAM, armazenamento, interfaces de rede e serviços já ativos.
2. Definir a finalidade funcional da aplicação e os seus utilizadores.
3. Escolher a stack e o modelo de execução (serviço nativo ou contentores), justificando a decisão.
4. Definir domínio, DNS, política de acesso e terminação TLS.
5. Criar o esqueleto executável, testes mínimos e configuração segura.
6. Realizar o primeiro deploy com verificação e plano de rollback.

## 12. Governança do repositório

- A branch `main` deve representar estado integrado e validado.
- Alterações relevantes devem ter commits claros e escopo limitado.
- Quando o trabalho justificar revisão, utilizar branches e pull requests.
- Não registar no README passwords, tokens, endereços privados desnecessários ou outros segredos.
- Atualizar este documento quando decisões de arquitetura mudarem.
- Distinguir sempre entre **planeado**, **em desenvolvimento**, **implementado** e **validado**.

---

**Princípio orientador:** primeiro definir e verificar; depois implementar; por fim, automatizar. O objetivo não é apenas colocar uma página no ar, mas construir um sistema web operacional, seguro, documentado e sustentável.
