# Project Overview

This project contains a collection of Python scripts for automating tasks related to document creation and data extraction. The project is structured into three main components:

1.  **`create_ppts`**: A tool for automatically generating PowerPoint presentations from Markdown files.
2.  **`pdf_to_excels`**: A script for converting PDF files into Excel spreadsheets.
3.  **`screenimage_to_htmls`**: A set of instructions for a prompt engineer to create HTML files from images and add JavaScript functionality.

## Building and Running

### `create_ppts`

To run the PowerPoint creation script, execute the following command from the project root:

```bash
python codes/create_ppts/src/main.py
```

### `pdf_to_excels`

To run the PDF to Excel conversion script, execute the following command from the project root:

```bash
python codes/pdf_to_excels/pdf_to_excel.py
```

## Development Conventions

The project uses the following libraries:

*   `python-pptx`: For creating and editing PowerPoint files.
*   `pdfplumber`: For extracting text from PDF files.
*   `pandas`: For data manipulation and creating Excel files.

The code is written in Python and follows standard Python conventions.
