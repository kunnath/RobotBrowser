# RobotBrowser

## Overview

RobotBrowser is a Streamlit-based app for automated browser tasks with comprehensive reporting and screenshot management.  
It consists of two main components:

- **`demo/app.py`**: The main Streamlit app for running browser automation, viewing status, and generating reports.
- **`demo/copyreport.py`**: A utility script for copying and organizing automation reports and screenshots.

---

## Workflow

1. **Start the App**  
   Launch the Streamlit app (`app.py`). Fill in the form with your task details and click "Start Automation".

2. **Automation Process**  
   The app runs browser automation, collects screenshots, and organizes results in timestamped folders.

3. **Generate Report**  
   Once automation is complete, the "Generate Report" button is enabled. Click it to generate a comprehensive HTML report with screenshots and data.

4. **Manage Reports**  
   Use `copyreport.py` to copy or organize reports and screenshots as needed.

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/robotbrowser.git
   cd robotbrowser
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   *Typical dependencies include:*
   - streamlit
   - browser-use (or your automation library)
   - any other packages listed in `requirements.txt`

---

## Usage

### Run the Streamlit App

```bash
streamlit run demo/app.py
```

- Fill in the form fields (URL, task description, etc.).
- Click **Start Automation**.
- Wait for automation to complete.
- Click **Generate Report** to create the HTML report.
- Access reports and screenshots in the `automation_reports/` folder.

#### Example Inputs

**URL:**  
```
https://www.bbc.com/news
```

**Task Description:**  
```
Extract the headlines from the main news section and take screenshots of the top three articles.
```

**Another Example**

**URL:**  
```
https://www.wikipedia.org/
```

**Task Description:**  
```
Search for "Artificial Intelligence", capture the summary section, and take a screenshot of the results page.
```

### Copy and Organize Reports

Use the utility script to copy reports:

```bash
python demo/copyreport.py --source automation_reports/<report_folder> --dest <destination_folder>
```

- Replace `<report_folder>` with the name of your report folder.
- Replace `<destination_folder>` with your desired destination.

---

## Folder Structure

- `automation_reports/`  
  Contains all reports and screenshots, organized by timestamp.

- `demo/app.py`  
  Main Streamlit application.

- `demo/copyreport.py`  
  Utility for copying reports.

---

## Notes

- Screenshots are automatically copied and organized after each automation run.
- Reports are only generated when you click the "Generate Report" button.
- For troubleshooting, check the status panel in the app or the logs in your terminal.

---

## License

MIT License

---

For more details, see the code comments in `app.py` and `copyreport.py`.
