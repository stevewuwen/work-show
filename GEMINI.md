# Project Context: work-show

## Project Overview
`work-show` is a Python-based recruitment information acquisition and visualization tool. Its primary function is to crawl job postings from various platforms (e.g., Bytedance Campus, Kuaishou Social), process the data (optionally using LLMs for extraction), and store it in a local SQLite database.

## Architecture
The project follows a modular architecture:
- **Engine (`src/work_show/engine/crawler.py`):** The core `CrawlerEngine` orchestrates the crawling process, handling fetching, deduplication, and storage. It supports running multiple sources in parallel using threading.
- **Sources (`src/work_show/sources/`):**  Each job platform is implemented as a separate source class (e.g., `WebByteDanceCampusSource`) adhering to the `DataSource` protocol. These classes handle the specific logic for fetching data from their respective websites.
- **Storage (`src/work_show/storage/`):** `SqliteStorage` provides persistence, saving job data to a SQLite database.
- **Deduplication (`src/work_show/deduplicator/`):** Prevents processing of duplicate job postings using strategies like `SetDeduplicator`.
- **Utils (`src/work_show/utils/`):**  Includes utilities for logging and LLM integration (`call_llm.py`) for extracting structured data from unstructured job descriptions.

## Building and Running

### Prerequisites
- Python >= 3.12
- `uv` (project manager)

### Installation
1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

### Configuration
1.  **Create Configuration File:**
    Copy the example configuration to `config/settings.yaml`.
    ```bash
    cp config/settings.yaml.example config/settings.yaml
    ```
2.  **Edit `config/settings.yaml`:**
    -   Configure the database URL.
    -   Set LLM API keys (`gemini_api_key`, `deepseek_api_key`) if using LLM features.
    -   Enable/Disable specific sources under the `sources` section.

### Running the Crawler
Execute the main script to start the crawling process:
```bash
python main.py
```
This will start threads for each configured source and save data to the specified SQLite database.

## Development Conventions

### Code Structure
-   **`src/work_show/`**: Main package containing all source code.
-   **`config/`**: Configuration files.
-   **`test/`**: Unit tests.

### Key Patterns
-   **Protocols:** The project uses Python `Protocol` (in `core/protocols.py`) to define interfaces for `DataSource`, `DataStorage`, etc., ensuring loose coupling.
-   **Dependency Injection:** `CrawlerEngine` receives its dependencies (source, storage, deduplicator) via its constructor.
-   **Threading:** Uses standard `threading` library for concurrent crawling.
-   **DrissionPage:** Used for web crawling and page interaction.

### Adding a New Source
To add a new job source:
1.  Create a new file in `src/work_show/sources/`.
2.  Implement a class that satisfies the `DataSource` protocol.
3.  Add the new source to `config/settings.yaml` under the `sources` list.
