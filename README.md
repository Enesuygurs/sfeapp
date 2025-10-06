# Subtitles for Everyone (SFE)

A powerful real-time screen text translation application that instantly translates subtitles and text overlays in movies, TV shows, games, and any on-screen content using advanced OCR technology and DeepL's high-quality translation API. Break language barriers and enjoy global content without missing a beat!

![chrome_6uCRReoojV](https://github.com/user-attachments/assets/fb0f07c2-3898-424c-8d1e-028a6e25cf94)


## Features

- **Real-time OCR**: Captures text from selected screen areas using Tesseract OCR
- **Multiple Translation Modes**:
  - Grayscale threshold
  - Adaptive threshold
  - Color filtering (HSV-based)
- **DeepL Integration**: High-quality translations using DeepL API
- **System Tray**: Runs in background with system tray icon
- **Customizable UI**: Adjustable fonts, colors, transparency, and positioning
- **Hotkey Support**: Keyboard shortcuts for area selection, pause/resume, and exit
- **Multi-language Support**: Interface available in multiple languages
- **Smart Filtering**: Avoids duplicate translations and filters short text

## Requirements

- Python 3.9+
- Tesseract OCR (installed and added to PATH)
- DeepL API key
- Windows OS (tested on Windows 10/11)

### Python Dependencies

```
opencv-python
pytesseract
deepl
keyboard
pystray
Pillow
mss
ttkthemes
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Enesuygurs/sfeapp.git
   cd sfeapp
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install and add to system PATH
   - Test installation: `tesseract --version`

4. **Get DeepL API Key**:
   - Sign up at: https://www.deepl.com/pro-api
   - Get your API key from the dashboard

## Configuration

1. **First Run Setup**:
   - Run `python sfe.py`
   - Configure Tesseract path in settings
   - Enter your DeepL API key
   - Select target language

2. **Area Selection**:
   - Use hotkey (default: F8) to open area selector
   - Click and drag to select the area to monitor
   - The application will capture text from this area

3. **OCR Settings**:
   - **Grayscale Threshold**: Simple binary thresholding
   - **Adaptive Threshold**: Dynamic thresholding for varying lighting
   - **Color Filter**: HSV-based color filtering for specific text colors

## Usage

1. **Start the Application**:
   ```bash
   python sfe.py
   ```

2. **System Tray Controls**:
   - Right-click the tray icon for menu options
   - **Select Area**: Choose screen area to monitor (F8)
   - **Pause/Resume**: Toggle translation (F9)
   - **Settings**: Open configuration window
   - **Exit**: Close application (F10)

3. **Translation Process**:
   - Application continuously captures the selected area
   - OCR extracts text from the image
   - Text is translated using DeepL API
   - Translated text appears as an overlay on screen

## Configuration Options

### General Settings
- **Tesseract Path**: Path to tesseract.exe
- **DeepL API Key**: Your DeepL API authentication key
- **Target Language**: Language to translate to
- **Interface Language**: Application UI language
- **Scan Interval**: Time between screen captures (seconds)
- **Similarity Threshold**: Minimum text similarity to trigger new translation
- **Min Text Length**: Minimum character count for translation

### OCR Settings
- **Processing Mode**: Grayscale, Adaptive, or Color filtering
- **Threshold Value**: Binary threshold for grayscale mode
- **Auto Invert**: Automatically detect and invert dark text on light backgrounds
- **HSV Color Range**: Color filtering parameters (H, S, V min/max)

### Interface Settings
- **Font**: Family, size, style (bold, italic, underline)
- **Colors**: Font and background colors
- **Transparency**: Overlay opacity (0.1-1.0)
- **Position**: Vertical offset from top of screen
- **Translation Lifespan**: How long translations remain visible (seconds)

### Hotkeys
- **Select Area**: Open area selection tool
- **Pause/Resume**: Toggle translation on/off
- **Exit**: Close application

## Project Structure

```
sfeapp/
├── sfe.py                 # Main application file
├── gui.py                 # GUI components and settings window
├── config_manager.py      # Configuration management
├── ocr_tester.py          # OCR testing and preview tool
├── config.ini            # User configuration file
├── diller.json           # Supported target languages
├── arayuz_dilleri.json   # Supported interface languages
├── lang/                 # Language files
│   ├── en.json
│   ├── tr.json
│   ├── de.json
│   ├── es.json
│   └── fr.json
├── images/               # Application icons
│   ├── icon.png
│   ├── stop.png
│   └── icson.png
└── README.md
```

## How It Works

1. **Screen Capture**: Uses `mss` library to capture selected screen area
2. **OCR Processing**:
   - Converts image to appropriate format (grayscale/color filtering)
   - Applies thresholding or color filtering
   - Uses Tesseract to extract text
3. **Text Filtering**:
   - Compares with previous text using similarity ratio
   - Filters out short or duplicate text
4. **Translation**: Sends text to DeepL API for translation
5. **Display**: Shows translated text as transparent overlay

## Troubleshooting

### Common Issues

1. **Tesseract not found**:
   - Ensure Tesseract is installed and in PATH
   - Check path in settings matches actual location

2. **DeepL API errors**:
   - Verify API key is correct
   - Check API quota and billing status
   - Ensure internet connection is stable

3. **No text detected**:
   - Adjust OCR settings (try different modes)
   - Ensure selected area contains clear, readable text
   - Check screen resolution and DPI settings

4. **Application won't start**:
   - Check Python version (3.9+ required)
   - Verify all dependencies are installed
   - Check for missing language files

### Debug Mode

Run with debug output:
```bash
python sfe.py
```

Check console output for detailed error messages and OCR results.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review existing issues for similar problems
