# Guia de Git: commit seguro no `ibn-llm-framework`

Referência prática para usar Git no terminal do VS Code em
Windows/PowerShell.

## 1. Diferença entre `git add`, `git commit` e `git push`

``` text
Arquivos modificados -> git add -> git commit -> git push
                         seleciona   registra      publica no remoto
```

-   `git add`: prepara alterações para o próximo commit.
-   `git commit`: registra as alterações preparadas no histórico local.
-   `git push`: envia commits locais ao repositório remoto, como o
    GitHub.
-   Fazer commit **não** envia automaticamente as alterações ao GitHub.

## 2. Rotina recomendada

### Passo 1 --- Confira a pasta, branch e estado

``` powershell
git status
git branch --show-current
git log -5 --oneline
```

### Passo 2 --- Revise as alterações

``` powershell
git diff
```

Para um arquivo específico:

``` powershell
git diff -- caminho/do/arquivo.py
```

`git diff` mostra alterações ainda não preparadas. Arquivos novos
aparecem em `git status`, mas não no diff normal antes de serem
adicionados.

### Passo 3 --- Execute os testes relevantes

No projeto atual:

``` powershell
python -m pytest -v
```

Se houver falhas, investigue-as antes de considerar a mudança validada.

### Passo 4 --- Prepare os arquivos

Escolha uma das formas da seção seguinte.

### Passo 5 --- Confira o conteúdo que será commitado

``` powershell
git status
git diff --cached
git diff --cached --check
```

-   `git diff --cached` mostra exatamente o conteúdo preparado para o
    próximo commit.
-   `git diff --cached --check` verifica problemas comuns de espaços em
    branco.
-   Faça o commit apenas quando o diff preparado contiver as alterações
    pretendidas.

### Passo 6 --- Crie o commit

``` powershell
git commit -m "Mensagem curta e descritiva"
```

### Passo 7 --- Confirme o resultado

``` powershell
git status
git log -1 --oneline
```

### Passo 8 --- Publique, se desejado

``` powershell
git push
```

Antes de enviar, confirme que está na branch correta. Se o push for
recusado, investigue a divergência; não use `--force` como primeira
solução.

## 3. Commit de apenas um arquivo

Use quando quiser registrar um arquivo específico, mesmo que outros
estejam modificados.

Exemplo:

``` powershell
git status
git diff -- tests/test_topology.py
python -m pytest -v
git add tests/test_topology.py
git diff --cached -- tests/test_topology.py
git diff --cached --check
git status
git commit -m "Add topology domain tests"
git status
git log -1 --oneline
```

`git add tests/test_topology.py` prepara somente esse arquivo, exceto se
outras alterações já estivessem preparadas antes.

**Atenção:** o Git prepara o conteúdo do arquivo no momento do
`git add`. Se editar o arquivo depois, adicione-o novamente e revise o
diff preparado.

## 4. Commit de vários arquivos específicos

Use quando os arquivos fazem parte da mesma mudança lógica.

``` powershell
git status
git diff
python -m pytest -v
git add tests/test_topology.py docs/topology-domain.md
git diff --cached
git diff --cached --check
git status
git commit -m "Add topology domain tests and documentation"
git status
git log -1 --oneline
```

Substitua `docs/topology-domain.md` por um caminho real do seu
repositório. Para adicionar mais arquivos:

``` powershell
git add arquivo1.py arquivo2.py pasta/arquivo3.md
```

Agrupe arquivos que fazem parte da mesma mudança coerente, por exemplo
uma funcionalidade, seus testes e a documentação relacionada. Separe
alterações independentes em commits diferentes.

## 5. Preparar todas as alterações

``` powershell
git status
git add -A
git status
git diff --cached
git diff --cached --check
```

`git add -A` prepara todos os arquivos novos, modificados e removidos
detectados no repositório. Só use depois de revisar `git status`, porque
pode incluir mudanças que você não queria colocar no mesmo commit.

Se o conteúdo estiver correto:

``` powershell
git commit -m "Describe the complete change"
```

## 6. Preparar partes de um arquivo

Para selecionar blocos específicos de alterações:

``` powershell
git add -p caminho/do/arquivo.py
git diff --cached
git diff
git status
```

É uma opção mais avançada. Revise os blocos selecionados. O diff em
cache mostra o que será commitado; o diff normal mostra alterações ainda
não preparadas.

## 7. Boas mensagens de commit

Exemplos:

``` text
Add topology domain tests
Fix topology serialization validation
Document Git commit workflow
Add versioned synthetic topology scenarios
Refactor topology metadata handling
```

Prefira mensagens curtas, específicas e iniciadas por um verbo. Evite
mensagens vagas como `changes`, `update`, `fix` ou `final`. Uma mudança
lógica por commit facilita a revisão e a reversão.

## 8. Como interpretar `git status`

  -----------------------------------------------------------------------
  Estado                              Significado
  ----------------------------------- -----------------------------------
  `modified`                          Um arquivo acompanhado foi alterado

  `Untracked files`                   Arquivos novos ainda não
                                      acompanhados pelo Git

  `Changes to be committed`           Alterações preparadas para o
                                      próximo commit

  `Changes not staged for commit`     Alterações ainda não preparadas

  `deleted`                           Um arquivo acompanhado foi removido

  `working tree clean`                Não há alterações locais pendentes
                                      detectadas
  -----------------------------------------------------------------------

Um mesmo arquivo pode ter alterações preparadas e outras ainda não
preparadas. Por isso, confira `git status`, `git diff` e
`git diff --cached`.

## 9. Comandos relacionados

  -----------------------------------------------------------------------
  Comando                             Função
  ----------------------------------- -----------------------------------
  `git add`                           Prepara alterações

  `git commit`                        Registra as alterações preparadas
                                      localmente

  `git push`                          Envia commits ao repositório remoto

  `git pull`                          Busca e integra alterações remotas
                                      na branch atual

  `git fetch`                         Busca referências remotas sem
                                      integrá-las automaticamente

  `git diff`                          Mostra alterações não preparadas

  `git diff --cached`                 Mostra alterações preparadas

  `git status`                        Resume o estado atual

  `git log -5 --oneline`              Exibe os cinco commits mais
                                      recentes em formato compacto
  -----------------------------------------------------------------------

## 10. Corrigir erros comuns com segurança

### Preparei o arquivo errado, mas ainda não fiz commit

``` powershell
git restore --staged caminho/do/arquivo.py
```

Isso retira o arquivo da área de preparação sem apagar suas alterações
locais.

### Editei um arquivo depois do `git add`

``` powershell
git add caminho/do/arquivo.py
git diff --cached
```

Adicione novamente para atualizar o conteúdo preparado.

### Fiz commit, mas ainda não enviei

``` powershell
git status
git log -1 --oneline
git push
```

Confirme a branch e o commit antes de publicar.

### Quero descartar alterações locais

Cuidado: `git restore caminho/do/arquivo.py` pode descartar alterações
locais não commitadas. Não use comandos destrutivos sem conferir o que
será perdido.

## 11. Checklist antes de cada commit

-   [ ] Estou na pasta correta do projeto.
-   [ ] Confirmei a branch com `git branch --show-current`.
-   [ ] Revisei `git status`.
-   [ ] Inspecionei as alterações com `git diff`.
-   [ ] Executei os testes relevantes.
-   [ ] Adicionei somente os arquivos que pertencem a este commit.
-   [ ] Revisei `git diff --cached`.
-   [ ] Executei `git diff --cached --check`.
-   [ ] Escrevi uma mensagem específica.
-   [ ] Confirmei o resultado com `git log -1 --oneline`.
-   [ ] Executei `git push` se queria publicar o commit.

## 12. Modelo de rotina para o dia a dia

``` powershell
# 1. Conferir estado e branch
git status
git branch --show-current

# 2. Revisar alterações
git diff

# 3. Executar testes
python -m pytest -v

# 4. Preparar somente os arquivos relevantes
git add caminho/do/arquivo1.py caminho/do/arquivo2.py

# 5. Revisar o que entrará no commit
git diff --cached
git diff --cached --check
git status

# 6. Registrar
git commit -m "Describe the change"

# 7. Conferir
git status
git log -1 --oneline

# 8. Publicar, se desejado
git push
```

**Regra de ouro:** não confie apenas nos nomes dos arquivos. Antes de
executar `git commit`, confira o conteúdo de `git diff --cached` para
saber exatamente o que será registrado.
