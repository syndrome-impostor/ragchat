# Chatbot
Customizable RAG chatbot for security research, consisting of: 
- Web scraper
- Vector DB ingest pipeline (chunking, embedding, storage)
- Chat interface

I have only tested this on Arch Linux with an AMD GPU, but designed it to be easily portable to other systems.


Primary technologies:
- Embeddings: Instructor-xl
- Vector search: ChromaDB
- LLM: Anthropic (API key required)
- Text processing: NLTK

Design choices:
- Python venv for system isolation/portability
- Multimodal web scraper, using Selenium for websites with a JS challenge (configure JS sites in `config.yaml`)

System requirements:
- Python 3
Scraper:
- Chrome(ish) browser for selenium


# Usage
This implementation provides:
1. Basic HTML/md/txt processing
2. Chunking, embedding, and storage pipeline
3. ChromaDB storage for vector search
4. Chat interface (CLI for now)

Quickstart:
1. In the project root, create a `urls.txt` and `.env` file (example files provided)
    a. `urls.txt` should contain a newline separated list of URLs to be scraped
    b. `.env` should contain: `ANTHROPIC_API_KEY=<your_api_key>`
2. Configure your GPU type in `config.yaml`
3. `./run.sh scrape` to scrape documents
4. `./run.sh ingest` to ingest documents into ChromaDB
5. `./run.sh chat` to start a chat session

# Troubleshooting
- To check if documents are being ingested, run `./run.sh query` to query the vector database
- For issues with documents, delete the `data/` directory and re-run the scrape step
- For issues with python configuration, delete the `venv/` directory. It will be re-created when you run `./run.sh`

# GPU acceleration
## Required config
- For GPU acceleration, user needs to be in the video and render groups (usermod -aG video,render $USER)

To test if python is able to use GPU acceleration:
`./test_gpu.sh`

## Required software packages for AMD GPUs (ROCm)
- rocm
- rocm-hip-sdk 
- rocm-hip-runtime


---

# License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.