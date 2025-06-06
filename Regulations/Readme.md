# Regulate.py

A Python automation script for collecting, filtering, and extracting text from PDF attachments linked in web comment containers filtered for the term **"Attach"**. Designed to work robustly newest-to-oldest, this script is especially suitable for compliance, documentation review, or periodic archival workflows.

---

## 📋 Features

- **Newest-to-Oldest Scanning**: Processes results in reverse chronological order, so you always handle the most recent entries first.
- **Date Filtering**: Only processes entries within a user-defined "days back" window for targeted, timely extractions.
- **Comment Container Parsing**: Collects results from filtered site views (already searched for "Attach").
- **Selective PDF Handling**: Downloads and processes **only the first PDF** in each qualifying comment or article container.
- **ID-Based Filenames**: Uses a unique identifier from each container as the filename for extracted text.
- **Configurable Processing**:
  - `-G` : Enables GPT processing (if available/configured).
  - `-d N` / `--days=N`: Specify how many days back to include (default is today only).
- **Automated Output**: Saves each processed PDF’s text as a `.txt` file in your working directory.
- **Informative Logging**: Actions, skips, and file saves are logged for transparency and troubleshooting.

---

## 🚀 Process Overview

1. **Startup & Argument Parsing**
   - Parses command-line arguments to set GPT and date filtering.
2. **Site Access**
   - Connects to the pre-searched and filtered site (ensure you are authenticated as needed).
3. **Container Gathering**
   - Collects all relevant "comment" or article containers from the results.
4. **Date & Validity Checks**
   - Verifies the date of each entry; continues **only** if within your specified window.
   - Skips containers that are too old or malformed.
5. **PDF Extraction**
   - Searches for PDF links within the comment.
   - Downloads and extracts the **first** PDF found.
6. **Saving the Output**
   - Saves extracted PDF text to a `.txt` file named after the container’s ID.
   - Each action and outcome is logged to terminal and/or log file.

---

## 🛠️ Setup & Installation

### 1. **Dependencies**

Install required Python packages:
pip install requests beautifulsoup4 pdfplumber

### 2. **API Credentials**

- Create a file named `key` in the same directory as `Regulate.py`.
- Insert your API key or relevant credential in this file.
    - **Note:** The file `key` is listed in `.gitignore` to prevent accidental exposure via version control.

### 3. **How to Run**

Basic command usage:
python Regulate.py -G -d 3

- `-G` : Enables GPT processing (if available/configured).
- `-d 3` : Only process containers from the last 3 days.

### 4. **Output**

- Each successful entry creates a `.txt` file named after the unique container ID.
- Output is placed in the working directory.
- Actions and skipped containers are logged for traceability.

---

## ⚙️ Detailed Workflow

1. **Initialize & Parse Arguments**
   - Process command-line switches for date-windows and processing mode.
2. **Connect to Website**
   - Site must be pre-filtered for "Attach"; ensure you are logged in if required.
3. **Scrape Comment Containers**
   - All available containers are gathered for subsequent filtering.
4. **Date Validation**
   - Any container outside your `days_back` window is skipped and logged.
5. **Download and Process**
   - Finds **the first PDF** in each valid container and extracts its text.
   - Saves as `<containerID>.txt`.
6. **Repeat Until Done**
   - Continues newest to oldest until containers are exhausted.

---

## 💡 Notes & Best Practices

- **Authentication:** If the site requires authentication, ensure your session/cookies are valid.
- **File Naming:** Only the **first PDF** per qualifying container is processed, with its text saved using the entry’s ID.
- **Designed for Automation:** The script is well-suited for cron jobs or scheduled repeat use.
- **Logs:** Helpful for auditing, debugging, or retrying failed extracts.
- **Permissions:** Ensure your user and directory permissions allow output file creation.

---

## 🐞 Troubleshooting

- **Nothing Extracted?**
  - Check your date settings and site filter.
  - Confirm your `key` file and dependencies are set up.
  - The site’s HTML/CSS may have changed—check container or PDF link selectors.
- **Authentication Issues?**
  - Ensure proper cookies or login session.

---

**For advanced or custom use, adapt the code to fit your site's unique structure or authentication flow.**

---

**Enjoy automated, reliable processing of your site’s attachments with Regulate.py!**