# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bread and Butter is a Flutter mobile application for a food delivery service. The app provides user authentication, menu browsing, cart management, offers, loyalty program, and order management functionality.

## Development Commands

### Building and Running
```bash
# Run the app in debug mode
flutter run

# Build APK for Android
flutter build apk

# Build for iOS (requires Xcode)
flutter build ios

# Run tests
flutter test

# Analyze code for issues
flutter analyze

# Clean build artifacts
flutter clean
```

### Development Workflow
```bash
# Get dependencies after changes to pubspec.yaml
flutter pub get

# Generate launcher icons
flutter pub run flutter_launcher_icons

# Hot reload during development (R key when running)
# Hot restart (Shift+R key when running)
```

## Project Structure

### Core Files
- `lib/main.dart` - App entry point with splash screen logic
- `lib/config.dart` - API configuration (base URL and image URL)
- `lib/home.dart` - Main home screen with bottom navigation
- `pubspec.yaml` - Dependencies and asset declarations

### Feature Modules
- `lib/login.dart` - User authentication
- `lib/register.dart` - User registration
- `lib/verificaition.dart` - Account verification (typo in filename)
- `lib/forgot_password.dart` & `lib/reset_password.dart` - Password recovery
- `lib/menu.dart` - Food menu with filtering and search
- `lib/cart.dart` - Shopping cart management
- `lib/offers.dart` - Special offers display
- `lib/loyality.dart` - Loyalty program (typo in filename)
- `lib/orders.dart` - Order history and tracking
- `lib/profile.dart` - User profile management

### Key Dependencies
- `http: ^1.2.2` - API communication
- `shared_preferences: ^2.0.15` - Local storage for user session
- `intl: ^0.20.2` - Internationalization support

## Architecture Notes

### API Integration
- Base API URL configured in `config.dart`
- Uses HTTP package for REST API calls
- Shared preferences for session management
- Image assets served from remote URL

### Navigation Pattern
- Bottom navigation bar in home screen
- MaterialPageRoute for screen transitions
- Splash screen with 2-second delay before login

### State Management
- Uses StatefulWidget with setState for local state
- SharedPreferences for persistent user data
- No external state management library (Redux, Provider, etc.)

### UI/UX
- Material Design components
- Orange color theme (`Colors.orange`)
- Custom splash screen with full-cover background image
- Responsive design considerations

## Assets
- Images stored in `assets/` directory
- Splash screen, menu items, offers, and login assets
- All assets declared in pubspec.yaml

## Testing
- Basic widget test setup in `test/widget_test.dart`
- Uses flutter_test framework
- Note: Current test is a template and needs updating for app-specific functionality

## Known Issues
- Filename typos: `verificaition.dart` should be `verification.dart`, `loyality.dart` should be `loyalty.dart`
- Test file contains template counter app test, not app-specific tests