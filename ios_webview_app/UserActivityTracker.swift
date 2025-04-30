import Foundation
import WebKit

/// UserActivityTracker handles tracking user interactions within the WebView
class UserActivityTracker: NSObject, WKScriptMessageHandler {
    
    // MARK: - Properties
    
    /// Types of user activities to track
    enum ActivityType: String {
        case pageView = "pageView"
        case interaction = "interaction"
        case timeSpent = "timeSpent"
        case scrollDepth = "scrollDepth"
        case search = "search"
        case login = "login"
        case error = "error"
    }
    
    /// Tracking configuration
    struct TrackingConfig {
        var enablePageViews: Bool = true
        var enableInteractions: Bool = true
        var enableTimeTracking: Bool = true
        var enableScrollDepth: Bool = true
        var anonymizeUser: Bool = true
        var collectionFrequency: TimeInterval = 60 // seconds
    }
    
    /// User session data
    private struct UserSession {
        var sessionId: String
        var startTime: Date
        var lastActivityTime: Date
        var deepestScrollPercentage: Int = 0
        var pagesViewed: [String] = []
        var interactions: [String: Int] = [:]
    }
    
    // Configuration for tracking
    private var config: TrackingConfig
    
    // Current user session
    private var session: UserSession
    
    // File URL for storing tracking data
    private var storageURL: URL?
    
    // MARK: - Initialization
    
    init(config: TrackingConfig = TrackingConfig()) {
        self.config = config
        
        // Create a new session ID (UUID)
        let sessionId = UUID().uuidString
        let currentTime = Date()
        self.session = UserSession(
            sessionId: sessionId,
            startTime: currentTime,
            lastActivityTime: currentTime
        )
        
        // Set up storage location
        if let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first {
            self.storageURL = documentsDirectory.appendingPathComponent("user_activity_data.json")
        }
        
        super.init()
        
        // Start periodic tracking if enabled
        if config.enableTimeTracking {
            startPeriodicTracking()
        }
    }
    
    // MARK: - JavaScript Injection
    
    /// JavaScript to inject into the WebView for tracking
    var trackingScript: String {
        return """
        (function() {
            // Track page views
            function trackPageView() {
                const path = window.location.pathname;
                const title = document.title;
                window.webkit.messageHandlers.userActivity.postMessage({
                    type: 'pageView',
                    path: path,
                    title: title,
                    timestamp: new Date().toISOString()
                });
            }
            
            // Track user interactions
            function trackInteraction(event) {
                // Only track clicks on interactive elements
                if (event.target.tagName === 'BUTTON' || 
                    event.target.tagName === 'A' ||
                    event.target.closest('button') ||
                    event.target.closest('a')) {
                    
                    const element = event.target.tagName.toLowerCase();
                    const id = event.target.id || '';
                    const text = event.target.innerText || '';
                    const className = event.target.className || '';
                    
                    window.webkit.messageHandlers.userActivity.postMessage({
                        type: 'interaction',
                        element: element,
                        id: id,
                        text: text,
                        className: className,
                        timestamp: new Date().toISOString()
                    });
                }
            }
            
            // Track scroll depth
            function trackScrollDepth() {
                const scrollHeight = document.documentElement.scrollHeight;
                const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
                const clientHeight = document.documentElement.clientHeight;
                
                // Calculate scroll percentage
                const scrollPercentage = Math.floor((scrollTop + clientHeight) / scrollHeight * 100);
                
                window.webkit.messageHandlers.userActivity.postMessage({
                    type: 'scrollDepth',
                    percentage: scrollPercentage,
                    timestamp: new Date().toISOString()
                });
            }
            
            // Track search queries
            function trackSearch() {
                const searchForms = document.querySelectorAll('form');
                searchForms.forEach(form => {
                    form.addEventListener('submit', function(e) {
                        const searchInputs = form.querySelectorAll('input[type="search"], input[type="text"]');
                        searchInputs.forEach(input => {
                            if (input.value.trim()) {
                                window.webkit.messageHandlers.userActivity.postMessage({
                                    type: 'search',
                                    query: input.value.trim(),
                                    timestamp: new Date().toISOString()
                                });
                            }
                        });
                    });
                });
            }
            
            // Track errors
            window.addEventListener('error', function(e) {
                window.webkit.messageHandlers.userActivity.postMessage({
                    type: 'error',
                    message: e.message,
                    source: e.filename,
                    lineno: e.lineno,
                    timestamp: new Date().toISOString()
                });
            });
            
            // Set up event listeners
            window.addEventListener('load', function() {
                trackPageView();
                trackSearch();
                
                // Throttle scroll events for performance
                let scrollTimeout;
                window.addEventListener('scroll', function() {
                    if (!scrollTimeout) {
                        scrollTimeout = setTimeout(function() {
                            trackScrollDepth();
                            scrollTimeout = null;
                        }, 500);
                    }
                });
                
                // Track clicks
                document.addEventListener('click', trackInteraction);
            });
            
            // Track navigation changes for SPA
            const originalPushState = history.pushState;
            const originalReplaceState = history.replaceState;
            
            history.pushState = function() {
                originalPushState.apply(this, arguments);
                trackPageView();
            };
            
            history.replaceState = function() {
                originalReplaceState.apply(this, arguments);
                trackPageView();
            };
            
            window.addEventListener('popstate', function() {
                trackPageView();
            });
        })();
        """
    }
    
    // MARK: - WKScriptMessageHandler
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "userActivity", let messageBody = message.body as? [String: Any] {
            processActivityMessage(messageBody)
        }
    }
    
    // MARK: - Tracking Methods
    
    /// Process activity messages from JavaScript
    private func processActivityMessage(_ messageBody: [String: Any]) {
        guard let typeString = messageBody["type"] as? String,
              let activityType = ActivityType(rawValue: typeString) else {
            return
        }
        
        // Update last activity time
        session.lastActivityTime = Date()
        
        // Process based on activity type
        switch activityType {
        case .pageView:
            if config.enablePageViews, let path = messageBody["path"] as? String {
                session.pagesViewed.append(path)
                logActivity(type: .pageView, details: messageBody)
            }
            
        case .interaction:
            if config.enableInteractions, let element = messageBody["element"] as? String {
                session.interactions[element, default: 0] += 1
                logActivity(type: .interaction, details: messageBody)
            }
            
        case .scrollDepth:
            if config.enableScrollDepth, let percentage = messageBody["percentage"] as? Int {
                if percentage > session.deepestScrollPercentage {
                    session.deepestScrollPercentage = percentage
                    logActivity(type: .scrollDepth, details: messageBody)
                }
            }
            
        case .search, .login, .error:
            // Always log these important activities
            logActivity(type: activityType, details: messageBody)
        }
        
        // Save data periodically
        saveActivityData()
    }
    
    /// Start periodic tracking for user session
    private func startPeriodicTracking() {
        // Create a timer to log user time spent periodically
        Timer.scheduledTimer(withTimeInterval: config.collectionFrequency, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            
            let currentTime = Date()
            let timeSpentSeconds = currentTime.timeIntervalSince(self.session.lastActivityTime)
            
            // Only log if there was recent activity
            if timeSpentSeconds < self.config.collectionFrequency * 2 {
                self.logActivity(type: .timeSpent, details: [
                    "seconds": timeSpentSeconds,
                    "timestamp": ISO8601DateFormatter().string(from: currentTime)
                ])
                
                // Save the updated data
                self.saveActivityData()
            }
        }
    }
    
    /// Log activity to console and storage
    private func logActivity(type: ActivityType, details: [String: Any]) {
        // Create activity record
        var activityRecord: [String: Any] = [
            "type": type.rawValue,
            "sessionId": session.sessionId,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]
        
        // Add details (removing any PII if anonymization is enabled)
        if config.anonymizeUser {
            var sanitizedDetails = details
            // Remove potential PII (email, names, etc.)
            sanitizedDetails.removeValue(forKey: "email")
            sanitizedDetails.removeValue(forKey: "name")
            sanitizedDetails.removeValue(forKey: "user")
            sanitizedDetails.removeValue(forKey: "userId")
            activityRecord["details"] = sanitizedDetails
        } else {
            activityRecord["details"] = details
        }
        
        // Log to console for debugging
        #if DEBUG
        print("User Activity: \(activityRecord)")
        #endif
    }
    
    /// Save activity data to a local file
    private func saveActivityData() {
        guard let storageURL = storageURL else { return }
        
        // Prepare session data for storage
        let sessionData: [String: Any] = [
            "sessionId": session.sessionId,
            "startTime": ISO8601DateFormatter().string(from: session.startTime),
            "lastActivityTime": ISO8601DateFormatter().string(from: session.lastActivityTime),
            "deepestScrollPercentage": session.deepestScrollPercentage,
            "pagesViewed": session.pagesViewed,
            "interactions": session.interactions,
            "totalTimeSpent": session.lastActivityTime.timeIntervalSince(session.startTime)
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: sessionData, options: .prettyPrinted)
            try jsonData.write(to: storageURL, options: .atomic)
        } catch {
            print("Error saving activity data: \(error)")
        }
    }
    
    /// Get the session summary for analytics
    func getSessionSummary() -> [String: Any] {
        return [
            "sessionId": session.sessionId,
            "duration": session.lastActivityTime.timeIntervalSince(session.startTime),
            "pagesViewed": session.pagesViewed.count,
            "uniquePagesViewed": Set(session.pagesViewed).count,
            "interactionCount": session.interactions.values.reduce(0, +),
            "deepestScrollPercentage": session.deepestScrollPercentage
        ]
    }
    
    /// Export all tracking data for analysis
    func exportTrackingData() -> Data? {
        guard let storageURL = storageURL, FileManager.default.fileExists(atPath: storageURL.path) else {
            return nil
        }
        
        do {
            return try Data(contentsOf: storageURL)
        } catch {
            print("Error exporting tracking data: \(error)")
            return nil
        }
    }
    
    /// Clear all stored tracking data
    func clearTrackingData() {
        guard let storageURL = storageURL, FileManager.default.fileExists(atPath: storageURL.path) else {
            return
        }
        
        do {
            try FileManager.default.removeItem(at: storageURL)
        } catch {
            print("Error clearing tracking data: \(error)")
        }
    }
}

// MARK: - WebView Extension

extension WKWebView {
    /// Add activity tracking to the WebView
    func addUserActivityTracking(config: UserActivityTracker.TrackingConfig = UserActivityTracker.TrackingConfig()) -> UserActivityTracker {
        let tracker = UserActivityTracker(config: config)
        
        // Add script message handler
        configuration.userContentController.add(tracker, name: "userActivity")
        
        // Add tracking script
        let script = WKUserScript(
            source: tracker.trackingScript,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: true
        )
        configuration.userContentController.addUserScript(script)
        
        return tracker
    }
}