# CSV Data Visualizer

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A powerful Python-based application for visualizing time-series CSV data with PyQt6, Pandas, and Plotly.

## 🌟 Features

- **Interactive Visualization** of time-series CSV data
- **Multiple Chart Types**: Line, Bar, Pie, and Diverging Bar charts
- **Time Period Selection** with predefined periods and custom date ranges
- **Multi-File Aggregation** for combining related data across files
- **Data Filtering** by series or categories
- **Efficient Handling** of large datasets
- **Dark Theme UI** for better visualization experience
- **Metrics Dashboard** for data analysis

## 📊 Screenshots

*[Screenshots coming soon!]*

## 🚀 Installation

### Option 1: From Source

```bash
# Clone the repository
git clone https://github.com/Winnie7050/csv-data-visualizer.git
cd csv-data-visualizer

# Create a virtual environment (optional but recommended)
python -m venv venv
# On Windows
venv\\Scripts\\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 2: Using pip

```bash
# Install from GitHub
pip install git+https://github.com/Winnie7050/csv-data-visualizer.git

# Run the application
csv-visualizer
```

## 🔧 Build Executable

To build a standalone Windows executable:

```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Build the executable
pyinstaller pyinstaller.spec
```

The executable will be created in the `dist/CSV Visualizer` directory.

## 📂 Data Format

The application is designed to work with time-series CSV files in the following format:

- Files contain a date/time column and numeric data columns
- Multiple data series can be present (e.g., "Total," "Computer," "Console," "Phone")
- File names typically follow the pattern: `[Metric Name] - [Identifier], [Start DateTime] to [End DateTime]`

Example directory structure:
```
/Statistics
  /Week1[2025-3-22_2025-3-29]
    Client crash rate ClientCrashRate15m.csv
    Client memory usage percentage ClientMemoryUsagePercentage.csv
  /Week2[2025-3-30_2025-4-5]
    ...
```

## 🔄 Multi-File Aggregation

The application can automatically combine data from multiple CSV files that contain the same metric but cover different time periods:

### How It Works

1. **File Detection**: Files with the same metric name (e.g., "Session time- SessionDurationSeconds") are identified and grouped together
2. **Chronological Merging**: Data from all files in a group is combined into a continuous timeline
3. **Duplicate Handling**: Overlapping data points are resolved using the configured strategy (last, first, or average)
4. **Unified Visualization**: All data is displayed in a single chart showing the complete timeline

### Using the Feature

- **Enable/Disable**: Toggle File Aggregation in the toolbar or File → File Aggregation menu
- **Configure Options**: Access advanced settings via Settings dialog:
  - **Show Single File Groups**: Include metrics with only one file
  - **Add File Metadata Columns**: Add source file information to the combined dataset
  - **Duplicate Handling Strategy**: Choose how to resolve duplicate data points

### Viewing Aggregated Data

- File groups appear in blue with a count of included files
- Click on a file group to visualize the combined dataset
- The File Info tab in the metrics panel shows details about the combined files

## 🧰 Project Structure

```
/csv_visualizer
    /core - Core application components
    /data - Data loading and processing
        /file_aggregator.py - Multi-file aggregation implementation
    /ui - User interface components
        /widgets - Custom UI widgets
        /dialogs - Dialog windows including settings
    /visualization - Visualization engines
    /utils - Utility functions
```

## 💻 Technology Stack

- **Python 3.9+**: Core programming language
- **PyQt6**: GUI framework for native-feeling Windows UI
- **Pandas**: Efficient CSV handling and time-series operations
- **Plotly**: Interactive visualizations with hover capabilities
- **Matplotlib**: Alternative visualization engine (fallback)
- **NumPy**: Numerical operations
- **dateutil**: Parsing varied date formats

## 📄 License

MIT

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For any questions or issues, please open an issue on the GitHub repository.
