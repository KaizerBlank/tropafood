# TP1 - ALG II - 2026/02

### INTEGRANTES

- **Marney Santos de Melo - 2024106034**
- **Rafael Resende Miranda - 2024065990**
- **Victor Murilo Kaizer - 2024096551**

# Como rodar?

- Tenha o docker instalado
- Na pasta raíz do projeto, no terminal rode: 
    - Construa a imagem no Docker: `docker build -t tropafood .` Isso pode levar vários minutos, minha primeira vez levou cerca de 600 segundos...
    - Execute o container: `docker run -p 8050:8050 tropafood`

- Caso seja feita alguma mudança e queira atualizar a execução: `docker run -p 8050:8050 -v ${PWD}:/app tropafood-app`
