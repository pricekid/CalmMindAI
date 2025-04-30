# Calm Journey iOS WebView App Implementation Guide

This guide provides step-by-step instructions for creating an iOS WebView app that wraps your Calm Journey web application.

## Prerequisites

- Xcode 14.0 or later
- Apple Developer account (for App Store distribution)
- macOS computer for development
- Your deployed web application URL

## Implementation Steps

### 1. Create a New Xcode Project

1. Open Xcode and select "Create a new Xcode project"
2. Choose "App" under iOS templates
3. Set product name to "CalmJourney"
4. Set Organization Identifier to "com.calmjourney" (or your preferred domain)
5. Select "Swift" for language and "Storyboard" for interface
6. Ensure "Use Core Data" is unchecked
7. Choose a location to save your project

### 2. Replace Files with Our Implementation

We've provided the core files for your WebView app. You'll need to:

1. Replace the default `AppDelegate.swift` with our version
2. Replace the default `SceneDelegate.swift` with our version
3. Add the `WebViewController.swift` file we've created
4. Update the Info.plist file with necessary permissions

### 3. Configure WebView URL

In `WebViewController.swift`, update the appURL constant to point to your deployed application:

```swift
// Change this URL to your deployed app URL
private let appURL = URL(string: "https://your-deployed-app-url.replit.app")!
```

### 4. Configure App Icons and Launch Screen

1. Update the Assets.xcassets folder with your app icons
2. Update the LaunchScreen.storyboard to match your branding

### 5. Add User Activity Tracking

If you want to implement user activity tracking in the app:

1. Add the WKScriptMessageHandler implementation to WebViewController.swift as shown in the README.md
2. Configure your analytics service in the logPageView and logInteraction methods
3. Make sure to respect user privacy and only collect necessary data

### 6. Configure App for Distribution

1. In Xcode, select "Signing & Capabilities" in the project settings
2. Connect your Apple Developer account
3. Configure app bundle identifier
4. Generate app icons using Asset Catalog Creator or similar tools
5. Complete App Store Connect setup with app metadata

## Tracking Features

Our implementation includes a JavaScript bridge for tracking user activity:

1. Page views are tracked when users navigate to different screens
2. Button and link interactions are captured
3. Data is available through the WKScriptMessageHandler protocol
4. All tracking respects user privacy and is contained within the app

## Special Considerations

### Local Storage and Cookies

The WebView configuration includes settings to preserve local storage and cookies, which ensures:

1. User sessions are maintained
2. Offline functionality works correctly (if supported by your PWA)
3. User preferences are saved between sessions

### Deep Linking

For deep linking support (opening specific screens from notifications):

1. Update the Info.plist to include URL scheme registration
2. Add URL handling code to AppDelegate.swift
3. Pass the URL parameters to the WebViewController

### Push Notifications

If you want to enable push notifications:

1. Add the Push Notifications capability in Xcode
2. Update AppDelegate with notification handling code
3. Create a notification service extension
4. Implement a bridge between native notifications and web app

## Testing Your App

Before submitting to the App Store:

1. Test on multiple iOS devices and iOS versions
2. Verify all PWA functionality works properly
3. Test offline mode and recovery
4. Ensure proper error handling for network issues
5. Test deep linking if implemented
6. Verify your analytics tracking works correctly

## Submission Checklist

- App icons in all required sizes
- App Store screenshots for iPhone and iPad
- App description, keywords, and metadata
- Privacy policy URL
- Support website URL
- App Store rating information
- Build uploaded via Xcode or App Store Connect
- TestFlight version tested successfully

## Troubleshooting Common Issues

### Content Not Loading

- Check your URL is correct and the website is accessible
- Verify App Transport Security settings in Info.plist
- Check WebView logs for JavaScript errors

### JavaScript Errors

- Ensure JavaScript is enabled in WKWebViewConfiguration
- Check for JavaScript console errors using Safari Developer Tools
- Test your web app in Safari to isolate WebView-specific issues

### App Rejection Issues

- Ensure your app provides sufficient native features beyond just a wrapper
- Make sure all App Store guidelines are followed
- Include proper functionality description in your submission notes