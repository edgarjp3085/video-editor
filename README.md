# 🎬 Editor de Vídeo Kwai - Interface Gráfica

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Uma interface gráfica moderna e intuitiva para editar vídeos automaticamente para o Kwai, com geração de títulos por IA e efeitos anti-plágio.

## ✨ Principais Funcionalidades

- 🤖 **Geração automática de títulos** usando Google Gemini AI
- 🎯 **Interface gráfica moderna** com Tkinter
- 🔒 **Efeitos anti-plágio** sutis e eficazes
- 🎵 **Preservação do áudio original**
- 📱 **Formato otimizado para Kwai** (720x1280)
- 🎨 **Backgrounds personalizáveis**
- 💾 **Configurações salvas automaticamente**
- 📊 **Monitoramento em tempo real** do progresso

## 🖼️ Screenshots

### Interface Principal
```
<img width="837" height="638" alt="image" src="https://github.com/user-attachments/assets/65ddc236-447f-4e18-988f-fd5615686ba6" />

```

## 🚀 Instalação Rápida

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/video-editor.git
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Instale o FFmpeg
- **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html)
- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`

### 4. Execute o programa
```bash
python make.py
```

## 📋 Requisitos

### Sistema
- Python 3.8+
- FFmpeg (para processamento de áudio)
- 4GB RAM recomendado
- Espaço em disco para vídeos processados

### Dependências Python
- `opencv-python>=4.8.0` - Processamento de vídeo
- `Pillow>=10.0.0` - Manipulação de imagens  
- `google-generativeai>=0.3.0` - IA para títulos
- `SpeechRecognition>=3.10.0` - Transcrição
- `pydub>=0.25.1` - Processamento de áudio
- `numpy>=1.24.0` - Operações matemáticas
- `tqdm>=4.65.0` - Barras de progresso

## 🔑 Configuração da API

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API Key do Google Gemini
3. Cole a chave na interface do programa
4. A configuração será salva automaticamente

## 📁 Estrutura do Projeto

```
editor-video-kwai/
├── video_editor_gui.py          # Interface principal
├── requirements.txt             # Dependências
├── README.md                   # Este arquivo
├── INSTALAÇÃO.md              # Guia detalhado
├── LICENSE                    # Licença MIT
├── .gitignore                # Arquivos ignorados
├── videos_originais/         # Seus vídeos (criar)
├── videos_editados/          # Vídeos processados
├── backgrounds/              # Backgrounds personalizados
└── video_editor_config.json # Configurações (auto)
```

## 🎯 Como Usar

### 1. Preparação
- Coloque seus vídeos na pasta `videos_originais/`
- Adicione backgrounds personalizados em `backgrounds/` (opcional)
- Configure sua API Key do Google

### 2. Configuração
- Abra a aba "⚙️ Configurações"
- Defina as pastas de entrada e saída
- Escolha opções desejadas (título, posição, efeitos)

### 3. Processamento
- Vá para "🎥 Processar Vídeos"
- Clique em "🎬 Processar Vídeos"
- Acompanhe o progresso na aba "📋 Log"

### 4. Resultado
- Vídeos editados aparecerão em `videos_editados/`
- Prontos para upload no Kwai!

## 🛠️ Funcionalidades Técnicas

### Processamento de Vídeo
- ✅ Redimensionamento inteligente
- ✅ Crop automático para 9:16
- ✅ Preservação da qualidade
- ✅ Efeitos anti-plágio sutis

### Geração de Títulos
- 🤖 IA analisa áudio e contexto
- 🎯 Títulos otimizados para engajamento
- 📝 Fallback para títulos manuais
- 🇧🇷 Suporte completo ao português

### Interface
- 🎨 Tema escuro moderno
- 📊 Progresso em tempo real  
- 💾 Configurações persistentes
- 🔄 Processamento assíncrono

## 🐛 Solução de Problemas

### Erro comum: "FFmpeg not found"
```bash
# Windows - Adicione ao PATH
set PATH=%PATH%;C:\ffmpeg\bin

# Ou instale via package manager
choco install ffmpeg  # Chocolatey
```

### Erro: "API Key inválida"
- Verifique se copiou a chave completa
- Certifique-se de que a API Gemini está habilitada
- Confirme se há créditos na conta Google

### Performance lenta
- Feche outros programas pesados
- Use vídeos menores para teste
- Verifique espaço em disco disponível

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Changelog

### v1.0.0 (2025-01-XX)
- ✨ Interface gráfica completa
- 🤖 Integração com Google Gemini AI
- 🔒 Sistema anti-plágio
- 💾 Configurações persistentes
- 📊 Monitoramento de progresso

## 🙏 Agradecimentos

- Google Gemini AI pela geração de títulos
- OpenCV pela biblioteca de processamento de vídeo
- Comunidade Python pelas excelentes bibliotecas

## 📞 Suporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/SEU_USUARIO/editor-video-kwai/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/SEU_USUARIO/editor-video-kwai/discussions)
- 📧 **Email**: edgar.solin@gmail.com

---

<p align="center">
  <b>⭐ Se este projeto te ajudou, dê uma estrela!</b><br>
  <sub>Feito com ❤️ para a comunidade de criadores de conteúdo</sub>
</p>
