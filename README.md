# OnD-AI-samples: On-Device AI Sample Projects

![Repo Banner](./assets/CoryLabScene-Small.png)

A collection of sample projects demonstrating on-device AI capabilities across different applications, from computer vision to natural language processing. These samples run locally on Windows machines without requiring cloud services (after initial model download).

## 🧩 Sample Projects

### 📊 LLM Benchmarking Tool
[`/bench`](/bench) - A menu-driven CLI tool for benchmarking local LLM models.
- Compare models based on metrics like token counts, response time, and hardware utilization
- Supports Foundry Local models with GPU/CPU/NPU acceleration
- Save and analyze benchmark results for performance comparisons
- [View detailed README](/bench/README.md)

### 🖼️ Background Remover
[`/samples/image-edit`](/samples/image-edit) - Desktop app that removes image backgrounds entirely on-device.
- Uses ONNX Runtime with DirectML for GPU acceleration when available
- Simple UI for loading, processing, and saving images
- Supports multiple segmentation models (u2netp, isnet-general-use)
- [View detailed README](/samples/image-edit/README.md)

### 🏷️ Image Classifier
[`/samples/image-classify`](/samples/image-classify) - Image classification with local ONNX models.
- Includes normalization pipeline for preparing image datasets
- Runs MobileNetV2 or ResNet50 ONNX classifiers trained on ImageNet
- DirectML support for GPU acceleration on Windows
- [View detailed README](/samples/image-classify/README.md)

### 🎙️ Live Captions
[`/samples/speech`](/samples/speech) - Real-time speech transcription with a professional terminal UI.
- Uses OpenAI Whisper models running entirely locally
- Sophisticated Rich-based terminal interface with VU meters
- Voice Activity Detection for smart utterance segmentation
- [View detailed README](/samples/speech/README.md)

### 🏗️ Next.js Sample
[`/samples/folder-structure`](/samples/folder-structure) - Basic Next.js project structure for web applications.
- Starting point for web-based AI applications
- [View detailed README](/samples/folder-structure/README.md)

## 🚀 Getting Started

Each sample project contains its own README with specific instructions, but most follow a similar setup pattern:

1. **Prerequisites**
   - Windows 10/11
   - Python 3.9+ (for Python projects)
   - Node.js/npm (for web projects)
   - Optional: GPU with DirectML support for acceleration

2. **Common Setup (Python projects)**
   ```powershell
   cd <project-directory>
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Run the Sample**
   - Each sample has specific run instructions in its README

## ⚡ Quick Start Scripts

For convenience, the repository includes PowerShell scripts to quickly set up and run specific samples:

### Background Remover (`run-image-edit.ps1`)

This script sets up and runs the Background Remover app with a single command:

```powershell
# Run in GUI mode
.\run-image-edit.ps1

# Run in CLI mode
.\run-image-edit.ps1 -infile "path\to\image.jpg" -outfile "path\to\output.png" -model "u2netp"

# Run with GPU acceleration explicitly enabled
.\run-image-edit.ps1 -gpu
```

**Features:**
- Automatically creates and activates a virtual environment
- Installs all dependencies
- Checks system prerequisites (Windows, Python version)
- Supports both GUI and CLI modes
- Allows model selection and GPU acceleration

### Live Captions (`run-speech.ps1`)

Launch the Live Captions application with all dependencies automatically configured:

```powershell
.\run-speech.ps1
```

**Features:**
- Automatically creates and activates a virtual environment
- Installs required packages for speech recognition
- Verifies system compatibility
- Launches the Rich UI-based terminal interface

Each script handles environment setup, dependency installation, and proper error checking to ensure a smooth experience for users new to the samples.

## 🧠 Supported AI Capabilities

- **Computer Vision**: Image classification, background removal, object detection
- **Natural Language Processing**: LLM benchmarking, inference
- **Speech**: Real-time transcription, voice activity detection
- **Hardware Acceleration**: DirectML (GPU), CPU optimization, NPU support

## 📚 Resources

- [Foundry Local Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started) - For running local LLMs
- [ONNX Runtime Documentation](https://onnxruntime.ai/) - For model inference
- [DirectML Documentation](https://learn.microsoft.com/en-us/windows/ai/directml/dml) - For GPU acceleration on Windows
- [Python Documentation](https://docs.python.org/3/) - Core language used in most samples
- [Whisper Models](https://github.com/openai/whisper) - Speech recognition used in Live Captions sample

## 📋 Repository Structure

```
OnD-AI-samples/
├── bench/               # LLM benchmarking tool
├── samples/
│   ├── image-edit/      # Background removal app
│   ├── image-classify/  # Image classification app with normalization pipeline
│   ├── speech/          # Live captions app
│   └── folder-structure/ # Next.js sample
├── run-image-edit.ps1   # Quick start script for background remover
├── run-speech.ps1       # Quick start script for live captions
├── .gitignore
└── README.md
```

## 📝 TODO

The following improvements are planned for this repository:

1. **Quick Run Scripts**
   - [ ] Create `run-image-classify.ps1` for the Image Classifier sample
   - [ ] Create `run-bench.ps1` for the LLM Benchmarking tool
   - [ ] Add a unified `run.ps1` that presents a menu of all samples

2. **Documentation**
   - [ ] Add architecture diagrams for each sample showing data flow
   - [ ] Create tutorial videos demonstrating each sample
   - [ ] Add troubleshooting guides for common issues

3. **Features**
   - [ ] Add Docker support for containerized deployment
   - [ ] Implement cross-platform compatibility (Linux/macOS)
   - [ ] Add more examples of hardware acceleration options

## 🤝 Contributing

We welcome contributions to this repository! Here's how you can help:

### Types of Contributions

- **Bug fixes**: If you find any issues with the samples, please submit a fix
- **Feature enhancements**: Add new capabilities to existing samples
- **New samples**: Contribute entirely new AI sample projects
- **Documentation**: Improve READMEs, add tutorials, or create diagrams
- **Performance optimizations**: Enhance model inference or processing speed

### Contribution Process

1. **Fork the repository**
   - Create your own fork of the repository to work on changes

2. **Create a branch**
   ```powershell
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style and project structure
   - Add appropriate documentation and comments
   - Ensure all samples have proper README files

4. **Test your changes**
   - Verify that your changes work as expected
   - Test on different hardware configurations if possible

5. **Submit a pull request**
   - Provide a clear description of what your changes accomplish
   - Link to any related issues

### Code Style Guidelines

- Use descriptive variable and function names
- Include comments explaining complex logic
- Follow PEP 8 for Python code
- Keep individual samples focused on demonstrating specific AI capabilities

## ⚖️ License

See the [LICENSE](LICENSE) file for details.
