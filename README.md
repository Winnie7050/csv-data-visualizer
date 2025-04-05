# CSV Data Visualizer

A Python-based application for visualizing time-series CSV data with PyQt6, Pandas, and Plotly.

## Features

- Interactive visualization of time-series CSV data
- Multiple chart types: Line, Bar, Pie, and Diverging Bar charts
- Time period selection and data filtering
- Efficient handling of large datasets
- Dark theme UI for better visualization experience

## Installation

```bash
# Clone the repository
git clone https://github.com/Winnie7050/csv-data-visualizer.git
cd csv-data-visualizer

# Create a virtual environment (optional but recommended)
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Build Executable

```bash
pyinstaller pyinstaller.spec
```

## Project Structure

```
/csv_visualizer
    /core - Core application components
    /data - Data loading and processing
    /ui - User interface components
    /visualization - Visualization engines
    /utils - Utility functions
```

## License

MIT
