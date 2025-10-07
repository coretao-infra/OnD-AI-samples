<p align="center">
	<img src="../../assets/CoryLabScene-Small.png" alt="Project Banner" width="400" />
</p>

# Folder Structure Foundry Local Example

**Explore, analyze, and summarize your local file system using Microsoft Foundry Local AI models.**

This interactive Next.js app lets you:
- Enter any directory path on your machine
- Instantly list all files and folders (recursively)
- Select which cached Foundry Local model to use for analysis
- Generate a rich, AI-powered report on the file structure, types, and context

All AI runs are local—no cloud calls, no data leaves your device.



## Getting Started

### Requirements
- Node.js 18+
- Foundry Local installed and running (see [Foundry Local docs](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/overview))
- At least one model cached locally (run `foundry cache list`)

### How to run
1. Install dependencies:
	```bash
	npm install
	```
2. Start the dev server:
	```bash
	npm run dev
	```
3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features
- **File Explorer UI:** Enter a path, browse files/folders, see instant results
- **Model Selection:** Choose from your locally cached Foundry models (CPU/GPU/NPU)
- **AI Report Generation:** Get a detailed, structured summary of your file tree
- **Performance Metrics:** See prompt size, model info, response size, and throughput
- **Markdown Rendering:** Beautiful, readable output with tables, lists, and code blocks


---

## Learn More

- [Next.js Documentation](https://nextjs.org/docs) — framework powering the UI
- [Foundry Local SDK Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/sdk-reference) — manage, cache, and run local AI models
- [Foundry Local CLI Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/cli-reference) — command-line tools for model management

## Contributing / TODO
- Add dropdown for cached model selection
- Show model details (context window, token limits)
- Improve response summary formatting
- Add prompt customization fields
- Expand documentation and usage examples