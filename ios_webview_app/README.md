# Calm Journey iOS WebView App

This is an iOS WebView wrapper for the Calm Journey web application. It provides a native app experience for users on iOS devices.

## Features

- Native iOS WebView wrapper
- Pull-to-refresh functionality
- Progress indicator for page loading
- Offline error handling
- Handle external links appropriately
- Support for JavaScript alerts and dialogs

## Project Setup

### Prerequisites

- Xcode 12.0 or later
- iOS 13.0+ deployment target
- Apple Developer account (for distributing on App Store)
- Your deployed web application URL

### Configuration

Before building the app, make sure to update the following:

1. In `WebViewController.swift`, change the `appURL` value to your deployed application URL:
   ```swift
   private let appURL = URL(string: "https://your-deployed-app-url.replit.app")!
   ```

2. Add your app icon to the Assets.xcassets folder
3. Update app colors in Assets.xcassets if needed

### Building the Project

1. Open the project in Xcode
2. Select your development team in Signing & Capabilities
3. Build and run on a simulator or physical device

## Tracking Capabilities

### Analytics Integration

To track user activity in the app:

1. Add a custom JavaScript bridge to the WebView to communicate between the web app and native code
2. Use the following code in WebViewController.swift to inject a user tracking script:

```swift
func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
    // Inject tracking JavaScript
    let trackingScript = """
    (function() {
        // Record page views
        window.addEventListener('load', function() {
            window.webkit.messageHandlers.appInterface.postMessage({
                type: 'pageView',
                page: window.location.pathname
            });
        });
        
        // Track user interactions
        document.addEventListener('click', function(e) {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                window.webkit.messageHandlers.appInterface.postMessage({
                    type: 'interaction',
                    element: e.target.tagName,
                    id: e.target.id || '',
                    text: e.target.innerText || ''
                });
            }
        });
    })();
    """
    
    webView.evaluateJavaScript(trackingScript, completionHandler: nil)
}
```

3. Add a message handler to receive these events:

```swift
// Add this to configureWebView() method
let contentController = WKUserContentController()
contentController.add(self, name: "appInterface")
configuration.userContentController = contentController

// Implement the message handler protocol
extension WebViewController: WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "appInterface", let messageBody = message.body as? [String: Any] {
            // Process tracking data
            if let type = messageBody["type"] as? String {
                switch type {
                case "pageView":
                    if let page = messageBody["page"] as? String {
                        logPageView(page)
                    }
                case "interaction":
                    logInteraction(messageBody)
                default:
                    break
                }
            }
        }
    }
    
    private func logPageView(_ page: String) {
        // Log page view to your analytics system
        print("Page viewed: \(page)")
    }
    
    private func logInteraction(_ data: [String: Any]) {
        // Log user interaction to your analytics system
        print("User interaction: \(data)")
    }
}
```

## Privacy Considerations

- The WebView wrapper requests minimal permissions
- All analytics data is stored locally and not shared with third parties
- User tracking is limited to in-app actions
- No personal information is collected outside what's provided in the web app

## App Store Submission

1. Create screenshots for various device sizes
2. Prepare app metadata:
   - App name
   - Description
   - Keywords
   - Support URL
   - Privacy Policy URL
3. Submit for review through App Store Connect

## Troubleshooting

- If the web app doesn't load:
  - Check your internet connection
  - Verify the URL is correct and the web app is deployed
  - Ensure content security policies allow embedding

- If JavaScript isn't working:
  - Confirm JavaScript is enabled in WKWebView
  - Check for console errors in Safari Developer Tools

## Support

For any issues or questions regarding the iOS app wrapper, contact the development team.