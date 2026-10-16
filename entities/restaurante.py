class Restaurante:
    def __init__(self, id, cnae, desc_cnae, desc_logradouro, nome_logradouro, numero, complemento, nome_bairro, nome, nome_fantasia):
        self.id = id
        self.cnae = cnae
        self.desc_cnae = desc_cnae
        self.endereco = desc_logradouro + ' ' + nome_logradouro + ',' + numero + '-' + nome_bairro
        self.complemento = complemento
        self.nome = nome
        self.nome_fantasia = nome_fantasia