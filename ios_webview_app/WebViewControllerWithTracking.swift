import UIKit
import WebKit

class WebViewControllerWithTracking: UIViewController {
    
    // MARK: - Properties
    private var webView: WKWebView!
    private var progressView: UIProgressView!
    private var refreshControl: UIRefreshControl!
    private var observation: NSKeyValueObservation?
    private var activityTracker: UserActivityTracker!
    
    // Change this URL to your deployed app URL
    private let appURL = URL(string: "https://your-deployed-app-url.replit.app")!
    
    // MARK: - Lifecycle Methods
    override func viewDidLoad() {
        super.viewDidLoad()
        
        setupNavigationBar()
        configureWebView()
        setupProgressView()
        setupRefreshControl()
        loadWebContent()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startObservingProgress()
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        observation?.invalidate()
    }
    
    // MARK: - Setup Methods
    private func setupNavigationBar() {
        title = "Calm Journey"
        
        // Add refresh button
        let refreshButton = UIBarButtonItem(barButtonSystemItem: .refresh, target: self, action: #selector(refreshTapped))
        
        // Add home button
        let homeButton = UIBarButtonItem(barButtonSystemItem: .bookmarks, target: self, action: #selector(homeTapped))
        
        // Add privacy policy button
        let privacyButton = UIBarButtonItem(
            image: UIImage(systemName: "shield.lefthalf.filled"),
            style: .plain,
            target: self,
            action: #selector(privacyTapped)
        )
        
        navigationItem.rightBarButtonItems = [refreshButton, homeButton, privacyButton]
    }
    
    private func configureWebView() {
        // Configure WebView preferences
        let preferences = WKWebpagePreferences()
        preferences.allowsContentJavaScript = true
        
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences = preferences
        
        // Enable features needed for PWA support
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        
        // Create the web view
        webView = WKWebView(frame: view.bounds, configuration: configuration)
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.navigationDelegate = self
        webView.uiDelegate = self
        
        view.addSubview(webView)
        
        // Setup user activity tracking with privacy-focused configuration
        let trackingConfig = UserActivityTracker.TrackingConfig(
            enablePageViews: true,
            enableInteractions: true,
            enableTimeTracking: true,
            enableScrollDepth: true,
            anonymizeUser: true,  // Important: Ensure user data is anonymized
            collectionFrequency: 60
        )
        
        activityTracker = webView.addUserActivityTracking(config: trackingConfig)
    }
    
    private func setupProgressView() {
        progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(progressView)
        
        NSLayoutConstraint.activate([
            progressView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            progressView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            progressView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            progressView.heightAnchor.constraint(equalToConstant: 2)
        ])
    }
    
    private func setupRefreshControl() {
        refreshControl = UIRefreshControl()
        refreshControl.addTarget(self, action: #selector(refreshWebView), for: .valueChanged)
        webView.scrollView.addSubview(refreshControl)
    }
    
    private func startObservingProgress() {
        observation = webView.observe(\.estimatedProgress, options: [.new]) { [weak self] webView, change in
            guard let self = self else { return }
            
            self.progressView.progress = Float(webView.estimatedProgress)
            
            // Show/hide progress view based on load state
            if webView.estimatedProgress >= 1.0 {
                UIView.animate(withDuration: 0.3, delay: 0.3, options: .curveEaseOut, animations: {
                    self.progressView.alpha = 0
                }, completion: { finished in
                    self.progressView.progress = 0
                })
            } else {
                UIView.animate(withDuration: 0.3, delay: 0, options: .curveEaseIn, animations: {
                    self.progressView.alpha = 1
                }, completion: nil)
            }
        }
    }
    
    private func loadWebContent() {
        let request = URLRequest(url: appURL, cachePolicy: .returnCacheDataElseLoad)
        webView.load(request)
    }
    
    // MARK: - Action Methods
    @objc private func refreshTapped() {
        refreshWebView()
    }
    
    @objc private func homeTapped() {
        let request = URLRequest(url: appURL, cachePolicy: .returnCacheDataElseLoad)
        webView.load(request)
    }
    
    @objc private func privacyTapped() {
        showPrivacyOptions()
    }
    
    @objc private func refreshWebView() {
        webView.reload()
        refreshControl.endRefreshing()
    }
    
    private func showPrivacyOptions() {
        let alertController = UIAlertController(
            title: "Privacy Options",
            message: "Control how your user activity data is collected in this app",
            preferredStyle: .actionSheet
        )
        
        // Show tracking summary
        let summary = activityTracker.getSessionSummary()
        let pageCount = summary["pagesViewed"] as? Int ?? 0
        let interactionCount = summary["interactionCount"] as? Int ?? 0
        
        alertController.addAction(UIAlertAction(title: "View Data Collected", style: .default) { [weak self] _ in
            self?.showTrackingSummary(pageCount: pageCount, interactionCount: interactionCount)
        })
        
        alertController.addAction(UIAlertAction(title: "Clear All Data", style: .destructive) { [weak self] _ in
            self?.activityTracker.clearTrackingData()
            self?.showMessage(title: "Data Cleared", message: "All collected usage data has been removed from this device")
        })
        
        alertController.addAction(UIAlertAction(title: "Privacy Policy", style: .default) { [weak self] _ in
            // Navigate to privacy policy page
            if let privacyURL = URL(string: "\(self?.appURL.absoluteString ?? "")/privacy") {
                self?.webView.load(URLRequest(url: privacyURL))
            }
        })
        
        alertController.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        
        // For iPad compatibility
        if let popoverController = alertController.popoverPresentationController {
            popoverController.barButtonItem = navigationItem.rightBarButtonItems?.last
        }
        
        present(alertController, animated: true)
    }
    
    private func showTrackingSummary(pageCount: Int, interactionCount: Int) {
        let message = """
        Calm Journey collects anonymous usage data to improve your experience.
        
        Current session:
        • Pages viewed: \(pageCount)
        • Interactions: \(interactionCount)
        
        This data is stored only on your device and is not shared with third parties.
        """
        
        showMessage(title: "Data Collection", message: message)
    }
    
    private func showMessage(title: String, message: String) {
        let alertController = UIAlertController(
            title: title,
            message: message,
            preferredStyle: .alert
        )
        
        alertController.addAction(UIAlertAction(title: "OK", style: .default))
        
        present(alertController, animated: true)
    }
}

// MARK: - WKNavigationDelegate
extension WebViewControllerWithTracking: WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else {
            decisionHandler(.cancel)
            return
        }
        
        // Handle external links
        if url.host != appURL.host && (url.scheme == "http" || url.scheme == "https") {
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        
        decisionHandler(.allow)
    }
    
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // Add any JavaScript to be executed after page load
    }
    
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        refreshControl.endRefreshing()
        handleNavigationError(error)
    }
    
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        refreshControl.endRefreshing()
        handleNavigationError(error)
    }
    
    private func handleNavigationError(_ error: Error) {
        // Handle errors like no network connection
        if let error = error as NSError?, error.code == NSURLErrorNotConnectedToInternet {
            let alertController = UIAlertController(
                title: "Connection Error",
                message: "Could not connect to Calm Journey. Please check your internet connection and try again.",
                preferredStyle: .alert
            )
            
            alertController.addAction(UIAlertAction(title: "Retry", style: .default) { [weak self] _ in
                self?.loadWebContent()
            })
            
            alertController.addAction(UIAlertAction(title: "Cancel", style: .cancel))
            
            present(alertController, animated: true)
        }
    }
}

// MARK: - WKUIDelegate
extension WebViewControllerWithTracking: WKUIDelegate {
    // Standard WKUIDelegate implementations for handling JavaScript alerts/confirms/prompts
    // (Same code as in the original WebViewController)
}