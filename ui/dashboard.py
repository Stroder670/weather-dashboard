import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QScrollArea, QFrame, QMessageBox, QComboBox
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from api.weather_api import WeatherAPI
from utils.config import Config


class WeatherWorker(QThread):
    """Worker thread for API calls"""
    weather_fetched = pyqtSignal(dict)
    forecast_fetched = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, api: WeatherAPI):
        super().__init__()
        self.api = api
        self.city = None
        self.fetch_type = None
    
    def set_city(self, city: str, fetch_type: str = 'both'):
        """Set city and fetch type"""
        self.city = city
        self.fetch_type = fetch_type
    
    def run(self):
        """Run API calls"""
        if not self.city:
            return
        
        try:
            if self.fetch_type in ['current', 'both']:
                current = self.api.get_current_weather(self.city)
                if current:
                    parsed = self.api.parse_current_weather(current)
                    self.weather_fetched.emit(parsed)
                else:
                    self.error.emit("Could not fetch weather data")
            
            if self.fetch_type in ['forecast', 'both']:
                forecast = self.api.get_forecast(self.city)
                if forecast:
                    parsed = self.api.parse_forecast(forecast)
                    self.forecast_fetched.emit(parsed)
        
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class WeatherDashboard(QMainWindow):
    """Main Weather Dashboard Application"""
    
    def __init__(self):
        super().__init__()
        
        # Check configuration
        if not Config.validate():
            QMessageBox.critical(
                self, "Configuration Error",
                "Please set OPENWEATHER_API_KEY in .env file\n"
                "Get a free key at: https://openweathermap.org/api"
            )
            sys.exit(1)
        
        self.api = WeatherAPI()
        self.current_weather = {}
        self.forecast_data = []
        
        self.init_ui()
        self.setup_worker()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(Config.APP_TITLE)
        self.setGeometry(100, 100, Config.APP_WIDTH, Config.APP_HEIGHT)
        
        # Modern stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0e17;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 2px solid #0f3460;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e5ff;
            }
            QPushButton:pressed {
                background-color: #00a8cc;
            }
            QFrame {
                background-color: #16213e;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 2px solid #0f3460;
                border-radius: 6px;
                padding: 5px;
            }
        """)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Search bar
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search city...")
        self.search_input.returnPressed.connect(self.search_weather)
        self.search_input.setMinimumHeight(40)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_weather)
        search_btn.setMaximumWidth(120)
        search_layout.addWidget(search_btn)
        
        main_layout.addWidget(search_frame)
        
        # Current weather frame
        self.current_frame = QFrame()
        current_layout = QVBoxLayout(self.current_frame)
        
        self.city_label = QLabel()
        self.city_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.city_label.setAlignment(Qt.AlignCenter)
        current_layout.addWidget(self.city_label)
        
        self.temp_label = QLabel()
        self.temp_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setStyleSheet("color: #00d4ff;")
        current_layout.addWidget(self.temp_label)
        
        self.desc_label = QLabel()
        self.desc_label.setFont(QFont("Arial", 16))
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #90ee90;")
        current_layout.addWidget(self.desc_label)
        
        # Weather details grid
        details_frame = QFrame()
        details_layout = QHBoxLayout(details_frame)
        
        self.humidity_label = QLabel("💧 Humidity: --")
        self.wind_label = QLabel("💨 Wind: --")
        self.pressure_label = QLabel("🔽 Pressure: --")
        self.feels_label = QLabel("🌡️ Feels: --")
        
        for label in [self.humidity_label, self.wind_label, self.pressure_label, self.feels_label]:
            label.setFont(QFont("Arial", 11))
            label.setStyleSheet("color: #b0c4de;")
            details_layout.addWidget(label)
        
        current_layout.addWidget(details_frame)
        main_layout.addWidget(self.current_frame)
        
        # Forecast label
        forecast_title = QLabel("📅 5-Day Forecast")
        forecast_title.setFont(QFont("Arial", 14, QFont.Bold))
        forecast_title.setStyleSheet("color: #00d4ff;")
        main_layout.addWidget(forecast_title)
        
        # Forecast scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.forecast_container = QWidget()
        self.forecast_layout = QHBoxLayout(self.forecast_container)
        self.forecast_layout.setSpacing(10)
        
        scroll_area.setWidget(self.forecast_container)
        main_layout.addWidget(scroll_area)
        
        # Initial placeholder
        self.city_label.setText("Enter a city name to get started")
        self.temp_label.setText("--")
        self.desc_label.setText("Search for weather information")
    
    def setup_worker(self):
        """Setup worker thread"""
        self.worker = WeatherWorker(self.api)
        self.worker.weather_fetched.connect(self.display_weather)
        self.worker.forecast_fetched.connect(self.display_forecast)
        self.worker.error.connect(self.show_error)
    
    def search_weather(self):
        """Search for weather"""
        city = self.search_input.text().strip()
        
        if not city:
            QMessageBox.warning(self, "Input Error", "Please enter a city name")
            return
        
        self.city_label.setText("Loading...")
        self.worker.set_city(city, 'both')
        self.worker.start()
    
    def display_weather(self, weather: dict):
        """Display current weather"""
        self.current_weather = weather
        
        if not weather:
            return
        
        # Update labels
        city_country = f"{weather['city']}, {weather['country']}"
        self.city_label.setText(city_country)
        
        temp_symbol = Config.get_temp_symbol()
        self.temp_label.setText(f"{weather['temp']}{temp_symbol}")
        self.desc_label.setText(weather['description'])
        
        self.humidity_label.setText(f"💧 Humidity: {weather['humidity']}%")
        self.wind_label.setText(f"💨 Wind: {weather['wind_speed']} m/s")
        self.pressure_label.setText(f"🔽 Pressure: {weather['pressure']} hPa")
        self.feels_label.setText(f"🌡️ Feels: {weather['feels_like']}{temp_symbol}")
    
    def display_forecast(self, forecast: list):
        """Display forecast"""
        self.forecast_data = forecast
        
        # Clear existing forecast widgets
        while self.forecast_layout.count():
            self.forecast_layout.takeAt(0).widget().deleteLater()
        
        temp_symbol = Config.get_temp_symbol()
        
        for day in forecast:
            day_frame = QFrame()
            day_frame.setMaximumWidth(150)
            day_layout = QVBoxLayout(day_frame)
            day_layout.setSpacing(8)
            
            # Date
            date_label = QLabel(day['date'])
            date_label.setFont(QFont("Arial", 11, QFont.Bold))
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet("color: #00d4ff;")
            day_layout.addWidget(date_label)
            
            # Temperature range
            temp_range = QLabel(f"↑ {day['temp_max']}{temp_symbol}\n↓ {day['temp_min']}{temp_symbol}")
            temp_range.setFont(QFont("Arial", 13, QFont.Bold))
            temp_range.setAlignment(Qt.AlignCenter)
            temp_range.setStyleSheet("color: #90ee90;")
            day_layout.addWidget(temp_range)
            
            # Description
            desc = QLabel(day['description'])
            desc.setFont(QFont("Arial", 9))
            desc.setAlignment(Qt.AlignCenter)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #b0c4de;")
            day_layout.addWidget(desc)
            
            # Rain chance
            rain = QLabel(f"🌧️ {day['rain_chance']}%")
            rain.setFont(QFont("Arial", 10))
            rain.setAlignment(Qt.AlignCenter)
            rain.setStyleSheet("color: #add8e6;")
            day_layout.addWidget(rain)
            
            self.forecast_layout.addWidget(day_frame)
        
        self.forecast_layout.addStretch()
    
    def show_error(self, error_msg: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", error_msg)
        self.city_label.setText("Error - Please try again")
