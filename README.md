# Bread and Butter

A Flutter mobile application for a food delivery service that provides user authentication, menu browsing, cart management, offers, loyalty program, and order management functionality.

## Features

- **User Authentication**: Login, registration, verification, and password recovery
- **Menu Management**: Browse food items with filtering and search capabilities
- **Shopping Cart**: Add, remove, and manage food items in cart
- **Special Offers**: View and access promotional deals and discounts
- **Loyalty Program**: Earn and track loyalty points
- **Order Management**: View order history and track order status
- **ML Recommendations**: Personalized food recommendations powered by machine learning

## Prerequisites

### System Requirements

- **Flutter SDK**: 3.3.3 or higher
- **Dart SDK**: 3.0.0 or higher (included with Flutter)
- **Android Studio** or **VS Code** with Flutter extensions
- **Android SDK** for Android development
- **Xcode** for iOS development (macOS only)
- **Git** for version control

### Development Tools

- Android Emulator or physical Android device
- iOS Simulator or physical iOS device (macOS only)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd breadandbutter
```

### 2. Install Flutter

If you haven't installed Flutter yet:

```bash
# On macOS using Homebrew
brew install --cask flutter

# Or download from https://flutter.dev/docs/get-started/install
```

Verify installation:
```bash
flutter doctor
```

### 3. Set Up Development Environment

#### For Android Development:

1. Install Android Studio
2. Install Android SDK (API level 21 or higher)
3. Create an Android Virtual Device (AVD) or connect a physical device
4. Enable USB debugging on your physical device

#### For iOS Development (macOS only):

1. Install Xcode from the App Store
2. Install Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```
3. Configure iOS Simulator:
   ```bash
   open -a Simulator
   ```

### 4. Install Dependencies

```bash
# Get Flutter dependencies
flutter pub get

# Check for any issues
flutter analyze
```

### 5. Configure Backend

The app requires a backend API server to function properly:

1. Set up the backend server (default: `http://10.0.2.2:5002/api`)
2. Configure API endpoints in `lib/config.dart`
3. Ensure the ML recommendation service is accessible at `https://model.ayeshmadana.site/`

### 6. Run the Application

#### Development Mode:

```bash
# Run in debug mode with hot reload
flutter run

# Run on specific device
flutter run -d <device-id>

# List available devices
flutter devices
```

#### Build for Production:

```bash
# Build APK for Android
flutter build apk

# Build app bundle for Android Play Store
flutter build appbundle

# Build for iOS (macOS only)
flutter build ios
```

## Development Workflow

### Common Commands

```bash
# Get dependencies after updating pubspec.yaml
flutter pub get

# Clean build artifacts
flutter clean

# Run tests
flutter test

# Generate launcher icons
dart run flutter_launcher_icons

# Analyze code for issues
flutter analyze

# Format code
dart format .
```

### Hot Reload Features

- Press **R** in the terminal for hot reload
- Press **Shift+R** for hot restart
- Changes to code are reflected immediately without full app restart

## Project Structure

```
lib/
├── main.dart              # App entry point with splash screen
├── config.dart            # API configuration
├── home.dart              # Main home screen with navigation
├── login.dart             # User authentication
├── register.dart          # User registration
├── menu.dart              # Food menu with search
├── cart.dart              # Shopping cart management
├── offers.dart            # Special offers display
├── orders.dart            # Order history
├── profile.dart           # User profile
└── ...                    # Other feature modules

assets/                    # Static images and assets
backend/                   # Backend API and database scripts
test/                      # Test files
```

## Configuration

### API Configuration

Edit `lib/config.dart` to configure:
- Base API URL
- Image server URL
- ML recommendation service endpoint

### Environment Variables

Create a `.env` file in the root directory for environment-specific settings (this file is ignored by git).

## Key Dependencies

- `http: ^1.2.2` - API communication
- `shared_preferences: ^2.0.15` - Local storage
- `intl: ^0.20.2` - Internationalization
- `flutter_launcher_icons: ^0.9.2` - App icon generation

## Testing

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/widget_test.dart

# Run tests with coverage
flutter test --coverage
```

## Troubleshooting

### Common Issues

1. **Flutter doctor shows issues**:
   ```bash
   flutter doctor -v
   ```
   Follow the suggested fixes for each component.

2. **Gradle build fails**:
   ```bash
   cd android
   ./gradlew clean
   cd ..
   flutter clean
   flutter pub get
   flutter run
   ```

3. **iOS build issues**:
   ```bash
   cd ios
   pod install
   cd ..
   flutter clean
   flutter run
   ```

4. **Hot reload not working**:
   - Ensure you're running in debug mode
   - Try hot restart (Shift+R)
   - Check console for error messages

### Performance Optimization

- Use `flutter analyze` to identify performance issues
- Profile your app with `flutter run --profile`
- Optimize image assets and use appropriate formats
- Use const constructors where possible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Dart Language Guide](https://dart.dev/guides)
- [Android Development Guide](https://developer.android.com/guide)
- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the [Flutter documentation](https://docs.flutter.dev/)
- Review existing issues in the repository
- Create a new issue with detailed information about your problem
