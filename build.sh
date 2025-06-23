#!/bin/bash
# Script de build para o Render

echo "Instalando dependências..."

# Instalar dependências usando a versão do Python especificada no runtime.txt
pip install --no-cache-dir -r requirements.txt

echo "Configuração concluída!"

