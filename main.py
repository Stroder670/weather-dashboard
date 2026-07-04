#!/usr/bin/env python3
"""
Weather Dashboard - Main Entry Point
A beautiful Python application for real-time weather data
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.dashboard import WeatherDashboard


def main():
    """Run the application"""
    app = QApplication(sys.argv)
    window = WeatherDashboard()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
