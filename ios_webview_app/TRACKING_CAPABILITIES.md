# Privacy-Focused User Activity Tracking

This document outlines the tracking capabilities built into the Calm Journey iOS WebView app, with a strong emphasis on user privacy, data minimization, and transparency.

## Overview

The tracking system monitors user interactions with the app to provide insights for improving user experience and application functionality. All tracking is:

- **Privacy-first**: Personal information is anonymized by default
- **Transparent**: Users can view what data is collected and clear it at any time
- **Device-only**: Data is stored only on the user's device by default
- **Minimal**: Only essential interactions needed for improving the app are tracked

## Tracked Activities

The system captures the following user activities:

### 1. Page Views
- **What**: Pages/screens the user visits
- **Why**: Understand navigation patterns and popular content
- **Data collected**: Path, title, timestamp
- **Anonymized**: Yes (no user identifiers)

### 2. User Interactions
- **What**: Button clicks, link taps
- **Why**: Identify usability issues and feature usage
- **Data collected**: Element type, element ID/text (if available), timestamp
- **Anonymized**: Yes (no user identifiers)

### 3. Time Spent
- **What**: Duration of active app usage
- **Why**: Understand engagement and retention
- **Data collected**: Session duration, time between activities
- **Anonymized**: Yes (no user identifiers)

### 4. Scroll Depth
- **What**: How far users scroll on pages
- **Why**: Determine content visibility and engagement
- **Data collected**: Scroll percentage, timestamp
- **Anonymized**: Yes (no user identifiers)

### 5. Error Events
- **What**: JavaScript errors encountered
- **Why**: Identify and fix technical issues
- **Data collected**: Error message, source, line number
- **Anonymized**: Yes (no user identifiers)

## Privacy Controls

### User Transparency
The app includes a privacy menu that allows users to:
- View a summary of data collected in the current session
- Clear all collected data
- Access the full privacy policy

### Data Storage
- All tracking data is stored locally on the device
- No automatic transmission to external servers
- Data is cleared when the app is uninstalled

### Anonymization
- User identifiers are removed from all tracking data
- Device identifiers are not linked to activity data
- Session IDs are randomly generated and temporary

## Implementation

### Integration

To add the tracking system to your WebView:

1. Include the UserActivityTracker.swift file in your project
2. Configure the tracker when setting up your WebView:

```swift
// Create tracking configuration
let trackingConfig = UserActivityTracker.TrackingConfig(
    enablePageViews: true,
    enableInteractions: true,
    enableTimeTracking: true,
    enableScrollDepth: true,
    anonymizeUser: true,
    collectionFrequency: 60
)

// Add tracking to WebView
activityTracker = webView.addUserActivityTracking(config: trackingConfig)
```

### Data Submission

If you wish to send anonymized analytics to your server:

```swift
// Example of submitting data (implement this according to your needs)
func submitAnonymizedData() {
    if let trackingData = activityTracker.exportTrackingData() {
        // Convert to JSON string for submission
        if let jsonString = String(data: trackingData, encoding: .utf8) {
            // Submit to your analytics endpoint
            // ...
            
            // Clear local data after successful submission if desired
            activityTracker.clearTrackingData()
        }
    }
}
```

## Best Practices

1. **Transparency**: Always inform users about data collection in your privacy policy
2. **Consent**: Consider implementing an opt-in model for analytics
3. **Data minimization**: Only collect what you need to improve the app
4. **Storage limitation**: Set reasonable time limits for data retention
5. **Security**: If implementing data transfer, use secure connections (HTTPS)

## Privacy Policy Recommendations

Your app's privacy policy should clearly state:

- What information is collected
- How it is used
- Where it is stored
- How long it is kept
- User rights regarding their data
- How users can delete their data

## Compliance Considerations

This implementation is designed with privacy regulations in mind:

- **GDPR**: Supports data minimization, purpose limitation, storage limitation
- **CCPA**: Provides transparency and user control over personal information
- **App Store Guidelines**: Adheres to Apple's privacy requirements

## Future Enhancements

Potential future privacy enhancements:

- Event sampling to further reduce data collection
- Automated data purging after set time periods
- Enhanced data anonymization techniques
- Differential privacy implementation for statistical analysis