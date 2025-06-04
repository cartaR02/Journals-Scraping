
## Table of Contents

<details>

   <summary>Contents</summary>

1. [Description](#description)
1. [Installation](#installation)
1. [Usage](#usage)
   1. [Command-line Options](#command-line-options)
   1. [Examples](#examples)
1. [Data Format](#data-format)
1. [Project Structure](#project-structure)
1. [Dependencies](#dependencies)
1. [Logging](#logging)

</details>

## Table of Contents

<details>

   <summary>Contents</summary>

- [Journals Scraping](#journals-scraping)
  - [Description](#description)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Command-line Options](#command-line-options)
    - [Examples](#examples)
  - [Data Format](#data-format)
  - [Project Structure](#project-structure)
  - [Dependencies](#dependencies)
  - [Logging](#logging)

</details>
# Journals Scraping

A Python-based web scraper for extracting and processing content from academic journals.

## Description

This tool automates the process of scraping academic journal websites to extract article information. It can navigate through journal landing pages, handle cookie consent popups, and extract content from article pages. Optionally, it can process the extracted content using OpenAI's GPT models to generate summaries or news stories.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/Journals-Scraping.git
   cd Journals-Scraping
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   - Create a file named `key` in the project root directory
   - Add your OpenAI API key to this file (no quotes or extra spaces)

## Usage

Run the script with:

```
python Journals.py [options]
```

### Command-line Options

- `-i <id>`: Filter by journal ID. Only processes entries in the CSV file with the matching ID.
- `-G`: Enable GPT processing. When enabled, the script will send extracted content to OpenAI's GPT model to generate a news story.

### Examples

Process all journals without GPT:
```
python Journals.py
```

Process only journal with ID 37493:
```
python Journals.py -i 37493
```

Process all journals with GPT enabled:
```
python Journals.py -G
```

Process specific journal with GPT enabled:
```
python Journals.py -i 37493 -G
```

## Data Format

The script reads journal information from `WebsiteData.csv`. Each row in the CSV should contain:

1. Journal ID
2. URLs (landing page URL and base URL for article links, separated by `|`) 3. CSS class for article links
4. CSS class for article content container

Example CSV format:
```
37493,https://journals.sagepub.com/loi/aer|https://journals.sagepub.com,loi__issue__link,toc-container
```

## Project Structure

- `Journals.py`: Main script
- `WebsiteData.csv`: Contains journal website information
- `key`: OpenAI API key
- `logs/`: Directory containing log files
- `Notes/`: Additional notes and comments

## Dependencies

- BeautifulSoup4: HTML parsing
- Selenium: Web browser automation
- OpenAI: GPT API integration
- Requests: HTTP requests
- Firefox WebDriver: Required for Selenium

## Logging

The script creates detailed logs in the `logs/` directory with timestamps. These logs include information about the scraping process, any errors encountered, and the output from GPT processing if enabled.
