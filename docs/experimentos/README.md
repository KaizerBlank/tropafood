# Reprodução dos experimentos

Os arquivos `saidas/resultados_consultas.csv` e `saidas/tempos_brutos.csv` contêm os resultados consolidados e as 25 medições. Os JSONs `C1_resultados.json` a `C5_resultados.json` registram os IDs, as distâncias geográficas e viárias e os tempos exibidos. As frotas utilizadas estão preservadas em JSON compactado com gzip. Os comprimentos viários registrados têm a precisão exibida pela aplicação, de uma casa decimal.

`codigo_execucao.json` registra o commit e os hashes SHA-256 dos arquivos utilizados. `saidas/ambiente.json` identifica o ambiente desta execução. Ao reproduzir em outro computador, atualize a descrição do host no script de medição; ela descreve o Mac desta execução, não é uma detecção automática do computador hospedeiro.

Na raiz do projeto, com a imagem `tropafood-app` já construída e a malha `data/malha_bh_drive_31983.graphml` já disponível, execute:

```sh
docker run --rm --network none \
  --mount "type=bind,source=$PWD,target=/app,readonly" \
  --mount "type=bind,source=$PWD/docs/experimentos,target=/experimento" \
  --workdir /app \
  -e PYTHONDONTWRITEBYTECODE=1 \
  tropafood-app python -B /experimento/medir.py
```

O comando grava novamente os resultados em `saidas/`. A geração usa a semente `20261020 + N` e desvio padrão de 500 metros. Cada consulta tem uma execução de aquecimento e cinco repetições medidas, com os mesmos entregadores. O script verifica a estabilidade dos resultados e registra separadamente o processamento dos callbacks de mapa/resumo e tabela/rotas.

O total medido corresponde a dois pedidos locais executados em sequência pelo cliente de teste do Flask, incluindo a serialização. Não mede rede, carregamento da cartografia nem renderização no navegador. Os callbacks da interface podem executar em paralelo, de modo que o total sequencial não deve ser apresentado como latência visual da página.

Para reproduzir as frotas das imagens em uma instância separada da interface:

```sh
docker run --rm -p 127.0.0.1:8051:8051 \
  --mount "type=bind,source=$PWD,target=/app,readonly" \
  --mount "type=bind,source=$PWD/docs/experimentos,target=/experimento,readonly" \
  --workdir /app \
  -e PYTHONDONTWRITEBYTECODE=1 \
  tropafood-app python -B /experimento/servidor_figuras.py
```

Abra `http://localhost:8051/`, mantenha a opção de salvar CSVs desmarcada e gere 1.000 ou 5.000 entregadores. A semente é fixada somente nesse processo de documentação. A aplicação principal permanece com sua geração habitual.

Os cenários são:

| Caso | Frota | Restaurante | Índice na base | Raio (m) |
| --- | ---: | --- | ---: | ---: |
| C1 | 1.000 | NECTAR DA SERRA LTDA | 3 | 1.000 |
| C2 | 5.000 | NECTAR DA SERRA LTDA | 3 | 1.000 |
| C3 | 5.000 | NECTAR DA SERRA LTDA | 3 | 2.000 |
| C4 | 5.000 | BAR E CAFE DONATELO LTDA | 0 | 2.000 |
| C5 | 5.000 | NECTAR DA SERRA LTDA | 3 | 100 |

Os valores variam se a base, a malha, as bibliotecas ou o código forem alterados. A semente permite repetir a geração no mesmo ambiente; os tempos dependem da máquina e da carga de execução.
