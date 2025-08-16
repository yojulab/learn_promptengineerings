# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **prompt engineering learning platform** that combines AI multi-agent systems for document parsing and visualization. The project includes educational materials from Korea Tech University courses and multiple practical implementations including Streamlit UIs, PowerPoint generation, and document processing tools.

## Development Environment Setup

### Python Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Key dependencies include:
# - streamlit (for web UI)
# - python-pptx (for PowerPoint generation)
# - openai (for AI integration)
# - pandas, numpy (for data processing)
# - pytest, black, isort, pylint (for testing and code quality)
```

### Docker Environment
```bash
# Build and run with Docker Compose
cd dockers/
docker-compose up --build

# The container runs on port 80 (mapped from internal port 3005)
# Uses Node.js 24.2 with Python support
```

### Development Container
The project includes a `.devcontainer` setup with:
- Python 3.10 and Node.js LTS
- Pre-configured VS Code extensions (Python, Jupyter, GitHub Copilot)
- Automatic dependency installation
- Port forwarding for 8000, 8888

## Key Commands

### Running Applications
```bash
# Run main Streamlit application
streamlit run codes/app.py

# Run multi-model chat application  
streamlit run codes/app_multimodel_chats.py

# Generate PowerPoint from markdown
python codes/create_ppts/src/main.py
```

### Code Quality
```bash
# Format code
black codes/
isort codes/

# Lint code
pylint codes/

# Run tests
pytest
```

### Jupyter Notebooks
```bash
# Start Jupyter for educational materials
jupyter notebook codes/koreatech_univ/
```

## Architecture & Code Structure

### Multi-Agent Architecture
The project implements a **LangGraph-based multi-agent system** for document processing:

```
codes/
├── app.py                    # Main Streamlit UI with agent orchestration
├── agents/                   # Multi-agent components
│   ├── parser_agent.py      # MCP server selection and parsing
│   ├── log_agent.py         # Progress logging
│   └── render_agent.py      # HTML result rendering
├── services/                 # External integrations
│   ├── ollama_client.py     # Ollama AI model interface
│   └── mcp_client.py        # MCP server communication
└── utils/                   # Shared utilities
    ├── file_utils.py        # File processing
    └── prompt_utils.py      # Prompt manipulation
```

### Core Workflow
1. **Prompt Analysis**: System analyzes user prompts to determine appropriate MCP servers
2. **Multi-Agent Coordination**: Agents coordinate to parse documents (PDF, Excel, Word, HWP)
3. **HTML Rendering**: Results are converted to HTML for display in Streamlit canvas
4. **Real-time Logging**: Progress tracking through dedicated log agent

### Document Processing Pipeline
- **Input**: Multi-file upload support (PDF, Excel, Word, HWP)
- **Processing**: MCP server selection based on file type and user prompts
- **Output**: HTML visualization in Streamlit canvas with real-time progress logs

### Educational Components
- **Korea Tech University Materials**: Comprehensive prompt engineering curriculum
  - Day 1: LLM evolution, prompt basics, structural design
  - Day 2: Specialized prompts, evaluation, optimization
- **Jupyter Notebooks**: Interactive exercises and practical implementations
- **PDF to Excel Conversion**: Automated curriculum processing tools

### PowerPoint Generation System
- **Input**: Markdown content files
- **Processing**: Template-based slide generation using python-pptx
- **Output**: Formatted PowerPoint presentations
- **Features**: Auto-layouts, image insertion, content structuring

## File Processing Patterns

### MCP Server Integration
The system uses Model Context Protocol (MCP) servers for specialized document processing:
- `pdf`: PDF document parsing
- `excel`: Spreadsheet processing  
- `doc`: Word document handling
- `hwp`: Korean HWP file support

### Agent Communication
Agents communicate through a structured workflow:
1. **Log Agent**: Maintains processing state and user feedback
2. **Parser Agent**: Routes to appropriate MCP servers based on content analysis
3. **Render Agent**: Transforms parsed content to HTML for display

## Development Patterns

### Streamlit UI Architecture
- **Sidebar**: AI model and MCP server selection with multi-select widgets
- **Main Area**: Prompt input (system/user), file upload, progress logs
- **Canvas**: Real-time HTML result display with scroll support

### Error Handling
- Graceful degradation when MCP servers are unavailable
- Comprehensive logging for debugging multi-agent interactions
- File validation before processing

### Testing Strategy
- Use pytest for unit testing agent components
- Test document processing pipelines with sample files in `koreatech_univ/` directory
- Validate PowerPoint generation with markdown fixtures

## Integration Points

### AI Model Integration
- **Ollama Server**: Local AI model hosting (gemma3:1b, qwen3:1.7b)
- **OpenAI API**: External AI service integration
- **Multi-Model Support**: Concurrent model execution for comparison

### External Services
- **MCP Servers**: Document-specific processing services
- **Docker Integration**: Containerized deployment with GitHub PAT authentication
- **DevContainer**: VS Code development environment with pre-configured tools

## Educational Use Cases

This codebase serves as both a functional tool and educational resource for:
- **Prompt Engineering Techniques**: Structured prompt design and evaluation
- **Multi-Agent Systems**: Practical implementation of agent coordination
- **Document Processing**: Automated parsing and transformation workflows
- **AI Integration**: Multiple AI model orchestration and comparison